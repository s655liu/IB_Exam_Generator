"""
Base class for all IB Exam subject skills.

Each skill encapsulates:
  - Subject-specific LLM prompt instructions  (get_instructions)
  - Paper-structure rules                      (get_prompt_overrides → structure_rule)
  - Model essay / answer requirements          (get_prompt_overrides → model_essay_req)
  - Any overrides to exam specs                (get_prompt_overrides → specs_overrides)

Usage (in generator.py):
    skill = get_skill(request.subject)
    overrides = skill.get_prompt_overrides(request, specs)
    specs.update(overrides.get("specs_overrides", {}))
    instructions = skill.get_instructions(request.level, request.paper, specs)
    structure_rule = overrides.get("structure_rule", ...)
    model_essay_req = overrides.get("model_essay_req", "")
    output_lang = skill.output_language
"""
from __future__ import annotations


class BaseExamSkill:
    """
    Default / fallback skill.

    Subclasses should override:
      - subject_key       → key used in exam_specs.json lookups
      - output_language   → language the LLM should write the exam in
      - get_instructions  → returns subject-specific prompt additions
      - get_prompt_overrides → returns structure_rule / model_essay_req / specs_overrides
    """

    subject_key: str = ""
    output_language: str = "English"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_instructions(self, level: str, paper: str, specs: dict) -> str:
        """
        Return a multi-line string of subject-specific bullet-point instructions
        to be injected into the LLM prompt.  Return "" if no special instructions.
        """
        return ""

    def get_prompt_overrides(self, request, specs: dict) -> dict:
        """
        Inspect the request and current specs dict and return a dict with any
        subset of the following keys:

          "structure_rule"  (str)  – appended to EXAM SPECIFICATIONS block
          "model_essay_req" (str)  – appended after subject instructions
          "specs_overrides" (dict) – values merged into specs before the prompt
                                     template is rendered (e.g. History P2 marks)

        The base implementation covers the three standard structure types that
        are driven by specs["structure_type"] from exam_specs.json:
          - essay_choice / essay_based / short_and_extended_response
          - receptive
          - everything else (standard question count rule)
        """
        q_count = specs.get("question_count", "5-10")
        structure_type = specs.get("structure_type", "")

        if structure_type in ("essay_choice", "essay_based", "short_and_extended_response"):
            return {
                "structure_rule": (
                    f"\n- **STRICT QUESTION COUNT**: You MUST provide EXACTLY {q_count} essay "
                    f"prompts/options. The user will choose 1 of these {q_count} prompts."
                ),
                "model_essay_req": (
                    "\n- **MODEL ESSAY & GRADING**: Inside the [SECTION_MARK_SCHEME], you MUST "
                    "provide ONE FULL, HIGH-LEVEL sample essay response for at least one of the "
                    "generated prompts. IMMEDIATELY FOLLOWING the essay, provide a detailed "
                    "**EXAMINER COMMENTARY AND GRADE**. Break down the marks for each IB Criterion "
                    "(e.g., Criterion A, B, C, D) and provide a 2-3 sentence justification for "
                    "the marks in each category."
                ),
            }

        if structure_type == "receptive":
            return {
                "structure_rule": (
                    f"\n- **STRICT RECEPTIVE FORMAT**: This is a {specs.get('duration', 120)}-minute "
                    "comprehension paper. Do NOT include any writing tasks.\n"
                    "- **TRANSCRIPTS**: You MUST provide the full text transcripts for the "
                    "Section A Listening passages. Wrap EACH transcript in triple backtick code "
                    "blocks with the language tag 'audio'.\n"
                    "- **AUTHENTIC TEXTS**: You MUST provide the full reading texts for Section B.\n"
                    "- **NO DICTIONARY**: Instruction: 'Do not use a dictionary.'\n"
                    "- **PLAYBACK**: Instruction: 'You will hear each passage twice.'"
                ),
                "model_essay_req": (
                    "\n- **MODEL ANSWERS**: Inside the [SECTION_MARK_SCHEME], provide a complete "
                    "answer key for every question. No essay is required for receptive papers."
                ),
            }

        # Default: standard question count rule
        return {
            "structure_rule": (
                f"\n- **STRICT QUESTION COUNT**: The exam MUST contain EXACTLY {q_count} questions/tasks."
            ),
            "model_essay_req": "",
        }
