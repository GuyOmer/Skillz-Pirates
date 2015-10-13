conq = False

def do_turn(game):
	pirates = game.all_my_pirates()
	islands = game.islands()
	if not islands[0].owner == game.ME and pirates[0].is_lost == False == pirates[1].is_lost:
		movePirate(game,pirates[0],islands[0])
		movePirate(game,pirates[1],islands[0])
	else:
		movePirate(game,pirates[0],islands[1])
		movePirate(game,pirates[1],islands[1])
	if not pirates[2].is_lost:
		movePirate(game,pirates[2],islands[1])
	if not pirates[3].is_lost:
		movePirate(game,pirates[3],islands[1])

	global conq
	conq = islands[0].owner == game.ME == islands[0].owner
	return


def movePirate(game,pirate, dest):
	if not pirate.is_lost:       #check if pirate is alive (should be done by caller)
			path = game.get_directions(pirate,dest)[game.get_turn()%2*-1] #gets direction to destination
			if not len(path) == 0:                   #if havent arrived yet
				game.set_sail(pirate, path) 