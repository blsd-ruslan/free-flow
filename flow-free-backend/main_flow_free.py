from collections import deque

from flask import Flask, jsonify, request
import threading
from copy import deepcopy
import sys
from flask_cors import CORS

sys.setrecursionlimit(10000)

# Directions: up, down, left, right
directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

app = Flask(__name__)
CORS(app)


# Shared Game Logic
class FlowFreeGame:
    def __init__(self, size, pairs):
        self.size = size
        self.grid = [[0] * size for _ in range(size)]  # Use 0 for empty cells
        self.pairs = pairs
        self.colors = [pair['color'] for pair in pairs]
        self.color_ids = {color: idx + 1 for idx, color in enumerate(self.colors)}  # Map colors to unique numbers
        self.steps = []
        self.status = "not_started"

        # Place the start and end points
        for pair in pairs:
            x1, y1 = pair['start']
            x2, y2 = pair['end']
            color = pair['color']
            color_id = self.color_ids[color]
            self.grid[y1][x1] = color_id
            self.grid[y2][x2] = color_id

    def save_step(self, grid):
        self.steps.append(deepcopy(grid))  # Save the current grid state


# Algorithms
class FlowFreeSolverDFS:
    def __init__(self, game):
        self.game = game
        self.size = game.size
        self.visited_states_count = 0

    def solve(self):
        self.game.status = "in_progress"
        grid = deepcopy(self.game.grid)
        self.game.save_step(grid)
        if self.dfs(0, grid):
            self.game.status = "finished"
            return True
        return False

    def dfs(self, color_index, grid):
        if color_index == len(self.game.colors):
            return True

        color_id = self.game.color_ids[self.game.colors[color_index]]
        start = tuple(self.game.pairs[color_index]['start'])
        end = tuple(self.game.pairs[color_index]['end'])
        visited = set()

        return self.dfs_connect(start, end, grid, color_id, visited, color_index)

    def dfs_connect(self, current, end, grid, color_id, visited, color_index):
        if current == end:
            return self.dfs(color_index + 1, grid)

        x, y = current
        visited.add(current)
        self.game.save_step(grid)

        for dx, dy in sorted(directions, key=lambda d: abs((x + d[0]) - end[0]) + abs((y + d[1]) - end[1])):
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                if (nx, ny) not in visited and (grid[ny][nx] == 0 or (nx, ny) == end):
                    backup = grid[ny][nx]
                    grid[ny][nx] = color_id
                    self.game.save_step(grid)
                    if self.dfs_connect((nx, ny), end, grid, color_id, visited, color_index):
                        return True
                    grid[ny][nx] = backup
                    self.game.save_step(grid)
        visited.remove(current)
        return False


class FlowFreeSolverFC:
    def __init__(self, game):
        self.game = game
        self.size = game.size
        self.visited_states_count = 0

    def solve(self):
        self.game.status = "in_progress"
        grid = deepcopy(self.game.grid)
        if self.forward_check(0, grid):
            print("Solution found.")
            self.game.status = "finished"
        else:
            print("No solution exists.")
        print(f"Number of visited states: {self.visited_states_count}")

    def forward_check(self, color_index, grid):
        if color_index == len(self.game.colors):
            return True

        color = self.game.colors[color_index]
        color_id = self.game.color_ids[color]
        pair = self.game.pairs[color_index]
        start = tuple(pair['start'])
        end = tuple(pair['end'])
        if not self.is_path_possible(start, end, grid):
            return False

        visited = set()
        return self.fc_connect(start, end, grid, color_id, visited, color_index)

    def fc_connect(self, current, end, grid, color_id, visited, color_index):
        if current == end:
            # Move on to the next color
            if self.forward_check(color_index + 1, grid):
                return True
            else:
                return False

        x, y = current
        visited.add(current)
        self.game.save_step(grid)
        self.visited_states_count += 1

        moves = [(dx, dy) for dx, dy in directions]
        moves.sort(key=lambda d: abs((x + d[0]) - end[0]) + abs((y + d[1]) - end[1]))

        for dx, dy in moves:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                if (nx, ny) not in visited and (grid[ny][nx] == 0 or (nx, ny) == end):
                    backup = grid[ny][nx]
                    grid[ny][nx] = color_id
                    self.game.save_step(grid)

                    # Check if current path leads to the dead end
                    if not self.is_path_possible((nx,ny), end, grid):
                        # print("dead end")
                        grid[ny][nx] = backup
                        continue

                    # Check if other remaining pairs are possible to solve (BFS)
                    if self.all_colors_still_feasible(color_index, grid) and self.fc_connect((nx, ny), end, grid,
                                                                                             color_id, visited,
                                                                                             color_index):
                        return True

                    grid[ny][nx] = backup
                    self.game.save_step(grid)

        visited.remove(current)
        return False

    def all_colors_still_feasible(self, current_color_index, grid):
        for idx in range(current_color_index + 1, len(self.game.colors)):
            pair = self.game.pairs[idx]
            start = tuple(pair['start'])
            end = tuple(pair['end'])
            if not self.is_path_possible(start, end, grid):
                return False
        return True

    def is_path_possible(self, start, end, grid):
        """
        Check if a path is possible from `start` to `end` using a simple BFS
        without modifying the grid.
        """
        queue = deque([start])
        visited = set()
        while queue:
            x, y = queue.popleft()
            if (x, y) == end:
                return True
            visited.add((x, y))
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.size and 0 <= ny < self.size and (nx, ny) not in visited:
                    if grid[ny][nx] == 0 or (nx, ny) == end:
                        queue.append((nx, ny))
        return False


class FlowFreeSolverReverse:
    def __init__(self, game):
        self.game = game
        self.size = game.size
        self.visited_states_count = 0

    def solve(self):
        self.game.status = "not_started"
        grid = deepcopy(self.game.grid)
        self.game.save_step(grid)
        if self.reverse_search(0, grid):
            print("Solution found.")
            self.game.status = "finished"
        else:
            print("No solution exists.")
        print(f"Number of visited states: {self.visited_states_count}")

    def reverse_search(self, color_index, grid):
        if color_index == len(self.game.colors):
            return True

        color_id = self.game.color_ids[self.game.colors[color_index]]
        start = tuple(self.game.pairs[color_index]['start'])
        end = tuple(self.game.pairs[color_index]['end'])
        visited = set()

        return self.reverse_connect(end, start, grid, color_id, visited, color_index)

    def reverse_connect(self, current, target, grid, color_id, visited, color_index):
        if current == target:
            return self.reverse_search(color_index + 1, grid)

        x, y = current
        visited.add(current)
        self.game.save_step(grid)

        for dx, dy in sorted(directions, key=lambda d: abs((x + d[0]) - target[0]) + abs((y + d[1]) - target[1])):
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                if (nx, ny) not in visited and (grid[ny][nx] == 0 or (nx, ny) == target):
                    backup = grid[ny][nx]
                    grid[ny][nx] = color_id
                    self.game.save_step(grid)
                    if self.reverse_connect((nx, ny), target, grid, color_id, visited, color_index):
                        return True
                    grid[ny][nx] = backup
                    self.game.save_step(grid)
        visited.remove(current)
        return False


# Backend API
maps = {
    "Map1": {"size": 6, "pairs": [
        {"color": "1", "start": [5, 1], "end": [4, 3]},
        {"color": "2", "start": [2, 3], "end": [5, 2]},
        {"color": "3", "start": [5, 0], "end": [1, 5]},
        {"color": "4", "start": [1, 1], "end": [3, 1]},
        {"color": "5", "start": [3, 2], "end": [5, 5]},
    ]},
    "Map2": {"size": 6, "pairs": [
        {"color": "1", "start": [1, 1], "end": [4, 4]},
        {"color": "2", "start": [3, 1], "end": [5, 2]},
        {"color": "3", "start": [1, 0], "end": [3, 2]},
        {"color": "4", "start": [5, 0], "end": [3, 3]},
    ]},
    "Map3": {"size": 6, "pairs": [
        {"color": "1", "start": [1, 4], "end": [5, 4]},
        {"color": "2", "start": [3, 5], "end": [5, 5]},
        {"color": "3", "start": [0, 0], "end": [4, 1]},
        {"color": "4", "start": [4, 4], "end": [1, 0]},
    ]},
    "Map4": {"size": 6, "pairs": [
        {"color": "1", "start": [2, 0], "end": [5, 5]},
        {"color": "2", "start": [1, 2], "end": [3, 1]},
        {"color": "3", "start": [0, 0], "end": [0, 2]},
        {"color": "4", "start": [1, 4], "end": [2, 3]},
        {"color": "5", "start": [1, 0], "end": [3, 4]},
    ]},
    "Map5": {"size": 6, "pairs": [
        {"color": "1", "start": [4, 1], "end": [2, 2]},
        {"color": "2", "start": [4, 4], "end": [2, 0]},
        {"color": "3", "start": [1, 4], "end": [5, 0]},
        {"color": "4", "start": [4, 5], "end": [5, 4]},
        {"color": "5", "start": [4, 0], "end": [1, 3]},
    ]},
    "Map6": {"size": 6, "pairs": [
        {"color": "1", "start": [0, 1], "end": [4, 1]},
        {"color": "2", "start": [1, 4], "end": [5, 3]},
        {"color": "3", "start": [4, 0], "end": [5, 1]},
        {"color": "4", "start": [0, 3], "end": [5, 4]},
        {"color": "5", "start": [0, 2], "end": [3, 3]},
        {"color": "6", "start": [1, 1], "end": [5, 2]},
    ]},
    "Map7": {"size": 6, "pairs": [
        {"color": "1", "start": [0, 5], "end": [1, 2]},
        {"color": "2", "start": [1, 1], "end": [4, 5]},
        {"color": "3", "start": [5, 0], "end": [5, 5]},
        {"color": "4", "start": [3, 3], "end": [4, 4]},
        {"color": "5", "start": [4, 0], "end": [4, 3]},
        {"color": "6", "start": [0, 4], "end": [3, 2]},
    ]},
    "Map8": {"size": 6, "pairs": [
        {"color": "1", "start": [0, 5], "end": [4, 2]},
        {"color": "2", "start": [1, 0], "end": [1, 5]},
        {"color": "3", "start": [1, 3], "end": [4, 4]},
        {"color": "4", "start": [1, 4], "end": [3, 4]},
        {"color": "5", "start": [0, 0], "end": [4, 1]},
    ]},
    "Map9": {"size": 6, "pairs": [
        {"color": "1", "start": [5, 0], "end": [4, 4]},
        {"color": "2", "start": [3, 3], "end": [2, 5]},
        {"color": "3", "start": [1, 1], "end": [5, 1]},
        {"color": "4", "start": [1, 2], "end": [1, 4]},
    ]},
    "Map10": {"size": 6, "pairs": [
        {"color": "1", "start": [2, 3], "end": [4, 4]},
        {"color": "2", "start": [2, 2], "end": [4, 2]},
        {"color": "3", "start": [0, 0], "end": [4, 1]},
        {"color": "4", "start": [1, 4], "end": [3, 5]},
        {"color": "5", "start": [0, 1], "end": [1, 2]},
        {"color": "6", "start": [1, 3], "end": [2, 5]},
        {"color": "7", "start": [2, 0], "end": [4, 5]},
    ]},

}

algorithms = {
    "DFS": FlowFreeSolverDFS,
    "Forward Checking": FlowFreeSolverFC,
    "Reverse Search": FlowFreeSolverReverse,
}

game = None
solver = None


@app.route('/algorithms', methods=['GET'])
def get_algorithms():
    return jsonify(list(algorithms.keys()))


@app.route('/maps', methods=['GET'])
def get_maps():
    return jsonify(list(maps.keys()))


@app.route('/start', methods=['POST'])
def start_solver():
    global game, solver
    data = request.get_json()
    map_name = data.get('map')
    algorithm_name = data.get('algorithm')

    if map_name not in maps or algorithm_name not in algorithms:
        return jsonify({"error": "Invalid map or algorithm"}), 400

    selected_map = maps[map_name]
    game = FlowFreeGame(selected_map['size'], selected_map['pairs'])
    solver_class = algorithms[algorithm_name]
    solver = solver_class(game)

    threading.Thread(target=solver.solve).start()
    return jsonify({'status': 'Solver started'})


@app.route('/steps', methods=['GET'])
def get_steps():
    if game:
        return jsonify({'steps': game.steps, 'status': game.status})
    return jsonify({'error': 'No game in progress'})


if __name__ == '__main__':
    app.run(debug=True)
