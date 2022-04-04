import sys

from admdp import ADMDP
from adg import ADG, Subgoal, Attack, Defense, OperationType
from uppaal import UppaalExporter
from optimizer import Optimizer

sys.setrecursionlimit(10 ** 6)

# Defenses
d_dk = Defense(period=1000, success_probability=1, name="d_dk", cost=1)
d_cp = Defense(period=1000, success_probability=1, name="d_cp", cost=1)
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
    completion_time=3,
    success_probability=1,
    activation_cost=200,
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

g_tc = Subgoal(
    children=[a_ad, a_ic], operation_type=OperationType.AND, name="g_tc"
)
g_up = Subgoal(children=[d_cp, a_sp], operation_type=OperationType.AND, name="g_up")
g_ac = Subgoal(
    children=[d_cc, a_bf, a_ss], operation_type=OperationType.OR, name="g_ac"
)
g_th = Subgoal(children=[g_up, a_p, g_ac], operation_type=OperationType.AND, name="g_th")
g_hs = Subgoal(children=[a_fue], operation_type=OperationType.AND, name="g_hs")
g_ts = Subgoal(children=[g_ac, g_hs], operation_type=OperationType.AND, name="g_ts")
g_0 = Subgoal(children=[g_tc, g_th, g_ts], operation_type=OperationType.OR, name="g_0")

adg = ADG(g_0)

optimizer = Optimizer(adg)
optimizer.export("output.xml", simulation_number=10000, cost_limit=400)

# Default defense time
for time_limit, cost_limit in [(10000,None), (None, 10000), (500,1000)]:
    result = optimizer.verify(
        "output.xml", time_limit=time_limit, cost_limit=cost_limit
    )
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
        E_time, E_cost, P_success_inf, P_success_sup = result[0]
        print(
            f"""With time limit={time_limit}, cost limit={cost_limit}, the cheapest attack strategy gives:
            E(time) = {E_time}
            E(cost) = {E_cost}
            P(success) in [{P_success_inf}, {P_success_sup}]"""
        )
        E_time, E_cost, P_success_inf, P_success_sup = result[1]
        print(
            f"""With time limit={time_limit}, cost limit={cost_limit}, the fastest attack strategy gives:
            E(time) = {E_time}
            E(cost) = {E_cost}
            P(success) in [{P_success_inf}, {P_success_sup}]"""
        )
    else:
        E_time, E_cost, P_success_inf, P_success_sup = result
        print(
            f"""Without limits, the fastest attack strategy gives:
            E(time) = {E_time}
            E(cost) = {E_cost}
            P(success) in [{P_success_inf}, {P_success_sup}]"""
        )

# Set new defense time
new_defenses = {"d_dsr": 720}
optimizer.set_defense_times(new_defenses)
print(f"New defense time: {str(new_defenses)}")
for time_limit, cost_limit in [(10000,None), (None, 10000)]:
    result = optimizer.verify(
        "output.xml", time_limit=time_limit, cost_limit=cost_limit
    )
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
        E_time, E_cost, P_success_inf, P_success_sup = result[0]
        print(
            f"""With time limit={time_limit}, cost limit={cost_limit}, the cheapest attack strategy gives:
            E(time) = {E_time}
            E(cost) = {E_cost}
            P(success) in [{P_success_inf}, {P_success_sup}]"""
        )
        E_time, E_cost, P_success_inf, P_success_sup = result[1]
        print(
            f"""With time limit={time_limit}, cost limit={cost_limit}, the fastest attack strategy gives:
            E(time) = {E_time}
            E(cost) = {E_cost}
            P(success) in [{P_success_inf}, {P_success_sup}]"""
        )
    else:
        E_time, E_cost, P_success_inf, P_success_sup = result
        print(
            f"""Without limits, the fastest attack strategy gives:
            E(time) = {E_time}
            E(cost) = {E_cost}
            P(success) in [{P_success_inf}, {P_success_sup}]"""
        )
