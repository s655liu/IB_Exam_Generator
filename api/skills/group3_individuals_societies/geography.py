"""
Skill: IB Geography — HL and SL.  [Group 3: Individuals and Societies]

Prompt additions:
  - SVG for maps, demographic cycles, climate graphs, and landform diagrams.
"""
from __future__ import annotations
from ..base import BaseExamSkill


class GeographySkill(BaseExamSkill):
    subject_key = "Geography"
    output_language = "English"

    def get_instructions(self, level: str, paper: str, specs: dict) -> str:
        return (
            "- Use SVG for simple maps, demographic cycles, climate graphs, "
            "or landform diagrams."
        )
