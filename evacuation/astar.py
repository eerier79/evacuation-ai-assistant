"""A* search on the grid; the cost of entering a cell grows with its blockage probability."""
import heapq


def neighbours(cell, walls, rows, cols):
    r, c = cell
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in walls:
            yield (nr, nc)


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(start, goal, walls, rows, cols, cell_cost):
    """cell_cost(cell) >= 1, so the Manhattan distance never overestimates (admissible)."""
    counter = 0
    frontier = [(manhattan(start, goal), counter, 0.0, start)]
    came_from, best_cost, expanded = {start: None}, {start: 0.0}, 0
    while frontier:
        _, _, cost, cell = heapq.heappop(frontier)
        if cost > best_cost[cell]:
            continue
        expanded += 1
        if cell == goal:
            path = []
            while cell is not None:
                path.append(cell)
                cell = came_from[cell]
            return {"path": path[::-1], "cost": cost, "expanded": expanded}
        for nxt in neighbours(cell, walls, rows, cols):
            new_cost = cost + cell_cost(nxt)
            if new_cost < best_cost.get(nxt, float("inf")):
                best_cost[nxt] = new_cost
                came_from[nxt] = cell
                counter += 1
                heapq.heappush(frontier, (new_cost + manhattan(nxt, goal), counter, new_cost, nxt))
    return None
