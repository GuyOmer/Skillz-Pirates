def do_turn(game):
	loc = spawnEdges(game)
	

def spawnEdges(game):
    
	Centres = findSafeZones(game)
	Edges = [] * len(Centres)
	for Centre in Centres:
		Edges.append(findEdge(game,Centre))

	return Edges

    

def TestGoodSpot(game,x,y):
    if game.is_passable((x,y)) and 0 < x < game.get_rows() and 0 < y < game.get_cols(): # Check if location is
        game.debug("Got it: " + str(x) + ", " + str(y))                                 # passable & valid
        return ((x,y))
    return False

def insurePathUnPassable(game,loc_a,loc_b):
	"""
	This function will make sure the way between two locations
	 is unpassable. It will assume safe zone is in a normal geometric shape
	 no weird shit like pants shaped zone (zone with holes etc..)
	 """

	 path = game.get_directions(loc_a, loc_b)  # Get the path between two locations

	 if len(path) == 0:
	 	return True                            # Shouldn't happen

	 for index in len(path):
	 	step = path[index%2*-1]                # Zig-Zag the route (will reduce false-negatives)
	 	path.remove(step)                      # Remove the step from path list
	 	loc_a += step                          # Make the step
	 	if game.is_passable(loc_a):            # Make sure we can't step there!
	 		return False
	return True

def findSafeZones(game):
	
	enemyPirates = game.all_enemy_pirates()
	pirates_broken_apart = []*len(enemyPirates)           # Index = pirates id, Value = ids of pirate that are broken apart
	for i, pirate_a in enumerate(enemyPirates):           # Iterate all pirates with all pirates
		for pirate_b in enemyPirates:
			if pirate_a != pirate_b:        # Avoid checking yourself
				if not insurePathUnPassable(game, pirate_a.location, pirate_b.location):
					#Path is passable!
					pirates_broken_apart[i].append(pirate_b.id)

	Groups = []
	
	# Pirates groups that are broken apart from the same other pirates group, are togther in a group
	for i, brokenList in enumerate(pirates_broken_apart):
		tempGroup = []
		for j in xrange(len(pirates_broken_apart)):
			if i != j:					# Avoid checking yourself
				if brokenList == pirates_broken_apart[j]:
					tempGroup.append(j) # i and j are correlated with pirate's id
					pirates_broken_apart.remove(pirates_broken_apart[j]) #This pirate was already fitted to
																		 # a group, no need to check him again
																		 # might cause problems test it!
																		 # TODO: make sure removing from list
																		 # is working
		Groups.append(tempGroup)

	# We have all groups mapped out, lets find their center!
	Zones_Centre = []
	for group in Groups:
		row, col = 0, 0
		for id in group:
			loc = game.get_enemy_pirate(id).location  # Get pirate location
			row, col += loc[0], loc[1]                # unpack it
		row, col /= len(group), len(group)            # Average it
		Zones_Centre.append((row, col))               # Add to list

	return Zones_Centre

def findEdge(game, centre, MAX_RADIUS=30):
	# Midpoint circle algorithm
	radius = 1
	x0, y0 = centre[0], centre[1]

    game.debug(str(x0) + ", " + str(y0))

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