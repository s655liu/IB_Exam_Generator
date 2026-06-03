"""
Shared base skill for IB Language B subjects.  [Group 2: Language Acquisition]

Paper-specific behaviour:
  Paper 1 – Writing tasks: three prompts in the target language; student chooses one.
  Paper 2 – Receptive skills ONLY (listening + reading comprehension in target language).
             Section A: THREE audio transcripts (wrapped in ```audio``` blocks), 25 marks.
             Section B: THREE reading texts, 40 marks.

Subclasses set `target_language` (e.g. "French") and may override `_get_length_instruction`
for language-specific length requirements (e.g. Mandarin B HL uses character count).
"""
from __future__ import annotations
from ..base import BaseExamSkill


class LanguageBSkill(BaseExamSkill):
    """Base for French B, Spanish B, Mandarin B."""

    subject_key: str = ""
    target_language: str = "English"

    @property
    def output_language(self) -> str:  # type: ignore[override]
        return self.target_language

    def get_instructions(self, level: str, paper: str, specs: dict) -> str:
        lang = self.target_language
        lang_instr = (
            f"- **STRICT LANGUAGE REQUIREMENT**: This is a Language B exam. EVERYTHING "
            f"(Instructions, Section Headers, Questions, and Transcripts/Texts) MUST be "
            f"written in {lang}. Do NOT use English for any part of the exam content."
        )

        if "Paper 1" in paper:
            return (
                f"{lang_instr}\n"
                f"- Provide three specific writing prompts in {lang}.\n"
                f"- Students must choose ONE and produce a piece of writing in {lang}.\n"
                "- Ensure each prompt specifies a clear text type "
                "(e.g., blog, email, report)."
            )

        if "Paper 2" in paper:
            len_instr = self._get_length_instruction(level)
            return (
                f"{lang_instr}\n"
                "- **RECEPTIVE FOCUS**: This paper tests Listening and Reading Comprehension "
                "only. NO WRITING TASKS.\n"
                f"- **SECTION A (LISTENING - 60 min)**: Provide THREE distinct listening "
                f"transcripts in {lang}. **STRICT**: Each transcript MUST be a minimum of "
                f"{len_instr}. Do NOT summarize.\n"
                "  - **AUDIO PLAYER**: Wrap the ENTIRE transcript within triple backtick code "
                "blocks with the language tag 'audio' "
                "(e.g., ```audio [transcript text] ```). "
                "**NEVER** use brackets like [PLAYABLE_AUDIO].\n"
                "  - **COMPLEXITY**: Passages must be academically demanding, including "
                "nuanced arguments and varying opinions.\n"
                f"  - **QUESTIONS (25 marks)**: Include detailed questions in {lang} on "
                "tone, purpose, and inference.\n"
                f"- **SECTION B (READING - 60 min)**: Provide THREE authentic-style reading "
                f"texts in {lang}.\n"
                f"  - **LENGTH**: Each HL text MUST be a minimum of {len_instr}. "
                "**CRITICAL**: Use high-level academic vocabulary and deep literary analysis.\n"
                f"  - **QUESTIONS (40 marks)**: Focus on higher-order thinking in {lang}.\n"
                "- **STRICT**: Section A = 25 marks, Section B = 40 marks. "
                f"Total = {specs.get('total_marks', 65)} marks.\n"
                f"- **NO DICTIONARY**: Instruction (in {lang}): 'Do not use a dictionary.'\n"
                f"- **PLAYBACK**: Instruction (in {lang}): "
                "'You will hear each passage twice. You may take notes.'"
            )

        return f"- Provide contextual situational prompts in {lang}."

    def _get_length_instruction(self, level: str) -> str:
        """Override in subclasses for non-standard length requirements."""
        return "450-600 words"

    def get_prompt_overrides(self, request, specs: dict) -> dict:
        if "Paper 2" in request.paper:
            duration = specs.get("duration", 120)
            return {
                "structure_rule": (
                    f"\n- **STRICT RECEPTIVE FORMAT**: This is a {duration}-minute comprehension "
                    "paper. Do NOT include any writing tasks.\n"
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
        return super().get_prompt_overrides(request, specs)
