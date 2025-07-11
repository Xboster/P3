from planet_wars import issue_order
import random


def spread_to_weakest_neutral_planet(state):
    if len(state.my_fleets()) >= 1:
        return False
    strongest = max(state.my_planets(), key=lambda p: p.num_ships, default=None)
    weakest = min(state.neutral_planets(), key=lambda p: p.num_ships, default=None)
    if strongest and weakest:
        return issue_order(state, strongest.ID, weakest.ID, strongest.num_ships / 2)
    return False


def attack_weakest_enemy_planet(state):
    if len(state.my_fleets()) >= 1:
        return False
    strongest = max(state.my_planets(), key=lambda p: p.num_ships, default=None)
    weakest = min(state.enemy_planets(), key=lambda p: p.num_ships, default=None)
    if strongest and weakest:
        return issue_order(state, strongest.ID, weakest.ID, strongest.num_ships / 2)
    return False


def attack_best_target(state):
    my_planets = state.my_planets()
    enemy_planets = state.enemy_planets()
    if not my_planets or not enemy_planets:
        return False
    best_source = max(my_planets, key=lambda p: p.num_ships, default=None)
    best_target = min(
        enemy_planets,
        key=lambda p: (p.num_ships + 5 * state.distance(best_source.ID, p.ID)),
        default=None
    )
    if best_source and best_target and best_source.num_ships > 30:
        return issue_order(state, best_source.ID, best_target.ID, best_source.num_ships * 0.65)
    return False


def reinforce_weakest_frontline(state):
    my_planets = state.my_planets()
    if len(my_planets) < 2:
        return False

    weakest = min(my_planets, key=lambda p: p.num_ships)
    strongest = max(my_planets, key=lambda p: p.num_ships)
    if weakest.ID != strongest.ID and strongest.num_ships > 50:
        return issue_order(state, strongest.ID, weakest.ID, strongest.num_ships * 0.4)
    return False
