"""
Skill: IB English Literature A — HL and SL.  [Group 1: Language and Literature]

Paper-specific behaviour:
  Paper 1  – Unseen textual analysis (standard essay_choice rules apply via base class).
  Paper 2  – Comparative essay.
             If the student provides prescribed_texts, the prompts are tailored to those works.
             Always requires a full model essay with examiner commentary and grade breakdown
             per IB criterion.
"""
from __future__ import annotations
from ..base import BaseExamSkill


class EnglishLitASkill(BaseExamSkill):
    subject_key = "English_Literature_A"
    output_language = "English"

    def get_instructions(self, level: str, paper: str, specs: dict) -> str:
        return ""

    def get_prompt_overrides(self, request, specs: dict) -> dict:
        q_count = specs.get("question_count", "5")

        structure_rule = (
            f"\n- **STRICT QUESTION COUNT**: You MUST provide EXACTLY {q_count} essay "
            f"prompts/options. The user will choose 1 of these {q_count} prompts."
        )

        # Inject prescribed texts when provided (Paper 2 comparative essays)
        if request.prescribed_texts and len(request.prescribed_texts) >= 2:
            texts = [t for t in request.prescribed_texts if t.strip()]
            texts_str = " and ".join(texts)
            if texts_str:
                structure_rule += (
                    f"\n- **CUSTOM CONTEXT**: The student has specifically studied: {texts_str}. "
                    "Tailor the essay prompts to be highly relevant to exploring themes, "
                    "techniques, or contexts found in these works."
                )

        model_essay_req = (
            "\n- **MODEL ESSAY & GRADING**: Inside the [SECTION_MARK_SCHEME], you MUST provide "
            "ONE FULL, HIGH-LEVEL sample essay response for at least one of the generated prompts. "
            "IMMEDIATELY FOLLOWING the essay, provide a detailed **EXAMINER COMMENTARY AND GRADE**. "
            "Break down the marks for each IB Criterion (e.g., Criterion A, B, C, D) and provide "
            "a 2-3 sentence justification for the marks in each category."
        )

        return {"structure_rule": structure_rule, "model_essay_req": model_essay_req}
