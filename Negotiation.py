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