"""
loot_stack.py - Módulo 3 (Integrante 3)
El integrante 3 reemplaza este archivo con su implementación real
Interfaz esperada por main.py:
    loot = LootStack(dungeon)
    item = loot.peek(room_id)       → str | None
    item = loot.pick_up(room_id)    → str
    lista = loot.get_all(room_id)   → list[str]
"""

import random

LOOT_TABLE = {
    "chest":  ["Espada legendaria", "Poción mayor", "Escudo de hierro", "Llave maestra"],
    "enemy":  ["Monedas", "Poción débil", "Fragmento de hueso"],
    "elite":  ["Reliquia menor", "Poción mayor", "Arma rara", "Monedas de élite"],
    "normal": ["Antorcha", "Vendaje", "Monedas"],
    "boss":   [],
    "start":  [],
}

# Objetos raros que se suman a los cofres a partir de cierto piso
RARE_LOOT = ["Gema de poder", "Anillo del abismo", "Fragmento legendario"]
RARE_LOOT_MIN_FLOOR = 3

class LootStack:
    def __init__(self, dungeon):
        self.stacks: dict[int, list[str]] = {}
        self.floor = dungeon.get_floor()
        self._populate(dungeon)

    def _populate(self, dungeon):
        for room_id in dungeon.get_all_room_ids():
            room_type = dungeon.get_room_type(room_id)
            tabla = list(LOOT_TABLE.get(room_type, []))

            # Cofres en pisos profundos pueden tener objetos raros
            if room_type == "chest" and self.floor >= RARE_LOOT_MIN_FLOOR:
                tabla += RARE_LOOT

            if not tabla:
                self.stacks[room_id] = []
                continue

            if room_type == "elite":
                # Las salas de élite siempre premian con al menos 1 ítem
                n = random.randint(1, min(2, len(tabla)))
            else:
                n = random.randint(0, min(2, len(tabla)))

            self.stacks[room_id] = random.sample(tabla, n)

    def peek(self, room_id: int):
        """Ver el ítem del tope sin sacarlo. Retorna None si está vacía."""
        stack = self.stacks.get(room_id, [])
        return stack[-1] if stack else None

    def pick_up(self, room_id: int) -> str:
        """Saca y retorna el ítem del tope (pop). LIFO."""
        stack = self.stacks.get(room_id, [])
        if stack:
            return stack.pop()
        return "No hay nada que recoger."

    def get_all(self, room_id: int) -> list[str]:
        """Retorna todos los ítems de la sala sin modificar la pila."""
        return list(self.stacks.get(room_id, []))