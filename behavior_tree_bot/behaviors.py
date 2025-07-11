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

def is_any_planet_under_threat(state):
    for planet in state.my_planets():
        incoming_enemy_ships = sum(
            fleet.num_ships for fleet in state.enemy_fleets()
            if fleet.destination_planet == planet.ID
        )
        arrival_turns = [
            fleet.turns_remaining for fleet in state.enemy_fleets()
            if fleet.destination_planet == planet.ID
        ]
        if not arrival_turns:
            continue
        turns_until_attack = min(arrival_turns)
        projected_ships = planet.num_ships + planet.growth_rate * turns_until_attack
        if incoming_enemy_ships >= projected_ships:
            return True
    return False


def can_safely_attack(state):
    my_planets = state.my_planets()
    enemy_planets = state.enemy_planets()
    if not my_planets or not enemy_planets:
        return False

    for source in my_planets:
        for target in enemy_planets:
            dist = state.distance(source.ID, target.ID)
            projected_defenders = target.num_ships + target.growth_rate * dist
            if source.num_ships > projected_defenders * 1.5:
                return True
    return False


def projected_ships_at_arrival(state, planet_id, turns_until_arrival, include_my_fleets=True, include_enemy_fleets=True):
    """
    Predicts how many ships a planet will have after 'turns_until_arrival' turns.
    Includes growth and incoming fleets.
    """
    target = state.planets[planet_id]
    projected = target.num_ships

    # Growth applies only if owned (not neutral)
    if target.owner in [1, 2]:  # 1 = me, 2 = enemy
        projected += (target.growth_rate * turns_until_arrival -1)

    # Adjust for incoming fleets
    for fleet in state.fleets:
        if fleet.destination_planet != planet_id:
            continue

        if fleet.turns_remaining > turns_until_arrival:
            continue  # Will arrive later, ignore

        if fleet.owner == 1 and include_my_fleets:
            if target.owner == 1:
                projected += fleet.num_ships  # Friendly reinforcement
            elif target.owner == 0:
                projected -= fleet.num_ships  # Capturing neutral
            elif target.owner == 2:
                projected -= fleet.num_ships  # Attacking enemy

        elif fleet.owner == 2 and include_enemy_fleets:
            if target.owner == 2:
                projected += fleet.num_ships  # Enemy reinforcement
            elif target.owner == 0:
                projected -= fleet.num_ships  # Enemy capturing neutral
            elif target.owner == 1:
                projected -= fleet.num_ships  # Enemy attacking us

    return int(projected)


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

    return issue_order(state, strongest_planet.ID, weakest_planet.ID, strongest_planet.num_ships // 2)


def spread_to_weakest_neutral_planet(state):
    strongest_planet = max(state.my_planets(), key=lambda p: p.num_ships, default=None)
    weakest_planet = min(state.neutral_planets(), key=lambda p: p.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        return False

    # if is_planet_targeted(state, weakest_planet.ID):
    #     return False
    if is_planet_sufficiently_targeted(state, weakest_planet.ID, weakest_planet.num_ships):
        return False

    return issue_order(state, strongest_planet.ID, weakest_planet.ID, strongest_planet.num_ships // 2)


def attack_closest_enemy_planet(state):
    my_planets = state.my_planets()
    enemy_planets = state.enemy_planets()
    if not my_planets or not enemy_planets:
        return False

    source = max(my_planets, key=lambda p: p.num_ships)
    target = min(enemy_planets, key=lambda e: state.distance(source.ID, e.ID))

    if is_planet_sufficiently_targeted(state, target.ID, target.num_ships):
        return False

    return issue_order(state, source.ID, target.ID, source.num_ships // 2)


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

    return issue_order(state, source.ID, target.ID, source.num_ships // 3)


def spread_to_strategic_neutral(state):
    my_planets = state.my_planets()
    neutral_planets = state.neutral_planets()
    enemy_fleets = state.enemy_fleets()

    if not my_planets or not neutral_planets:
        return False

    # Step 1: Try to snipe contested neutrals
    for target in neutral_planets:
        # Enemy fleets targeting this planet
        incoming_enemy_fleets = [
            fleet for fleet in enemy_fleets
            if fleet.destination_planet == target.ID
        ]
        if not incoming_enemy_fleets:
            continue  # No snipe opportunity

        soonest_enemy_fleet = min(incoming_enemy_fleets, key=lambda f: f.turns_remaining)
        enemy_arrival = soonest_enemy_fleet.turns_remaining
        enemy_ships = sum(f.num_ships for f in incoming_enemy_fleets if f.turns_remaining == enemy_arrival)

        # We want to arrive before or with more force at same time
        for source in sorted(my_planets, key=lambda p: state.distance(p.ID, target.ID)):
            my_arrival = state.distance(source.ID, target.ID)
            ships_needed = target.num_ships + enemy_ships + 1  # Overwhelm them and original defenders

            if my_arrival <= enemy_arrival and source.num_ships > ships_needed:
                return issue_order(state, source.ID, target.ID, ships_needed)

    # Step 2: Fallback to regular neutral spread if no snipe possible
    source = max(my_planets, key=lambda p: p.num_ships)
    sorted_targets = sorted(
        neutral_planets,
        key=lambda n: state.distance(source.ID, n.ID) + n.num_ships
    )

    for target in sorted_targets:
        distance_to_target = state.distance(source.ID, target.ID)
        ships_needed = target.num_ships + 2
        incoming_enemy_ships = sum(
            fleet.num_ships
            for fleet in enemy_fleets
            if fleet.destination_planet == target.ID and fleet.turns_remaining <= distance_to_target
        )
        total_required = ships_needed + incoming_enemy_ships

        if source.num_ships > total_required:
            return issue_order(state, source.ID, target.ID, total_required)

    return False


def spread_to_nearest_capturable_neutral(state):
    my_planets = state.my_planets()
    neutral_planets = state.neutral_planets()
    my_fleets = state.my_fleets()
    enemy_planets = state.enemy_planets()

    if not my_planets or not neutral_planets:
        return False

    issued = False

    for source in sorted(my_planets, key=lambda p: -p.num_ships):
        available_ships = source.num_ships
        if available_ships <= 1:
            continue

        def priority_score(n):
            dist_to_us = min(state.distance(p.ID, n.ID) for p in my_planets)
            dist_to_enemy = min(state.distance(p.ID, n.ID) for p in enemy_planets) if enemy_planets else 999
            bias = dist_to_enemy - dist_to_us  # Higher is better
            return -bias * 100 + state.distance(source.ID, n.ID) + n.num_ships

        candidates = sorted(neutral_planets, key=priority_score)

        for target in candidates:
            if any(f.destination_planet == target.ID for f in my_fleets):
                continue  # Already targeted

            dist = state.distance(source.ID, target.ID)
            projected = projected_ships_at_arrival(state, target.ID, dist)

            if projected < 0:
                continue  # Enemy will likely own it before we get there

            ships_needed = projected + 1

            if available_ships > ships_needed:
                if issue_order(state, source.ID, target.ID, ships_needed):
                    issued = True
                    break

        if issued:
            break

    return issued



def smart_coordinated_attack_enemy_planet(state, max_arrival_delay=10):
    my_planets = state.my_planets()
    enemy_planets = state.enemy_planets()

    if not my_planets or not enemy_planets:
        return False

    # Sort enemy planets by distance to our closest planet
    potential_targets = sorted(
        enemy_planets,
        key=lambda ep: min(state.distance(ep.ID, mp.ID) for mp in my_planets)
    )

    for target in potential_targets:
        if is_planet_sufficiently_targeted(state, target.ID, projected_ships_at_arrival(state, target.ID, 0)):
            continue

        # Try different coordinated arrival times
        for arrival_time in range(1, max_arrival_delay + 1):
            projected_defense = projected_ships_at_arrival(state, target.ID, arrival_time)
            required_force = projected_defense + 3

            contributors = []
            total_available = 0

            for source in my_planets:
                available = source.num_ships - 10  # Keep 10 ships for safety
                if available <= 0:
                    continue

                distance = state.distance(source.ID, target.ID)
                if distance != arrival_time:
                    continue  # Only use planets that can arrive at the target exactly on this turn

                contributors.append((source, available))
                total_available += available

                if total_available >= required_force:
                    break

            if total_available >= required_force:
                for planet, ships in contributors:
                    ships_to_send = min(ships, required_force)
                    issue_order(state, planet.ID, target.ID, ships_to_send)
                    required_force -= ships_to_send
                    if required_force <= 0:
                        break
                return True  # One coordinated attack per turn

    return False

def smart_attack_enemy_planet(state):
    my_planets = state.my_planets()
    enemy_planets = state.enemy_planets()

    if not my_planets or not enemy_planets:
        return False

    did_attack = False

    # Sort enemy planets by proximity
    potential_targets = sorted(
        enemy_planets,
        key=lambda ep: min(state.distance(ep.ID, mp.ID) for mp in my_planets)
    )

    for target in potential_targets:
        sources = sorted(
            [p for p in my_planets if p.num_ships > 10],
            key=lambda p: state.distance(p.ID, target.ID)
        )

        contribution_plan = []
        total_available = 0
        max_arrival = 0

        # Estimate worst-case (latest) arrival time
        for source in sources:
            distance = state.distance(source.ID, target.ID)
            max_arrival = max(max_arrival, distance)

            projected_defense = projected_ships_at_arrival(state, target.ID, distance)
            required_force = projected_defense + 2

            available = source.num_ships - 10
            if available <= 0:
                continue

            to_send = min(available, required_force - total_available)
            if to_send > 0:
                contribution_plan.append((source, to_send))
                total_available += to_send

            if total_available >= required_force:
                break

        # Abort safely if no plan was formed
        if not contribution_plan:
            continue

        # Double-check: projected defense at final arrival time
        final_arrival_time = max(state.distance(p.ID, target.ID) for p, _ in contribution_plan)
        final_projected_defense = projected_ships_at_arrival(state, target.ID, final_arrival_time)
        final_required_force = final_projected_defense + 1

        if total_available >= final_required_force:
            for planet, ships in contribution_plan:
                issue_order(state, planet.ID, target.ID, ships)
            did_attack = True

    return did_attack





def reinforce_if_under_threat(state):
    reinforced_any = False

    for target in state.my_planets():
        # Identify enemy fleets targeting this planet
        incoming_enemy_fleets = [
            fleet for fleet in state.enemy_fleets()
            if fleet.destination_planet == target.ID
        ]
        if not incoming_enemy_fleets:
            continue

        # Earliest threat
        soonest_fleet = min(incoming_enemy_fleets, key=lambda f: f.turns_remaining)
        arrival_time = soonest_fleet.turns_remaining

        # Predict defense strength at that moment
        projected = projected_ships_at_arrival(state, target.ID, arrival_time)
        if projected >= 0:
            continue  # Planet is safe

        # Reinforcements needed
        ships_needed = abs(projected) + 1
        total_sent = 0

        # Helpers sorted by proximity
        helpers = sorted(
            [p for p in state.my_planets() if p.ID != target.ID and p.num_ships > 1],
            key=lambda p: state.distance(p.ID, target.ID)
        )

        for helper in helpers:
            distance = state.distance(helper.ID, target.ID)
            if distance > arrival_time:
                continue  # Too far

            # Leave a small reserve, but allow flexible help
            reserve = max(1, int(helper.num_ships * 0.2))
            available = helper.num_ships - reserve
            if available <= 0:
                continue

            send_amount = min(ships_needed - total_sent, available)
            if send_amount > 0:
                issue_order(state, helper.ID, target.ID, send_amount)
                total_sent += send_amount

            if total_sent >= ships_needed:
                break

        if total_sent > 0:
            reinforced_any = True

    return reinforced_any



def do_nothing(state):
    return True  # Always succeeds
