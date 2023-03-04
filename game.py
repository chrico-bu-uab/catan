from math import exp
from random import random, randint, shuffle, choice

import matplotlib.pyplot as plt
from numpy import argmax, mean
from sympy import cos, pi, sin

UNOWNED = "lightgray"


def flatten_counts(counter):
    lst = []
    for k, v in counter.items():
        lst.extend([k] * v)
    return lst


class Tile:  # there are 19 tiles on the board
    def __init__(self, a, b, terrain_type, die):
        self.a = a
        self.b = b
        self.terrain_type = terrain_type
        self.die = die
        self.probability = 0 if self.die == 7 else (6 - abs(self.die - 7)) / 36
        self.neighbors = {}
        self.spots = {}
        self.paths = {}
        self.robber = False

    def __eq__(self, other):
        return self.a == other.a and self.b == other.b

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if self.a == other.a:
            return self.b < other.b
        return self.a < other.a

    def __gt__(self, other):
        if self.a == other.a:
            return self.b > other.b
        return self.a > other.a

    def __hash__(self):
        return hash((self.a, self.b))

    def __str__(self):
        return str((self.a, self.b, self.terrain_type, self.die))

    def __repr__(self):
        return str(self)


class Spot:  # there are 54 spots on the board
    def __init__(self, *tiles: Tile):
        self.a = self.b = None
        self.tiles = tiles
        self.neighbors = {}
        self.paths = {}
        self.build_level = 0
        self.owner = UNOWNED

    def __eq__(self, other):
        return self.a == other.a and self.b == other.b

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.tiles < other.tiles

    def __gt__(self, other):
        return self.tiles > other.tiles

    def __hash__(self):
        return hash((self.a, self.b))

    def __str__(self):
        return str((self.a, self.b))

    def __repr__(self):
        return str(self)


class Path:  # there are 72 paths on the board
    def __init__(self, key, harbor):
        self.a, self.b = key
        self.spots = {}
        self.neighbors = {}
        self.harbor = harbor
        self.build_level = 0
        self.owner = UNOWNED
        self.visited = False

    def __eq__(self, other):
        return self.a == other.a and self.b == other.b

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.a, self.b))

    def __str__(self):
        return str((self.a, self.b))

    def __repr__(self):
        return str(self)


class Board:
    def __init__(self):
        terrain_types = ["ore", "brick"] * 3 + ["wheat", "lumber", "sheep"] * 4
        dice = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]
        shuffle(terrain_types)
        pairs = list(zip(terrain_types, dice))
        pairs.append(("desert", 7))
        shuffle(pairs)
        terrain_types, dice = zip(*pairs)

        self.tiles = {(0, 0): Tile(0, 0, terrain_types[0], dice[0])}
        h = 1
        x = pi / 3

        def rgfdgfds(pair):
            increment = False
            if pair not in self.tiles:
                if pair[0] ** 2 + pair[1] ** 2 <= 4:
                    self.tiles[pair] = Tile(*pair, terrain_types[h], dice[h])
                    increment = True
                else:
                    self.tiles[pair] = Tile(*pair, "water", 7)
            return increment

        for i in range(6):
            pair = cos(x * i), sin(x * i)
            h += rgfdgfds(pair)
            for j in range(6):
                pair2 = pair[0] + cos(x * j), pair[1] + sin(x * j)
                h += rgfdgfds(pair2)
                for k in range(6):
                    pair3 = pair2[0] + cos(x * k), pair2[1] + sin(x * k)
                    h += rgfdgfds(pair3)
        assert len(self.tiles) == 37, len(self.tiles)

        self.tiles = list(self.tiles.values())
        print(self.tiles)
        desert_tile = [tile for tile in self.tiles if tile.terrain_type == "desert"][0]
        desert_tile.robber = True
        self.robber = desert_tile

        for tile in self.tiles:
            for tile2 in self.tiles:
                key = (tile2.a, tile2.b)
                if (tile.a - tile2.a) ** 2 + (tile.b - tile2.b) ** 2 == 1:
                    if key not in tile.neighbors:
                        tile.neighbors[key] = tile2

        ttl_neighbors = 0
        for tile in self.tiles:
            ttl_neighbors += len(tile.neighbors)
        assert ttl_neighbors == 180, ttl_neighbors

        self.tiles = [tile for tile in self.tiles if tile.terrain_type != "water"]

        for tile in self.tiles:
            assert len(tile.neighbors) == 6, len(tile.neighbors)

        self.spots = {}
        for tile in self.tiles:
            for tile2 in tile.neighbors.values():
                assert tile in tile2.neighbors.values(), (tile, tile2)
                for tile3 in tile2.neighbors.values():
                    assert tile2 in tile3.neighbors.values(), (tile2, tile3)
                    if tile3 in tile.neighbors.values():
                        key = mean([tile.a for tile in (tile, tile2, tile3)]), \
                            mean([tile.b for tile in (tile, tile2, tile3)])
                        if key not in self.spots:
                            self.spots[key] = Spot(tile, tile2, tile3)
                        tile.spots[key] = self.spots[key]
            assert len(tile.spots) == 6, len(tile.spots)
        assert len(self.spots) == 54, len(self.spots)

        harbors = list(set(terrain_types)) + ["3:1"] * 4 + [None] * 21
        harbors.remove("desert")
        shuffle(harbors)
        self.paths = {}
        items = list(self.spots.items())
        for name, spot in list(items):
            if not spot.a:
                spot.a, spot.b = name
            for name2, spot2 in items:
                if not spot2.a:
                    spot2.a, spot2.b = name2
                if len(set(spot.tiles).union(spot2.tiles)) == 4:
                    if any(tile.terrain_type == "water" for tile in spot.tiles) and \
                            any(tile.terrain_type == "water" for tile in spot2.tiles):
                        harbor = harbors.pop()
                    else:
                        harbor = "N/A"
                    key = mean([spot.a for spot in (spot, spot2)]), \
                        mean([spot.b for spot in (spot, spot2)])
                    if key not in self.paths:
                        self.paths[key] = Path(key, harbor)
                    path = self.paths[key]
                    path.spots = (spot.a, spot.b), (spot2.a, spot2.b)
                    spot.paths[key] = path
                    spot2.paths[key] = path
            items.pop(0)
        plt.scatter([x.a for x in self.paths.values()], [x.b for x in self.paths.values()])
        assert len(self.paths) == 72, len(self.paths)

        for spot in self.spots.values():
            assert len(spot.paths) < 4, len(spot.paths)
            assert len(spot.paths) > 1, len(spot.paths)
            for key, spot2 in self.spots.items():
                if len(set(spot.paths).union(spot2.paths)) < len(spot.paths) + len(spot2.paths) and spot != spot2:
                    spot.neighbors[key] = spot2

        for spot in self.spots.values():
            assert len(spot.neighbors) < 4, len(spot.neighbors)
            assert len(spot.neighbors) > 1, len(spot.neighbors)

        for key, path in self.paths.items():
            assert len(path.spots) == 2, len(path.spots)
            spot, spot2 = path.spots
            spot, spot2 = self.spots[spot], self.spots[spot2]
            for tile in set(spot.tiles).intersection(spot2.tiles):
                tile.paths[key] = path
            for key2, path2 in self.paths.items():
                if len(set(path.spots).union(path2.spots)) < len(path.spots) + len(path2.spots) and path != path2:
                    path.neighbors[key2] = path2
            path.a = (spot.a + spot2.a) / 2
            path.b = (spot.b + spot2.b) / 2

        for tile in self.tiles:
            assert len(tile.paths) == 6, len(tile.paths)

        for path in self.paths.values():
            assert len(path.neighbors) < 5, len(path.neighbors)
            assert len(path.neighbors) > 1, len(path.neighbors)

        last_high_dice = {}
        restricted_tiles = []
        for tile in self.tiles:
            # fix dice so that 6's and 8's are not next to each other
            if tile.die in [6, 8]:
                restricted_tiles.append(tile)
                for tile2 in tile.neighbors.values():
                    restricted_tiles.append(tile2)
                    if tile2.die in [6, 8]:
                        last_high_dice[tile2] = tile2.die
                        tile2.die = None

        shuffle(self.tiles)
        bad_tiles = list(last_high_dice)
        for tile in self.tiles:
            if last_high_dice and tile not in restricted_tiles:
                low_dice = tile.die
                bad_tile = bad_tiles.pop()
                tile.die = last_high_dice.pop(bad_tile)
                bad_tile.die = low_dice

        self.paths = list(self.paths.items())
        while True:
            shuffle(self.paths)
            last_harbors = []
            restricted_paths = []
            for _, path in self.paths:
                # fix harbors so that they are not next to each other
                if path.harbor != "N/A":
                    if path.harbor is not None and path.harbor != "N/A":
                        restricted_paths.append(path)
                        for path2 in path.neighbors.values():
                            restricted_paths.append(path2)
                            if path2.harbor is not None and path2.harbor != "N/A":
                                last_harbors.append(path2.harbor)
                                path2.harbor = None
            if not last_harbors:
                break
            shuffle(self.paths)
            for _, path in self.paths:
                if last_harbors and (path not in restricted_paths) and (path.harbor != "N/A"):
                    path.harbor = last_harbors.pop()
        self.paths = dict(self.paths)

        self.dev_cards = {"knight": 14, "victory_point": 5, "road_building": 2, "year_of_plenty": 2, "monopoly": 2}

        self.agents = []

        self.turn = -1

        self.agent_with_longest_road = None
        self.agent_with_largest_army = None

        self.plot()

    def add_agent(self, agent):
        self.agents.append(agent)

    def longest_road(self):
        longest_roads = [agent.longest_road() for agent in self.agents]
        longest_road = max(longest_roads)
        if longest_road >= 5:
            if self.agent_with_longest_road is None:
                self.agent_with_longest_road = (self.agents[argmax(longest_roads)], longest_road)
                self.agent_with_longest_road[0].victory_points += 2
            elif self.agent_with_longest_road[1] < longest_road:
                self.agent_with_longest_road[0].victory_points -= 2
                self.agent_with_longest_road = (self.agents[argmax(longest_roads)], longest_road)
                self.agent_with_longest_road[0].victory_points += 2
        return longest_road

    def largest_army(self):
        largest_armies = [agent.largest_army() for agent in self.agents]
        largest_army = max(largest_armies)
        if largest_army >= 3:
            if self.agent_with_largest_army is None:
                self.agent_with_largest_army = (self.agents[argmax(largest_armies)], largest_army)
                self.agent_with_largest_army[0].victory_points += 2
            elif self.agent_with_largest_army[1] < largest_army:
                self.agent_with_largest_army[0].victory_points -= 2
                self.agent_with_largest_army = (self.agents[argmax(largest_armies)], largest_army)
                self.agent_with_largest_army[0].victory_points += 2
        return largest_army

    def plot(self):
        plt.figure(figsize=(5, 5))
        harbor_colors = {"ore": "lavender", "brick": "firebrick", "wheat": "lemonchiffon", "lumber": "olive",
                         "sheep": "lightgreen", "3:1": "deepskyblue", None: UNOWNED, "desert": "orange", "N/A": UNOWNED}
        for tile in sorted(self.tiles):
            plt.scatter(tile.a, tile.b, color=harbor_colors[tile.terrain_type], s=3500, marker="h")
            plt.text(tile.a, tile.b, tile.die, ha="center", va="center", fontsize=10)
            for spot in tile.spots.values():
                plt.scatter(spot.a, spot.b, color="black" if spot.build_level == 0 else spot.owner,
                            s=75 * spot.build_level + 25,
                            marker="o" if spot.build_level == 1 else ("D" if spot.build_level == 2 else "*"))
                for path in spot.paths.values():
                    plt.plot([spot.a, path.a], [spot.b, path.b], color=path.owner)
                for path in spot.paths.values():
                    plt.scatter(path.a, path.b, color=harbor_colors[path.harbor], marker="H",
                                s=50 if (path.harbor is not None) and (path.harbor != "N/A") else 0)
                    plt.text(path.a, path.b, path.harbor, ha="left", va="bottom",
                             fontsize=10 if (path.harbor is not None) and (path.harbor != "N/A") else 0)
            if tile.robber:
                plt.text(tile.a, tile.b, "*", ha="left", va="bottom", fontsize=10)
        plt.show()


class Agent:
    def __init__(self, name, board: Board):
        self.name = name
        while name in [agent.name for agent in board.agents]:
            self.name = input(f'"{name}" already taken! Please choose a different name: ')
        self.board = board
        self.resources = {"ore": 0, "brick": 0, "wheat": 0, "lumber": 0, "sheep": 0}
        self.roads = 15
        self.settlements = 5
        self.cities = 4
        self.dev_cards = {"knight": 0, "victory_point": 0, "monopoly": 0, "road_building": 0, "year_of_plenty": 0}
        self.victory_points = 0
        self.board.add_agent(self)

    def available_paths(self):
        if not (self.roads and ((self.resources["brick"] and self.resources["lumber"]) or self.board.turn <= 0)):
            return []
        paths = [path for name, path in self.board.paths.items() if
                 (any([self.board.paths[path2].owner == self.name for path2 in path.neighbors]) or
                  any([self.board.spots[spot].owner == self.name for spot in path.spots]))
                 and path.owner == UNOWNED]
        return paths

    def available_spots_for_settlement(self):
        if not (self.settlements and ((self.resources["brick"] and self.resources["lumber"] and
                                       self.resources["wheat"] and self.resources["sheep"]) or self.board.turn <= 0)):
            return []
        spots = []
        for _, spot in self.board.spots.items():
            if spot.build_level == 0 and \
                    (any([path.owner == self.name for path in spot.paths.values()]) or self.board.turn <= 0) and \
                    not any([i.build_level > 0 for i in spot.neighbors.values()]):
                spots.append(spot)
        return spots

    def choose_tile_to_occupy(self):
        tiles = [tile for tile in self.board.tiles
                 if all(spot.owner != self.name for spot in tile.spots.values()) and not tile.robber]
        shuffle(tiles)
        return tiles[argmax([tile.probability for tile in tiles])]

    def choose_resource(self, exclude=None):
        return choice([resource for resource in self.resources if self.resources[resource] == min(
            [v for k, v in self.resources.items() if k != exclude]) and resource != exclude])

    def drop_resources(self, n):
        resources = flatten_counts(self.resources)
        for _ in range(n):
            resources.remove(choice(resources))

    def choose_path_to_build(self):
        paths = self.available_paths()
        if paths:
            optimal_paths = [path for path in paths if
                             all(spot.owner in UNOWNED for spot in [self.board.spots[name] for name in path.spots]) and
                             any(all(self.board.spots[name].owner == UNOWNED for name in path2.spots) for path2 in
                                 path.neighbors.values())]
            if optimal_paths:
                return choice(optimal_paths)
            return choice(paths)
        return None

    def choose_spot_to_build(self):
        spots = self.available_spots_for_settlement()
        if spots:
            shuffle(spots)
            return spots[
                argmax([sum(tile.probability for tile in spot.tiles) for spot in spots])]
        return None

    def choose_spot_to_upgrade(self):
        spots = [spot for spot in self.board.spots.values() if spot.build_level == 1
                 and spot.owner == self.name and (
                         self.resources["wheat"] > 1 and self.resources["ore"] > 2)
                 and self.cities > 0 and spot.build_level == 1]
        if spots:
            return choice(spots)
        return None

    def choose_dev_card(self):
        cards = [card for card in self.dev_cards if self.dev_cards[card] > 0 and card != "victory_point"]
        if cards:
            return choice(cards)
        return None

    def choose_person_to_steal_from(self, tile):
        people = [agent for agent in self.board.agents if
                  (agent.name != self.name) and sum(agent.resources.values()) and (
                          agent.name in [spot.owner for spot in tile.spots.values()])]
        try:
            return choice(people)
        except IndexError:
            return None

    def steal(self, tile):
        person = self.choose_person_to_steal_from(tile)
        if person:
            resource = choice(flatten_counts(person.resources))
            person.resources[resource] -= 1
            self.resources[resource] += 1
            print(f"{self.name} stole a {resource} from {person.name}!")
            return True
        else:
            print("You cannot steal from anyone!")
            return False

    def move_robber(self):  # stealing disabled for the sake of simplicity
        tile = self.choose_tile_to_occupy()
        robber_tile = self.board.robber
        robber_tile.robber = False
        if tile != robber_tile:
            self.board.robber = tile
            tile.robber = True
            self.steal(tile)
            return True
        else:
            print("You must move the robber!")
            return False

    def roll(self):
        dice = [randint(1, 6), randint(1, 6)]
        # print(f"{self.name} rolled a {dice[0]} and a {dice[1]}!")
        if sum(dice) == 7:
            ttl = sum(self.resources.values())
            if ttl >= 8:
                self.drop_resources(ttl // 2)
            self.move_robber()
        for tile in self.board.tiles:
            if tile.die == sum(dice) and tile.terrain_type not in ["water", "desert"] and not tile.robber:
                for spot in tile.spots.values():
                    if spot.owner == self.name:
                        self.resources[tile.terrain_type] += spot.build_level
        return dice

    def build_road(self):
        path = self.choose_path_to_build()
        if path is None:
            return False
        self.roads -= 1
        path.build_level = 1
        if self.board.turn > 0:
            self.resources["brick"] -= 1
            self.resources["lumber"] -= 1
        path.owner = self.name
        print(f"road built by {self.name}")
        return True

    def build_settlement(self):
        spot = self.choose_spot_to_build()
        if spot is None:
            return False
        self.settlements -= 1
        spot.build_level = 1
        if self.board.turn <= 0:
            if self.board.turn == 0:
                for tile in spot.tiles:
                    if tile.terrain_type not in ["water", "desert"]:
                        self.resources[tile.terrain_type] += 1
        else:
            self.resources["brick"] -= 1
            self.resources["lumber"] -= 1
            self.resources["sheep"] -= 1
            self.resources["wheat"] -= 1
        self.victory_points += 1
        spot.owner = self.name
        print(f"settlement built by {self.name}")
        return spot

    def build_city(self):
        spot = self.choose_spot_to_upgrade()
        if not spot:
            return False
        self.cities -= 1
        self.settlements += 1
        spot.build_level = 2
        self.resources["wheat"] -= 2
        self.resources["ore"] -= 3
        self.victory_points += 1
        print(f"city built by {self.name}")  # "we built this city..."
        return True

    def buy_dev_card(self):
        resource_req = self.resources["wheat"] > 0 and self.resources["sheep"] > 0 and self.resources["ore"] > 0
        if resource_req and sum(self.board.dev_cards.values()) > 0:
            card = choice([card for card in self.board.dev_cards if self.board.dev_cards[card]])
            self.resources["sheep"] -= 1
            self.resources["wheat"] -= 1
            self.resources["ore"] -= 1
            self.dev_cards[card] += 1  # randomly selected without replacement
            self.board.dev_cards[card] -= 1
            print(f"dev card bought by {self.name}")
            if card == "victory_point":
                self.victory_points += 1
            return True
        return False

    def play_dev_card(self):
        card = self.choose_dev_card()
        if card is not None:
            self.dev_cards[card] -= 1
            if card == "knight":
                self.move_robber()
                self.dev_cards["knight"] += 1
            elif card == "monopoly":
                resource = self.choose_resource()
                for agent in self.board.agents:
                    if agent.name != self.name:
                        self.resources[resource] += agent.resources[resource]
                        agent.resources[resource] = 0
            elif card == "road_building":
                self.resources["brick"] += 2
                self.resources["lumber"] += 2
                self.build_road()
                self.build_road()
            elif card == "year_of_plenty":
                self.resources[self.choose_resource()] += 1
                self.resources[self.choose_resource()] += 1
            else:
                self.dev_cards[card] += 1
            print(f"dev card played by {self.name}")
            return True
        return False

    def consolidate(self):
        if sum(self.resources.values()) > 7:
            harbors = []
            for path in self.board.paths.values():
                my_harbor = False
                for spot in [self.board.spots[name] for name in path.spots]:
                    if spot.owner == self.name:
                        my_harbor = True
                if my_harbor:
                    harbors.append(path.harbor)
            for resource in self.resources:
                if random() < 0.5:
                    continue
                if resource in harbors and self.resources[resource] > 1:
                    self.resources[resource] -= 2
                    self.resources[self.choose_resource(resource)] += 1
                elif "3:1" in harbors and self.resources[resource] > 2:
                    self.resources[resource] -= 3
                    self.resources[self.choose_resource(resource)] += 1
                elif self.resources[resource] > 3:
                    self.resources[resource] -= 4
                    self.resources[self.choose_resource(resource)] += 1

    def do_actions(self):
        self.build_settlement()
        if random() < exp((1 - self.longest_road()) / 5):
            self.build_road()
        self.build_city()
        if random() < 0.5:
            self.buy_dev_card()
        if random() < 0.5:
            self.play_dev_card()

    def longest_road_helper(self, path, length):
        longest = length
        for neighbor in path.neighbors.values():
            if neighbor.owner == self.name and not neighbor.visited:
                neighbor.visited = True
                longest = max(longest, self.longest_road_helper(neighbor, length + 1))
                neighbor.visited = False
        return longest

    def longest_road(self):
        longest = 0
        for name, path in self.board.paths.items():
            if path.owner == self.name:
                path.visited = True
                longest = max(longest, self.longest_road_helper(path, 1))
                path.visited = False
        return longest

    def largest_army(self):
        return sum([self.dev_cards["knight"] for agent in self.board.agents if agent.name == self.name])

    def __str__(self):
        return self.name + "\n\tvictory points: " + str(self.victory_points) + " " + str(self.resources)

    def __repr__(self):
        return str(self)
