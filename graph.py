class Graph:
    def __init__(self, tree):
        self.tree = tree
        self.states = dict()
        self.build_graph()

    def build_graph(self):
        self.defense_periods = self.tree.get_defense_periods
        AttackerState([], [], defense_periods, self)


class State:
    def __inti__(self, edges=None):
        self.edges = edges if edge else list()


class AttackerState(State):
    def __init__(self, activated, completed, defense_periods=None, graph=None):
        super().__init__()
        self.activated = activated
        self.completed = completed
        self.defense_periods = defense_periods
        self.key = self.serialize()
        if graph:
            if key not in graph.states:
                graph.states[key] = self
            self.edges = self.build_edges(graph)

    def build_edges(self, graph):
        for attack in self.activated:
            self.build_attack_edge(attack, graph)

        for completed_node in self.completed:
            pass

    def build_attack_edges(self, attack, graph):
        destination = AttackerState(
            self.get_activated().add(attack),
            self.get_completed(),
            self.defense_periods,
            graph,
        )
        self.edges.append(
            ActivationEdge(source=self, destination=destination, attack=attack)
        )

    def serialize(self):
        return (
            tuple(sorted(activated)),
            tuple(sorted(completed)),
            tuple(sorted(defense_periods)),
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


class MTDState(State):
    def __init__(self):
        pass


class CompletionState(State):
    def __init__(self):
        pass


class Edge:
    def __init__(self, source, destination):
        self.source = source
        self.destination = destination


class ActivationEdge(Edge):
    def __init__(self, source, destination, attack):
        super().init(source=source, destination=destination)
        self.attack = attack
