from collections import deque, OrderedDict

dirs = {'n':(-1,0), 'e':(0,1), 's':(1,0), 'w':(0,-1)}
firststage = False
ttl = 10
def do_turn(game):

    starting_time = game.time_remaining()
    print spawnEdge(game)

    star = AStar()
    global firststage, ttl
    game.debug(firststage)
    for pirate in game.my_pirates():
        target = (25,27)
        firststage |= pirate.location == (25,27)
        if not firststage:
            ttl-=1
            if ttl < 0:
                target = (16,27)
        else:
            target = (25,27)

        dic = star.aStar(game,pirate.location,target)
        
        if dic == 0 or len(dic) == 0:
            pass
        else:
            #print dic
            #print "\n"
            #print "Going to: ", dic[0]
            movePirate(game,pirate,dic[0])


    print "Turn took: " + str((starting_time - game.time_remaining())) + " ms."
    return

def movePirate(game,pirate, dest):
    if not pirate.is_lost:       #check if pirate is alive (should be done by caller)
            path = game.get_directions(pirate,dest) #get directions to destnation
            if not len(path) == 0:                  #if havent arrived yet
                game.set_sail(pirate, path[0])

def spawnEdge(game):
    center = []
    spawns = []
    # Centre of enemy spawns:
    for enemy in game.all_enemy_pirates():
        spawns.append(enemy.initial_loc)
    x0 = sum([init[0] for init in spawns]) / len(spawns)
    y0 = sum([init[1] for init in spawns]) / len(spawns)
    radius = 1

    game.debug(str(x0) + ", " + str(y0))

    while radius < 30:
        f = 1 - radius
        ddf_x = 1
        ddf_y = -2 * radius
        x = 0
        y = radius
        if TestGoodSpot(game, x0, y0 + radius): 
            return
        if TestGoodSpot(game, x0, y0 - radius): 
            return
        if TestGoodSpot(game, x0 + radius, y0): 
            return
        if TestGoodSpot(game, x0 - radius, y0): 
            return
     
        while x < y:
            if f >= 0: 
                y -= 1
                ddf_y += 2
                f += ddf_y
            x += 1
            ddf_x += 2
            f += ddf_x    
            if TestGoodSpot(game, x0 + x, y0 + y): 
                return
            if TestGoodSpot(game, x0 - x, y0 + y): 
                return
            if TestGoodSpot(game, x0 + x, y0 - y): 
                return
            if TestGoodSpot(game, x0 - x, y0 - y): 
                return
            if TestGoodSpot(game, x0 + y, y0 + x): 
                return
            if TestGoodSpot(game, x0 - y, y0 + x): 
                return
            if TestGoodSpot(game, x0 + y, y0 - x): 
                return
            if TestGoodSpot(game, x0 - y, y0 - x):
                return
        radius += 1

def TestGoodSpot(game,x,y):
    if game.is_passable((x,y)) and 0 < x < game.get_rows() and 0 < y < game.get_cols():
        game.debug("Got it: " + str(x) + ", " + str(y))
        return ((x,y))
    return False

class AStar:
    def distBetween(self,current,neighbor):
        return 1

    def heuristicEstimate(self,start,goal):
        (x1, y1) = start
        (x2, y2) = goal
        return abs(x1 - x2) + abs(y1 - y2)

    def neighborNodes(self,game,loc):
        Neighbors = []
        for dir in dirs.values():
            tmp = (loc[0]+dir[0], loc[1]+dir[1])
            if game.is_passable(tmp):
                Neighbors.append(tmp)

        return Neighbors
    
    def reconstructPath(self,cameFrom,goal):
        path = deque()
        node = goal
        path.appendleft(node)
        while node in cameFrom:
            node = cameFrom[node]
            path.appendleft(node)
        path.popleft()
        return path
    
    def getLowest(self,openSet,fScore):
        lowest = float("inf")
        lowestNode = None
        for node in openSet:
            if fScore[node] < lowest:
                lowest = fScore[node]
                lowestNode = node
        return lowestNode

    def aStar(self,game,start,goal):
        cameFrom = OrderedDict()
        openSet = set([start])
        closedSet = set()
        gScore = {}
        fScore = {}
        gScore[start] = 0
        fScore[start] = gScore[start] + self.heuristicEstimate(start,goal)
        while len(openSet) != 0:
            current = self.getLowest(openSet,fScore)
            if current == goal:
                return self.reconstructPath(cameFrom,goal)
            openSet.remove(current)
            closedSet.add(current)
            for neighbor in self.neighborNodes(game,current):
                tentative_gScore = gScore[current] + self.distBetween(current,neighbor)
                if neighbor in closedSet and tentative_gScore >= gScore[neighbor]:
                    continue
                if neighbor not in closedSet or tentative_gScore < gScore[neighbor]:
                    cameFrom[neighbor] = current
                    gScore[neighbor] = tentative_gScore
                    fScore[neighbor] = gScore[neighbor] + self.heuristicEstimate(neighbor,goal)
                    if neighbor not in openSet:
                        openSet.add(neighbor)
        return 0