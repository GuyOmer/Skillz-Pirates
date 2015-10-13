from collections import deque, OrderedDict

dirs = {'n':(-1,0), 'e':(0,1), 's':(1,0), 'w':(0,-1)}
firststage = False
def do_turn(game):

    global firststage, Edge1
    starting_time = game.time_remaining()
    if game.get_turn() == 1:
        Edge = spawnEdges(game)
        game.debug(Edge)
        Edge1 = Edge[0]

    star = AStar()
    
    for pirate in game.my_pirates():
        target = Edge1
        firststage |= (pirate.location == (target) and False)
        if not firststage:
            target = target
        else:
            target = target

        dic = star.aStar(game,pirate.location,target)
        
        if dic == 0 or len(dic) == 0:
            pass
        else:
            #print dic
            #print "\n"
            #print "Going to: ", dic[0]
            movePirate(game,pirate,dic[0])
        break

    print "Turn took: " + str((starting_time - game.time_remaining())) + " ms."
    return

def movePirate(game,pirate, dest):
    if not pirate.is_lost:       #check if pirate is alive (should be done by caller)
            path = game.get_directions(pirate,dest) #get directions to destnation
            if not len(path) == 0:                  #if havent arrived yet
                game.set_sail(pirate, path[0])

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
    

def spawnEdges(game):
    
    Centres = findSafeZones(game)
    Edges = [] * len(Centres)
    for Centre in Centres:
        Edges.append(findEdge(game,Centre))

    return Edges

    

def TestGoodSpot(game,x,y):
    if game.is_passable((x,y)) and 0 < x < game.get_rows() and 0 < y < game.get_cols(): # Check if location is passable & valid
        return ((x,y))
    return False

def insurePathUnPassable(game,loc_a,loc_b):
    """
    This function will make sure the way between two locations
     is unpassable. It will assume safe zone is in a normal geometric shape
     no weird things like pants shaped zone (zone with holes, asymetrics, etc..)
     """

    path = game.get_directions(loc_a, loc_b)*game.distance(loc_a,loc_b)  # Get the path between two locations

    if len(path) == 0:
        return True                            # Shouldn't happen
    for index in xrange(len(path)):
        step = path[index%2*-1]                                 # Zig-Zag the route (will reduce false-negatives)
        path.remove(step)                                       # Remove the step from path list
        loc_a = loc_a[0]+dirs[step][0], loc_a[1]+dirs[step][1]  # Make the step
        if game.is_passable(loc_a):                             # Make sure we can't step there!
            return False
    return True

def findSafeZones(game):
    
    enemyPirates = game.all_enemy_pirates()
    pirates_broken_apart = []
    for i in xrange(len(enemyPirates)):                   # Index = pirates id, Value = ids of pirate that are broken apart
        pirates_broken_apart.append([])

    for i, pirate_a in enumerate(enemyPirates):           # Iterate all pirates with all pirates
        for pirate_b in enemyPirates:
            if pirate_a != pirate_b:        # Avoid checking yourself
                if not insurePathUnPassable(game, pirate_a.initial_loc, pirate_b.initial_loc):
                    #Path is passable!
                    pirates_broken_apart[i].append(pirate_b.id)
        #pirates_broken_apart[i].append(i)    # Append self to list
        pirates_broken_apart[i] = sorted(pirates_broken_apart[i])  # TODO: find a way not to use sort

    Groups = []
    tempGroup = []
    deducer = 0
    #j = 0
    # Pirates groups that are broken apart from the same other pirates group, are togther in a group
    for i, brokenList in enumerate(pirates_broken_apart):
        #brokenList.remove(j)
        for j in xrange(len(pirates_broken_apart)):
            if i != j:                  # Avoid checking yourself
                if brokenList == pirates_broken_apart[j-deducer]: 
                    tempGroup.append(j) # i and j are correlated with pirate's id
                    pirates_broken_apart.remove(pirates_broken_apart[j-deducer]) #This pirate was already fitted to
                    deducer += 1                                                 # a group, no need to check him again
                #pirates_broken_apart[j-deducer].append(i)                                                                 # might cause problems test it!
                                                                                 # TODO: make sure removing from list
                                                                                 # is working
                                                                                 # sloution is the deducer, fixes
                                                                                 # correlation between j xrange(len(...))
                                                                                 # and the real index - trust me it works
        tempGroup.append(i)     # Append self to group
        Groups.append(tempGroup) 
        tempGroup = []

    # We have all groups mapped out, lets find their center!
    Zones_Centre = []

    for group in Groups:
        row, col = 0, 0
        for id in group:
            loc = game.get_enemy_pirate(id).location  # Get pirate location
            row, col = row+loc[0], col+loc[1]         # unpack it
        row, col = row/len(group), col/len(group)     # Average it
        Zones_Centre.append((row, col))               # Add to list

    return Zones_Centre

def findEdge(game, centre, MAX_RADIUS=30):
    # Midpoint circle algorithm
    radius = 1
    x0, y0 = centre[0], centre[1]

    while radius < MAX_RADIUS:
        f = 1 - radius
        ddf_x = 1
        ddf_y = -2 * radius
        x = 0
        y = radius
        if TestGoodSpot(game, x0, y0 + radius): 
            return (x0, y0 + radius)
        if TestGoodSpot(game, x0, y0 - radius): 
            return (x0, y0 - radius)
        if TestGoodSpot(game, x0 + radius, y0): 
            return (x0 + radius, y0)
        if TestGoodSpot(game, x0 - radius, y0): 
            return (x0 - radius, y0)
     
        while x < y:
            if f >= 0: 
                y -= 1
                ddf_y += 2
                f += ddf_y
            x += 1
            ddf_x += 2
            f += ddf_x    
            if TestGoodSpot(game, x0 + x, y0 + y): 
                return (x0 + x, y0 + y)
            if TestGoodSpot(game, x0 - x, y0 + y): 
                return (x0 - x, y0 + y)
            if TestGoodSpot(game,  x0 + x, y0 - y): 
                return (x0 + x, y0 - y)
            if TestGoodSpot(game, x0 - x, y0 - y): 
                return (x0 - x, y0 - y)
            if TestGoodSpot(game, x0 + y, y0 + x): 
                return (x0 + y, y0 + x)
            if TestGoodSpot(game, x0 - y, y0 + x): 
                return (x0 - y, y0 + x)
            if TestGoodSpot(game,  x0 + y, y0 - x): 
                return (x0 + y, y0 - x)
            if TestGoodSpot(game, x0 - y, y0 - x):
                return (x0 - y, y0 - x)
        radius += 1

    return centre