#!/usr/bin/env python
#

"""
// There is already a basic strategy in place here. You can use it as a
// starting point, or you can throw it out entirely and replace it with your
// own.
"""
import logging, traceback, sys, os, inspect
logging.basicConfig(filename=__file__[:-3] +'.log', filemode='w', level=logging.DEBUG)
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from behavior_tree_bot.behaviors import *
from behavior_tree_bot.checks import *
from behavior_tree_bot.bt_nodes import Selector, Sequence, Action, Check

from planet_wars import PlanetWars, finish_turn

# You have to improve this tree or create an entire new one that is capable
# of winning against all the 5 opponent bots

def setup_behavior_tree():
    # === Spread to Neutral Planets if Available ===
    spread_sequence = Sequence(name="Smart Spread to Neutral")
    spread_sequence.child_nodes = [
        Check(if_neutral_planet_available),
        Action(spread_to_nearest_capturable_neutral)
    ]

    # === Defend if Any Planet is Under Threat ===
    defend_sequence = Sequence(name="Defend Under Threat")
    defend_sequence.child_nodes = [
        Check(is_any_planet_under_threat),
        Action(reinforce_if_under_threat)
    ]

    # === Attack Smartly Only If It’s Safe ===
    attack_sequence = Sequence(name="Safe Attack")
    attack_sequence.child_nodes = [
        Check(can_safely_attack),
        Action(smart_attack_enemy_planet)
    ]

    # === Fallback (Do Nothing) ===
    fallback = Action(do_nothing)

    # === Root Selector Strategy ===
    root = Selector(name="Main Strategy")
    root.child_nodes = [
        defend_sequence,        # Defend first!
        attack_sequence,        # Then attack if safe
        spread_sequence,        # Then spread to neutral
        fallback                # Do nothing if no valid moves
    ]

    # === Logging and Saving Tree ===
    tree_string = root.tree_to_string()
    logging.info('\n' + tree_string)

    # Save tree structure to a text file (for submission)
    try:
        with open("behavior_tree.txt", "w") as f:
            f.write(tree_string)
    except Exception as e:
        logging.error("Failed to write behavior tree to file: %s", e)

    return root

# You don't need to change this function
def do_turn(state):
    behavior_tree.execute(planet_wars)

if __name__ == '__main__':
    logging.basicConfig(filename=__file__[:-3] + '.log', filemode='w', level=logging.DEBUG)

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
