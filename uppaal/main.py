import sys

from admdp import ADMDP
from adg import ADG, Subgoal, Attack, Defense, OperationType
from uppaal import UppaalExporter
from optimizer import Optimizer
import numpy as np
import os
import time
import subprocess

# Limits set
time_limits = [
    10000,
    2000,
    1800,
    1600,
    1500,
    1400,
    1500,
    1400,
    1300,
    1200,
    1100,
    1000,
    900,
    800,
    700,
    600,
    500,
    400,
    300,
    250,
    200,
    150,
    100,
    75,
    50,
    25,
    20,
    15,
    10,
    7,
    5,
    3,
    2,
    1,
]

cost_limits = [
    10000,
    4000,
    2000,
    1900,
    1800,
    1700,
    1600,
    1500,
    1400,
    1300,
    1200,
    1100,
    900,
    800,
    700,
    600,
    500,
    450,
    400,
    350,
    300,
    250,
    200,
    175,
    150,
    125,
    100,
    75,
    50,
    30,
    25,
    20,
    15,
    10,
    5,
]


def build_adg():
    # Defenses
    d_dk = Defense(period=1000, success_probability=1, name="d_dk", cost=1)
    d_cp = Defense(period=1000, success_probability=0.5, name="d_cp", cost=1)
    d_cc = Defense(period=1000, success_probability=1, name="d_cc", cost=1)
    d_dsr = Defense(period=1000, success_probability=1, name="d_dsr", cost=1)

    # Atomic attacks
    a_ad = Attack(
        completion_time=8,
        success_probability=0.5,
        activation_cost=100,
        proportional_cost=200,
        defenses=[d_dk],
        name="a_ad",
    )
    a_ic = Attack(
        completion_time=4,
        success_probability=0.3,
        activation_cost=0,
        proportional_cost=500,
        name="a_ic",
    )
    a_sp = Attack(
        completion_time=240,
        success_probability=0.8,
        activation_cost=20,
        proportional_cost=0,
        defenses=[d_cp],
        name="a_sp",
    )
    a_p = Attack(
        completion_time=1,
        success_probability=1,
        activation_cost=0,
        proportional_cost=200,
        name="a_p",
    )
    a_bf = Attack(
        completion_time=1,
        success_probability=0.001,
        activation_cost=0,
        proportional_cost=1,
        defenses=[d_cc],
        name="a_bf",
    )
    a_ss = Attack(
        completion_time=30,
        success_probability=0.2,
        activation_cost=10,
        proportional_cost=0,
        defenses=[d_cc],
        name="a_ss",
    )
    a_fue = Attack(
        completion_time=720,
        success_probability=0.8,
        activation_cost=10,
        proportional_cost=0,
        defenses=[d_dsr],
        name="a_fue",
    )

    # Subgoals
    g_tc = Subgoal(children=[a_ad, a_ic], operation_type=OperationType.AND, name="g_tc")
    g_up = Subgoal(children=[d_cp, a_sp], operation_type=OperationType.AND, name="g_up")
    g_ac = Subgoal(
        children=[d_cc, a_bf, a_ss], operation_type=OperationType.OR, name="g_ac"
    )
    g_th = Subgoal(
        children=[g_up, a_p, g_ac], operation_type=OperationType.AND, name="g_th"
    )
    g_hs = Subgoal(children=[a_fue], operation_type=OperationType.AND, name="g_hs")
    g_ts = Subgoal(children=[g_ac, g_hs], operation_type=OperationType.AND, name="g_ts")
    g_0 = Subgoal(
        children=[g_tc, g_th, g_ts], operation_type=OperationType.OR, name="g_0"
    )

    return ADG(g_0)


def build_adg_simple():
    # Defenses
    d_cp = Defense(period=1000, success_probability=0.5, name="d_cp", cost=1)
    d_cc = Defense(period=1000, success_probability=1, name="d_cc", cost=1)

    # Atomic attacks
    a_sp = Attack(
        completion_time=240,
        success_probability=1,
        activation_cost=20,
        proportional_cost=0,
        defenses=[d_cp],
        name="a_sp",
    )
    a_p = Attack(
        completion_time=1,
        success_probability=1,
        activation_cost=0,
        proportional_cost=200,
        name="a_p",
    )
    a_bf = Attack(
        completion_time=1,
        success_probability=0.001,
        activation_cost=0,
        proportional_cost=1,
        defenses=[d_cc],
        name="a_bf",
    )
    a_ss = Attack(
        completion_time=30,
        success_probability=0.2,
        activation_cost=10,
        proportional_cost=0,
        defenses=[d_cc],
        name="a_ss",
    )

    # Subgoals
    g_up = Subgoal(children=[d_cp, a_sp], operation_type=OperationType.AND, name="g_up")
    g_ac = Subgoal(
        children=[d_cc, a_bf, a_ss], operation_type=OperationType.OR, name="g_ac"
    )
    g_th = Subgoal(
        children=[g_up, a_p, g_ac], operation_type=OperationType.AND, name="g_th"
    )

    return ADG(g_th)


def build_adg_very_simple():
    # Defenses
    d_cc = Defense(period=1000, success_probability=1, name="d_cc", cost=1)

    # Atomic attacks
    a_bf = Attack(
        completion_time=1,
        success_probability=0.001,
        activation_cost=0,
        proportional_cost=1,
        defenses=[d_cc],
        name="a_bf",
    )
    a_ss = Attack(
        completion_time=30,
        success_probability=0.2,
        activation_cost=10,
        proportional_cost=0,
        defenses=[d_cc],
        name="a_ss",
    )

    # Subgoals
    g_ac = Subgoal(
        children=[a_bf, a_ss], operation_type=OperationType.OR, name="g_ac"
    )

    return ADG(g_ac)


def print_results(
    optimizer, time_limit, cost_limit, model_name, csv=False, output=None, simulation_number=10000
):
    adg = optimizer.admdp.adg
    result = optimizer.verify(model_name, simulation_number=simulation_number, time_limit=time_limit, cost_limit=cost_limit)
    if csv:
        (
            E_time,
            E_cost,
            (P_success_inf, P_success_sup, P_success_confidence),
            (time_distribution_low, time_distribution_up, time_distribution_hist),
            (cost_distribution_low, cost_distribution_up, cost_distribution_hist),
        ) = result
        line = f"{time_limit}, {cost_limit}, {E_time}, {E_cost}, {P_success_inf}, {P_success_sup}, {P_success_confidence}, {time_distribution_low}, {time_distribution_up}, {'; '.join(map(str, time_distribution_hist)) if time_distribution_hist else None}, {cost_distribution_low}, {cost_distribution_up}, {'; '.join(map(str, cost_distribution_hist)) if cost_distribution_hist else None}, {', '.join(map(str, adg.defense_periods + adg.defense_proba +adg.attack_times + adg.attack_proba + adg.attack_costs + adg.attack_costrates))}"
        if output:
            with open(output, "a") as f:
                f.write(line + "\n")
                f.flush()
        else:
            print(line)
    else:
        if cost_limit is None:
            E_time, E_cost, P_success_inf, P_success_sup = result
            print(
                f"""With time limit={time_limit}, the cheapest attack strategy gives:
                E(time) = {E_time}
                E(cost) = {E_cost}
                P(success) in [{P_success_inf}, {P_success_sup}]"""
            )
        elif time_limit is None:
            E_time, E_cost, P_success_inf, P_success_sup = result
            print(
                f"""With cost limit={cost_limit}, the fastest attack strategy gives:
                E(time) = {E_time}
                E(cost) = {E_cost}
                P(success) in [{P_success_inf}, {P_success_sup}]"""
            )
        elif time_limit is not None and cost_limit is not None:
            print("TODO: not implemented")
            # E_time, E_cost, P_success_inf, P_success_sup = result[0]
            # print(
            #    f"""With time limit={time_limit}, cost limit={cost_limit}, the cheapest attack strategy gives:
            #    E(time) = {E_time}
            #    E(cost) = {E_cost}
            #    P(success) in [{P_success_inf}, {P_success_sup}]"""
            # )
            # E_time, E_cost, P_success_inf, P_success_sup = result[1]
            # print(
            #    f"""With time limit={time_limit}, cost limit={cost_limit}, the fastest attack strategy gives:
            #    E(time) = {E_time}
            #    E(cost) = {E_cost}
            #    P(success) in [{P_success_inf}, {P_success_sup}]"""
            # )
        else:
            E_time, E_cost, P_success_inf, P_success_sup = result
            print(
                f"""Without limits, the fastest attack strategy gives:
                E(time) = {E_time}
                E(cost) = {E_cost}
                P(success) in [{P_success_inf}, {P_success_sup}]"""
            )

    return E_time, E_cost, P_success_sup


def explore_limits(optimizer, csv, model_name, output):
    timeout_series = 0
    time_limit = 10000
    while time_limit is not None:
        print(f"time limit {time_limit}")
        try:
            E_time, E_cost, P_success_sup = print_results(
                optimizer,
                time_limit=time_limit,
                cost_limit=None,
                model_name=model_name,
                csv=csv,
                output=output,
            )
        except subprocess.TimeoutExpired:
            timeout_series += 1
            print(f"time limit {time_limit} -> timeout {timeout_series}")
            E_time = time_limit  # To continue the loop
            if timeout_series >= 3:
                break
        else:
            timeout_series = 0
        time_limit = (
            int(
                max(
                    min(
                        [
                            min([E_time, time_limit]) * 0.99,
                            min([E_time, time_limit]) - 5,
                        ]
                    ),
                    1,
                )
            )
            if E_time is not None
            else None
        )

    timeout_series = 0
    cost_limit = 10000
    while cost_limit is not None:
        print(f"cost_limit {cost_limit}")
        try:
            E_time, E_cost, P_success_sup = print_results(
                optimizer,
                time_limit=None,
                cost_limit=cost_limit,
                model_name=model_name,
                csv=csv,
                output=output,
            )
        except subprocess.TimeoutExpired:
            timeout_series += 1
            print(f"time limit {time_limit} -> timeout {timeout_series}")
            E_cost = cost_limit  # To continue the loop
            if timeout_series >= 3:
                break
        else:
            timeout_series = 0
        cost_limit = (
            int(
                max(
                    min(
                        [
                            min([E_cost, cost_limit]) * 0.99,
                            min([E_cost, cost_limit]) - 5,
                        ]
                    ),
                    1,
                )
            )
            if E_cost is not None
            else None
        )


def list_limits(optimizer, csv, model_name, output, time_limits, cost_limits):
    timeout_series = 0
    for time_limit in time_limits:
        print(f"time limit {time_limit}")
        try:
            E_time, E_cost, P_success_sup = print_results(
                optimizer,
                time_limit=time_limit,
                cost_limit=None,
                model_name=model_name,
                csv=csv,
                output=output,
            )
        except subprocess.TimeoutExpired:
            timeout_series += 1
            print(f"time limit {time_limit} -> timeout {timeout_series}")
            if timeout_series >= 3:
                break
            else:
                continue
        else:
            timeout_series = 0
        if E_cost is None:
            break
    timeout_series = 0
    for cost_limit in cost_limits:
        print(f"cost_limit {cost_limit}")
        try:
            E_time, E_cost, P_success_sup = print_results(
                optimizer,
                time_limit=None,
                cost_limit=cost_limit,
                model_name=model_name,
                csv=csv,
                output=output,
            )
        except subprocess.TimeoutExpired:
            timeout_series += 1
            print(f"time limit {time_limit} -> timeout {timeout_series}")
            if timeout_series >= 3:
                break
            else:
                continue
        else:
            timeout_series = 0
        if E_time is None:
            break


############
### MAIN ###
############

if __name__ == "__main__":
    csv = True
    explore = False
    nickname = sys.argv[1] if len(sys.argv) > 1 else ""
    dirname = f"experiment-{time.strftime('%Y-%m-%d_%H-%M-%S')}{nickname}"
    os.makedirs(dirname)
    output = f"{dirname}/results.csv"
    model_name = f"{dirname}/output.xml"

    print(f"""csv = {csv}
explore = {explore}
output = {output}
model_name = {model_name}
""")
    sys.setrecursionlimit(10 ** 6)

    adg = build_adg()

    optimizer = Optimizer(adg)
    optimizer.export(model_name, simulation_number=10000, cost_limit=400)

    if csv:
        defense_names = [defense.name for defense in adg.defenses]
        attack_names = [attack.name for attack in adg.attacks]
        with open(output, "a") as f:
            f.write(
                f"time_limit, cost_limit, E_time, E_cost, P_success_inf, P_success_sup, P_success_confidence, time_distribution_low, time_distribution_up, time_distribution_hist, cost_distribution_low, cost_distribution_up, cost_distribution_hist, t_{', t_'.join(defense_names)},  p_{', p_'.join(defense_names)}, t_{', t_'.join(attack_names)}, p_{', p_'.join(attack_names)}, w_{', w_'.join(attack_names)}, wp_{', wp_'.join(attack_names)}\n"
            )
            f.flush()

    # Play with other defenses
    for new_defenses in [
        set(),
        {"d_dsr": 720},
        {"d_dsr": 719},
        {"d_dsr": 719, "d_dk": 2},
        {"d_dsr": 719, "d_dk": 1},
        {"d_dsr": 719, "d_dk": 1, "d_cc": 200},
        {"d_dsr": 719, "d_dk": 1, "d_cc": 100},
        {"d_dsr": 719, "d_dk": 1, "d_cc": 80},
        {"d_dsr": 719, "d_dk": 1, "d_cc": 50},
        {"d_dsr": 719, "d_dk": 1, "d_cc": 20},
        {"d_dsr": 719, "d_dk": 1, "d_cp": 800},
        {"d_dsr": 719, "d_dk": 1, "d_cp": 400},
        {"d_dsr": 719, "d_dk": 1, "d_cp": 200},
        {"d_dsr": 719, "d_dk": 1, "d_cp": 100},
        {"d_dsr": 719, "d_dk": 1, "d_cp": 50},
    ]:
        pass

    for t_dsr in [2000, 1000, 500, 250]:
        for t_dk in [40, 20, 10, 5]:
            for t_cc in [1600, 800, 400, 200]:
                for t_cp in [800, 400, 200, 100]:
                    if t_dsr / 250 + t_dk / 5 + t_cc / 200 + t_cp / 100 != 8:
                        continue

                    new_defenses = {
                            "d_dsr": t_dsr,
                            "d_dk": t_dk,
                            "d_cc": t_cc,
                            "d_cp": t_cp,
                            }

                    optimizer.set_defense_times(new_defenses)
                    print(f"Defense periods: {optimizer.admdp.adg.defense_periods}")
                    if explore:
                        explore_limits(optimizer, csv=csv, model_name=model_name, output=output)
                    else:
                        list_limits(
                            optimizer,
                            csv=csv,
                            model_name=model_name,
                            output=output,
                            time_limits=time_limits,
                            cost_limits=cost_limits,
                        )
