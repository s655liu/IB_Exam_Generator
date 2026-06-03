"""
Skill: IB Information Technology in a Global Society (ITGS) — HL and SL.
[Group 3: Individuals and Societies]

Prompt additions:
  - Mermaid for network diagrams, data-flow diagrams, and system flowcharts.
"""
from __future__ import annotations
from ..base import BaseExamSkill


class ITGSSkill(BaseExamSkill):
    subject_key = "ITGS"
    output_language = "English"

    def get_instructions(self, level: str, paper: str, specs: dict) -> str:
        return "- Use Mermaid for network diagrams, flowcharts, or organizational charts."
