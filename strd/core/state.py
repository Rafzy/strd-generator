import random
from dataclasses import dataclass
from typing import Optional, Literal

type Actions = Literal["pick", "drop", "pass", "move"]


@dataclass
class ActionLog:
    action: Literal["pick", "drop", "pass", "move", "none"]
    order: Optional[int] = None
    entity: Optional[str] = None
    obj: Optional[str] = None
    location: Optional[str] = None
    to_entity: Optional[str] = None
    to_location: Optional[str] = None
    error_log: Optional[str] = None
    distractor_action: Optional[bool] = False


@dataclass
class ActionSpec:
    action: Literal["pick", "drop", "pass", "move"]
    entity: Optional[str] = None
    obj: Optional[str] = None
    location: Optional[str] = None
    to_entity: Optional[str] = None
    to_location: Optional[str] = None


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

        self.object_holder = {}  # object -> entity (Andy is holding an apple) if object is held by someone
        """
        object -> holder
        """

        self.object_loc = {}  # object -> location (The apple is under a table) if object isn't held by someone
        """
        object -> location
        """

        for e in entities:
            location = self.rng.choice(locations)
            self.entity_loc[e] = location

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

        # Ensure no duplicated items
        assert len(set(self.entities)) == len(self.entities), "Duplicate entities"
        assert len(set(self.objects)) == len(self.objects), "Duplicate objects"
        assert len(set(self.locations)) == len(self.locations), "Duplicate locations"

    # Incase we need to know who has what and where is what
    def where_is_obj(self, obj):
        """
        Returns the location of an object
        If the object is being held by an entity, return the entity's location
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

    def enumerate_valid_actions(self) -> list[ActionSpec]:
        """
        Return all possible valid actions
        Shape:
        action: Literal["pick", "drop", "pass", "move"]
        entity: Optional[str] = None
        obj: Optional[str] = None
        location: Optional[str] = None
        to_entity: Optional[str] = None
        to_location: Optional[str] = None
        """
        actions = []

        # move
        for entity in self.entities:
            curr_loc = self.where_is_ent(entity)
            for loc in self.locations:
                if loc != curr_loc:
                    actions.append(
                        ActionSpec(
                            action="move",
                            entity=entity,
                            location=curr_loc,
                            to_location=loc,
                        )
                    )

        # pick
        for obj, obj_loc in self.object_loc.items():
            for ent, ent_loc in self.entity_loc.items():
                if obj_loc == ent_loc:
                    actions.append(
                        ActionSpec(action="pick", entity=ent, obj=obj, location=obj_loc)
                    )

        # drop
        for obj, obj_holder in self.object_holder.items():
            holder_loc = self.where_is_ent(obj_holder)
            actions.append(
                ActionSpec(
                    action="drop", entity=obj_holder, obj=obj, location=holder_loc
                )
            )

        # pass
        for obj, obj_holder in self.object_holder.items():
            holder_loc = self.where_is_ent(obj_holder)
            for ent, ent_loc in self.entity_loc.items():
                if ent != obj_holder and ent_loc == holder_loc:
                    actions.append(
                        ActionSpec(
                            action="pass",
                            entity=obj_holder,
                            obj=obj,
                            location=holder_loc,
                            to_entity=ent,
                        )
                    )

        return actions

    def enumerate_invalid_actions(self) -> list[ActionSpec]:
        """
        Enumerate all invalid actions
        Used for distractors
        """
        actions = []

        # pass
        # Passing to another entity that's not in the same location
        for obj, holder in self.object_holder.items():
            holder_loc = self.where_is_ent(holder)
            for ent, ent_loc in self.entity_loc.items():
                if ent != holder and ent_loc != holder_loc:
                    actions.append(
                        ActionSpec(
                            action="pass",
                            entity=holder,
                            obj=obj,
                            location=holder_loc,
                            to_entity=ent,
                        )
                    )
        # Passing object that the entity is not holding
        for ent1, ent1_loc in self.entity_loc.items():
            for ent2, ent2_loc in self.entity_loc.items():
                for obj, obj_loc in self.object_loc.items():
                    if ent1_loc == ent2_loc and ent1 != ent2:
                        actions.append(
                            ActionSpec(
                                action="pass",
                                entity=ent1,
                                obj=obj,
                                location=ent1_loc,
                                to_entity=ent2,
                            )
                        )

        # pick
        # Picking objects not in the same location
        for obj, obj_loc in self.object_loc.items():
            for ent, ent_loc in self.entity_loc.items():
                if obj_loc != ent_loc:
                    actions.append(
                        ActionSpec(action="pick", entity=ent, obj=obj, location=obj_loc)
                    )

        # Picking objects that's already held by another entity at the same location
        for obj, obj_holder in self.object_holder.items():
            obj_holder_loc = self.where_is_ent(obj_holder)
            for entity, ent_loc in self.entity_loc.items():
                if obj_holder_loc == ent_loc and entity != obj_holder:
                    actions.append(
                        ActionSpec(
                            action="pick", entity=entity, obj=obj, location=ent_loc
                        )
                    )

        return actions

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
            return ActionLog(
                action="none",
                error_log="Entity and object are not at the same location",
            )

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
        if init_loc == loc:
            return ActionLog(
                action="none", error_log="Entity must move to a different location"
            )
        self.assign_ent_loc(ent, loc)
        return ActionLog("move", entity=ent, location=init_loc, to_location=loc)

    def execute(self, spec: ActionSpec) -> ActionLog:
        """
        Given an actionspec, execute the action
        """
        if spec.action == "move":
            return self.move_entity(ent=spec.entity, loc=spec.to_location)
        elif spec.action == "pick":
            return self.pick_object(obj=spec.obj, ent=spec.entity)
        elif spec.action == "drop":
            return self.drop_object(obj=spec.obj)
        elif spec.action == "pass":
            return self.pass_obj(obj=spec.obj, ent=spec.to_entity)
        return ActionLog(action="none", error_log="Unknown Action")

    def validate(self) -> None:
        """
        Check every state's validity
        """
        # every entity must have exactly one location
        assert set(self.entity_loc.keys()) == set(self.entities)

        # every object must be either held or at a location, not both, not neither
        for obj in self.objects:
            in_holder = obj in self.object_holder
            in_loc = obj in self.object_loc
            assert in_holder != in_loc, f"{obj} must be either held or placed"

        # holders must be valid entities
        for obj, holder in self.object_holder.items():
            assert holder in self.entities, f"Invalid holder {holder} for {obj}"

        # object locations must be valid locations
        for obj, loc in self.object_loc.items():
            assert loc in self.locations, f"Invalid location {loc} for {obj}"

        # entity locations must be valid
        for ent, loc in self.entity_loc.items():
            assert loc in self.locations, f"Invalid location {loc} for {ent}"

    def take_snapshot(self):
        snapshot = {
            "objects": [],
            "entities": [],
            "relations": {
                "entity_location": dict(self.entity_loc),
                "object_location": dict(self.object_loc),
                "object_holder": dict(self.object_holder),
            },
        }

        for obj in self.objects:
            holder = self.who_has(obj)
            snapshot["objects"].append(
                {
                    "name": obj,
                    "is_held": holder is not None,
                    "holder": holder,
                    "location": self.where_is_obj(obj),
                }
            )

        for ent in self.entities:
            held_objects = [
                obj for obj, entity in self.object_holder.items() if entity == ent
            ]
            snapshot["entities"].append(
                {
                    "name": ent,
                    "location": self.where_is_ent(ent),
                    "holding_objects": held_objects,
                    "is_holding_object": len(held_objects) > 0,
                }
            )

        return snapshot
