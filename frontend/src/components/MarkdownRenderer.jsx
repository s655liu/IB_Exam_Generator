/**
 * MarkdownRenderer — centralised markdown rendering for all LLM output.
 *
 * Features:
 *  - Preprocessing: converts LATEX<<...>> / LATEXBLOCK<<...>> delimiters
 *    (written by the LLM) into KaTeX-compatible $...$ / $$...$$ notation.
 *  - Plugins: remark-math, remark-gfm, rehype-katex.
 *  - Accepts custom `components` (e.g., audio/mermaid/svg code block renderers).
 *
 * LLM contract:
 *  - Inline math   → LATEX<<formula>>        e.g. LATEX<<x^{2} + 1>>
 *  - Display math  → LATEXBLOCK<<formula>>   e.g. LATEXBLOCK<<\frac{a}{b}>>
 */
import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

// ---------------------------------------------------------------------------
// Preprocessing
// ---------------------------------------------------------------------------

/**
 * Convert LLM-specific math delimiters → standard KaTeX delimiters.
 *
 * Handles:
 *  LATEXBLOCK<<...>>  → $$ ... $$    (display math, must come first)
 *  LATEX<<...>>       → $ ... $      (inline math)
 *
 * The `<<` / `>>` delimiters were chosen because they never appear in LaTeX
 * formula syntax, making them unambiguous even when the formula contains
 * `[`, `]`, `(`, `)`, `{`, `}`, etc.
 */
export function preprocessMarkdown(text) {
  if (!text) return '';

  // ── Primary contract: LATEX<<>> / LATEXBLOCK<<>> ────────────────────
  // Display math
  text = text.replace(
    /LATEXBLOCK<<([\s\S]*?)>>/gi,
    (_, f) => `\n$$\n${f.trim()}\n$$\n`
  );
  // Inline math
  text = text.replace(
    /LATEX<<([\s\S]*?)>>/gi,
    (_, f) => `$${f.trim()}$`
  );

  // ── Fallback 1: Standard LaTeX delimiters \[ \] and \( \) ───────────
  // LLM sometimes uses these even when instructed otherwise
  text = text.replace(
    /\\\[([\s\S]*?)\\\]/g,
    (_, f) => `\n$$\n${f.trim()}\n$$\n`
  );
  text = text.replace(
    /\\\(([\s\S]*?)\\\)/g,
    (_, f) => `$${f.trim()}$`
  );

  // ── Fallback 2: ( formula ) — space-padded parens containing LaTeX ──
  // Matches patterns like:  ( W = q \Delta V )  or  ( \Delta U = Q - W )
  // Rules: must have a space after ( and before ), content must contain \,
  //        no nested parens or newlines allowed inside (to avoid false positives)
  text = text.replace(
    /\(\s+((?:[^()\n]*\\[^()\n]*)+?)\s+\)/g,
    (_, f) => `$${f.trim()}$`
  );

  return text;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * @param {string}   content    - Raw markdown string from the LLM.
 * @param {object}   components - Custom ReactMarkdown component overrides
 *                                (e.g., audio/mermaid/svg code block renderers).
 */
export function MarkdownRenderer({ content = '', components = {} }) {
  const processed = useMemo(() => preprocessMarkdown(content), [content]);

  return (
    <ReactMarkdown
      remarkPlugins={[remarkMath, remarkGfm]}
      rehypePlugins={[rehypeKatex]}
      components={components}
    >
      {processed}
    </ReactMarkdown>
  );
}
