import sys

from admdp import ADMDP
from adg import ADG, Subgoal, Attack, Defense, OperationType
from uppaal import UppaalExporter
from optimizer import Optimizer

sys.setrecursionlimit(10 ** 6)

d_0 = Defense(period=10, success_probability=0.5, name="d_0", cost=1)

a_0 = Attack(
    completion_time=100,
    success_probability=0.8,
    activation_cost=1,
    proportional_cost=1,
    defenses=[d_0],
    name="a_0",
)
a_1 = Attack(
    completion_time=10,
    success_probability=0.9,
    activation_cost=1000,
    proportional_cost=1,
    name="a_1",
)

g_0 = Subgoal(children=[a_0, a_1], operation_type=OperationType.OR, name="g_0")

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
