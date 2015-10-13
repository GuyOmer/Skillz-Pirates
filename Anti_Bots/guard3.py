def do_turn(game):
	
	if game.get_turn() > 110:
		if not game.all_my_pirates()[0].is_lost and not game.get_island(0).owner == game.ME:
			game.set_sail(game.all_my_pirates()[0],game.get_directions(\
				game.all_my_pirates()[0],game.islands()[0])[0])
		if not game.all_my_pirates()[1].is_lost and not game.get_island(0).owner == game.ME:
			game.set_sail(game.all_my_pirates()[1],game.get_directions(\
				game.all_my_pirates()[1],game.islands()[0])[0])
	if not game.all_my_pirates()[2].is_lost and not game.get_island(1).owner == game.ME:
		game.set_sail(game.all_my_pirates()[2],game.get_directions(\
			game.all_my_pirates()[2],game.islands()[1])[0])
	if not game.all_my_pirates()[3].is_lost and not game.get_island(1).owner == game.ME:
		game.set_sail(game.all_my_pirates()[3],game.get_directions(\
			game.all_my_pirates()[3],game.islands()[1])[0])
	if game.get_turn() > 80:
		if not game.all_my_pirates()[4].is_lost and not game.get_island(2).owner == game.ME:
			game.set_sail(game.all_my_pirates()[4],game.get_directions(\
				game.all_my_pirates()[4],game.islands()[2])[0])
	return