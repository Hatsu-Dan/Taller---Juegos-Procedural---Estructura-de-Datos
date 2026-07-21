"""
main.py
Autor: Christian Correa
Punto de entrada del juego. Orquesta los 4 módulos:
    - DungeonGraph  → genera el mapa (grafo no dirigido)
    - Pathfinder    → BFS y DFS sobre el grafo
    - LootStack     → pila de ítems por sala
    - Renderer      → visualización en consola (matriz 2D)
"""

import sys
import time
import random
from dungeon_graph import DungeonGraph
from pathfinder   import Pathfinder
from loot_stack   import LootStack
from renderer     import Renderer
import save_manager

#  Configuración del juego
PLAYER_MAX_HP          = 100
ROOMS_BASE             = 8    # salas del piso 1
ROOMS_PER_FLOOR        = 2    # salas extra por cada piso adicional
ROOMS_MAX              = 20   # tope para que el mapa no crezca sin límite
ENEMY_DAMAGE_BASE      = 15
ENEMY_DAMAGE_PER_FLOOR = 3    # los enemigos pegan más fuerte en pisos altos
ELITE_DAMAGE_BONUS     = 15   # daño extra si la sala es "elite"
HEAL_ON_FLOOR_CLEAR    = 30   # HP recuperado al derrotar al jefe de piso

# Ítems curativos que pueden encontrarse explorando (loot_stack.py) y
# cuánto HP recupera cada uno al ser usado con el comando "u".
HEALING_ITEMS = {
    "Poción mayor": 50,
    "Poción débil": 20,
    "Vendaje":       15,
}

def rooms_for_floor(floor: int) -> int:
    """Cuántas salas tiene el piso N (crece y luego se topa en ROOMS_MAX)."""
    return min(ROOMS_BASE + (floor - 1) * ROOMS_PER_FLOOR, ROOMS_MAX)

def enemy_damage_for_floor(floor: int, room_type: str) -> int:
    """Daño de una sala de enemigo/elite, escalado por piso."""
    dmg = ENEMY_DAMAGE_BASE + (floor - 1) * ENEMY_DAMAGE_PER_FLOOR
    if room_type == "elite":
        dmg += ELITE_DAMAGE_BONUS
    return dmg

#  Pantallas de inicio / progreso / fin
def screen_title():
    print("\033[H\033[J", end="")
    print("""
    ╔══════════════════════════════════════════╗
    ║                                          ║
    ║       ⚔   DUNGEON ROGUELIKE   ⚔          ║
    ║    Generador de Mazmorras en Python      ║
    ║                                          ║
    ║    Estructuras de datos usadas:          ║
    ║      - Grafo no dirigido (DungeonGraph)  ║
    ║      - Cola deque        (Pathfinder)    ║
    ║      - Pila list         (LootStack)     ║
    ║      - Matriz 2D         (Renderer)      ║
    ║                                          ║
    ║    Ahora con PISOS INFINITOS             ║
    ║                                          ║
    ╚══════════════════════════════════════════╝
    """)

def screen_main_menu() -> str:
    """
    Si hay una partida guardada, deja elegir entre nueva partida o
    continuar. Si no hay ninguna, solo pide ENTER para empezar.
    Retorna "new" o "continue".
    """
    if not save_manager.has_save():
        input("  Presiona ENTER para comenzar...")
        return "new"

    print("  Se encontró una partida guardada.\n")
    print("    1. Nueva partida")
    print("    2. Continuar partida guardada")
    while True:
        choice = input("\n  > ").strip()
        if choice == "1":
            return "new"
        if choice == "2":
            return "continue"
        print("  Opción inválida. Escribe 1 o 2.")

def screen_floor_intro(floor: int, n_rooms: int):
    print("\033[H\033[J", end="")
    print(f"""
    ╔══════════════════════════════════════════╗
    ║                                          ║
    ║              PISO {floor:<3}                    ║
    ║       {n_rooms} salas te esperan...             ║
    ║                                          ║
    ╚══════════════════════════════════════════╝
    """)
    input("  Presiona ENTER para descender...")

def screen_floor_clear(floor: int, route_taken: list, player_hp: int, reward: str):
    print("\033[H\033[J", end="")
    print(f"""
    ╔══════════════════════════════════════════╗
    ║                                          ║
    ║   ★  ¡PISO {floor} SUPERADO!  ★                ║
    ║                                          ║
    ╚══════════════════════════════════════════╝
    """)
    print(f"  Ruta recorrida : {' → '.join(str(r) for r in route_taken)}")
    print(f"  HP restante    : {player_hp}/{PLAYER_MAX_HP}")
    print(f"  Recompensa     : {reward}")
    print(f"  Descansas un momento... (+{HEAL_ON_FLOOR_CLEAR} HP)")
    print()
    input("  [ENTER para continuar al siguiente piso]")

def screen_death(floor: int, inventory: list):
    print("\033[H\033[J", end="")
    print("""
    ╔══════════════════════════════════════════╗
    ║                                          ║
    ║   ✝  HAS MUERTO EN EL DUNGEON            ║
    ║   La oscuridad te ha consumido.          ║
    ║                                          ║
    ╚══════════════════════════════════════════╝
    """)
    print(f"  Llegaste hasta el piso {floor}.")
    print(f"  Objetos recolectados: {len(inventory)}")
    print()

#  Comandos del juego
def print_commands(neighbors: list):
    print("\n  COMANDOS:")
    print(f"    [número]  → Mover a sala  {neighbors}")
    print("    r         → Recoger ítem de esta sala")
    print("    u         → Usar poción o vendaje")
    print("    i         → Ver inventario completo")
    print("    ruta      → Mostrar ruta más corta al jefe (BFS)")
    print("    mapa      → Imprimir mapa del grafo")
    print("    q         → Salir del juego")
    print()

def handle_move(choice: str, current_room: int,
                dungeon: DungeonGraph) -> int | None:
    """Intenta mover al jugador. Retorna el nuevo room_id o None si inválido."""
    try:
        target = int(choice)
    except ValueError:
        print(f"  ✗ Comando no reconocido: '{choice}'. "
            "Escribe el número de una sala o uno de los comandos listados.")
        time.sleep(1.2)
        return None

    neighbors = dungeon.get_neighbors(current_room)
    if target in neighbors:
        return target

    print(f"  ✗ La sala {target} no está conectada a esta. "
        f"Salas disponibles: {neighbors}")
    time.sleep(1.2)
    return None

def handle_use_item(player_hp: int, inventory: list) -> int:
    """
    Permite al jugador consumir una poción o vendaje de su inventario
    para recuperar HP. Si hay varios ítems usables, deja elegir cuál.
    Retorna el player_hp actualizado (el inventario se modifica in-place).
    """
    usables = [item for item in inventory if item in HEALING_ITEMS]

    if not usables:
        print("\n  No tienes pociones ni vendajes para usar.")
        time.sleep(1.2)
        return player_hp

    if player_hp >= PLAYER_MAX_HP:
        print("\n  Ya tienes la vida al máximo, no hace falta curarte.")
        time.sleep(1.2)
        return player_hp

    print("\n  ── OBJETOS USABLES ──────────────")
    for idx, item in enumerate(usables, 1):
        print(f"    {idx}. {item}  (+{HEALING_ITEMS[item]} HP)")
    print("    0. Cancelar")
    print("  ─────────────────────────────────")

    choice = input("  > ").strip()
    if choice in ("0", ""):
        return player_hp

    try:
        sel = int(choice)
        if not (1 <= sel <= len(usables)):
            raise ValueError
    except ValueError:
        print("\n  Opción inválida.")
        time.sleep(1.0)
        return player_hp

    item = usables[sel - 1]
    heal = HEALING_ITEMS[item]
    inventory.remove(item)          # saca solo esa copia del ítem
    nuevo_hp = min(PLAYER_MAX_HP, player_hp + heal)
    ganado = nuevo_hp - player_hp
    print(f"\n  ✔ Usaste {item}. Recuperas {ganado} HP. "
        f"({nuevo_hp}/{PLAYER_MAX_HP})")
    time.sleep(1.2)
    return nuevo_hp

def handle_enemy(room_id: int, player_hp: int,
                dungeon: DungeonGraph, floor: int) -> int:
    """Aplica daño si la sala es de tipo 'enemy' o 'elite' (escalado por piso)."""
    room_type = dungeon.get_room_type(room_id)
    if room_type in ("enemy", "elite") and not dungeon.is_visited(room_id):
        dmg = enemy_damage_for_floor(floor, room_type)
        etiqueta = "¡Enemigo de élite!" if room_type == "elite" else "¡Enemigo!"
        print(f"\n  ⚠  {etiqueta} Recibes {dmg} de daño.")
        time.sleep(1.2)
        player_hp = max(0, player_hp - dmg)
    return player_hp

#  Game loop principal
def game_loop(dungeon: DungeonGraph, pathfinder: Pathfinder,
            loot: LootStack, renderer: Renderer,
            player_hp: int, inventory: list, floor: int):
    """
    Bucle principal del juego para UN piso.
    Retorna (resultado, player_hp, inventory, route_taken)
    donde resultado ∈ {"won", "died", "quit"}.
    """
    current_room  = dungeon.start_room
    route_taken   = [current_room]
    dungeon.mark_visited(current_room)

    while True:
        # Dibujar estado actual
        loot_peek = loot.peek(current_room)
        renderer.draw(current_room, player_hp, inventory, loot_peek)
        print_commands(dungeon.get_neighbors(current_room))

        # Verificar muerte
        if player_hp <= 0:
            return "died", player_hp, inventory, route_taken

        # Verificar victoria del piso
        if current_room == dungeon.boss_room:
            return "won", player_hp, inventory, route_taken

        # Leer input
        try:
            choice = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  Saliendo...")
            return "quit", player_hp, inventory, route_taken

        if choice == "q":
            print("\n  Hasta la próxima, aventurero.")
            return "quit", player_hp, inventory, route_taken

        # Recoger ítem
        elif choice == "r":
            item = loot.pick_up(current_room)
            if item != "No hay nada que recoger.":
                inventory.append(item)
                print(f"\n  ✔ Recogiste: {item}")
            else:
                print(f"\n  {item}")
            time.sleep(1.0)

        # Usar poción / vendaje
        elif choice == "u":
            player_hp = handle_use_item(player_hp, inventory)

        # Ver inventario
        elif choice == "i":
            print("\n  ── INVENTARIO ──────────────────")
            if inventory:
                for idx, it in enumerate(inventory, 1):
                    tag = f"  (usable, +{HEALING_ITEMS[it]} HP)" if it in HEALING_ITEMS else ""
                    print(f"    {idx}. {it}{tag}")
            else:
                print("    (vacío)")
            print("  ────────────────────────────────")
            input("  [ENTER para continuar]")

        # Mostrar ruta al jefe (BFS)
        elif choice == "ruta":
            ruta = pathfinder.bfs(current_room, dungeon.boss_room)
            if ruta:
                print(f"\n  Ruta más corta al jefe: "
                    f"{' → '.join(str(r) for r in ruta)}")
            else:
                print("\n  No se encontró ruta al jefe desde aquí.")
            input("  [ENTER para continuar]")

        # Imprimir mapa del grafo
        elif choice == "mapa":
            dungeon.print_graph()
            input("  [ENTER para continuar]")

        # Mover
        else:
            new_room = handle_move(choice, current_room, dungeon)
            if new_room is not None:
                current_room = new_room
                route_taken.append(current_room)

                # Daño de enemigo al entrar
                player_hp = handle_enemy(current_room, player_hp, dungeon, floor)
                dungeon.mark_visited(current_room)

def build_floor(floor: int, master_seed: int):
    """
    Genera un piso jugable garantizando que el jefe sea alcanzable.
    Reseedea random.seed(master_seed + floor) antes de generar, así
    que para un mismo (master_seed, floor) siempre sale exactamente
    el mismo mapa y el mismo loot — esto es lo que permite guardar
    solo 4 números/strings y reconstruir la partida después.
    Retorna (dungeon, pathfinder, loot, renderer, reachable).
    """
    random.seed(master_seed + floor)
    n_rooms = rooms_for_floor(floor)
    while True:
        dungeon = DungeonGraph()
        dungeon.generate(n=n_rooms, floor=floor)
        pathfinder = Pathfinder(dungeon)
        reachable  = pathfinder.dfs(dungeon.start_room)
        if dungeon.boss_room in reachable:
            break
        # En el caso muy raro de que el jefe no sea alcanzable, regenerar
        # (sigue consumiendo la misma secuencia semillada, así que el
        # resultado final para este (master_seed, floor) sigue siendo
        # reproducible de punta a punta)

    loot     = LootStack(dungeon)
    renderer = Renderer(dungeon)
    return dungeon, pathfinder, loot, renderer, reachable

def run_game(master_seed: int, floor: int, player_hp: int, inventory: list) -> None:
    """
    Corre pisos consecutivos a partir de un checkpoint dado
    (master_seed, floor, player_hp, inventory).
    Autoguarda al llegar a cada piso. Si el jugador muere, borra el
    guardado (permadeath). Si el jugador sale con "q", el guardado
    del último checkpoint queda intacto para continuar después.
    """
    while True:  # cada vuelta = un piso
        dungeon, pathfinder, loot, renderer, reachable = build_floor(floor, master_seed)

        # Checkpoint: se guarda el inicio de este piso, antes de jugarlo
        save_manager.save_game(master_seed, floor, player_hp, inventory)
        screen_floor_intro(floor, dungeon.room_count())

        # Demo del mapa antes de jugar (útil para la presentación)
        print("\033[H\033[J", end="")
        dungeon.print_graph()
        ruta_optima = pathfinder.bfs(dungeon.start_room, dungeon.boss_room)
        print(f"  Ruta óptima al jefe (BFS): "
            f"{' → '.join(str(r) for r in ruta_optima)}")
        print(f"  Salas accesibles (DFS)   : {sorted(reachable)}")
        input("\n  [ENTER para empezar a jugar]")

        # Jugar el piso
        result, player_hp, inventory, route_taken = game_loop(
            dungeon, pathfinder, loot, renderer, player_hp, inventory, floor
        )

        if result == "won":
            reward = f"Reliquia del Piso {floor}"
            inventory.append(reward)
            player_hp = min(PLAYER_MAX_HP, player_hp + HEAL_ON_FLOOR_CLEAR)
            screen_floor_clear(floor, route_taken, player_hp, reward)
            floor += 1
            continue  # ↓ al siguiente piso, con el mismo HP/inventario

        elif result == "died":
            screen_death(floor, inventory)
            save_manager.delete_save()  # permadeath: no se puede reintentar el piso
            return

        elif result == "quit":
            print(f"\n  Progreso guardado (piso {floor}). ¡Hasta la próxima!\n")
            sys.exit(0)

#  Entrada principal
def main():
    while True:  # cada vuelta = una partida completa
        screen_title()
        choice = screen_main_menu()
        data = save_manager.load_game() if choice == "continue" else None

        if data is not None:
            master_seed = data["master_seed"]
            floor       = data["floor"]
            player_hp   = data["player_hp"]
            inventory   = data["inventory"]
        else:
            master_seed = random.randint(1, 2**31 - 1)
            floor, player_hp, inventory = 1, PLAYER_MAX_HP, []

        run_game(master_seed, floor, player_hp, inventory)

        # Solo se llega aquí si el jugador murió (quit hace sys.exit antes)
        again = input("  ¿Jugar de nuevo? (s/n): ").strip().lower()
        if again != "s":
            print("\n  ¡Gracias por jugar!\n")
            sys.exit(0)

if __name__ == "__main__":
    main()