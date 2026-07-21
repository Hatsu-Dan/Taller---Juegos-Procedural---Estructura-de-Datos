"""
renderer.py - Módulo 4 (Integrante 4)
El integrante 4 reemplaza este archivo con su implementación real
Interfaz esperada por main.py:
    renderer = Renderer(dungeon)
    renderer.draw(current_room, player_hp, inventory, loot)

Novedades para el sistema de pisos:
    - El header y el panel de estado ahora muestran el piso actual,
      leído directamente de dungeon.get_floor() (sin cambiar la
      firma pública del constructor: sigue siendo Renderer(dungeon)).
    - Se añadió el ícono para el nuevo tipo de sala "elite".
    - Los íconos se unificaron a 3 caracteres ("[X]") para que la
      matriz 2D quede alineada sin importar la fuente de la terminal
      (antes se mezclaban emojis de ancho variable con texto).
    - _draw_map ya no lee dungeon.rooms directamente; usa
      dungeon.get_all_room_ids(), la interfaz pública del grafo.
"""

TILE_ICONS = {
    "start":   "[S]",
    "normal":  "[ ]",
    "chest":   "[$]",
    "enemy":   "[E]",
    "elite":   "[X]",
    "boss":    "[B]",
    "player":  "[@]",
    "unknown": "[?]",
}

BOX_WIDTH = 38


class Renderer:
    def __init__(self, dungeon):
        self.dungeon = dungeon

    def draw(self, current_room: int, player_hp: int,
            inventory: list, loot_peek):
        """
        Dibuja el estado actual del dungeon en consola.
        Usa la MATRIZ 2D interna para representar el mapa.
        """
        print("\033[H\033[J", end="")   # limpiar consola
        self._draw_header()
        self._draw_map(current_room)
        self._draw_status(current_room, player_hp, inventory, loot_peek)

    def _draw_header(self):
        floor = self.dungeon.get_floor()
        print("╔" + "═" * BOX_WIDTH + "╗")
        print("║" + "⚔  DUNGEON ROGUELIKE  ⚔".center(BOX_WIDTH) + "║")
        print("║" + f"— PISO {floor} —".center(BOX_WIDTH) + "║")
        print("╚" + "═" * BOX_WIDTH + "╝")

    def _draw_map(self, current_room: int):
        """
        Representación simple del mapa usando la matriz 2D.
        El integrante 4 expande esto con su implementación.
        """
        print("\n  [ MAPA ]")
        cols = 4
        ids  = self.dungeon.get_all_room_ids()
        for i, rid in enumerate(ids):
            if i % cols == 0:
                print("  ", end="")
            rtype = self.dungeon.get_room_type(rid)
            if rid == current_room:
                tile = TILE_ICONS["player"]
            elif self.dungeon.is_visited(rid):
                tile = TILE_ICONS.get(rtype, TILE_ICONS["unknown"])
            else:
                tile = TILE_ICONS["unknown"]
            print(f"{tile}", end=" ")
            if (i + 1) % cols == 0:
                print()
        print()

    def _draw_status(self, current_room: int, player_hp: int,
                    inventory: list, loot_peek):
        rtype = self.dungeon.get_room_type(current_room)
        rdesc = self.dungeon.get_room_desc(current_room)
        neighbors = self.dungeon.get_neighbors(current_room)
        floor = self.dungeon.get_floor()
        bar_filled = max(0, min(10, int((player_hp / 100) * 10)))
        hp_bar = "█" * bar_filled + "░" * (10 - bar_filled)

        print("─" * 40)
        print(f"  Piso #{floor}  |  Sala #{current_room}  [{rtype.upper()}]")
        print(f"  {rdesc}")
        print(f"  HP: [{hp_bar}] {player_hp}/100")
        print(f"  Ítem visible : {loot_peek if loot_peek else 'ninguno'}")
        print(f"  Inventario   : {inventory if inventory else '(vacío)'}")
        print(f"  Salidas      : {neighbors}")
        print("─" * 40)
