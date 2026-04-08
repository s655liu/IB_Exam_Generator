import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { BookOpen, Award, FileText, CheckCircle, Send, Loader2, Sparkles, Languages, Download } from 'lucide-react';
import 'katex/dist/katex.min.css';
import mermaid from 'mermaid';
import subjectData from '@data/exam_subject_structure.json';
import markSchemes from '@data/mark_schemes.json';

mermaid.initialize({
  startOnLoad: true,
  theme: 'base',
  themeVariables: {
    primaryColor: '#0ea5e9',
    primaryTextColor: '#fff',
    primaryBorderColor: '#3b82f6',
    lineColor: '#94a3b8',
    secondaryColor: '#1e293b',
    tertiaryColor: '#0f172a',
  },
  securityLevel: 'loose',
});

const Mermaid = ({ chart }) => {
  const ref = React.useRef(null);

  useEffect(() => {
    if (ref.current && chart) {
      ref.current.removeAttribute('data-processed');
      mermaid.render(`mermaid-${Math.random().toString(36).substr(2, 9)}`, chart).then(({ svg }) => {
        if (ref.current) ref.current.innerHTML = svg;
      });
    }
  }, [chart]);

  return <div key={chart} ref={ref} className="mermaid flex justify-center my-6 bg-slate-900/50 p-6 rounded-xl border border-white/10" />;
};

const SVGRenderer = ({ code }) => {
  const processedCode = React.useMemo(() => {
    if (!code.includes('<svg')) return code;
    // Ensure responsive and safe attributes
    return code
      .replace(/<svg/, '<svg style="max-width: 100%; height: auto;" preserveAspectRatio="xMidYMid meet"')
      .replace(/width=".*?"/, '')
      .replace(/height=".*?"/, '');
  }, [code]);

  return (
    <div 
      className="svg-diagram flex justify-center my-6 bg-slate-900/30 p-8 rounded-2xl border border-white/10 shadow-2xl backdrop-blur-sm overflow-hidden"
      dangerouslySetInnerHTML={{ __html: processedCode }}
    />
  );
};

const API_BASE_URL = '/api';


function App() {
  // State for selections
  const [selectedSubject, setSelectedSubject] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('');
  const [selectedPaper, setSelectedPaper] = useState('');
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [includeAnswerKey, setIncludeAnswerKey] = useState(true);

  // UI State
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('paper');
  const [dots, setDots] = useState('');

  // Derived official data (Boundaries & Rubrics)
  const officialData = useMemo(() => {
    if (!selectedSubject) return null;
    
    // 1. Determine Subject Key for Boundaries (Physics, Mathematics_AA, etc.)
    let subjectKey = selectedSubject.replace(' ', '_');
    if (selectedSubject === 'Math AA') subjectKey = 'Mathematics_AA';
    if (selectedSubject === 'Business Management') subjectKey = 'Business';
    if (selectedSubject === 'English A') subjectKey = 'English_A';

    const boundaries = markSchemes.grade_boundaries?.[subjectKey]?.[selectedLevel] || null;
    
    // 2. Determine Rubric Key (English_A, History, Sciences, etc.)
    let paperKey = selectedPaper?.toLowerCase().replace(' ', '_');
    let rubricKey = subjectKey;
    
    // Sciences mapping (Physics/Chemistry/Biology use common Science rubrics)
    if (['Physics', 'Chemistry', 'Biology'].includes(selectedSubject)) {
      rubricKey = 'Sciences_post2025';
    }
    if (selectedSubject === 'Math AA') rubricKey = 'Mathematics_AA';

    let rubric = markSchemes.rubrics?.[rubricKey]?.[paperKey] || null;

    return { boundaries, rubric, notes: markSchemes.grade_boundaries?.notes };
  }, [selectedSubject, selectedLevel, selectedPaper]);

  // Animate dots
  useEffect(() => {
    let interval;
    if (isGenerating) {
      setDots('.');
      interval = setInterval(() => {
        setDots(prev => prev.length >= 3 ? '.' : prev + '.');
      }, 500);
    } else {
      setDots('');
    }
    return () => clearInterval(interval);
  }, [isGenerating]);

  // Derived data
  const subjects = Object.keys(subjectData).filter(key => key !== 'metadata');
  
  const currentSubject = useMemo(() => 
    selectedSubject ? subjectData[selectedSubject] : null
  , [selectedSubject]);

  const isMathOrScience = useMemo(() => {
    const scienceMathKeywords = ['Math', 'Biology', 'Chemistry', 'Physics'];
    return selectedSubject && scienceMathKeywords.some(k => selectedSubject.includes(k));
  }, [selectedSubject]);

  const papers = useMemo(() => {
    if (!currentSubject || !selectedLevel) return [];
    return currentSubject.papers_by_level[selectedLevel] || [];
  }, [currentSubject, selectedLevel]);

  const availableOptions = useMemo(() => {
    if (!currentSubject || !selectedPaper) return [];

    const isEnglishA = selectedSubject === 'English A';
    const isHistory = selectedSubject === 'History';
    const isLanguageB = selectedSubject.endsWith(' B');

    if (isEnglishA) return currentSubject.types_by_paper[selectedPaper] || [];

    if (isHistory) {
      if (selectedPaper === 'Paper 1') return currentSubject.topics.core_topics['Paper 1 Prescribed Subjects'] || [];
      if (selectedPaper === 'Paper 2') return currentSubject.topics.core_topics['Paper 2 World History Topics'] || [];
      if (selectedPaper === 'Paper 3' && selectedLevel === 'HL') return currentSubject.topics.hl_topics['Paper 3 HL Options'] || [];
      return [];
    }

    if (isLanguageB) return currentSubject.topics.core_topics || [];

    // Science Paper 1B specialized skills selection
    if (isMathOrScience && selectedPaper === 'Paper 1B' && currentSubject.post_2025_notes?.key_skills_assessed) {
      return currentSubject.post_2025_notes.key_skills_assessed;
    }

    let options = [...(currentSubject.topics.core_topics || [])];
    if (selectedLevel === 'HL' && currentSubject.topics.hl_topics) {
      options = [...options, ...currentSubject.topics.hl_topics];
    }
    if (currentSubject.topics.options && selectedPaper === 'Paper 3') {
      options = [...options, ...currentSubject.topics.options];
    }
    return options;
  }, [selectedSubject, selectedLevel, selectedPaper, currentSubject]);

  // Effects to clear dependent fields
  useEffect(() => { setSelectedLevel(''); setSelectedPaper(''); setSelectedTopics([]); }, [selectedSubject]);
  useEffect(() => { setSelectedPaper(''); setSelectedTopics([]); }, [selectedLevel]);
  useEffect(() => { setSelectedTopics([]); }, [selectedPaper]);

  const toggleTopic = (topic) => {
    setSelectedTopics(prev => 
      prev.includes(topic) ? prev.filter(t => t !== topic) : [...prev, topic]
    );
  };

  const selectAllTopics = () => {
    if (selectedTopics.length === availableOptions.length) {
      setSelectedTopics([]);
    } else {
      setSelectedTopics([...availableOptions]);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const canGenerate = selectedSubject && selectedLevel && selectedPaper && selectedTopics.length > 0;

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    setResult(null);
    setActiveTab('paper');

    try {
      const response = await axios.post(`${API_BASE_URL}/generate-exam`, {
        subject: selectedSubject,
        level: selectedLevel,
        paper: selectedPaper,
        topic_or_type: selectedTopics,
        include_answer_key: includeAnswerKey
      });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'An unexpected error occurred during generation.');
    } finally {
      setIsGenerating(false);
    }
  };

  const MarkdownComponents = {
    code({ node, inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || '');
      if (!inline && match && match[1] === 'mermaid') {
        return <Mermaid chart={String(children).replace(/\n$/, '')} />;
      }
      if (!inline && match && match[1] === 'svg') {
        return <SVGRenderer code={String(children).replace(/\n$/, '')} />;
      }
      return <code className={className} {...props}>{children}</code>;
    }
  };

  return (
    <div className="container">
      <header className="no-print">
        <div className="logo">
          <Award className="w-8 h-8 text-sky-400" />
          <span>IB Exam Generator <span className="text-sm font-light opacity-50">AI Powered</span></span>
        </div>
      </header>

      <main>
        <section className="generator-card glass no-print">
          <div className="grid-cols-4">
            <div className="form-group">
              <label>Subject</label>
              <select value={selectedSubject} onChange={(e) => setSelectedSubject(e.target.value)}>
                <option value="">Select Subject</option>
                {subjects.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            <div className="form-group">
              <label>Level</label>
              <select value={selectedLevel} onChange={(e) => setSelectedLevel(e.target.value)} disabled={!selectedSubject}>
                <option value="">Select Level</option>
                {currentSubject?.levels.map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>

            <div className="form-group">
              <label>Paper</label>
              <select value={selectedPaper} onChange={(e) => setSelectedPaper(e.target.value)} disabled={!selectedLevel}>
                <option value="">Select Paper</option>
                {papers.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            
            <div className="form-group">
              <label>Answer Key</label>
              <div className="toggle-group" style={{marginTop: '0.25rem'}}>
                <label className="switch">
                  <input type="checkbox" checked={includeAnswerKey} onChange={(e) => setIncludeAnswerKey(e.target.checked)} />
                  <span className="slider"></span>
                </label>
              </div>
            </div>
          </div>

          <div className="topics-container">
            <div className="topics-header">
              <label>
                {selectedSubject === 'English A' ? 'Task Type (Multi-Select)' : 
                 (isMathOrScience && selectedPaper === 'Paper 1B') ? 'Experimental Skills (Multi-Select)' : 
                 'Focus Topics (Multi-Select)'}
              </label>
              {isMathOrScience && availableOptions.length > 0 && (
                <button className="select-all-btn" onClick={selectAllTopics}>
                  {selectedTopics.length === availableOptions.length ? 'Deselect All' : 'Select All Topics'}
                </button>
              )}
            </div>
            
            {!selectedPaper ? (
              <div className="flex items-center gap-2 p-2 text-slate-500 italic text-sm">
                <div className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-pulse"></div>
                Please select Subject {'->'} Level {'->'} Paper {'->'} Generate
              </div>
            ) : (
              <div className="topics-grid">
                {availableOptions.map(t => (
                  <label key={t} className={`topic-checkbox ${selectedTopics.includes(t) ? 'selected' : ''}`}>
                    <input 
                      type="checkbox" 
                      checked={selectedTopics.includes(t)} 
                      onChange={() => toggleTopic(t)} 
                    />
                    {t}
                  </label>
                ))}
              </div>
            )}
          </div>

          <button 
            className="btn-generate"
            disabled={!canGenerate || isGenerating}
            onClick={handleGenerate}
          >
            {isGenerating ? (
              <span className="flex items-center justify-center gap-2">
                <span style={{ display: 'inline-flex', transform: 'translate(-6px, 2px)' }}>
                  <Loader2 className="w-5 h-5 animate-spin" />
                </span>
                Generating Official Paper{dots}
              </span>
            ) : (
              <span className="flex items-center justify-center gap-2">
                <Sparkles className="w-5 h-5" />
                Generate Examination
              </span>
            )}
          </button>

          {error && (
            <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-sm">
              {error}
            </div>
          )}
        </section>

        {result && (
          <div className="exam-layout relative">
            {/* Tab Bar + Export PDF on same row */}
            <div className="no-print" style={{display:'flex', alignItems:'center', gap:'1rem', marginBottom:'2rem'}}>
              <button 
                onClick={() => setActiveTab('paper')}
                style={{
                  display:'flex', alignItems:'center', gap:'0.5rem',
                  padding:'0.65rem 1.4rem', borderRadius:'12px',
                  fontSize:'0.875rem', fontWeight:600, cursor:'pointer',
                  transition:'all 0.2s',
                  background: activeTab === 'paper' ? 'linear-gradient(135deg,#1e40af55,#0ea5e966)' : 'rgba(255,255,255,0.05)',
                  color: activeTab === 'paper' ? '#93c5fd' : '#9ca3af',
                  border: activeTab === 'paper' ? '1px solid #3b82f660' : '1px solid rgba(255,255,255,0.08)',
                  boxShadow: activeTab === 'paper' ? '0 0 20px #3b82f620' : 'none',
                }}
              >
                <FileText style={{width:'16px',height:'16px'}} />
                Question Paper
              </button>
              
              {result.answer_key && (
                <button 
                  onClick={() => setActiveTab('key')}
                  style={{
                    display:'flex', alignItems:'center', gap:'0.5rem',
                    padding:'0.65rem 1.4rem', borderRadius:'12px',
                    fontSize:'0.875rem', fontWeight:600, cursor:'pointer',
                    transition:'all 0.2s',
                    background: activeTab === 'key' ? 'linear-gradient(135deg,#06442a88,#10b98166)' : 'rgba(255,255,255,0.05)',
                    color: activeTab === 'key' ? '#6ee7b7' : '#9ca3af',
                    border: activeTab === 'key' ? '1px solid #10b98160' : '1px solid rgba(255,255,255,0.08)',
                    boxShadow: activeTab === 'key' ? '0 0 20px #10b98120' : 'none',
                  }}
                >
                  <CheckCircle style={{width:'16px',height:'16px'}} />
                  Mark Scheme & Boundaries
                </button>
              )}

              {/* Export PDF — same row, pushed to the right */}
              <button 
                onClick={handlePrint}
                style={{
                  marginLeft:'auto',
                  display:'flex', alignItems:'center', gap:'0.5rem',
                  padding:'0.65rem 1.4rem', borderRadius:'12px',
                  fontSize:'0.875rem', fontWeight:600, cursor:'pointer',
                  transition:'all 0.2s',
                  background:'rgba(255,255,255,0.06)',
                  color:'#cbd5e1',
                  border:'1px solid rgba(255,255,255,0.12)',
                }}
              >
                <Download style={{width:'16px',height:'16px'}} />
                Download PDF
              </button>
            </div>


            {/* UI View */}
            <div className="no-print mt-8">
               {/* Question Paper Container */}
               {activeTab === 'paper' && (
                 <section className="exam-page glass animate-fade-in">
                    <div className="markdown-body">
                      <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]} components={MarkdownComponents}>
                        {result.exam_text}
                      </ReactMarkdown>
                    </div>
                 </section>
               )}

               {/* Mark Scheme Container */}
               {activeTab === 'key' && (
                 <section className="exam-page glass mark-scheme-page animate-fade-in relative">
                   <div className="markdown-body">
                     {/* Official Rubric Section */}
                     {officialData?.rubric && (
                        <div className="rubric-box mb-12">
                          <h2 className="flex items-center gap-3 text-emerald-400 mb-6 font-bold text-2xl border-b border-emerald-500/20 pb-4">
                            <BookOpen className="w-7 h-7" /> {officialData.rubric.title} (Official Rubric)
                          </h2>
                          {officialData.rubric.marking_bands ? (
                             <table className="grade-table">
                               <thead><tr><th>Marks</th><th>Descriptor</th></tr></thead>
                               <tbody>{Object.entries(officialData.rubric.marking_bands).map(([marks, desc]) => <tr key={marks}><td>{marks}</td><td>{desc}</td></tr>)}</tbody>
                             </table>
                          ) : officialData.rubric.criteria ? (
                            <div className="grid gap-6">
                               {officialData.rubric.criteria.map((c, i) => (
                                 <div key={i} className="p-4 bg-white/5 rounded-xl border border-white/10">
                                   <div className="font-bold text-emerald-400 mb-2">{c.criterion}</div>
                                   <p className="text-sm text-slate-400 mb-3">{c.what_is_assessed}</p>
                                   <div className="text-xs space-y-1 pl-4 border-l-2 border-emerald-500/30">
                                      {Object.entries(c.descriptors).map(([m, d]) => <div key={m}><strong>{m}:</strong> {d}</div>)}
                                   </div>
                                 </div>
                               ))}
                            </div>
                          ) : (
                             <div className="p-4 bg-white/5 rounded-xl">
                               <p className="text-sm">{officialData.rubric.marking_approach || officialData.rubric.marking_notes}</p>
                             </div>
                          )}
                        </div>
                     )}

                     {result.answer_key ? (
                       <>
                         <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]} components={MarkdownComponents}>
                           {result.answer_key}
                         </ReactMarkdown>
                         
                         {/* Priority: Local JSON Boundaries then AI Boundaries */}
                         {(officialData?.boundaries || result.grade_boundaries) && (
                            <div className="mt-12 p-8 bg-emerald-500/5 border border-emerald-500/20 rounded-2xl grade-boundaries-box">
                              <h3 className="flex items-center gap-3 text-emerald-400 mb-2 font-bold text-xl">
                                <Award className="w-6 h-6" /> Official Grade Boundaries
                              </h3>
                              <p className="text-xs text-slate-500 mb-6">{markSchemes.grade_boundaries.explanation}</p>
                              
                              {officialData?.boundaries ? (
                                <table className="grade-table">
                                  <thead><tr><th>Grade</th><th>Percentage Range</th><th>Description</th></tr></thead>
                                  <tbody>
                                    {Object.entries(officialData.boundaries)
                                      .filter(([k]) => k.startsWith('grade_'))
                                      .map(([k, v]) => (
                                      <tr key={k}>
                                        <td className="font-bold text-lg">{k.replace('grade_', '')}</td>
                                        <td>{v.min}% - {v.max}%</td>
                                        <td className="text-slate-400">{v.description}</td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              ) : (
                                <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]} components={MarkdownComponents}>
                                  {result.grade_boundaries}
                                </ReactMarkdown>
                              )}
                            </div>
                         )}
                       </>
                     ) : (
                       <div className="p-12 text-center text-slate-500 italic">Mark Scheme not available.</div>
                     )}
                   </div>
                 </section>
               )}
            </div>

            {/* Print Only View (PDF) */}
            <div className="print-only">
               <section className="exam-page">
                 <div className="markdown-body">
                   <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]} components={MarkdownComponents}>
                     {result.exam_text}
                   </ReactMarkdown>
                 </div>
               </section>
               {(result.answer_key || result.grade_boundaries || officialData) && (
                 <section className="exam-page mark-scheme-page">
                   <div className="markdown-body">
                     {/* Official Rubric in Print */}
                     {officialData?.rubric && (
                        <div className="rubric-print-section mb-8">
                          <h2 className="text-xl font-bold border-b-2 border-black pb-2 mb-4">
                            {officialData.rubric.title} (Official Rubric)
                          </h2>
                          {officialData.rubric.marking_bands ? (
                             <table className="grade-table-print">
                               <thead><tr><th>Marks</th><th>Descriptor</th></tr></thead>
                               <tbody>{Object.entries(officialData.rubric.marking_bands).map(([marks, desc]) => <tr key={marks}><td>{marks}</td><td>{desc}</td></tr>)}</tbody>
                             </table>
                          ) : (
                             <p className="italic text-sm mb-4">Official marking criteria applied based on IB standards.</p>
                          )}
                        </div>
                     )}

                     {result.answer_key && (
                       <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]} components={MarkdownComponents}>
                         {result.answer_key}
                       </ReactMarkdown>
                     )}
                     
                     {/* Official Boundaries in Print */}
                     {(officialData?.boundaries || result.grade_boundaries) && (
                        <div className="mt-12 pt-8 border-t border-slate-200">
                          <h3 className="text-xl font-bold mb-4">Official Grade Boundaries</h3>
                          {officialData?.boundaries ? (
                             <table className="grade-table-print">
                               <thead><tr><th>Grade</th><th>Range (%)</th><th>Descriptor</th></tr></thead>
                               <tbody>{Object.entries(officialData.boundaries).filter(([k]) => k.startsWith('grade_')).map(([k, v]) => <tr key={k}><td>{k.replace('grade_', '')}</td><td>{v.min}-{v.max}%</td><td>{v.description}</td></tr>)}</tbody>
                             </table>
                          ) : (
                            <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]} components={MarkdownComponents}>
                              {result.grade_boundaries}
                            </ReactMarkdown>
                          )}
                        </div>
                     )}
                   </div>
                 </section>
               )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
