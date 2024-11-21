from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
import random
from Vehicle import Vehicle


# ------------------------ Agente Toyota Trueno: Speedster ------------------------
class ToyotaTrueno(Agent):
    """
    Este es el agente Toyota Trueno: Speedster, diseñado para recorrer la ciudad 
    con el mayor número de giros o de forma eficiente dependiendo de su estado.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = "feliz"  # Estados: feliz (default), enojado
        self.speed = 1  # Velocidad base
        self.target = None
        self.path = []
        self.glory_loop = False  # Indica si está disfrutando en una glorieta
        self.decision = None

    def step(self):
        self.perceive_environment()
        self.make_decision()
        self.act()

    # Componente Reactivo
    def perceive_environment(self):
        """Evalúa el entorno inmediato y su posición."""
        if self.state == "feliz":
            # Busca glorietas o rutas con giros
            if self.is_in_roundabout() and not self.glory_loop:
                self.glory_loop = True

        elif self.state == "enojado":
            # Cambia de estado si el camino está despejado
            if not self.is_obstructed():
                self.state = "feliz"

    def is_in_roundabout(self):
        """Detecta si el vehículo está en una glorieta."""
        from interaccion_agentes import Street
        x, y = self.pos
        return self.model.grid.get_cell_list_contents((x, y)) and isinstance(
            self.model.grid.get_cell_list_contents((x, y))[0], Street
        )

    def is_obstructed(self):
        """Evalúa si el camino está bloqueado."""
        x, y = self.pos
        neighbors = self.model.grid.get_neighbors((x, y), moore=False, include_center=False)
        return any(isinstance(neighbor, Vehicle) for neighbor in neighbors)

    # Componente Deliberativo
    def make_decision(self):
        """Planea sus movimientos en función de su estado."""
        if not self.path:
            if self.state == "feliz":
                self.decision = "cede"
                self.plan_route_with_turns()
            elif self.state == "enojado":
                self.decision = "compite"
                self.plan_fastest_route()

        if self.glory_loop:
            self.enjoy_roundabout()
        return self.decision

    def plan_route_with_turns(self):
        """Planea una ruta que maximice los giros."""
        grid_width, grid_height = self.model.grid.width, self.model.grid.height
        all_positions = [(x, y) for x in range(grid_width) for y in range(grid_height)]
        self.path = sorted(
            all_positions,
            key=lambda pos: abs(pos[0] - self.pos[0]) + abs(pos[1] - self.pos[1]),
            reverse=True,
        )  # Ruta que incluye más cambios de dirección
        self.target = self.path.pop(0)

    def plan_fastest_route(self):
        """Planea la ruta más rápida de un extremo al otro."""
        grid_width, grid_height = self.model.grid.width, self.model.grid.height
        if self.pos[0] < grid_width // 2:
            self.target = (grid_width - 1, self.pos[1])  # Ir al extremo derecho
        else:
            self.target = (0, self.pos[1])  # Ir al extremo izquierdo

    def enjoy_roundabout(self):
        """Realiza una vuelta adicional en una glorieta."""
        self.path = [self.pos] * 3  # Permanece en su posición actual por unos pasos
        self.glory_loop = False

    # Acciones
    def act(self):
        """Ejecuta la acción correspondiente según la decisión tomada."""
        if self.target:
            self.move_towards(self.target)

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

        # Cambia de estado si llega a su destino
        if (x, y) == destination:
            self.target = None
            if self.state == "enojado":
                self.state = "feliz"