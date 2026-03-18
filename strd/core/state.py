import random


class State:
    def __init__(self, entities, objects, locations) -> None:
        self.entities = list(entities)
        self.objects = list(objects)
        self.locations = list(locations)

        self.entity_loc = {}  # entity -> locations (Andy is in his bedroom)

        for e in entities:
            location = random.choice(locations)
            self.entity_loc[e] = location

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
        If the object is being held by an entity, return None
        """
        if object in self.object_holder:
            # Maybe it's better to return none when it's being held by an entity
            # holder = self.object_holder[object]
            # return self.entity_loc[holder]
            return None
        else:
            return self.object_loc[object]

    def where_is_ent(self, entity):
        """
        Returns an entitiy's location
        """
        return self.entity_loc[entity]

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
        entities = [entity for entity, loc in self.entity_loc if loc == location]
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
        self.entity_loc[entity] = location

    def del_object_holder(self, object):
        """
        Deletes an object holder record
        """
        del self.object_holder[object]

    def del_object_loc(self, object):
        """
        Deletes an object location record
        """
        del self.object_loc[object]

    def del_entity_loc(self, entity):
        """
        Deletes an entity location record
        """
        del self.entity_loc[entity]

    def drop_object(self, object):
        """
        Takes one object, if that object isn't being held, return 1

        If it exists in object_holder, delete that record
        Assign object_loc to the previous holder's location and return 0
        """
        holder = self.who_has(object)

        if holder is None:
            return 1

        holder_loc = self.where_is_ent(holder)

        self.del_object_holder(object)
        self.assign_object_loc(object, holder_loc)

        return 0

    def pick_object(self, object):
        """
        Takes one object, if it's already being held, return 1

        else, choose a random entity that's at the same location of the object,
        and assign that object to the entity and return 0
        """
        if self.who_has(object) is not None:
            return 1

        obj_loc = self.where_is_obj(object)

        ent_same_loc = self.entities_at(obj_loc)

        random_ent = random.choice(ent_same_loc)

        self.assign_object_holder(object, random_ent)
        self.del_object_loc(object)

        return 0

    def pass_object(self, object, entity):
        """
        Passes an object from one entity to another random entity at the same location, then return 0

        returns 1 if an object isn't being held by an entity
        """
        if who_has(object) is None:
            return 1

    def move_entity(self, entity):
        """
        Randomly changes an entity to another location
        """
        curr_loc = self.where_is_ent(entity)
        other_locs = [location for location in self.locations if location != curr_loc]
        new_loc = random.choice(other_locs)
        self.assign_ent_loc(entity, new_loc)

    def move_object(self, object):
        """
        Takes one object, if the object is held, it can randomly be
        dropped to the location of the entity, or given to another random entity at the
        same location

        If the object isn't being held, it can only be picked up by a random entity
        at the object's location
        """

        pass
