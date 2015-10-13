Ways = ['n','e','s','w'] #not used

def do_turn(game):
	if len(game.my_pirates())>0 and game.islands()[0].team_capturing == game.ENEMY\
	or game.islands()[0].owner == game.ENEMY or game.islands()[0] in game.my_islands()\
	or game.get_turn() >50 or True:
		form = formTank(game, game.my_pirates(),'s')
		game.debug(form)
		if form >= len(game.my_pirates()):
			game.debug("We have a Tank!")
			moveTank(game,game.my_pirates(),(16,27))
	elif game.get_turn() <8:
		game.debug("Uni-Movement Mode")
		moveTank(game,game.my_pirates(),(16,27))
	else:
		pass


	for p in game.my_pirates():
		game.debug("Pirate %d: %s", p.id, p.location)

	return

def formTank(game,pirates,orientation='n'):
	if len(pirates) == 0:
		return 0
	#base Cords, find our pirates concentration, for shorter travelling distances
	# ^^ will use same algorithm as enemy pirates group
	#meanwhile use first pirate as base cords

	game.debug("Tank Mode!")

	base_loc = pirates[0].location
	tank_pos = [None] * 5 	  #tank formation is suitted for 5 pirates
							  #additional pirates will follow the tank leader (not implemented yet)

	  #different tanks orientation
	if orientation == 'n':   #North
		tank_pos[0] = base_loc
		tank_pos[1] = (base_loc[0]-1, base_loc[1])
		tank_pos[2] = (base_loc[0]-2, base_loc[1]+1)
		tank_pos[3] = (base_loc[0]-1, base_loc[1]+2)
		tank_pos[4] = (base_loc[0], base_loc[1]+2)
	elif orientation == 'e': #East
		tank_pos[0] = base_loc
		tank_pos[1] = (base_loc[0], base_loc[1]+1)
		tank_pos[2] = (base_loc[0]-1, base_loc[1]+2)
		tank_pos[3] = (base_loc[0]-2, base_loc[1])
		tank_pos[4] = (base_loc[0]-2, base_loc[1]+1)
	elif orientation == 's': #South
		tank_pos[0] = base_loc
		tank_pos[1] = (base_loc[0]-1, base_loc[1])
		tank_pos[2] = (base_loc[0]+1, base_loc[1]+1)
		tank_pos[3] = (base_loc[0]-1, base_loc[1]+2)
		tank_pos[4] = (base_loc[0], base_loc[1]+2)
	elif orientation == 'w': #West
		tank_pos[0] = base_loc
		tank_pos[1] = (base_loc[0], base_loc[1]+1)
		tank_pos[2] = (base_loc[0]-1, base_loc[1]-1)
		tank_pos[3] = (base_loc[0]-2, base_loc[1])
		tank_pos[4] = (base_loc[0]-2, base_loc[1]+1)

	for pirate, pos in zip(pirates,tank_pos):  #not sure if best implementation
		path = game.get_directions(pirate,pos)[game.get_turn()%2*-1]
		if not len(path) == 0:                
			blocker = whoIsThere(game,game.destination(pirate.location,path))
			if not blocker == None and blocker.location == tank_pos[blocker.id]:
				tank_pos[pirate.id], tank_pos[blocker.id] = tank_pos[blocker.id], tank_pos[pirate.id]

	in_formation = 0
	for pirate, pos in zip(pirates,tank_pos):  #not sure if best implementation
		if pirate.location == pos:  #if arrived already
			in_formation += 1
			game.debug("Pirate %d is O.K!",pirate.id)
		else:
			movePirate(game, pirate, pos)
			game.debug("Pirate %d moved solo",pirate.id)

	return in_formation
		
def movePirate(game,pirate, dest):
	if not pirate.is_lost:       #check if pirate is alive (should be done by caller)
			path = game.get_directions(pirate,dest)[game.get_turn()%2*-1] #gets direction to destination
			if not len(path) == 0:                   #if havent arrived yet
				game.set_sail(pirate, path) 

def moveTank(game, pirates, dest):
	path = game.get_directions(pirates[0], dest)[game.get_turn()%2*-1]
	if len(path) == 0:
		return

	way_is_clear = True  #make sure all pirates can move in desierd direction,
	for pirate in pirates: #otherwise take a different path
		way_is_clear &= game.is_passable(game.destination(pirate,path))
	if not way_is_clear:
		path = game.get_directions(pirates[0], dest)[(game.get_turn()+1)%2*-1]

	for pirate in pirates:
		if not pirate.is_lost:       #check if pirate is alive (should be done by caller)
			game.set_sail(pirate, path)

def whoIsThere(game,location):
	for pirate in game.my_pirates():
		if pirate.location == location:
			return pirate

	#for pirate in game.enemy_pirates():  #For enemy pirates
	#	if pirate.location == location:
	#		return pirate
	return None