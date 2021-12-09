from lxml import etree
from graph import Graph

class UppaalExporter:
    output_file=None
    indent = 0

    def __init__(self, graph, output_file_name):
        self.graph = graph
        self.output_file_name = output_file_name

    def open_file(self):
        self.output_file = open(output_file_name, 'w')

    def write(self, text):
        output_file.write(indent*"  " + text + "\n")

    def make_header(self):
        self.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>")
        self.write("<!DOCTYPE nta PUBLIC '-//Uppaal Team//DTD Flat System 1.1//EN' 'http://www.it.uu.se/research/group/darts/uppaal/flat-1_2.dtd'>")
        etree.Element("nta")

    def make_declaration(self):
        tree = self.graph.tree
        old_indent = self.indent
        #etree.Element("declaration")
        self..write("<declaration>")
        self.indent = 0
        self.write(f"const int n_a = {len(tree.attacks)};")
        self.write(f"const int n_d = {len(tree.defenses)};")
        self.write("hybrid clock time;")
        self.write("int attack_cost;")

        self.write("")
        self.write("clock x_a[n_a];")
        # Attack completion times
        t_a = [attack.completion_time for attack in tree.attacks]
        t_a_string = f"{t_a[0]}"
        for time in t_a[1:]:
            t_a_string += f", {time}"
        self.write("const int t_a[n_a] = \{{t_a_string}\};")
        # Attack success probabilities
        p_a = [attack.success_probability for attack in tree.attacks]
        p_a_string = f"{p_a[0]}"
        for proba in p_a[1:]:
            p_a_string += f", {proba}"
        self.write("const int p_a[n_a] = \{{p_a_string}\};")
        # Attack costs
        c_a = [attack.activation_cost for attack in tree.attacks]
        c_a_string = f"{c_a[0]}"
        for cost in c_a[1:]:
            c_a_string += f", {cost}"
        self.write("const int c_a[n_a] = \{{c_a_string}\};")

        self.write("")
        self.write("clock x_d[n_d];")
        # Defense periods
        t_d = [defense.period for defense in tree.defenses]
        t_d_string = f"{t_d[0]}"
        for period in t_d[1:]:
            t_d_string += f", {period}"
        self.write("const int t_a[n_d] = \{{t_a_string}\};")
        # Defense success probabilities
        p_d = [defense.success_probability for defense in tree.defenses]
        p_d_string = f"{p_d[0]}"
        for proba in p_d[1:]:
            p_d_string += f", {proba}"
        self.write("const int p_d[n_d] = \{{p_d_string}\};")
        self..write("</declaration>")
