from enum import Enum
from tree import Tree, Goal, Attack, Defense, OperationType, NodeType


class StateType(Enum):
    NORMAL = 1
    MTD = 2
    COMPLETION = 3
    NO_ACTIVATION = 4
    ACTIVATION_COST = 5


class EdgeType(Enum):
    ACTIVATION = 1
    TO_COMPLETION = 2
    COMPLETION = 3
    TO_DEFENSE = 4
    DEFENSE = 5
    LOOP_DEFENSE = 6
    NO_ACTIVATION = 7
    TO_ACTIVATION_COST = 8


def defense_activation_activated_completed(
    defense, destination_activated, destination_completed
):
    """Remove inplace the atomic attacks that are deactivated and the goals that are
    reseted with a successful defense activation."""
    for reseted_attack in defense.parent.attack_childern:
        if reseted_attack in destination_activated:
            destination_activated.remove(reseted_attack)
    if defense.parent.reset and defense.parent in destination_completed:
        destination_completed.remove(defense.parent)


class Graph:
    def __init__(self, tree):
        self.tree = tree
        self.states = dict()
        self.build_graph()

    def build_graph(self):
        """Build graph from given tree."""
        self.initial_state = AttackerState(
            activated=[],
            completed=[],
            tree=self.tree,
            initial=True,
        )
        self.initial_state.build(graph=self)

    def __str__(self):
        edges_number = 0
        for state in self.states.values():
            edges_number += len(state.edges)
        string = (
            f"number of states: {len(self.states)}, number of edges: {edges_number}\n"
        )
        for state in self.states.values():
            string += f"=======>{state}<=======\n"
        return string


class Unique(type):
    """Make sure a state class has unique objects."""

    def __call__(cls, *args, **kwargs):
        self = cls.__new__(cls, *args, **kwargs)
        cls.__init__(self, *args, **kwargs)
        if self.key not in cls._cache:
            cls._cache[self.key] = self
        return cls._cache[self.key]

    def __init__(cls, name, bases, attributes):
        super().__init__(name, bases, attributes)
        cls._cache = {}


class State(metaclass=Unique):
    """Super class for states."""

    def __init__(
        self,
        activated,
        completed,
        tree,
        state_type=None,
        edges=None,
        initial=False,
        accepting=False,
    ):
        self.edges = edges if edges else list()
        self.activated = activated
        self.completed = completed
        self.initial = initial
        self.accepting = accepting
        tree.reduce_activated_completed(self.activated, self.completed)
        # Build subtrees of nodes that doesn't matter anymore
        self.completed_subtree = []
        for node in self.completed:
            if node not in self.completed_subtree:
                self.completed_subtree += [node]
                if node.node_type == NodeType.GOAL and not node.reset:
                    node.dfs(self.completed_subtree)

        # Build list of defenses that matter
        self.active_defenses = []
        for attack in self.activated:
            if attack.parent is None:
                continue
            defense = attack.parent.defense_child
            if defense is not None and defense not in self.active_defenses:
                self.active_defenses.append(defense)

        for node in self.completed:
            if (
                node.node_type == NodeType.GOAL
                and node.defense_child is not None
                and node.reset
            ):
                self.active_defenses.append(node.defense_child)
            if (
                node.node_type == NodeType.ATTACK
                and node.parent is not None
                and node.parent.defense_child is not None
            ):
                self.active_defenses.append(node.parent.defense_child)

        self.tree = tree
        self.state_type = state_type

    def __str__(self):
        string = ""
        for edge in self.edges:
            string += f"--> {edge.destination.serialize()}\n"
        return string

    def serialize(self):
        """Hashable name of the state used for insuring unique states."""
        return (
            tuple(sorted({elem.name for elem in self.activated})),
            tuple(sorted({elem.name for elem in self.completed})),
            # we remove the defense periods while it is unique in the graph
            # tuple(sorted(self.tree.defense_periods)),
            self.state_type.name,
        )

    def get_activated(self, copy=True):
        if copy:
            return self.activated.copy()
        else:
            return self.activated

    def get_completed(self, copy=True):
        if copy:
            return self.completed.copy()
        else:
            return self.completed


class AttackerState(State):
    """States (A,B) of atomic attacks activated and completed nodes."""

    def __init__(self, activated, completed, tree, initial=False, accepting=False):
        super().__init__(
            activated=activated,
            completed=completed,
            tree=tree,
            state_type=StateType.NORMAL,
            initial=initial,
            accepting=accepting,
        )
        self.key = self.serialize()
        if len(self.completed) > 0 and self.completed[0].name == tree.root.name:
            self.accepting = True

    def __str__(self):
        return f"Attacker State {self.serialize()}\n" + super().__str__()

    def build(self, graph):
        if self.key not in graph.states:
            graph.states[self.key] = self
            self.build_edges(graph)
            if self.accepting:
                graph.accepting_state = self

    def build_edges(self, graph):
        """Edges to activate other atomic attacks or to wait for completion or mtd
        activation."""
        # Activation edges
        for attack in graph.tree.attacks:
            if attack not in self.activated and attack not in self.completed_subtree:
                if attack.activation_cost is None:
                    self.build_activation_edges(attack, graph)
                else:
                    self.build_activation_cost_edge(attack, graph)

        # No activation edge
        if len(self.activated) > 0 or any(
            [
                (
                    node.node_type == NodeType.ATTACK
                    and node.parent.defense_child is not None
                )
                or (node.node_type == NodeType.GOAL and node.reset)
                for node in self.completed
            ]
        ):
            self.build_no_activation_edge(graph)

    def build_activation_edges(self, attack, graph):
        destination = AttackerState(
            activated=self.get_activated() + [attack],
            completed=self.get_completed(),
            tree=self.tree,
        )
        self.edges.append(
            ActivationEdge(source=self, destination=destination, attack=attack)
        )
        destination.build(graph=graph)

    def build_activation_cost_edge(self, attack, graph):
        destination = ActivationCostState(
            activated=self.get_activated(),
            completed=self.get_completed(),
            attack=attack,
            tree=self.tree,
        )
        self.edges.append(
            ActivationCostEdge(source=self, destination=destination, attack=attack)
        )
        destination.build(graph=graph)

    def build_no_activation_edge(self, graph):
        destination = NoActivationState(
            activated=self.get_activated(),
            completed=self.get_completed(),
            tree=self.tree,
        )
        self.edges.append(NoActivationEdge(source=self, destination=destination))
        destination.build(graph=graph)


class CompletionState(State):
    """State when an atomic attack is stochasticly completed. It leads to a branchpoint
    in Uppaal."""

    def __init__(self, activated, completed, new_completed, tree, initial=False):
        super().__init__(
            activated=activated,
            completed=completed,
            tree=tree,
            state_type=StateType.COMPLETION,
            initial=initial,
        )
        self.new_completed = new_completed
        self.key = self.serialize()

    def __str__(self):
        return f"Completion State {self.serialize()}\n" + super().__str__()

    def build(self, graph):
        if self.key not in graph.states:
            graph.states[self.key] = self
            self.build_edges(graph)

    def build_edges(self, graph):
        # Success edge
        destination_success_activated = self.get_activated()
        destination_success_activated.remove(self.new_completed)
        destination_success_completed = self.get_completed()
        destination_success_completed.append(self.new_completed)

        destination_success = AttackerState(
            activated=destination_success_activated,
            completed=destination_success_completed,
            tree=self.tree,
        )

        self.edges.append(
            CompletionEdge(
                source=self,
                destination=destination_success,
                attack=self.new_completed,
                success=True,
            )
        )
        destination_success.build(graph=graph)

        # Fail edge
        destination_fail_activated = self.get_activated()
        destination_fail_activated.remove(self.new_completed)
        destination_fail_completed = self.get_completed()

        destination_fail = AttackerState(
            activated=destination_fail_activated,
            completed=destination_fail_completed,
            tree=self.tree,
        )

        self.edges.append(
            CompletionEdge(
                source=self,
                destination=destination_fail,
                attack=self.new_completed,
                success=False,
            )
        )
        destination_fail.build(graph=graph)

    def serialize(self):
        return super().serialize() + (self.new_completed.name,)


class DefenseState(State):
    """State when a MTD defense is stochasticly activated. It leads to a branchpoint
    in Uppaal."""

    def __init__(self, activated, completed, defense, tree, initial=False):
        super().__init__(
            activated=activated,
            completed=completed,
            tree=tree,
            state_type=StateType.MTD,
            initial=initial,
        )
        self.defense = defense
        self.key = self.serialize()

    def __str__(self):
        return f"Defense State {self.serialize()}\n" + super().__str__()

    def build(self, graph):
        if self.key not in graph.states:
            graph.states[self.key] = self
            self.build_edges(graph)

    def build_edges(self, graph):
        # Success edge
        destination_success_activated = self.get_activated()
        destination_success_completed = self.get_completed()
        defense_activation_activated_completed(
            self.defense, destination_success_activated, destination_success_completed
        )

        destination_success = AttackerState(
            activated=destination_success_activated,
            completed=destination_success_completed,
            tree=self.tree,
        )

        self.edges.append(
            DefenseEdge(
                source=self,
                destination=destination_success,
                defense=self.defense,
                success=True,
            )
        )
        destination_success.build(graph=graph)

        # Fail edge
        destination_fail = AttackerState(
            activated=self.get_activated(),
            completed=self.get_completed(),
            tree=self.tree,
        )

        self.edges.append(
            DefenseEdge(
                source=self,
                destination=destination_fail,
                defense=self.defense,
                success=False,
            )
        )

    def serialize(self):
        return super().serialize() + (self.defense.name,)


class NoActivationState(State):
    """State when the defenser decides to wait and not activated more atomic attacks."""

    def __init__(self, activated, completed, tree, initial=False):
        super().__init__(
            activated=activated,
            completed=completed,
            tree=tree,
            state_type=StateType.NO_ACTIVATION,
            initial=initial,
        )
        self.key = self.serialize()

    def __str__(self):
        return f"No activation State {self.serialize()}\n" + super().__str__()

    def build(self, graph):
        if self.key not in graph.states:
            graph.states[self.key] = self
            self.build_edges(graph)

    def build_edges(self, graph):
        for attack in self.activated:
            self.build_completion_edge(attack, graph)

        for defense in self.tree.defenses:
            self.build_defense_edge(defense, graph)

    def build_completion_edge(self, attack, graph):
        """A completion edge for each atomic attacks in self.activated."""
        if attack.success_probability < 1:
            destination = CompletionState(
                activated=self.get_activated(),
                completed=self.get_completed(),
                new_completed=attack,
                tree=self.tree,
            )
        else:
            destination = AttackerState(
                activated=self.get_activated(),
                completed=self.get_completed() + [attack],
                tree=self.tree,
            )
        self.edges.append(
            ToCompletionEdge(source=self, destination=destination, attack=attack)
        )
        destination.build(graph=graph)

    def build_defense_edge(self, defense, graph):
        """For each defense, a looping edge to reset a clock if the
        defense is not active, and a MTD activation edge if the defense
        has an impact on the activated atomic attacks or the completed
        nodes."""
        if defense in self.active_defenses:
            if defense.success_probability < 1:
                destination = DefenseState(
                    activated=self.get_activated(),
                    completed=self.get_completed(),
                    defense=defense,
                    tree=self.tree,
                )
            else:
                destination_activated = self.get_activated()
                destination_completed = self.get_completed()
                defense_activation_activated_completed(
                    defense, destination_activated, destination_completed
                )

                destination = AttackerState(
                    activated=destination_activated,
                    completed=destination_completed,
                    tree=self.tree,
                )
            self.edges.append(
                ToDefenseEdge(source=self, destination=destination, defense=defense)
            )
            destination.build(graph=graph)
        else:
            self.edges.append(
                LoopDefenseEdge(source=self, destination=self, defense=defense)
            )


class ActivationCostState(State):
    """State where we stay one unit of time to increase the cost hybrid clock
    of a given cost activation value."""

    def __init__(self, activated, completed, attack, tree):
        super().__init__(
            activated=activated,
            completed=completed,
            state_type=StateType.ACTIVATION_COST,
            tree=tree,
        )
        self.attack = attack
        self.key = self.serialize()

    def __str__(self):
        return f"Activation cost state {self.serialize()}\n" + super().__str__()

    def build(self, graph):
        if self.key not in graph.states:
            graph.states[self.key] = self
            self.build_activation_edge(self.attack, graph)

    def build_activation_edge(self, attack, graph):
        destination = AttackerState(
            activated=self.get_activated() + [attack],
            completed=self.get_completed(),
            tree=self.tree,
        )
        self.edges.append(
            ActivationEdge(source=self, destination=destination, attack=attack)
        )
        destination.build(graph=graph)

    def serialize(self):
        return super().serialize() + (self.attack.name,)


class Edge:
    """Edge super class."""

    def __init__(self, source, destination):
        assert source is not None and destination is not None
        self.source = source
        self.destination = destination


class ActivationEdge(Edge):
    def __init__(self, source, destination, attack):
        super().__init__(source=source, destination=destination)
        self.attack = attack
        self.type = EdgeType.ACTIVATION


class ToCompletionEdge(Edge):
    def __init__(self, source, destination, attack):
        super().__init__(source=source, destination=destination)
        self.attack = attack
        self.type = EdgeType.TO_COMPLETION


class CompletionEdge(Edge):
    def __init__(self, source, destination, attack, success):
        super().__init__(source=source, destination=destination)
        self.attack = attack
        self.success = success
        if success:
            self.success_probability = attack.success_probability
        else:
            self.success_probability = 1.0 - attack.success_probability
        self.type = EdgeType.COMPLETION


class ToDefenseEdge(Edge):
    def __init__(self, source, destination, defense):
        super().__init__(source=source, destination=destination)
        self.defense = defense
        self.type = EdgeType.TO_DEFENSE


class DefenseEdge(Edge):
    def __init__(self, source, destination, defense, success):
        super().__init__(source=source, destination=destination)
        self.defense = defense
        self.success = success
        if success:
            self.success_probability = defense.success_probability
        else:
            self.success_probability = 1.0 - defense.success_probability
        self.type = EdgeType.DEFENSE


class LoopDefenseEdge(Edge):
    def __init__(self, source, destination, defense):
        super().__init__(source=source, destination=destination)
        self.defense = defense
        self.type = EdgeType.LOOP_DEFENSE


class NoActivationEdge(Edge):
    def __init__(self, source, destination):
        super().__init__(source=source, destination=destination)
        self.type = EdgeType.NO_ACTIVATION


class ActivationCostEdge(Edge):
    def __init__(self, source, destination, attack):
        super().__init__(source=source, destination=destination)
        self.attack = attack
        self.type = EdgeType.TO_ACTIVATION_COST


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
                        completion_time=3,
                        success_probability=0.2,
                        activation_cost=1,
                        name="a1",
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
        reset=False,
        name="g0",
    )
    tree = Tree(root)
    print(
        f"parent of {tree.root}'s child {tree.get_children()[1]} is {tree.get_children()[1].parent}"
    )
    graph = Graph(tree)
    print(graph)
