import random
from state import State
from dataclasses import dataclass


class Simulation:
    def __init__(self, max_steps, seed=None) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.max_steps = max_steps
        self.history = {}
        pass

    def run_sim(self, entities: list[str], objects: list[str], locations: list[str]):

        state = State(
            entities=entities, objects=objects, locations=locations, seed=self.seed
        )

        for i in range(self.max_steps):
            if self.rng.random() < 0.5:
                state.move_object_rand()
            else:
                state.move_entity_rand()

        pass
