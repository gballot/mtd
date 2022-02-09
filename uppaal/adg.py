from enum import Enum


class NodeType(Enum):
    GOAL = 1
    ATTACK = 2
    DEFENSE = 3


class OperationType(Enum):
    AND = 1
    OR = 2


class Node:
    def __init__(
        self,
        parents=None,
        defenses=None,
        attack_childern=None,
        goal_children=None,
        node_type=None,
        name=None,
    ):
        self.parents = parents
        self.defenses = defenses
        self.node_type = node_type
        if attack_childern:
            self.attack_childern = attack_childern
        else:
            self.attack_childern = []

        if goal_children:
            self.goal_children = goal_children
        else:
            self.goal_children = []

        if name:
            self.name = name
        else:
            self.name = f"{self.node_type}:{id(self)}"

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

    def get_children(self):
        return self.attack_childern + self.goal_children

    def check_parents(self, parents):
        assert self.parents is None or set(self.parents) == set(parents)

    def set_parents(self, parents=None):
        self.check_parents(parents)
        self.parents = parents
        for child in self.get_children():
            child.set_parents(self)

    def dfs(self, visited):
        for child in self.get_children():
            visited.add(child)
            child.dfs(visited)

    def dfs_parents(self, visited):
        for parent in self.parents:
            visited.add(parent)
            parent.dfs_parents(visited)

    def dfs_defenses(self, defenses):
        defenses.add(self.defenses)
        for child in self.get_children():
            child.dfs_defenses(defenses)


class Goal(Node):
    def __init__(
        self,
        name,
        operation_type,
        children=None,
        defenses=None,
        attack_childern=None,
        goal_children=None,
        parents=None,
    ):
        if children:
            assert defenses is None
            assert attack_childern is None
            assert goal_children is None
            defenses = []
            attack_childern = []
            goal_children = []
            for child in children:
                if child.node_type == NodeType.DEFENSE:
                    defenses.append(child)
                elif child.node_type == NodeType.ATTACK:
                    attack_childern.append(child)
                elif child.node_type == NodeType.GOAL:
                    goal_children.append(child)
                else:
                    raise Exception("Children without type")
        super().__init__(
            parent=parent,
            defenses=defenses,
            attack_childern=attack_childern,
            goal_children=goal_children,
            node_type=NodeType.GOAL,
            name=name,
        )
        self.operation_type = operation_type


class Attack(Node):
    def __init__(
        self,
        completion_time,
        success_probability,
        name,
        activation_cost=None,
        proportional_cost=None,
        parents=None,
    ):
        super().__init__(
            parents=parents,
            node_type=NodeType.ATTACK,
            name=name,
        )
        self.completion_time = completion_time
        self.success_probability = success_probability
        self.activation_cost = activation_cost
        self.proportional_cost = proportional_cost


class Defense(Node):
    def __init__(self, period, success_probability, cost, name, parents=None):
        super().__init__(
            parents=parents,
            node_type=NodeType.DEFENSE,
            name=name,
        )
        self.period = period
        self.success_probability = success_probability
        self.cost = cost


class Tree:
    def __init__(self, root):
        assert not root.defenses
        self.root = root
        self.root.set_parents()
        self.init_dfs()

    def get_children(self, include_defense=False):
        return self.root.get_children(include_defense)

    def init_dfs(self):
        """Sould be used only at initialization to set self.attacks, self.defenses
        self.goals."""
        self.attacks = {}
        self.defenses = {}
        self.goals = {}
        nodes = {}
        self.root.dfs_defenses(self.defenses)
        self.root.dfs(nodes)
        for node in nodes:
            if node.node_type == NodeType.ATTACK:
                self.attacks.append(node)
            elif node.node_type == NodeType.GOAL:
                self.goals.append(node)
        self.nodes = self.attacks + self.goals
        self.defense_periods = []
        for defense in self.defenses:
            self.defense_periods.append(defense.period)

    def propagate(self, activated, completed):
        # Add parents node that are completed
        fixed_point = False
        while not fixed_point:
            fixed_point = True
            for node in completed.copy():
                for parent in node.parents:
                    if (
                        parent is not None
                        and parent not in completed
                        and (
                            parent.operation_type == OperationType.OR
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



    def reduce_activated_completed(self, activated, completed):
        # Remove completed nodes that have a checkpoint in all paths leading to the main goal
        TODO
        for node in completed.copy():
            checkpoint = False
            current = node
            while current.parents:
                if checkpoint:
                    break
                for parent in current.parents.copy():
                    current = parent
                    if current in completed and not current.defenses:
                        checkpoint = True
                        break

            if checkpoint:
                completed.remove(node)
        # Remove activated nodes that have a checkpoint above
        for node in activated.copy():
            if node in completed:
                activated.remove(node)
                break
            checkpoint = False
            current = node
            while current.parent:
                current = current.parent
                if current in completed and not current.defenses:
                    checkpoint = True
                    break

            if checkpoint:
                activated.remove(node)
