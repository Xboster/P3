#!/usr/bin/env python
import logging, traceback, sys, os, inspect
logging.basicConfig(filename=__file__[:-3] + '.log', filemode='w', level=logging.DEBUG)
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from behavior_tree_bot.behaviors import *
from behavior_tree_bot.checks import *
from behavior_tree_bot.bt_nodes import Selector, Sequence, Action, Check

from planet_wars import PlanetWars, finish_turn


def setup_behavior_tree():
    root = Selector(name='High-Level Strategy')

    early_expansion = Sequence(name='Early Expansion')
    early_expansion.child_nodes = [
        Check(if_neutral_planet_available),
        Action(spread_to_weakest_neutral_planet)
    ]

    reinforce = Sequence(name='Reinforcement Strategy')
    reinforce.child_nodes = [
        Check(need_reinforcement),
        Action(reinforce_weakest_frontline)
    ]

    attack_sequence = Sequence(name='Attack Strategy')
    attack_sequence.child_nodes = [
        Check(have_largest_fleet),
        Action(attack_best_target)
    ]

    fallback = Selector(name='Fallback')
    fallback.child_nodes = [
        Action(spread_to_weakest_neutral_planet),
        Action(attack_weakest_enemy_planet)
    ]

    root.child_nodes = [early_expansion, reinforce, attack_sequence, fallback]
    logging.info('\n' + root.tree_to_string())
    return root

def do_turn(state):
    behavior_tree.execute(state)

if __name__ == '__main__':
    behavior_tree = setup_behavior_tree()
    try:
        map_data = ''
        while True:
            current_line = input()
            if len(current_line) >= 2 and current_line.startswith("go"):
                planet_wars = PlanetWars(map_data)
                do_turn(planet_wars)
                finish_turn()
                map_data = ''
            else:
                map_data += current_line + '\n'
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
    except Exception:
        traceback.print_exc(file=sys.stdout)
        logging.exception("Error in bot.")
