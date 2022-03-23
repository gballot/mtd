from enum import Enum


class NodeType(Enum):
    SUBGOAL = 1
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
        subgoal_children=None,
        node_type=None,
        name=None,
    ):
        self.parents = parents if parents else []
        self.defenses = defenses if defenses else []
        self.node_type = node_type
        self.attack_childern = attack_childern if attack_childern else []
        self.subgoal_children = subgoal_children if subgoal_children else []
        self.name = name if name else f"{self.node_type}:{id(self)}"

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
        return self.attack_childern + self.subgoal_children

    def set_parents(self, parents=None):
        if not parents:
            self.parents = []
        else:
            self.parents.append(parents)
        for child in self.get_children():
            child.set_parents(self)

    def dfs(self, visited):
        for child in self.get_children():
            if child not in visited:
                visited.append(child)
                child.dfs(visited)

    def dfs_parents(self, visited):
        for parent in self.parents:
            if parent not in visited:
                visited.append(parent)
                parent.dfs_parents(visited)

    def dfs_defenses(self, defenses):
        for defense in self.defenses:
            if defense not in defenses:
                defenses.append(defense)
        for child in self.get_children():
            child.dfs_defenses(defenses)


class Subgoal(Node):
    def __init__(
        self,
        name,
        operation_type,
        children=None,
        defenses=None,
        attack_childern=None,
        subgoal_children=None,
        parents=None,
    ):
        if children:
            assert defenses is None
            assert attack_childern is None
            assert subgoal_children is None
            defenses = []
            attack_childern = []
            subgoal_children = []
            for child in children:
                if child.node_type == NodeType.DEFENSE:
                    defenses.append(child)
                elif child.node_type == NodeType.ATTACK:
                    attack_childern.append(child)
                elif child.node_type == NodeType.SUBGOAL:
                    subgoal_children.append(child)
                else:
                    raise Exception("Children without type")
        super().__init__(
            parents=parents,
            defenses=defenses,
            attack_childern=attack_childern,
            subgoal_children=subgoal_children,
            node_type=NodeType.SUBGOAL,
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


class ADG:
    def __init__(self, root):
        assert not root.defenses
        self.root = root
        self.root.set_parents()
        self.init_dfs()

    def get_children(self, include_defense=False):
        return self.root.get_children(include_defense)

    def init_dfs(self):
        """Sould be used only at initialization to set self.attacks, self.defenses
        self.subgoals."""
        self.attacks = []
        self.defenses = []
        self.subgoals = []
        nodes = []
        self.root.dfs_defenses(self.defenses)
        self.root.dfs(nodes)
        for node in nodes:
            if node.node_type == NodeType.ATTACK:
                self.attacks.append(node)
            elif node.node_type == NodeType.SUBGOAL:
                self.subgoals.append(node)
        self.nodes = self.attacks + self.subgoals

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
                                and {n.name for n in parent.subgoal_children}
                                <= {n.name for n in completed}
                            )
                        )
                    ):
                        fixed_point = False
                        completed.append(parent)



    def has_checkpoint_ancestor(self, subgoal, completed):
        #TODO: ne dois pas renvoyer le noeud lui meme. Done?
        if subgoal in completed and not subgoal.defenses:
            return True
        elif not subgoal.parents:
            return False
        else:
            return all([self.has_checkpoint_ancestor(parent, completed) for parent in subgoal.parents])

    def completed_subadg(self, completed):
        return [node for node in self.nodes if self.has_checkpoint_ancestor(node, completed)]


    def reduce_activated_completed(self, activated, completed):
        # Remove completed nodes that have a checkpoint in all paths leading to the main subgoal
        old_completed = completed.copy()
        for node in old_completed:
            if self.has_checkpoint_ancestor(node, old_completed):
                completed.remove(node)
        # Remove activated nodes that have a checkpoint in all paths leading to the main subgoal
        for node in activated.copy():
            if self.has_checkpoint_ancestor(node, old_completed):
                activated.remove(node)
        # Remove activated nodes that are comleted
        for node in activated.copy():
            if node in completed:
                activated.remove(node)
