from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
import random


#  ------------------------ Agente Microbús ------------------------
class Microbus(Agent):
    """
    Este es el agente de microbús, un híbrido entre reactivo y deliberativo.
    Optimiza la recogida de pasajeros, utiliza estrategias deliberativas y cambia de carril rápidamente según el tráfico.
    """
    def __init__(self, unique_id, model, state="normal"):
        super().__init__(unique_id, model)
        self.state = state
        self.passengers = 0
        self.speed = 1
        self.destination = None
        self.route = []
        self.pickup_points = []
        self.at_pickup = False
        self.possible_states = ["normal", "happy", "angry"]
        self.decision = None

    def step(self):
        self.perceive_environment()
        self.make_decision()
        self.act()

    # Componente Reactivo
    def perceive_environment(self):
        """Detecta pasajeros o evalúa posibles bloqueos para cambiar de carril."""
        x, y = self.pos
        neighbors = self.model.grid.get_neighbors((x, y), moore=False, include_center=False)

        # Evalúa si hay pasajeros en la vía
        for neighbor in neighbors:
            if isinstance(neighbor, Passenger):
                self.at_pickup = True
                self.pickup_points.append(neighbor)

        # Cambia de carril si hay bloqueo
        if self.state == "angry":
            self.change_lane()

    # Componente Deliberativo
    def make_decision(self):
        """Planifica la ruta según el tráfico y optimiza el tiempo."""
        if not self.route:
            self.plan_route()

        if self.at_pickup:
            self.state = "happy"
            self.decision = "cede"
        elif len(self.pickup_points) > 3:
            self.state = "angry"
            self.decision = "compite"
        else:
            self.state = "normal"
            self.decision = "cede"
        return self.decision

    def plan_route(self):
        """Define una ruta óptima basada en paradas y tráfico."""
        # Generar una ruta ficticia considerando paradas y tráfico.
        grid_width, grid_height = self.model.grid.width, self.model.grid.height
        self.route = [(grid_width // 2, grid_height - 1), (0, grid_height // 2), (grid_width - 1, 0)]
        self.destination = self.route.pop(0)

    # Acciones
    def act(self):
        """Efectúa movimientos y recoge pasajeros."""
        if self.at_pickup:
            self.pick_up_passenger()
        elif self.destination:
            self.move_towards(self.destination)

    def move_towards(self, destination):
        """Se mueve hacia un destino objetivo."""
        x, y = self.pos
        dest_x, dest_y = destination

        if x < dest_x:
            x += self.speed
        elif x > dest_x:
            x -= self.speed

        if y < dest_y:
            y += self.speed
        elif y > dest_y:
            y -= self.speed

        self.model.grid.move_agent(self, (x, y))

        if (x, y) == destination:
            if self.route:
                self.destination = self.route.pop(0)
            else:
                self.destination = None

    def pick_up_passenger(self):
        """Recoge pasajeros si están presentes."""
        for passenger in self.pickup_points:
            self.model.grid.remove_agent(passenger)
            self.passengers += 1
        self.pickup_points = []
        self.at_pickup = False

    def change_lane(self):
        """Intenta cambiar de carril para avanzar."""
        x, y = self.pos
        neighbors = self.model.grid.get_neighborhood((x, y), moore=False, include_center=False)
        for pos in neighbors:
            if self.model.grid.is_cell_empty(pos):
                self.model.grid.move_agent(self, pos)
                break


# ------------------------ Agente Pasajero ------------------------
class Passenger(Agent):
    """
    Representa a un pasajero que espera ser recogido por un microbús.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)