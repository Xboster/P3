import sys
sys.path.insert(0, '../')
from planet_wars import issue_order

# === Utility Functions ===

def is_planet_targeted(state, target_id):
    """
    Returns True if any of your fleets are already heading to the target planet.
    """
    return any(fleet.destination_planet == target_id for fleet in state.my_fleets())

def is_planet_sufficiently_targeted(state, target_id, threshold):
    """
    Returns True if the total number of ships in-flight to a target planet is >= threshold.
    """
    total_ships = sum(fleet.num_ships for fleet in state.my_fleets() if fleet.destination_planet == target_id)
    return total_ships >= threshold

# === Behavior Functions ===

def attack_weakest_enemy_planet(state):
    strongest_planet = max(state.my_planets(), key=lambda t: t.num_ships, default=None)
    weakest_planet = min(state.enemy_planets(), key=lambda t: t.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        return False

    # Check if a fleet is already heading to that planet
    # if is_planet_targeted(state, weakest_planet.ID):
    #     return False
    if is_planet_sufficiently_targeted(state, weakest_planet.ID, weakest_planet.num_ships):
        return False

    return issue_order(state, strongest_planet.ID, weakest_planet.ID, strongest_planet.num_ships / 2)


def spread_to_weakest_neutral_planet(state):
    strongest_planet = max(state.my_planets(), key=lambda p: p.num_ships, default=None)
    weakest_planet = min(state.neutral_planets(), key=lambda p: p.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        return False

    # if is_planet_targeted(state, weakest_planet.ID):
    #     return False
    if is_planet_sufficiently_targeted(state, weakest_planet.ID, weakest_planet.num_ships):
        return False

    return issue_order(state, strongest_planet.ID, weakest_planet.ID, strongest_planet.num_ships / 2)


def attack_closest_enemy_planet(state):
    my_planets = state.my_planets()
    enemy_planets = state.enemy_planets()
    if not my_planets or not enemy_planets:
        return False

    source = max(my_planets, key=lambda p: p.num_ships)
    target = min(enemy_planets, key=lambda e: state.distance(source.ID, e.ID))

    if is_planet_sufficiently_targeted(state, target.ID, target.num_ships):
        return False

    return issue_order(state, source.ID, target.ID, source.num_ships / 2)


def reinforce_weakest_own_planet(state):
    planets = state.my_planets()
    if len(planets) < 2:
        return False

    source = max(planets, key=lambda p: p.num_ships)
    target = min(planets, key=lambda p: p.num_ships)

    if source.num_ships <= 20 or source == target:
        return False

    if is_planet_targeted(state, target.ID):
        return False

    return issue_order(state, source.ID, target.ID, source.num_ships / 3)


def spread_to_strategic_neutral(state):
    my_planets = state.my_planets()
    neutral_planets = state.neutral_planets()

    if not my_planets or not neutral_planets:
        return False

    source = max(my_planets, key=lambda p: p.num_ships)
    # Pick neutral planets closest + weakest
    target = min(
        neutral_planets,
        key=lambda n: state.distance(source.ID, n.ID) + n.num_ships
    )

    ships_needed = target.num_ships + 1
    if source.num_ships > ships_needed:
        return issue_order(state, source.ID, target.ID, ships_needed)

    return False


def spread_to_nearest_capturable_neutral(state):
    my_planets = state.my_planets()
    neutral_planets = state.neutral_planets()
    my_fleets = state.my_fleets()

    if not my_planets or not neutral_planets:
        return False

    issued = False

    for source in sorted(my_planets, key=lambda p: -p.num_ships):
        available_ships = source.num_ships
        if available_ships <= 1:
            continue

        # Sort neutral planets by distance + ships (prioritize closeness and ease of capture)
        candidates = sorted(neutral_planets, key=lambda n: state.distance(source.ID, n.ID) + n.num_ships)

        for target in candidates:
            if any(f.destination_planet == target.ID for f in my_fleets):
                continue  # Skip if already targeting this neutral

            if available_ships > target.num_ships + 1:
                num_to_send = target.num_ships + 1
                if issue_order(state, source.ID, target.ID, num_to_send):
                    issued = True
                    break  # Only one fleet per turn from this source

        if issued:
            break  # Only send one fleet total per turn

    return issued


def do_nothing(state):
    return True  # Always succeeds
