import xml.etree.ElementTree as etree
from graph import Graph, StateType, EdgeType
from tree import Tree, Goal, Attack, Defense, OperationType


def list_to_string(names, prefix="", values=None):
    if len(names) == 0:
        return ""
    string = f"{prefix}{names[0]}"
    if values is not None:
        string += f" = {values[0]}"

    for i in range(1, len(names)):
        string += f", {prefix}{names[i]}"
        if values is not None:
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

    def __init__(self, graph, output_file_name):
        self.graph = graph
        self.output_file_name = output_file_name

    def open_file(self):
        self.output_file = open(self.output_file_name, "w")

    def close_file(self):
        self.output_file.close

    def make_xml(self):
        self.open_file()
        self.output_file.write('<?xml version="1.0" encoding="utf-8"?>\n')
        self.output_file.write(
            "<!DOCTYPE nta PUBLIC '-//Uppaal Team//DTD Flat System 1.1//EN' 'http://www.it.uu.se/research/group/darts/uppaal/flat-1_2.dtd'>\n"
        )
        self.close_file()
        self.nta = etree.Element("nta")
        self.make_declaration()
        self.make_templates()
        system = etree.SubElement(self.nta, "system")
        system.text = "system AttackDefenseGraph;"
        self.make_queries()
        etree.indent(self.nta, space="\t", level=0)
        self.output_file.write(etree.tostring(self.nta, encoding="unicode"))

    def make_declaration(self):
        tree = self.graph.tree
        attack_names = [attack.name for attack in tree.attacks]
        defense_names = [defense.name for defense in tree.defenses]
        t_a = [attack.completion_time for attack in tree.attacks]
        p_a = [attack.success_probability for attack in tree.attacks]
        c_a = [attack.activation_cost for attack in tree.attacks]
        t_d = [defense.period for defense in tree.defenses]
        p_d = [defense.success_probability for defense in tree.defenses]

        self.declaration = etree.SubElement(self.nta, "declaration")
        self.declaration.text = f"""const int n_a = {len(tree.attacks)};
const int n_d = {len(tree.defenses)};
hybrid clock time;
double attack_cost;

clock {list_to_string(attack_names, prefix='x_')};
const int {list_to_string(attack_names, prefix='t_', values=t_a)};
//const int {list_to_string(attack_names, prefix='p_', values=p_a)};
const int {list_to_string(attack_names, prefix='c_', values=c_a)};
"""
        if len(defense_names) > 0:
            self.declaration.text += f"""
clock {list_to_string(defense_names, prefix='x_')};
const int {list_to_string(defense_names, prefix='t_', values=t_d)};
//const int {list_to_string(defense_names, prefix='p_', values=p_d)};
"""

    def make_templates(self):
        template = etree.SubElement(self.nta, "template")
        template_name = etree.SubElement(template, "name")
        template_name.set("x", "0")
        template_name.set("y", "0")
        template_name.text = "AttackDefenseGraph"
        etree.SubElement(template, "parameter")
        etree.SubElement(template, "declaration")
        states = self.graph.states
        for state in states.values():
            if state.state_type == StateType.NORMAL:
                state_id = self.make_location(state, template)
                if state_id:
                    initial_state_id = state_id
        for state in states.values():
            if state.state_type != StateType.NORMAL:
                self.make_branchpoint(state, template)
        initial = etree.SubElement(template, "init")
        for state in states.values():
            for edge in state.edges:
                self.make_transition(edge, template)

        initial.set("ref", initial_state_id)

    def make_location(self, state, template):
        self.serial_to_id[state.serialize()] = f"id{self.state_id}"
        self.id_to_serial[f"id{self.state_id}"] = state.serialize()
        location_x, location_y = self.dx * (self.state_id // self.lx), self.dy * (
            self.state_id % self.lx
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
        branchpoint_x, branchpoint_y = self.dx * (self.state_id // self.lx), self.dy * (
            self.state_id % self.lx
        )
        self.serial_to_position[state.serialize()] = (branchpoint_x, branchpoint_y)

        branchpoint = etree.SubElement(template, "branchpoint")
        branchpoint.set("id", f"id{self.state_id}")
        branchpoint.set("x", str(branchpoint_x))
        branchpoint.set("y", str(branchpoint_y))
        self.state_id += 1

    def make_label(self, state, location, x, y):
        # Stop time of goal
        if state.accepting:
            label = etree.SubElement(
                location,
                "label",
                {"kind": "invariant", "x": str(x - 50), "y": str(y + 20)},
            )
            label.text = f"time' == 0"

        if len(self.graph.tree.defenses) == 0 and len(state.activated) == 0:
            return
        label = etree.SubElement(
            location,
            "label",
            {"kind": "invariant", "x": str(x - 50), "y": str(y + 20)},
        )
        # Make defense clocks guards
        if len(self.graph.tree.defenses) > 0:
            defense_name = self.graph.tree.defenses[0].name
            invariant = f"x_{defense_name} <= t_{defense_name}"
            for defense in self.graph.tree.defenses[1:]:
                invariant += f"&&\nx_{defense.name} <= t_{defense.name}"
        # Make active attacks clocks guards
        if len(self.graph.tree.defenses) == 0:
            invariant = f"x_{state.activated[0].name} <= t_{state.activated[0].name}"
        elif len(state.activated) > 0:
            invariant += f"&&\nx_{state.activated[0].name} <= t_{state.activated[0].name}"
        if len(state.activated) > 0:
            for activated in state.activated[1:]:
                invariant += f"&&\nx_{activated.name} <= t_{activated.name}"
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
            label.text = f"x_{edge.attack.name} = 0,\nattack_cost = attack_cost + c_{edge.attack.name}"
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
        if edge.type == EdgeType.COMPLETION or edge.type == EdgeType.DEFENSE:
            label = etree.SubElement(
                transition,
                "label",
                {"kind": "probability", "x": str(label_x), "y": str(label_y)},
            )
            label.text = str(int(edge.success_probability * 1000))

    def make_queries(self):
        goal_name = self.serial_to_location_name[self.graph.accepting_state.serialize()]
        goal_name = "AttackDefenseGraph." + goal_name
        queries = etree.SubElement(self.nta, "queries")
        # Fast strategy
        query = etree.SubElement(queries, "query")
        formula = etree.SubElement(query, "formula")
        formula.text = f"strategy fast = minE(time)[<=1000]: <>{goal_name}"
        comment = etree.SubElement(query, "comment")
        comment.text = "Fast strategy"
        # Expected time under fast
        query = etree.SubElement(queries, "query")
        formula = etree.SubElement(query, "formula")
        formula.text = f"E[<=1000;500](max: time) under fast"
        comment = etree.SubElement(query, "comment")
        comment.text = "Expected time under fast"
        # Expected cost under fast
        query = etree.SubElement(queries, "query")
        formula = etree.SubElement(query, "formula")
        formula.text = f"E[<=1000;500](max: attack_cost) under fast"
        comment = etree.SubElement(query, "comment")
        comment.text = "Expected cost under fast"
        # Success probability under fast
        query = etree.SubElement(queries, "query")
        formula = etree.SubElement(query, "formula")
        formula.text = f"Pr[<=1000](<>{goal_name}) under fast"
        comment = etree.SubElement(query, "comment")
        comment.text = "Success probability under fast"

        query = etree.SubElement(queries, "query")

        # Cheap strategy
        query = etree.SubElement(queries, "query")
        formula = etree.SubElement(query, "formula")
        formula.text = f"strategy cheap = minE(attack_cost)[<=1000]: <>{goal_name}"
        comment = etree.SubElement(query, "comment")
        comment.text = "Cheap strategy"
        # Expected time under cheap
        query = etree.SubElement(queries, "query")
        formula = etree.SubElement(query, "formula")
        formula.text = f"E[<=1000;500](max: time) under cheap"
        comment = etree.SubElement(query, "comment")
        comment.text = "Expected time under cheap"
        # Expected cost under cheap
        query = etree.SubElement(queries, "query")
        formula = etree.SubElement(query, "formula")
        formula.text = f"E[<=1000;500](max: attack_cost) under cheap"
        comment = etree.SubElement(query, "comment")
        comment.text = "Expected cost under cheap"
        # Success probability under cheap
        query = etree.SubElement(queries, "query")
        formula = etree.SubElement(query, "formula")
        formula.text = f"Pr[<=1000](<>{goal_name}) under cheap"
        comment = etree.SubElement(query, "comment")
        comment.text = "Success probability under cheap"


if __name__ == "__main__":
    root = Goal(
        children=[
            Goal(
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
    tree = Tree(root)
    print(
        f"parent of {tree.root}'s child {tree.get_children()[1]} is {tree.get_children()[1].parent}"
    )
    graph = Graph(tree)
    print(graph)
    uppaal = UppaalExporter(graph, "output.xml")
    uppaal.make_xml()
