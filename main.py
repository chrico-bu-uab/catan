import game

"""
need to add:
knight/robber stealing
dont build from split roads
and much more
"""

if __name__ == '__main__':
    VP = 10
    board = game.Board()
    player1 = game.Player("red", board)
    player2 = game.Player("blue", board)
    player3 = game.Player("green", board)
    for player in board.players:
        built = False
        while not built:
            built = player.build_settlement()
        built = player.build_road(built)
    board.players = board.players[::-1]
    for player in board.players:
        built = False
        while not built:
            built = player.build_settlement()
        built = player.build_road(built)  # pretend you can put two roads on one settlement
    board.players = board.players[::-1]
    i = 0
    while all([player.victory_points < VP for player in board.players]):
        if i % 100 == 0:
            board.plot()
        i += 1
        board.turn += 1
        for player in board.players:
            player.roll()
            player.do_actions()
            board.longest_road()
            board.largest_army()
            print(i, player.name, player.resources, player.victory_points, player.dev_cards)
            if player.victory_points >= VP:
                board.plot()
                break
            player.consolidate()
