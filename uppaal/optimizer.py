import subprocess
import re

from graph import Graph
from tree import Tree, Goal, Attack, Defense, OperationType
from uppaal import UppaalExporter


def score(E_time, E_cost, P_success_inf, P_success_sup):
    return E_time / 100 - E_cost / 400 + (P_success_inf + P_success_sup) / 2


class Optimizer:
    verifyta_prefix = "/home/gabriel/uppaal64-4.1.20-stratego-7/bin-Linux/"

    def __init__(self, tree):
        self.tree = tree
        self.graph = Graph(self.tree)

    def set_defense_times(self, times):
        """times is a dictionary with names of the defenses as key."""
        for defense in self.tree.defenses:
            defense.period = times[defense.name]
        self.graph = Graph(self.tree)  # We could avoid rebuilding it

    def export(
        self, file_name, simulation_number=10000, time_limit=1000, cost_limit=400
    ):
        uppaal = UppaalExporter(self.graph, file_name)
        uppaal.make_xml(simulation_number, time_limit, cost_limit)

    def verify(self, file_name):
        command = f"{self.verifyta_prefix}verifyta -s {file_name}"
        process = subprocess.run(command.split(), capture_output=True, encoding="utf-8")
        output = process.stdout
        output = output.replace("\x1b[2K", "")
        output = output.replace("\x1b[K", "")
        output = output.replace("\n\n\n", "\n\n")
        formulas = output.split("\n\n")
        # Formula 9: strategy limited_cost = minE(time)[cost<=400]: <>AttackDefenseGraph.goal
        strategy_found = "Formula is satisfied." in formulas[9]
        if strategy_found:
            # Formula 10: E[cost<={cost_limit};{simulation_number}](max: time) under limited_cost
            E_time = float(
                re.findall(
                    "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?",
                    formulas[10].split("\n")[2],
                )[1][0]
            )
            time_distribution_matches = re.findall(
                "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?", formulas[10].split("\n")[3]
            )
            time_distribution_low = float(time_distribution_matches[0][0])
            time_distribution_up = float(time_distribution_matches[1][0])
            time_distribution_hist = [int(m[0]) for m in time_distribution_matches[4:]]
            # Formula 11: E[cost<={cost_limit};{simulation_number}](max: cost) under limited_cost
            E_cost = float(
                re.findall(
                    "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?",
                    formulas[11].split("\n")[2],
                )[1][0]
            )
            cost_distribution_matches = re.findall(
                "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?", formulas[11].split("\n")[3]
            )
            cost_distribution_low = float(cost_distribution_matches[0][0])
            cost_distribution_up = float(cost_distribution_matches[1][0])
            cost_distribution_hist = [int(m[0]) for m in cost_distribution_matches[4:]]
            # Formula 11: Pr[cost<={cost_limit}](<>AttackDefenseGraph.goal) under limited_cost
            P_success_inf = float(
                re.findall(
                    "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?",
                    formulas[12].split("\n")[2],
                )[1][0]
            )
            P_success_sup = float(
                re.findall(
                    "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?",
                    formulas[12].split("\n")[2],
                )[2][0]
            )
            P_success_confidence = float(
                re.findall(
                    "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?",
                    formulas[12].split("\n")[3],
                )[0][0]
            )
        return E_time, E_cost, P_success_inf, P_success_sup

    def evaluate(
        self, times, file_name, simulation_number=10000, time_limit=1000, cost_limit=400
    ):
        self.set_defense_times(times)
        self.export(file_name, cost_limit=cost_limit)
        return score(*self.verify(file_name))
