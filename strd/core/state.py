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
        self.object_loc = {}  # object -> location (The apple is under a table) if object isn't held by someone

        for obj in objects:
            # Half of the time, the object will either be held by someone, or put down somewhere
            if random.random() < 0.5:
                holder = random.choice(entities)
                self.object_holder[obj] = holder
            else:
                location = random.choice(locations)
                self.object_loc[obj] = location

            assert not (obj in self.object_holder and obj in self.object_loc), (
                f"Inconsistent state for {obj}"
            )

    # Incase we need to know who has what and where is what
    def where_is_obj(self, obj):
        """
        Returns the location of an object
        If the object is being held by an entity, return None
        """
        if obj in self.object_holder:
            holder = self.object_holder[object]
            return self.entity_loc[holder]
        else:
            return self.object_loc[object]

    def where_is_ent(self, entity):
        """
        Returns an entitiy's location
        """
        return self.entity_loc[entity]

    def who_has(self, obj):
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
        objects = [object for object, loc in self.object_loc.items() if loc == location]
        return objects

    def entities_at(self, location):
        """
        Returns a list of entities given a location
        """
        entities = [
            entity for entity, loc in self.entity_loc.items() if loc == location
        ]
        return entities

    def assign_object_holder(self, obj, entity):
        """
        Assigns an object to an entity
        """
        self.object_loc.pop(obj, None)
        self.object_holder[obj] = entity

        assert obj not in self.object_loc

    def assign_object_loc(self, obj, location):
        """
        Assigns an object to a location
        """
        self.object_holder.pop(obj, None)
        self.object_loc[obj] = location

        assert obj not in self.object_holder

    def assign_ent_loc(self, entity, location):
        """
        Assigns an entity to a location
        """
        self.entity_loc[entity] = location

    def del_object_holder(self, obj):
        """
        Deletes an object holder record
        """
        self.object_holder.pop(obj, None)

    def del_object_loc(self, obj):
        """
        Deletes an object location record
        """
        self.object_loc.pop(obj, None)

    def del_entity_loc(self, entity):
        """
        Deletes an entity location record
        """
        self.entity_loc.pop(entity, None)

    def drop_object(self, obj):
        """
        Takes one object, if that object isn't being held, return 1

        If it exists in object_holder, delete that record
        Assign object_loc to the previous holder's location and return 0
        """
        holder = self.who_has(obj)

        if holder is None:
            return False

        holder_loc = self.where_is_ent(holder)

        self.assign_object_loc(obj, holder_loc)

        return True

    def pick_object(self, obj):
        """
        Takes one object, if it's already being held, return False

        else, choose a random entity that's at the same location of the object,
        and assign that object to the entity and return True
        """
        if self.who_has(obj) is not None:
            return False

        obj_loc = self.where_is_obj(obj)

        ent_same_loc = self.entities_at(obj_loc)

        if not ent_same_loc:
            return False

        random_ent = random.choice(ent_same_loc)

        self.assign_object_holder(obj, random_ent)
        return True

    def pass_obj(self, obj):
        """
        Takes one object, if that object isn't being held, return False

        Pass the object from one entity to another at the same location
        """
        holder = self.who_has(obj)

        if holder is None:
            return False

        holder_loc = self.where_is_ent(holder)
        ent_same_loc = self.entities_at(holder_loc)

        other_ents = [ent for ent in ent_same_loc if ent != holder]

        if not other_ents:
            return False

        new_holder = random.choice(other_ents)
        self.assign_object_holder(obj, new_holder)
        return True

    def move_entity(self, entity):
        """
        Randomly changes an entity to another location
        """
        curr_loc = self.where_is_ent(entity)
        other_locs = [location for location in self.locations if location != curr_loc]
        new_loc = random.choice(other_locs)
        self.assign_ent_loc(entity, new_loc)

    def move_object(self, obj):
        """
        Takes one object, if the object is held, it can randomly be
        dropped to the location of the entity, or given to another random entity at the
        same location

        If the object isn't being held, it can only be picked up by a random entity
        at the object's location
        """
        pass
