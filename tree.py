from enum import Enum


class NodeType(Enum):
    GOAL = 1
    ATTACK = 2
    DEFENSE = 3


class OperationType(Enum):
    AND = 1
    OR = 2
    EDGE = 3


class Node:
    def __init__(
        self,
        parent=None,
        defense_child=None,
        attack_childern=None,
        goal_children=None,
        node_type=None,
        name=None,
    ):
        self.parent = parent
        self.defense_child = defense_child
        self.node_type = node_type
        if attack_childern:
            assert len(attack_childern) < 3
            self.attack_childern = attack_childern
        else:
            self.attack_childern = []

        if goal_children:
            assert len(goal_children) < 3
            self.goal_children = goal_children
        else:
            self.goal_children = []

        if name:
            self.name = name
        else:
            self.name = f"{self.node_type}:{id(self)}"

        assert len(self.goal_children) + len(self.attack_childern) < 3

    def __str__(self):
        return self.name

    def get_children(self, include_defense=False):
        if include_defense and self.defense_child:
            return self.attack_childern + self.goal_children + [self.defense_child]
        else:
            return self.attack_childern + self.goal_children

    def check_parent(self, parent):
        assert self.parent is None or self.parent == parent

    def set_parents(self, parent=None):
        self.check_parent(parent)
        self.parent = parent
        for child in self.get_children(include_defense=True):
            child.set_parents(self)

    def dfs(self, visited, include_defense=False):
        for child in self.get_children(include_defense=include_defense):
            visited.append(child)
            child.dfs(visited, include_defense=include_defense)


class Goal(Node):
    def __init__(
        self,
        children=None,
        defense_child=None,
        attack_childern=None,
        goal_children=None,
        operation_type=None,
        reset=False,
        name=None,
        parent=None,
    ):
        if children:
            assert defense_child is None
            assert attack_childern is None
            assert goal_children is None
            defense_child
            attack_childern = []
            goal_children = []
            for child in children:
                if child.node_type == NodeType.DEFENSE:
                    defense_child = child
                elif child.node_type == NodeType.ATTACK:
                    attack_childern.append(child)
                elif child.node_type == NodeType.GOAL:
                    goal_children.append(child)
                else:
                    raise Exception("Children without type")
        super().__init__(
            parent=parent,
            defense_child=defense_child,
            attack_childern=attack_childern,
            goal_children=goal_children,
            node_type=NodeType.GOAL,
            name=name,
        )
        self.operation_type = operation_type
        self.reset = reset


class Attack(Node):
    def __init__(
        self,
        completion_time=None,
        success_probability=None,
        activation_cost=None,
        name=None,
        parent=None,
    ):
        super().__init__(
            parent=parent,
            node_type=NodeType.ATTACK,
            name=name,
        )
        self.completion_time = completion_time
        self.success_probability = success_probability
        self.activation_cost = activation_cost


class Defense(Node):
    def __init__(
        self, period=None, success_probability=None, cost=None, name=None, parent=None
    ):
        super().__init__(
            parent=parent,
            node_type=NodeType.DEFENSE,
            name=name,
        )
        self.period = period
        self.success_probability = success_probability
        self.cost = cost


class Tree:
    def __init__(self, root):
        self.root = root
        self.root.set_parents()
        self.defense_periods = self.get_defense_periods(root)
        self.init_dfs()

    def get_defense_periods(self, root):
        defense_periods = []
        for node in self.dfs(include_defense=True):
            if node.node_type == NodeType.DEFENSE:
                defense_periods.append(node.period)
        return defense_periods

    def get_children(self, include_defense=False):
        return self.root.get_children(include_defense)

    def dfs(self, include_defense=False):
        nodes = []
        if self.root.node_type == NodeType.DEFENSE and not include_defense:
            return nodes
        self.root.dfs(nodes, include_defense=include_defense)
        return nodes

    def init_dfs(self):
        self.attacks = []
        self.defenses = []
        self.goals = []
        nodes = []
        self.root.dfs(nodes, include_defense=True)
        for node in nodes:
            if node.node_type == NodeType.ATTACK:
                self.attacks.append(node)
            elif node.node_type == NodeType.DEFENSE:
                self.defenses.append(node)
            elif node.node_type == NodeType.GOAL:
                self.goals.append(node)
        self.nodes = self.attacks + self.goals


if __name__ == "__main__":
    root = Goal(
        children=[
            Goal(
                children=[
                    Attack(
                        completion_time=10,
                        success_probability=0.5,
                        activation_cost=5,
                        name="a0",
                    ),
                    Attack(
                        completion_time=3, success_probability=0.2, activation_cost=1
                    ),
                ],
                operation_type=OperationType.OR,
                reset=False,
                name="g1",
            ),
            Attack(
                completion_time=7,
                success_probability=0.7,
                activation_cost=10,
                name="a2",
            ),
            Defense(period=5, success_probability=0.6, name="d0"),
        ],
        operation_type=OperationType.AND,
        reset=True,
        name="g0",
    )
    tree = Tree(root)
    print(
        f"parent of {tree.root}'s child {tree.get_children()[1]} is {tree.get_children()[1].parent}"
    )
