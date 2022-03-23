import sys

from admdp import ADMDP
from adg import ADG, Subgoal, Attack, Defense, OperationType
from uppaal import UppaalExporter
from optimizer import Optimizer

sys.setrecursionlimit(10 ** 6)

a_ad = Attack(
    completion_time=20,
    success_probability=1,
    activation_cost=10,
    proportional_cost=2,
    name="a_ad",
)
a_ic = Attack(
    completion_time=20,
    success_probability=1,
    activation_cost=10,
    proportional_cost=2,
    name="a_ic",
)
a_sp = Attack(
    completion_time=20,
    success_probability=1,
    activation_cost=10,
    proportional_cost=2,
    name="a_sp",
)
a_p = Attack(
    completion_time=20,
    success_probability=1,
    activation_cost=10,
    proportional_cost=2,
    name="a_p",
)
a_bf = Attack(
    completion_time=20,
    success_probability=1,
    activation_cost=10,
    proportional_cost=2,
    name="a_bf",
)
a_ss = Attack(
    completion_time=20,
    success_probability=1,
    activation_cost=10,
    proportional_cost=2,
    name="a_ss",
)
a_fue = Attack(
    completion_time=20,
    success_probability=1,
    activation_cost=10,
    proportional_cost=2,
    name="a_fue",
)

d_dk = Defense(period=15, success_probability=1, name="d_dk", cost=1)
d_cp = Defense(period=15, success_probability=1, name="d_cp", cost=1)
d_cc = Defense(period=15, success_probability=1, name="d_cc", cost=1)
d_dsr = Defense(period=15, success_probability=1, name="d_dsr", cost=1)

g_tc = Subgoal(
    children=[d_dk, a_ad, a_ic], operation_type=OperationType.AND, name="g_tc"
)
g_up = Subgoal(children=[d_cp, a_sp], operation_type=OperationType.AND, name="g_up")
g_th = Subgoal(children=[g_up, a_p], operation_type=OperationType.AND, name="g_th")
g_ac = Subgoal(
    children=[d_cc, a_bf, a_ss], operation_type=OperationType.AND, name="g_ac"
)
g_hs = Subgoal(children=[d_dsr, a_fue], operation_type=OperationType.AND, name="g_hs")
g_ts = Subgoal(children=[g_ac, g_hs], operation_type=OperationType.AND, name="g_ts")
g_1 = Subgoal(children=[g_tc, g_th], operation_type=OperationType.OR, name="g_1")
g_0 = Subgoal(children=[g_1, g_ts], operation_type=OperationType.OR, name="g_0")

adg = ADG(g_0)

optimizer = Optimizer(adg)
optimizer.export("output.xml", simulation_number=10000, cost_limit=400)

# Default defense time
E_time, E_cost, P_success_inf, P_success_sup = optimizer.verify(
    "output.xml", time_limit=1000
)
print(
    f"With time limit={100} for the attack:\nE(time) = {E_time}\nE(cost) = {E_cost}\nP(success) in [{P_success_inf}, {P_success_sup}]\n"
)
E_time, E_cost, P_success_inf, P_success_sup = optimizer.verify(
    "output.xml", time_limit=1000
)
print(
    f"With time limit={100} for the attack:\nE(time) = {E_time}\nE(cost) = {E_cost}\nP(success) in [{P_success_inf}, {P_success_sup}]\n"
)
E_time, E_cost, P_success_inf, P_success_sup = optimizer.verify(
    "output.xml", time_limit=20
)
print(
    f"With time limit={20} for the attack:\nE(time) = {E_time}\nE(cost) = {E_cost}\nP(success) in [{P_success_inf}, {P_success_sup}]\n"
)
E_time, E_cost, P_success_inf, P_success_sup = optimizer.verify(
    "output.xml", time_limit=10
)
print(
    f"With time limit={10} for the attack:\nE(time) = {E_time}\nE(cost) = {E_cost}\nP(success) in [{P_success_inf}, {P_success_sup}]\n"
)
# Set new defense time
optimizer.set_defense_times({"d0": 100})
print("New defense time: d0-> 100")
E_time, E_cost, P_success_inf, P_success_sup = optimizer.verify(
    "output.xml", time_limit=1000
)
print(
    f"With time limit={100} for the attack:\nE(time) = {E_time}\nE(cost) = {E_cost}\nP(success) in [{P_success_inf}, {P_success_sup}]\n"
)
E_time, E_cost, P_success_inf, P_success_sup = optimizer.verify(
    "output.xml", time_limit=100
)
print(
    f"With time limit={100} for the attack:\nE(time) = {E_time}\nE(cost) = {E_cost}\nP(success) in [{P_success_inf}, {P_success_sup}]\n"
)
E_time, E_cost, P_success_inf, P_success_sup = optimizer.verify(
    "output.xml", time_limit=20
)
print(
    f"With time limit={20} for the attack:\nE(time) = {E_time}\nE(cost) = {E_cost}\nP(success) in [{P_success_inf}, {P_success_sup}]\n"
)
E_time, E_cost, P_success_inf, P_success_sup = optimizer.verify(
    "output.xml", time_limit=10
)
print(
    f"With time limit={10} for the attack:\nE(time) = {E_time}\nE(cost) = {E_cost}\nP(success) in [{P_success_inf}, {P_success_sup}]\n"
)
