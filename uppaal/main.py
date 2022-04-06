import sys

from admdp import ADMDP
from adg import ADG, Subgoal, Attack, Defense, OperationType
from uppaal import UppaalExporter
from optimizer import Optimizer
import numpy as np


def build_adg():
    # Defenses
    d_dk = Defense(period=1000, success_probability=1, name="d_dk", cost=1)
    d_cp = Defense(period=1000, success_probability=0.5, name="d_cp", cost=1)
    d_cc = Defense(period=1000, success_probability=1, name="d_cc", cost=1)
    d_dsr = Defense(period=1000, success_probability=1, name="d_dsr", cost=1)

    # Atomic attacks
    a_ad = Attack(
        completion_time=1,
        success_probability=1,
        activation_cost=100,
        proportional_cost=200,
        defenses=[d_dk],
        name="a_ad",
    )
    a_ic = Attack(
        completion_time=2,
        success_probability=1,
        activation_cost=0,
        proportional_cost=500,
        name="a_ic",
    )
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
    a_fue = Attack(
        completion_time=720,
        success_probability=1,
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


def print_results(optimizer, time_limit, cost_limit, csv=False, output=None):
    adg = optimizer.admdp.adg
    result = optimizer.verify(
        "output.xml", time_limit=time_limit, cost_limit=cost_limit
    )
    if csv:
        E_time, E_cost, (P_success_inf, P_success_sup, P_success_confidence), (time_distribution_low, time_distribution_up, time_distribution_hist), (cost_distribution_low, cost_distribution_up, cost_distribution_hist) = result
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
            #E_time, E_cost, P_success_inf, P_success_sup = result[0]
            #print(
            #    f"""With time limit={time_limit}, cost limit={cost_limit}, the cheapest attack strategy gives:
            #    E(time) = {E_time}
            #    E(cost) = {E_cost}
            #    P(success) in [{P_success_inf}, {P_success_sup}]"""
            #)
            #E_time, E_cost, P_success_inf, P_success_sup = result[1]
            #print(
            #    f"""With time limit={time_limit}, cost limit={cost_limit}, the fastest attack strategy gives:
            #    E(time) = {E_time}
            #    E(cost) = {E_cost}
            #    P(success) in [{P_success_inf}, {P_success_sup}]"""
            #)
        else:
            E_time, E_cost, P_success_inf, P_success_sup = result
            print(
                f"""Without limits, the fastest attack strategy gives:
                E(time) = {E_time}
                E(cost) = {E_cost}
                P(success) in [{P_success_inf}, {P_success_sup}]"""
            )

    return E_time, E_cost, P_success_sup


def explore_limits(optimizer, csv, output):
    time_limit = 100000
    while time_limit is not None:
        E_time, E_cost, P_success_sup, = print_results(optimizer, time_limit, None, csv, output)
        time_limit = np.floor(max(min([E_time * 0.99, E_time - 5]), 1)) if E_time is not None else None


    cost_limit = 100000
    while cost_limit is not None:
        E_time, E_cost, P_success_sup, = print_results(optimizer, None, cost_limit, csv, output)
        cost_limit = np.floor(max(min([E_cost * 0.99, E_cost - 5]), 1)) if E_cost is not None else None

if __name__ == "__main__":
    csv = True
    output = "results.csv"
    sys.setrecursionlimit(10 ** 6)

    adg = build_adg()

    optimizer = Optimizer(adg)
    optimizer.export("output.xml", simulation_number=10000, cost_limit=400)

    if csv:
        defense_names = [defense.name for defense in adg.defenses]
        attack_names = [attack.name for attack in adg.attacks]
        with open(output, "a") as f:
            f.write(
                f"time_limit, cost_limit, E_time, E_cost, P_success_inf, P_success_sup, P_success_confidence, time_distribution_low, time_distribution_up, time_distribution_hist, cost_distribution_low, cost_distribution_up, cost_distribution_hist, t_{', t_'.join(defense_names)},  p_{', p_'.join(defense_names)}, t_{', t_'.join(attack_names)}, p_{', p_'.join(attack_names)}, w_{', w_'.join(attack_names)}, wp_{', wp_'.join(attack_names)}\n"
            )
            f.flush()

    # Limits set
    limits = [
        (10000, None),
        (2000, None),
        (1800, None),
        (1600, None),
        (1500, None),
        (1400, None),
        (1500, None),
        (1400, None),
        (1300, None),
        (1200, None),
        (1100, None),
        (1000, None),
        (900, None),
        (800, None),
        (700, None),
        (600, None),
        (500, None),
        (400, None),
        (300, None),
        (250, None),
        (200, None),
        (150, None),
        (100, None),
        (75, None),
        (50, None),
        (25, None),
        (20, None),
        (15, None),
        (10, None),
        (7, None),
        (5, None),
        (3, None),
        (2, None),
        (1, None),
        (None, 10000),
        (None, 4000),
        (None, 2000),
        (None, 1900),
        (None, 1800),
        (None, 1700),
        (None, 1600),
        (None, 1500),
        (None, 1400),
        (None, 1300),
        (None, 1200),
        (None, 1100),
        (None, 900),
        (None, 800),
        (None, 700),
        (None, 600),
        (None, 500),
        (None, 450),
        (None, 400),
        (None, 350),
        (None, 300),
        (None, 250),
        (None, 200),
        (None, 175),
        (None, 150),
        (None, 125),
        (None, 100),
        (None, 75),
        (None, 50),
        (None, 30),
        (None, 25),
        (None, 20),
        (None, 15),
        (None, 10),
        (None, 5),
    ]


    # Default defense time
    explore_limits(optimizer, csv, output)

    # Set new defense time to compromise the cheapest attack
    new_defenses = {"d_dsr": 720}
    optimizer.set_defense_times(new_defenses)
    if not csv:
        print(f"New defense time: {str(new_defenses)}")
    explore_limits(optimizer, csv, output)

    new_defenses = {"d_dsr": 719}
    optimizer.set_defense_times(new_defenses)
    explore_limits(optimizer, csv, output)

    # Set new defense time to compromise the fastest attack
    new_defenses = {"d_dsr": 719, "d_dk": 2}
    optimizer.set_defense_times(new_defenses)
    explore_limits(optimizer, csv, output)

    new_defenses = {"d_dsr": 719, "d_dk": 1}
    optimizer.set_defense_times(new_defenses)
    explore_limits(optimizer, csv, output)

    # Play with other defenses
    for new_defenses in [
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
        optimizer.set_defense_times(new_defenses)
        explore_limits(optimizer, csv, output)
