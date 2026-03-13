from strd.core.state import State


def main():
    entities = ["Andy", "Lucy", "Bob", "John"]
    objects = ["Apple", "Orange", "Pencil", "Avocado"]
    locations = ["Bedroom", "Living room", "Italy", "Prison"]
    state = State(entities=entities, objects=objects, locations=locations)
    print(state.entities_loc)


if __name__ == "__main__":
    main()
