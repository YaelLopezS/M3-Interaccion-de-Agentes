from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
import random

# ------------------------ Agente semaforo ------------------------

class TrafficLight(Agent):
    """
    Este es nuestro agente semaforo, el cual recibe la informacion del auto mas proximo a llegar y da una secuencia de luces para que los vehiculos pasen.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = "yellow"
        self.color = "yellow"
        self.waiting_vehicles = []
        self.light_cycle = ["north", "south", "east", "west"]
        self.cycle_index = 0
        self.saturated = False

    def recibir_mensaje(self, vehicle):
        self.waiting_vehicles.append((vehicle, vehicle.arrival_time))
        if len(self.waiting_vehicles) > 5:
            self.saturated = True

    def make_decision(self):
        """
        Toma la decisión sobre el estado del semáforo según la información de los vehículos cercanos.
        """
        if not self.waiting_vehicles:
            # Si no hay vehículos cercanos, luz amarilla
            self.state = "yellow"
            self.color = "yellow"
            return

        # Identificar el vehículo más cercano (menor tiempo de arribo)
        nearest_vehicle, _ = min(self.waiting_vehicles, key=lambda x: x[1])
        
        if self.saturated:
            # Si el semáforo está saturado, alterna entre rojo y verde
            self.state = "green" if self.state == "red" else "red"
            self.color = self.state
            self.cycle_index = (self.cycle_index + 1) % len(self.light_cycle)
        else:
            # Dar luz verde al vehículo más cercano y establecer el programa de luces
            self.state = "green"
            self.color = "green"
            self.cycle_index = self.light_cycle.index(nearest_vehicle.destination)
            # Eliminar el vehículo procesado de la lista
            self.waiting_vehicles.remove((nearest_vehicle, nearest_vehicle.arrival_time))

    def step(self):
        """
        Método de actualización del agente en cada paso de la simulación.
        """
        self.make_decision()