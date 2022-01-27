import sys

from graph import Graph
from tree import Tree, Goal, Attack, Defense, OperationType
from uppaal import UppaalExporter
from optimizer import Optimizer

sys.setrecursionlimit(10 ** 6)

a0 = Attack(completion_time=20, success_probability=1, activation_cost=10, name="a0")
a1 = Attack(completion_time=10, success_probability=0.5, proportional_cost=2, name="a1")

d0 = Defense(period=15, success_probability=1, name="d0", cost=1)

g0 = Goal(
    children=[d0, a0, a1], operation_type=OperationType.OR, reset=False, name="g0"
)

tree = Tree(g0)

optimizer = Optimizer(tree)
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
