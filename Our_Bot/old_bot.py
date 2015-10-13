#!/usr/bin/env python
# coding=utf-8
__author__ = "Team Hadarim 2015"

import sys
import math
import heapq
# import random
# import cProfile


tankData = {}
last_locs = {}
movements = []
time_to_move = 2
time_for_check = 10
max_turn_time = 0
re_routes = set()
enemySpawns = ([], [])
enemiesInRadius_cache = {}


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


# Write current bot strategy here:
def runStrategy(game):
    islands = game.not_my_islands() * 2
    for p in game.my_pirates():
        if len(islands) == 0:
            islands += game.not_my_islands()
        if len(islands) == 0:
            islands += game.my_islands()
        target = min(islands, key=lambda island: game.distance(island.location, p.location))  # Nearest location
        islands.remove(target)
        if not game.is_capturing(p):
            movePirate(p, target.location)


# --------------------------------------------------------------------------------------------------- #
# ---------------------------------- DON'T EDIT BELOW THIS LINE ------------------------------------- #
# --------------------------------------------------------------------------------------------------- #

# Profiler
# ---------------------------------------------------------
# def do_turn(game):
#     global rgame
#     rgame = game
#
#     if game.get_turn() > 200:
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
    global radius, attackRadius, max_turn_time  # , rgame
    # game = rgame

    starting_time = game.time_remaining()

    if game.get_turn() == 1:
        attackRadius = game.get_attack_radius()
        radius = int(math.sqrt(attackRadius))
        locateEnemySpawnsCenters(game)

    if not endGame(game) and game.get_my_score() > game.get_enemy_score()+100:
        # Current bot strategy
        runStrategy(game)

    proccessMovements(game)
    turn_time = starting_time - game.time_remaining()
    max_turn_time = max(max_turn_time, turn_time)
    selective_debug(game, "Turn took: {} ms / 100 ms [Max so far: {} ms / 100 ms]".format(turn_time, max_turn_time))


def assign_kamikaze(game, my_pirates, enemy_pirates):
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

    len_m = len(my_pirates)
    len_e = len(enemy_pirates)

    my_table = []
    # Build table
    for i in xrange(min(len_m, len_e)):
        for j in xrange(max(len_m, len_e)):
            if len_e <= len_m:
                enemy_pirate = enemy_pirates[i]
                my_pirate = my_pirates[j]
            else:
                enemy_pirate = enemy_pirates[j]
                my_pirate = my_pirates[i]

            my_table.append((enemy_pirate, my_pirate, game.distance(enemy_pirate, my_pirate)))

    selective_debug(game, [(row[0].id, row[1], row[2]) for row in my_table])

    largest = None
    diff = 0
    if len_e > len_m:
        diff = len_e - len_m
        largest = enemy_pirates
    elif len_m > len_e:
        diff = len_m - len_e
        largest = my_pirates

    # Proccess table
    good_table = set()
    while len(good_table) + len(my_table) > min(len_e, len_m):
        max_distance_row, max_distance = max(enumerate(my_table), key=lambda p: p[1][2])
        enemy_found, my_found = False, False
        temp = list(my_table)
        temp += list(good_table)
        for r in xrange(len(temp)):
            row = temp[r]
            if r != max_distance_row:
                enemy_found |= (row[0] == max_distance[0])
                my_found |= (row[1] == max_distance[1])

            if my_found and enemy_found:
                break
        else:
            temp = list(my_table)
            temp += list(good_table)
            for row in temp:
                if row != max_distance:
                    if enemy_found:
                        if row[0] == max_distance[0]:
                            if diff == 0 or largest == enemy_pirates:
                                # Make sure there are more pirates of this kind
                                atemp = list(my_table)
                                atemp += list(good_table)
                                for arow in atemp:
                                    if arow != row:
                                        if arow[1] == row[1] and row in my_table:
                                            my_table.remove(row)
                                            # print("Removed row {} from enemy".format(row))
                                            break
                    elif my_found:
                        if row[1] == max_distance[1]:
                            if diff == 0 or largest == my_pirates:
                                my_table.remove(row)
            if diff == 0 \
                    or (largest == enemy_pirates and enemy_found) \
                    or (largest == my_pirates and my_found) \
                    or not (enemy_found or my_found):
                good_table.add(max_distance)
            else:
                diff -= 1

        my_table.remove(max_distance)

    good_table.update(my_table)
    return good_table


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

    global tankData, enemySpawns

    # Check if it is not time for an end-game yet:
    # TODO: change to a more smart function to switch to end-game (consider having more or equal number of pirates alive than enemy)
    if game.get_my_score() <= game.get_enemy_score() or len(game.my_islands()) < len(game.enemy_islands()):
        return False

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
        while len(kamikaze) < len(pirates) and len(enemies) > 0:
            assignments = assign_kamikaze(game, [pirate for pirate in pirates if pirate not in kamikaze], enemies)
            # selective_debug(game, [(row[0].id, row[1].id, row[2]) for row in assignments])
            ratio_count = [0]*len(enemies)
            for assignment in assignments:
                chosen_enemy = assignment[0]
                if chosen_enemy in enemies:
                    if ratio_count[enemies.index(chosen_enemy)] < 2:
                        ratio_count[enemies.index(chosen_enemy)] += 1
                        chosen_pirate = assignment[1]
                        selective_debug(game, "Sending pirate {} to kamikaze on {}".format(
                            chosen_pirate.id, chosen_enemy.id
                        ))
                        movePirate(chosen_pirate, chosen_enemy, kamikaze=True)
                        kamikaze.append(chosen_pirate)
                    else:
                        enemies.remove(chosen_enemy)

        tank_pirates = [p for p in pirates if p not in kamikaze]
        for spawn, spawn_enemy_count in zip(enemySpawns[0], enemySpawns[1]):
            if len(tank_pirates) > 0:
                # Choose pirates for tank
                assignments = assign_kamikaze(game, [spawn] * spawn_enemy_count, tank_pirates)
                selective_debug(game, assignments)
                spawn_tank_pirates = []
                for assignment in assignments:
                    spawn_tank_pirates.append(assignment[0])
                    tank_pirates.remove(assignment[0])

                # Move tank to enemy spawn
                selective_debug(game, "Tank is: {} for spawn {}".format([p.id for p in spawn_tank_pirates], spawn))
                myTank = Tank(game, spawn_tank_pirates, tankData.get(spawn, None))
                myTank.moveTank(spawn)
                tankData[spawn] = myTank.exportData()

    return True


def locateEnemySpawnsCenters(game):
    global enemySpawns

    enemies_initial_locs = [enemy.initial_loc for enemy in game.all_enemy_pirates()]
    spawns = []
    spawns_enemy_count = []
    for initial_loc in enemies_initial_locs:
        for spawn_index, spawn in enumerate(spawns):
            if pathNotPassable(game, initial_loc, spawn):
                avr_r = (initial_loc[0] + spawn[0]) / 2
                avr_c = (initial_loc[1] + spawn[1]) / 2
                spawns[spawn_index] = (avr_r, avr_c)
                spawns_enemy_count[spawn_index] += 1
                break
        else:  # No break
            spawns.append(initial_loc)  # New spawn
            spawns_enemy_count.append(1)

    selective_debug(game, "Enemy spawns located: {}".format(spawns))

    enemySpawns = (list(spawns), list(spawns_enemy_count))


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
    global movements

    if type(dest) is not tuple:
        dest = dest.location

    for move in movements:  # If already has pirate in movements, remove move and add new one
        if move[0].id == pirate.id:
            movements.remove(move)

    movements.append((pirate, dest, kamikaze, in_tank))


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
    global causes, last_locs, re_routes

    if re_routed and hasattr(pirate, 'location'):
        # Add to global
        re_routes.add(((pirate,), (old_dest,), dest))

    reset = False
    done_rerouting = False
    # Check if was re-routed:
    for reroute in re_routes.copy():
        # If this re-route includes my pirate, re-route him
        if pirate in reroute[0]:
            pirate_old_dest = reroute[1][reroute[0].index(pirate)]
            reroute_dest = reroute[2]

            # Check if everyone got to re-route target:
            for sub_pirate in reroute[0]:
                if (len(reroute[0]) == 1 and sub_pirate.location != reroute_dest) or\
                        (len(reroute[0]) > 1 and not my_in_range(sub_pirate, reroute_dest)):
                    break  # Some pirate still has not reached target
            else:  # No breaks
                selective_debug(game,
                                "Pirate {} reached re-route target, returning to original destination".format(pirate))
                re_routes.discard(reroute)  # Done re-routing
                done_rerouting = True
                break

            # If still on way to original final dest
            if old_dest is None:
                old_dest = dest

            if old_dest == pirate_old_dest:  # Kept same final destination
                dest = reroute_dest  # Update dest to re-route target
            else:  # Changed final destination
                selective_debug(game,
                                "Pirate {} changed final target, returning to original destination".format(pirate))
                # This breaks re-routing for all pirates invloved
                reset = True  # Means that all pirates moves should be re-calculated
                done_rerouting = True
                re_routes.discard(reroute)  # Done re-routing

            break

    last_loc = None
    if done_rerouting:
        last_loc = last_locs[pirate]
        selective_debug(game, "Pirate {} last loc is: {}".format(pirate.id, last_loc))

    path1 = game.get_directions(pirate, dest)[alternating * ((game.get_turn() % 2) * -1)]
    path1_dest = game.destination(pirate, path1)
    path1_cancel_cause = ''
    path1_good = game.is_passable(path1_dest) \
        and len(path1) > 0 \
        and not (is_kamikaze and path1_dest in [_isl.location for _isl in game.islands()]) \
        and path1_dest != last_loc

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
        and path2_dest != last_loc

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

    # Check if all re-routed pirates are still alive
    for reroute in re_routes.copy():
        for pirate in reroute[0]:
            if pirate not in game.my_pirates():
                # This breaks re-routing for all pirates invloved
                re_routes.discard(reroute)
                break

    # Un-pack movements
    reset = True
    while reset:
        reset = False
        for move_i in xrange(len(movements)):
            move = movements[move_i]
            pirate, dest, is_kamikaze, is_tank = move[0], move[1], move[2], move[3]

            dest = nearestPassableLoc(game, dest)
            path, cancel_cause, reset = createPaths(game, pirate, dest, is_kamikaze)

            if reset:
                break

            def assign(lst, val):
                try:
                    lst[move_i] = val
                except IndexError:
                    lst.append(val)
            assign(final_dests, dest)
            assign(pirates, pirate)
            assign(paths, path)
            assign(start_paths, list(path))
            assign(dests, (game.destination(pirate, path[0]), game.destination(pirate, path[1])))
            assign(cancel_causes, cancel_cause)
            assign(escapes, False)
            assign(is_rerouted, False)
            assign(kamikaze, is_kamikaze)
            assign(in_tank, is_tank)

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

    # Make sure that each path is safe to travel
    for x in xrange(3):  # This should run 3 times so that pirates will be updated about how other pirates paths changed
        time_for_check_start = game.time_remaining()
        if time_for_check_start < time_for_check + time_to_move:  # No time for another check
            selective_debug(game,
                            "No time for another check, breaking. [Done: {} ; Time left: {} ; Max time per check: {}]".
                            format(x, time_for_check_start, time_for_check))
            break

        for i in xrange(len(pirates)):
            pirate, path, dest, start_path = pirates[i], paths[i], dests[i], start_paths[i]
            rerouted, escaped, is_kamikaze, is_tank = is_rerouted[i], escapes[i], kamikaze[i], in_tank[i]
            pirate_index = i

            # selective_debug(game, "Pirate {} paths: {}".format(pirate.id, path))
            # Start with checking possible paths
            for path_index, dest in zip(xrange(len(path)), dest):
                checkPath(game, pirates, paths, dests, cancel_causes, escapes, pirate, path_index, dest, is_kamikaze)
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
                                            pirate)
                    # None = no re-route found or no need to re-route
                    if result is not None:
                        pirates_to_move, old_targets, new_target = result

                        # Calc paths for new destination for each pirate
                        for move_pirate in pirates_to_move:
                            move_index = pirates.index(move_pirate)
                            changePath(game, pirates, paths, dests, cancel_causes, move_pirate, kamikaze[move_index],
                                       new_target=new_target)
                            is_rerouted[move_index] = True  # tag as re-routed
                            selective_debug(game, "Re-routed pirate {} to {} to go around {}.".format(
                                move_pirate.id, new_target,
                                [causes.reverse_mapping[item] for item in
                                 cancel_causes[move_index] if item in range(2)]))

                        re_routes.add(tuple(result))  # Add to global
                        continue  # Succesfully rerouted, continue to proccess next pirate

                # No re-route found or no need to re-route, try escaping
                escape_direction, moved_pirates = escapeEnemy(game, pirates, dests, pirate)
                if escape_direction != '-':  # Found a new way
                    selective_debug(game, "Pirate {} moving to the {} to escape.".format(pirate.id, escape_direction))
                    changePath(game, pirates, paths, dests, cancel_causes, pirate, is_kamikaze,
                               new_path=escape_direction)
                    escapes[i] = True  # tag as escaped
                    for i_pirate, i_path in moved_pirates:  # Pirates that occupy chosen direction
                        i_pirate_index = pirates.index(i_pirate)
                        new_path = escape_direction if paths[i_pirate_index][i_path] == '-' else '-'
                        selective_debug(game, "Pirate {} moved pirate {} to '{}' so he can escape.".format(
                            pirate.id, i_pirate.id, new_path
                        ))
                        paths[i_pirate_index][i_path] = new_path
                        new_dest = nearestPassableLoc(game, game.destination(i_pirate, new_path), dests)
                        if i_path == 0:
                            dests[i_pirate_index] = (new_dest, dests[i_pirate_index][1])
                        else:
                            dests[i_pirate_index] = (dests[i_pirate_index][0], new_dest)

                        is_rerouted[i_pirate_index] = False
                        final_dests[i_pirate_index] = new_dest

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

    time_to_move = max(time_to_move, time_to_move_start - game.time_remaining())

    # Clear movements, cache
    enemiesInRadius_cache.clear()
    movements[:] = []


def checkPath(game, pirates, paths, dests, cancel_causes, escapes, my_pirate, path_index, my_dest, is_kamikaze):
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

    if paths[list_index][path_index] == '-':
        return False  # Good path

    # Test if some other pirate will occupy destination for sure
    for other_index, other_pirate in enumerate(pirates):
        if other_pirate.id != my_pirate.id:
            other_dest = dests[other_index]
            # If both his paths will collide with current path:
            if other_dest[0] == my_dest and other_dest[1] == my_dest:
                # selective_debug(game, "Pirate {} is going to collide with {} if he goes {}".format(
                # my_pirate.id, other_pirate.id, paths[list_index][path_index]))
                paths[list_index][path_index] = '-'
                cancel_causes[list_index][path_index] = causes.NOT_PASSABLE
                return True  # Not a good path

    enemies = enemiesInRadius(game, my_dest)
    # selective_debug(game, "Pirate {} enemies: {}".format(my_pirate.id, enemies))

    if len(enemies) == 0:
        return False  # Good path

    in_small_radius = []
    final_large_radius = []
    if len(enemies) < len(pirates):
        in_large_radius = []
        for friendly_pirate, path, dest, escaped in zip(pirates, paths, dests, escapes):
            if friendly_pirate.id != my_pirate.id and not escaped:
                for _dest_index, _dest in enumerate(dest):
                    if path[_dest_index] == '-' \
                            and path[1 - _dest_index] != '-':
                        continue

                    # If friendly pirate does not go on island (pirates on island cannot support in a battle)
                    if _dest not in [island.location for island in game.islands()]:
                        distance = game.distance(_dest, my_dest)  # Distance from my_pirate to friendly_pirate
                        my_list = None
                        if distance < radius:
                            my_list = in_small_radius
                        elif distance == radius or distance == radius + 1:
                            my_list = in_large_radius

                        if my_list is not None:
                            # Delete friendly pirate path if it is colliding with another pirate path
                            for other_friendly in my_list:
                                other_index = pirates.index(other_friendly)
                                other_dest = dests[other_index]

                                for other_dest_item_index, other_dest_item in enumerate(other_dest):
                                    if other_dest_item == _dest:
                                        # Delete other pirate colliding path
                                        paths[other_index][other_dest_item_index] = '-'

                                        # Update dests list
                                        dests[other_index] = (
                                            game.destination(
                                                other_friendly,
                                                paths[other_index][0]
                                            ),
                                            game.destination(
                                                other_friendly,
                                                paths[other_index][1]
                                            )
                                        )

                            # If not already included in a list
                            if friendly_pirate not in list(in_small_radius + in_large_radius):
                                my_list.append(friendly_pirate)

        for friendly_pirate in in_small_radius:
            dest = dests[pirates.index(friendly_pirate)]

            ok = False
            for _dest in dest:
                distance = game.distance(_dest, my_dest)  # Distance from my_pirate to friendly_pirate
                ok |= distance < radius

            if not ok:
                in_small_radius.remove(friendly_pirate)

        for friendly_pirate in in_large_radius:
            dest = dests[pirates.index(friendly_pirate)]

            ok = False
            for _dest in dest:
                distance = game.distance(_dest, my_dest)  # Distance from my_pirate to friendly_pirate
                ok |= distance == radius or distance == radius + 1

            if not ok:
                in_large_radius.remove(friendly_pirate)

        if len(in_large_radius) + len(in_small_radius) >= len(enemies):
            for pirate in in_large_radius:
                if len(final_large_radius) + len(in_small_radius) < len(enemies):
                    pirate_index = pirates.index(pirate)
                    for dest_index, dest in enumerate(dests[pirate_index]):
                        if game.distance(dest, my_dest) <= radius:
                            final_large_radius.append([pirate_index, dest_index])
                            break
                else:
                    break

            if len(final_large_radius) + len(in_small_radius) >= len(enemies):
                # Can survive, actually change other pirates paths so they'll help current pirate
                paths_changed = False
                for data in final_large_radius:
                    if paths[data[0]][1 - data[1]] != '-':
                        selective_debug(game, "Pirate {} canceled pirate {} original path '{}' ".format(
                            my_pirate.id, pirates[data[0]].id, paths[data[0]][1 - data[1]]))

                        paths[data[0]][1 - data[1]] = '-'
                        # Update dests list
                        dests[data[0]] = (
                            game.destination(
                                pirates[data[0]],
                                paths[data[0]][0]
                            ),
                            game.destination(
                                pirates[data[0]],
                                paths[data[0]][1])
                        )
                        paths_changed = True
                selective_debug(game, "Pirate {} can survive with {} friends vs {} enemies".format(
                    my_pirate.id, len(final_large_radius) + len(in_small_radius), len(enemies)))
                return paths_changed  # Done checking path
            else:
                selective_debug(game, "Pirate {} will die on path '{}' - enemies({}): {} || friends({}): {}".format(
                    my_pirate.id,
                    paths[list_index][path_index],
                    len(enemies),
                    enemies,
                    len(final_large_radius) + len(in_small_radius),
                    final_large_radius + in_small_radius
                ))
                pass
        else:
            selective_debug(game, "Pirate {} will die on path '{}' - enemies({}): {} || friends({}): {}".format(
                my_pirate.id,
                paths[list_index][path_index],
                len(enemies),
                enemies,
                len(final_large_radius) + len(in_small_radius),
                final_large_radius + in_small_radius
            ))
            pass

    if is_kamikaze:
        # Test if gonna be on an island (can't fight if so)
        if my_dest in [isl.location for isl in game.islands()]:
            selective_debug(game,
                            "Pirate {} is going to be on an island if he goes {} - he won't survive battle".format(
                                my_pirate.id, paths[list_index][path_index]))
            paths[list_index][path_index] = '-'
            cancel_causes[list_index][path_index] = causes.NOT_PASSABLE
            return True  # Not a good path

        for enemy in enemies:
            updated_dests = list(dests)
            updated_pirates = list(pirates)
            updated_dests.remove(updated_dests[list_index])
            updated_pirates.remove(my_pirate)

            enemy_no_longer_threat = False
            willDie = pirateWillDie(game, enemy, pirates, dests, kamikaze_target=True)
            if willDie:
                # Assume enemy will be escaping (to ensure my_pirate safety)
                enemy_escape_path, moved_pirates = escapeEnemy(game, pirates, dests, enemy)
                enemy_destination = game.destination(enemy, enemy_escape_path)
                enemy_no_longer_threat = not my_in_range(enemy_destination, my_dest)
                selective_debug(game, "Pirate {} - enemy will die and be trying to escape to the '{}'".format(
                    my_pirate.id, enemy_escape_path
                ))

                willDie = pirateWillDie(game, enemy, pirates, dests, enemy_destination, kamikaze_target=True)
            else:
                enemy_destination = enemy.location  # game.destination(enemy, game.get_directions(enemy, my_pirate)[0])

            # Check if my_pirate actually killed an enemy (if he would also be killed without my_pirate)
            if not pirateWillDie(game, enemy, updated_pirates, updated_dests, enemy_destination):
                if willDie:
                    selective_debug(game, "Pirate {} will cause enemy {} to die if he goes {}".format(
                        my_pirate.id, enemy.id, paths[list_index][path_index]))
                    return False  # Can kamikaze
                elif enemy_no_longer_threat:
                    if len(final_large_radius) + len(in_small_radius) >= len(enemies) - 1:
                        selective_debug(game, "Pirate {} will cause enemy {} to die if he goes {}".format(
                            my_pirate.id, enemy.id, paths[list_index][path_index]))
                        return False  # Can survive

            selective_debug(game, "Pirate {} will not cause enemy {} to die if he goes {}".format(
                my_pirate.id, enemy.id, paths[list_index][path_index]))

    paths[list_index][path_index] = '-'
    cancel_causes[list_index][path_index] = causes.ENEMY
    return True  # Not a good path


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
            islands = [isl for isl in game.islands() if isl.location == el]
            # Island being captured
            if len(islands) > 0:
                island = islands[0]
                # already captured atleast some of an island
                if island.turns_being_captured > island.capture_turns / 4:
                    continue  # skip this enemy (enemies on islands don't count)

            enemy_on_loc = game.get_pirate_on(loc) in game.enemy_pirates()

            for r_loc in xrange(-1, 2):  # Row
                for c_loc in xrange(-1, 2):  # Col
                    if ((c_loc == 0 or r_loc == 0) and enemy_on_loc) or (c_loc == 0 and r_loc == 0):
                        for r in xrange(-1, 2):  # Row
                            for c in xrange(-1, 2):  # Col
                                if c == 0 or r == 0:
                                    # If he might be able to attack me:
                                    if my_in_range((el[0] + r, el[1] + c), (loc[0] + r_loc, loc[1] + c_loc))\
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

    if owner or destenations is None or pirates is None:
        enemiesInRadius_cache[(loc, real_owner)] = strong_enemies

    return list(strong_enemies)


def pirateWillDie(game, checked_enemy, my_pirates, my_dests, enemy_location=None, kamikaze_target=False):
    """
    Check if pirate will die

    :param game: the game
    :param checked_enemy:
    :param my_pirates:
    :param my_dests:
    :param enemy_location:
    :rtype : bool
    :return: True if pirate will die (i.e. have more enemies than friends). False otherwise
    """
    if enemy_location is None:
        enemy_location = checked_enemy.location

    notOwnedPirate = (checked_enemy.owner != game.ME)
    his_friends = set(enemiesInRadius(game, enemy_location,
                                      owner=notOwnedPirate,
                                      pirates=my_pirates,
                                      destenations=my_dests))
    his_friends.discard(checked_enemy)

    his_enemies = set(enemiesInRadius(game, enemy_location,
                                      owner=(not notOwnedPirate),
                                      pirates=my_pirates,
                                      destenations=my_dests))

    if kamikaze_target and len(his_enemies) == 0:
        his_enemies.add(None)

    # if notOwnedPirate:
    #     selective_debug(game, "Enemies of enemy {}: {} vs {}".format(checked_enemy.id, his_enemies, his_friends))
    # else:
    #     selective_debug(game, "Pirate {} enemies: {} || friends: {}".format(
    #         checked_enemy.id, his_enemies, his_friends))

    return len(his_enemies) > len(his_friends)


def escapeEnemy(game, pirates, dests, my_pirate):
    ownedPirate = (my_pirate.owner == game.ME)

    # Sum enemies
    strong_enemies = enemiesInRadius(game, my_pirate.location,
                                     owner=ownedPirate,
                                     pirates=pirates,
                                     destenations=dests)

    pirates_to_move = frozenset()
    # Escape from enemies
    if len(strong_enemies) > 0:
        my_friends = set(enemiesInRadius(game, my_pirate.location,
                                         owner=not ownedPirate,
                                         pirates=pirates,
                                         destenations=dests))
        my_friends.discard(my_pirate)
        if ownedPirate:
            final_enemies = set(strong_enemies)

            if len(final_enemies) > len(my_friends):
                if ownedPirate:
                    selective_debug(game, "Pirate {} will die if he doesn't move - "
                                          "{} f vs {} e : F: {} || E: {}".format(my_pirate.id, len(my_friends),
                                                                                 len(final_enemies), my_friends,
                                                                                 final_enemies))
                pass  # Not ok - my_pirate will die
            else:  # no breaks
                selective_debug(game, "Pirate {} will not move - won't die. {} f vs {} e : F: {} || E: {}".format(
                    my_pirate.id, len(my_friends), len(final_enemies), my_friends, final_enemies))
                return '-', pirates_to_move  # It is OK to do nothing, pirate won't die

        possible_directions = {'n', 'e', 's', 'w'}
        backup_directions = set()
        occupied_directions = set()

        # Plan escape route
        for se in strong_enemies:
            for direction in game.get_directions(my_pirate, se.location):
                if direction in possible_directions:
                    if ownedPirate:
                        selective_debug(game, "Pirate {} escape path '{}' removed - enemy".format(
                            my_pirate.id, direction))
                    backup_directions.add(direction)
                    possible_directions.discard(direction)

        # Remove directions on which my_pirate will die or will be on island with less friends
        for p_dir in possible_directions.copy():
            _dest = game.destination(my_pirate, p_dir)
            if pirateWillDie(game, my_pirate, pirates, dests, _dest):
                if ownedPirate:
                    selective_debug(game, "Pirate {} escape path '{}' removed - willDie".format(
                        my_pirate.id, p_dir
                    ))
                backup_directions.add(p_dir)
                possible_directions.discard(p_dir)

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
                                                                                                   other_pirate,
                                                                                                   other_dest, _dest))
                if is_occupied and len(pirates_occuping) > 0:
                    occupied_directions.add((direction, frozenset(pirates_occuping)))
            else:
                for other_pirate in game.enemy_pirates():
                    if other_pirate.id != my_pirate.id:
                        is_occupied |= (other_pirate.location == _dest)

            if (not game.is_passable(_dest)) or is_occupied:
                # if ownedPirate:
                # selective_debug(game, "Pirate {} escape path '{}' removed - occupied or not passable".format(
                # my_pirate.id, direction))
                possible_directions.discard(direction)

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
            if moved_pirates:  # If had to move pirates, actually move them here
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


def reroutePirates(game, pirates, paths, dests, kamikaze, final_dests, cancel_causes, my_pirate):
    global radius, causes, re_routes

    my_index = pirates.index(my_pirate)
    my_cancel_causes = cancel_causes[my_index]

    # Check if already re-routed
    for reroute in re_routes.copy():
        if my_pirate in reroute[0]:
            # Cancel last re-route and recreate paths for all involved pirates to their old dest
            for pirate_index, pirate in enumerate(reroute[0]):
                index = pirates.index(pirate)
                is_kamikaze = kamikaze[index]
                pirate_old_dest = reroute[1][pirate_index]
                final_dests[index] = pirate_old_dest
                path, cancel_cause, reset = createPaths(game, pirate, pirate_old_dest, is_kamikaze)
                paths[index] = path
                dests[index] = (game.destination(pirate, path[0]), game.destination(pirate, path[1]))
                cancel_causes[index] = cancel_cause
            re_routes.discard(reroute)
            break  # Break and continue with re-route to old dest

    my_final_dest = final_dests[my_index]

    # if my_final_dest == my_pirate.location:
    #     return None  # pirate didn't want to go anywhere

    pirates_to_move = [my_pirate]
    old_dests = [my_final_dest]

    for cause in my_cancel_causes:
        # Handle first case when being stuck because of non-passable location
        if cause == causes.NOT_PASSABLE:
            is_kamikaze = kamikaze[my_index]
            new_target = obstaclePass(game, my_pirate.location, my_final_dest, is_kamikaze=is_kamikaze, dests=dests)
            if new_target is not None and new_target != my_final_dest:
                return tuple(pirates_to_move), tuple(old_dests), new_target
            selective_debug(game, (new_target, my_final_dest))
            selective_debug(game, "Pirate {} could not find path to go around obstacle".format(my_pirate.id))
            pass  # Did not find path

        # Handle case when being stuck because of enemy
        elif cause == causes.ENEMY:
            for other_pirate, other_final_dest, other_path, other_cause in\
                    zip(pirates, final_dests, paths, cancel_causes):
                if other_pirate.id != my_pirate.id:
                    # If both pirates go to a near dest and other pirate also escaping from enemy and stuck
                    if my_in_range(my_final_dest, other_final_dest) or my_final_dest == other_final_dest:
                        if other_pirate not in pirates_to_move:
                            pirates_to_move.append(other_pirate)
                            old_dests.append(other_final_dest)

            # selective_debug(game, "Other pirates of pirate {} for target {} are: {}".format(
            #     my_pirate.id, my_final_dest, pirates_to_move))

            # Multiple pirates afraid to attack with shared destination
            if len([m_pirate for m_pirate in pirates_to_move if
                    not my_in_range(m_pirate, my_pirate) and m_pirate != my_pirate]) > 0:
                # Find good place for regrouping
                pirates_rows = [mpirate.location[0] for mpirate in pirates_to_move]
                pirates_cols = [mpirate.location[1] for mpirate in pirates_to_move]
                avg_row = sum(pirates_rows) / len(pirates_to_move)
                avg_col = sum(pirates_cols) / len(pirates_to_move)

                try:
                    row_sign = (avg_row - my_final_dest[0]) / abs(avg_row - my_final_dest[0])
                except ZeroDivisionError:
                    row_sign = 0
                try:
                    col_sign = (avg_col - my_final_dest[1]) / abs(avg_col - my_final_dest[1])
                except ZeroDivisionError:
                    col_sign = 0

                if col_sign == 0 and row_sign == 0:
                    row_sign = 1

                cur_r = game.distance((avg_row, avg_col), my_final_dest)
                delta = radius + 3 - cur_r
                avg_row += row_sign * delta
                avg_col += row_sign * delta
                new_target = (avg_row, avg_col)

                return tuple(pirates_to_move), tuple(old_dests), new_target

    return None  # Didn't found a re-route


def obstaclePass(game, my_pirate_loc, dest, is_kamikaze=False, dests=None):
    """
    :rtype : location of the next step that should be taken towards dest. None if no path found
    """
    # If destenation is actually reachable, pass obstacle using Best First Search
    if game.is_passable(dest) and (dests is None or
                                   len([_dest for _dests in dests for _dest in _dests if _dest == dest]) == 0):

        selective_debug(game, "Pirate on location {} using Best First Search to pass obstacle in way to target: {}".format(
            my_pirate_loc, dest
        ))

        # Go in reverse
        goal = my_pirate_loc
        start = dest
        testLoc = lambda loc: loc == goal\
            or (game.is_passable(loc)
                and (dests is None or len([n_dest for n_dests in dests for n_dest in n_dests if n_dest == loc]) == 0)
                and (not is_kamikaze or len([_isl for _isl in game.islands() if _isl.location == loc]) == 0)
                )

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
                selective_debug(game, "Pirate on location {} best-first search reached goal! (Found new target: {})".format(
                    my_pirate_loc, came_from[current]))
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


def nearestPassableLoc(game, loc, dests=None):  # Midpoint circle algorithm
    testLoc = lambda c, r:\
        game.is_passable((r, c)) and\
        (dests is None or len([n_dest for n_dests in dests for n_dest in n_dests if n_dest == (r, c)]) == 0)

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


def my_in_range(loc1, loc2):
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

    d_row, d_col = loc1[0]-loc2[0], loc1[1]-loc2[1]
    distance = d_row * d_row + d_col * d_col
    if 0 <= distance <= attackRadius:
        return True
    return False


class Tank():
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

    def __init__(self, game, pirates, tank_data, startingLocation=None):
        """
        Creates Tank instance
        :param game: the game
        :param pirates: list of the pirates of the tank
        :param startingLocation: tuple - base location of the Tank (Location - LocationObject)
        :param tank_data: if no Tank was created, is None.
               after first time - list. used to resume data: contains  Tank's base location
        """

        self.game = game
        self.pirates = pirates

        if tank_data is not None:
            self.resumeFromData(tank_data)
        else:
            self.calculateFormation()
            if startingLocation is None:
                self.baseLoc = nearestPassableLoc(self.game, self.getBaseLoc())
            else:
                self.baseLoc = nearestPassableLoc(self.game, startingLocation)

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

        dest = nearestPassableLoc(self.game, dest)
        paths, cancel_causes, reset = createPaths(self.game, self.baseLoc, dest, alternating=False)

        path = paths[0] if paths[0] != '-' else paths[1]

        if path != '-':
            self.last_path = path

        # selective_debug(self.game, "Tank going to target {} with path '{}'".format(dest, path))

        if self.formTank(path):
            # selective_debug(self.game, "We've got a tank! prepare to die..")
            if path is not None and path != '-':
                for pirate in self.pirates:
                    dest = self.game.destination(pirate, path)
                    movePirate(pirate, dest)

                # Apply new base
                self.baseLoc = self.game.destination(self.baseLoc, path)
            else:
                selective_debug(self.game, "Stopped tank from moving.")

    def changeReference(self, locations):
        global radius
        max_rows = self.game.get_rows()
        max_cols = self.game.get_cols()
        Aradius = int(radius)

        # Fix out-of map tank
        if max_cols - self.baseLoc[1] < Aradius:
            self.baseLoc = (self.baseLoc[0], max_cols - Aradius - 1)

        if max_rows - self.baseLoc[0] < Aradius:
            self.baseLoc = (max_rows - Aradius - 1, self.baseLoc[1])
        elif self.baseLoc[0] < Aradius:
            self.baseLoc = (Aradius, self.baseLoc[1])

        # Adjust location list to be around a new base location
        newList = []
        for loc in locations:
            newList.append((loc[0] + self.baseLoc[0], loc[1] + self.baseLoc[1]))
        return newList

    def formTank(self, path='-'):
        if len(self.pirates) == 0:
            return False
        elif len(self.pirates) == 1 and self.pirates[0].location == self.baseLoc:
            return True

        self.pirates = [pirate for pirate in self.pirates if not pirate.is_lost]

        if path == '-':
            path = self.last_path
        paths = ['n', 'w', 's', 'e']
        targetLocations = [pos for pirate, pos in zip(self.pirates, self.tankFormations[paths.index(path)])]
        selective_debug(self.game, "Tank front is faced to the '{}'".format(path))

        # Calculate position for each pirate
        targetLocations = self.changeReference(targetLocations)

        self.pirates = [pirate for pirate, pos in zip(self.pirates, targetLocations)]

        # Check available target locations
        tempPirates = list(self.pirates)
        tempLocs = list(targetLocations)

        for pirate_index, pirate in enumerate(self.pirates):
            if pirate.location in targetLocations:
                tempPirates.remove(pirate)
                tempLocs.remove(pirate.location)
                targetLocations[pirate_index] = pirate.location

        # Update target locations for pirates that are not in a target location.
        for pirate in tempPirates:
            # Update the target location to be one that is still not occupied:
            target = min(tempLocs, key=lambda loc: self.game.distance(loc, pirate))  # Nearest location
            targetLocations[self.pirates.index(pirate)] = target
            tempLocs.remove(target)

        # Debug print-out
        # for pirate, pos in zip(self.pirates, targetLocations):
        #     selective_debug(self.game, "Pirate: {} Location: {} Target: {}".format(pirate.id, pirate.location, pos))

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
                        # selective_debug(self.game, "Pirate %d is blocking %d", blocker.id, pirate.id)
                        # If blocker is where he should be:
                        if blocker.location == targetLocations[blocker_index]:
                            # Switch target locations between blocker and active pirate:
                            targetLocations[self.pirates.index(pirate)] = targetLocations[blocker_index]
                            targetLocations[blocker_index] = pos
                            selective_debug(self.game, "Switched pirate %d with pirate %d", pirate.id, blocker.id)
                            reset = True

        # Move pirates to formation:
        in_formation = True  # Number of pirates in target place
        for pirate, pos in zip(self.pirates, targetLocations):
            # selective_debug(self.game, "pirate: {}, location: {}, pos: {} ".format(pirate.id, pirate.location, pos))
            movePirate(pirate, pos)
            in_formation &= pirate.location == pos  # if arrived already

        return in_formation

    def exportData(self):
        """
        export Tank class instance data to use in next turn

        :return: list with Tank class instance data
        """
        resumeData = [self.baseLoc, self.tankFormations, self.last_path]
        # resumeData.append([p.id for p in self.pirates])

        return resumeData

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
                for col in xrange(radius+1):
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


def selective_debug(game, string, *args):
    """
    print debug only on condition

    :param game: The game
    :param string: String to print (debug)
    :param args: arguments to format string
    """
    if game.get_turn() > 83:
        game.debug(string, *args)
    return