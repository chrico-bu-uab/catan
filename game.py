import math
import random

import matplotlib.pyplot as plt
import numpy as np

UNOWNED = "lightgray"


def flatten_counts(counter):
    lst = []
    for k, v in counter.items():
        lst.extend([k] * v)
    return lst


class Tile:  # there are 19 tiles on the board
    def __init__(self, depth, position, terrain_type, die):
        self.position = position
        self.depth = depth
        radians = math.pi * self.position / 18
        self.a = self.depth * math.cos(radians)
        self.b = self.depth * math.sin(radians)
        self.terrain_type = terrain_type
        self.die = die
        self.probability = 0 if self.die == 7 else (6 - abs(self.die - 7)) / 36
        self.neighbors = set()
        self.intersections = set()
        self.paths = set()
        self.robber = False

    def __eq__(self, other):
        return self.depth == other.depth and self.position == other.position

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "Tile at depth " + str(self.depth) + " and position " + str(self.position) + \
            " with terrain type " + self.terrain_type + " and " + str(self.die) + " dice."

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash((self.depth, self.position))

    def __lt__(self, other):
        if self.depth == other.depth:
            return self.position < other.position
        return self.depth < other.depth

    def __gt__(self, other):
        if self.depth == other.depth:
            return self.position > other.position
        return self.depth > other.depth


class Intersection:  # there are 54 intersections on the board
    def __init__(self, *tiles: Tile):
        self.neighbors = set()
        self.tiles = tuple(sorted(tiles))
        self.paths = set()
        self.build_level = 0
        self.a = self.b = None
        self.owner = UNOWNED

    def __eq__(self, other):
        return self.tiles == other.tiles

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "\n\tIntersection with tiles\n\t\t" + str(self.tiles) + "\n\t\tand build level " + \
            str(self.build_level) + " and owner " + str(self.owner)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.tiles)

    def __lt__(self, other):
        return self.tiles < other.tiles

    def __gt__(self, other):
        return self.tiles > other.tiles


class Path:  # there are 72 paths on the board
    def __init__(self, *intersections: Intersection, harbor):
        self.neighbors = set()
        self.intersections = tuple(sorted(intersections))
        self.harbor = harbor
        self.build_level = 0
        self.a = self.b = None
        self.owner = UNOWNED
        self.visited = False

    def __eq__(self, other):
        return self.intersections == other.intersections

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "\nPath with intersections " + str(self.intersections) + "\n\tand build level " + str(self.build_level) \
            + " and harbor " + str(self.harbor) + " and owner " + str(self.owner)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.intersections)


class Board:
    def __init__(self):
        terrain_types = ["ore", "brick"] * 3 + ["wheat", "lumber", "sheep"] * 4
        dice = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]
        random.shuffle(terrain_types)
        pairs = list(zip(terrain_types, dice))
        pairs.append(("desert", 7))
        random.shuffle(pairs)
        terrain_types, dice = zip(*pairs)

        self.tiles = [Tile(0, 0, terrain_types[0], dice[0])]
        for i in range(6):
            self.tiles.append(Tile(1, 6 * i, terrain_types[i + 1], dice[i + 1]))
        for i in range(12):
            self.tiles.append(Tile(2, 3 * i, terrain_types[i + 7], dice[i + 7]))
        for i in range(18):
            self.tiles.append(Tile(3, 2 * i, "ocean", 7))
        desert_tile = [tile for tile in self.tiles if tile.terrain_type == "desert"][0]
        desert_tile.robber = True
        self.robber = desert_tile

        for tile in self.tiles:
            for tile2 in self.tiles:
                if tile == tile2:
                    continue
                if tile.depth + tile2.depth == 1:
                    tile.neighbors.add(tile2)
                    continue
                proximity = abs(tile.position - tile2.position)
                proximity = min(proximity, 36 - proximity)
                if abs(tile.depth - tile2.depth) <= 1 and proximity * max(tile.depth, tile2.depth) <= 6:
                    tile.neighbors.add(tile2)

        ttl_neighbors = 0
        for tile in self.tiles:
            ttl_neighbors += len(tile.neighbors)
        assert ttl_neighbors == 180, ttl_neighbors

        self.tiles = self.tiles[:19]

        for tile in self.tiles:
            assert len(tile.neighbors) == 6, len(tile.neighbors)

        self.intersections = set()
        for tile in self.tiles:
            for tile2 in tile.neighbors:
                assert tile in tile2.neighbors, (tile, tile2)
                for tile3 in tile2.neighbors:
                    if tile3 in tile.neighbors:
                        intersection = Intersection(tile, tile2, tile3)
                        self.intersections.add(intersection)
                        tile.intersections.add(intersection)

        assert len(self.intersections) == 54, len(self.intersections)
        for tile in self.tiles:
            assert len(tile.intersections) == 6, len(tile.intersections)

        harbors = list(set(terrain_types)) + ["3:1"] * 4 + [None] * 21
        random.shuffle(harbors)
        self.paths = set()
        ints2 = list(self.intersections)
        for intersection in list(ints2):
            for i in ints2:
                if len(set(intersection.tiles).union(i.tiles)) == 4:
                    if any(tile not in self.tiles for tile in intersection.tiles) and any(
                            tile not in self.tiles for tile in i.tiles):
                        harbor = harbors.pop()
                    else:
                        harbor = "N/A"
                    path = Path(intersection, i, harbor=harbor)
                    self.paths.add(path)
                    print(path)
                    intersection.paths.add(path)
                    i.paths.add(path)
            ints2.remove(intersection)
        assert len(self.paths) == 72, len(self.paths)

        for intersection in self.intersections:
            assert len(intersection.paths) < 4, len(intersection.paths)
            assert len(intersection.paths) > 1, len(intersection.paths)
            for i in self.intersections:
                if len(set(intersection.paths).union(i.paths)) < \
                        len(intersection.paths) + len(i.paths) and intersection != i:
                    intersection.neighbors.add(i)
            intersection.a = sum(tile.a for tile in intersection.tiles) / 3
            intersection.b = sum(tile.b for tile in intersection.tiles) / 3

        for intersection in self.intersections:
            assert len(intersection.neighbors) < 4, len(intersection.neighbors)
            assert len(intersection.neighbors) > 1, len(intersection.neighbors)

        for path in self.paths:
            assert len(path.intersections) == 2, len(path.intersections)
            intersection, i = path.intersections
            for tile in set(intersection.tiles).intersection(i.tiles):
                tile.paths.add(path)
            for p in self.paths:
                if len(set(path.intersections).union(p.intersections)) < \
                        len(path.intersections) + len(p.intersections) and path != p:
                    path.neighbors.add(p)
            path.a = (intersection.a + i.a) / 2
            path.b = (intersection.b + i.b) / 2

        for tile in self.tiles:
            assert len(tile.paths) == 6, len(tile.paths)

        for path in self.paths:
            assert len(path.neighbors) < 5, len(path.neighbors)
            assert len(path.neighbors) > 1, len(path.neighbors)

        last_high_dice = {}
        restricted_tiles = []
        for tile in self.tiles:
            # fix dice so that 6's and 8's are not next to each other
            if tile.die in [6, 8]:
                restricted_tiles.append(tile)
                for tile2 in tile.neighbors:
                    restricted_tiles.append(tile2)
                    if tile2.die in [6, 8]:
                        last_high_dice[tile2] = tile2.die
                        tile2.die = None

        random.shuffle(self.tiles)
        bad_tiles = list(last_high_dice)
        for tile in self.tiles:
            if last_high_dice and tile not in restricted_tiles:
                low_dice = tile.die
                bad_tile = bad_tiles.pop()
                tile.die = last_high_dice.pop(bad_tile)
                bad_tile.die = low_dice

        self.intersections = list(self.intersections)
        random.shuffle(self.intersections)

        self.paths = list(self.paths)
        random.shuffle(self.paths)
        last_harbors = []
        restricted_paths = []
        for path in self.paths:
            # fix harbors so that they are not next to each other
            if path.harbor != "N/A":
                if path.harbor is not None and path.harbor != "N/A":
                    restricted_paths.append(path)
                    for p in path.neighbors:
                        restricted_paths.append(p)
                        if p.harbor is not None and p.harbor != "N/A":
                            last_harbors.append(p.harbor)
                            p.harbor = None

        random.shuffle(self.paths)
        for path in self.paths:
            if last_harbors and (path not in restricted_paths) and (path.harbor != "N/A"):
                path.harbor = last_harbors.pop()
        self.paths = set(self.paths)

        self.dev_cards = {"knight": 14, "victory_point": 5, "road_building": 2, "year_of_plenty": 2, "monopoly": 2}

        self.players = []

        self.turn = 0

        self.player_with_longest_road = None
        self.player_with_largest_army = None

    def add_player(self, player):
        self.players.append(player)

    def longest_road(self):
        longest_roads = [player.longest_road() for player in self.players]
        longest_road = max(longest_roads)
        if longest_road >= 5:
            if self.player_with_longest_road is None:
                self.player_with_longest_road = (self.players[np.argmax(longest_roads)], longest_road)
                self.player_with_longest_road[0].victory_points += 2
            elif self.player_with_longest_road[1] < longest_road:
                self.player_with_longest_road[0].victory_points -= 2
                self.player_with_longest_road = (self.players[np.argmax(longest_roads)], longest_road)
                self.player_with_longest_road[0].victory_points += 2
        return longest_road

    def largest_army(self):
        largest_armies = [player.largest_army() for player in self.players]
        largest_army = max(largest_armies)
        if largest_army >= 3:
            if self.player_with_largest_army is None:
                self.player_with_largest_army = (self.players[np.argmax(largest_armies)], largest_army)
                self.player_with_largest_army[0].victory_points += 2
            elif self.player_with_largest_army[1] < largest_army:
                self.player_with_largest_army[0].victory_points -= 2
                self.player_with_largest_army = (self.players[np.argmax(largest_armies)], largest_army)
                self.player_with_largest_army[0].victory_points += 2
        return largest_army

    def plot(self):
        plt.figure(figsize=(5, 5))
        harbor_colors = {"ore": "lavender", "brick": "firebrick", "wheat": "lemonchiffon", "lumber": "olive",
                         "sheep": "aquamarine", "3:1": "purple", None: UNOWNED, "desert": "orange",
                         "N/A": UNOWNED}
        for tile in sorted(self.tiles):
            plt.scatter(tile.a, tile.b, color=harbor_colors[tile.terrain_type], s=2000, marker="h")
            plt.text(tile.a, tile.b, tile.die, ha="center", va="center", fontsize=10)
            for intersection in tile.intersections:
                plt.scatter(intersection.a, intersection.b,
                            color="black" if intersection.build_level == 0 else intersection.owner,
                            s=75 * intersection.build_level + 25,
                            marker="o" if intersection.build_level == 1 else ("D" if intersection.build_level == 2
                                                                              else "1"))
                for path in intersection.paths:
                    plt.scatter(path.a, path.b, color=harbor_colors[path.harbor],
                                marker="+", s=50 if (path.harbor is not None) and (path.harbor != "N/A") else 0)
                    plt.plot([intersection.a, path.a], [intersection.b, path.b], color=path.owner)
            if tile.robber:
                plt.text(tile.a, tile.b, "*", ha="left", va="bottom", fontsize=10)
        plt.show()


class Player:
    def __init__(self, name, board: Board):
        self.name = name
        while name in [player.name for player in board.players]:
            self.name = input(f'"{name}" already taken! Please choose a different name: ')
        self.board = board
        self.resources = {"ore": 0, "brick": 0, "wheat": 0, "lumber": 0, "sheep": 0}
        self.roads = 15
        self.settlements = 5
        self.cities = 4
        self.dev_cards = {"knight": 0, "victory_point": 0, "monopoly": 0, "road_building": 0, "year_of_plenty": 0}
        self.victory_points = 0
        self.board.add_player(self)

    def available_paths(self, source):
        if not (self.roads and ((self.resources["brick"] and self.resources["lumber"]) or not self.board.turn)):
            return []
        paths = [path for path in self.board.paths if
                 (any([p.owner == self.name for p in path.neighbors]) or
                  any([i.owner == self.name for i in path.intersections]))
                 and path.owner == UNOWNED]
        if source is not None:
            paths = [path for path in paths if source in path.intersections]
        return paths

    def available_intersections_for_settlement(self):
        if not (self.settlements and ((self.resources["brick"] and self.resources["lumber"] and
                                       self.resources["wheat"] and self.resources["sheep"]) or not self.board.turn)):
            return []
        intersections = []
        for intersection in self.board.intersections:
            if intersection.build_level == 0 and \
                    (any([path.owner == self.name for path in intersection.paths]) or not self.board.turn) and \
                    not any([i.build_level > 0 for i in intersection.neighbors]):
                intersections.append(intersection)
        return intersections

    def choose_tile_to_occupy(self):
        tiles = [tile for tile in self.board.tiles
                 if all(intersection.owner != self.name for intersection in tile.intersections) and not tile.robber]
        random.shuffle(tiles)
        return tiles[np.argmax([tile.probability for tile in tiles])]

    def choose_resource(self, exclude=None):
        return random.choice([resource for resource in self.resources if self.resources[resource] == min(
            [v for k, v in self.resources.items() if k != exclude]) and resource != exclude])

    def drop_resources(self, n):
        resources = flatten_counts(self.resources)
        for _ in range(n):
            resources.remove(random.choice(resources))

    def choose_path_to_build(self, source):
        paths = self.available_paths(source)
        if paths:
            optimal_paths = [path for path in paths if
                             all(i.owner == UNOWNED for i in path.intersections) and
                             any(all(i.owner == UNOWNED for i in p.intersections) for p in path.neighbors)]
            if optimal_paths:
                return random.choice(optimal_paths)
            return random.choice(paths)
        return None

    def choose_intersection_to_build(self):
        intersections = self.available_intersections_for_settlement()
        if intersections:
            random.shuffle(intersections)
            return intersections[
                np.argmax([sum(tile.probability for tile in intersection.tiles) for intersection in intersections])]
        return None

    def choose_intersection_to_upgrade(self):
        intersections = [intersection for intersection in self.board.intersections if intersection.build_level == 1
                         and intersection.owner == self.name and (
                                 self.resources["wheat"] > 1 and self.resources["ore"] > 2)
                         and self.cities > 0 and intersection.build_level == 1]
        if intersections:
            return random.choice(intersections)
        return None

    def choose_dev_card(self):
        cards = [card for card in self.dev_cards if self.dev_cards[card] > 0 and card != "victory_point"]
        if cards:
            return random.choice(cards)
        return None

    def choose_person_to_steal_from(self, tile):
        people = [player for player in self.board.players if
                  (player.name != self.name) and sum(player.resources.values()) and (
                          player.name in [intersection.owner for intersection in tile.intersections])]
        return random.choice(people)

    def steal(self, tile):
        person = self.choose_person_to_steal_from(tile)
        if person:
            resource = random.choice(flatten_counts(person.resources))
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
        dice = [random.randint(1, 6), random.randint(1, 6)]
        # print(f"{self.name} rolled a {dice[0]} and a {dice[1]}!")
        if sum(dice) == 7:
            ttl = sum(self.resources.values())
            if ttl >= 8:
                self.drop_resources(ttl // 2)
            self.move_robber()
        for tile in self.board.tiles:
            if tile.die == sum(dice) and tile.terrain_type not in ["ocean", "desert"] and not tile.robber:
                for intersection in tile.intersections:
                    if intersection.owner == self.name:
                        self.resources[tile.terrain_type] += intersection.build_level

    def build_road(self, source=None):
        path = self.choose_path_to_build(source)
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
        intersection = self.choose_intersection_to_build()
        if intersection is None:
            return False
        self.settlements -= 1
        intersection.build_level = 1
        if not self.board.turn:
            for tile in intersection.tiles:
                if tile.terrain_type not in ["ocean", "desert"]:
                    self.resources[tile.terrain_type] += 1
        else:
            self.resources["brick"] -= 1
            self.resources["lumber"] -= 1
            self.resources["sheep"] -= 1
            self.resources["wheat"] -= 1
        self.victory_points += 1
        intersection.owner = self.name
        print(f"settlement built by {self.name}")
        return intersection

    def build_city(self):
        intersection = self.choose_intersection_to_upgrade()
        if not intersection:
            return False
        self.cities -= 1
        self.settlements += 1
        intersection.build_level = 2
        self.resources["wheat"] -= 2
        self.resources["ore"] -= 3
        self.victory_points += 1
        print(f"city built by {self.name}")  # "we built this city..."
        return True

    def buy_dev_card(self):
        resource_req = self.resources["wheat"] > 0 and self.resources["sheep"] > 0 and self.resources["ore"] > 0
        if resource_req and sum(self.board.dev_cards.values()) > 0:
            card = random.choice([card for card in self.board.dev_cards if self.board.dev_cards[card]])
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
                for player in self.board.players:
                    if player.name != self.name:
                        self.resources[resource] += player.resources[resource]
                        player.resources[resource] = 0
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
            for path in self.board.paths:
                my_harbor = False
                for intersection in path.intersections:
                    if intersection.owner == self.name:
                        my_harbor = True
                if my_harbor:
                    harbors.append(path.harbor)
            for resource in self.resources:
                if random.random() < 0.5:
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
        if random.random() < math.exp((1 - self.longest_road()) / 5):
            self.build_road()
        self.build_city()
        if random.random() < 0.5:
            self.buy_dev_card()
        if random.random() < 0.5:
            self.play_dev_card()

    def longest_road_helper(self, path, length):
        longest = length
        for neighbor in path.neighbors:
            if neighbor.owner == self.name and not neighbor.visited:
                neighbor.visited = True
                longest = max(longest, self.longest_road_helper(neighbor, length + 1))
                neighbor.visited = False
        return longest

    def longest_road(self):
        longest = 0
        for path in self.board.paths:
            if path.owner == self.name:
                path.visited = True
                longest = max(longest, self.longest_road_helper(path, 1))
                path.visited = False
        return longest

    def largest_army(self):
        return sum([self.dev_cards["knight"] for player in self.board.players if player.name == self.name])

    def __str__(self):
        return self.name + "\n\tvictory points: " + str(self.victory_points) + " " + str(self.resources)

    def __repr__(self):
        return self.name + "\n\tvictory points: " + str(self.victory_points) + " " + str(self.resources)
