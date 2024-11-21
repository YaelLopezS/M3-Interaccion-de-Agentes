from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
import random

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