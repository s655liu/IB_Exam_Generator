"""
Skill: IB Mandarin B — HL and SL.  [Group 2: Language Acquisition]

Extends LanguageBSkill with Mandarin-specific length requirements:
  - HL Paper 2: transcripts and reading texts must be ≥ 1200 characters.
  - SL Paper 2: standard 450-600 words.
"""
from __future__ import annotations
from .language_b import LanguageBSkill


class MandarinBSkill(LanguageBSkill):
    subject_key = "Mandarin_B"
    target_language = "Chinese (Simplified)"

    def _get_length_instruction(self, level: str) -> str:
        if level == "HL":
            return (
                "1200 characters (MUST be extremely detailed and complex, matching the length "
                "of a professional literary essay)"
            )
        return "450-600 words"
