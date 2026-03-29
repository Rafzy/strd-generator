import random
from dataclasses import dataclass, asdict
from typing import Optional, Literal

type Actions = Literal["pick", "drop", "pass", "move"]


@dataclass
class ActionLog:
    action: Literal["pick", "drop", "pass", "move", "none"]
    entity: Optional[str] = None
    obj: Optional[str] = None
    location: Optional[str] = None
    to_entity: Optional[str] = None
    to_location: Optional[str] = None
    error_log: Optional[str] = None


class State:
    def __init__(
        self, entities: list[str], objects: list[str], locations: list[str], seed=None
    ) -> None:

        # Initialize random with seed
        self.seed = seed
        self.rng = random.Random(seed)
        self.entities = list(entities)
        self.objects = list(objects)
        self.locations = list(locations)

        self.entity_loc = {}  # entity -> locations (Andy is in his bedroom)
        """
        entity -> location
        """

        for e in entities:
            location = self.rng.choice(locations)
            self.entity_loc[e] = location

        self.object_holder = {}  # object -> entity (Andy is holding an apple) if object is held by someone
        self.object_loc = {}  # object -> location (The apple is under a table) if object isn't held by someone

        for obj in objects:
            # Half of the time, the object will either be held by someone, or put down somewhere
            if self.rng.random() < 0.5:
                holder = self.rng.choice(entities)
                self.object_holder[obj] = holder
            else:
                location = self.rng.choice(locations)
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
            holder = self.object_holder[obj]
            return self.entity_loc[holder]
        else:
            return self.object_loc[obj]

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
        if obj in self.object_holder:
            return self.object_holder[obj]
        else:
            # If object is not being held, return none
            return None

    def is_held(self, obj) -> bool:
        """
        Returns True if object is being held
        """
        return obj in self.object_holder

    def objects_at(self, location):
        """
        Returns a list of objects given a location
        """
        objects = [obj for obj, loc in self.object_loc.items() if loc == location]
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

    def valid_actions(self, obj) -> list[Actions]:
        """
        Returns a list of valid actions given an object
        """
        valids: list[Actions] = []
        if self.is_held(obj):
            # If held, being dropped is immediately a valid action
            valids.append("drop")
            holder = self.who_has(obj)
            holder_loc = self.where_is_ent(holder)
            other_ents = [
                ent
                for ent, loc in self.entity_loc.items()
                if loc == holder_loc and ent != holder
            ]
            if len(other_ents) > 0:
                valids.append("pass")

        else:
            obj_loc = self.where_is_obj(obj)
            ent_same_loc = [
                ent for ent, loc in self.entity_loc.items() if loc == obj_loc
            ]
            if len(ent_same_loc) > 0:
                valids.append("pick")

        return valids

    # ACTIONS
    def drop_object(self, obj) -> ActionLog:
        """
        Takes one object, if that object isn't being held, return 1

        If it exists in object_holder, delete that record
        Assign object_loc to the previous holder's location and return 0
        """
        holder = self.who_has(obj)

        if holder is None:
            return ActionLog(action="none", error_log="Object isn't being held")

        holder_loc = self.where_is_ent(holder)

        self.assign_object_loc(obj, holder_loc)

        return ActionLog(action="drop", entity=holder, obj=obj, location=holder_loc)

    def pick_object(self, obj, ent) -> ActionLog:
        """
        Takes one object, if it's already being held, return False

        else, choose a random entity that's at the same location of the object,
        and assign that object to the entity and return True
        """
        if self.who_has(obj) is not None:
            return ActionLog(action="none", error_log="Object is already being held")

        obj_loc = self.where_is_obj(obj)
        ent_loc = self.where_is_ent(ent)

        if obj_loc != ent_loc:
            return ActionLog(action="none")

        self.assign_object_holder(obj, ent)
        return ActionLog(action="pick", entity=ent, obj=obj, location=obj_loc)

    def pass_obj(self, obj, ent) -> ActionLog:
        """
        Takes one object, if that object isn't being held, return False

        Pass the object from one entity to another at the same location
        """
        holder = self.who_has(obj)

        if holder is None:
            return ActionLog(action="none", error_log="Object isn't being held")

        if holder == ent:
            return ActionLog(action="none", error_log="cannot pass to the same entity")

        holder_loc = self.where_is_ent(holder)
        ent_loc = self.where_is_ent(ent)

        if holder_loc != ent_loc:
            return ActionLog(
                action="none",
                error_log="Target entity isn't in the same place as current holder",
            )

        self.assign_object_holder(obj, ent)
        return ActionLog(
            action="pass",
            entity=holder,
            obj=obj,
            location=holder_loc,
            to_entity=ent,
        )

    def move_entity(self, ent, loc) -> ActionLog:
        init_loc = self.where_is_ent(ent)
        self.assign_ent_loc(ent, loc)
        return ActionLog("move", entity=ent, location=init_loc, to_location=loc)

    # DEPCRECATED
    def move_entity_rand(self):
        """
        !!DEPCRECATED
        Randomly takes one entity, and move it to a random place

        Will be used in the simulation
        """
        rand_ent = self.rng.choice(self.entities)
        curr_loc = self.where_is_ent(rand_ent)
        other_locs = [location for location in self.locations if location != curr_loc]
        new_loc = self.rng.choice(other_locs)
        self.assign_ent_loc(rand_ent, new_loc)

    # DEPCRECATED
    def move_object_rand(self):
        """
        !!DEPCRECATED
        Takes one random object, and randomly move it based on the restrictions available

        Will be used in the simulation
        """
        rand_obj = self.rng.choice(self.objects)

        # if self.is_held(rand_obj):
        #     if self.rng.random() < 0.5:
        #         result = self.pass_obj(rand_obj)
        #         if not result:
        #             self.drop_object(rand_obj)
        #             return None
        #         return None
        #     else:
        #         self.drop_object(rand_obj)
        #         return None
        # else:
        #     if not self.pick_object(rand_obj):
        #         return None

    def take_snapshot(self):
        snapshot = {
            "objects": [],
            "entities": [],
            "locations": self.locations,
        }

        for obj in self.objects:
            object_state = {}
            object_state["name"] = obj
            holder = self.who_has(obj)
            object_state["is_held"] = holder is not None
            object_state["holder"] = holder
            object_state["location"] = self.where_is_obj(obj)

            snapshot["objects"].append(object_state)

        for ent in self.entities:
            entity_state = {}
            entity_state["name"] = ent
            entity_state["location"] = self.where_is_ent(ent)
            held_objects = [
                obj for obj, entity in self.object_holder.items() if entity == ent
            ]
            entity_state["holding_object"] = held_objects
            entity_state["is_holding_object"] = len(held_objects) > 0
            snapshot["entities"].append(entity_state)

        return snapshot
