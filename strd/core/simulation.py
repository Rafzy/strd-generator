import random
from .state import ActionSpec, State, Actions, ActionLog
from dataclasses import asdict, dataclass
import json


class Simulation:
    def __init__(self, max_steps, seed=None) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.max_steps = max_steps
        self.history = {}
        self.policy = {}
        pass

    def export_episode(
        self,
        episode_id: str,
        entities: list[str],
        objects: list[str],
        locations: list[str],
    ):

        state = State(
            entities=entities, objects=objects, locations=locations, seed=self.seed
        )

        initial_state = state.take_snapshot()
        action_logs = []
        timeline = []

        i = 0

        while True:
            if i >= self.max_steps:
                break

            enumerated_valid_actions: list[ActionSpec] = state.enumerate_valid_actions()
            random_valid_action: ActionSpec = self.rng.choice(enumerated_valid_actions)
            result = state.execute(random_valid_action)
            state.validate()

            # append the log to action_logs
            if result.action == "none":
                continue

            result.order = i + 1
            action_logs.append(asdict(result))
            timeline.append({"order": i + 1, "snapshot": state.take_snapshot()})

            # curr_timeline = {}
            # curr_timeline["order"] = i + 1
            # curr_timeline["snapshot"] = state.take_snapshot()

            # append current timeline to state timeline

            i += 1

        episode = {
            "episode_id": episode_id,
            "seed": self.seed,
            "config": {
                "max_steps": self.max_steps,
            },
            "world": {
                "entities": entities,
                "objects": objects,
                "locations": locations,
            },
            "initial_state": initial_state,
            "actions": action_logs,
            "timeline": timeline,
        }

        return episode
