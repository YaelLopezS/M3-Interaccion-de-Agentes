from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
import random
from Vehicle import Vehicle


# ------------------------ Agente Ferrari F40 ------------------------
class FerrariF40(Agent):
    """
    Este es el agente Ferrari F40, un híbrido que busca optimizar su velocidad y recorrido por la ciudad.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = "normal"  # Estados: normal, ansioso/enojado
        self.speed = 2  # Más rápido que los vehículos normales
        self.path = []
        self.current_target = None
        self.visited_positions = set()
        self.decision = None

    def step(self):
        self.perceive_environment()
        self.make_decision()
        self.act()

    # Componente Reactivo
    def perceive_environment(self):
        """Evalúa el entorno inmediato."""
        x, y = self.pos
        neighbors = self.model.grid.get_neighbors((x, y), moore=False, include_center=False)

        # Cambiar de estado si hay bloqueo o espera prolongada
        if self.state == "normal" and self.is_waiting_too_long():
            self.state = "ansioso/enojado"

    def is_waiting_too_long(self):
        """Evalúa si el Ferrari ha estado en la misma posición demasiado tiempo."""
        if self.pos in self.visited_positions:
            return True
        self.visited_positions.add(self.pos)
        return False

    # Componente Deliberativo
    def make_decision(self):
        """Planea su siguiente movimiento en función de su estado."""
        if not self.path:
            self.plan_route()

        if self.state == "ansioso/enojado":
            # Busca rutas alternativas para avanzar más rápido
            self.decision = "compite"
            self.find_alternate_route()
        else:
            self.decision = "cede"
        return self.decision

    def plan_route(self):
        """Genera un recorrido que optimiza el tiempo para explorar toda la ciudad."""
        grid_width, grid_height = self.model.grid.width, self.model.grid.height
        all_positions = [(x, y) for x in range(grid_width) for y in range(grid_height)]
        self.path = [pos for pos in all_positions if pos != self.pos]
        self.current_target = self.path.pop(0)

    def find_alternate_route(self):
        """Intenta buscar una ruta diferente si está bloqueado."""
        x, y = self.pos
        neighbors = self.model.grid.get_neighborhood((x, y), moore=False, include_center=False)
        for pos in neighbors:
            if self.model.grid.is_cell_empty(pos):
                self.current_target = pos
                break

    # Acciones
    def act(self):
        """Realiza su movimiento o cede el paso."""
        if self.current_target:
            self.move_towards(self.current_target)

        if self.state == "normal" and self.encounter_other_vehicle():
            self.yield_to_other_vehicle()

    def move_towards(self, destination):
        """Se mueve hacia un destino."""
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
            self.current_target = self.path.pop(0) if self.path else None

    def encounter_other_vehicle(self):
        """Detecta si hay otros vehículos cerca."""
        x, y = self.pos
        neighbors = self.model.grid.get_neighbors((x, y), moore=False, include_center=False)
        return any(isinstance(neighbor, Vehicle) for neighbor in neighbors)

    def yield_to_other_vehicle(self):
        """Cede el paso a otro vehículo."""
        x, y = self.pos
        neighbors = self.model.grid.get_neighbors((x, y), moore=False, include_center=False)
        for neighbor in neighbors:
            if isinstance(neighbor, Vehicle):
                # Espera en su posición actual un paso de tiempo para ceder el paso
                break