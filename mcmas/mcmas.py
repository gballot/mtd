from tree import NodeType, Goal, Attack, OperationType


def make_list(l, prefix="(", suffix=")", connector="and"):
    return prefix + f"{suffix}{connector}{prefix}".join([str(e) for e in l]) + suffix

def make_completion_condition(node):
    if node.node_type == NodeType.GOAL:
        if node.operation_type == OperationType.EDGE:
            condition = f"( finished_{node.name} or {make_completion_condition(node.get_children()[0])} )"
        elif node.operation_type == OperationType.AND:
            condition = f"( finished_{node.name} or ( " + make_completion_condition(node.get_children()[0]) + " and " + make_completion_condition(node.get_children()[1]) + " )"
        elif node.operation_type == OperationType.OR:
            condition = f"( finished_{node.name} or ( " + make_completion_condition(node.get_children()[0]) + " or " + make_completion_condition(node.get_children()[1]) + " )"
        if node.reset:
            condition = f"( {condition} and !(Defense_{node.defense_child.name}.Action=move) )"
    if node.node_type == NodeType.ATTACK:
        condition = f"(Attack_{node.name}.Action=finished)"
    return condition


class McmasExporter():
    indent = 0

    def __init__(self, tree, max_time):
        self.tree = tree
        self.max_time = max_time

    def export(self, output):
        self.output = output
        self.file = open(output, 'w')
        try:
            self.writel("Semantics=SingleAssignment;\n")
            self.make_environment()
        finally:
            self.file.close()

    def writel(self, txt):
        self.file.write(self.indent * "\t" + txt + "\n")

    def make_environment(self):
        self.indent = 0
        self.writel("Agent Environment")
        # Vars
        self.indent = 1
        self.writel("Vars:")
        self.indent = 2
        self.writel(f"time : 0 .. {self.max_time};")
        for goal in self.tree.goals:
            self.writel(f"finished_{goal.name} : boolean;")
            if goal.detection_time is not None:
                self.writel(f"detected_{goal.name} : boolean;")
                self.writel(f"time_{goal.name} : 0 .. {goal.detection_time};")
        self.indent = 1
        self.writel("end Vars")
        # Actions
        self.writel("Actions = {none};")
        # Protocol
        self.writel("Protocol:")
        self.indent = 2
        self.writel("Other: {none};")
        self.indent = 1
        self.writel("end Protocol")
        # Evolution
        self.writel("Evolution:")
        self.indent = 2
        for t in range(self.max_time):
            self.writel(f"time={t+1} if (time={t});")
        for goal in self.tree.goals:
            self.writel(f"finished_{goal.name} = {make_completion_condition(goal)};")
            if goal.detection_time is not None:
                for t in range(goal.detection_time):
                    self.writel(f"time_{goal.name}={t+1} if (time_{goal.name}={t}) and {make_completion_condition(goal)};")
                self.writel(f"detected_{goal.name} = (time_{goal}={goal.detection_time - 1}) and {make_completion_condition(goal)};")
        self.indent = 1
        self.writel("end Evolution")
        self.indent = 0
        self.writel("end Agent")

    def make_defense(self, defense):
        self.indent = 0
        self.writel(f"Agent Defense_{defense.name}")
        # Vars
        self.indent = 1
        self.writel("Vars:")
        self.indent = 2
        self.writel(f"period : 0 .. {self.max_period};")
        for goal in self.tree.goals:
            self.writel(f"finished_{goal.name} : boolean;")
            if goal.detection_time is not None:
                self.writel(f"detected_{goal.name} : boolean;")
                self.writel(f"time_{goal.name} : 0 .. {goal.detection_time};")
        self.indent = 1
        self.writel("end Vars")
        # Actions
        self.writel("Actions = {none};")
        # Protocol
        self.writel("Protocol:")
        self.indent = 2
        self.writel("Other: {none};")
        self.indent = 1
        self.writel("end Protocol")
        # Evolution
        self.writel("Evolution:")
        self.indent = 2
        for t in range(self.max_time):
            self.writel(f"time={t+1} if (time={t});")
        for goal in self.tree.goals:
            self.writel(f"finished_{goal.name} = {make_completion_condition(goal)};")
            if goal.detection_time is not None:
                for t in range(goal.detection_time):
                    self.writel(f"time_{goal.name}={t+1} if (time_{goal.name}={t}) and {make_completion_condition(goal)};")
                self.writel(f"detected_{goal.name} = (time_{goal}={goal.detection_time - 1}) and {make_completion_condition(goal)};")
        self.indent = 1
        self.writel("end Evolution")
        self.indent = 0
        self.writel("end Agent")


