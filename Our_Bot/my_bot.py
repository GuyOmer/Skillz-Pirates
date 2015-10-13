#!/usr/bin/env python
# coding=utf-8
__author__ = "Team Hadarim 2015"

import sys
import math
import heapq
import copy
# import random
# import cProfile


def enum(*sequential, **named):
    """
    implement enum type

     enum is used to represent constants or values as names.
     helps to avoid errors as it enables us to choose (or compare) fixed options
     by using words (enum.OPTION) instead of integers that represent those options.

    - parameters with */** before name contains optional arguments, and may be empty
    - we used them without the */** before the name.
    :type *sequential: tuple (may be empty)
    :param *sequential: all arguments that passed without specific name (Ex: enum('Me'). 'ME' would be in sequential[0]
    :type **named: dictionary (may be empty)
    :param **named: all arguments that passed with specific name (Ex: enum(me = 'ME'). 'ME' would be in named[me])
    :return: new type - enum
    """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)


causes = enum('NOT_PASSABLE', 'ENEMY')


# Write bot strategies here:
def TwoByTwo(game):
    islands = game.not_my_islands() * 2
    assign = {}
    for p in game.my_pirates():
        if len(islands) == 0:
            islands += game.not_my_islands()
        if len(islands) == 0:
            islands += game.my_islands()
        target = min(islands, key=lambda island: game.distance(island.location, p.location))  # Nearest location
        islands.remove(target)
        if not game.is_capturing(p):
            if target.location in assign:
                assign[target.location].append(p)
            else:
                assign[target.location] = [p]

    for target, pirates in assign.items():
        for pirate in pirates:
            movePirate(pirate, target)


def oneByOne_strategy(game):
    """
    every pirate attack different island.
    pirate choose closest island.
    if there are more pirates than islands, they attack the most valuable island.
    if all island equal, go to closest island
    :param game: the game
    Function Variables:
    @var morePirates: int. number of pirates mor than islands
    @var flag: bool. indicate if send more than 1 pirate to island. True if can send mor pirate. false if already sent
    @var sail: set of pirates that were moved
    """
    # TODO: check why sending game pirate to 2 islands
    # TODO: use updeted 'regroup'
    # TODO: consider: send pirates to our islands that being captured (if would get in time/anyway to reduce distance)
    islands = game.not_my_islands()
    pirates = game.my_pirates()
    pirates = [pirate for pirate in pirates if not game.is_capturing(pirate)]
    assignments = cross_assign(game, pirates, islands, islandScore)
    # sail = set()
    game.debug("assignments: {}".format(assignments))
    for assignment in assignments:
        island = assignment[0]
        pirate = assignment[1]
        # selective_debug(game, "Sending pirate {} to capture island: {}".format(pirate.id, island.id))
        # if pirate not in sail:
        game.debug("Sending pirate {} to capture island: {}".format(pirate.id, island.id))
        movePirate(pirate, island)
        # sail.add(pirate)
    """
    islands = game.not_my_islands()
    other_pirates = [pirate for pirate in pirates if pirate not in sail]
    for pirate in other_pirates:
        islands.sort(key=lambda an_island: (an_island.value, 0-game.distance(pirate, an_island)), reverse=True)
        #                                              ^sort High->Low, 0-distance=> lower distance better
        game.debug("others: pirate {}, island: {}".format(pirate.id, islands))
        game.debug("others: Sending pirate {} to capture island: {}".format(pirate.id, islands[0].id))
        movePirate(pirate, islands[0])
    """


# Choose current bot strategy here:
def runStrategy(game):
    TwoByTwo(game)

# --------------------------------------------------------------------------------------------------- #
# ---------------------------------- DON'T EDIT BELOW THIS LINE ------------------------------------- #
# --------------------------------------------------------------------------------------------------- #

# Globals:
# ----------
last_locs = {}
movements = []
time_to_move = 2
time_for_check = 10
max_turn_time = 0
re_routes = []
enemySpawns = ([], [])
enemiesInRadius_cache = {}
kamikaze_assignments = None
pirates_on_enemies = {}

# Profiler
# ---------------------------------------------------------
# def do_turn(game):
# global rgame
# rgame = game
#
# if game.get_turn() > 200:
#         profiler = cProfile.Profile()
#         profiler.runctx('main()', globals(), locals())
#         profiler.print_stats(sort='cumtime')
#     else:
#         main()
# ---------------------------------------------------------


# def main():
def do_turn(game):
    """

    :type game: game object
    """
    global max_turn_time, last_enemy_count, last_mine_count  # , rgame
    # game = rgame

    starting_time = game.time_remaining()
    mine_count = len(game.my_pirates())
    enemy_count = len(
        [enemy_pirate for enemy_pirate in game.enemy_pirates() if game.is_passable(enemy_pirate.location)])

    if game.get_turn() == 1:
        global radius, attackRadius
        attackRadius = game.get_attack_radius()
        radius = int(math.sqrt(attackRadius))
        locateEnemySpawnsCenters(game)

    if not endGame(game):
        # Current bot strategy
        runStrategy(game)

    proccessMovements(game)
    last_mine_count = mine_count
    last_enemy_count = enemy_count
    turn_time = starting_time - game.time_remaining()
    max_turn_time = max(max_turn_time, turn_time)
    selective_debug(game, "Turn took: {} ms / 100 ms [Max so far: {} ms / 100 ms]".format(turn_time, max_turn_time))


def cross_assign(game, my_pirates, enemy_pirates, score=None):
    """
    create table (list of lists) that assign target enemy to each pirate

    assign to

    :rtype : Table - list of lists
    :param game: the game
    :param my_pirates: list of pirates - my pirates to turn to kamikaze
    :param enemy_pirates: list of pirates - enemy pirates to attack
    :return: table (list of lists) of pirate and enemy target
            format: [ [enemy_pirate, my_pirate, distance(my - enemy)], [...], ...]
    """
    # TODO: ! Try giving way less weight for pirates that were in a tank. More weight to enemies near my islands.
    e = list(enemy_pirates)
    m = list(my_pirates)

    if len(e) == 0 or len(m) == 0:
        return []

    my_table = []
    # Build table
    for i, enemy in enumerate(e):
        row = []
        for j, mine in enumerate(m):
            if score is not None:
                row.append(score(game, enemy, mine))
            else:
                row.append(game.distance(enemy, mine))
        my_table.append(row)

    munk = Munkres()
    answer = []
    index_list = range(len(m))
    while len(my_table) > 0:
        indexes = munk.compute(my_table)
        for row, column in indexes:
            answer.append((e[row], m[index_list[column]]))

        for row, column in sorted(indexes, key=lambda indexi: indexi[1], reverse=True):
            for _row_index, _row in enumerate(list(my_table)):
                del _row[column]

                if len(_row) == 0:
                    my_table.remove(_row)

            index_list.remove(index_list[column])

    return answer


def endGame(game):
    """
    check if need to use strategy for end game, and implement it

    if the current situation would lead us to victory, use 'endGame' strategy:
                    - attack enemy pirates (kamikaze)
                    - Siege enemy base using tank
    :rtype : bool
    :param game: the game
    :return: False if need to continue normal strategy. True if used 'endGame' strategy
    """

    global enemySpawns, kamikaze_assignments, last_mine_count, last_enemy_count

    # Check if it is not time for an end-game yet:
    if not who_will_win(game)[0] == 0:
        selective_debug(game, "Still not end-game.")
        return False

    selective_debug(game, "End game reached :)")
    enemies = [enemy_pirate for enemy_pirate in game.enemy_pirates() if game.is_passable(enemy_pirate.location)]
    # if len(enemies) == 0:
    #     enemies = game.enemy_pirates()

    pirates = []
    for p in game.my_pirates():
        if not game.is_capturing(p):
            pirates.append(p)

    if len(pirates) > 0:
        kamikaze = []
        # TODO: Make one kamikaze pirate a ghost ship?
        # Get kamikaze pirates
        if kamikaze_assignments is None or len(pirates) != last_mine_count or len(enemies) != last_enemy_count:
            kamikaze_assignments = []  # Clear assignments
            attackers = {}
            while len(kamikaze) < len(pirates) and len(enemies) > 0:
                assignments = cross_assign(game, [pirate for pirate in pirates if pirate not in kamikaze], enemies)
                # selective_debug(game, [(row[0].id, row[1].id, row[2]) for row in assignments])
                ratio_count = [0] * len(enemies)
                for assignment in assignments:
                    chosen_enemy = assignment[0]
                    if chosen_enemy in enemies:
                        chosen_pirate = game.get_my_pirate(assignment[1].id)
                        if ratio_count[enemies.index(chosen_enemy)] < 2 and \
                                my_in_range(chosen_pirate, attackers.get(chosen_enemy, chosen_pirate)):

                            attackers[chosen_enemy] = chosen_pirate
                            ratio_count[enemies.index(chosen_enemy)] += 1
                            chosen_pirate = game.get_my_pirate(assignment[1].id)
                            selective_debug(game, "Sending pirate {} to kamikaze on {}".format(
                                chosen_pirate.id, chosen_enemy.id
                            ))
                            kamikaze_assignments.append((chosen_enemy.id, chosen_pirate.id))
                            movePirate(chosen_pirate, chosen_enemy, kamikaze=True)
                            kamikaze.append(chosen_pirate)
                        else:
                            enemies.remove(chosen_enemy)
        else:
            selective_debug(game, "Resuming kamikaze assignments from last turn.")
            selective_debug(game, "Last turn enemy count: {} || now: {}".format(last_enemy_count, len(enemies)))
            for assignment in kamikaze_assignments:
                chosen_pirate = game.get_my_pirate(assignment[1])
                chosen_enemy = game.get_enemy_pirate(assignment[0])
                selective_debug(game, "Sending pirate {} to kamikaze on {}".format(
                    chosen_pirate.id, chosen_enemy.id
                ))
                movePirate(chosen_pirate, chosen_enemy, kamikaze=True)
                kamikaze.append(chosen_pirate)

        # *****Send pirates to island if they can capture it before enemies revive ******
        leftover_pirates = set([p for p in pirates if p not in kamikaze])
        tank_pirates = []

        if len(leftover_pirates) > 0:
            islands = game.not_my_islands()
            if len(islands) > 0:
                nearest_islands = []
                for pirate in leftover_pirates:
                    nearest_islands.append(min(islands, key=lambda isl: game.distance(pirate, isl)))
                # assing spawn to islands (not my islands)
                island_spawn = {}
                for island in islands:
                    island_spawn[island] = min(enemySpawns[0],
                                               key=lambda a_spawn: game.distance(pirate, nearestPassableLoc(game, a_spawn)))
                # check if can capture island and send pirates
                for pirate_index, pirate in enumerate(leftover_pirates):
                    nearest_island = nearest_islands[pirate_index]
                    nearest_spawn = island_spawn[nearest_island]
                    enemys_in_spawn = enemySpawns[2][enemySpawns[0].index(nearest_spawn)]
                    c_island_time = game.distance(pirate, nearest_island) + nearest_island.capture_turns + \
                                    game.distance(nearest_island, nearestPassableLoc(game, nearest_spawn))
                    revive = min([game.get_enemy_pirate(enemy_id) for enemy_id in enemys_in_spawn], key=lambda enemy: enemy.turns_to_revive)
                    if c_island_time <= revive:
                        # send pirate to island
                        movePirate(pirate, nearest_island)
                        game.debug("pirate: {} go to island: {}".format(pirate.id, nearest_island.id))
                    else:
                        # send pirate to spawn
                        tank_pirates.append(pirate)
            else:
                tank_pirates = leftover_pirates

        for spawn, spawn_enemy_count in zip(enemySpawns[0], enemySpawns[1]):
            if len(tank_pirates) > 0:
                # Choose pirates for tank
                assignments = cross_assign(game, tank_pirates, [spawn] * spawn_enemy_count)
                # selective_debug(game, assignments)
                spawn_tank_pirates = set()
                for assignment in assignments:
                    spawn_tank_pirates.add(assignment[1])
                    tank_pirates.discard(assignment[1])

                selective_debug(game, "Tank is: {} for spawn {}".format([p.id for p in spawn_tank_pirates], spawn))
                selective_debug(game, "Tank pirates left: {}".format([p.id for p in tank_pirates]))

                with Tank(game,
                          _pirates=list(spawn_tank_pirates),
                          _identifier=spawn,
                          _starting_location=nearestPassableLoc(game, spawn, is_kamikaze=True),
                          _is_kamikaze=True) as myTank:
                    # Move tank to enemy spawn
                    myTank.moveTank(spawn)
    return True


def who_will_win(game):
    """ check who will win if the game will stay the same, and how many turns it will take.
     who_wins[0] - who will win
     0 - we,1 - enemy,2 - tie
     who_wins[1] - how many turns until game over """
    # TODO: also take in account islands that are beging captured (i.e enemy about to capture our only island and we have less score)
    who_wins = [0, 0]
    turns_left = game.get_max_turns() - game.get_turn()
    last_points = game.get_last_turn_points()  # [0] = ours [1] = enemy
    if last_points[0] == 0 and last_points[1] == 0:  # no one is getting points
        if game.get_my_score() == game.get_enemy_score():
            who_wins[0] = 2
        else:
            who_wins[0] = int(game.get_enemy_score() > game.get_my_score())
        who_wins[1] = turns_left
    elif last_points[0] == 0:  # just the enemy is getting points
        turns_to_win = math.ceil((game.get_max_points() - game.get_enemy_score()) / float(last_points[1]))
        if turns_to_win > turns_left:
            if game.get_my_score() == game.get_enemy_score() + last_points[1] * turns_left:
                who_wins[0] = 2
            else:
                who_wins[0] = int(game.get_my_score() < game.get_enemy_score() + last_points[1] * turns_left)
            who_wins[1] = turns_left
        else:
            who_wins[0] = 1
            who_wins[1] = turns_to_win
    elif last_points[1] == 0:  # just we are getting points
        turns_to_win = math.ceil((game.get_max_points() - game.get_my_score()) / float(last_points[0]))
        if turns_to_win > turns_left:
            if game.get_enemy_score() == game.get_my_score() + last_points[0] * turns_left:
                who_wins[0] = 2
            else:
                who_wins[0] = int(game.get_enemy_score() > game.get_my_score() + last_points[0] * turns_left)
            who_wins[1] = turns_left
        else:
            who_wins[0] = 0
            who_wins[1] = turns_to_win
    else:  # both getting points
        my_turns_to_win = math.ceil((game.get_max_points() - game.get_my_score()) / float(last_points[0]))
        enemy_turns_to_win = math.ceil((game.get_max_points() - game.get_enemy_score()) / float(last_points[1]))
        if my_turns_to_win == enemy_turns_to_win:
            who_wins[0] = 2
            who_wins[1] = my_turns_to_win
        else:
            who_wins[0] = int(my_turns_to_win > enemy_turns_to_win)
            who_wins[1] = max(my_turns_to_win, enemy_turns_to_win)
    return who_wins


def kamikazeScore(game, my_pirate, enemy_pirate, tank_pirates):
    """
    calculate kamikaze score. Inverse(i.e. higher score indicate the pirate is not good kamikaze)
    consider multiple elements:
            - distance between enemy and pirate (base of calculation)
            - our pirate in tank
            - enemy distance from our island
            - enemy distance from natural island
            - enemy's closest(best score) island value
    :param game: the game
    :param my_pirate: our pirate (Pirate Object)
    :param enemy_pirate: enemy pirate (Pirate Object)
    :param tank_pirates: list of pirates that are in tank mode
    :rtype float
    :return score(lower is better)
    Function Variables:
    @var distance_from_pirate: distance between pirates. lower is better
    @var value_from_island: kamikaze value increment because of island. higher is better
    @var value_from_tank: kamikaze value decrement because pirate in tank. lower is better
    """
    # TODO: consider build and use function to calculate distance by turns (not squared)
    max_inc = 2.0
    min_inc = 1.0
    distance_from_pirate = game.distance(my_pirate, enemy_pirate)
    if game.is_capturing(enemy_pirate):
        value_from_island = max_inc  # if enemy capture island, max impact.
    else:  # else, value between 1 and 2, by island score
        islands = game.my_islands() + game.neutral_islands()  # not enemies islands
        islands.sort(key=lambda island: islandScore(game, island, enemy_pirate))  # sort island by value to enemy
        value_from_island = (1.0 / islandScore(game, islands[0], enemy_pirate)) * (
            max_inc - min_inc) + 1  # Normalize value between 1 and 2
    if my_pirate in tank_pirates:
        value_from_tank = max_inc
    else:
        value_from_tank = min_inc
    score = distance_from_pirate * value_from_tank / value_from_island
    return score


def islandScore(game, island, pirate=None):
    """
    calculate island score. can work with our pirate or with enemy's
    Inverse(i.e. lower score indicate better island)
    consider multiple elements:
            - island value
            - island time to capture
            - island owner
            - distance from pirate (optional)
    formula:
        score = {[(time to capture) + distance] / value} / opponent_island
                                           ^                     ^
                                        optional   if island belongs to other team
    - default owner is us (game.ME)
    :param game: the game
    :param island: island to score
    :param pirate: Optional - pirate to calculate distance from. may be any LocationObject, not just pirate
    :rtype float
    :return score of an island (lower is better)
    """
    # TODO: consider add value to islands nearby (more islands=more value), ~ only with bool parameter
    # TODO: consider add 1 to score to ensure that score>1 ()
    opponent_island = 1.5  # constant value if island belongs to other team
    capture_time = island.capture_turns
    if pirate is not None:
        # if island.location == pirate.location:
        #     score = capture_time - island.turns_being_captured
        # else:
        #     score = game.distance(pirate, island) + capture_time
        score = game.distance(pirate, island) + capture_time
        score /= float(island.value)
        pirate_owner = pirate.owner
    else:
        score = island.capture_turns
        score /= island.value
        pirate_owner = game.ME
    if pirate_owner != island.owner and island.owner != game.NEUTRAL:  # island belongs to the other team
        score /= opponent_island
    # game.debug("pirate: {}, island: {}, score: {}".format(pirate.id, island.id, score))
    return score


def locateEnemySpawnsCenters(game):
    global enemySpawns

    spawns = []
    spawns_enemies = []
    for enemy in game.all_enemy_pirates():
        initial_loc = enemy.initial_loc
        for spawn_index, spawn in enumerate(spawns):
            if pathNotPassable(game, initial_loc, spawn):
                avr_r = (initial_loc[0] + spawn[0]) / 2
                avr_c = (initial_loc[1] + spawn[1]) / 2
                spawns[spawn_index] = (avr_r, avr_c)
                spawns_enemies[spawn_index].append(enemy.id)
                break
        else:  # No break
            spawns.append(initial_loc)  # New spawn
            spawns_enemies.append([enemy.id])

    spawns_enemy_count = [len(enemies) for enemies in spawns_enemies]

    selective_debug(game, "Enemy spawns located: {}".format(spawns))

    enemySpawns = (list(spawns), list(spawns_enemy_count), list(spawns_enemies))


def pathNotPassable(game, loc_a, loc_b):
    current = loc_a
    i = 0
    while current != loc_b:
        path = game.get_directions(current, loc_b)  # Get the path between two locations
        for pathi in path:
            if pathi == '-':
                path.remove(pathi)

        if len(path) == 0:
            break

        current = game.destination(current, path[i % 2 * -1])  # Zig-Zag the route (will reduce false-negatives)
        if game.is_passable(current):  # Make sure we can't step there!
            return False
        i += 1
    return True


# --------------------------------------------------------------------------------------------------- #
# -------------------------------------- MOVEMENT CODE BELOW ---------------------------------------- #
# --------------------------------------------------------------------------------------------------- #


def movePirate(pirate, dest, kamikaze=False, in_tank=False):
    """
    update global variable 'movements' to include pirate movement.


    :param pirate: our pirate (pirate Object) to move
    :param dest: locationObject - the pirate destination
    :param kamikaze: boolean - True if kamikaze mode. False otherwise.
    :param in_tank: boolean - True if Tank mode. False otherwise.
    """
    global movements, pirates_on_enemies

    if type(dest) is not tuple:
        dest = dest.location

    for move in movements:  # If already has pirate in movements, remove move and add new one
        if move[0].id == pirate.id:
            movements.remove(move)

    movements.append((pirate, dest, kamikaze, in_tank))

    if hasattr(dest, 'is_lost') and hasattr(dest, 'id'):  # Check if object of type pirate
        pirates_on_enemies[pirate.id] = dest.id


def createPaths(game, pirate, dest, is_kamikaze=False, old_dest=None, re_routed=False, alternating=True):
    """
    Calculate pirate possible paths to desired location

    :param game: the game
    :param pirate: The pirate to check path for. (Pirate Object)
    :param dest: The pirate destination (LocationObject)
    :param is_kamikaze: indicate if pirate in kamikaze mode. Default value: False
    :param re_routed: indicate if pirate was already re-routed around non passable location from this function
    :rtype : Tuple of lists
    :return: Tuple (size 2) of lists (each in size 2).
            -First list contains paths
            -Second list contains cancel cause, if any
    """
    global causes, last_locs, re_routes, pirates_on_enemies

    reset = False
    done_rerouting = False
    # Check if was re-routed:
    for reroute in list(re_routes):
        # If this re-route includes my pirate, re-route him
        if pirate in reroute[0]:
            reroute_index = reroute[0].index(pirate)
            pirate_old_dest = reroute[1][reroute_index]
            reroute_dest = reroute[2]

            # Check if everyone got to re-route target:
            for sub_pirate in reroute[0]:
                sub_pirate = game.get_my_pirate(sub_pirate.id)
                if (len(reroute[0]) == 1 and sub_pirate.location != reroute_dest) or \
                        (len(reroute[0]) > 1 and (not my_in_range(sub_pirate.location, reroute_dest))):
                    break  # Some pirate still has not reached target
            else:  # No breaks
                selective_debug(game,
                                "Pirate {} reached re-route target, returning to original destination".format(pirate.id))
                re_routes.remove(reroute)  # Done re-routing
                done_rerouting = True
                break

            # If still on way to original final dest
            if old_dest is None:
                old_dest = dest

            still_on_enemy = False
            if pirate.id in pirates_on_enemies:
                still_on_enemy = game.get_enemy_pirate(pirates_on_enemies[pirate.id]).location == old_dest

            # Kept same final destination
            if my_in_range(old_dest, pirate_old_dest, custom_attack_radius=1) or still_on_enemy:
                dest = reroute_dest  # Update dest to re-route target
            else:  # Changed final destination
                selective_debug(game,
                                "Pirate {} changed final target (from {} to {}), cancelling re-route.".format(
                                    pirate.id, pirate_old_dest, old_dest))
                # This breaks re-routing for all pirates invloved
                reset = True  # Means that all pirates moves should be re-calculated
                done_rerouting = True

                if len(reroute[0]) > 2:
                    # Remove self from re-route
                    reroute[0] = tuple([item for index, item in enumerate(reroute[0]) if index != reroute_index])
                    reroute[1] = tuple([item for index, item in enumerate(reroute[1]) if index != reroute_index])
                    reroute[3] = tuple([item for index, item in enumerate(reroute[3]) if index != reroute_index])
                else:
                    re_routes.remove(reroute)  # Done re-routing
            break

    last_loc = None
    if done_rerouting and pirate in last_locs:
        last_loc = last_locs[pirate]
        selective_debug(game, "Pirate {} last loc is: {}".format(pirate.id, last_loc))

    path1 = game.get_directions(pirate, dest)[alternating * ((game.get_turn() % 2) * -1)]
    path1_dest = game.destination(pirate, path1)
    path1_cancel_cause = ''
    path1_good = game.is_passable(path1_dest) \
        and len(path1) > 0 \
        and not (is_kamikaze and path1_dest in [_isl.location for _isl in game.islands()]) \
        and path1_dest != last_loc \
        and len([ep for ep in game.enemy_pirates() if my_in_range(path1_dest, ep, custom_attack_radius=1)])\
        == 0

    if not path1_good:
        # selective_debug(game, "Path {} not good for {}".format(path1, pirate))
        path1 = '-'
        path1_cancel_cause = causes.NOT_PASSABLE

    path2 = game.get_directions(pirate, dest)[alternating * ((game.get_turn() + 1) % 2) * -1 - (not alternating)]
    path2_dest = game.destination(pirate, path2)
    path2_cancel_cause = ''
    path2_good = game.is_passable(path2_dest) \
        and len(path2) > 0 \
        and not (is_kamikaze and path2_dest in [isl.location for isl in game.islands()]) \
        and path2_dest != last_loc \
        and len([ep for ep in game.enemy_pirates() if my_in_range(path2_dest, ep, custom_attack_radius=1)])\
        == 0

    if path2 == path1:
        path2 = '-'

    if not path2_good:
        # selective_debug(game, "Path {} not good for {}".format(path2, pirate))
        path2 = '-'
        path2_cancel_cause = causes.NOT_PASSABLE

    if not path1_good and not path2_good and not re_routed:
        new_target = None
        if type(pirate) is tuple:
            new_target = obstaclePass(game, pirate, dest, is_kamikaze=is_kamikaze)
        elif hasattr(pirate, 'location'):
            new_target = obstaclePass(game, pirate.location, dest, is_kamikaze=is_kamikaze)
        if new_target is not None:
            return createPaths(game, pirate, new_target, is_kamikaze, old_dest=dest, re_routed=True)
    elif re_routed and hasattr(pirate, 'location'):
        # Add to global
        re_routes.append([(pirate,), (old_dest,), dest, ((path1, path2),)])

    return [path1, path2], [path1_cancel_cause, path2_cancel_cause], reset


def changePath(game, pirates, paths, dests, cancel_causes, my_pirate, is_kamikaze, new_target=None, new_path=None):
    index = pirates.index(my_pirate)
    if new_target is not None:
        path, cancel_cause, reset = createPaths(game, my_pirate, new_target, is_kamikaze)
    elif new_path is not None:
        path, cancel_cause = [new_path, '-'], ['', '']
    else:
        return

    paths[index] = path
    dests[index] = (game.destination(my_pirate, path[0]),
                    game.destination(my_pirate, path[1]))
    cancel_causes[index] = cancel_cause
    return path


def proccessMovements(game):
    """
    process all pirates movements

    :param game: the game

    :var global movements:
    :var global time_to_move: remaining turn time
    :var global re_routes:


    Function Variables:

    @var pirate: list of pirates
    @var paths: list of lists of directions. Each inner list contains 2 possible directions
                format: [ ['n','w'], ['e', '-'], ... ]
    @var dests:
    @var final_dests:
    @var cancel_causes:
    @var escapes:
    @var kamikaze:
    @var in_tank:
    """
    global movements, last_locs, time_to_move, time_for_check, re_routes

    pirates = []
    start_paths = []
    paths = []
    dests = []
    final_dests = []
    cancel_causes = []
    escapes = []
    is_rerouted = []
    kamikaze = []
    in_tank = []

    selective_debug(game, "---------------------------")

    # Check if all re-routed pirates are still alive
    for reroute in list(re_routes):
        reroute[0] = [game.get_my_pirate(pirate.id) for pirate in reroute[0]]
        for pirate in reroute[0]:
            if pirate not in game.my_pirates():
                # This breaks re-routing for all pirates invloved
                re_routes.remove(reroute)
                break

    # Un-pack movements
    reset = True
    while reset:
        reset = False
        for move_i in xrange(len(movements)):
            move = movements[move_i]
            pirate, dest, is_kamikaze, is_tank = move[0], move[1], move[2], move[3]
            old_dest = tuple(dest)
            dest = nearestPassableLoc(game, dest, dests, pirates, is_kamikaze=is_kamikaze)
            path, cancel_cause, reset = createPaths(game, pirate, dest, is_kamikaze, old_dest=old_dest)

            if reset:
                break

            def assign(lst, val):
                try:
                    lst[move_i] = val
                except IndexError:
                    lst.append(val)

            assign(final_dests, old_dest)
            assign(pirates, pirate)
            assign(paths, path)
            assign(start_paths, list(path))
            assign(dests, (game.destination(pirate, path[0]), game.destination(pirate, path[1])))
            assign(cancel_causes, cancel_cause)
            assign(escapes, False)
            assign(is_rerouted, False)
            assign(kamikaze, is_kamikaze)
            assign(in_tank, is_tank)

            selective_debug(game, "Pirate {} target: {} ; final destination: {}".format(pirate.id, old_dest, dest))

    # Add non-moving pirates
    for not_moving_pirate in game.my_pirates():
        if not_moving_pirate not in pirates:
            pirates.append(not_moving_pirate)
            final_dests.append(not_moving_pirate.location)
            paths.append(['-', '-'])
            start_paths.append(['-', '-'])
            dests.append((not_moving_pirate.location, not_moving_pirate.location))
            cancel_causes.append(['', ''])
            escapes.append(False)
            is_rerouted.append(False)
            kamikaze.append(False)
            in_tank.append(False)

            selective_debug(game, "Pirate {} target: {} ; final destination: {}".format(
                not_moving_pirate.id, not_moving_pirate.location, not_moving_pirate.location))

    selective_debug(game, "---------------------------")

    # Make sure that each path is safe to travel
    for x in xrange(3):  # This should run 3 times so that pirates will be updated about how other pirates paths changed
        time_for_check_start = game.time_remaining()
        if time_for_check_start < time_for_check + time_to_move:  # No time for another check
            selective_debug(game,
                            "No time for another check, breaking. [Done: {} ; Time left: {} ; Max time per check: {}]".
                            format(x, time_for_check_start, time_for_check))
            break

        selective_debug(game, "---------------------------")
        for pirate, path in zip(pirates, paths):
            selective_debug(game, "Pirate {} paths: {}".format(pirate.id, path))
        selective_debug(game, "---------------------------")

        for i in xrange(len(pirates)):
            pirate, path, dest, start_path = pirates[i], paths[i], dests[i], start_paths[i]
            rerouted, escaped, is_kamikaze, is_tank = is_rerouted[i], escapes[i], kamikaze[i], in_tank[i]
            pirate_index = i

            # selective_debug(game, "Pirate {} paths: {}".format(pirate.id, path))
            # Start with checking possible paths
            for path_index, dest in zip(xrange(len(path)), dest):
                checkPath(game, pirates, paths, dests, cancel_causes, escapes, is_rerouted, final_dests, kamikaze,
                          pirate, path_index, dest, is_kamikaze)
                dests[pirate_index] = (game.destination(pirate, paths[pirate_index][0]),
                                       game.destination(pirate, paths[pirate_index][1]))

                path = paths[pirate_index]
                # dest = dests[pirate_index]
                # If path is not good, make sure it is defined '-' (and not None) and debug canceling reason
                if path[path_index] is None or path[path_index] == '-':
                    paths[pirate_index][path_index] = '-'
                    if start_path[path_index] != '-':
                        selective_debug(game, "Pirate {} path '{}' canceled because {}.".format(
                            pirate.id, start_path[path_index],
                            [causes.reverse_mapping[item] for
                             item in [cancel_causes[pirate_index][path_index]] if item in [0, 1]]))

            # If both paths are bad, re-route or escape
            if path[0] == '-' and path[1] == '-':
                if not rerouted:  # If not already tried re-routing
                    selective_debug(game, "Pirate {} trying rerouting".format(pirate.id))
                    is_rerouted[pirate_index] = True  # tag as re-routed
                    result = reroutePirates(game, pirates, paths, dests, kamikaze, final_dests, cancel_causes,
                                            start_paths, pirate)
                    # None = no re-route found or no need to re-route
                    if result is not None:
                        pirates_to_move, old_targets, new_target = result

                        # Calc paths for new destination for each pirate
                        new_paths = []
                        for move_pirate in pirates_to_move:
                            move_index = pirates.index(move_pirate)
                            new_path = changePath(game, pirates, paths, dests, cancel_causes, move_pirate,
                                                  kamikaze[move_index],
                                                  new_target=new_target)
                            new_paths.append(tuple(new_path))
                            is_rerouted[move_index] = True  # tag as re-routed
                            selective_debug(game, "Re-routed pirate {} to {} to go around {}.".format(
                                move_pirate.id, new_target,
                                [causes.reverse_mapping[item] for item in
                                 cancel_causes[move_index] if item in range(2)]))

                        re_routes.append([result[0], result[1], result[2], tuple(new_paths)])  # Add to global
                        continue  # Succesfully rerouted, continue to proccess next pirate

                selective_debug(game, "Pirate {} trying escaping".format(pirate.id))
                # No re-route found or no need to re-route, try escaping
                escape_direction, moved_pirates = escapeEnemy(game, pirates, paths, dests, final_dests, kamikaze,
                                                              cancel_causes, escapes, is_rerouted, pirate)
                if escape_direction != '-':  # Found a new way
                    selective_debug(game, "Pirate {} moving to the {} to escape.".format(pirate.id, escape_direction))
                    changePath(game, pirates, paths, dests, cancel_causes, pirate, is_kamikaze,
                               new_path=escape_direction)
                    escapes[i] = True  # tag as escaped
                    chainEscape(game, pirates, paths, dests, is_rerouted, final_dests, kamikaze, cancel_causes, escapes,
                                moved_pirates, pirate, escape_direction)

        time_for_check = max(time_for_check, time_for_check_start - game.time_remaining())

    # Do the actual sailing
    time_to_move_start = game.time_remaining()
    for pirate, path, dest in zip(pirates, paths, dests):
        if not pirate.is_lost:
            path1 = path[0]
            path2 = path[1]
            last_locs[pirate] = pirate.location

            if path1 is not None and path1 != '-':
                selective_debug(game, "Pirate {} moving to the {}".format(pirate.id, path1))
                game.set_sail(pirate, path1)
            elif path2 is not None and path2 != '-':
                selective_debug(game, "Pirate {} moving to the {}".format(pirate.id, path2))
                game.set_sail(pirate, path2)
            else:
                selective_debug(game, "Stopped pirate #{} from moving.".format(pirate.id))
                game.set_sail(pirate, '-')  # Stay in place
        else:
            if pirate in last_locs:
                last_locs.pop(pirate)
    time_to_move = max(time_to_move, time_to_move_start - game.time_remaining())

    # Clear movements, cache
    enemiesInRadius_cache.clear()
    movements[:] = []


def chainEscape(game, pirates, paths, dests, is_rerouted, final_dests, kamikaze, cancel_causes, escapes, moved_pirates,
                pirate, escape_direction):
    moved_pirates = list(moved_pirates)  # frozenset -> list
    for i_pirate, i_path in moved_pirates:  # Pirates that occupy chosen direction
        if i_pirate.id == pirate.id:
            continue

        i_pirate_index = pirates.index(i_pirate)
        new_path = escape_direction if paths[i_pirate_index][i_path] == '-' else '-'

        # Don't move pirates to islands
        if game.destination(i_pirate, new_path) in [isl.location for isl in game.islands()]:
            selective_debug(game, "Pirate {} will be on island with chain escape to the '{}'.".format(
                i_pirate.id, new_path))
            new_path, pirates_to_move = escapeEnemy(game, pirates, paths, dests, final_dests, kamikaze, cancel_causes,
                                                    escapes, is_rerouted, i_pirate, force_escape=True)
            if new_path != '-':
                chainEscape(game, pirates, paths, dests, is_rerouted, final_dests, kamikaze, cancel_causes, escapes,
                            pirates_to_move, i_pirate, new_path)
            else:
                new_path = escape_direction if paths[i_pirate_index][i_path] == '-' else '-'

        selective_debug(game, "Pirate {} moved pirate {} to '{}' so he can escape.".format(
            pirate.id, i_pirate.id, new_path
        ))
        paths[i_pirate_index][i_path] = new_path
        new_dest = nearestPassableLoc(game, game.destination(i_pirate, new_path), no_pirates=True)
        if i_path == 0:
            dests[i_pirate_index] = (new_dest, dests[i_pirate_index][1])
        else:
            dests[i_pirate_index] = (dests[i_pirate_index][0], new_dest)

        # is_rerouted[i_pirate_index] = False
        final_dests[i_pirate_index] = new_dest

        # Check new collisions:
        new_moved_pirates = []
        for other_dest, other_pirate in zip(dests, pirates):
            if other_pirate.id != i_pirate.id:
                selective_debug(game, "Pirate {} dests: {} || Pirate {} (chained) new dest: {}".format(other_pirate.id,
                                                                                                     other_dest,
                                                                                                     i_pirate.id,
                                                                                                     new_dest))
                change = 0
                if other_dest[0] == '-':
                    other_dest = list(other_dest[::-1])  # Reverse dest list so real path will be first
                    change = 1
                # If both his paths will collide with current path:
                if other_dest[0] == new_dest:
                    new_moved_pirates.append((other_pirate, 0 - change))
                elif other_dest[1] == new_dest:
                    new_moved_pirates.append((other_pirate, 1 - change))
                else:
                    continue
                selective_debug(game, "Pirate {} colliding with pirate {} escape, moving him aswell.".format(
                    other_pirate.id, i_pirate.id))

        selective_debug(game, "Moved pirate {} paths: {}".format(i_pirate.id, paths[i_pirate_index]))

        if len(new_moved_pirates) > 0:
            chainEscape(game, pirates, paths, dests, is_rerouted, final_dests, kamikaze, cancel_causes,
                        escapes, new_moved_pirates, i_pirate, escape_direction)


def checkPath(game, pirates, paths, dests, cancel_causes, escapes, is_rerouted, final_dests, kamikaze, my_pirate,
              path_index, my_dest, is_kamikaze):
    """
    check pirate path to ensure our pirate can go in this path, and if so, that he wouldn't die

    the function checks multiple

    :param game: the game

    following parameters are parallel lists - each index refers to the same pirate and describe pirate attribute
            For each pirate in pirates[index], there are paths in paths[index], destination in dests[index] and so on...
    :param pirates: list of pirates(our) that move in current turn
    :param paths: list of lists of directions. Each inner list contains 2 possible directions
                format: [ ['n','w'], ['e', '-'], ... ]
    :param dests: list of lists of destinations. Each inner list contains 2 possible destinations
                format: [ [(3,6),(4,5)], [(26,12), (25,13)], ... ]
                inner lists parallel to paths's inner lists:
                Each destination is the location the pirate would be in the next turn if he would take the parallel path
    :param cancel_causes:list of lists of cancel path causes. Each inner list contains 2
                format:
                inner lists parallel to paths's inner lists:
                Each cause is the cause that we cancel the parallel path
    :param escapes: list of booleans. indicate if matching pirate is trying to escape


    :param my_pirate: the pirate to check his path
    :param path_index: current path's index to check (in pirates paths - can be [0] or [1])
    :param my_dest: the destination that the pirate would be at if he takes paths[pirate][path_index]
    :param is_kamikaze: bool. indicate if my_pirate in kamikaze mode. True if pirate in kamikaze mode. False otherwise

    :return: bool indicating whether a change to paths was made
    """
    global movements, radius, causes

    list_index = pirates.index(my_pirate)

    selective_debug(game, "Pirate {} checking path '{}' out of {}:".format(my_pirate.id,
                                                                           paths[list_index][path_index],
                                                                           paths[list_index]))

    enemies = enemiesInRadius(game, my_dest)
    # selective_debug(game, "Pirate {} enemies: {}".format(my_pirate.id, enemies))

    if len(enemies) == 0:
        return False  # Good path
    else:
        for enemy in enemies:
            if my_in_range(my_dest, enemy, custom_attack_radius=1):
                selective_debug(game, "Pirate {} is going to collide with enemy {} if he goes {}".format(
                    my_pirate.id, enemy.id, paths[list_index][path_index]))
                paths[list_index][path_index] = '-'
                cancel_causes[list_index][path_index] = causes.NOT_PASSABLE
                return True  # Not a good path

    if paths[list_index][path_index] == '-':
        return False  # Good path

    # Test if some other pirate will occupy destination for sure
    for other_index, other_pirate in enumerate(pirates):
        if other_pirate.id != my_pirate.id:
            other_dest = dests[other_index]
            # If both his paths will collide with current path:
            if other_dest[0] == my_dest and other_dest[1] == my_dest:
                selective_debug(game, "Pirate {} is going to collide with {} if he goes {}".format(
                    my_pirate.id, other_pirate.id, paths[list_index][path_index]))
                paths[list_index][path_index] = '-'
                cancel_causes[list_index][path_index] = causes.NOT_PASSABLE
                return True  # Not a good path

    # Try getting other pirates to help my_pirate survive
    got_help, force_size = helpPirate(game, enemies, pirates, paths, dests, escapes, is_rerouted, final_dests, kamikaze,
                                      cancel_causes, my_pirate, my_dest, is_kamikaze)
    if got_help is not None:
        return got_help

    if is_kamikaze:
        # Test if gonna be on an island (can't fight if so)
        if my_dest in [isl.location for isl in game.islands()]:
            selective_debug(game,
                            "Pirate {} is going to be on an island if he goes {} - he won't survive battle".format(
                                my_pirate.id, paths[list_index][path_index]))
            paths[list_index][path_index] = '-'
            cancel_causes[list_index][path_index] = causes.NOT_PASSABLE
            return True  # Not a good path

        enemies_dead = []
        for enemy in enemies:
            updated_dests = list(dests)
            updated_pirates = list(pirates)
            updated_dests.remove(updated_dests[list_index])
            updated_pirates.remove(my_pirate)
            enemy_destination = enemy.location  # game.destination(enemy, game.get_directions(enemy, my_pirate)[0])

            # enemy_no_longer_threat = False
            willDie = pirateWillDie(game, enemy, pirates, dests, kamikaze_target=True)
            if willDie:
                # Assume enemy will be escaping (to ensure my_pirate safety)
                enemy_escape_path, moved_pirates = escapeEnemy(game, pirates, paths, dests, final_dests, kamikaze,
                                                               cancel_causes, escapes, is_rerouted, enemy)
                enemy_destination = game.destination(enemy, enemy_escape_path)
                # enemy_no_longer_threat = not my_in_range(enemy_destination, my_dest)
                selective_debug(game, "Pirate {} - enemy {} will die and be trying to escape to the '{}'".format(
                    my_pirate.id, enemy.id, enemy_escape_path
                ))

                willDie = pirateWillDie(game, enemy, pirates, dests, enemy_destination, kamikaze_target=True)

            # Check if my_pirate actually killed an enemy (if he would also be killed without my_pirate)
            if not pirateWillDie(game, enemy, updated_pirates, updated_dests, enemy_destination):
                if willDie:
                    selective_debug(game, "Pirate {} will cause enemy {} to die if he goes {}".format(
                        my_pirate.id, enemy.id, paths[list_index][path_index]))
                    # return False  # Can kamikaze
                    enemies_dead.append(enemy)
                # elif enemy_no_longer_threat:
                #     if force_size >= len(enemies) - 1:
                #         selective_debug(game, "Pirate {} will cause enemy {} to die if he goes {}"
                #                               " - no longer a threat".format(my_pirate.id, enemy.id,
                #                                                              paths[list_index][path_index]))
                #         return False  # Can survive

            selective_debug(game, "Pirate {} will not cause enemy {} to die if he goes {}".format(
                my_pirate.id, enemy.id, paths[list_index][path_index]))

        friends_dead = []
        # After dead enemies got counted, count dead friends:
        for pirate, pdest in zip(pirates, dests):
            if pirate != my_pirate:
                shared_enemy = False
                for _pdest in pdest:
                    pirate_enemies = enemiesInRadius(game, _pdest)
                    for pirate_enemy in pirate_enemies:
                        if pirate_enemy in enemies:
                            shared_enemy = True
                            break

                if shared_enemy and pirateWillDie(game, pirate, pirates, dests, paths, escapes, is_rerouted,
                                                  final_dests, kamikaze, cancel_causes, my_dest, is_kamikaze):
                    friends_dead.append(pirate)

        if len(enemies_dead) >= len(friends_dead) + 1:
            selective_debug(game, "Pirate {} found {} enemies dead: {} || {} friends dead {}".format(my_pirate.id,
                                                                                                     len(enemies_dead),
                                                                                                     [ep.id for ep in enemies_dead],
                                                                                                     len(friends_dead),
                                                                                                     [mp.id for mp in friends_dead]))
            return False  # Can survive

    selective_debug(game, "Pirate {} path '{}' canceled - ENEMY".format(my_pirate.id, paths[list_index][path_index]))
    paths[list_index][path_index] = '-'
    cancel_causes[list_index][path_index] = causes.ENEMY
    return True  # Not a good path


def helpPirate(game, enemies, pirates, paths, dests, escapes, is_rerouted, final_dests, kamikaze, cancel_causes,
               my_pirate, my_dest, is_kamikaze):
    # global radius
    if len(enemies) == 0:  # or not pirateWillDie(game, my_pirate, pirates, dests, checked_pirate_location=my_dest):
        selective_debug(game, "Pirate {} will survive on destination {}".format(my_pirate.id, my_dest))
        return False, 0  # Good path, won't die

    supporting_pirates = {}
    paths_to_cancel = {}
    paths_to_add = {}
    for pirate, dest, path, escaped in zip(pirates, dests, paths, escapes):
        if len(supporting_pirates) < len(enemies) and pirate != my_pirate:
            pirate_index = pirates.index(pirate)
            relevent_dests = [_dest
                              for _dest_index, _dest in enumerate(dest)
                              if ((is_kamikaze and not escaped)
                                  or (_dest != pirate.location) or (dest[1 - _dest_index] == pirate.location))
                              and _dest not in [isl.location for isl in game.not_my_islands()]]

            if len(relevent_dests) > 0:
                good_dests_count = 0
                good_path_index = None
                for relevent_dest_index, relevent_dest in enumerate(relevent_dests):
                    if my_in_range(relevent_dest, my_dest):
                        good_dests_count += 1
                        good_path_index = dest.index(relevent_dest)
                        continue

                if good_dests_count == 2:
                    supporting_pirates[pirate] = relevent_dests  # Good already, no need to force path
                    selective_debug(game, "Pirate {} is supported by {} with both dests good ({})".format(
                        my_pirate.id, pirate.id, relevent_dests))
                    continue

                # One of the paths is actually good
                if good_path_index is not None:
                    paths_to_cancel[pirate_index] = 1 - good_path_index
                    supporting_pirates[pirate] = relevent_dests
                    selective_debug(game, "Pirate {} is supported by {} with path '{}' good".format(
                        my_pirate.id, pirate.id, path[good_path_index]))
                    continue

                # if escaped:
                #     for _dir in ['n', 'e', 's', 'w']:
                #         new_loc = game.destination(pirate, _dir)
                #         if game.is_passable(new_loc) \
                #             and not (new_loc in [_isl.location for _isl in game.islands()]) \
                #                 and len([ep for ep in game.enemy_pirates() if
                #                          my_in_range(new_loc, ep.location, custom_radius=1)]) == 0:
                #                 if my_in_range(new_loc, my_dest):
                #                     if not pirateWillDie(game, pirate, pirates, dests):
                #                         paths_to_add[pirate_index] = _dir
                #                         supporting_pirates[pirate] = [new_loc]
                #                         break
                #                     else:
                #                         selective_debug(game, "Pirate {} can't get help by pirate {} "
                #                                               "- other pirate will die".format(my_pirate.id, pirate.id))

            selective_debug(game, "Pirate {} dests: {}".format(pirate.id, dest))
            selective_debug(game, "Pirate {} relevent dests: {}".format(pirate.id, relevent_dests))

    if len(supporting_pirates) >= len(enemies):  # Will be able to survive
        paths_changed = False

        # Add paths
        # for pirate_index, new_dir in paths_to_add.items():
        #     selective_debug(game, "Pirate {} added path '{}' for pirate {} so he'll help.".format(
        #         my_pirate.id,
        #         new_dir,
        #         pirates[pirate_index].id
        #     ))
        #
        #     paths[pirate_index][0] = new_dir  # Add new path
        #     paths[pirate_index][1] = '-'  # Cancel other paths
        #
        #     # Update destination:
        #     dests[pirate_index] = (
        #         game.destination(
        #             pirates[pirate_index],
        #             paths[pirate_index][0]
        #         ),
        #         game.destination(
        #             pirates[pirate_index],
        #             paths[pirate_index][1]
        #         )
        #     )
        #
        #     paths_changed = True

        # Force paths
        for pirate_index, path_to_cancel in paths_to_cancel.items():
            if paths[pirate_index][path_to_cancel] != '-' and not escapes[pirate_index]:
                pirate = pirates[pirate_index]

                selective_debug(game, "Pirate {} canceled pirate {} original path '{}' to force other path".format(
                    my_pirate.id,
                    pirates[pirate_index].id,
                    paths[pirate_index][path_to_cancel]
                ))
                paths[pirate_index][path_to_cancel] = '-'  # Cancel bad path
                # Update destination:
                dests[pirate_index] = (
                    game.destination(
                        pirates[pirate_index],
                        paths[pirate_index][0]
                    ),
                    game.destination(
                        pirates[pirate_index],
                        paths[pirate_index][1]
                    )
                )

                dest = dests[pirate_index]
                relevent_dests = [_dest
                                  for _dest_index, _dest in enumerate(dest)
                                  if (is_kamikaze or (_dest != pirate.location)
                                      or (dest[1 - _dest_index] == pirate.location))
                                  and _dest not in [isl.location for isl in game.not_my_islands()]]

                # Remove dests on islands if more than 1 turn left to capture them
                for relevent_dest in relevent_dests:
                    islands_on = [isl for isl in game.islands() if isl.location == relevent_dest]
                    if len(islands_on) > 0:
                        if relevent_dest != pirate.location or \
                                (islands_on[0].capture_turns - islands_on[0].turns_being_captured == 1):
                            relevent_dests.remove(relevent_dest)

                supporting_pirates[pirate] = relevent_dests
                paths_changed = True

        for pirate, relevent_dests in supporting_pirates.viewitems():
            pirate_index = pirates.index(pirate)
            good_path_index = None
            good_already = pirate_index not in paths_to_cancel
            if not good_already:  # -> in paths_to_cancel
                good_path_index = 1 - paths_to_cancel[pirate_index]

            # Move pirates on islands:
            if len(relevent_dests) > 0 and\
                    relevent_dests[0] == pirate.location and relevent_dests[-1] == pirate.location and\
                    (pirate.location in [isl.location for isl in game.islands()] or not my_in_range(pirate, my_dest)):

                escape_direction, moved_pirates = escapeEnemy(game, pirates, paths, dests, final_dests, kamikaze,
                                                              cancel_causes, escapes, is_rerouted, pirate,
                                                              force_escape=True)
                paths[pirate_index][0] = escape_direction

                if escape_direction == '-':
                    directions = [direction for direction in ['n', 'w', 's', 'e']
                                  if game.is_passable(game.destination(pirate, direction))
                                  and len([_dest for _dests in dests for _dest in _dests
                                          if _dest == game.destination(pirate, direction)]) == 0]
                    if len(directions) > 0:
                        paths[pirate_index][0] = max(directions,
                                                     key=lambda _dir:
                                                     game.distance(list(enemies)[0], game.destination(pirate, _dir)))
                else:
                    selective_debug(game, "Pirate {} forced escape successful".format(pirates[pirate_index].id))
                    chainEscape(game, pirates, paths, dests, is_rerouted, final_dests, kamikaze, cancel_causes,
                                escapes, moved_pirates, pirate, escape_direction)

                # Update destination:
                dests[pirate_index] = (
                    game.destination(
                        pirates[pirate_index],
                        paths[pirate_index][0]
                    ),
                    game.destination(
                        pirates[pirate_index],
                        paths[pirate_index][1]
                    )
                )
                if len(relevent_dests) > 0:
                    relevent_dests[0] = relevent_dests[-1] = dests[pirate_index][0]

                selective_debug(game, "Pirate {} forced pirate {} to go off same location to: '{}'.".format(
                    my_pirate.id,
                    pirates[pirate_index].id,
                    paths[pirate_index][0]
                ))
                paths_changed = True

            # Cancel colliding paths:
            # TODO: don't cancel escaping pirates colliding paths
            if good_already or good_path_index is not None:
                for other_pirate, other_dest in zip(pirates, dests):
                    other_pirate_index = pirates.index(other_pirate)
                    if other_pirate != pirate:
                        for _other_dest_index, _other_dest in enumerate(other_dest):
                            if (_other_dest != other_pirate.location) or (other_dest[1 - _other_dest_index] ==
                                                                          other_pirate.location):

                                pirate_relevent_dests = supporting_pirates[pirate]
                                for pirate_relevent_dest in list(pirate_relevent_dests):
                                    if len(pirate_relevent_dests) > 1:
                                        if pirate_relevent_dest == pirate.location:
                                            pirate_relevent_dests.remove(pirate_relevent_dest)

                                if _other_dest in pirate_relevent_dests:  # Colliding
                                    if good_already or dests[pirate_index].index(_other_dest) == good_path_index:
                                        if paths[pirate_index][dests[pirate_index].index(_other_dest)] != '-' and\
                                                (good_already or paths[other_pirate_index][_other_dest_index] == '-'):
                                            if not escapes[pirate_index]:
                                                selective_debug(game, "Pirate {} is getting help from pirate {} who"
                                                                      " got his colliding path '{}' "
                                                                      "with pirate {} canceled.".format(
                                                                my_pirate.id,
                                                                pirate.id,
                                                                paths[pirate_index][dests[pirate_index].index(_other_dest)],
                                                                other_pirate.id
                                                ))
                                                # Cancel pirate colliding path
                                                paths[pirate_index][dests[pirate_index].index(_other_dest)] = '-'
                                                # Update destination:
                                                dests[pirate_index] = (
                                                    game.destination(
                                                        pirates[pirate_index],
                                                        paths[pirate_index][0]
                                                    ),
                                                    game.destination(
                                                        pirates[pirate_index],
                                                        paths[pirate_index][1]
                                                    )
                                                )

                                                dest = dests[pirate_index]
                                                relevent_dests = [_dest
                                                                  for _dest_index, _dest in enumerate(dest)
                                                                  if (is_kamikaze or (_dest != pirate.location)
                                                                      or (dest[1 - _dest_index] == pirate.location))
                                                                  and _dest not in [isl.location for isl in game.not_my_islands()]]

                                                # Remove dests on islands if more than 1 turn left to capture them
                                                for relevent_dest in relevent_dests:
                                                    islands_on = [isl for isl in game.islands() if
                                                                  isl.location == relevent_dest]
                                                    if len(islands_on) > 0:
                                                        if relevent_dest != pirate.location or \
                                                                (islands_on[0].capture_turns - islands_on[0].turns_being_captured == 1):
                                                            relevent_dests.remove(relevent_dest)

                                                supporting_pirates[pirate] = [_dest
                                                                              for _dest_index, _dest
                                                                              in enumerate(dests[pirate_index])
                                                                              if ((_dest != pirate.location) or
                                                                                  (dests[pirate_index][
                                                                                   1 - _dest_index]
                                                                                   == pirate.location))]
                                                good_already = False
                                        elif not escapes[other_pirate_index]:
                                            selective_debug(game, "Pirate {} is getting help from pirate {} who"
                                                                  " canceled pirate {} colliding path '{}'".format(
                                                my_pirate.id,
                                                pirate.id,
                                                other_pirate.id,
                                                paths[other_pirate_index][_other_dest_index]
                                                ))
                                            # Cancel other pirate colliding path
                                            paths[other_pirate_index][_other_dest_index] = '-'
                                            # Update destination:
                                            dests[other_pirate_index] = (
                                                game.destination(
                                                    pirates[other_pirate_index],
                                                    paths[other_pirate_index][0]
                                                ),
                                                game.destination(
                                                    pirates[other_pirate_index],
                                                    paths[other_pirate_index][1]
                                                )
                                            )

                                            if other_pirate in supporting_pirates:
                                                supporting_pirates[other_pirate] = [_dest
                                                                                    for _dest_index, _dest
                                                                                    in enumerate(dests[other_pirate_index])
                                                                                    if ((_dest != other_pirate.location) or
                                                                                        (dests[other_pirate_index][
                                                                                         1 - _dest_index]
                                                                                         == other_pirate.location))]

                                        paths_changed = True

        selective_debug(game, "---------------------------")
        for pirate, path in zip(pirates, paths):
            selective_debug(game, "Pirate {} paths: {}".format(pirate.id, path))
        selective_debug(game, "---------------------------")

        selective_debug(game, "Pirate {} will survive on dest '{}' - enemies({}): {} || friends({}): {}".format(
            my_pirate.id,
            my_dest,
            len(enemies),
            [ep.id for ep in enemies],
            len(supporting_pirates),
            [p.id for p in supporting_pirates.keys()]
        ))
        return paths_changed, len(supporting_pirates)
    else:
        selective_debug(game, "Pirate {} will die on dest '{}' - enemies({}): {} || friends({}): {}".format(
            my_pirate.id,
            my_dest,
            len(enemies),
            [ep.id for ep in enemies],
            len(supporting_pirates),
            [p.id for p in supporting_pirates.keys()]
        ))

    return None, len(supporting_pirates)


def enemiesInRadius(game, loc, owner=True, pirates=None, destenations=None):
    """
    Find how many enemies in location radius


    function can work both on our pirates(find enemies)
    and on enemy pirates (find our pirates - in order to verified that enemy would die {Ex: kamikaze mode})

    :param game: the game
    :param loc: location to check the radius of.
    :param owner: bool. True if location of Our pirate - check enemies in radius
                        False if Enemy's location - check our
    :param pirates: pirates list
    :param destenations: pirates destinations list
    :return: list of enemy pirates in radius
    """
    global radius, enemiesInRadius_cache

    real_owner = owner or destenations is None or pirates is None

    # Check if available in cache:
    if (loc, real_owner) in enemiesInRadius_cache:
        return enemiesInRadius_cache[(loc, real_owner)]

    strong_enemies = set()
    # Find out who are the enemies
    if real_owner:
        if owner:  # If I'm the owner
            enemies = game.enemy_pirates()
        else:
            enemies = game.my_pirates()  # use current locations

        for ep in enemies:
            el = ep.location

            # Verify if enemy even worth checking:
            if game.distance(loc, el) > radius + 3:
                continue

            found = False
            # TODO: identify if enemies on island escape death or not and skip them if they do not escape death.
            # islands = [isl for isl in game.islands() if isl.location == el]
            # # Island being captured
            # if len(islands) > 0:
            #     island = islands[0]
            #     # already captured atleast some of an island
            #     if island.turns_being_captured > island.capture_turns / 4:
            #         continue  # skip this enemy (enemies on islands don't count)

            enemy_on_loc = game.get_pirate_on(loc) in game.enemy_pirates()

            for r_loc in xrange(-1, 2):  # Row
                for c_loc in xrange(-1, 2):  # Col
                    if ((c_loc == 0 or r_loc == 0) and enemy_on_loc) or (c_loc == 0 and r_loc == 0):
                        for r in xrange(-1, 2):  # Row
                            for c in xrange(-1, 2):  # Col
                                if c == 0 or r == 0:
                                    # If he might be able to attack me:
                                    if my_in_range((el[0] + r, el[1] + c), (loc[0] + r_loc, loc[1] + c_loc)) \
                                            and ep not in strong_enemies:
                                        # selective_debug(game, "Pirate on loc {} has enemy: {} with dest {}".format(
                                        #     loc, ep.id, (el[0] + r, el[1] + c)))
                                        strong_enemies.add(ep)
                                        found = True
                                        break
                if found:
                    break
            if found:
                continue

    else:  # Go through future movements lists
        islands = [isl.location for isl in game.islands()]
        for index in xrange(len(destenations)):
            dest_tuple = destenations[index]
            ep = pirates[index]  # Current pirate
            for el_index, el in enumerate(dest_tuple):
                # Consider only path on which pirate moves, if he has one
                if (el != ep.location) or (dest_tuple[1 - el_index] == ep.location):
                    # If he might be able to attack me:
                    if ep.location not in islands and ep not in strong_enemies and my_in_range(el, loc):
                        # selective_debug(game, "Enemy on loc {} has enemy: {} with dest {}".format(
                        #     loc, ep.id, el))
                        strong_enemies.add(ep)
                        break

    if real_owner:
        enemiesInRadius_cache[(loc, real_owner)] = strong_enemies

    return list(strong_enemies)


def pirateWillDie(game, checked_pirate, my_pirates, my_dests, my_paths=None, my_escapes=None, my_is_rerouted=None,
                  my_final_dests=None, my_kamikaze=None, my_cancel_causes=None, my_dest=None, is_kamikaze=None,
                  checked_pirate_location=None, kamikaze_target=False):
    """
    Check if pirate will die

    :param game: the game
    :param checked_pirate:
    :param my_pirates:
    :param my_dests:
    :param checked_pirate_location:
    :rtype : bool
    :return: True if pirate will die (i.e. have more enemies than friends). False otherwise
    """

    if checked_pirate_location is None:
        checked_pirate_location = checked_pirate.location

    notOwnedPirate = (checked_pirate.owner != game.ME)

    his_enemies = set(enemiesInRadius(game, checked_pirate_location,
                                      owner=(not notOwnedPirate),
                                      pirates=my_pirates,
                                      destenations=my_dests))

    if notOwnedPirate:
        his_friends = set(enemiesInRadius(game, checked_pirate_location,
                                          owner=notOwnedPirate,
                                          pirates=my_pirates,
                                          destenations=my_dests))
        his_friends.discard(checked_pirate)

        if kamikaze_target and len(his_enemies) == 0:
            his_enemies.add(None)

        # if notOwnedPirate:
        #     selective_debug(game, "Enemies of enemy {}: {} vs {}".format(checked_pirate.id,
        #                                                                  [ep.id if ep is not None else 'None'
        #                                                                   for ep in his_enemies],
        #                                                                  [p.id for p in his_friends]))
        # else:
        #     selective_debug(game, "Pirate {} enemies: {} || friends: {}".format(
        #         checked_pirate.id, [ep.id for ep in his_enemies], [p.id for p in his_friends]))

        return len(his_enemies) > len(his_friends)

    else:
        got_help, force_size = helpPirate(game, his_enemies, my_pirates, my_paths, my_dests, my_escapes, my_is_rerouted,
                                          my_final_dests, my_kamikaze, my_cancel_causes, checked_pirate, my_dest,
                                          is_kamikaze)
        return got_help is None


def escapeEnemy(game, pirates, paths, dests, final_dests, kamikaze, cancel_causes, escapes, is_rerouted, my_pirate,
                force_escape=False):
    ownedPirate = (my_pirate.owner == game.ME)

    if ownedPirate:
        cancelReroute(game, pirates, paths, dests, final_dests, kamikaze, cancel_causes, my_pirate)

    # Sum enemies
    strong_enemies = enemiesInRadius(game, my_pirate.location,
                                     owner=ownedPirate,
                                     pirates=pirates,
                                     destenations=dests)

    pirates_to_move = frozenset()
    # Escape from enemies
    if len(strong_enemies) > 0:
        if ownedPirate and not force_escape:
            pirate_index = pirates.index(my_pirate)
            got_help, force_size = helpPirate(game, strong_enemies, pirates, paths, dests, escapes, is_rerouted,
                                              final_dests, kamikaze, cancel_causes, my_pirate, my_pirate.location,
                                              kamikaze[pirate_index])

            if got_help is None:
                selective_debug(game, "Pirate {} will die if he doesn't move. || E: {}".format(my_pirate.id,
                                                                                      [ep.id for ep in strong_enemies]))
                pass  # Not ok - my_pirate will die
            else:  # no breaks
                selective_debug(game, "Pirate {} will not move - won't die.".format(my_pirate.id))
                return '-', pirates_to_move  # It is OK to do nothing, pirate won't die

        possible_directions = {'n', 'e', 's', 'w'}
        backup_directions = set()
        occupied_directions = set()

        # Plan escape route
        # for se in strong_enemies:
        #     for direction in game.get_directions(my_pirate, se.location):
        #         if direction in possible_directions:
        #             if ownedPirate:
        #                 selective_debug(game, "Pirate {} escape path '{}' removed - enemy".format(
        #                     my_pirate.id, direction))
        #             backup_directions.add(direction)
        #             possible_directions.discard(direction)

        # Remove un-travelable directions
        for direction in possible_directions.copy():
            _dest = game.destination(my_pirate, direction)
            is_occupied = False  # Destination occupied

            # Test if some other pirate will occupy destination
            if ownedPirate:
                pirates_occuping = set()
                for other_pirate_index, other_pirate in enumerate(pirates):
                    if other_pirate.id != my_pirate.id:
                        other_dest = dests[other_pirate_index]
                        current_location = other_pirate.location
                        is_now_occupied = False
                        problematic_path = None

                        if other_dest[0] != current_location and other_dest[1] == current_location:
                            is_now_occupied = (other_dest[0] == _dest)
                            problematic_path = 0
                        elif other_dest[1] != current_location and other_dest[0] == current_location:
                            is_now_occupied = (other_dest[1] == _dest)
                            problematic_path = 1
                        elif other_dest[0] != current_location and other_dest[1] != current_location:
                            is_now_occupied = (other_dest[0] == _dest) or (other_dest[1] == _dest)
                            if other_dest[0] == _dest:
                                problematic_path = 0
                            else:
                                problematic_path = 1
                        elif other_dest[0] == current_location and other_dest[1] == current_location:
                            is_now_occupied = (other_dest[0] == _dest) or (other_dest[1] == _dest)
                            problematic_path = 0

                        if is_now_occupied:
                            if game.is_passable(game.destination(other_pirate, direction)):
                                pirates_occuping.add((other_pirate, problematic_path))
                            is_occupied = True
                            selective_debug(game, "Pirate {} escape path '{}' removed -"
                                                  " occupied by {} (dests: {} ; _dest: {})".format(my_pirate.id,
                                                                                                   direction,
                                                                                                   other_pirate.id,
                                                                                                   other_dest, _dest))
                if is_occupied and len(pirates_occuping) > 0:
                    occupied_directions.add((direction, frozenset(pirates_occuping)))
            else:
                for other_pirate in game.enemy_pirates():
                    if other_pirate.id != my_pirate.id:
                        is_occupied |= (other_pirate.location == _dest)

            if (not game.is_passable(_dest)) or is_occupied \
                    or (force_escape and _dest in [isl.location for isl in game.islands()])\
                    or len([ep for ep in game.enemy_pirates() if my_in_range(_dest, ep, custom_attack_radius=1)]) > 0:
                if ownedPirate:
                    selective_debug(game, "Pirate {} escape path '{}' removed - occupied or not passable".format(
                        my_pirate.id, direction))
                possible_directions.discard(direction)

        possible_directions_list = list(possible_directions)
        for p_dir in possible_directions_list:
            if game.destination(my_pirate, p_dir) in [isl.location for isl in game.islands()]:
                if len(possible_directions) > 1:
                    possible_directions_list.remove(p_dir)
        possible_directions = set(possible_directions_list)

        # Remove directions on which my_pirate will die or will be on island with less friends
        for p_dir in possible_directions.copy():
            _dest = game.destination(my_pirate, p_dir)
            is_kamikaze = kamikaze[pirates.index(my_pirate)] if my_pirate in pirates else None
            if pirateWillDie(game, my_pirate, pirates, dests, paths, escapes, is_rerouted, final_dests, kamikaze,
                             cancel_causes, _dest, is_kamikaze, checked_pirate_location=_dest):
                if ownedPirate:
                    selective_debug(game, "Pirate {} escape path '{}' removed - willDie".format(
                        my_pirate.id, p_dir
                    ))
                backup_directions.add(p_dir)
                possible_directions.discard(p_dir)

        moved_pirates = False
        if len(possible_directions) == 0:
            if len(occupied_directions) > 0 and ownedPirate:
                selective_debug(game, "Pirate {} has no actual way to escape, moving other pirates.".format(
                    my_pirate.id))
                moved_pirates = True
                possible_directions.update([interrupt[0] for interrupt in occupied_directions])
            else:
                if ownedPirate:
                    selective_debug(game, "Pirate {} has no actual way to escape, using backup routes.".format(
                        my_pirate.id))
                possible_directions = backup_directions

        escape_direction = escapeTests(game, pirates, dests, my_pirate, possible_directions, ownedPirate)
        if escape_direction != '-':
            if moved_pirates:  # If had to move pirates, add pirates to move list
                for interrupt in occupied_directions:
                    direction, i_pirates = interrupt

                    if direction == escape_direction:
                        pirates_to_move = i_pirates.copy()
                        break
            return escape_direction, pirates_to_move

    return '-', pirates_to_move  # No enemies - no need to escape


def escapeTests(game, pirates, dests, my_pirate, possible_directions, ownedPirate):
    if len(possible_directions) > 0:  # Found a way to escape
        escape_directions = []

        # if ownedPirate:
        #     selective_debug(game, "Pirate {} ZERO escape dirs: {}".format(my_pirate.id, possible_directions))

        # Construct a list of best escaping paths (filter by ranges my_pirate will be in)
        dir_ranges_count = [0] * len(possible_directions)
        for e_dir in possible_directions:
            for enemy in game.enemy_pirates():
                dir_ranges_count[list(possible_directions).index(e_dir)] += \
                    int(my_in_range(enemy, game.destination(my_pirate, e_dir)))

        escape_directions = list_min(possible_directions,
                                     func=lambda p_dir: dir_ranges_count[list(possible_directions).index(p_dir)])

        # if ownedPirate:
        #     selective_debug(game, "Pirate {} ONE escape dirs: {}".format(my_pirate.id, escape_directions))

        if len(escape_directions) > 1:
            # If multiple paths still available, filter by enemy count
            escape_directions = list_min(escape_directions,
                                         func=lambda p_dir: len(
                                             enemiesInRadius(game,
                                                             loc=game.destination(my_pirate, p_dir),
                                                             owner=ownedPirate,
                                                             pirates=pirates,
                                                             destenations=dests)
                                         )
                                         )

            # if ownedPirate:
            #     selective_debug(game, "Pirate {} TWO escape dirs: {}".format(my_pirate.id, escape_directions))

            if len(escape_directions) > 1 and ownedPirate:
                # If multiple paths still available, filter by dead enemy count
                # Test for a favourable direction, on which an enemy dies, if one exists
                dir_enemy_count = [0] * len(escape_directions)  # Count of dead enemies in each direction
                for e_dir_index, e_dir in enumerate(escape_directions):
                    updated_dests = list(dests)
                    updated_dests[pirates.index(my_pirate)] = (game.destination(my_pirate, e_dir),
                                                               game.destination(my_pirate, e_dir))
                    for enemy in game.enemy_pirates():
                        dir_enemy_count[e_dir_index] += \
                            int(pirateWillDie(game, enemy, pirates, updated_dests))

                escape_directions = list_max(escape_directions,
                                             func=lambda p_dir: dir_enemy_count[escape_directions.index(p_dir)])

                # selective_debug(game, "Pirate {} THREE escape dirs: {}".format(my_pirate.id, escape_directions))

                if len(escape_directions) > 1 and ownedPirate:
                    # If multiple paths still available, filter by friends count
                    escape_directions = list_max(escape_directions,
                                                 func=lambda p_dir: len(
                                                     enemiesInRadius(game,
                                                                     loc=game.destination(my_pirate, p_dir),
                                                                     owner=(not ownedPirate),
                                                                     pirates=pirates,
                                                                     destenations=dests)
                                                 )
                                                 )

                    # selective_debug(game, "Pirate {} FOUR escape dirs: {}".format(my_pirate.id, escape_directions))

        # Choose a random escape path from directions list
        return escape_directions[0]  # TODO: random.choice(escape_directions)  # Found a way to escape
    return '-'


def list_max(my_list, func=lambda x: x):
    my_list_copy = list(my_list)
    max_count = None
    temp_list = []
    for item in my_list_copy:
        value = func(item)
        if max_count is None or value > max_count:
            temp_list = [item]
            max_count = value
        elif value == max_count:
            temp_list.append(item)
    return temp_list


def list_min(my_list, func=lambda x: x):
    my_list_copy = list(my_list)
    min_count = None
    temp_list = []
    for item in my_list_copy:
        value = func(item)
        if min_count is None or value < min_count:
            temp_list = [item]
            min_count = value
        elif value == min_count:
            temp_list.append(item)
    return temp_list


def reroutePirates(game, pirates, paths, dests, kamikaze, final_dests, cancel_causes, start_paths, my_pirate):
    global radius, causes, re_routes

    my_index = pirates.index(my_pirate)
    my_cancel_causes = cancel_causes[my_index]
    is_kamikaze = kamikaze[my_index]

    # Cancel re-route if already re-routed
    cancelReroute(game, pirates, paths, dests, final_dests, kamikaze, cancel_causes, my_pirate)

    my_final_dest = final_dests[my_index]
    my_final_dest = nearestPassableLoc(game, my_final_dest)

    # if my_final_dest == my_pirate.location:
    #     return None  # pirate didn't want to go anywhere

    pirates_to_move = [my_pirate]
    old_dests = [my_final_dest]

    for cause in my_cancel_causes:
        # Handle first case when being stuck because of non-passable location
        if cause == causes.NOT_PASSABLE:
            start_path = start_paths[my_index]
            new_target = obstaclePass(game, my_pirate.location, my_final_dest,
                                        is_kamikaze=is_kamikaze, dests=dests, pirates=pirates)

            # TODO: Check that newely found target is not an already canceled dest.
            start_dest = [game.destination(my_pirate, path) for path in start_path]
            selective_debug(game, "Pirate {} starting dests: {}".format(my_pirate.id, start_dest))
            if new_target is not None and new_target != my_final_dest and new_target not in start_dest:
                return tuple(pirates_to_move), tuple(old_dests), new_target
            selective_debug(game, "Pirate {} could not find path to go around obstacle".format(my_pirate.id))
            continue  # Did not find path

        # Handle case when being stuck because of enemy
        elif cause == causes.ENEMY:
            is_kamikaze = kamikaze[my_index]
            for other_pirate, other_final_dest in \
                    zip(pirates, final_dests):
                if other_pirate.id != my_pirate.id:
                    # If both pirates go to a near dest
                    if my_in_range(final_dests[my_index], other_final_dest):
                        if other_pirate not in pirates_to_move:
                            pirates_to_move.append(other_pirate)
                            old_dests.append(other_final_dest)
                    else:
                        selective_debug(game, "Pirate {} Re-routing: Pirate {} target ({}) "
                                              "not in range of target ({}).".format(my_pirate.id, other_pirate.id,
                                                                                    other_final_dest,
                                                                                    final_dests[my_index]))

            selective_debug(game, "Other pirates of pirate {} for target {} are: {}".format(
                my_pirate.id, final_dests[my_index], pirates_to_move))

            # Multiple pirates afraid to attack with shared destination
            if len([m_pirate for m_pirate in pirates_to_move if
                    not my_in_range(m_pirate, my_pirate) and m_pirate != my_pirate]) > 0:

                best_locations = findRegroup(game, old_dests, pirates_to_move)

                if best_locations is not None:
                    # Choose best target (best_locations ordered from best to worst)
                    new_target = nearestPassableLoc(game, best_locations[0], dests, pirates, is_kamikaze=is_kamikaze)
                    return tuple(pirates_to_move), tuple(old_dests), new_target

    selective_debug(game, "Pirate {} re-routing failed.".format(my_pirate.id))
    return None  # Didn't found a re-route


def findRegroup(game, target_locations, pirates_to_move):
    global radius

    pirate_blobs = []
    # Split pirates to blobs (group of nearby pirates):
    for pirate in pirates_to_move:
        location = pirate.location
        for blob_index, blob in enumerate(pirate_blobs):
            for pirate_in_blob in blob:
                if my_in_range(pirate_in_blob, location, custom_attack_radius=((radius-1) ** 2 + 1)):
                    pirate_blobs[blob_index].append(location)
                    break
            else:
                continue
            break
        else:
            pirate_blobs.append([location])
    selective_debug(game, "Pirate Blobs found: {}".format(pirate_blobs))

    blobs = []
    for pirate_blob in pirate_blobs:
        blob_r = sum([pirate_in_blob[0] for pirate_in_blob in pirate_blob]) / len(pirate_blob)
        blob_c = sum([pirate_in_blob[1] for pirate_in_blob in pirate_blob]) / len(pirate_blob)
        blobs.append((blob_r, blob_c))
    selective_debug(game, "Blobs found: {}".format(blobs))

    if len(blobs) < 2:
        return None  # Not enough groups to regroup

    # Find bounding box of blobs
    blob_max_r = max(blobs, key=lambda _blob: _blob[0])[0]
    blob_min_r = min(blobs, key=lambda _blob: _blob[0])[0]
    blob_max_c = max(blobs, key=lambda _blob: _blob[1])[1]
    blob_min_c = min(blobs, key=lambda _blob: _blob[1])[1]

    # Calculate target_center (center of targets)
    target_center_r = sum([old_dest[0] for old_dest in target_locations]) / len(target_locations)
    target_center_c = sum([old_dest[1] for old_dest in target_locations]) / len(target_locations)

    # Build circle around target_center
    x0 = target_center_c
    y0 = target_center_r
    closest_enemy = min(game.enemy_pirates(), key=lambda enemy: game.distance(enemy, (y0, x0))).location
    circle_radius = int(math.sqrt((y0 - closest_enemy[0]) ** 2 + (x0 - closest_enemy[1]) ** 2)) + radius + 2

    circle = set()
    f = 1 - circle_radius
    ddf_x = 1
    ddf_y = -2 * circle_radius
    x = 0
    y = circle_radius
    circle.add((y0 + circle_radius, x0))
    circle.add((y0 - circle_radius, x0))
    circle.add((y0, x0 + circle_radius))
    circle.add((y0, x0 - circle_radius))

    while x < y:
        if f >= 0:
            y -= 1
            ddf_y += 2
            f += ddf_y
        x += 1
        ddf_x += 2
        f += ddf_x
        circle.add((y0 + y, x0 + x))
        circle.add((y0 + y, x0 - x))
        circle.add((y0 - y, x0 + x))
        circle.add((y0 - y, x0 - x))
        circle.add((y0 + x, x0 + y))
        circle.add((y0 + x, x0 - y))
        circle.add((y0 - x, x0 + y))
        circle.add((y0 - x, x0 - y))
    best_locations = list(circle)

    # From locations left, sort by distance to closest enemy
    best_locations = sorted(best_locations, key=lambda loc:
        game.distance(min(game.enemy_pirates(), key=lambda enemy: game.distance(enemy, loc)), loc))

    # selective_debug(game, "Stage 0 best locs: {}".format(best_locations[::-1]))

    # Remove locations inside bounding box rows/columns
    # for location in list(best_locations):
    #     if len(best_locations) > 1:
    #         if blob_min_r <= location[0] <= blob_max_r or blob_min_c <= location[1] <= blob_max_c:
    #             best_locations.remove(location)

    selective_debug(game, "Stage 1 best locs: {}".format(best_locations[::-1]))

    # Get best location on circle (closest to all blobs)
    distances = {}
    for location in best_locations:
        distances[location] = sum([game.distance(blob, location) for blob in blobs])
    min_dist_sum = min(distances.itervalues())
    best_locations = [k for k, v in distances.iteritems() if v == min_dist_sum]
    distances.clear()

    selective_debug(game, "Stage 2 best locs: {}".format(best_locations[::-1]))

    # From location left, choose only locations furthest from all blobs
    for location in best_locations:
        closest_blob = min(blobs, key=lambda _blob: game.distance(_blob, location))
        distances[location] = game.distance(location, closest_blob)
    max_dist_sum = max(distances.itervalues())
    best_locations = [k for k, v in distances.iteritems() if v == max_dist_sum]

    # From locations left, sort by distance to closest enemy
    best_locations = sorted(best_locations, key=lambda loc:
        game.distance(min(game.enemy_pirates(), key=lambda enemy: game.distance(enemy, loc)), loc), reverse=True)

    selective_debug(game, "Stage 3 best locs: {}".format(best_locations))

    return best_locations


def cancelReroute(game, pirates, paths, dests, final_dests, kamikaze, cancel_causes, my_pirate):
    global re_routes

    def cancelPirate(pirate, current_reroute):
        pirate_index = pirates.index(pirate)
        reroute_index = current_reroute[0].index(pirate)
        if tuple(paths[pirate_index]) == current_reroute[3][reroute_index]:
            is_kamikaze = kamikaze[pirate_index]
            pirate_old_dest = current_reroute[1][reroute_index]
            final_dests[pirate_index] = pirate_old_dest
            path, cancel_cause, reset = createPaths(game, pirate, pirate_old_dest, is_kamikaze)
            paths[pirate_index] = path
            dests[pirate_index] = (game.destination(pirate, path[0]), game.destination(pirate, path[1]))
            cancel_causes[pirate_index] = cancel_cause
            selective_debug(game, "Reroute to {} cancelled, returning pirate {} to old dest {}".format(
                current_reroute[2], pirate.id, pirate_old_dest))

            # Remove from re-route
            current_reroute[0] = tuple([item for index, item in enumerate(current_reroute[0]) if index != reroute_index])
            current_reroute[1] = tuple([item for index, item in enumerate(current_reroute[1]) if index != reroute_index])
            current_reroute[3] = tuple([item for index, item in enumerate(current_reroute[3]) if index != reroute_index])
            return True
        return False

    for reroute in list(re_routes):
        if my_pirate in reroute[0]:
            if cancelPirate(my_pirate, reroute):
                if len(reroute[0]) == 1:  # Only one pirate left in re-route:
                    cancelPirate(reroute[0][0], reroute)
                    re_routes.remove(reroute)
            else:  # Paths changed so not deleted
                if len(reroute[0]) == 2:  # Only one pirate left in re-route:
                    cancelPirate(reroute[0][0], reroute)
                    cancelPirate(reroute[0][-1], reroute)
                    re_routes.remove(reroute)
            break  # Found pirate, no need to continue searching

            # # Cancel last re-route and recreate paths for all involved pirates to their old dest
            # for pirate_index, pirate in enumerate(reroute[0]):
            #     index = pirates.index(pirate)
            #     if tuple(paths[index]) == reroute[3][pirate_index]:
            #         is_kamikaze = kamikaze[index]
            #         pirate_old_dest = reroute[1][pirate_index]
            #         final_dests[index] = pirate_old_dest
            #         path, cancel_cause, reset = createPaths(game, pirate, pirate_old_dest, is_kamikaze)
            #         paths[index] = path
            #         dests[index] = (game.destination(pirate, path[0]), game.destination(pirate, path[1]))
            #         cancel_causes[index] = cancel_cause
            #         selective_debug(game, "Reroute to {} cancelled, returning pirate {} to old dest {}".format(
            #             reroute[2], pirate.id, pirate_old_dest))
            # re_routes.discard(reroute)


def obstaclePass(game, my_pirate_loc, dest, is_kamikaze=False, dests=None, pirates=None):
    """
    :rtype : location of the next step that should be taken towards dest. None if no path found
    """

    # Relevent dests are only paths pirates will really take.
    relevent_dests = []
    if dests is not None and pirates is not None:
        for pirate, pirate_dest in zip(pirates, dests):
            for _dest_index, _dest in enumerate(pirate_dest):
                if (_dest != pirate.location) or (pirate_dest[1 - _dest_index] == pirate.location):
                    relevent_dests.append(_dest)

    # If destenation is actually reachable, pass obstacle using Best First Search
    if game.is_passable(dest) and dest not in relevent_dests:
        selective_debug(game, "Pirate on location {} using Best First Search to pass"
                              " obstacle in way to target: {}".format(my_pirate_loc, dest))

        # Go in reverse
        goal = my_pirate_loc
        start = dest
        testLoc = lambda loc: loc == goal \
            or (game.is_passable(loc)
                and loc not in relevent_dests
                and (not is_kamikaze or len([_isl for _isl in game.islands() if _isl.location == loc]) == 0)
                and len([ep for ep in game.enemy_pirates() if my_in_range(loc, ep.location, custom_attack_radius=1)])
                == 0)

        # Make sure that goal is reachable
        for location in [(goal[0] + r, goal[1] + c) for r in xrange(-1, 2) for c in xrange(-1, 2)
                         if ((c == 0) != (r == 0))]:
            if testLoc(location):
                break
        else:  # no break
            return None

        # Greedy Best-First Search Algorithm:
        # ----------------------------------
        # heuristic(loc) = Manhattan distance on a square grid from loc to goal

        frontier = PriorityQueue()
        frontier.put(start, 0)
        came_from = {start: None}

        heuristic = lambda loc: abs(loc[0] - goal[0]) + abs(loc[1] - goal[1])  # Manhattan distance on a square grid

        while not frontier.empty():
            current = frontier.get()

            if current == goal:
                selective_debug(game, "Pirate on location {} best-first search reached goal!"
                                      " (Found new target: {})".format(my_pirate_loc, came_from[current]))
                new_target = came_from[current]
                # path = []
                # while current != start:
                #     current = came_from[current]
                #     path.append(current)
                # selective_debug(game, "Pirate {} path to target: {})".format(my_pirate.id, path))
                return new_target

            for next_loc in [(current[0] + r, current[1] + c) for r in xrange(-1, 2) for c in xrange(-1, 2)
                             if ((c == 0) != (r == 0))]:
                if testLoc(next_loc):
                    if next_loc not in came_from:
                        frontier.put(next_loc, heuristic(next_loc))
                        came_from[next_loc] = current
    return None


class PriorityQueue:
    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]


def nearestPassableLoc(game, loc, dests=None, pirates=None, is_kamikaze=False, no_pirates=False):
    # Midpoint circle algorithm
    relevent_dests = []
    if dests is not None and pirates is not None:
        for pirate, pirate_dest in zip(pirates, dests):
            # Relevent dests are only paths pirates will really take.
            relevent_dests += [_dest
                               for _dest_index, _dest in enumerate(pirate_dest)
                               if (_dest != pirate.location) or (pirate_dest[1 - _dest_index] == pirate.location)
                               ]

            # Remove dests on islands if more than 1 turn left to capture them
            for relevent_dest in relevent_dests:
                islands_on = [isl for isl in game.islands() if isl.location == relevent_dest]
                if len(islands_on) > 0:
                    if relevent_dest != pirate.location or \
                            (islands_on[0].capture_turns - islands_on[0].turns_being_captured == 1):
                        relevent_dests.remove(relevent_dest)
    elif not no_pirates:
        relevent_dests += [pirate.location for pirate in game.my_pirates()]

    testLoc = lambda c, r: game.is_passable((r, c)) and (r, c) not in relevent_dests and \
        (is_kamikaze or
            len([ep for ep in game.enemy_pirates() if my_in_range((r, c), ep.location, custom_attack_radius=1)]) == 0)

    if testLoc(loc[1], loc[0]):
        return loc

    x0 = loc[1]
    y0 = loc[0]
    test_radius = 1
    good_locs = []
    while test_radius < max(game.get_rows(), game.get_cols()):
        f = 1 - test_radius
        ddf_x = 1
        ddf_y = -2 * test_radius
        x = 0
        y = test_radius
        if testLoc(x0, y0 + test_radius):
            good_locs.append((y0 + test_radius, x0))
        if testLoc(x0, y0 - test_radius):
            good_locs.append((y0 - test_radius, x0))
        if testLoc(x0 + test_radius, y0):
            good_locs.append((y0, x0 + test_radius))
        if testLoc(x0 - test_radius, y0):
            good_locs.append((y0, x0 - test_radius))

        if len(good_locs) > 0:
            return min(good_locs, key=lambda val: game.distance(loc, val))

        while x < y:
            if f >= 0:
                y -= 1
                ddf_y += 2
                f += ddf_y
            x += 1
            ddf_x += 2
            f += ddf_x

            xy = [x, y]
            for var in xrange(2):
                for xsign in xrange(-1, 2):
                    for ysign in xrange(-1, 2):
                        if ysign != 0 and xsign != 0:
                            if testLoc(x0 + xsign * xy[var], y0 + ysign * xy[1 - var]):
                                good_locs.append((y0 + ysign * xy[1 - var], x0 + xsign * xy[var]))

            if len(good_locs) > 0:
                return min(good_locs, key=lambda val: game.distance(loc, val))
        test_radius += 1
    return loc  # Did not find passable location


def my_in_range(loc1, loc2, custom_attack_radius=None):
    global attackRadius

    # Check if two objects or locations are in attack range - faster than my_in_range()
    if type(loc1) is not tuple:
        if hasattr(loc1, 'location'):
            loc1 = loc1.location
        else:
            raise Exception('No \'location\' attribute for {}'.format(loc1))
            # return False
    if type(loc2) is not tuple:
        if hasattr(loc2, 'location'):
            loc2 = loc2.location
        else:
            raise Exception('No \'location\' attribute for {}'.format(loc2))
            # return False

    d_row, d_col = loc1[0] - loc2[0], loc1[1] - loc2[1]
    distance = d_row * d_row + d_col * d_col
    if 0 <= distance <= (custom_attack_radius if custom_attack_radius is not None else attackRadius):
        return True
    return False


class Tank():
    def __init__(self, _game, _pirates, _identifier=None, _starting_location=None, _is_kamikaze=False):
        self._game = _game
        self._pirates = _pirates
        self._identifier = _identifier
        self._starting_location = _starting_location
        self._is_kamikaze = _is_kamikaze

    def __enter__(self):
        class TankInstance():
            """
            Creates a Tank and manage it.

            :var baseLoc: the base location of the Tank
            :var pirates: list of pirates (objects) (updated each turn to
            :var game: the game
            :var tankFormations: locations to form tank
            """
            baseLoc = (0, 0)
            pirates = []
            game = None
            tankFormations = []
            last_path = 'n'
            is_kamikaze = False

            def __init__(self, game, pirates, identifier=None, startingLocation=None, is_kamikaze=False):
                """
                Creates Tank instance
                :param game: the game
                :param pirates: list of the pirates of the tank
                :param identifier: tankInstance identifier
                :param startingLocation: tuple - base location of the Tank (Location - LocationObject)
                       after first time - list. used to resume data: contains  Tank's base location
                """
                global tankData

                self.game = game
                self.pirates = pirates
                self.is_kamikaze = is_kamikaze

                if identifier is None:
                    identifier = tuple(pirates)
                self.identifier = identifier
                tank_data = tankData.get(identifier, None)

                if tank_data is not None:
                    self.resumeFromData(tank_data)
                else:
                    self.calculateFormation()
                    if startingLocation is None:
                        self.baseLoc = nearestPassableLoc(self.game, self.getBaseLoc(), is_kamikaze=is_kamikaze)
                    else:
                        self.baseLoc = nearestPassableLoc(self.game, startingLocation, is_kamikaze=is_kamikaze)

            def getBaseLoc(self):
                """
                used when no startingLocation is passed to __init__ (default value is None)
                :rtype:  LocationObject
                :return: location for tank base - average of pirates location
                """

                # Centre of islands, more weight to valued islands:
                # islands = []
                # center = []
                #
                # for island in self.game.islands():
                # for v in xrange(island.value):
                # islands.append(island)
                #
                # center.append(sum([island.location[0] for island in islands]) / len(islands))
                # center.append(sum([island.location[1] for island in islands]) / len(islands))
                #
                # return tuple(center)

                # Centre of pirates
                return tuple((sum([pirate.location[0] for pirate in self.pirates]) / len(self.pirates),
                              sum([pirate.location[1] for pirate in self.pirates]) / len(self.pirates)))

            def moveTank(self, dest):
                """
                Move the Tank, only if Tank already in form, if not - form tank

                uses 'movePirate' to move Tank
                :param dest: destination to move the Tank to.
                """

                dest = nearestPassableLoc(self.game, dest, is_kamikaze=self.is_kamikaze)
                paths, cancel_causes, reset = createPaths(self.game, self.baseLoc, dest, alternating=False)

                path = paths[0] if paths[0] != '-' else paths[1]

                if path != '-':
                    self.last_path = path

                selective_debug(self.game, "Tank going to target {} with path '{}'".format(dest, path))

                if self.formTank(path):
                    selective_debug(self.game, "We've got a tank! prepare to die..")
                    for pirate in self.pirates:
                        dest = self.game.destination(pirate, path)
                        movePirate(pirate, dest, kamikaze=self.is_kamikaze, in_tank=True)

                    # Apply new base
                    self.baseLoc = self.game.destination(self.baseLoc, path)

                    if path is None or path == '-':
                        selective_debug(self.game, "Stopped tank from moving.")

            def changeReference(self, locations):
                global radius
                max_rows = self.game.get_rows()
                max_cols = self.game.get_cols()

                # Fix out-of map tank
                if max_cols - self.baseLoc[1] < radius:
                    self.baseLoc = (self.baseLoc[0], max_cols - radius - 1)
                elif self.baseLoc[1] < radius:
                    self.baseLoc = (self.baseLoc[0], radius)

                if max_rows - self.baseLoc[0] < radius:
                    self.baseLoc = (max_rows - radius - 1, self.baseLoc[1])
                elif self.baseLoc[0] < radius:
                    self.baseLoc = (radius, self.baseLoc[1])

                # Adjust location list to be around a new base location
                newList = []
                for loc in locations:
                    new_loc = (loc[0] + self.baseLoc[0], loc[1] + self.baseLoc[1])
                    # TODO: handle un-passable locations in the tank (use nearestPassableLoc test to test if passable)
                    newList.append(new_loc)

                return newList

            def formTank(self, path='-'):
                if len(self.pirates) == 0:
                    return False
                elif len(self.pirates) == 1 and self.pirates[0].location == self.baseLoc:
                    return True

                self.pirates = [pirate for pirate in self.pirates if not pirate.is_lost]
                selective_debug(self.game, "Tank pirates are: {}".format([p.id for p in self.pirates]))

                if path == '-':
                    path = self.last_path
                paths = ['n', 'w', 's', 'e']
                targetLocations = [pos for pirate, pos in zip(self.pirates, self.tankFormations[paths.index(path)])]
                selective_debug(self.game, "Tank front is faced to the '{}'".format(path))

                # Calculate position for each pirate
                targetLocations = self.changeReference(targetLocations)

                # Check available target locations
                tempPirates = list(self.pirates)
                tempLocs = list(targetLocations)

                for pirate_index, pirate in enumerate(self.pirates):
                    if pirate.location in targetLocations:
                        tempPirates.remove(pirate)
                        tempLocs.remove(pirate.location)
                        targetLocations[pirate_index] = pirate.location

                # Update target locations for pirates that are not in a target location.
                assignments = cross_assign(self.game, tempPirates, tempLocs)[:len(targetLocations)]
                for assignment in assignments:
                    targetLocations[self.pirates.index(assignment[1])] = assignment[0]

                # Debug print-out
                for pirate, pos in zip(self.pirates, targetLocations):
                    selective_debug(self.game, "Pirate: {} Location: {} Target: {}".format(
                        pirate.id, pirate.location, pos))

                # Check if pirates are blocking each other and change their targets if so:
                reset = True
                while reset:
                    reset = False
                    for pirate, pos in zip(self.pirates, targetLocations):
                        path = self.game.get_directions(pirate, pos)[(self.game.get_turn() % 2) * -1]
                        if not len(path) == 0:
                            dest = self.game.destination(pirate.location, path)
                            pirateOnLocation = [p for p in self.pirates if p != pirate and p.location == dest]
                            blocker = pirateOnLocation[0] if len(pirateOnLocation) > 0 else None
                            # If some pirate is blocking the way:
                            if blocker is not None:
                                blocker_index = self.pirates.index(blocker)
                                selective_debug(self.game, "Pirate %d is blocking %d", blocker.id, pirate.id)
                                # If blocker is where he should be:
                                if blocker.location == targetLocations[blocker_index]:
                                    # Switch target locations between blocker and active pirate:
                                    targetLocations[self.pirates.index(pirate)] = tuple(targetLocations[blocker_index])
                                    targetLocations[blocker_index] = tuple(pos)
                                    selective_debug(self.game, "Switched pirate %d with pirate %d", pirate.id,
                                                    blocker.id)
                                    reset = True

                # Move pirates to formation:
                in_formation = True  # Number of pirates in target place
                for pirate, pos in zip(self.pirates, targetLocations):
                    selective_debug(self.game, "pirate: {}, location: {}, pos: {} ".format(
                        pirate.id, pirate.location, pos))
                    movePirate(pirate, pos, kamikaze=self.is_kamikaze)
                    in_formation &= pirate.location == pos  # if arrived already

                return in_formation

            def exportData(self):
                """
                export Tank class instance data to use in next turn

                :return: list with Tank class instance data
                """
                global tankData
                resumeData = [self.baseLoc, self.tankFormations, self.last_path]
                # resumeData.append([p.id for p in self.pirates])

                tankData[self.identifier] = resumeData

            def resumeFromData(self, resumeData):
                """
                resume Tank from data

                :param resumeData: Tank class instance data to use from last turn
                :raise if run into error, debug error but dismass exception
                """
                if resumeData is not None:
                    # noinspection PyBroadException
                    try:
                        self.baseLoc = resumeData.pop(0)
                        self.tankFormations = resumeData.pop(0)
                        self.last_path = resumeData.pop(0)
                        # To overcome that pirates are passed by value
                        # self.pirates = [self.game.get_my_pirate(id) for id in resumeData.pop(0)]

                        # selective_debug(self.game, "Successful resumed data!")
                    except:
                        selective_debug(self.game, "Error while resuming data: {}".format(sys.exc_info()[0]))

            def calculateFormation(self):
                """
                Calculate positions to form Tank in current game radius (base is (0,0))

                :return: sorted list of good Tank's location, when base is (0,0)
                """
                global radius

                # Path-faced tank formation calculation:
                # -----------------------------------

                starting_loc = (0, 0)
                direction_forms = []
                for direction in xrange(4):  # n, w, s, e
                    goodloc = []
                    count = 1
                    row = 0
                    while count > 0:
                        count = 0
                        for col in xrange(radius + 1):
                            col_or_row = (direction % 2 == 1)
                            possible_loc = (starting_loc[0] + col_or_row * col + (not col_or_row) * row,
                                            starting_loc[1] + col_or_row * row + (not col_or_row) * col)
                            for test_loc in goodloc:
                                if not my_in_range(possible_loc, test_loc):
                                    break
                            else:
                                count += 1
                                goodloc.append(possible_loc)
                                continue

                        row += 1 + -2 * int(direction >= 2)
                    direction_forms.append(goodloc)

                self.tankFormations = direction_forms  # n, w, s, e

                # Centered tank formation calculation:
                # -----------------------------------

                # starting_loc = (0, 0)
                # goodloc = [starting_loc]
                #
                # possible_loc = starting_loc
                # startedDown = False
                #
                # while True:
                #     count = 0
                #     while abs(possible_loc[1] - starting_loc[1]) <= radius:
                #         for test_loc in goodloc:
                #             if not my_in_range(possible_loc, test_loc):
                #                 break
                #         else:
                #             count += 1
                #             goodloc.append(possible_loc)
                #
                #         possible_loc = (possible_loc[0], possible_loc[1] + 1)
                #
                #     if count > 0 and not startedDown:
                #         possible_loc = (possible_loc[0] + 1, starting_loc[1])
                #     else:
                #         if not startedDown:
                #             possible_loc = (starting_loc[0] - 1, starting_loc[1])
                #         else:
                #             possible_loc = (possible_loc[0] - 1, starting_loc[1])
                #
                #         if startedDown and count == 0:
                #             break
                #
                #         startedDown = True
                #
                # goodloc = list(set(goodloc))
                # self.tankFormations = [sorted(goodloc, key=lambda loc: (abs(loc[0]), abs(loc[1])))] * 4

        self.tank_obj = TankInstance(self._game,
                                     self._pirates,
                                     identifier=self._identifier,
                                     startingLocation=self._starting_location,
                                     is_kamikaze=self._is_kamikaze)
        return self.tank_obj

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tank_obj.exportData()
tankData = {}


def selective_debug(game, string, *args):
    """
    print debug only on condition

    :param game: The game
    :param string: String to print (debug)
    :param args: arguments to format string
    """
    if game.get_turn() >= 155:
        game.debug(string, *args)
    return


class Munkres:
    """
    Calculate the Munkres solution to the classical assignment problem.
    See the module documentation for usage.
    """

    def __init__(self):
        """Create a new instance"""
        self.C = None
        self.row_covered = []
        self.col_covered = []
        self.n = 0
        self.Z0_r = 0
        self.Z0_c = 0
        self.original_length = 0
        self.original_width = 0
        self.marked = None
        self.path = None

    def make_cost_matrix(profit_matrix, inversion_function):
        """
        **DEPRECATED**

        Please use the module function ``make_cost_matrix()``.
        """
        import munkres
        return munkres.make_cost_matrix(profit_matrix, inversion_function)

    make_cost_matrix = staticmethod(make_cost_matrix)

    @staticmethod
    def pad_matrix(matrix, pad_value=0):
        """
        Pad a possibly non-square matrix to make it square.

        :Parameters:
            matrix : list of lists
                matrix to pad

            pad_value : int
                value to use to pad the matrix

        :rtype: list of lists
        :return: a new, possibly padded, matrix
        """
        max_columns = 0
        total_rows = len(matrix)

        for row in matrix:
            max_columns = max(max_columns, len(row))

        total_rows = max(max_columns, total_rows)

        new_matrix = []
        for row in matrix:
            row_len = len(row)
            new_row = row[:]
            if total_rows > row_len:
                # Row too short. Pad it.
                new_row += [pad_value] * (total_rows - row_len)
            new_matrix += [new_row]

        while len(new_matrix) < total_rows:
            new_matrix += [[pad_value] * total_rows]

        return new_matrix

    def compute(self, cost_matrix):
        """
        Compute the indexes for the lowest-cost pairings between rows and
        columns in the database. Returns a list of (row, column) tuples
        that can be used to traverse the matrix.

        :Parameters:
            cost_matrix : list of lists
                The cost matrix. If this cost matrix is not square, it
                will be padded with zeros, via a call to ``pad_matrix()``.
                (This method does *not* modify the caller's matrix. It
                operates on a copy of the matrix.)

                **WARNING**: This code handles square and rectangular
                matrices. It does *not* handle irregular matrices.

        :rtype: list
        :return: A list of ``(row, column)`` tuples that describe the lowest
                 cost path through the matrix

        """
        self.C = self.pad_matrix(cost_matrix)
        self.n = len(self.C)
        self.original_length = len(cost_matrix)
        self.original_width = len(cost_matrix[0])
        self.row_covered = [False] * self.n
        self.col_covered = [False] * self.n
        self.Z0_r = 0
        self.Z0_c = 0
        self.path = self.__make_matrix(self.n * 2, 0)
        self.marked = self.__make_matrix(self.n, 0)

        done = False
        step = 1

        steps = {1: self.__step1,
                 2: self.__step2,
                 3: self.__step3,
                 4: self.__step4,
                 5: self.__step5,
                 6: self.__step6
                 }

        while not done:
            try:
                func = steps[step]
                step = func()
            except KeyError:
                done = True

        # Look for the starred columns
        results = []
        for i in range(self.original_length):
            for j in range(self.original_width):
                if self.marked[i][j] == 1:
                    results += [(i, j)]

        return results

    @staticmethod
    def __copy_matrix(matrix):
        """Return an exact copy of the supplied matrix"""
        return copy.deepcopy(matrix)

    @staticmethod
    def __make_matrix(n, val):
        """Create an *n*x*n* matrix, populating it with the specific value."""
        matrix = []
        for i in range(n):
            matrix += [[val]*n]
        return matrix

    def __step1(self):
        """
        For each row of the matrix, find the smallest element and
        subtract it from every element in its row. Go to Step 2.
        """
        n = self.n
        for i in range(n):
            minval = min(self.C[i])
            # Find the minimum value for this row and subtract that minimum
            # from every element in the row.
            for j in range(n):
                self.C[i][j] -= minval

        return 2

    def __step2(self):
        """
        Find a zero (Z) in the resulting matrix. If there is no starred
        zero in its row or column, star Z. Repeat for each element in the
        matrix. Go to Step 3.
        """
        n = self.n
        for i in range(n):
            for j in range(n):
                if (self.C[i][j] == 0) and \
                        (not self.col_covered[j]) and \
                        (not self.row_covered[i]):
                    self.marked[i][j] = 1
                    self.col_covered[j] = True
                    self.row_covered[i] = True

        self.__clear_covers()
        return 3

    def __step3(self):
        """
        Cover each column containing a starred zero. If K columns are
        covered, the starred zeros describe a complete set of unique
        assignments. In this case, Go to DONE, otherwise, Go to Step 4.
        """
        n = self.n
        count = 0
        for i in range(n):
            for j in range(n):
                if self.marked[i][j] == 1:
                    self.col_covered[j] = True
                    count += 1

        if count >= n:
            step = 7  # done
        else:
            step = 4

        return step

    def __step4(self):
        """
        Find a noncovered zero and prime it. If there is no starred zero
        in the row containing this primed zero, Go to Step 5. Otherwise,
        cover this row and uncover the column containing the starred
        zero. Continue in this manner until there are no uncovered zeros
        left. Save the smallest uncovered value and Go to Step 6.
        """
        step = 0
        done = False
        while not done:
            (row, col) = self.__find_a_zero()
            if row < 0:
                done = True
                step = 6
            else:
                self.marked[row][col] = 2
                star_col = self.__find_star_in_row(row)
                if star_col >= 0:
                    col = star_col
                    self.row_covered[row] = True
                    self.col_covered[col] = False
                else:
                    done = True
                    self.Z0_r = row
                    self.Z0_c = col
                    step = 5

        return step

    def __step5(self):
        """
        Construct a series of alternating primed and starred zeros as
        follows. Let Z0 represent the uncovered primed zero found in Step 4.
        Let Z1 denote the starred zero in the column of Z0 (if any).
        Let Z2 denote the primed zero in the row of Z1 (there will always
        be one). Continue until the series terminates at a primed zero
        that has no starred zero in its column. Unstar each starred zero
        of the series, star each primed zero of the series, erase all
        primes and uncover every line in the matrix. Return to Step 3
        """
        count = 0
        path = self.path
        path[count][0] = self.Z0_r
        path[count][1] = self.Z0_c
        done = False
        while not done:
            row = self.__find_star_in_col(path[count][1])
            if row >= 0:
                count += 1
                path[count][0] = row
                path[count][1] = path[count-1][1]
            else:
                done = True

            if not done:
                col = self.__find_prime_in_row(path[count][0])
                count += 1
                path[count][0] = path[count-1][0]
                path[count][1] = col

        self.__convert_path(path, count)
        self.__clear_covers()
        self.__erase_primes()
        return 3

    def __step6(self):
        """
        Add the value found in Step 4 to every element of each covered
        row, and subtract it from every element of each uncovered column.
        Return to Step 4 without altering any stars, primes, or covered
        lines.
        """
        minval = self.__find_smallest()
        for i in range(self.n):
            for j in range(self.n):
                if self.row_covered[i]:
                    self.C[i][j] += minval
                if not self.col_covered[j]:
                    self.C[i][j] -= minval
        return 4

    def __find_smallest(self):
        """Find the smallest uncovered value in the matrix."""
        minval = sys.maxsize
        for i in range(self.n):
            for j in range(self.n):
                if (not self.row_covered[i]) and (not self.col_covered[j]):
                    if minval > self.C[i][j]:
                        minval = self.C[i][j]
        return minval

    def __find_a_zero(self):
        """Find the first uncovered element with value 0"""
        row = -1
        col = -1
        i = 0
        n = self.n
        done = False

        while not done:
            j = 0
            while True:
                if (self.C[i][j] == 0) and \
                        (not self.row_covered[i]) and \
                        (not self.col_covered[j]):
                    row = i
                    col = j
                    done = True
                j += 1
                if j >= n:
                    break
            i += 1
            if i >= n:
                done = True

        return row, col

    def __find_star_in_row(self, row):
        """
        Find the first starred element in the specified row. Returns
        the column index, or -1 if no starred element was found.
        """
        col = -1
        for j in range(self.n):
            if self.marked[row][j] == 1:
                col = j
                break

        return col

    def __find_star_in_col(self, col):
        """
        Find the first starred element in the specified row. Returns
        the row index, or -1 if no starred element was found.
        """
        row = -1
        for i in range(self.n):
            if self.marked[i][col] == 1:
                row = i
                break

        return row

    def __find_prime_in_row(self, row):
        """
        Find the first prime element in the specified row. Returns
        the column index, or -1 if no starred element was found.
        """
        col = -1
        for j in range(self.n):
            if self.marked[row][j] == 2:
                col = j
                break

        return col

    def __convert_path(self, path, count):
        for i in range(count+1):
            if self.marked[path[i][0]][path[i][1]] == 1:
                self.marked[path[i][0]][path[i][1]] = 0
            else:
                self.marked[path[i][0]][path[i][1]] = 1

    def __clear_covers(self):
        """Clear all covered matrix cells"""
        for i in range(self.n):
            self.row_covered[i] = False
            self.col_covered[i] = False

    def __erase_primes(self):
        """Erase all prime markings"""
        for i in range(self.n):
            for j in range(self.n):
                if self.marked[i][j] == 2:
                    self.marked[i][j] = 0