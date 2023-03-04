from game import Agent, Board


def run_simulation(vp=10):
    board = Board()
    Agent("red", board)
    Agent("blue", board)
    Agent("green", board)
    for agent in board.agents:
        agent.build_settlement()
        agent.build_road()
    board.agents = board.agents[::-1]
    board.turn += 1
    for agent in board.agents:
        agent.build_settlement()
        agent.build_road()  # pretend you can put two roads on one settlement
    board.agents = board.agents[::-1]
    i = 0
    while True:
        if i % 100 == 0:
            board.plot()
        i += 1
        board.turn += 1
        for agent in board.agents:
            dice = agent.roll()
            print(i, dice, agent.name, agent.resources, agent.victory_points, agent.dev_cards)
            agent.do_actions()
            board.longest_road()
            board.largest_army()
            if agent.victory_points >= vp:
                board.plot()
                break
            agent.consolidate()


if __name__ == "__main__":
    run_simulation()
