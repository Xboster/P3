

def if_neutral_planet_available(state):
    return any(state.neutral_planets())


def have_largest_fleet(state):
    return sum(planet.num_ships for planet in state.my_planets()) \
             + sum(fleet.num_ships for fleet in state.my_fleets()) \
           > sum(planet.num_ships for planet in state.enemy_planets()) \
             + sum(fleet.num_ships for fleet in state.enemy_fleets())


def if_enemy_planet_available(state):
    return any(state.enemy_planets())


def have_more_planets_than_enemy(state):
    return len(state.my_planets()) > len(state.enemy_planets())


def fleet_in_flight(state):
    return len(state.my_fleets()) > 0


def is_losing(state):
    my_ships = sum(p.num_ships for p in state.my_planets()) + sum(f.num_ships for f in state.my_fleets())
    enemy_ships = sum(p.num_ships for p in state.enemy_planets()) + sum(f.num_ships for f in state.enemy_fleets())
    return my_ships < enemy_ships


def has_strong_planet(state, min_ships=50):
    return any(p.num_ships >= min_ships for p in state.my_planets())
