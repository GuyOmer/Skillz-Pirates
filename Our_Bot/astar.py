import heapq, collections

dirs = {'n':(-1,0), 'e':(0,1), 's':(1,0), 'w':(0,-1)}

def do_turn(game):
    dic = a_star_search(game,game.my_pirates()[0].location,game.enemy_pirates()[0].location)

    print dic.values()
    movePirate(game,game.my_pirates()[0],dic.popitem(False)[0])
    return



def heuristic(a, b):
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)

def a_star_search(game, start, goal):
    frontier = PriorityQueue()
    frontier.put(start, 0)
    came_from = collections.OrderedDict()
    cost_so_far = collections.OrderedDict()
    came_from[start] = None
    cost_so_far[start] = 0
    
    while not frontier.empty():
        current = frontier.get()
        
        if current == goal:
            break
        
        for next in getNeighbors(game, current):
            new_cost = cost_so_far[current] + 1 #graph.cost(current, next)
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + heuristic(goal, next)
                frontier.put(next, priority)
                came_from[next] = current
    
    #game.debug("Cost: %d",cost_so_far)
    return came_from

def getNeighbors(game, loc):
    Neighbors = []
    for dir in dirs.values():
        tmp = (loc[0]+dir[0], loc[1]+dir[1])
        if game.is_passable(tmp):
            Neighbors.append(tmp)

    return Neighbors


def movePirate(game,pirate, dest):
    if not pirate.is_lost:       #check if pirate is alive (should be done by caller)
            path = game.get_directions(pirate,dest) #get directions to destnation
            if not len(path) == 0:                  #if havent arrived yet
                game.set_sail(pirate, path[0])

class PriorityQueue:
    def __init__(self):
        self.elements = []
    
    def empty(self):
        return len(self.elements) == 0
    
    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))
    
    def get(self):
        return heapq.heappop(self.elements)[1]