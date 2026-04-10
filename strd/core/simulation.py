import random
from .state import ActionLog, ActionSpec, State, Actions
from dataclasses import asdict


class Simulation:
    def __init__(self, max_steps, seed=None) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.max_steps = max_steps
        self.history = {}
        self.policy = {}
        pass

    def sample_weighted_action(
        self, valid_actions: list[ActionSpec], action_type_weights: dict[Actions, float]
    ) -> ActionSpec:
        grouped: dict[Actions, list[ActionSpec]] = {}

        for action in valid_actions:
            grouped.setdefault(action.action, []).append(action)

        available_types = list(grouped.keys())
        available_weights = [
            action_type_weights.get(action_type, 1) for action_type in available_types
        ]

        chosen_type = self.rng.choices(available_types, weights=available_weights, k=1)[
            0
        ]

        return self.rng.choice(grouped[chosen_type])

    def export_episode(
        self,
        episode_id: str,
        entities: list[str],
        objects: list[str],
        locations: list[str],
        action_type_weights: dict[Actions, float],
        distractor_p: float = 0,
    ) -> dict:

        state = State(
            entities=entities, objects=objects, locations=locations, seed=self.seed
        )

        initial_state = state.take_snapshot()
        action_logs = []
        timeline = []

        distractor_positions = set()

        if distractor_p > 0:
            distractor_num = round(self.max_steps * distractor_p)
            distractor_positions = set(
                random.sample(range(self.max_steps), distractor_num)
            )
        i = 0

        while True:
            if i >= self.max_steps:
                break

            if i in distractor_positions:
                # If current i is in distractor position
                enumerated_invalid_actions: list[ActionSpec] = (
                    state.enumerate_invalid_actions()
                )

                # Dumb solution, fix this later
                if not enumerated_invalid_actions:
                    i += 1
                    continue

                random_invalid_action: ActionSpec = self.sample_weighted_action(
                    enumerated_invalid_actions, action_type_weights
                )
                result: ActionLog = ActionLog(
                    action=random_invalid_action.action,
                    entity=random_invalid_action.entity,
                    obj=random_invalid_action.obj,
                    location=random_invalid_action.location,
                    to_entity=random_invalid_action.to_entity,
                    to_location=random_invalid_action.to_location,
                    distractor_action=True,
                )
            else:
                enumerated_valid_actions: list[ActionSpec] = (
                    state.enumerate_valid_actions()
                )
                random_valid_action: ActionSpec = self.sample_weighted_action(
                    enumerated_valid_actions, action_type_weights
                )
                result: ActionLog = state.execute(random_valid_action)

            state.validate()

            # append the log to action_logs
            if result.action == "none":
                continue

            result.order = i + 1
            action_logs.append(asdict(result))
            timeline.append({"order": i + 1, "snapshot": state.take_snapshot()})

            i += 1

        episode = {
            "episode_id": episode_id,
            "seed": self.seed,
            "config": {
                "max_steps": self.max_steps,
                "distractor_p": distractor_p,
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
