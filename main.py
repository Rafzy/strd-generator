from strd.core.simulation import Simulation
from dataclasses import asdict


# -------- FORMATTERS -------- #


def format_action(log):
    if log.action == "pick":
        return f"{log.entity} picked up {log.obj} at {log.location}"
    elif log.action == "drop":
        return f"{log.entity} dropped {log.obj} at {log.location}"
    elif log.action == "pass":
        return f"{log.entity} passed {log.obj} to {log.to_entity} at {log.location}"
    elif log.action == "move":
        return f"{log.entity} moved from {log.location} to {log.to_location}"
    return f"ERROR: {log.error_log}"


def format_snapshot(snapshot):
    output = []

    for loc in snapshot["locations"]:
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


def print_simulation(action_logs, timeline):
    print("\n=== SIMULATION TRACE ===\n")

    for log, step in zip(action_logs, timeline):
        print(f"========== STEP {log.order} ==========")

        # Action
        print("Action:")
        print(f"  {format_action(log)}\n")

        # State
        print("State after action:")
        print(format_snapshot(step["snapshot"]))

        print("=" * 35 + "\n")


# -------- TEST -------- #


def run_test():
    entities = ["Alice", "Bob", "Charlie"]
    objects = ["Apple", "Book"]
    locations = ["Kitchen", "Bedroom", "Office"]

    sim = Simulation(max_steps=10, seed=123)

    action_logs, timeline = sim.run_sim(
        entities=entities,
        objects=objects,
        locations=locations,
    )

    print_simulation(action_logs, timeline)


if __name__ == "__main__":
    run_test()
