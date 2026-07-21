"""
save_manager.py
La idea clave es que la generación de cada piso es procedural pero
DETERMINISTA — depende únicamente de una semilla maestra y del
número de piso (ver main.build_floor). Por eso NO hace falta guardar
el mapa, el grafo ni el loot completo: basta con guardar
{master_seed, floor, player_hp, inventory} y, al continuar, el piso
se vuelve a generar exactamente igual a partir de esos cuatro datos.
Interfaz pública:
    save_manager.has_save()                                   → bool
    save_manager.save_game(master_seed, floor, hp, inventory)  → None
    save_manager.load_game()                                   → dict | None
    save_manager.delete_save()                                  → None
"""

import json
import os

SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "savegame.json")
REQUIRED_KEYS = {"master_seed", "floor", "player_hp", "inventory"}

def has_save() -> bool:
    """Indica si existe un archivo de partida guardada."""
    return os.path.isfile(SAVE_PATH)

def save_game(master_seed: int, floor: int, player_hp: int, inventory: list) -> None:
    """
    Guarda el checkpoint actual (siempre al INICIO de un piso).
    No guarda el mapa ni el loot recogido dentro del piso: al
    continuar, ese piso se regenera desde cero con la misma semilla,
    así que el checkpoint es "vuelves a empezar este piso, con el
    HP y el inventario que tenías al llegar a él".
    """
    data = {
        "master_seed": master_seed,
        "floor": floor,
        "player_hp": player_hp,
        "inventory": inventory,
    }
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"  ⚠ No se pudo guardar la partida: {e}")

def load_game() -> dict | None:
    """
    Carga el checkpoint guardado.
    Retorna None si no existe, o si el archivo está corrupto/incompleto
    (en ese caso también lo elimina para no volver a fallar).
    """
    if not has_save():
        return None
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not REQUIRED_KEYS.issubset(data.keys()):
            raise ValueError("El archivo de guardado no tiene todos los campos.")
        return data
    except (OSError, json.JSONDecodeError, ValueError, AttributeError, TypeError):
        print("  ⚠ El archivo de guardado está corrupto. Se descartará.")
        delete_save()
        return None

def delete_save() -> None:
    """
    Elimina la partida guardada.
    Se usa al morir (permadeath: no puedes reintentar el mismo piso
    con el guardado anterior) y opcionalmente al terminar el juego.
    """
    if has_save():
        try:
            os.remove(SAVE_PATH)
        except OSError:
            pass