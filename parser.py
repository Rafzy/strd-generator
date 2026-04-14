from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TemplateBank = list[tuple[str, int]]


@dataclass
class NarrationConfig:
    seed: int = 0
    include_initial_state: bool = True
    include_action_numbers: bool = True
    paragraph_mode: bool = False
    reveal_distractors: bool = False
    style: str = "natural"
    allow_contextual_phrasing: bool = True
    explicit_failed_distractors: bool = True


class EpisodeNarrator:
    LOCATION_PREPOSITIONS = {
        "Reception": "at",
        "Terrace": "on",
    }

    STYLE_GROUP_SIZE = {
        "canonical": 1,
        "varied": 2,
        "natural": 3,
    }

    FIRST_MARKERS = {
        "canonical": [
            ("First", 3),
            ("At first", 2),
            ("To begin with", 1),
        ],
        "varied": [
            ("First", 2),
            ("At first", 2),
            ("To begin with", 1),
            ("", 1),
        ],
        "natural": [
            ("First", 1),
            ("At first", 1),
            ("To begin with", 1),
            ("", 3),
        ],
    }

    NEXT_MARKERS = {
        "canonical": [
            ("Then", 3),
            ("After that", 2),
            ("Next", 2),
            ("Afterward", 1),
            ("Soon afterward", 1),
            ("Before long", 1),
        ],
        "varied": [
            ("Then", 2),
            ("After that", 2),
            ("Next", 2),
            ("Later", 1),
            ("Afterward", 1),
            ("Soon afterward", 1),
            ("Before long", 1),
            ("A little later", 1),
            ("", 2),
        ],
        "natural": [
            ("Then", 1),
            ("After that", 1),
            ("Next", 1),
            ("Later", 1),
            ("Afterward", 1),
            ("Soon afterward", 1),
            ("Before long", 1),
            ("A little later", 1),
            ("", 5),
        ],
    }

    INITIAL_HOLD_TEMPLATES: TemplateBank = [
        ("{holder} was carrying {objects} {loc}", 3),
        ("{holder} was holding {objects} {loc}", 2),
        ("{holder} had {objects} with them {loc}", 2),
    ]

    MOVE_TEMPLATES: TemplateBank = [
        ("{entity} moved from {src} to {dst}", 3),
        ("{entity} went from {src} to {dst}", 3),
        ("{entity} left {src} and headed to {dst}", 3),
        ("from {src}, {entity} made their way to {dst}", 1),
    ]

    PICK_TEMPLATES: TemplateBank = [
        ("{entity} picked up {obj} {loc}", 4),
        ("{loc}, {entity} picked up {obj}", 3),
        ("{entity} picked {obj} up {loc}", 2),
        ("{entity} took {obj} {loc}", 1),
    ]

    PICK_TEMPLATES_CONTEXT: TemplateBank = [
        ("still {loc}, {entity} picked up {obj}", 3),
        ("{entity} picked up {obj} while still {loc}", 2),
        ("still {loc}, {entity} picked {obj} up", 1),
    ]

    DROP_TEMPLATES: TemplateBank = [
        ("{entity} dropped {obj} {loc}", 3),
        ("{entity} set {obj} down {loc}", 3),
        ("{loc}, {entity} put {obj} down", 2),
    ]

    DROP_TEMPLATES_CONTEXT: TemplateBank = [
        ("still {loc}, {entity} dropped {obj}", 3),
        ("{entity} set {obj} down while still {loc}", 2),
    ]

    PASS_TEMPLATES: TemplateBank = [
        ("{entity} handed {obj} to {to_entity} {loc}", 4),
        ("{entity} passed {obj} to {to_entity} {loc}", 3),
        ("{loc}, {entity} gave {obj} to {to_entity}", 2),
        ("{to_entity} received {obj} from {entity} {loc}", 1),
    ]

    PASS_TEMPLATES_CONTEXT: TemplateBank = [
        ("still {loc}, {entity} handed {obj} to {to_entity}", 3),
        ("{entity} passed {obj} to {to_entity} while still {loc}", 2),
    ]

    FAILED_PASS_NO_OBJECT: TemplateBank = [
        (
            "{entity} tried to hand {obj} to {to_entity} {loc}, but "
            "{entity} did not have it",
            3,
        ),
        (
            "{entity} attempted to pass {obj} to {to_entity} {loc}, but "
            "{entity} was not carrying it",
            2,
        ),
    ]

    FAILED_PASS_RECIPIENT_MISSING: TemplateBank = [
        (
            "{entity} tried to hand {obj} to {to_entity} {loc}, but "
            "{to_entity} was not there",
            3,
        ),
        (
            "{entity} attempted to pass {obj} to {to_entity} {loc}, but "
            "{to_entity} was not {loc}",
            2,
        ),
    ]

    FAILED_PICK_NOT_THERE: TemplateBank = [
        (
            "{entity} tried to pick up {obj} {loc}, but it was not there",
            3,
        ),
        (
            "{entity} attempted to take {obj} {loc}, but {obj} was not there",
            2,
        ),
    ]

    FAILED_PICK_ALREADY_HELD: TemplateBank = [
        (
            "{entity} tried to pick up {obj} {loc}, but {holder} already had it",
            3,
        ),
        (
            "{entity} attempted to take {obj} {loc}, but {holder} was already "
            "holding it",
            2,
        ),
    ]

    FAILED_DROP_NOT_HELD: TemplateBank = [
        (
            "{entity} tried to put down {obj} {loc}, but was not carrying it",
            3,
        ),
        (
            "{entity} attempted to drop {obj} {loc}, but did not have it",
            2,
        ),
    ]

    FAILED_MOVE_WRONG_SOURCE: TemplateBank = [
        (
            "{entity} tried to leave {src} for {dst}, but was actually {actual}",
            3,
        ),
        (
            "{entity} set out from {src} toward {dst}, but was really {actual}",
            1,
        ),
    ]

    FAILED_MOVE_GENERIC: TemplateBank = [
        (
            "{entity} tried to go from {src} to {dst}, but the move did not happen",
            3,
        ),
    ]

    def __init__(
        self,
        episode: dict[str, Any],
        config: NarrationConfig | None = None,
    ) -> None:
        self.episode = episode
        self.config = config or NarrationConfig()
        self.rng = random.Random(self.config.seed)

        if self.config.style not in self.STYLE_GROUP_SIZE:
            raise ValueError("style must be one of: canonical, varied, natural")

        self.entity_order = {
            name: i for i, name in enumerate(self.episode["world"]["entities"])
        }
        self.object_order = {
            name: i for i, name in enumerate(self.episode["world"]["objects"])
        }
        self.location_order = {
            name: i for i, name in enumerate(self.episode["world"]["locations"])
        }

        self._last_marker: str | None = None
        self._pre_action_snapshots = self.build_pre_action_snapshots()

    def build_pre_action_snapshots(self) -> dict[int, dict[str, Any]]:
        timeline = {
            item["order"]: item["snapshot"] for item in self.episode.get("timeline", [])
        }
        actions = sorted(self.episode["actions"], key=lambda x: x["order"])

        pre_snapshots: dict[int, dict[str, Any]] = {}
        previous_snapshot = self.episode["initial_state"]

        for action in actions:
            pre_snapshots[action["order"]] = previous_snapshot
            previous_snapshot = timeline.get(action["order"], previous_snapshot)

        return pre_snapshots

    @staticmethod
    def humanize_common(name: str) -> str:
        name = name.replace("_", " ")
        name = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)
        return re.sub(r"\s+", " ", name).strip().lower()

    @staticmethod
    def humanize_proper(name: str) -> str:
        name = name.replace("_", " ")
        name = re.sub(r"(?<!^)(?=[A-Z])", " ", name)
        return re.sub(r"\s+", " ", name).strip()

    @staticmethod
    def sentence_case(text: str) -> str:
        if not text:
            return text
        return text[0].upper() + text[1:]

    @staticmethod
    def oxford_join(items: list[str]) -> str:
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        return f"{', '.join(items[:-1])}, and {items[-1]}"

    @staticmethod
    def chunked(items: list[str], size: int) -> list[list[str]]:
        return [items[i : i + size] for i in range(0, len(items), size)]

    @staticmethod
    def join_clauses(clauses: list[str]) -> str:
        if not clauses:
            return ""
        if len(clauses) == 1:
            return clauses[0]
        if len(clauses) == 2:
            return f"{clauses[0]}, and {clauses[1]}"
        return f"{'; '.join(clauses[:-1])}; and {clauses[-1]}"

    def weighted_choice(self, items: TemplateBank) -> str:
        options, weights = zip(*items)
        return self.rng.choices(options, weights=weights, k=1)[0]

    def entity_name(self, name: str) -> str:
        return self.humanize_proper(name)

    def object_np(self, obj_name: str) -> str:
        return f"the {self.humanize_common(obj_name)}"

    def place_np(self, location: str) -> str:
        return f"the {self.humanize_common(location)}"

    def place_pp(self, location: str) -> str:
        prep = self.LOCATION_PREPOSITIONS.get(location, "in")
        return f"{prep} {self.place_np(location)}"

    def choose_marker(self, index: int) -> str:
        if index == 0:
            bank = self.FIRST_MARKERS[self.config.style]
        else:
            bank = self.NEXT_MARKERS[self.config.style]

        if self._last_marker:
            filtered = [
                item for item in bank if item[0] != self._last_marker or item[0] == ""
            ]
            bank = filtered or bank

        marker = self.weighted_choice(bank)
        self._last_marker = marker or None
        return marker

    def finalize_clause(self, clause: str, marker: str) -> str:
        if marker:
            return f"{marker}, {clause}."
        return f"{self.sentence_case(clause)}."

    def entity_location_in(
        self,
        snapshot: dict[str, Any],
        entity: str,
    ) -> str:
        return snapshot["relations"]["entity_location"][entity]

    def object_holder_in(
        self,
        snapshot: dict[str, Any],
        obj: str,
    ) -> str | None:
        return snapshot["relations"]["object_holder"].get(obj)

    def object_location_in(
        self,
        snapshot: dict[str, Any],
        obj: str,
    ) -> str | None:
        holder = self.object_holder_in(snapshot, obj)
        if holder is not None:
            return self.entity_location_in(snapshot, holder)

        location = snapshot["relations"]["object_location"].get(obj)
        if location is not None:
            return location

        for item in snapshot.get("objects", []):
            if item["name"] == obj:
                if item["is_held"] and item["holder"] is not None:
                    return self.entity_location_in(snapshot, item["holder"])
                return item["location"]

        return None

    @staticmethod
    def resulting_location(action: dict[str, Any]) -> str:
        if action["action"] == "move":
            return action["to_location"]
        return action["location"]

    def same_entity_same_location_as_previous(
        self,
        action: dict[str, Any],
        previous_action: dict[str, Any] | None,
    ) -> bool:
        if previous_action is None:
            return False
        if action["entity"] != previous_action["entity"]:
            return False

        current_loc = action["location"]
        previous_result_loc = self.resulting_location(previous_action)
        return current_loc == previous_result_loc

    def use_context(
        self,
        action: dict[str, Any],
        previous_action: dict[str, Any] | None,
    ) -> bool:
        if not self.config.allow_contextual_phrasing:
            return False
        if self.config.style == "canonical":
            return False
        return self.same_entity_same_location_as_previous(
            action,
            previous_action,
        )

    def describe_initial_state(self) -> list[str]:
        state = self.episode["initial_state"]

        entity_locations: dict[str, list[str]] = {}
        held_by_entity: dict[str, list[str]] = {}
        dropped_by_location: dict[str, list[str]] = {}

        entity_location_lookup = {
            ent["name"]: ent["location"] for ent in state["entities"]
        }

        for ent in state["entities"]:
            entity_locations.setdefault(ent["location"], []).append(ent["name"])

        for obj in state["objects"]:
            if obj["is_held"]:
                held_by_entity.setdefault(obj["holder"], []).append(obj["name"])
            else:
                dropped_by_location.setdefault(obj["location"], []).append(obj["name"])

        for location, names in entity_locations.items():
            names.sort(key=lambda x: self.entity_order[x])

        for holder, objects in held_by_entity.items():
            objects.sort(key=lambda x: self.object_order[x])

        for location, objects in dropped_by_location.items():
            objects.sort(key=lambda x: self.object_order[x])

        sentences: list[str] = []
        group_size = self.STYLE_GROUP_SIZE[self.config.style]

        location_clauses: list[str] = []
        ordered_locations = sorted(
            entity_locations.keys(),
            key=lambda x: self.location_order[x],
        )
        for location in ordered_locations:
            names = entity_locations[location]
            subject = self.oxford_join([self.entity_name(name) for name in names])
            verb = "was" if len(names) == 1 else "were"
            location_clauses.append(f"{subject} {verb} {self.place_pp(location)}")

        for idx, group in enumerate(self.chunked(location_clauses, group_size)):
            sentence = self.join_clauses(group)
            if idx == 0:
                sentence = f"At the beginning, {sentence}"
            sentences.append(f"{sentence}.")

        ordered_holders = sorted(
            held_by_entity.keys(),
            key=lambda x: self.entity_order[x],
        )
        for holder in ordered_holders:
            objects = held_by_entity[holder]
            object_text = self.oxford_join([self.object_np(obj) for obj in objects])
            location = entity_location_lookup[holder]
            template = self.weighted_choice(self.INITIAL_HOLD_TEMPLATES)
            sentence = template.format(
                holder=self.entity_name(holder),
                objects=object_text,
                loc=self.place_pp(location),
            )
            sentences.append(f"{sentence}.")

        dropped_clauses: list[str] = []
        ordered_drop_locations = sorted(
            dropped_by_location.keys(),
            key=lambda x: self.location_order[x],
        )
        for location in ordered_drop_locations:
            objects = dropped_by_location[location]
            object_text = self.oxford_join([self.object_np(obj) for obj in objects])
            verb = "was" if len(objects) == 1 else "were"
            dropped_clauses.append(
                f"{object_text} {verb} lying {self.place_pp(location)}"
            )

        for group in self.chunked(dropped_clauses, group_size):
            sentence = self.join_clauses(group)
            sentences.append(f"{self.sentence_case(sentence)}.")

        return sentences

    def render_move_clause(self, action: dict[str, Any]) -> str:
        template = self.weighted_choice(self.MOVE_TEMPLATES)
        return template.format(
            entity=self.entity_name(action["entity"]),
            src=self.place_np(action["location"]),
            dst=self.place_np(action["to_location"]),
        )

    def render_pick_clause(
        self,
        action: dict[str, Any],
        previous_action: dict[str, Any] | None,
    ) -> str:
        contextual = self.use_context(action, previous_action)
        templates = self.PICK_TEMPLATES_CONTEXT if contextual else self.PICK_TEMPLATES
        template = self.weighted_choice(templates)
        return template.format(
            entity=self.entity_name(action["entity"]),
            obj=self.object_np(action["obj"]),
            loc=self.place_pp(action["location"]),
        )

    def render_drop_clause(
        self,
        action: dict[str, Any],
        previous_action: dict[str, Any] | None,
    ) -> str:
        contextual = self.use_context(action, previous_action)
        templates = self.DROP_TEMPLATES_CONTEXT if contextual else self.DROP_TEMPLATES
        template = self.weighted_choice(templates)
        return template.format(
            entity=self.entity_name(action["entity"]),
            obj=self.object_np(action["obj"]),
            loc=self.place_pp(action["location"]),
        )

    def render_pass_clause(
        self,
        action: dict[str, Any],
        previous_action: dict[str, Any] | None,
    ) -> str:
        contextual = self.use_context(action, previous_action)
        templates = self.PASS_TEMPLATES_CONTEXT if contextual else self.PASS_TEMPLATES
        template = self.weighted_choice(templates)
        return template.format(
            entity=self.entity_name(action["entity"]),
            obj=self.object_np(action["obj"]),
            to_entity=self.entity_name(action["to_entity"]),
            loc=self.place_pp(action["location"]),
        )

    def render_failed_move_clause(
        self,
        action: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> str:
        actual_location = self.entity_location_in(snapshot, action["entity"])

        if actual_location != action["location"]:
            template = self.weighted_choice(self.FAILED_MOVE_WRONG_SOURCE)
            return template.format(
                entity=self.entity_name(action["entity"]),
                src=self.place_np(action["location"]),
                dst=self.place_np(action["to_location"]),
                actual=self.place_pp(actual_location),
            )

        template = self.weighted_choice(self.FAILED_MOVE_GENERIC)
        return template.format(
            entity=self.entity_name(action["entity"]),
            src=self.place_np(action["location"]),
            dst=self.place_np(action["to_location"]),
        )

    def render_failed_pick_clause(
        self,
        action: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> str:
        holder = self.object_holder_in(snapshot, action["obj"])
        object_location = self.object_location_in(snapshot, action["obj"])

        if holder is not None and holder != action["entity"]:
            template = self.weighted_choice(self.FAILED_PICK_ALREADY_HELD)
            return template.format(
                entity=self.entity_name(action["entity"]),
                obj=self.object_np(action["obj"]),
                loc=self.place_pp(action["location"]),
                holder=self.entity_name(holder),
            )

        template = self.weighted_choice(self.FAILED_PICK_NOT_THERE)
        return template.format(
            entity=self.entity_name(action["entity"]),
            obj=self.object_np(action["obj"]),
            loc=self.place_pp(action["location"]),
            actual_loc=(
                self.place_pp(object_location)
                if object_location is not None
                else "somewhere else"
            ),
        )

    def render_failed_drop_clause(
        self,
        action: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> str:
        holder = self.object_holder_in(snapshot, action["obj"])

        if holder != action["entity"]:
            template = self.weighted_choice(self.FAILED_DROP_NOT_HELD)
            return template.format(
                entity=self.entity_name(action["entity"]),
                obj=self.object_np(action["obj"]),
                loc=self.place_pp(action["location"]),
            )

        template = self.weighted_choice(self.FAILED_DROP_NOT_HELD)
        return template.format(
            entity=self.entity_name(action["entity"]),
            obj=self.object_np(action["obj"]),
            loc=self.place_pp(action["location"]),
        )

    def render_failed_pass_clause(
        self,
        action: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> str:
        holder = self.object_holder_in(snapshot, action["obj"])
        recipient_location = self.entity_location_in(snapshot, action["to_entity"])

        if holder != action["entity"]:
            template = self.weighted_choice(self.FAILED_PASS_NO_OBJECT)
            return template.format(
                entity=self.entity_name(action["entity"]),
                obj=self.object_np(action["obj"]),
                to_entity=self.entity_name(action["to_entity"]),
                loc=self.place_pp(action["location"]),
            )

        if recipient_location != action["location"]:
            template = self.weighted_choice(self.FAILED_PASS_RECIPIENT_MISSING)
            return template.format(
                entity=self.entity_name(action["entity"]),
                obj=self.object_np(action["obj"]),
                to_entity=self.entity_name(action["to_entity"]),
                loc=self.place_pp(action["location"]),
            )

        template = self.weighted_choice(self.FAILED_PASS_RECIPIENT_MISSING)
        return template.format(
            entity=self.entity_name(action["entity"]),
            obj=self.object_np(action["obj"]),
            to_entity=self.entity_name(action["to_entity"]),
            loc=self.place_pp(action["location"]),
        )

    def render_failed_action_clause(self, action: dict[str, Any]) -> str:
        snapshot = self._pre_action_snapshots.get(
            action["order"],
            self.episode["initial_state"],
        )
        action_type = action["action"]

        if action_type == "move":
            return self.render_failed_move_clause(action, snapshot)
        if action_type == "pick":
            return self.render_failed_pick_clause(action, snapshot)
        if action_type == "drop":
            return self.render_failed_drop_clause(action, snapshot)
        if action_type == "pass":
            return self.render_failed_pass_clause(action, snapshot)

        return f"{self.entity_name(action['entity'])} attempted an action that failed"

    def render_action(
        self,
        action: dict[str, Any],
        index: int,
        previous_action: dict[str, Any] | None,
    ) -> str:
        marker = self.choose_marker(index)

        if action["distractor_action"] and self.config.explicit_failed_distractors:
            clause = self.render_failed_action_clause(action)
        else:
            action_type = action["action"]

            if action_type == "move":
                clause = self.render_move_clause(action)
            elif action_type == "pick":
                clause = self.render_pick_clause(action, previous_action)
            elif action_type == "drop":
                clause = self.render_drop_clause(action, previous_action)
            elif action_type == "pass":
                clause = self.render_pass_clause(action, previous_action)
            else:
                clause = (
                    f"{self.entity_name(action['entity'])} performed an unknown action"
                )

        sentence = self.finalize_clause(clause, marker)

        if self.config.include_action_numbers:
            sentence = f"[Action {action['order']}] {sentence}"

        if self.config.reveal_distractors and action["distractor_action"]:
            sentence += " [DISTRACTOR]"

        return sentence

    def render(self) -> str:
        initial_sentences: list[str] = []
        if self.config.include_initial_state:
            initial_sentences = self.describe_initial_state()

        actions = sorted(
            self.episode["actions"],
            key=lambda x: x["order"],
        )

        action_sentences: list[str] = []
        previous_action: dict[str, Any] | None = None
        for index, action in enumerate(actions):
            action_sentences.append(self.render_action(action, index, previous_action))
            previous_action = action

        if self.config.paragraph_mode:
            paragraphs: list[str] = []
            if initial_sentences:
                paragraphs.append(" ".join(initial_sentences))
            if action_sentences:
                paragraphs.append(" ".join(action_sentences))
            return "\n\n".join(paragraphs)

        return "\n".join([*initial_sentences, *action_sentences])


def load_episode(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert an episode JSON file into natural language."
    )
    parser.add_argument("episode_json", type=str, help="Path to episode JSON")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--style",
        type=str,
        default="natural",
        choices=["canonical", "varied", "natural"],
        help="Narration style",
    )
    parser.add_argument(
        "--no-initial-state",
        action="store_true",
        help="Omit the initial state description",
    )
    parser.add_argument(
        "--no-action-numbers",
        action="store_true",
        help="Omit action number prefixes",
    )
    parser.add_argument(
        "--paragraph",
        action="store_true",
        help="Render as paragraphs instead of line-by-line text",
    )
    parser.add_argument(
        "--reveal-distractors",
        action="store_true",
        help="Append a distractor tag for debugging",
    )
    parser.add_argument(
        "--no-contextual-phrasing",
        action="store_true",
        help="Disable phrases like 'still in the pantry'",
    )
    parser.add_argument(
        "--no-explicit-failed-distractors",
        action="store_true",
        help=(
            "Do not narrate distractors as failed attempts. Use this only if your "
            "distractor actions should be rendered as normal actions."
        ),
    )

    args = parser.parse_args()

    episode = load_episode(args.episode_json)
    config = NarrationConfig(
        seed=args.seed,
        include_initial_state=not args.no_initial_state,
        include_action_numbers=not args.no_action_numbers,
        paragraph_mode=args.paragraph,
        reveal_distractors=args.reveal_distractors,
        style=args.style,
        allow_contextual_phrasing=not args.no_contextual_phrasing,
        explicit_failed_distractors=not args.no_explicit_failed_distractors,
    )

    narrator = EpisodeNarrator(episode, config)
    print(narrator.render())


if __name__ == "__main__":
    main()
