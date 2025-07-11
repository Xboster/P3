def if_neutral_planet_available(state):
    return any(state.neutral_planets())


def have_largest_fleet(state):
    my_power = sum(p.num_ships for p in state.my_planets()) + sum(f.num_ships for f in state.my_fleets())
    enemy_power = sum(p.num_ships for p in state.enemy_planets()) + sum(f.num_ships for f in state.enemy_fleets())
    return my_power > enemy_power


def need_reinforcement(state):
    planets = state.my_planets()
    if len(planets) < 2:
        return False
    strongest = max(planets, key=lambda p: p.num_ships)
    weakest = min(planets, key=lambda p: p.num_ships)
    return strongest.num_ships > 2 * weakest.num_ships

