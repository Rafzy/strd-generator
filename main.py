from strd.core.state import State


def print_state(state):
    print("\n=== CURRENT STATE ===")
    print("Entities:", state.entities)
    print("Locations:", state.locations)
    print("Objects:", state.objects)

    print("\nEntity Locations:")
    for ent, loc in state.entity_loc.items():
        print(f"  {ent} -> {loc}")

    print("\nObject Holders:")
    for obj, holder in state.object_holder.items():
        print(f"  {obj} held by {holder}")

    print("\nObject Locations:")
    for obj, loc in state.object_loc.items():
        print(f"  {obj} at {loc}")
    print("====================\n")


def setup_state():
    entities = ["Alice", "Bob", "Charlie"]
    objects = ["apple", "book"]
    locations = ["kitchen", "bedroom"]

    state = State(entities, objects, locations)

    # Clear random initialization
    state.entity_loc.clear()
    state.object_holder.clear()
    state.object_loc.clear()

    # Manually assign locations
    state.assign_ent_loc("Alice", "kitchen")
    state.assign_ent_loc("Bob", "kitchen")
    state.assign_ent_loc("Charlie", "bedroom")

    # Assign objects
    state.assign_object_loc("apple", "kitchen")  # on the ground
    state.assign_object_holder("book", "Charlie")  # already held

    return state


def test_actions():
    state = setup_state()

    print("Initial State:")
    print_state(state)

    # --- PICK OBJECT ---
    print("Alice/Bob tries to pick up apple")
    result = state.pick_object("apple")
    print("pick_object result:", result)
    print_state(state)

    # --- PASS OBJECT ---
    print("Passing apple to another entity in same location")
    result = state.pass_obj("apple")
    print("pass_obj result:", result)
    print_state(state)

    # --- DROP OBJECT ---
    print("Dropping apple")
    result = state.drop_object("apple")
    print("drop_object result:", result)
    print_state(state)

    # --- MOVE ENTITY ---
    print("Moving Alice")
    state.move_entity_rand("Alice")
    print_state(state)

    # --- TRY EDGE CASE ---
    print("Trying to pass object not held (apple)")
    result = state.pass_obj("apple")
    print("pass_obj result:", result)
    print_state(state)


def main():
    pass


if __name__ == "__main__":
    test_actions()
