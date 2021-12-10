import xml.etree.ElementTree as etree
from graph import Graph, StateType
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
int attack_cost;

clock {list_to_string(attack_names, prefix='x_')};
const int {list_to_string(attack_names, prefix='t_', values=t_a)};
const int {list_to_string(attack_names, prefix='p_', values=p_a)};
const int {list_to_string(attack_names, prefix='c_', values=c_a)};

clock {list_to_string(defense_names, prefix='x_')};
const int {list_to_string(defense_names, prefix='t_', values=t_d)};
const int {list_to_string(defense_names, prefix='p_', values=p_d)};
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
            state_id = self.make_state(state, template)
            if state_id:
                initial_state_id = state_id
        initial = etree.SubElement(template, "init")
        initial.set("ref", initial_state_id)

    def make_state(self, state, template):
        dx, dy, lx = 100, 100, 8
        location_x, location_y = dx * (self.state_id // lx), dy * (self.state_id % lx)
        initial_state_id = None
        location = etree.SubElement(template, "location")
        location.set("id", f"id{self.state_id}")
        location.set("x", str(location_x))
        location.set("y", str(location_y))
        location_name = etree.SubElement(location, "name")
        location_name.set("x", str(location_x - 50))
        location_name.set("y", str(location_y - 34))
        location_name.text = "_".join(
            e if type(e) is str else "_".join(str(sub_elem) for sub_elem in e)
            for e in state.serialize()
        )
        self.make_label(state, location, location_x, location_y)
        if state.initial:
            initial_state_id = f"id{self.state_id}"
        self.state_id += 1
        return initial_state_id

    def make_label(self, state, location, x, y):
        if state.state_type == StateType.NORMAL:
            # Make defense clocks guards
            if len(state.active_defenses) > 0:
                defense_name = state.active_defenses[0].name
                label = etree.SubElement(
                    location,
                    "label",
                    {"kind": "invariant", "x": str(x - 50), "y": str(y + 20)},
                )
                invariant = f"x_{defense_name} <= t_{defense_name}"
                for defense in state.active_defenses[1:]:
                    invariant += f"&&\nx_{defense.name} <= t_{defense.name}"
                label.text = invariant
            # Make active attacks clocks guards
            if len(state.activated) > 0:
                activated_name = state.activated[0].name
                label = etree.SubElement(
                    location,
                    "label",
                    {"kind": "invariant", "x": str(x - 50), "y": str(y + 20)},
                )
                invariant = f"x_{activated_name} <= t_{activated_name}"
                for activated in state.activated[1:]:
                    invariant += f"&&\nx_{activated.name} <= t_{activated.name}"
                label.text = invariant


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
