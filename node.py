from enum import Enum


class NodeType(Enum):
    GOAL = 1
    ATTACK = 2
    DEFENSE = 3


class Node:
    def __init__(
        self,
        parent=None,
        defense_child=None,
        attack_childern=None,
        goal_children=None,
        node_type=None,
    ):
        self.parent = parent
        self.defense_child = defense_child
        self.node_type = node_type
        if attack_childern is not None:
            self.attack_childern = attack_childern
        else:
            self.attack_childern = []

        if goal_children is not None:
            self.goal_children = goal_children
        else:
            self.goal_children = []

    def get_children(self):
        return attack_childern + goal_children



class Goal(Node):
    def __init__(
        self, parent=None, defense_child=None, attack_childern=None, goal_children=None, operation_type=None, reset=None
    ):
        __init__(
            self,
            parent=parent,
            defense_child=defense_child,
            attack_childern=attack_childern,
            goal_children=goal_children,
            node_type=NodeType.GOAL,
        )
        self.operation_type = operation_type
        self.reset = reset

class Attack(Node):
    def __init__(self, parent=None, completion_time=None, success_probability=None, activation_cost=None):
        __init__(
            self,
            parent=parent,
            node_type=NodeType.ATTACK,
        )
        self.completion_time = completion_time
        self.success_probability = success_probability
        self.activation_cost = activation_cost

class Defense(Node):
    def __init__(self, parent=None, period=None, success_probability=None, cost):
        __init__(
            self,
            parent=parent,
            node_type=NodeType.DEFENSE,
        )
        self.period = period
        self.success_probability = success_probability
        self.cost = cost

