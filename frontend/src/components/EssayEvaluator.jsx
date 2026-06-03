/**
 * EssayEvaluator — lets students upload / paste an essay and get
 * AI-powered IB criterion-by-criterion feedback.
 *
 * Props:
 *   subject       {string}  e.g. "History"
 *   level         {string}  "HL" | "SL"
 *   paper         {string}  e.g. "Paper 2"
 *   examText      {string}  The generated exam (so student can copy the question)
 *   markScheme    {string}  The generated mark scheme (sent to evaluator for context)
 *   prescribedTexts {string[]}  For English Lit A
 */
import React, { useState, useRef } from 'react';
import axios from 'axios';
import { MarkdownRenderer } from './MarkdownRenderer';
import { FileText, Upload, Send, Loader2, AlertCircle, X, BookOpen } from 'lucide-react';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function wordCount(text) {
  return text.trim() ? text.trim().split(/\s+/).length : 0;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function EssayEvaluator({ subject, level, paper, examText = '', markScheme = '', prescribedTexts = [] }) {
  const [question, setQuestion]       = useState('');
  const [essayText, setEssayText]     = useState('');
  const [fileName, setFileName]       = useState('');
  const [evaluation, setEvaluation]   = useState('');
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState('');
  const fileRef = useRef(null);

  // ── File upload ──────────────────────────────────────────────────────────
  function handleFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (ev) => setEssayText(ev.target.result || '');
    reader.readAsText(file, 'utf-8');
  }

  function clearFile() {
    setFileName('');
    setEssayText('');
    if (fileRef.current) fileRef.current.value = '';
  }

  // ── Submit evaluation ────────────────────────────────────────────────────
  async function handleEvaluate() {
    if (!question.trim()) { setError('Please enter the question you answered.'); return; }
    if (!essayText.trim()) { setError('Please paste or upload your essay.'); return; }
    setError('');
    setLoading(true);
    setEvaluation('');
    try {
      const res = await axios.post('/api/evaluate-essay', {
        subject,
        level,
        paper,
        question: question.trim(),
        student_essay: essayText.trim(),
        mark_scheme: markScheme,
        prescribed_texts: prescribedTexts,
      });
      setEvaluation(res.data.evaluation || '');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to evaluate essay. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  // ── UI ───────────────────────────────────────────────────────────────────
  const wc = wordCount(essayText);
  const wcColor = wc < 200 ? '#f59e0b' : wc > 1000 ? '#10b981' : '#38bdf8';

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
          width: 40, height: 40, background: 'linear-gradient(135deg,#0ea5e9,#6366f1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <BookOpen size={20} color="white" />
        </div>
        <div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>
            Essay Evaluator
          </h2>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: 0 }}>
            Submit your essay response for IB criterion-by-criterion feedback
          </p>
        </div>
      </div>

      {/* Question input */}
      <div style={{ marginBottom: '1.25rem' }}>
        <label style={{
          display: 'block', fontSize: '0.75rem', fontWeight: 600,
          color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em',
          marginBottom: '0.5rem',
        }}>
          Question / Prompt You Answered
        </label>
        <textarea
          value={question}
          onChange={e => setQuestion(e.target.value)}
          placeholder="Paste or type the specific question / essay prompt from the generated exam above…"
          rows={3}
          style={{
            width: '100%', background: 'rgba(15,23,42,0.8)',
            border: '1px solid rgba(148,163,184,0.15)', padding: '0.75rem',
            color: '#f1f5f9', fontSize: '0.9rem', resize: 'vertical',
            fontFamily: 'Inter, sans-serif', lineHeight: 1.6,
            boxSizing: 'border-box',
          }}
        />
      </div>

      {/* Essay textarea + upload */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <label style={{
            fontSize: '0.75rem', fontWeight: 600,
            color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em',
          }}>
            Your Essay
          </label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '0.75rem', color: wcColor, fontWeight: 600 }}>
              {wc} words
            </span>
            {/* File upload button */}
            <button
              onClick={() => fileRef.current?.click()}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.35rem',
                background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
                color: '#94a3b8', padding: '0.3rem 0.7rem', fontSize: '0.75rem',
                cursor: 'pointer', fontWeight: 500,
              }}
            >
              <Upload size={12} /> Upload .txt / .md
            </button>
            <input
              ref={fileRef}
              type="file"
              accept=".txt,.md,.text"
              style={{ display: 'none' }}
              onChange={handleFile}
            />
            {fileName && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', color: '#38bdf8' }}>
                <FileText size={12} />
                {fileName}
                <button onClick={clearFile} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: 0, display: 'flex' }}>
                  <X size={12} />
                </button>
              </span>
            )}
          </div>
        </div>

        <textarea
          value={essayText}
          onChange={e => { setEssayText(e.target.value); setFileName(''); }}
          placeholder="Paste your essay here, or upload a .txt file above…"
          rows={14}
          style={{
            width: '100%', background: 'rgba(15,23,42,0.8)',
            border: '1px solid rgba(148,163,184,0.15)', padding: '0.75rem',
            color: '#f1f5f9', fontSize: '0.9rem', resize: 'vertical',
            fontFamily: 'Georgia, serif', lineHeight: 1.8,
            boxSizing: 'border-box',
          }}
        />
      </div>

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

      {/* Submit button */}
      <button
        onClick={handleEvaluate}
        disabled={loading}
        style={{
          width: '100%', padding: '1rem',
          background: loading ? 'rgba(99,102,241,0.3)' : 'linear-gradient(135deg,#6366f1,#0ea5e9)',
          border: 'none', color: 'white', fontSize: '1rem',
          fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
          transition: 'all 0.3s',
          boxShadow: loading ? 'none' : '0 4px 20px rgba(99,102,241,0.35)',
        }}
      >
        {loading
          ? <><Loader2 size={18} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} /> Evaluating — this may take 20–30 s…</>
          : <><Send size={18} /> Evaluate My Essay</>
        }
      </button>

      {/* ── Results ─────────────────────────────────────────────────────────── */}
      {evaluation && (
        <div style={{
          marginTop: '2rem',
          borderTop: '1px solid rgba(99,102,241,0.3)',
          paddingTop: '2rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
            <div style={{ width: 8, height: 8, background: '#6366f1', borderRadius: '50%' }} />
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#a5b4fc', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              IB Examiner Feedback
            </span>
          </div>
          <div className="markdown-body" style={{ color: '#f1f5f9' }}>
            <MarkdownRenderer content={evaluation} />
          </div>
        </div>
      )}
    </section>
  );
}
