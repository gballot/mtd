import xml.etree.ElementTree as etree
from admdp import ADMDP, StateType, EdgeType
from adg import ADG, Subgoal, Attack, Defense, OperationType


def list_to_string(names, prefix="", values=None, format_values=None):
    if len(names) == 0:
        return ""
    connector = ""
    string = ""
    for i in range(len(names)):
        if values is None or values[i] is not None:
            string += f"{connector}{prefix}{names[i]}"
            connector = ", "
        if values is not None and values[i] is not None:
            if format_values:
                string += f" = {format_values.format(values[i])}"
            else:
                string += f" = {values[i]}"
    return string


class UppaalExporter:
    output_file = None
    state_id = 0
    id_to_serial = dict()
    serial_to_id = dict()
    serial_to_position = dict()
    serial_to_location_name = dict()
    dx, dy, lx = 100, 100, 8

    def __init__(self, admdp, output_file_name):
        self.admdp = admdp
        self.output_file_name = output_file_name

    def open_file(self, mode="w"):
        self.output_file = open(self.output_file_name, mode)

    def close_file(self):
        self.output_file.close()

    def make_xml(self, simulation_number=10000, time_limit=1000, cost_limit=400):
        """XML file interpretable by Uppaal Stratego."""
        self.open_file()
        self.output_file.write('<?xml version="1.0" encoding="utf-8"?>\n')
        self.output_file.write(
            "<!DOCTYPE nta PUBLIC '-//Uppaal Team//DTD Flat System 1.1//EN' 'http://www.it.uu.se/research/group/darts/uppaal/flat-1_2.dtd'>\n"
        )
        self.nta = etree.Element("nta")
        self.make_declaration()
        self.make_templates()
        system = etree.SubElement(self.nta, "system")
        system.text = "system AttackDefenseADMDP;"
        self.make_queries(simulation_number, time_limit, cost_limit)
        etree.indent(self.nta, space="\t", level=0)
        self.output_file.write(
            etree.tostring(self.nta, encoding="unicode", short_empty_elements=False)
        )
        self.close_file()

    def set_queries(self, simulation_number=10000, time_limit=None, cost_limit=None):
        self.open_file(mode="r")
        system = etree.parse(self.output_file)
        self.close_file()
        self.nta = system.getroot()
        self.nta.remove(system.find("queries"))
        self.open_file(mode="w")
        self.make_queries(simulation_number, time_limit, cost_limit)
        etree.indent(self.nta, space="\t", level=0)
        self.output_file.write(
            etree.tostring(self.nta, encoding="unicode", short_empty_elements=False)
        )
        self.close_file()

    def set_defense_times(self, times):
        self.open_file(mode="r")
        system = etree.parse(self.output_file)
        self.close_file()
        self.nta = system.getroot()
        self.open_file(mode="w")
        self.make_declaration(remake=True)
        etree.indent(self.nta, space="\t", level=0)
        self.output_file.write(
            etree.tostring(self.nta, encoding="unicode", short_empty_elements=False)
        )
        self.close_file()

    def make_declaration(self, remake=False):
        """Declaration section of Uppaal."""
        adg = self.admdp.adg
        attack_names = [attack.name for attack in adg.attacks]
        defense_names = [defense.name for defense in adg.defenses]
        t_a = [attack.completion_time for attack in adg.attacks]
        p_a = [attack.success_probability for attack in adg.attacks]
        c_a = [attack.activation_cost for attack in adg.attacks]
        cp_a = [attack.proportional_cost for attack in adg.attacks]
        t_d = [defense.period for defense in adg.defenses]
        p_d = [defense.success_probability for defense in adg.defenses]

        if remake:
            declaration = self.nta.find("declaration")
        else:
            declaration = etree.SubElement(self.nta, "declaration")
        declaration.text = f"""const int n_a = {len(adg.attacks)};
const int n_d = {len(adg.defenses)};
hybrid clock time;
hybrid clock cost;

hybrid clock xcost;

hybrid clock {list_to_string(attack_names, prefix='x_')};
const int {list_to_string(attack_names, prefix='t_', values=t_a)};
const double {list_to_string(attack_names, prefix='p_', values=p_a, format_values='{:.5f}')};
const int {list_to_string(attack_names, prefix='c_', values=c_a)};
"""
        if any(cp_a):
            declaration.text += (
                f"const int {list_to_string(attack_names, prefix='cp_', values=cp_a)};"
            )

        if len(defense_names) > 0:
            declaration.text += f"""
hybrid clock {list_to_string(defense_names, prefix='x_')};
const int {list_to_string(defense_names, prefix='t_', values=t_d)};
const double {list_to_string(defense_names, prefix='p_', values=p_d, format_values='{:.5f}')};
"""

    def make_templates(self):
        """The unic template of our uppaal model."""
        template = etree.SubElement(self.nta, "template")
        template_name = etree.SubElement(template, "name")
        template_name.set("x", "0")
        template_name.set("y", "0")
        template_name.text = "AttackDefenseADMDP"
        etree.SubElement(template, "parameter")
        etree.SubElement(template, "declaration")
        states = self.admdp.states
        for state in states.values():
            if (
                state.state_type == StateType.NORMAL
                or state.state_type == StateType.NO_ACTIVATION
                or state.state_type == StateType.ACTIVATION_COST
            ):
                state_id = self.make_location(state, template)
                if state_id:
                    initial_state_id = state_id
        for state in states.values():
            if (
                state.state_type == StateType.MTD
                or state.state_type == StateType.COMPLETION
            ):
                self.make_branchpoint(state, template)
        initial = etree.SubElement(template, "init")
        for state in states.values():
            for edge in state.edges:
                self.make_transition(edge, template)

        initial.set("ref", initial_state_id)

    def make_location(self, state, template):
        """Locations of the template."""
        self.serial_to_id[state.serialize()] = f"id{self.state_id}"
        self.id_to_serial[f"id{self.state_id}"] = state.serialize()
        location_x, location_y = (
            self.dx * (self.state_id // self.lx),
            self.dy * (self.state_id % self.lx),
        )
        self.serial_to_position[state.serialize()] = (location_x, location_y)

        location = etree.SubElement(template, "location")
        location.set("id", f"id{self.state_id}")
        location.set("x", str(location_x))
        location.set("y", str(location_y))
        location_name = etree.SubElement(location, "name")
        location_name.set("x", str(location_x - 50))
        location_name.set("y", str(location_y - 34))
        location_name.text = "__".join(
            e if type(e) is str else "_".join(str(sub_elem) for sub_elem in e)
            for e in state.serialize()
        )
        self.serial_to_location_name[state.serialize()] = location_name.text
        self.make_label(state, location, location_x, location_y)

        initial_state_id = f"id{self.state_id}" if state.initial else None

        self.state_id += 1
        return initial_state_id

    def make_branchpoint(self, state, template):
        self.serial_to_id[state.serialize()] = f"id{self.state_id}"
        self.id_to_serial[f"id{self.state_id}"] = state.serialize()
        branchpoint_x, branchpoint_y = (
            self.dx * (self.state_id // self.lx),
            self.dy * (self.state_id % self.lx),
        )
        self.serial_to_position[state.serialize()] = (branchpoint_x, branchpoint_y)

        branchpoint = etree.SubElement(template, "branchpoint")
        branchpoint.set("id", f"id{self.state_id}")
        branchpoint.set("x", str(branchpoint_x))
        branchpoint.set("y", str(branchpoint_y))
        self.state_id += 1

    def make_label(self, state, location, x, y):
        """Labels of locations (invariant only are needed)."""
        # Stop time of subgoal
        if state.accepting:
            label = etree.SubElement(
                location,
                "label",
                {"kind": "invariant", "x": str(x - 50), "y": str(y + 20)},
            )
            label.text = f"time' == 0 && cost' == 0"
            return

        label = etree.SubElement(
            location,
            "label",
            {"kind": "invariant", "x": str(x - 50), "y": str(y + 20)},
        )
        if (
            state.state_type == StateType.NO_ACTIVATION
            or state.state_type == StateType.NORMAL
        ):
            # Make proportial cost invariant
            invariant = "cost' =="
            cost_connector = " "
            for attack in state.activated:
                if attack.proportional_cost is not None:
                    invariant += f"{cost_connector}cp_{attack.name}"
                    cost_connector = " + "
            if cost_connector == " ":
                invariant += " 0"
            # Make defense clocks guards
            for defense in self.admdp.adg.defenses:
                invariant += f" &&\nx_{defense.name} <= t_{defense.name}"
            # Make active attacks clocks guards
            for activated in state.activated:
                invariant += f" &&\nx_{activated.name} <= t_{activated.name}"
        elif state.state_type == StateType.ACTIVATION_COST:
            invariant = f"time' == 0 &&\nxcost <= 1 &&\ncost' == c_{state.attack.name}"
            for attack in self.admdp.adg.attacks:
                invariant += f" &&\nx_{attack.name}' == 0"
            for defense in self.admdp.adg.defenses:
                invariant += f" &&\nx_{defense.name}' == 0"

        label.text = invariant

    def make_transition(self, edge, template):
        transition = etree.SubElement(template, "transition")
        source = etree.SubElement(
            transition, "source", {"ref": self.serial_to_id[edge.source.serialize()]}
        )
        target = etree.SubElement(
            transition,
            "target",
            {"ref": self.serial_to_id[edge.destination.serialize()]},
        )
        source_x, source_y = self.serial_to_position[edge.source.serialize()]
        target_x, target_y = self.serial_to_position[edge.destination.serialize()]
        label_x, label_y = (source_x + target_x) // 2, (source_y + target_y) // 2
        if edge.type == EdgeType.ACTIVATION:
            label = etree.SubElement(
                transition,
                "label",
                {"kind": "assignment", "x": str(label_x), "y": str(label_y)},
            )
            label.text = f"x_{edge.attack.name} = 0"
            if edge.source.state_type == StateType.ACTIVATION_COST:
                transition.set("controllable", "false")
                label = etree.SubElement(
                    transition,
                    "label",
                    {"kind": "guard", "x": str(label_x), "y": str(label_y)},
                )
                label.text = f"xcost >= 1"
        if edge.type == EdgeType.LOOP_DEFENSE:
            label = etree.SubElement(
                transition,
                "label",
                {"kind": "assignment", "x": str(label_x), "y": str(label_y)},
            )
            label.text = f"x_{edge.defense.name} = 0"
            label = etree.SubElement(
                transition,
                "label",
                {"kind": "guard", "x": str(label_x), "y": str(label_y)},
            )
            label.text = f"x_{edge.defense.name} >= t_{edge.defense.name}"
            for follower in edge.defense.followers:
                label.text = label.text + f" and x_{follower.name} < t_{follower.name}"
        if edge.type == EdgeType.TO_COMPLETION:
            transition.set("controllable", "false")
            label = etree.SubElement(
                transition,
                "label",
                {"kind": "guard", "x": str(label_x), "y": str(label_y)},
            )
            label.text = f"x_{edge.attack.name} >= t_{edge.attack.name}"
        if edge.type == EdgeType.TO_DEFENSE:
            transition.set("controllable", "false")
            label = etree.SubElement(
                transition,
                "label",
                {"kind": "assignment", "x": str(label_x), "y": str(label_y)},
            )
            label.text = f"x_{edge.defense.name} = 0"
            label = etree.SubElement(
                transition,
                "label",
                {"kind": "guard", "x": str(label_x), "y": str(label_y)},
            )
            label.text = f"x_{edge.defense.name} >= t_{edge.defense.name}"
            for follower in edge.defense.followers:
                label.text = label.text + f" and x_{follower.name} < t_{follower.name}"
        if edge.type == EdgeType.COMPLETION:
            label = etree.SubElement(
                transition,
                "label",
                {"kind": "probability", "x": str(label_x), "y": str(label_y)},
            )
            if edge.success:
                label.text = f"fint(p_{edge.attack.name} * 1000)"
            else:
                label.text = f"fint((1-p_{edge.attack.name}) * 1000)"
        if edge.type == EdgeType.DEFENSE:
            label = etree.SubElement(
                transition,
                "label",
                {"kind": "probability", "x": str(label_x), "y": str(label_y)},
            )
            if edge.success:
                label.text = f"fint(p_{edge.defense.name} * 1000)"
            else:
                label.text = f"fint((1-p_{edge.defense.name}) * 1000)"
        if edge.type == EdgeType.TO_ACTIVATION_COST:
            label = etree.SubElement(
                transition,
                "label",
                {"kind": "assignment", "x": str(label_x), "y": str(label_y)},
            )
            label.text = "xcost = 0"

    def make_queries(
        self, simulation_number=10000, time_limit=None, cost_limit=None, infinity=100000
    ):
        """Uppaal and Stratego queries on the model."""
        goal_name = self.serial_to_location_name[self.admdp.accepting_state.serialize()]
        goal_name = "AttackDefenseADMDP." + goal_name
        queries = etree.SubElement(self.nta, "queries")

        # Fast strategy
        if time_limit is None and cost_limit is None:
            query = etree.SubElement(queries, "query")
            formula = etree.SubElement(query, "formula")
            formula.text = f"strategy fast = minE(time)[time<=10000]: <>{goal_name}"
            comment = etree.SubElement(query, "comment")
            comment.text = "Fast strategy"
            # Expected time under fast
            query = etree.SubElement(queries, "query")
            formula = etree.SubElement(query, "formula")
            formula.text = f"E[time<=10000;{simulation_number}](max: time) under fast"
            comment = etree.SubElement(query, "comment")
            comment.text = "Expected time under fast"
            # Expected cost under fast
            query = etree.SubElement(queries, "query")
            formula = etree.SubElement(query, "formula")
            formula.text = f"E[time<=10000;{simulation_number}](max: cost) under fast"
            comment = etree.SubElement(query, "comment")
            comment.text = "Expected cost under fast"
            # Success probability under fast
            query = etree.SubElement(queries, "query")
            formula = etree.SubElement(query, "formula")
            formula.text = f"Pr[time<=100](<>{goal_name}) under fast"
            comment = etree.SubElement(query, "comment")
            comment.text = "Success probability under fast"

        # Cheap strategy
        if time_limit is not None:
            query = etree.SubElement(queries, "query")
            formula = etree.SubElement(query, "formula")
            formula.text = (
                f"strategy cheap = minE(cost)[time<={time_limit}]: <>{goal_name}"
            )
            comment = etree.SubElement(query, "comment")
            comment.text = "Cheap strategy"
            # Expected time under cheap
            query = etree.SubElement(queries, "query")
            formula = etree.SubElement(query, "formula")
            formula.text = (
                f"E[time<={infinity};{simulation_number}](max: time) under cheap"
            )
            comment = etree.SubElement(query, "comment")
            comment.text = "Expected time under cheap"
            # Expected cost under cheap
            query = etree.SubElement(queries, "query")
            formula = etree.SubElement(query, "formula")
            formula.text = (
                f"E[time<={infinity};{simulation_number}](max: cost) under cheap"
            )
            comment = etree.SubElement(query, "comment")
            comment.text = "Expected cost under cheap"
            # Success probability under cheap
            query = etree.SubElement(queries, "query")
            formula = etree.SubElement(query, "formula")
            formula.text = f"Pr[time<={time_limit}](<>{goal_name}) under cheap"
            comment = etree.SubElement(query, "comment")
            comment.text = "Success probability under cheap"

            query = etree.SubElement(queries, "query")
            formula = etree.SubElement(query, "formula")
            comment = etree.SubElement(query, "comment")

        # Limited cost strategy
        if cost_limit is not None:
            query = etree.SubElement(queries, "query")
            formula = etree.SubElement(query, "formula")
            formula.text = (
                f"strategy limited_cost = minE(time)[cost<={cost_limit}]: <>{goal_name}"
            )
            comment = etree.SubElement(query, "comment")
            comment.text = "Limited cost fastest strategy"
            # Expected time under cheap
            query = etree.SubElement(queries, "query")
            formula = etree.SubElement(query, "formula")
            formula.text = (
                f"E[cost<={infinity};{simulation_number}](max: time) under limited_cost"
            )
            comment = etree.SubElement(query, "comment")
            comment.text = "Expected time under limited cost"
            # Expected cost under cheap
            query = etree.SubElement(queries, "query")
            formula = etree.SubElement(query, "formula")
            formula.text = (
                f"E[cost<={infinity};{simulation_number}](max: cost) under limited_cost"
            )
            comment = etree.SubElement(query, "comment")
            comment.text = "Expected cost under limited cost"
            # Success probability under cheap
            query = etree.SubElement(queries, "query")
            formula = etree.SubElement(query, "formula")
            formula.text = f"Pr[cost<={cost_limit}](<>{goal_name}) under limited_cost"
            comment = etree.SubElement(query, "comment")
            comment.text = "Success probability under limited_cost"


if __name__ == "__main__":
    root = Subgoal(
        children=[
            Subgoal(
                children=[
                    Attack(
                        completion_time=10,
                        success_probability=0.5,
                        activation_cost=5,
                        name="a0",
                    ),
                    Attack(
                        completion_time=3,
                        success_probability=0.2,
                        activation_cost=1,
                        name="a1",
                    ),
                ],
                operation_type=OperationType.OR,
                reset=False,
                name="g1",
            ),
            Attack(
                completion_time=7,
                success_probability=0.7,
                activation_cost=10,
                name="a2",
            ),
            Defense(period=5, success_probability=0.6, name="d0"),
        ],
        operation_type=OperationType.AND,
        reset=False,
        name="g0",
    )
    adg = adg(root)
    print(
        f"parent of {adg.root}'s child {adg.get_children()[1]} is {adg.get_children()[1].parent}"
    )
    admdp = ADMDP(adg)
    print(admdp)
    uppaal = UppaalExporter(admdp, "output.xml")
    uppaal.make_xml()
