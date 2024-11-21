from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
import random
from Negotiation import NegotiationManager
from Toyota import ToyotaTrueno
from Ferrari import FerrariF40
from Microbus import Microbus
from TrafficLight import TrafficLight
from Vehicle import Vehicle


# ------------------------ La calle ------------------------
class Street(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

# ------------------------ Modelo ------------------------
class IntersectionModel(Model):
    def __init__(self, width, height, num_vehicles, num_microbuses, num_ferraris, num_speedsters):
        super().__init__()
        self.grid = MultiGrid(width, height, True)
        self.schedule = SimultaneousActivation(self)
        self.negotiation_manager = NegotiationManager()
        self.running = True

        # Inicializar agentes
        for i in range(num_vehicles):
            vehicle = Vehicle(f"vehicle_{i}", self, destination="north")
            self.grid.place_agent(vehicle, (random.randint(0, width - 1), random.randint(0, height - 1)))
            self.schedule.add(vehicle)
        
        for i in range(num_microbuses):
            microbus = Microbus(f"microbus_{i}", self)
            initial_position = (random.randint(0, width - 1), random.randint(0, height - 1))
            self.grid.place_agent(microbus, initial_position)
            self.schedule.add(microbus)


        for i in range(num_speedsters):
            speedster = ToyotaTrueno(f"speedster_{i}", self)
            self.grid.place_agent(speedster, (random.randint(0, width - 1), random.randint(0, height - 1)))
            self.schedule.add(speedster)

        for i in range(num_ferraris):
            ferrari = FerrariF40(f"ferrari_{i}", self)
            self.grid.place_agent(ferrari, (random.randint(0, width - 1), random.randint(0, height - 1)))
            self.schedule.add(ferrari)
        
        # Crear semáforo
        self.traffic_light = TrafficLight("traffic_light", self)
        center = (width // 2, height // 2)
        self.grid.place_agent(self.traffic_light, center)
        self.schedule.add(self.traffic_light)

    def step(self):
        # Gestionar interacciones entre agentes
        for agent_a, agent_b in self.get_interacting_agents():
            self.negotiation_manager.negotiate(agent_a, agent_b)
        
        # Avanzar la simulación
        self.schedule.step()

    def get_interacting_agents(self):
        """Encuentra pares de agentes que interactúan en la misma celda."""
        interactions = []
        for cell in self.grid.coord_iter():
            agents_in_cell = cell[0]
            if len(agents_in_cell) > 1:
                interactions.extend([(a, b) for a in agents_in_cell for b in agents_in_cell if a != b])
        return interactions