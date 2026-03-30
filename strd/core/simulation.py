import random
from .state import State, Actions, ActionLog
from dataclasses import asdict, dataclass
import pprint


class Simulation:
    def __init__(self, max_steps, seed=None, state: State = State([], [], [])) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.state: State = state
        self.max_steps = max_steps
        self.history = {}
        self.policy = {}
        pass

    def run_sim(self, entities: list[str], objects: list[str], locations: list[str]):

        state = State(
            entities=entities, objects=objects, locations=locations, seed=self.seed
        )

        action_logs: list[ActionLog] = []
        state_timeline = []

        i = 0

        while True:
            if i >= self.max_steps:
                break

            random_obj = self.rng.choice(state.objects)
            valid_actions: list[Actions] = state.valid_actions(random_obj)

            if not valid_actions:
                print(f"No valid action for: {random_obj}")
                continue

            rand_action: Actions = self.rng.choice(valid_actions)

            result: ActionLog = ActionLog(action="none", error_log="not executed yet")

            # print(valid_actions)
            # pprint.pprint(state.take_snapshot())

            if rand_action == "pass":
                holder = state.who_has(random_obj)
                holder_loc = state.where_is_ent(holder)
                other_entities = [
                    ent
                    for ent, loc in state.entity_loc.items()
                    if ent != holder and loc == holder_loc
                ]

                to_entity = self.rng.choice(other_entities)
                result = state.pass_obj(random_obj, to_entity)

            elif rand_action == "drop":
                result = state.drop_object(random_obj)

            elif rand_action == "pick":
                obj_location = state.where_is_obj(random_obj)
                ent_same_loc = [
                    ent for ent, loc in state.entity_loc.items() if loc == obj_location
                ]
                picker = self.rng.choice(ent_same_loc)
                result = state.pick_object(random_obj, picker)

            elif rand_action == "move":
                rand_entity = self.rng.choice(state.entities)
                ent_loc = state.where_is_ent(rand_entity)
                other_locations = [loc for loc in state.locations if loc != ent_loc]
                rand_location = self.rng.choice(other_locations)
                result = state.move_entity(rand_entity, rand_location)

            if result.action == "none":
                print(result.error_log)
                break
            else:
                result.order = i + 1
                action_logs.append(result)

            curr_timeline = {}
            curr_timeline["order"] = i + 1
            curr_timeline["snapshot"] = state.take_snapshot()

            state_timeline.append(curr_timeline)

            i += 1

        # for actions in action_logs:
        #     pprint.pprint(asdict(actions))
        #
        # for timeline in state_timeline:
        #     pprint.pprint(timeline)
        return action_logs, state_timeline

    def format_action(self, log: ActionLog):
        if log.action == "pick":
            return f"{log.entity} picked up {log.obj} at {log.location}"
        elif log.action == "drop":
            return f"{log.entity} dropped {log.obj} at {log.location}"
        elif log.action == "pass":
            return f"{log.entity} passed {log.obj} to {log.to_entity} at {log.location}"
        elif log.action == "move":
            return f"{log.entity} moved from {log.location} to {log.to_location}"
        return f"ERROR: {log.error_log}"
