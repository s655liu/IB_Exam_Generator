/**
 * SampleEssayGenerator — generates a Band 6–7 model essay for a selected
 * question from the generated exam paper.
 *
 * The component parses essay-style questions out of the exam markdown and
 * shows them in a dropdown. The user can also enter a custom question.
 *
 * Props:
 *   subject, level, paper   {string}
 *   examText                {string}  Generated exam (source of questions)
 *   markScheme              {string}  For context
 *   prescribedTexts         {string[]}
 */
import React, { useState, useMemo } from 'react';
import axios from 'axios';
import { MarkdownRenderer } from './MarkdownRenderer';
import { Sparkles, Copy, Check, Loader2, AlertCircle, BookOpen, ChevronDown } from 'lucide-react';

// ---------------------------------------------------------------------------
// Question extraction
// ---------------------------------------------------------------------------

/**
 * Heuristically extract essay-style prompts from the generated exam markdown.
 * Returns an array of plain-text question strings.
 */
function extractEssayPrompts(examText) {
  if (!examText) return [];
  const prompts = [];

  // IB essay command terms
  const CMD = /^(Discuss|Evaluate|Analyse|Analyze|Explain|Compare|Contrast|Describe|Examine|Assess|Consider|Justify|Distinguish|To what extent|How far|In what ways|Why|How did|What were|What was|Outline|Identify)\b/i;

  const lines = examText.split('\n');
  for (const raw of lines) {
    // Strip markdown formatting
    const clean = raw
      .replace(/\*+/g, '')
      .replace(/^#+\s*/, '')
      .replace(/`+/g, '')
      .replace(/\[.*?\]\(.*?\)/g, '') // remove links
      .trim();

    if (clean.length < 25) continue; // Too short

    const hasMarkAlloc = /\[(\d+)\s*marks?\]/i.test(clean) || /\((\d+)\s*marks?\)/i.test(clean);
    const hasCommandTerm = CMD.test(clean);

    // Include if it's a command-term question OR a substantial line with mark allocation
    if (hasCommandTerm || (hasMarkAlloc && clean.length > 45)) {
      // Strip trailing mark allocations for a cleaner label
      const label = clean.replace(/\[\d+\s*marks?\]/gi, '').replace(/\(\d+\s*marks?\)/gi, '').trim();
      if (label.length > 20) prompts.push(label);
    }
  }

  // Deduplicate
  return [...new Set(prompts)].slice(0, 20);
}

// Truncate a string for the dropdown label
function truncate(str, n = 90) {
  return str.length > n ? str.slice(0, n - 1) + '…' : str;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function SampleEssayGenerator({ subject, level, paper, examText = '', markScheme = '', prescribedTexts = [] }) {
  const [selected, setSelected]       = useState('');
  const [customQ, setCustomQ]         = useState('');
  const [essay, setEssay]             = useState('');
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState('');
  const [copied, setCopied]           = useState(false);

  const questions = useMemo(() => extractEssayPrompts(examText), [examText]);

  // The question to actually send — either the selected dropdown item or the custom input
  const activeQuestion = selected === '__custom__' ? customQ : selected;

  // ── Generate ─────────────────────────────────────────────────────────────
  async function handleGenerate() {
    if (!activeQuestion.trim()) {
      setError('Please select a question or enter one manually.');
      return;
    }
    setError('');
    setLoading(true);
    setEssay('');
    try {
      const res = await axios.post('/api/generate-sample-essay', {
        subject, level, paper,
        question: activeQuestion.trim(),
        mark_scheme: markScheme,
        prescribed_texts: prescribedTexts,
      });
      setEssay(res.data.essay || '');
    } catch (err) {
      setError(err.response?.data?.detail || 'Generation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  function handleCopy() {
    navigator.clipboard.writeText(essay);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  // ── Styles ────────────────────────────────────────────────────────────────
  const inputStyle = {
    width: '100%', background: 'rgba(15,23,42,0.8)',
    border: '1px solid rgba(148,163,184,0.15)', padding: '0.75rem',
    color: '#f1f5f9', fontSize: '0.9rem', fontFamily: 'Inter, sans-serif',
    lineHeight: 1.6, boxSizing: 'border-box',
  };

  const labelStyle = {
    display: 'block', fontSize: '0.75rem', fontWeight: 600,
    color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em',
    marginBottom: '0.5rem',
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <section style={{
      background: 'rgba(15, 23, 42, 0.7)',
      border: '1px solid rgba(255,255,255,0.08)',
      padding: '2rem',
      marginTop: '0.5rem',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.75rem' }}>
        <div style={{
          width: 40, height: 40,
          background: 'linear-gradient(135deg,#4f46e5,#818cf8)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Sparkles size={20} color="white" />
        </div>
        <div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>
            Sample Essay Generator
          </h2>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: 0 }}>
            Choose a question from the exam above — the AI writes a Band 6–7 model response
          </p>
        </div>
      </div>

      {/* ── Question selector ─────────────────────────────────────────────── */}
      <div style={{ marginBottom: '1.25rem' }}>
        <label style={labelStyle}>Select Essay Question</label>

        {/* Dropdown */}
        <div style={{ position: 'relative' }}>
          <select
            value={selected}
            onChange={e => { setSelected(e.target.value); setCustomQ(''); setEssay(''); setError(''); }}
            style={{
              ...inputStyle,
              appearance: 'none', cursor: 'pointer',
              paddingRight: '2.5rem',
            }}
          >
            <option value="" disabled>
              {questions.length > 0
                ? `— ${questions.length} question${questions.length > 1 ? 's' : ''} found in exam — select one —`
                : '— No questions auto-detected — use custom entry below —'}
            </option>
            {questions.map((q, i) => (
              <option key={i} value={q}>{truncate(q)}</option>
            ))}
            <option value="__custom__">✏️  Enter / paste a custom question…</option>
          </select>
          <ChevronDown
            size={16}
            color="#64748b"
            style={{ position: 'absolute', right: '0.85rem', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}
          />
        </div>

        {/* Preview of the selected question (full text) */}
        {selected && selected !== '__custom__' && (
          <div style={{
            marginTop: '0.75rem', padding: '0.75rem 1rem',
            background: 'rgba(99,102,241,0.08)', borderLeft: '3px solid #6366f1',
            color: '#c7d2fe', fontSize: '0.875rem', lineHeight: 1.6,
          }}>
            {selected}
          </div>
        )}
      </div>

      {/* Custom question textarea */}
      {selected === '__custom__' && (
        <div style={{ marginBottom: '1.25rem' }}>
          <label style={labelStyle}>Custom Question / Prompt</label>
          <textarea
            value={customQ}
            onChange={e => setCustomQ(e.target.value)}
            placeholder="Paste or type the essay question here…"
            rows={4}
            style={{ ...inputStyle, resize: 'vertical' }}
          />
        </div>
      )}

      {/* Error */}
      {error && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.5rem',
          background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
          padding: '0.75rem 1rem', color: '#fca5a5', fontSize: '0.85rem',
          marginBottom: '1rem',
        }}>
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {/* Generate button */}
      <button
        onClick={handleGenerate}
        disabled={loading || !activeQuestion.trim()}
        style={{
          width: '100%', padding: '1rem',
          background: (loading || !activeQuestion.trim())
            ? 'rgba(79,70,229,0.25)'
            : 'linear-gradient(135deg,#4f46e5,#818cf8)',
          border: 'none', color: 'white', fontSize: '1rem',
          fontWeight: 700, cursor: (loading || !activeQuestion.trim()) ? 'not-allowed' : 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
          transition: 'all 0.3s',
          boxShadow: (loading || !activeQuestion.trim()) ? 'none' : '0 4px 20px rgba(79,70,229,0.4)',
        }}
      >
        {loading
          ? <><Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> Writing Band 6–7 essay — this may take 20–30 s…</>
          : <><Sparkles size={18} /> Generate Sample Essay</>
        }
      </button>

      {/* ── Essay output ──────────────────────────────────────────────────── */}
      {essay && (
        <div style={{ marginTop: '2rem', borderTop: '1px solid rgba(79,70,229,0.3)', paddingTop: '2rem' }}>
          {/* Result header row */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{ width: 8, height: 8, background: '#818cf8', borderRadius: '50%' }} />
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#a5b4fc', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                Model Essay · Band 6–7
              </span>
            </div>
            <button
              onClick={handleCopy}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.35rem',
                background: copied ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.06)',
                border: `1px solid ${copied ? 'rgba(16,185,129,0.4)' : 'rgba(255,255,255,0.1)'}`,
                color: copied ? '#6ee7b7' : '#94a3b8',
                padding: '0.4rem 0.9rem', fontSize: '0.78rem', fontWeight: 600,
                cursor: 'pointer', transition: 'all 0.2s',
              }}
            >
              {copied ? <><Check size={13} /> Copied!</> : <><Copy size={13} /> Copy Essay</>}
            </button>
          </div>

          {/* The essay itself */}
          <div className="markdown-body" style={{ color: '#f1f5f9', fontFamily: 'Georgia, serif', lineHeight: 1.85 }}>
            <MarkdownRenderer content={essay} />
          </div>
        </div>
      )}
    </section>
  );
}
