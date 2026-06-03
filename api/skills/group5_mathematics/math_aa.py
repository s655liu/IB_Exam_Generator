"""
Skill: Mathematics Analysis and Approaches (Math AA) — HL and SL.
[Group 5: Mathematics]

Prompt additions:
  - LaTeX for all mathematical notation
  - SVG for coordinate graphs and statistical charts
  - Difficulty progression within and across the paper
  - Explicit calculator / no-calculator statement
"""
from __future__ import annotations
from ..base import BaseExamSkill


class MathAASkill(BaseExamSkill):
    subject_key = "Mathematics_AA"
    output_language = "English"

    def get_instructions(self, level: str, paper: str, specs: dict) -> str:
        calc_str = (
            "CALCULATOR ALLOWED (GDC)" if specs.get("calculator") else "NO CALCULATORS ALLOWED"
        )
        return (
            f"- **{calc_str}**.\n"
            "- Show all working clearly.\n"
            "- Inline math → LATEX<<formula>>      e.g. LATEX<<x^{2} + 1>>, LATEX<<\\frac{a}{b}>>\n"
            "- Display math → LATEXBLOCK<<formula>> e.g. LATEXBLOCK<<\\int_{0}^{\\infty} e^{-x}\\,dx = 1>>\n"
            "- Use SVG for coordinate graphs, geometric shapes, and statistical charts "
            "where appropriate.\n"
            "- **DIFFICULTY PROGRESSION**: \n"
            "  1. Ensure each multi-part question follows a 'low floor, high ceiling' "
            "approach — starting with accessible marks and concluding with more demanding "
            "proofs or problem-solving.\n"
            "  2. The paper should grow in complexity, moving from standard routine problems "
            "to non-routine or unfamiliar contexts (especially for Section B)."
        )
