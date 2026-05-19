import React, { useEffect, useState } from 'react';
import Icon from '../../components/Icon';
import { Tag, ProgressBar } from '../../components/Shared';

function PaperReviewer({ paper, onAction, onBack }) {
  const [overrideMode, setOverrideMode] = useState(false);
  const [overrideScore, setOverrideScore] = useState(paper.aiScore);
  const [overrideNote, setOverrideNote] = useState('');

  const handleApprove = () => onAction('approved', paper.id, paper.aiScore, '');
  const handleOverride = () => {
    if (overrideMode) onAction('overridden', paper.id, overrideScore, overrideNote);
    else setOverrideMode(true);
  };
  const handleFlag = () => onAction('flagged', paper.id, paper.aiScore, '');

  useEffect(() => {
    const onKey = e => {
      if (e.key === 'a' || e.key === 'A') handleApprove();
      if (e.key === 'Escape') { setOverrideMode(false); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return (
    <div>
      <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:16 }}>
        <button className="btn-secondary" style={{ padding:'7px 12px', fontSize:12 }} onClick={onBack}>
          ← Back to Queue
        </button>
        <div style={{ fontSize:13, color:'var(--muted)' }}>Reviewing:</div>
        <div style={{ fontFamily:'var(--ff-mono)', fontSize:13, color:'var(--gold)' }}>{paper.student}</div>
        <div className="spacer"/>
        <div style={{ fontSize:12, color:'var(--muted)' }}>Exam: <strong style={{ color:'var(--text)', fontWeight:500 }}>{paper.exam}</strong></div>
        {paper.flagged && <Tag type="red">⚑ Plagiarism flagged</Tag>}
      </div>

      <div className="review-split">
        {/* Left: Student scan */}
        <div className="review-panel">
          <div className="review-panel-header">
            <Icon name="pdf" size={13}/> Student answer scan
          </div>
          <div className="review-panel-body">
            <div className="scan-title">Question</div>
            <div style={{ fontSize:13.5, marginBottom:16, lineHeight:1.6 }}>{paper.question}</div>
            <div className="scan-title">Handwritten answer (OCR extracted)</div>
            <div className="scan-placeholder">{paper.handwriting}</div>
            <div style={{ marginTop:12, padding:'10px 14px', background:'var(--card)', borderRadius:8, fontSize:12, color:'var(--muted)' }}>
              <span style={{ color:'var(--blue)' }}>📸</span> &nbsp;In production: actual cropped scan image rendered here from cloud storage.
            </div>
          </div>
        </div>

        {/* Right: AI grade */}
        <div className="review-panel">
          <div className="review-panel-header">
            <Icon name="review" size={13}/> AI-proposed grade
          </div>
          <div className="review-panel-body" style={{ flex:1 }}>
            <div className="ai-score-card">
              <div className="ai-score-label">AI Proposed Score</div>
              <div className="ai-score-value">
                {paper.aiScore}
                <span className="ai-score-max">/ {paper.maxScore}</span>
              </div>
              <div className="confidence-bar">
                <div style={{ display:'flex', justifyContent:'space-between', fontSize:11, color:'var(--muted)', marginBottom:4 }}>
                  <span>Confidence</span>
                  <span style={{ fontFamily:'var(--ff-mono)', color: paper.confidence > 0.85 ? 'var(--green)' : 'var(--gold)' }}>
                    {Math.round(paper.confidence * 100)}%
                  </span>
                </div>
                <ProgressBar value={paper.confidence * 100} color={paper.confidence > 0.85 ? 'var(--green)' : 'var(--gold)'}/>
              </div>
            </div>

            <div style={{ fontSize:12, color:'var(--muted)', fontFamily:'var(--ff-mono)', textTransform:'uppercase', letterSpacing:.5, marginBottom:8 }}>Criteria Breakdown</div>
            {paper.rubricCriteria.map((c, i) => (
              <div key={i} style={{ display:'flex', alignItems:'center', gap:10, padding:'7px 0', borderBottom:'1px solid var(--border)' }}>
                <div style={{ width:16, height:16, borderRadius:'50%', background: c.awarded === c.pts ? 'var(--green)' : c.awarded > 0 ? 'var(--gold)' : 'var(--red)', flexShrink:0, display:'flex', alignItems:'center', justifyContent:'center', fontSize:10, color:'#0b0d1a', fontWeight:700 }}>
                  {c.awarded === c.pts ? '✓' : c.awarded > 0 ? '~' : '✗'}
                </div>
                <div style={{ flex:1, fontSize:12.5 }}>{c.label}</div>
                <div style={{ fontFamily:'var(--ff-mono)', fontSize:12, color: c.awarded === c.pts ? 'var(--green)' : c.awarded > 0 ? 'var(--gold)' : 'var(--muted)' }}>
                  {c.awarded}/{c.pts}
                </div>
              </div>
            ))}

            <div style={{ fontSize:12, color:'var(--muted)', fontFamily:'var(--ff-mono)', textTransform:'uppercase', letterSpacing:.5, margin:'14px 0 8px' }}>AI Justification</div>
            <div className="justification-box">{paper.justification}</div>

            {paper.flagged && (
              <div className="flag-box">
                <Icon name="alert" size={15}/> <strong>Plagiarism flag:</strong> &nbsp;{paper.flagReason}
              </div>
            )}

            {overrideMode && (
              <div style={{ background:'var(--card)', border:'1px solid var(--blue)', borderRadius:8, padding:14, marginBottom:12 }}>
                <div style={{ fontSize:12, color:'var(--blue)', fontFamily:'var(--ff-mono)', marginBottom:10 }}>OVERRIDE SCORE</div>
                <div className="override-input-row">
                  <input type="number" value={overrideScore} min={0} max={paper.maxScore}
                    onChange={e => setOverrideScore(Number(e.target.value))}
                    style={{ maxWidth:80 }}
                  />
                  <span style={{ fontSize:13, color:'var(--muted)' }}>/ {paper.maxScore} pts</span>
                </div>
                <div className="mt-8">
                  <div className="form-label">Override Reason</div>
                  <textarea value={overrideNote} onChange={e => setOverrideNote(e.target.value)}
                    placeholder="Explain your override decision…" style={{ minHeight:60 }}/>
                </div>
              </div>
            )}
          </div>

          <div className="review-actions">
            <button className="btn-approve" onClick={handleApprove}>
              <Icon name="check" size={14}/> Approve <span className="kbd">A</span>
            </button>
            <button className="btn-override" onClick={handleOverride}>
              <Icon name="edit" size={14}/> {overrideMode ? 'Submit Override' : 'Override'}
            </button>
            {overrideMode && (
              <button className="btn-secondary" style={{ padding:'10px 12px', fontSize:13 }} onClick={() => setOverrideMode(false)}>Cancel</button>
            )}
            <button className="btn-flag" onClick={handleFlag}>
              <Icon name="flag" size={14}/> Flag
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── TA DASHBOARD ─────────────────────────────────────────────────────────

export default PaperReviewer;
