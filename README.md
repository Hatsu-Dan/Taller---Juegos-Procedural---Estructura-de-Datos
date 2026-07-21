# 🗡️ Dungeon Roguelike — Guía de Funciones

Este documento explica **qué hace cada archivo y cada función** del proyecto,
en lenguaje simple. Está pensado para exponer el proyecto o para explicárselo
a alguien que recién está aprendiendo a programar.

## 1. La idea general

El juego es una mazmorra generada por computadora. El jugador entra, se mueve
entre salas, recoge objetos, esquiva o enfrenta enemigos y busca al jefe.
Al vencerlo, baja a un piso más difícil. Todo el proyecto está dividido en
**5 archivos**, cada uno responsable de una sola cosa (esto se llama
*separación de responsabilidades*):

| Archivo | Rol | Estructura de datos que enseña |
|---|---|---|
| `dungeon_graph.py` | Crea el mapa de la mazmorra | **Grafo no dirigido** |
| `pathfinder.py` | Encuentra caminos dentro del mapa | **Cola (BFS)** y **Pila (DFS)** |
| `loot_stack.py` | Maneja los objetos de cada sala | **Pila (LIFO)** |
| `renderer.py` | Dibuja todo en la consola | **Matriz 2D** |
| `save_manager.py` | Guarda y carga la partida | Archivos / JSON |
| `main.py` | Conecta todos los módulos y corre el juego | Orquestación |

Una buena forma de explicarlo en una exposición: **cada estructura de datos
que se enseña en clase tiene un trabajo real y visible dentro del juego.**
No son ejercicios sueltos, son piezas que se necesitan entre sí.

---

## 2. `dungeon_graph.py` — El mapa (Grafo)

**Analogía para explicar:** un grafo es como un mapa de estaciones de metro:
las salas son las estaciones (nodos) y los pasillos son las vías (aristas).
Que sea "no dirigido" significa que si puedes ir de la sala A a la B,
también puedes volver de la B a la A.

### `class Room`
Una "ficha" con los datos de una sala: su `type` (tipo), su `desc`
(descripción) y si ya fue `visited` (visitada). Antes esto era un
diccionario suelto; usar una clase evita errores de tipeo en las claves.

### `class DungeonGraph`

| Función | Qué hace | Se explica como... |
|---|---|---|
| `__init__(self)` | Prepara el grafo vacío (sin salas ni conexiones todavía) | El constructor, arranca todo en cero |
| `generate(self, n, floor)` | Crea el mapa completo: decide cuántas salas hay, qué tipo es cada una, y las conecta | El "generador procedural" — la magia que arma un mapa distinto cada vez |
| `_reset(self)` | Borra el mapa anterior antes de crear uno nuevo | Limpieza interna (por eso empieza con `_`, es de uso privado) |
| `_assign_types(self, n, floor)` | Decide qué sala es `start`, cuál es `boss`, y reparte el resto (normal, cofre, enemigo, élite) según qué tan profundo esté el piso | Reparte "cartas" de tipos de sala |
| `_add_room(self, room_id, room_type)` | Registra una sala nueva en el grafo con su descripción | Agrega un nodo |
| `_connect(self, room_a, room_b)` | Crea un pasillo entre dos salas, en ambos sentidos | Agrega una arista (no dirigida) |
| `_add_extra_connections(self, count)` | Agrega conexiones extra para que el mapa no sea un simple camino recto, sino que tenga rutas alternativas | Le da "forma de laberinto" real al grafo |
| `get_neighbors(self, room_id)` | Devuelve la lista de salas conectadas a una sala dada | "¿A dónde puedo ir desde aquí?" |
| `get_room_type(self, room_id)` | Devuelve el tipo de una sala (`chest`, `enemy`, etc.) | Consulta de dato |
| `get_room_desc(self, room_id)` | Devuelve el texto descriptivo de una sala | Consulta de dato |
| `mark_visited(self, room_id)` | Marca una sala como ya explorada | Actualiza estado |
| `is_visited(self, room_id)` | Pregunta si una sala ya fue visitada | Consulta de estado |
| `is_valid_room(self, room_id)` | Pregunta si un número de sala existe en el grafo | Validación |
| `room_count(self)` | Cuenta cuántas salas tiene el piso actual | Utilidad |
| `get_all_room_ids(self)` | Devuelve la lista de IDs de todas las salas | Usada por otros módulos para recorrer el mapa sin tocar sus datos internos |
| `get_floor(self)` | Devuelve en qué piso está el jugador | Consulta de dato |
| `print_graph(self)` | Imprime el grafo completo en consola (para debug o demo) | Visualización rápida en texto |

**Punto clave para exponer:** el paso 3 de `generate()` (conectar cada sala
nueva con una sala anterior al azar) es lo que **garantiza matemáticamente**
que el grafo sea conexo — es decir, que siempre exista un camino de la
entrada al jefe. Eso es un **árbol generador aleatorio**.

---

## 3. `pathfinder.py` — Cómo moverse por el mapa (BFS y DFS)

**Analogía para explicar:** si el grafo es el mapa del metro, el Pathfinder
es "Google Maps": te dice cómo llegar de una estación a otra.

### `class Pathfinder`

| Función | Qué hace | Se explica como... |
|---|---|---|
| `__init__(self, dungeon)` | Guarda una referencia al mapa sobre el que va a buscar caminos | Constructor |
| `bfs(self, start, goal)` | **Breadth-First Search** (búsqueda en anchura): encuentra el camino **más corto** entre dos salas, explorando "capa por capa" con una **cola** (`deque`) | "¿Cuál es la ruta más rápida al jefe?" |
| `dfs(self, start)` | **Depth-First Search** (búsqueda en profundidad): encuentra **todas** las salas a las que se puede llegar desde una sala, usando una **pila** | "¿El mapa está completo/conectado? ¿A dónde puedo llegar en total?" |

**Punto clave para exponer:** BFS y DFS visitan el grafo de formas distintas
solo por *cómo sacan el siguiente elemento a revisar*:
- BFS usa una **cola** (`queue.popleft()` → FIFO, el primero en entrar es el
  primero en salir) → por eso encuentra el camino más corto.
- DFS usa una **pila** (`stack.pop()` → LIFO, el último en entrar es el
  primero en salir) → por eso se "mete" lo más profundo posible antes de
  volver.

En `main.py`, BFS se usa para mostrarle al jugador la ruta óptima al jefe,
y DFS se usa al generar cada piso para comprobar que el jefe sea alcanzable
(si no lo es, el piso se regenera).

---

## 4. `loot_stack.py` — Los objetos de cada sala (Pila)

**Analogía para explicar:** una pila es como una **torre de platos**: solo
puedes sacar el plato de arriba (`pop`). Aquí, cada sala tiene su propia
"torrecita" de objetos.

### `class LootStack`

| Función | Qué hace | Se explica como... |
|---|---|---|
| `__init__(self, dungeon)` | Recibe el mapa y llama a `_populate` para repartir el loot inicial | Constructor |
| `_populate(self, dungeon)` | Recorre todas las salas del mapa y decide qué objetos le tocan a cada una, según su tipo y el piso (los cofres desde el piso 3 pueden tener objetos raros; las salas élite siempre dan al menos 1 ítem) | El "repartidor" de objetos |
| `peek(self, room_id)` | Muestra el ítem que está *arriba de la pila* de una sala, **sin sacarlo** | "¿Qué hay en esta sala?" (solo mirar) |
| `pick_up(self, room_id)` | Saca (`pop`) el ítem de arriba de la pila y lo entrega al jugador | Recoger de verdad (esto modifica la pila) |
| `get_all(self, room_id)` | Devuelve una copia de **todos** los objetos que quedan en una sala, sin sacarlos | Ver el contenido completo, por ejemplo para debug |

**Punto clave para exponer:** por qué una pila y no una lista cualquiera:
usar `pop()` fuerza a que solo se pueda sacar un objeto a la vez y en un
orden concreto (LIFO), lo cual es exactamente el comportamiento que
queremos: "recoges el objeto que está arriba, uno por uno".

**Nota de diseño:** `LootStack` **nunca** lee `dungeon.rooms` directamente,
solo usa los métodos públicos de `DungeonGraph` (`get_all_room_ids`,
`get_room_type`). Esto es importante para exponer: si el equipo cambia cómo
se guarda una sala por dentro, este archivo no se rompe.

---

## 5. `renderer.py` — Dibujar todo en pantalla (Matriz 2D)

**Analogía para explicar:** el renderer es como el **tablero de un juego de
mesa**: toma los datos del mapa y los "dibuja" como una cuadrícula de
casillas (`[X]`, `[E]`, `[$]`...), acomodadas en filas y columnas — eso es
una matriz 2D, aunque aquí se construye fila por fila con un contador
(`cols = 4`) en vez de una lista de listas.

### `class Renderer`

| Función | Qué hace | Se explica como... |
|---|---|---|
| `__init__(self, dungeon)` | Guarda una referencia al mapa que va a dibujar | Constructor |
| `draw(self, current_room, player_hp, inventory, loot_peek)` | Limpia la consola y llama, en orden, a header → mapa → estado. Es la única función que el resto del juego necesita llamar | El "botón de refrescar pantalla" |
| `_draw_header(self)` | Imprime el título del juego y el número de piso actual | Encabezado |
| `_draw_map(self, current_room)` | Recorre todas las salas (`get_all_room_ids`) y dibuja un ícono por cada una: el jugador (`[@]`), salas visitadas (según su tipo) o salas no visitadas (`[?]`) — acomodadas en una cuadrícula de 4 columnas | La "matriz visual" del dungeon |
| `_draw_status(self, current_room, player_hp, inventory, loot_peek)` | Imprime el panel inferior: piso, sala actual, descripción, barra de HP (acotada siempre a 10 segmentos, sin importar el valor de `player_hp`), objeto visible, inventario y salidas disponibles | El "HUD" (interfaz de estado) del juego |

**Punto clave para exponer:** las salas que el jugador *no ha visitado
todavía* siempre se dibujan como `[?]`, aunque el programa ya sepa qué
tipo son — así el mapa se va "revelando" a medida que se explora, en vez de
mostrar todo desde el principio.

---

## 6. `save_manager.py` — Guardar y continuar la partida

**Analogía para explicar:** en vez de guardar una "foto" gigante de todo el
mapa y el loot, el juego guarda algo mucho más simple: **la receta para
volver a generar exactamente lo mismo**. Como el mapa se genera con una
semilla (`random.seed`), guardar solo 4 datos alcanza para reconstruir todo
el piso byte por byte.

| Función | Qué hace | Se explica como... |
|---|---|---|
| `has_save()` | Pregunta si existe un archivo de guardado en disco | "¿Hay una partida guardada?" |
| `save_game(master_seed, floor, player_hp, inventory)` | Escribe esos 4 datos en un archivo `savegame.json` | Guardar partida |
| `load_game()` | Lee el archivo de guardado y lo devuelve como diccionario. Si el archivo está roto, incompleto, o ni siquiera es un diccionario válido, lo borra y avisa (nunca deja que un guardado corrupto tumbe el juego) | Cargar partida (con manejo de errores) |
| `delete_save()` | Borra el archivo de guardado (se usa al morir, porque el juego es *permadeath*) | Borrar partida |

**Punto clave para exponer:** esto es un ejemplo real de por qué la
generación **determinista** (semilla + piso siempre dan el mismo mapa) es
útil más allá de la reproducibilidad: permite guardar partidas larguísimas
en un archivo de un par de líneas.

---

## 7. `main.py` — El director de orquesta

Este archivo no inventa estructuras de datos nuevas: su trabajo es **usar
los otros cuatro módulos en el orden correcto** para que el juego funcione,
y llevar el estado del jugador (HP, inventario, piso) entre pisos.

### Configuración y cálculos de dificultad

| Función | Qué hace |
|---|---|
| `rooms_for_floor(floor)` | Calcula cuántas salas debe tener un piso (crece con el piso, hasta un tope de `ROOMS_MAX`) |
| `enemy_damage_for_floor(floor, room_type)` | Calcula el daño de una sala de enemigo/élite, más alto mientras más profundo sea el piso |

### Pantallas (solo imprimen texto, no cambian el estado del juego)

| Función | Qué hace |
|---|---|
| `screen_title()` | Muestra la pantalla de bienvenida con el arte ASCII |
| `screen_main_menu()` | Pregunta si el jugador quiere una partida nueva o continuar una guardada |
| `screen_floor_intro(floor, n_rooms)` | Muestra el cartel de "vas a entrar al piso N" |
| `screen_floor_clear(floor, route_taken, player_hp, reward)` | Muestra el resumen al vencer al jefe de un piso: ruta recorrida, HP y recompensa |
| `screen_death(floor, inventory)` | Muestra la pantalla de "Game Over" |

### Comandos del jugador (cambian el estado del juego)

| Función | Qué hace |
|---|---|
| `print_commands(neighbors)` | Imprime la lista de comandos disponibles y las salas vecinas a las que se puede mover |
| `handle_move(choice, current_room, dungeon)` | Valida si el número que escribió el jugador es una sala vecina válida; si sí, devuelve esa sala. Si no —ya sea porque no es un número o porque no es una sala vecina— avisa el error en pantalla y devuelve `None` |
| `handle_use_item(player_hp, inventory)` | Deja al jugador elegir una poción o vendaje de su inventario (`HEALING_ITEMS`) para curarse; respeta el tope de HP y quita el ítem usado del inventario |
| `handle_enemy(room_id, player_hp, dungeon, floor)` | Si la sala a la que entraste es de tipo `enemy` o `elite` y era la primera vez que entrabas, resta HP según `enemy_damage_for_floor`, sin dejar que el HP baje de 0 |

### El corazón del juego

| Función | Qué hace |
|---|---|
| `game_loop(dungeon, pathfinder, loot, renderer, player_hp, inventory, floor)` | El **bucle principal de un piso**: dibuja pantalla, revisa si moriste o ganaste, lee el comando del jugador (`r`, `u`, `i`, `ruta`, `mapa`, moverse, `q`) y actúa en consecuencia. Termina devolviendo si el resultado fue `"won"`, `"died"` o `"quit"` |
| `build_floor(floor, master_seed)` | Genera un piso completo: fija la semilla, crea el `DungeonGraph`, el `Pathfinder`, el `LootStack` y el `Renderer`, y si el jefe queda inalcanzable, **regenera** el piso hasta que sí lo sea |
| `run_game(master_seed, floor, player_hp, inventory)` | El **bucle de pisos**: arma un piso, lo autoguarda, lo juega con `game_loop`, y según el resultado sube de piso, termina en muerte (borrando el guardado) o guarda y sale |

### Punto de entrada

| Función | Qué hace |
|---|---|
| `main()` | Muestra el título, pregunta si es partida nueva o continuar, carga los datos con `save_manager` si corresponde, y llama a `run_game`. Al volver de una muerte, pregunta si quiere jugar de nuevo |

**Punto clave para exponer:** `main.py` casi no tiene lógica propia de
"reglas del juego" — su trabajo es **coordinar**. Esto es justamente el
patrón de diseño que se quiere enseñar: cada módulo hace una sola cosa bien,
y `main.py` los conecta.

---

## 8. Cómo correr el juego

```bash
python main.py
```

Todos los archivos (`dungeon_graph.py`, `pathfinder.py`, `loot_stack.py`,
`renderer.py`, `save_manager.py`, `main.py`) deben estar en la misma
carpeta.
