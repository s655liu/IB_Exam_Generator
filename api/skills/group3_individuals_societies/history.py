"""
Skill: IB History — HL and SL.  [Group 3: Individuals and Societies]

Paper-specific behaviour:
  Paper 1  – Source-based questions (4 sources: A, B, C, D) with timelines/diagrams.
  Paper 2  – Comparative essay choice; exactly 2 questions per selected topic, 15 marks each.
             Overrides total_marks → 30, question_count → len(topics) * 2.
             Requires a model essay in the mark scheme.
  Paper 3  – HL only; extended essay choice (base class essay_choice rules apply).
"""
from __future__ import annotations
from ..base import BaseExamSkill


class HistorySkill(BaseExamSkill):
    subject_key = "History"
    output_language = "English"

    def get_instructions(self, level: str, paper: str, specs: dict) -> str:
        if "Paper 1" in paper:
            return (
                "- Provide 4 source-based questions.\n"
                "- Include brief placeholders/descriptions for 4 sources (Source A, B, C, D).\n"
                "- Use Mermaid or SVG to provide timelines or source hierarchy diagrams."
            )

        if "Paper 2" in paper:
            return (
                "- **STRICT TOPIC STRUCTURE**: For EACH of the focus areas (topics) provided, "
                "you MUST generate EXACTLY two questions.\n"
                "- **STRICT COMPARISON**: EVERY question MUST be comparative. Questions must "
                "require the student to compare and contrast at least two different leaders, "
                "states, or regions.\n"
                "- **MARKS**: Each question is worth exactly 15 marks.\n"
                "- **DEPTH**: Questions should focus on 20th-century world history themes "
                "(Authoritarian States, Cold War, etc.) as requested."
            )

        return "- Provide essay prompts following IB command terms."

    def get_prompt_overrides(self, request, specs: dict) -> dict:
        if "Paper 2" in request.paper:
            q_count = len(request.topic_or_type) * 2
            return {
                "specs_overrides": {
                    "total_marks": 30,
                    "question_count": q_count,
                    "structure_desc": (
                        "Answer two questions. "
                        "Each question must be selected from a different topic."
                    ),
                },
                "structure_rule": (
                    f"\n- **STRICT QUESTION COUNT**: You MUST provide EXACTLY {q_count} questions "
                    f"(2 questions per topic). The user will choose 2 questions, each from a "
                    "different topic."
                ),
                "model_essay_req": (
                    "\n- **MODEL ESSAY**: Inside the [SECTION_MARK_SCHEME], you MUST provide ONE "
                    "FULL, HIGH-LEVEL sample essay response (approx 800-1000 words in analysis) "
                    "for at least one of the generated prompts."
                ),
            }

        return super().get_prompt_overrides(request, specs)
