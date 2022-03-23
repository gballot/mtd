from scipy.optimize import LinearConstraint, Bounds, minimize
import numpy as np
import subprocess
import re

from admdp import ADMDP
from adg import ADG, Subgoal, Attack, Defense, OperationType
from uppaal import UppaalExporter


def score(E_time, E_cost, P_success_inf, P_success_sup):
    return E_time / 100 - E_cost / 400 + (P_success_inf + P_success_sup) / 2


class Optimizer:
    verifyta_prefix = "/home/gabriel/uppaal64-4.1.20-stratego-7/bin-Linux/"

    def __init__(self, adg):
        self.adg = adg
        self.admdp = ADMDP(self.adg)

    def set_defense_times(self, times):
        """times is a dictionary with names of the defenses as key."""
        for defense in self.adg.defenses:
            if defense.name in times:
                defense.period = times[defense.name]
        self.exporter.set_defense_times(times)

    def minimize(
        self,
        defense_cost_limit,
        defense_cost_proportions,
        time_limit=None,
        cost_limit=None,
    ):
        defenses = self.adg.defenses
        n_d = len(defenses)
        coeficients_defenses = np.array(
            [[c[1] for c in sorted(list(defense_cost_proportions.items()))]]
        )
        constraint_matrix = np.concatenate(
            [np.eye(n_d), coeficients_defenses], dtype=float
        )
        left_bound = np.ones(n_d + 1)
        left_bound[-1] = defense_cost_limit
        right_bound = np.full(n_d + 1, np.inf)
        right_bound[-1] = np.inf
        linear_constraint = LinearConstraint(constraint_matrix, left_bound, right_bound)
        result = minimize(
            lambda td: self.evaluate(td, time_limit=time_limit, cost_limit=cost_limit),
            np.ones(n_d),
            method="trust-constr",
        )
        print(result.x)
        return result

    def export(
        self, file_name, simulation_number=10000, time_limit=1000, cost_limit=400
    ):
        self.file_name = file_name
        self.exporter = UppaalExporter(self.admdp, file_name)
        self.exporter.make_xml(simulation_number, time_limit, cost_limit)

    def verify(
        self, file_name, simulation_number=10000, time_limit=None, cost_limit=None
    ):
        self.exporter.set_queries(simulation_number, time_limit, cost_limit)
        command = f"{self.verifyta_prefix}verifyta -s {file_name}"
        process = subprocess.run(command.split(), capture_output=True, encoding="utf-8")
        output = process.stdout
        output = output.replace("\x1b[2K", "")
        output = output.replace("\x1b[K", "")
        output = output.replace("\n\n\n", "\n\n")
        formulas = output.split("\n\n")
        # Formula 9: strategy limited_cost = minE(time)[cost<=400]: <>AttackDefenseADMDP.goal
        strategy_found = "Formula is satisfied." in formulas[1]
        if strategy_found:
            # Formula 10: E[cost<={cost_limit};{simulation_number}](max: time) under limited_cost
            E_time = float(
                re.findall(
                    "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?",
                    formulas[2].split("\n")[2],
                )[1][0]
            )
            time_distribution_matches = re.findall(
                "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?", formulas[2].split("\n")[3]
            )
            time_distribution_low = float(time_distribution_matches[0][0])
            time_distribution_up = float(time_distribution_matches[1][0])
            time_distribution_hist = [int(m[0]) for m in time_distribution_matches[4:]]
            # Formula 11: E[cost<={cost_limit};{simulation_number}](max: cost) under limited_cost
            E_cost = float(
                re.findall(
                    "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?",
                    formulas[3].split("\n")[2],
                )[1][0]
            )
            cost_distribution_matches = re.findall(
                "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?", formulas[3].split("\n")[3]
            )
            cost_distribution_low = float(cost_distribution_matches[0][0])
            cost_distribution_up = float(cost_distribution_matches[1][0])
            cost_distribution_hist = [int(m[0]) for m in cost_distribution_matches[4:]]
            # Formula 11: Pr[cost<={cost_limit}](<>AttackDefenseADMDP.goal) under limited_cost
            P_success_inf = float(
                re.findall(
                    "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?",
                    formulas[4].split("\n")[2],
                )[1][0]
            )
            P_success_sup = float(
                re.findall(
                    "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?",
                    formulas[4].split("\n")[2],
                )[2][0]
            )
            P_success_confidence = float(
                re.findall(
                    "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?",
                    formulas[4].split("\n")[3],
                )[0][0]
            )
            return E_time, E_cost, P_success_inf, P_success_sup
        return None, None, None, None

    def evaluate(
        self, times, simulation_number=10000, time_limit=None, cost_limit=None
    ):
        if type(times) is not dict:
            keys = sorted([d.name for d in self.adg.defenses])
            times_dict = dict()
            for i in range(len(keys)):
                times_dict[keys[i]] = times[i]
            times = times_dict

        self.set_defense_times(times)
        self.verify(self.file_name, cost_limit=cost_limit)
        return score(*self.verify(self.file_name))
