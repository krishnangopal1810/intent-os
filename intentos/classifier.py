"""Multi-app behavior classifier for IntentOS ActivityEvents."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from intentos.activity import ActivityEvent
from intentos.classifier_context import classification_text, context_cues


class BehaviorLabel(str, Enum):
    DEEP_WORK = "deep_work"
    SHALLOW_WORK = "shallow_work"
    LEARNING = "learning"
    COMMUNICATION = "communication"
    ADMIN = "admin"
    PASSIVE_CONSUMPTION = "passive_consumption"
    ACTIVE_CREATION = "active_creation"
    ENTERTAINMENT = "entertainment"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ActivityClassification:
    label: BehaviorLabel
    confidence: float
    reason: str
    scores: dict[BehaviorLabel, int]


LABEL_CUES: dict[BehaviorLabel, dict[str, int]] = {
    BehaviorLabel.DEEP_WORK: {
        "debug": 3,
        "debugging": 3,
        "failing": 1,
        "implement": 3,
        "implementation": 2,
        "classifier": 2,
        "coding": 3,
        "code": 2,
        "vscode": 2,
        "vs code": 2,
        "sublime": 2,
        "tests": 1,
        "unit test": 2,
        "unittest": 2,
        "pull request": 2,
        "github repository": 3,
        "intent-os": 3,
        "intentos": 3,
    },
    BehaviorLabel.SHALLOW_WORK: {
        "inbox": 3,
        "triage": 3,
        "calendar": 2,
        "lightweight": 2,
        "status update": 2,
    },
    BehaviorLabel.LEARNING: {
        "explain": 3,
        "learning": 3,
        "lecture": 3,
        "tutorial": 3,
        "deep dive": 3,
        "research": 2,
        "profile": 1,
        "strategy": 1,
        "system design": 3,
        "transformers": 2,
        "attention": 2,
        "examples": 1,
        "bazel": 3,
        "documentation": 2,
        "docs": 1,
        "external dependencies": 2,
        "guide": 2,
        "style guide": 3,
    },
    BehaviorLabel.COMMUNICATION: {
        "whatsapp": 3,
        "slack": 3,
        "messages": 2,
        "coordinate": 3,
        "coordination": 3,
        "sync": 2,
        "planning": 1,
        "family group": 2,
    },
    BehaviorLabel.ADMIN: {
        "admin": 2,
        "income tax": 4,
        "tax": 3,
        "e-filing": 4,
        "submit return": 3,
        "bill": 3,
        "payment": 3,
        "bank": 2,
        "portal": 1,
        "amazon": 2,
        "brunch": 2,
        "cafe": 2,
        "fitbit": 2,
        "locations": 2,
        "murukku": 2,
        "pixel watch": 2,
        "pressure cooker": 2,
        "restaurant": 2,
        "rice cooker": 2,
        "secondary market": 3,
        "share price": 2,
        "shopping": 2,
        "stock": 2,
        "visa": 3,
    },
    BehaviorLabel.PASSIVE_CONSUMPTION: {
        "feed": 3,
        "scroll": 3,
        "scrolling": 3,
        "doomscrolling": 4,
        "reels": 4,
        "timeline": 2,
        "short video": 3,
        "x.com/home": 2,
        "x.com/status": 2,
        "instagram": 2,
        "stories": 2,
        "linkedin.com/feed": 2,
    },
    BehaviorLabel.ACTIVE_CREATION: {
        "draft": 3,
        "notes": 2,
        "writing": 3,
        "design": 1,
        "document": 1,
        "taxonomy": 1,
    },
    BehaviorLabel.ENTERTAINMENT: {
        "fun": 2,
        "silly": 3,
        "story": 1,
        "laugh": 3,
        "compilation": 3,
        "funny": 2,
        "gaming": 3,
        "highlights": 2,
        "asia cup": 3,
        "cricket": 3,
        "england v india": 3,
        "india vs pakistan": 3,
        "ipl": 3,
        "lord's test": 3,
        "nail-biting": 2,
        "reaction": 2,
        "entertainment": 3,
    },
}

def classify_event(event: ActivityEvent) -> ActivityClassification:
    text = classification_text(event)
    matches = score_event(event, text)
    scores = {label: sum(cues.values()) for label, cues in matches.items()}
    nonzero = {label: score for label, score in scores.items() if score > 0}

    if not nonzero:
        return ActivityClassification(
            label=BehaviorLabel.UNKNOWN,
            confidence=0.35,
            reason="No strong behavior cues were present.",
            scores=scores,
        )

    ranked = sorted(nonzero.items(), key=lambda item: item[1], reverse=True)
    best_label, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0
    if best_score - second_score <= 1:
        return ActivityClassification(
            label=BehaviorLabel.UNKNOWN,
            confidence=0.45,
            reason=(
                "Behavior cues were too close to force a label: "
                f"{format_top_scores(ranked)}."
            ),
            scores=scores,
        )

    confidence = min(0.95, 0.55 + ((best_score - second_score) * 0.08))
    cues = ", ".join(sorted(matches[best_label])) or best_label.value
    return ActivityClassification(
        label=best_label,
        confidence=round(confidence, 2),
        reason=f"Classified as {best_label.value} because it matched: {cues}.",
        scores=scores,
    )


def score_labels(text: str) -> dict[BehaviorLabel, dict[str, int]]:
    return {
        label: {cue: weight for cue, weight in cues.items() if cue in text}
        for label, cues in LABEL_CUES.items()
    }


def score_event(event: ActivityEvent, text: str) -> dict[BehaviorLabel, dict[str, int]]:
    matches = score_labels(text)
    for label_value, cues in context_cues(event, text).items():
        label = BehaviorLabel(label_value)
        for cue, weight in cues.items():
            matches[label][cue] = max(matches[label].get(cue, 0), weight)
    return matches


def format_top_scores(ranked: list[tuple[BehaviorLabel, int]]) -> str:
    return ", ".join(f"{label.value}={score}" for label, score in ranked[:3])
