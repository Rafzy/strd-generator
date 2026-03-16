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

        self.object_holder = {}  # object -> entity (Andy is holding an apple) if object is held by someone
        self.object_loc = {}  # object -> location (The apple is under a table) if obbject isn't held by someone

        for obj in objects:
            # Half of the time, the object will either be held by someone, or put down somewhere
            if random.random() < 0.5:
                holder = random.choice(entities)
                self.object_holder[obj] = holder
            else:
                location = random.choice(locations)
                self.object_loc[obj] = location

    # Incase we need to know who has what and where is what
    def where_is_obj(self, object):
        """
        Returns the location of an object
        If the object is being held by an entity, return the location of that entity
        """
        if object in self.object_holder:
            holder = self.object_holder[object]
            return self.entities_loc[holder]
        else:
            return self.object_loc[object]

    def where_is_ent(self, entity):
        """
        Returns an entitiy's location
        """
        return self.entities_loc[entity]

    def who_has(self, object):
        """
        Returns an entity that's holding the given object
        Returns none if the object isn't being held
        """
        if object in self.object_holder:
            return self.object_holder[object]
        else:
            # If object is not being held, return none
            return None

    def objects_at(self, location):
        """
        Returns a list of objects given a location
        """
        objects = [object for object, loc in self.object_loc if loc == location]
        return objects

    def entities_at(self, location):
        """
        Returns a list of entities given a location
        """
        entities = [entity for entity, loc in self.entities_loc if loc == location]
        return entities

    def assign_object_holder(self, object, entity):
        """
        Assigns an object to an entity
        """
        self.object_holder[object] = entity

    def assign_object_loc(self, object, location):
        """
        Assigns an object to a location
        """
        self.object_loc[object] = location

    def assign_ent_loc(self, entity, location):
        """
        Assigns an entity to a location
        """
        self.entities_loc[entity] = location

    def drop_object(self, object):
        """
        Takes one object, if that object isn't being held, do nothing

        If it exists in object_holder, delete that record
        Assign object_loc to the previous holder's location
        """
        if self.who_has(object) is None:
            return None

        obj_loc = self.where_is_obj(object)

        if object in self.object_holder:
            del self.object_holder[object]

        # assigns object to object_loc since object is dropped
        self.object_loc[object] = obj_loc
        # TODO

    def move_entity(self, entity):
        # We can make entities randomly move places
        new_loc = random.choice(self.locations)
        self.assign_ent_loc(entity, new_loc)

    def pick_object(self, object):
        """
        Takes one object, if it's already being held, return nothing

        else, choose a random entity that's at the same location of the object,
        and assign that object to the entity
        """
        if self.who_has(object) is not None:
            return None

        # TODO

    def move_object(self, object):
        """
        Takes one object, if the object is held, it can randomly be
        dropped to the location of the entity, or given to another random entity at the
        same location

        If the object isn't being held, it can only be picked up by a random entity
        at the object's location
        """
        location = self.where_is_obj(object)
        holder = self.who_has(object)
        ent_same_loc = [
            entity
            for entity, loc in self.entities_loc
            if loc == location and entity != holder
        ]

        if len(ent_same_loc) == 0:
            pass
            # If there are no other entity at that same location,
            # then just put the object at that location

        pass

    def mutate_state(self):
        pass
