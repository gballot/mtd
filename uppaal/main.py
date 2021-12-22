from graph import Graph
from tree import Tree, Goal, Attack, Defense, OperationType
from uppaal import UppaalExporter

a0 = Attack(
    completion_time=100,
    success_probability=0.66,
    activation_cost=10,
    proportional_cost=1,
    name="a0",
)
a1 = Attack(completion_time=10, success_probability=0.1, activation_cost=1, name="a1")
a2 = Attack(completion_time=10, success_probability=0.5, activation_cost=300, name="a2")
a3 = Attack(completion_time=700, success_probability=0.95, activation_cost=1, name="a3")
a4 = Attack(completion_time=200, success_probability=0.75, activation_cost=6, name="a4")
a5 = Attack(completion_time=20, success_probability=0.66, activation_cost=1, name="a5")
a6 = Attack(completion_time=100, success_probability=0.9, activation_cost=1, name="a6")
a7 = Attack(completion_time=30, success_probability=0.1, activation_cost=1, name="a7")

d0 = Defense(period=50, success_probability=0.6, name="d0", cost=1)
d1 = Defense(period=40, success_probability=0.8, name="d1", cost=1)
d2 = Defense(period=40, success_probability=0.3, name="d2", cost=1)
d3 = Defense(period=20, success_probability=0.7, name="d3", cost=1)

g0 = Goal(
    children=[d0, a0, a1], operation_type=OperationType.AND, reset=False, name="g0"
)
g1 = Goal(children=[g0, a2], operation_type=OperationType.OR, name="g1")
g7 = Goal(children=[d3, a7], operation_type=OperationType.AND, reset=False, name="g7")
g6 = Goal(children=[a5, a6], operation_type=OperationType.AND, name="g6")
g5 = Goal(children=[g6, g7], operation_type=OperationType.AND, name="g5")
g4 = Goal(children=[d2, a4, g5], operation_type=OperationType.OR, reset=True, name="g4")
g3 = Goal(children=[d1, g4], operation_type=OperationType.EDGE, reset=True, name="g3")
g2 = Goal(children=[a3, g3], operation_type=OperationType.OR, name="g2")
gt = Goal(children=[g1, g2], operation_type=OperationType.OR, name="gt")

# gtest = Goal(children=[a1, a0], operation_type=OperationType.OR, name="gt")

tree = Tree(gt)
graph = Graph(tree)
print(graph)
uppaal = UppaalExporter(graph, "output.xml")
uppaal.make_xml()
