from strd.core.state import Actions
from strd.core.simulation import Simulation
from entity_list.entities import ENTITIES
from entity_list.objects import OBJECTS
from entity_list.locations import LOCATIONS
import json


def save_episode_json(path: str, episode: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(episode, f, indent=2, ensure_ascii=False)


def format_action(log: dict) -> str:
    action = log["action"]

    if action == "pick":
        return f"{log['entity']} picked up {log['obj']} at {log['location']} {'(Distrator)' if log['distractor_action'] else ''}"
    elif action == "drop":
        return f"{log['entity']} dropped {log['obj']} at {log['location']} {'(Distrator)' if log['distractor_action'] else ''}"
    elif action == "pass":
        return (
            f"{log['entity']} passed {log['obj']} "
            f"to {log['to_entity']} at {log['location']} {'(Distrator)' if log['distractor_action'] else ''}"
        )
    elif action == "move":
        return f"{log['entity']} moved from {log['location']} to {log['to_location']} {'(Distrator)' if log['distractor_action'] else ''}"

    return f"ERROR: {log.get('error_log', 'Unknown error')}"


def format_snapshot(snapshot: dict, locations: list[str]) -> str:
    output = []

    for loc in locations:
        ents = [e["name"] for e in snapshot["entities"] if e["location"] == loc]

        objs = []
        for o in snapshot["objects"]:
            if o["location"] == loc:
                if o["is_held"]:
                    objs.append(f"{o['name']} (held by {o['holder']})")
                else:
                    objs.append(o["name"])

        output.append(f"{loc}:")
        output.append(f"  Entities: {', '.join(ents) if ents else '-'}")
        output.append(f"  Objects: {', '.join(objs) if objs else '-'}")
        output.append("")

    return "\n".join(output)


def print_simulation(episode: dict) -> None:
    print("\n=== SIMULATION TRACE ===\n")

    locations = episode["world"]["locations"]

    print("========== INITIAL STATE ==========")
    print(format_snapshot(episode["initial_state"], locations))
    print("=" * 35 + "\n")

    for log, step in zip(episode["actions"], episode["timeline"]):
        print(f"========== STEP {log['order']} ==========")

        print("Action:")
        print(f"  {format_action(log)}\n")

        print("State after action:")
        print(format_snapshot(step["snapshot"], locations))

        print("=" * 35 + "\n")


def run_test(episode_id: str):
    sim = Simulation(max_steps=15)
    action_weights: dict[Actions, float] = {
        "move": 0.20,
        "pick": 0.30,
        "pass": 0.30,
        "drop": 0.20,
    }
    episode = sim.export_episode(
        episode_id=episode_id,
        entities=ENTITIES,
        objects=OBJECTS,
        locations=LOCATIONS,
        action_type_weights=action_weights,
        distractor_p=0.1,
        sample_size=10,
    )

    print_simulation(episode)
    save_episode_json(f"episodes/{episode_id}.json", episode)


if __name__ == "__main__":
    run_test(episode_id="ep_0001")
