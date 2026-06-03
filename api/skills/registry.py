"""
Skill registry — maps IB subject name strings to skill instances.

Skills are organized by IB subject group:
  Group 1: Language and Literature  → group1_language_literature/
  Group 2: Language Acquisition     → group2_language_acquisition/
  Group 3: Individuals & Societies  → group3_individuals_societies/
  Group 4: Sciences                 → group4_sciences/
  Group 5: Mathematics              → group5_mathematics/

Usage:
    from skills.registry import get_skill
    skill = get_skill("Math AA")
"""
from __future__ import annotations
from .base import BaseExamSkill

# Group 1: Language and Literature
from .group1_language_literature.english_lit_a import EnglishLitASkill

# Group 2: Language Acquisition
from .group2_language_acquisition.french_b import FrenchBSkill
from .group2_language_acquisition.spanish_b import SpanishBSkill
from .group2_language_acquisition.mandarin_b import MandarinBSkill

# Group 3: Individuals and Societies
from .group3_individuals_societies.history import HistorySkill
from .group3_individuals_societies.geography import GeographySkill
from .group3_individuals_societies.business import BusinessSkill
from .group3_individuals_societies.itgs import ITGSSkill

# Group 4: Sciences
from .group4_sciences.physics import PhysicsSkill
from .group4_sciences.chemistry import ChemistrySkill
from .group4_sciences.biology import BiologySkill

# Group 5: Mathematics
from .group5_mathematics.math_aa import MathAASkill


# ---------------------------------------------------------------------------
# Registry — subject name (as used in the UI / API) → skill instance
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, BaseExamSkill] = {
    # Group 1
    "English Literature A": EnglishLitASkill(),

    # Group 2
    "French B":   FrenchBSkill(),
    "Spanish B":  SpanishBSkill(),
    "Mandarin B": MandarinBSkill(),

    # Group 3
    "History":             HistorySkill(),
    "Geography":           GeographySkill(),
    "Business Management": BusinessSkill(),
    "ITGS":                ITGSSkill(),

    # Group 4
    "Physics":   PhysicsSkill(),
    "Chemistry": ChemistrySkill(),
    "Biology":   BiologySkill(),

    # Group 5
    "Math AA": MathAASkill(),
}

_FALLBACK = BaseExamSkill()


def get_skill(subject: str) -> BaseExamSkill:
    """
    Return the skill for the given subject name.

    Falls back to BaseExamSkill (no special instructions) for any subject
    not found in the registry — ensuring the generator never raises a KeyError.
    """
    return _REGISTRY.get(subject, _FALLBACK)


def list_subjects() -> list[str]:
    """Return all registered subject names (useful for debugging / tests)."""
    return list(_REGISTRY.keys())
