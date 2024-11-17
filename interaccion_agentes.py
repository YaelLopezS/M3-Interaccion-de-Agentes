from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
import random

# ------------------------ Nuestra negociacion ----------------
class NegotiationManager:
    """
    Maneja la negociación entre agentes utilizando teoría de juegos.
    """
    def __init__(self):
        self.reward_matrix = {
            ("cede", "cede"): (2, 2),
            ("cede", "compite"): (3, 1),
            ("compite", "cede"): (1, 3),
            ("compite", "compite"): (0, 0),
        }

    def negotiate(self, agent_a, agent_b):
        decision_a = agent_a.make_decision()  # O lo que corresponda
        decision_b = agent_b.make_decision()  # O lo que corresponda

        # Verifica que las decisiones no sean None
        if decision_a is None or decision_b is None:
            return

        # Ahora accede a la matriz de recompensas
        rewards = self.reward_matrix.get((decision_a, decision_b), (0, 0))  # valor por defecto



# ------------------------ Agente base ------------------------
class Vehicle(Agent):
    """
    Este es nuestro agente de vehiculo base, el cual comienza en posiciones aleatorias entre el norte, sur, este y oeste. Se dirige hacia el semaforo y le avisa si esta proximo a llegar.
    """
    def __init__(self, unique_id, model, destination, state="neutral"):
        super().__init__(unique_id, model)
        self.destination = destination
        self.state = state
        self.arrival_time = None
        self.speed = 1
        self.at_turning_point = False
        self.sem_x = model.grid.width // 2
        self.sem_y = model.grid.height // 2
        self.decision = None

    def step(self):
        if not self.at_turning_point:
            self.move()
        else:
            self.direccion()
        self.destino()

    def move(self):
        x, y = self.pos
        if x < self.sem_x:
            x += self.speed
        elif x > self.sem_x:
            x -= self.speed
    
        if y < self.sem_y:
            y += self.speed
        elif y > self.sem_y:
            y -= self.speed

        self.model.grid.move_agent(self, (x, y))

        if (x, y) == (self.sem_x, self.sem_y):
            self.at_turning_point = True
            self.avisar_aproximacion()
            self.model.traffic_light.recibir_mensaje(self)

            self.make_decision()


    def direccion(self):
        if self.destination == "north":
            self.model.grid.move_agent(self, (self.pos[0], self.pos[1] - self.speed))
        elif self.destination == "east":
            self.model.grid.move_agent(self, (self.pos[0] + self.speed, self.pos[1]))
        elif self.destination == "west":
            self.model.grid.move_agent(self, (self.pos[0] - self.speed, self.pos[1]))

    def avisar_aproximacion(self):
        distance = abs(self.pos[1] - self.sem_y) + abs(self.pos[0] - self.sem_x)
        self.arrival_time = distance // self.speed

    def destino(self):
        if (self.destination == "north" and self.pos[1] == 0) or \
           (self.destination == "east" and self.pos[0] == self.model.grid.width - 1) or \
           (self.destination == "west" and self.pos[0] == 0):
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
    
    def make_decision(self):
        if self.state == "calmado":
            self.decision = "cede"
            # Respetar el semáforo
            traffic_light = self.model.traffic_light
            if self.pos == (self.sem_x, self.sem_y):
                if traffic_light.color != "green":
                    # Si el semáforo no está en verde, el vehículo no avanza.
                    return
        elif self.state == "enojado":
            # Ignorar el semáforo
            self.decision = "compite"
            pass
        return self.decision


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