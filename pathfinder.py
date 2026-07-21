"""
pathfinder.py - Módulo 2 (Integrante 2)
El integrante 2 reemplaza este archivo con su implementación real
Interfaz esperada por main.py:
    pathfinder = Pathfinder(dungeon)
    ruta = pathfinder.bfs(sala_inicio, sala_jefe)   → list[int] | None
    todas = pathfinder.dfs(sala_inicio)              → set[int]
"""

from collections import deque

class Pathfinder:
    def __init__(self, dungeon):
        self.dungeon = dungeon

    def bfs(self, start: int, goal: int):
        """Camino más corto de start a goal. Retorna lista de IDs o None."""
        queue = deque([[start]])
        visited = {start}
        while queue:
            path = queue.popleft()
            node = path[-1]
            if node == goal:
                return path
            for neighbor in self.dungeon.get_neighbors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
        return None

    def dfs(self, start: int):
        """Devuelve el conjunto de salas alcanzables desde start."""
        visited = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                for neighbor in self.dungeon.get_neighbors(node):
                    stack.append(neighbor)
        return visited