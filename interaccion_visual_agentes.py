import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from interaccion_agentes import IntersectionModel, Vehicle, TrafficLight, Microbus, FerrariF40, ToyotaTrueno

# Configuración de la simulación
width = 20  # Ancho de la cuadrícula
height = 20  # Alto de la cuadrícula
num_vehicles = 2  # Número de vehículos
num_microbuses = 2  # Número de microbuses
num_ferraris = 2  # Número de Ferraris
num_speedsters = 2  # Número de Speedsters

# Crear el modelo de intersección
model = IntersectionModel(width, height, num_vehicles, num_microbuses, num_ferraris, num_speedsters)

# Crear el gráfico
fig, ax = plt.subplots(figsize=(8, 8))

# Colores para representar el estado del semáforo
semaforo_colors = {"yellow": "yellow", "green": "green", "red": "red"}

# Función para dibujar los carriles usando rectángulos
def draw_lanes():
    lane_color = "lightgray"
    
    # Dibujar carriles horizontales (en el eje y)
    for y in range(height):
        if y == height // 2 - 1 or y == height // 2 or y == height // 2 + 1:
            ax.add_patch(plt.Rectangle((0, y), width, 0.1, color=lane_color, zorder=1))

    # Dibujar carriles verticales (en el eje x)
    for x in range(width):
        if x == width // 2 - 1 or x == width // 2 or x == width // 2 + 1:
            ax.add_patch(plt.Rectangle((x, 0), 0.1, height, color=lane_color, zorder=1))

# Función para actualizar la visualización
def update(frame):
    # Realizar un paso de simulación
    model.step()

    # Limpiar la gráfica
    ax.clear()

    # Dibujar los carriles
    draw_lanes()

    # Dibujar las posiciones de los agentes
    vehicle_positions = [vehicle.pos for vehicle in model.schedule.agents if isinstance(vehicle, Vehicle)]
    microbus_positions = [microbus.pos for microbus in model.schedule.agents if isinstance(microbus, Microbus)]
    ferrari_positions = [ferrari.pos for ferrari in model.schedule.agents if isinstance(ferrari, FerrariF40)]
    speedster_positions = [speedster.pos for speedster in model.schedule.agents if isinstance(speedster, ToyotaTrueno)]
    traffic_light_position = model.traffic_light.pos

    # Dibujar los vehículos
    if vehicle_positions:
        vehicle_x, vehicle_y = zip(*vehicle_positions)
        ax.scatter(vehicle_x, vehicle_y, c="red", label="Vehículos", zorder=5)

    # Dibujar microbuses
    if microbus_positions:
        microbus_x, microbus_y = zip(*microbus_positions)
        ax.scatter(microbus_x, microbus_y, c="blue", label="Microbuses", zorder=5)

    # Dibujar Ferraris
    if ferrari_positions:
        ferrari_x, ferrari_y = zip(*ferrari_positions)
        ax.scatter(ferrari_x, ferrari_y, c="green", label="Ferraris", zorder=5)

    # Dibujar Speedsters
    if speedster_positions:
        speedster_x, speedster_y = zip(*speedster_positions)
        ax.scatter(speedster_x, speedster_y, c="purple", label="Speedsters", zorder=5)

    # Dibujar semáforo
    semaforo_state = model.traffic_light.state
    ax.add_patch(plt.Rectangle((traffic_light_position[0] - 0.5, traffic_light_position[1] - 0.5), 
                                1, 1, color=semaforo_colors[semaforo_state], label="Semáforo", zorder=10))

    # Título y leyenda
    ax.set_title(f"Paso {frame}")
    ax.legend(loc="upper left")

    # Limitar el rango para que no se mueva la vista
    ax.set_xlim(-1, width)
    ax.set_ylim(-1, height)

    ax.set_aspect('equal', adjustable='box')

# Crear la animación
ani = FuncAnimation(fig, update, frames=50, interval=500)

# Mostrar la animación
plt.show()
