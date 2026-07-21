"""
dungeon_graph.py
Módulo 1 - DungeonGraph
Autor: [Christian Correa]
"""

import random
from dataclasses import dataclass

#  Constantes públicas que usan los otros módulos
ROOM_DESCRIPTIONS = {
    "start":  "La entrada del dungeon. Huele a humedad y antorchas apagadas.",
    "normal": "Una sala vacía. Las paredes tienen marcas de garras.",
    "chest":  "Un cofre oxidado reposa en el centro de la sala.",
    "enemy":  "Las sombras se mueven. Hay algo aquí.",
    "elite":  "Un rugido grave retumba en las paredes. Algo poderoso acecha.",
    "boss":   "El aire se vuelve pesado. El jefe te espera.",
}

@dataclass
class Room:
    """
    Metadatos de una sala del dungeon.
    Reemplaza el dict suelto {"type": ..., "visited": ..., "desc": ...}
    que se usaba antes. Con una dataclass se gana tipado real y
    autocompletado en el IDE, y se evitan errores silenciosos de typo
    en las claves (ej. `rooms[id]["tpye"]` con un dict lanza un
    KeyError confuso en tiempo de ejecución; `rooms[id].tpye` con una
    dataclass lo marca el propio editor/linter antes de correr nada).
    """
    type: str
    desc: str
    visited: bool = False

class DungeonGraph:
    """
    Grafo no dirigido que representa el mapa de la mazmorra.
    Atributos públicos que usan los otros módulos:
        - rooms      : dict[int, Room]   → metadatos de cada sala
        - adjacency  : dict[int, list]   → lista de adyacencia
        - start_room : int               → ID de la sala inicial
        - boss_room  : int               → ID de la sala del jefe
        - total_rooms: int               → cantidad total de salas
        - floor      : int               → piso actual del dungeon
    Nota de diseño: ningún otro módulo debería leer `self.rooms`
    directamente. Para eso están los métodos públicos de abajo
    (get_room_type, get_room_desc, is_visited, get_all_room_ids...):
    si mañana cambia otra vez la representación interna de una sala,
    LootStack y Renderer no se enteran ni hay que tocarlos.
    """

    def __init__(self):
        self.rooms: dict[int, Room] = {}
        self.adjacency: dict[int, list[int]] = {}
        self.start_room: int = 0
        self.boss_room: int = 0
        self.total_rooms: int = 0
        self.floor: int = 1

    #  Generación procedural
    def generate(self, n: int = 8, floor: int = 1) -> None:
        """
        Genera un grafo conexo con n salas de forma procedural.
        Algoritmo:
            1.  Crea n salas con tipos asignados (start, boss, normal…)
                La mezcla de tipos depende de `floor`: a mayor piso,
                más salas de enemigo y aparición de salas "elite".
            2.  Conecta cada sala nueva a una sala anterior al azar
                → garantiza que el grafo siempre sea CONEXO
            3. Añade 1 o 2 conexiones extra para crear caminos alternativos
        """
        if n < 4:
            n = 4  # mínimo para tener start, boss y al menos 2 normales

        self.total_rooms = n
        self.floor = max(1, floor)
        self._reset()

        # 1. Asignar tipos (según dificultad del piso)
        types = self._assign_types(n, self.floor)

        # 2. Registrar salas
        for room_id in range(n):
            self._add_room(room_id, types[room_id])

        # 3. Conectar proceduralmente (árbol generador → garantiza conexión)
        for room_id in range(1, n):
            neighbor = random.randint(0, room_id - 1)
            self._connect(room_id, neighbor)

        # 4. Conexiones extra para hacer el mapa más interesante
        extra = max(1, n // 4)
        self._add_extra_connections(extra)

        # 5. Guardar referencias clave
        self.start_room = types.index("start")
        self.boss_room  = types.index("boss")

    def _reset(self) -> None:
        """Limpia el estado antes de una nueva generación."""
        self.rooms.clear()
        self.adjacency.clear()

    def _assign_types(self, n: int, floor: int) -> list[str]:
        """
        Crea la lista de tipos garantizando que haya exactamente
        1 sala de inicio y 1 sala de jefe. La bolsa de tipos ("pool")
        se vuelve más peligrosa en pisos más profundos.
        """
        types = ["start", "boss"]
        pool  = ["normal", "normal", "chest", "enemy"]
        if floor >= 2:
            pool.append("enemy")          # más enemigos desde el piso 2
        if floor >= 3:
            pool.append("elite")          # salas de élite desde el piso 3
        if floor >= 5:
            pool.append("elite")          # aún más élites en pisos avanzados

        for _ in range(n - 2):
            types.append(random.choice(pool))
        random.shuffle(types)
        return types

    def _add_room(self, room_id: int, room_type: str) -> None:
        """Registra una sala nueva en el grafo."""
        self.rooms[room_id] = Room(
            type=room_type,
            desc=ROOM_DESCRIPTIONS.get(room_type, "Una sala desconocida."),
        )
        self.adjacency[room_id] = []

    def _connect(self, room_a: int, room_b: int) -> None:
        """
        Crea un pasillo bidireccional entre room_a y room_b.
        No crea aristas duplicadas.
        """
        if room_b not in self.adjacency[room_a]:
            self.adjacency[room_a].append(room_b)
        if room_a not in self.adjacency[room_b]:
            self.adjacency[room_b].append(room_a)

    def _add_extra_connections(self, count: int) -> None:
        """Agrega conexiones adicionales para crear caminos alternativos."""
        ids = self.get_all_room_ids()
        attempts = 0
        added = 0
        while added < count and attempts < count * 10:
            a = random.choice(ids)
            b = random.choice(ids)
            if a != b and b not in self.adjacency[a]:
                self._connect(a, b)
                added += 1
            attempts += 1

    #  Interfaz pública para los otros módulos
    def get_neighbors(self, room_id: int) -> list[int]:
        """
        Devuelve la lista de salas vecinas a room_id.
        Usado por: Pathfinder, main.py
        """
        return self.adjacency.get(room_id, [])

    def get_room_type(self, room_id: int) -> str:
        """
        Devuelve el tipo de sala: 'start', 'normal', 'chest', 'enemy',
        'elite', 'boss'.
        Usado por: LootStack, Renderer, main.py
        """
        return self.rooms[room_id].type

    def get_room_desc(self, room_id: int) -> str:
        """
        Devuelve la descripción textual de la sala.
        Usado por: main.py
        """
        return self.rooms[room_id].desc

    def mark_visited(self, room_id: int) -> None:
        """
        Marca una sala como visitada.
        Usado por: main.py
        """
        self.rooms[room_id].visited = True

    def is_visited(self, room_id: int) -> bool:
        """Devuelve True si el jugador ya estuvo en esta sala."""
        return self.rooms[room_id].visited

    def is_valid_room(self, room_id: int) -> bool:
        """Devuelve True si room_id existe en el grafo."""
        return room_id in self.rooms

    def room_count(self) -> int:
        """Devuelve el número total de salas."""
        return len(self.rooms)

    def get_all_room_ids(self) -> list[int]:
        """
        Devuelve la lista de IDs de todas las salas del piso actual.
        Usado por: LootStack, Renderer — en vez de recorrer
        `dungeon.rooms` directamente, para no depender de cómo se
        representa una sala por dentro.
        """
        return list(self.rooms.keys())

    def get_floor(self) -> int:
        """
        Devuelve el número de piso actual del dungeon.
        Usado por: LootStack, Renderer, main.py
        """
        return self.floor

    #  Debug / presentación
    def print_graph(self) -> None:
        """
        Imprime el grafo completo en consola.
        Útil para debug y para la demo en la presentación.
        """
        width = 30
        print("\n╔" + "═" * width + "╗")
        print("║" + "MAPA DEL DUNGEON (GRAFO)".center(width) + "║")
        print("║" + f"PISO {self.floor}".center(width) + "║")
        print("╚" + "═" * width + "╝")
        for room_id, neighbors in self.adjacency.items():
            room_type = self.get_room_type(room_id)
            tag = ""
            if room_id == self.start_room:
                tag = " ← INICIO"
            elif room_id == self.boss_room:
                tag = " ← JEFE"
            print(f"  Sala {room_id:2d} [{room_type:6s}]{tag}")
            print(f"         └─ conectada con: {neighbors}")
        print()