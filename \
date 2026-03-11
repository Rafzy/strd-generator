from random import Random


class State:
    def __init__(self, entities, objects, locations, rng: Random) -> None:
        self.entities = list(entities)
        self.objects = list(objects)
        self.locations = list(locations)

        self.entities_loc = {}  # entity -> locations (Andy is in his bedroom)

        for e in entities:
            location = rng.choice(locations)
            self.entities_loc[e] = location

        self.object_holder = {}  # object -> entity (Andy is holding an apple)
        self.object_loc = {}  # object -> location (The apple is under a table)

        for obj in objects:
            # Half of the time, the object will be held by someone, or put down somewhere
            if rng.random() < 0.5:
                holder = rng.choice(entities)
                self.object_holder[obj] = holder
            else:
                location = rng.choice(locations)
                self.object_loc[obj] = location

    def where_is(self, object):
        if object in self.object_holder:
            return self.object_holder[object]
        else:
            return self.object_loc[object]
