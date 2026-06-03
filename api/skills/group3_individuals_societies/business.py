"""
Skill: IB Business Management — HL and SL.  [Group 3: Individuals and Societies]

Prompt additions:
  - Mermaid for organizational charts, flowcharts, and network diagrams.
  - SVG for supply/demand curves and break-even charts.
"""
from __future__ import annotations
from ..base import BaseExamSkill


class BusinessSkill(BaseExamSkill):
    subject_key = "Business"
    output_language = "English"

    def get_instructions(self, level: str, paper: str, specs: dict) -> str:
        return (
            "- Use Mermaid for network diagrams, flowcharts, or organizational charts.\n"
            "- Use SVG for supply/demand curves or break-even charts where appropriate."
        )
