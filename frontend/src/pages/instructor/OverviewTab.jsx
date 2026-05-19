import React from 'react';
import { DEMO_EXAMS } from '../../data/demoData';
import { Tag, StatusTag, ProgressBar } from '../../components/Shared';

function OverviewTab() {
  const stats = [
    { label: 'Total Papers', value: 200, delta: '+55 this week', color: 'var(--gold)', accent: 'var(--gold)' },
    { label: 'AI Graded',    value: 131, delta: '65% complete',  color: 'var(--blue)', accent: 'var(--blue)' },
    { label: 'Pending Review',value: 47, delta: '9 flagged',     color: 'var(--purple)', accent: 'var(--purple)' },
    { label: 'Approved',     value: 84,  delta: '42% of total',  color: 'var(--green)', accent: 'var(--green)' },
  ];

  return (
    <div>
      <div className="stats-grid">
        {stats.map((s, i) => (
          <div key={i} className={`stat-card fade-up-${i+1}`}>
            <div className="stat-label">{s.label}</div>
            <div className="stat-value" style={{ color: s.color }}>{s.value}</div>
            <div className="stat-delta text-muted" style={{ fontSize: 12 }}>{s.delta}</div>
            <div className="stat-accent" style={{ background: s.accent + '66' }}/>
          </div>
        ))}
      </div>

      <div className="section-card">
        <div className="section-title">Active Exams</div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Exam Name</th>
              <th>Course</th>
              <th>Papers</th>
              <th>Progress</th>
              <th>Flagged</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {DEMO_EXAMS.map(ex => (
              <tr key={ex.id}>
                <td><strong style={{ fontWeight: 500 }}>{ex.name}</strong></td>
                <td><span className="text-muted">{ex.course}</span></td>
                <td><span className="text-mono">{ex.papers}</span></td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <ProgressBar value={ex.progress} color={ex.status === 'complete' ? 'var(--green)' : 'var(--gold)'}/>
                    <span className="text-mono text-muted" style={{ fontSize: 12 }}>{ex.progress}%</span>
                  </div>
                </td>
                <td>
                  {ex.flagged > 0 ?
                    <Tag type="red">{ex.flagged} flagged</Tag> :
                    <span className="text-muted">—</span>
                  }
                </td>
                <td><StatusTag status={ex.status}/></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="section-card">
        <div className="section-title">Pipeline Activity</div>
        {[
          { time: '2 min ago',  msg: 'AI graded 12 papers for CS301 Midterm',          color: 'var(--blue)'   },
          { time: '15 min ago', msg: 'TA approved 8 papers — MATH202 Final',            color: 'var(--green)'  },
          { time: '31 min ago', msg: 'Plagiarism flagged: 2 papers in CS301 (Q3)',      color: 'var(--red)'    },
          { time: '1 hr ago',   msg: 'OCR completed for CS301 Midterm (48 papers)',     color: 'var(--gold)'   },
          { time: '2 hrs ago',  msg: 'Rubric uploaded for CS401 Final (18 criteria)',   color: 'var(--purple)' },
        ].map((a, i) => (
          <div key={i} style={{ display:'flex', gap:14, alignItems:'flex-start', padding:'10px 0', borderBottom: i < 4 ? '1px solid var(--border)' : 'none' }}>
            <div style={{ width:8, height:8, borderRadius:'50%', background:a.color, marginTop:5, flexShrink:0 }}/>
            <div style={{ flex:1 }}>
              <div style={{ fontSize:13.5 }}>{a.msg}</div>
            </div>
            <div style={{ fontSize:11, color:'var(--muted)', fontFamily:'var(--ff-mono)', whiteSpace:'nowrap' }}>{a.time}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── UPLOAD TAB ───────────────────────────────────────────────────────────

export default OverviewTab;
