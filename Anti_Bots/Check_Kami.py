import math
import sys

TankFormations = [[(0, 0)], [(0, 0), (0, 1)], [(0, 0), (0, 1), (1, 0), (1, 1)], [(0, 0), (0, 1), (1, 0), (1, 1)], [(0, 0), (0, 1), (0, 2), (-1, 1), (1, 1)], [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)], [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)], [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)], [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)], [(0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 2), (2, 1), (2, 2)], [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (-1, 1), (1, 1), (1, 2), (-1, 2), (1, 3), (2, 1), (2, 2)], [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (-1, 1), (1, 1), (1, 2), (-1, 2), (1, 3), (2, 1), (2, 2)], [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (-1, 1), (1, 1), (1, 2), (-1, 2), (1, 3), (2, 1), (2, 2)], [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2)], [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2)], [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 1), (1, 2), (-1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (3, 2)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (-1, 1), (1, 1), (1, 2), (-1, 2), (-1, 3), (1, 3), (1, 4), (2, 1), (2, 2), (2, 3), (3, 2)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (-1, 2), (1, 3), (1, 4), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2), (3, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (-1, 2), (1, 3), (1, 4), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2), (3, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (3, 1), (3, 2), (3, 3), (4, 2)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (3, 1), (3, 2), (3, 3), (4, 2)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (3, 1), (3, 2), (3, 3), (4, 2)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (3, 1), (3, 2), (3, 3), (4, 2)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (3, 1), (3, 2), (3, 3), (4, 2)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 1), (1, 2), (1, 3), (1, 4), (2, 1), (2, 2), (2, 3), (2, 4), (3, 1), (3, 2), (3, 3), (3, 4), (4, 2), (4, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 0), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (1, 5), (2, 1), (2, 2), (2, 3), (2, 4), (3, 1), (3, 2), (3, 3), (3, 4), (4, 2), (4, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 0), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (1, 5), (2, 1), (2, 2), (2, 3), (2, 4), (3, 1), (3, 2), (3, 3), (3, 4), (4, 2), (4, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 0), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (1, 5), (2, 1), (2, 2), (2, 3), (2, 4), (3, 1), (3, 2), (3, 3), (3, 4), (4, 2), (4, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 0), (-1, 1), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (-1, 4), (1, 5), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (3, 1), (3, 2), (3, 3), (3, 4), (4, 2), (4, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 0), (-1, 1), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (-1, 4), (1, 5), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (3, 1), (3, 2), (3, 3), (3, 4), (4, 2), (4, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 0), (-1, 1), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (-1, 4), (1, 5), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (3, 1), (3, 2), (3, 3), (3, 4), (4, 2), (4, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 0), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (1, 5), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (3, 1), (3, 2), (3, 3), (3, 4), (4, 1), (4, 2), (4, 3), (4, 4)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 0), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (1, 5), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (3, 1), (3, 2), (3, 3), (3, 4), (4, 1), (4, 2), (4, 3), (4, 4)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (4, 1), (4, 2), (4, 3), (4, 4), (5, 2), (5, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (4, 1), (4, 2), (4, 3), (4, 4), (5, 2), (5, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 1), (1, 2), (1, 3), (-1, 3), (1, 4), (1, 5), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (4, 2), (4, 3), (4, 4), (5, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 0), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (-1, 4), (1, 5), (1, 6), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (4, 2), (4, 3), (4, 4), (5, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 0), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (-1, 4), (1, 5), (1, 6), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (4, 2), (4, 3), (4, 4), (5, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 0), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (-1, 4), (1, 5), (1, 6), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (4, 2), (4, 3), (4, 4), (5, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 0), (-1, 1), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (-1, 4), (-1, 5), (1, 5), (1, 6), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (4, 2), (4, 3), (4, 4), (5, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 0), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (-1, 4), (1, 5), (1, 6), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (5, 2), (5, 3), (5, 4)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 0), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (-1, 4), (1, 5), (1, 6), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (5, 2), (5, 3), (5, 4)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 0), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (-1, 4), (1, 5), (1, 6), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (5, 2), (5, 3), (5, 4)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 0), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (-1, 4), (1, 5), (1, 6), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (5, 2), (5, 3), (5, 4)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (5, 2), (5, 3), (5, 4), (6, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (5, 2), (5, 3), (5, 4), (6, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (5, 2), (5, 3), (5, 4), (6, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (5, 2), (5, 3), (5, 4), (6, 3)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (-1, 1), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (-1, 4), (-1, 5), (1, 5), (1, 6), (-1, 6), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (4, 2), (4, 3), (4, 4), (4, 5), (5, 3), (5, 4)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (1, 0), (1, 1), (-1, 2), (1, 2), (1, 3), (-1, 3), (1, 4), (-1, 4), (-1, 5), (1, 5), (1, 6), (1, 7), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (4, 2), (4, 3), (4, 4), (4, 5), (5, 2), (5, 3), (5, 4), (5, 5)]]
tankData = None
movements = []


def do_turn(game):
    global tankData, TankFormations, radius

    if game.get_turn() == 1:
        radius = int(math.sqrt(game.get_attack_radius()))

    do_kamikaze(game)
    proccessMovements(game)


# TODO: add kamikaze param
def movePirate(pirate, dest, kamikaze=False):
    global movements
    movements.append((pirate, dest, kamikaze))


def proccessMovements(game):
    global movements
    # TODO: MIGHT ALREADY FIXED BY NEW movePirate: stop group if entering safe zone of enemy or getting out of map (so they won't die)

    pirates = []
    paths = []
    dests = []
    kamikaze = []

    # Un-pack movements
    for move in movements:
        pirate = move[0]
        dest = move[1]
        kamikaze.append(move[2])
        path = createPaths(game, pirate, dest)
        pirates.append(pirate)
        paths.append(path)
        dests.append((game.destination(pirate, path[0]), game.destination(pirate, path[1])))

    for i in xrange(len(pirates)):
        pirate, path, dest, is_kamikaze = pirates[i], paths[i], dests[i], kamikaze[i]
        pirate_index = pirates.index(pirate)

        # Make sure that path is safe to travel
        for j in xrange(len(path)):
            qdest = dest[j]
            checkPath(game, pirates, paths, dests, pirate, j, qdest, is_kamikaze)
            dests[pirate_index] = (game.destination(pirate, paths[pirate_index][0]),
                                   game.destination(pirate, paths[pirate_index][1]))

    for pirate, path, dest in zip(pirates, paths, dests):
        path1_good = path[0] is not None and path[0] != '-'
        path2_good = path[1] is not None and path[1] != '-'

        # Prepare path
        if not path1_good:
            paths[pirates.index(pirate)][0] = '-'

        if not path2_good:
            paths[pirates.index(pirate)][1] = '-'

        # Danger ahead, try escaping
        if not (path1_good or path2_good):
            strong_enemies = enemiesInRadius(game, pirate.location)

            # Escape from enemies
            if len(strong_enemies) > 0:
                directions = ['n', 'e', 's', 'w']
                possible_directions = ['n', 'e', 's', 'w']

                # Remove un-travelable directions
                for direction in possible_directions:
                    dest = game.destination(pirate, direction)
                    if not game.is_passable(dest) or game.is_occupied(dest):
                        possible_directions.remove(direction)

                # Plan escape route
                escape_direction = '-'
                no_escape = False
                for se in strong_enemies:
                    for direction in game.get_directions(pirate, se.location):
                        if direction in possible_directions:
                            possible_directions.remove(direction)

                            escape_direction_tmp = directions[directions.index(direction) - 2]
                            if escape_direction_tmp == escape_direction or escape_direction == '-':
                                escape_direction = escape_direction_tmp
                            elif len(possible_directions) > 0:
                                escape_direction = possible_directions[0]
                            else:
                                no_escape = True
                                break

                if no_escape:  # No escape from death
                    game.debug("Pirate {} has no where to escape, dies in peace.".format(pirate.id))
                    path[0] = '-'
                    path[1] = '-'

                else:  # Found a way to escape
                    game.debug("Pirate {} moving to the {} to escape from {}.".format(pirate.id,
                                                                                      escape_direction,
                                                                                      [p.id for p in strong_enemies]))
                    path[0] = escape_direction
            else:
                path[0] = '-'
                path[1] = '-'

        # Do the actual sailing
        if not pirate.is_lost:
            path1 = path[0]
            path2 = path[1]

            # Remove current pirate destenations from list
            if path1 is not None and path1 != '-':
                game.set_sail(pirate, path1)
            elif path2 is not None and path2 != '-':
                game.set_sail(pirate, path2)
            else:
                game.set_sail(pirate, '-')  # Stay in place
                game.debug("Stopped pirate #{} from moving to '{}'".format(pirate.id, path))

    # Clear movements
    movements[:] = []


def createPaths(game, pirate, dest):

    path1 = game.get_directions(pirate, dest)[(game.get_turn() % 2) * -1]  # Get alternating direction
    path1_dest = game.destination(pirate, path1)
    path1_good = game.is_passable(path1_dest) and len(path1) > 0

    if not path1_good:
        game.debug("Path {} not good for {}".format(path1, pirate))
        path1 = '-'

    path2 = game.get_directions(pirate, dest)[((game.get_turn() + 1) % 2) * -1]  # Get other alternating direction
    path2_dest = game.destination(pirate, path2)
    path2_good = game.is_passable(path2_dest) and len(path2) > 0 and path2 != path1

    if not path2_good:
        game.debug("Path {} not good for {}".format(path2, pirate))
        path2 = '-'

    return [path1, path2]


def checkPath(game, pirates, paths, dests, my_pirate, path_index, my_dest, is_kamikaze):
    global movements, radius

    list_index = pirates.index(my_pirate)
    enemies = enemiesInRadius(game, my_dest)

    if len(enemies) == 0:
        return

    if len(enemies) < len(pirates):
        in_small_radius = []
        in_large_radius = []
        for friendly_pirate, path, dest in zip(pirates, paths, dests):
            if friendly_pirate.id != my_pirate.id:
                for _dest in dest:
                    # If friendly pirate does not go on island
                    if game.destination(friendly_pirate, path[dest.index(_dest)]) not in\
                            [island.location for island in game.islands()]:
                        distance = game.distance(_dest, my_dest)

                        my_list = None
                        if distance < radius:
                            my_list = in_small_radius
                        elif distance == radius or distance == radius + 1:
                            my_list = in_large_radius

                        if my_list is not None:
                            # Delete paths that collide
                            for other_friendly in my_list:
                                other_dest = dests[pirates.index(other_friendly)]
                                other_dest1 = other_dest[0]
                                other_dest2 = other_dest[1]

                                if other_dest1 == _dest or other_dest2 == _dest:
                                    paths[paths.index(path)][dest.index(_dest)] = '-'
                                    break
                            else:
                                my_list.append(friendly_pirate)

        # TODO: consider if we want to deal with enemies on islands
        if len(in_large_radius) + len(in_small_radius) >= len(enemies)+is_kamikaze:  # if is_kamikaze add 1 (True = 1) else add 0.
            final_large_radius = []                         # go to groups that less or equal to our group
            for pirate in in_large_radius:
                if len(final_large_radius) + len(in_small_radius) < len(enemies):
                    pirate_index = pirates.index(pirate)
                    for dest in dests[pirate_index]:
                        if game.distance(dest, my_dest) <= radius:
                            final_large_radius.append([pirate_index, dests[pirate_index].index(dest)])
                            break
                else:
                    break

            if len(final_large_radius) + len(in_small_radius) >= len(enemies):
                for data in final_large_radius:
                    paths[data[0]][1 - data[1]] = '-'

                return  # Done checking path

    if is_kamikaze:
        for enemy in enemies:
            his_enemies = enemiesInRadius(game, enemy.location, owner=False)
            his_friends = enemiesInRadius(game, enemy.location, owner=True)
            
            for friend in his_friends:
                if friend.id == enemy.id:
                    his_friends.remove(friend)
                    
            if len(his_enemies) > len(his_friends):
                return  # kamikaze: enemy will die
    
    paths[list_index][path_index] = '-'


def enemiesInRadius(game, loc, owner=True):
    strong_enemies = []
    
    if owner:  # If I'm the owner
        enemies = game.enemy_pirates()
    else:
        enemies = game.my_pirates()  # TODO: change to use movemebts global for destenations
    
    # Find out who are the enemies
    for ep in enemies:
        el = ep.location
        
        for r in xrange(-1, 2):  # Row
            # If he might be able to attack me:
            if game.in_range((el[0] + r, el[1]), loc) and ep not in strong_enemies:
                strong_enemies.append(ep)

        for c in xrange(-1, 2):  # Col
            # If he might be able to attack me:
            if game.in_range((el[0], el[1] + c), loc) and ep not in strong_enemies:
                strong_enemies.append(ep)

    return strong_enemies

'''
def wouldWin(game, myPirate, enemyPirate, suicide=False):
    myPirates = []
    enemyPirates = []

    for pirate in game.my_pirates():
        if game.in_range(pirate.location, myPirate):
            if myPirate != pirate.location:  # My pirate is not included in the fight
                if not game.is_capturing(pirate):  # Capturing pirates do not count in fights
                    myPirates.append(pirate)

    for pirate in game.enemy_pirates():
        if game.in_range(pirate.location, enemyPirate) or pirate.location == enemyPirate:
            if not game.is_capturing(pirate):  # Capturing pirates do not count in fights
                enemyPirates.append(pirate)

    if len(myPirates) == 0 and len(enemyPirates) == 0:
        return True

    if not suicide:
        return len(myPirates) >= len(enemyPirates)
    else:
        return (1 + len(myPirates)) >= len(enemyPirates)
'''


class Tank():
    baseLoc = (0, 0)
    pirates = []
    game = None
    tankFormations = []

    def __init__(self, game, pirates, tankFormations, tankData, startingLocation=None):
        self.game = game
        self.pirates = pirates

        attackRadius = game.get_attack_radius()

        if len(self.pirates) < attackRadius:
            attackRadius = len(self.pirates)
            self.game.debug("Not enough pirates for optimal tank, reducing attack radius to: %d", attackRadius)

        # If doesn't have needed formation in memory for current attackRadius, calculate it:
        if attackRadius > len(tankFormations):
            self.game.debug("Doesn't have formation in memory for %d radius, calculating it.", attackRadius)
            self.tankFormations = self.calculateFormation(attackRadius)
        else:
            self.tankFormations = tankFormations[attackRadius]

        if tankData is not None:
            self.resumeFromData(tankData)
        else:
            if startingLocation is None:
                self.baseLoc = self.getBaseLoc()
            else:
                self.baseLoc = startingLocation

    def getBaseLoc(self):
        # islands = []
        # center = []
        #
        # # Centre of islands, more weight to valued islands:
        # for island in self.game.islands():
        #     for v in xrange(island.value):
        #         islands.append(island)
        #
        # center.append(sum([island.location[0] for island in islands]) / len(islands))
        # center.append(sum([island.location[1] for island in islands]) / len(islands))
        #
        # return tuple(center)

        # Centre of pirates
        return tuple((sum([pirate.location[0] for pirate in self.pirates]) / len(self.pirates),
                      sum([pirate.location[1] for pirate in self.pirates]) / len(self.pirates)))

    def moveTank(self, dest):
        if self.formTank():
            path = self.tankPath(dest)

            if path is not None and path != '-':
                for pirate in self.pirates:
                    dest = self.game.destination(pirate, path)
                    movePirate(pirate, dest)

                # Apply new base
                self.baseLoc = self.game.destination(self.baseLoc, path)
            else:
                self.game.debug("Stopped tank from moving.")

    def tankPath(self, dest):
        src = self.baseLoc
        directions = self.game.get_directions(src, dest)

        if len(directions) > 0:
            path1 = directions[(self.game.get_turn() % 2) * -1]  # Get alternating direction
            path1_dest = self.game.destination(src, path1)
            path1_good = self.game.is_passable(path1_dest) and len(path1) > 0

            if path1_good:
                return path1
            else:
                self.game.debug("Path {} not good for enemy on {}".format(path1, src))

                path2 = directions[((self.game.get_turn() + 1) % 2) * -1]  # Get alternating direction
                path2_dest = self.game.destination(src, path2)
                path2_good = self.game.is_passable(path2_dest) and len(path2) > 0

                if path2_good:
                    return path2
                else:
                    self.game.debug("Path {} not good for enemy on {}".format(path2, src))
                    return '-'
        return '-'

    def changeReference(self, locations):
        max_rows = self.game.get_rows()
        max_cols = self.game.get_cols()
        radius = int(math.sqrt(self.game.get_attack_radius()))

        if max_cols - self.baseLoc[1] < radius:
            self.baseLoc[1] = max_cols - radius - 1

        if max_rows - self.baseLoc[0] < radius:
            self.baseLoc[0] = max_rows - radius - 1
        elif self.baseLoc[0] < radius:
            self.baseLoc[0] = radius

        # Adjust location list to be around a new base location
        newList = []
        for loc in locations:
            newList.append((loc[0] + self.baseLoc[0], loc[1] + self.baseLoc[1]))
        return newList

    def formTank(self):
        if len(self.pirates) == 0:
            return False

        self.pirates = [pirate for pirate in self.pirates if not pirate.is_lost]

        targetLocations = [pos for pirate, pos in zip(self.pirates, self.tankFormations)]

        # Calculate position for each pirate
        targetLocations = self.changeReference(targetLocations)

        self.pirates = [pirate for pirate, pos in zip(self.pirates, targetLocations)]

        # Check available target locations
        tempPirates = []
        tempPirates += self.pirates
        tempLocs = []
        tempLocs += targetLocations

        for pirate in self.pirates:
            if pirate.location in targetLocations:
                tempPirates.remove(pirate)
                tempLocs.remove(pirate.location)
                targetLocations[self.pirates.index(pirate)] = pirate.location

        # Update target locations for pirates that are not in a target location.
        for pirate in tempPirates:
            # Update the target location to be one that is still not occupied:
            target = min(tempLocs, key=lambda loc: self.game.distance(loc, pirate))  # Nearest location
            targetLocations[self.pirates.index(pirate)] = target
            tempLocs.remove(target)

        # Debug print-out
        for pirate, pos in zip(self.pirates, targetLocations):
            # self.game.debug("Pirate: {} Location: {} Target: {}".format(pirate.id, pirate.location, pos))
            pass

        # Check if pirates are blocking each other and change their targets if so:
        reset = True
        while reset:
            reset = False
            for pirate, pos in zip(self.pirates, targetLocations):
                path = self.game.get_directions(pirate, pos)[(self.game.get_turn() % 2) * -1]
                if not len(path) == 0:
                    dest = self.game.destination(pirate.location, path)
                    blocker = self.pirateOnLocation(dest, [p for p in self.pirates if p != pirate])
                    # If some pirate is blocking the way:
                    if blocker is not None:
                        # self.game.debug("Pirate %d is blocking %d", blocker.id, pirate.id)
                        # If blocker is where he should be:
                        if blocker.location == targetLocations[self.pirates.index(blocker)]:
                            # Switch target locations between blocker and active pirate:
                            targetLocations[self.pirates.index(pirate)] = targetLocations[self.pirates.index(blocker)]
                            targetLocations[self.pirates.index(blocker)] = pos
                            self.game.debug("Switched pirate %d with pirate %d", pirate.id, blocker.id)
                            reset = True

        # Move pirates to formation:
        in_formation = True  # Number of pirates in target place
        for pirate, pos in zip(self.pirates, targetLocations):
            # self.game.debug("pirate: {}, location: {}, pos: {} ".format(pirate.id, pirate.location, pos))
            if pirate.location == pos:  # if arrived already
                # self.game.debug("Pirate %d is O.K!",pirate.id)
                in_formation &= True
            else:
                in_formation &= False
                movePirate(pirate, pos)
                # self.game.debug("Pirate %d moved solo",pirate.id)

        return in_formation

    @staticmethod
    def pirateOnLocation(location, pirates):
        for pirate in pirates:
            if pirate.location == location:
                return pirate
        return None

    def exportData(self):
        resumeData = [self.baseLoc]
        # resumeData.append([p.id for p in self.pirates])

        return resumeData

    def resumeFromData(self, resumeData):
        if resumeData is not None:
            try:
                self.baseLoc = resumeData.pop(0)
                # To overcome that pirates are passed by value
                # self.pirates = [self.game.get_my_pirate(id) for id in resumeData.pop(0)]

                # self.game.debug("Successful resumed data!")
            except:
                self.game.debug("Error while resuming data: {}".format(sys.exc_info()[0]))

    def calculateFormation(self, radius):
        s = int(math.sqrt(radius))

        starting_loc = (0, 0)
        goodloc = [starting_loc]

        possible_loc = starting_loc
        startedDown = False

        while True:
            count = 0
            while abs(possible_loc[1] - starting_loc[1]) <= s:
                for test_loc in goodloc:
                    if not self.game.in_range(possible_loc, test_loc):
                        break
                else:
                    count += 1
                    goodloc.append(possible_loc)

                possible_loc = (possible_loc[0], possible_loc[1] + 1)

            if count > 0 and not startedDown:
                possible_loc = (possible_loc[0] + 1, starting_loc[1])
            else:
                if not startedDown:
                    possible_loc = (starting_loc[0] - 1, starting_loc[1])
                else:
                    possible_loc = (possible_loc[0] - 1, starting_loc[1])

                if startedDown and count == 0:
                    break

                startedDown = True

        goodloc = list(set(goodloc))
        return sorted(goodloc, key=lambda loc: (abs(loc[0]), abs(loc[1])))


def do_kamikaze(game):
    """
    move pirates as kamikaze
    :param game:
    """
    # TODO do something with remaining pirates
    enemies = game.enemy_pirates()

    if (len(enemies) != 0):
        pirates = game.my_pirates()
        distances = []
        who_attacks_who = [None]*len(enemies)   # Key = enemy pirate, value = our pirate

        # create list of lists
        # of pirate distances from each enemy
        for pirate in pirates:
            pirate_distances = []
            for enemy in enemies:
                pirate_distances.append(game.distance(pirate, enemy))
            distances.append(pirate_distances)

        # guy's super magic average - calc avg of all distances from enemies
        avg = 0.0
        for lis in distances:
            avg += sum(lis)
        avg /= (len(enemies)*len(distances))
        avg = int(math.ceil(avg))

        for pirate_distances in distances:
            sorted_pirate_distances = pirate_distances[:]
            sorted_pirate_distances.sort(key=lambda num: abs(avg-num))
            index = 0
            pirate_to_attack = pirate_distances.index(sorted_pirate_distances[index])
            while index < len(enemies) and who_attacks_who[pirate_to_attack] is not None:
                pirate_to_attack = pirate_distances.index(sorted_pirate_distances[index])
                index += 1
            who_attacks_who[pirate_to_attack] = pirates[distances.index(pirate_distances)]

        for enemy_index, pirate in enumerate(who_attacks_who):
            movePirate(pirate, enemies[enemy_index].location, True)
        # for i in xrange(len(who_attacks_who)):
        #     movePirate(who_attacks_who[i],enemies)




