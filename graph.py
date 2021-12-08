from enum import Enum
from tree import Tree, Goal, Attack, Defense, OperationType


class StateType(Enum):
    NORMAL = 1
    MTD = 2
    COMPLETION = 3


class Graph:
    def __init__(self, tree):
        self.tree = tree
        self.states = dict()
        self.build_graph()

    def build_graph(self):
        self.defense_periods = self.tree.defense_periods
        AttackerState(
            activated=[],
            completed=[],
            defense_periods=self.defense_periods,
            graph=self,
            build=True,
        )

    def __str__(self):
        string = ""
        for name, state in self.states.items():
            string += f"=======>{state}<=======\n"
        return string


class State:
    def __init__(
        self, activated, completed, defense_periods, state_type=None, edges=None
    ):
        self.edges = edges if edges else list()
        self.activated = activated
        self.completed = completed
        self.defense_periods = defense_periods
        self.state_type = state_type

    def __str__(self):
        string = ""
        for edge in self.edges:
            string += f"--> {edge.destination.serialize()}\n"
        return string

    def serialize(self):
        return (
            tuple(sorted([elem.name for elem in self.activated])),
            tuple(sorted([elem.name for elem in self.completed])),
            tuple(sorted(self.defense_periods)),
            self.state_type.name,
        )


class AttackerState(State):
    def __init__(self, activated, completed, defense_periods, graph, build=False):
        super().__init__(
            activated=activated,
            completed=completed,
            defense_periods=defense_periods,
            state_type=StateType.NORMAL,
        )
        self.key = self.serialize()
        if self.key not in graph.states:
            graph.states[self.key] = self
        if build:
            self.build_edges(graph)

    def __str__(self):
        return f"Attacker State {self.serialize()}\n" + super().__str__()

    def build_edges(self, graph):
        for attack in self.activated:
            self.build_completion_edge(attack, graph)

        for attack in graph.tree.attacks:
            if attack not in self.activated:
                self.build_activation_edges(attack, graph)

        for completed_node in self.completed:
            pass

    def build_activation_edges(self, attack, graph):
        destination = AttackerState(
            activated=self.get_activated() + [attack],
            completed=self.get_completed(),
            defense_periods=self.defense_periods,
            graph=graph,
            build=True,
        )
        self.edges.append(
            ActivationEdge(source=self, destination=destination, attack=attack)
        )

    def build_completion_edge(self, attack, graph):
        destination = CompletionState(
            activated=self.get_activated(),
            completed=self.get_completed(),
            new_completed=attack,
            defense_periods=self.defense_periods,
            graph=graph,
            build=True,
        )
        self.edges.append(
            CompletionEdge(source=self, destination=destination, attack=attack)
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


class CompletionState(State):
    def __init__(
        self, activated, completed, new_completed, defense_periods, graph, build=False
    ):
        super().__init__(
            activated=activated,
            completed=completed,
            defense_periods=defense_periods,
            state_type=StateType.COMPLETION,
        )
        self.new_completed = new_completed
        self.key = self.serialize()
        if self.key not in graph.states:
            graph.states[self.key] = self
        if build:
            self.build_edges(graph)

    def __str__(self):
        return f"Completion State {self.serialize()}\n" + super().__str__()

    def build_edges(self, graph):
        pass

    def serialize(self):
        return super().serialize() + (self.new_completed.name,)


class MTDState(State):
    def __init__(self):
        pass


class Edge:
    def __init__(self, source, destination):
        self.source = source
        self.destination = destination


class ActivationEdge(Edge):
    def __init__(self, source, destination, attack):
        super().__init__(source=source, destination=destination)
        self.attack = attack


class CompletionEdge(Edge):
    def __init__(self, source, destination, attack):
        super().__init__(source=source, destination=destination)
        self.attack = attack


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
        reset=True,
        name="g0",
    )
    tree = Tree(root)
    print(
        f"parent of {tree.root}'s child {tree.get_children()[1]} is {tree.get_children()[1].parent}"
    )
    graph = Graph(tree)
    print(graph)
