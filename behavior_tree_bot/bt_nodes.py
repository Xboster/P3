from copy import deepcopy
import logging
import random

def log_execution(fn):
    def logged_fn(self, state):
        logging.debug('Executing:' + str(self))
        result = fn(self, state)
        logging.debug('Result: ' + str(self) + ' -> ' + ('Success' if result else 'Failure'))
        return result
    return logged_fn


############################### Base Classes ##################################
class Node:
    def __init__(self):
        raise NotImplementedError

    def execute(self, state):
        raise NotImplementedError

    def copy(self):
        return deepcopy(self)


class Composite(Node):
    def __init__(self, child_nodes=[], name=None):
        self.child_nodes = child_nodes
        self.name = name

    def execute(self, state):
        raise NotImplementedError

    def __str__(self):
        return self.__class__.__name__ + ': ' + self.name if self.name else ''

    def tree_to_string(self, indent=0):
        string = '| ' * indent + str(self) + '\n'
        for child in self.child_nodes:
            if hasattr(child, 'tree_to_string'):
                string += child.tree_to_string(indent + 1)
            else:
                string += '| ' * (indent + 1) + str(child) + '\n'
        return string


############################### Composite Nodes ##################################
class Selector(Composite):
    @log_execution
    def execute(self, state):
        for child_node in self.child_nodes:
            success = child_node.execute(state)
            if success:
                return True
        else:  # for loop completed without success; return failure
            return False


class Sequence(Composite):
    @log_execution
    def execute(self, state):
        for child_node in self.child_nodes:
            continue_execution = child_node.execute(state)
            if not continue_execution:
                return False
        else:  # for loop completed without failure; return success
            return True


############################### Leaf Nodes ##################################
class Check(Node):
    def __init__(self, check_function):
        self.check_function = check_function

    @log_execution
    def execute(self, state):
        return self.check_function(state)

    def __str__(self):
        return self.__class__.__name__ + ': ' + self.check_function.__name__


class Action(Node):
    def __init__(self, action_function):
        self.action_function = action_function

    @log_execution
    def execute(self, state):
        return self.action_function(state)

    def __str__(self):
        return self.__class__.__name__ + ': ' + self.action_function.__name__

############################### Decorator Nodes ##################################

class Inverter(Node):
    def __init__(self, child_node):
        self.child_node = child_node

    @log_execution
    def execute(self, state):
        return not self.child_node.execute(state)

    def __str__(self):
        return self.__class__.__name__ + ' -> ' + str(self.child_node)


class AlwaysSucceed(Node):
    def __init__(self, child_node):
        self.child_node = child_node

    @log_execution
    def execute(self, state):
        self.child_node.execute(state)
        return True

    def __str__(self):
        return self.__class__.__name__ + ' -> ' + str(self.child_node)


class AlwaysFail(Node):
    def __init__(self, child_node):
        self.child_node = child_node

    @log_execution
    def execute(self, state):
        self.child_node.execute(state)
        return False

    def __str__(self):
        return self.__class__.__name__ + ' -> ' + str(self.child_node)


class LoopUntilFailed(Node):
    def __init__(self, child_node):
        self.child_node = child_node

    @log_execution
    def execute(self, state):
        while True:
            if not self.child_node.execute(state):
                return False


class RandomSelector(Composite):
    @log_execution
    def execute(self, state):
        children = self.child_nodes[:]
        random.shuffle(children)
        for child_node in children:
            if child_node.execute(state):
                return True
        return False

    def __str__(self):
        return self.__class__.__name__ + ': ' + self.name if self.name else ''
