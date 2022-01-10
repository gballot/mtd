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

    def __le__(self, other):
        return self.name <= other.name

    def __ge__(self, other):
        return self.name >= other.name

    def __lt__(self, other):
        return self.name < other.name

    def __gt__(self, other):
        return self.name > other.name

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name

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
        name,
        operation_type,
        children=None,
        defense_child=None,
        attack_childern=None,
        goal_children=None,
        reset=False,
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
        completion_time,
        success_probability,
        name,
        activation_cost=None,
        proportional_cost=None,
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
        self.proportional_cost = proportional_cost


class Defense(Node):
    def __init__(self, period, success_probability, cost, name, parent=None):
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
        assert not root.reset
        self.root = root
        self.root.set_parents()
        self.defense_periods = self.get_defense_periods()
        self.init_dfs()

    def get_defense_periods(self):
        defense_periods = []
        for node in self.dfs(include_defense=True):
            if node.node_type == NodeType.DEFENSE:
                defense_periods.append(node.period)
        return defense_periods

    def get_children(self, include_defense=False):
        return self.root.get_children(include_defense)

    def dfs(self, include_defense=False):
        """Deep First Search."""
        nodes = []
        if self.root.node_type == NodeType.DEFENSE and not include_defense:
            return nodes
        self.root.dfs(nodes, include_defense=include_defense)
        return nodes

    def init_dfs(self):
        """Sould be used only at initialization to set self.attacks, self.defenses
        self.goals."""
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

    def reduce_activated_completed(self, activated, completed):
        """Uses the tree structure to determine the equivalence class of a
        set (A,B) of activated atomic attacks and completed nodes of the tree.
        The sets (A,B) and (A',B') are equivalent if they have the same upper
        non-reset nodes completed is the tree, and same reset nodes over the
        upper non rest-ones. Intuitiveley, (A,B) is equivalent to (A',B') if
        they have reached the same backup nodes and have the same atomic attacks
        activated that are not under a backup.

        This functions returns inplace the minimal representant (only backup
        nodes and other atomic attacks activated)."""
        # Add parents node that are completed
        fixed_point = False
        while not fixed_point:
            fixed_point = True
            for node in completed.copy():
                parent = node.parent
                if (
                    parent is not None
                    and parent not in completed
                    and (
                        parent.operation_type == OperationType.OR
                        or parent.operation_type == OperationType.EDGE
                        or (
                            parent.operation_type == OperationType.AND
                            and {n.name for n in parent.attack_childern}
                            <= {n.name for n in completed}
                            and {n.name for n in parent.goal_children}
                            <= {n.name for n in completed}
                        )
                    )
                ):
                    fixed_point = False
                    completed.append(parent)
        # Remove completed nodes that have a backup above
        for node in completed.copy():
            backup = node
            current = node
            while current.parent:
                current = current.parent
                if current in completed and not current.reset:
                    backup = current

            current = node
            while current is not backup:
                if current in completed:
                    completed.remove(current)
                current = current.parent
        # Remove activated nodes that have a backup above
        for node in activated.copy():
            if node in completed:
                activated.remove(node)
                break
            current = node
            while current.parent:
                current = current.parent
                if current in completed and not current.reset:
                    activated.remove(node)
                    break
