import random


class State:
    def __init__(self, entities, objects, locations) -> None:
        self.entities = list(entities)
        self.objects = list(objects)
        self.locations = list(locations)

        self.entities_loc = {}  # entity -> locations (Andy is in his bedroom)

        for e in entities:
            location = random.choice(locations)
            self.entities_loc[e] = location

        self.object_holder = {}  # object -> entity (Andy is holding an apple)
        self.object_loc = {}  # object -> location (The apple is under a table)

        for obj in objects:
            # Half of the time, the object will either be held by someone, or put down somewhere
            if random.random() < 0.5:
                holder = random.choice(entities)
                self.object_holder[obj] = holder
            else:
                location = random.choice(locations)
                self.object_loc[obj] = location

    # Incase we need to know who has what and where is what
    def where_is(self, object):
        if object in self.object_holder:
            holder = self.object_holder[object]
            return self.entities_loc[holder]
        else:
            return self.object_loc[object]

    def who_has(self, object):
        if object in self.object_holder:
            return self.object_holder[object]
        else:
            # If object is not being held, return none
            return None

    def move_entity(self, entity):
        # We can make entities randomly move places
        new_loc = random.choice(self.locations)
        self.entities_loc[entity] = new_loc

    def objects_at(self, location):
        locations = []

    def move_object(self, object):
        # Maybe we make it so that the object can only be moved to another entity in the same location,
        # if not, then it can only be put down at that location, if the object isn't being held by someone,
        # then another entity at that location can pick it up
        location = self.where_is(object)
        holder = self.who_has(object)
        ent_same_loc = [
            entity
            for entity, loc in self.entities_loc
            if loc == location and entity != holder
        ]

        if len(ent_same_loc) == 0:
            pass
            # If there are no other entity at that same location, then just put the object at that location

        pass

    def mutate_state(self):
        pass
