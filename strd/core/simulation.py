from state import State
from dataclasses import dataclass


class Simulation:
    def __init__(self, max_steps) -> None:
        self.max_steps = max_steps
        self.history = {}
        pass

    def run_sim(self, entities, objects, locations, seed, n):

        state = State(
            entities=entities, objects=objects, locations=locations, seed=seed
        )

        for i in range(n):
            pass

        pass
