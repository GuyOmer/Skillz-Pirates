def movePirate(game,pirate, dest):
	if not pirate.is_lost:       #check if pirate is alive (should be done by caller)
			path = game.get_directions(pirate,dest) #get directions to destnation
			if not len(path) == 0:                  #if havent arrived yet
				game.set_sail(pirate, path[game.get_turn()%2*-1])  #takes direction from the start of the list
																   #and next time then from the end of it