"""
Shared base skill for IB Science subjects.  [Group 4: Sciences]

Physics, Chemistry, and Biology all share identical paper formats:
  - Paper 1A: Multiple choice (calculator allowed on some)
  - Paper 1B: Data-based / experimental design (written analysis)
  - Paper 2 / 3: Structured and extended response

Subclasses set `subject_display_name` for the data-booklet reference line.
"""
from __future__ import annotations
from ..base import BaseExamSkill


class ScienceSkill(BaseExamSkill):
    """
    Shared logic for Physics, Chemistry, and Biology.

    Subclasses must set:
      subject_key          – e.g. "Physics"
      subject_display_name – e.g. "Physics"  (used in the data booklet line)
    """

    subject_key: str = ""
    subject_display_name: str = ""

    def get_instructions(self, level: str, paper: str, specs: dict) -> str:
        calc_str = (
            "CALCULATOR ALLOWED (GDC)" if specs.get("calculator") else "NO CALCULATORS ALLOWED"
        )
        instructions = (
            f"- **{calc_str}**.\n"
            f"- Reference relevant data from the IB {self.subject_display_name} Data Booklet.\n"
            "- Inline math → LATEX<<formula>>       e.g. LATEX<<F = ma>>, LATEX<<E = hf>>\n"
            "- Display math → LATEXBLOCK<<formula>>  e.g. LATEXBLOCK<<\\Delta G = \\Delta H - T\\Delta S>>"
        )

        if "Paper 1A" in paper:
            instructions += (
                "\n- **FORMAT**: Multiple Choice Questions only.\n"
                "- Provide 4 options (A, B, C, D) for each question.\n"
                "- Focus on core conceptual understanding and quick calculations."
            )
        elif "Paper 1B" in paper:
            selected_skills = specs.get("selected_skills", [])
            skills_str = (
                ", ".join(selected_skills) if selected_skills else "general experimental design"
            )
            instructions += (
                "\n- **FORMAT**: Data analysis and experimental design questions.\n"
                "- **STRICT**: This is NOT multiple choice. Provide structured questions "
                "requiring written analysis.\n"
                "- **TABLES**: Present experimental data in standard Markdown tables "
                "(properly formatted with newlines).\n"
                f"- **SKILLS FOCUS**: Focus heavily on the following selected skills: {skills_str}.\n"
                "- Include questions on: error analysis, graph interpretation, variable "
                "identification, and methodology evaluation.\n"
                "- Use SVG for experimental setups or data plots."
            )

        instructions += (
            "\n- **DIFFICULTY GRADIENT (SCALING)**: \n"
            "  1. Within each multi-part question, parts (a), (b), (c), etc., must strictly "
            "increase in difficulty and cognitive demand "
            "(e.g., recall → application → complex evaluation).\n"
            "  2. The overall paper should be structured so that earlier questions are more "
            "accessible, while later questions increasingly require synthesis of multiple "
            "topics and higher-order thinking."
        )
        return instructions
