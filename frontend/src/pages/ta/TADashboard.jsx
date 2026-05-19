import React, { useState } from 'react';
import Icon from '../../components/Icon';
import { Tag } from '../../components/Shared';
import { DEMO_QUEUE } from '../../data/demoData';
import PaperReviewer from './PaperReviewer';

function TADashboard({ onLogout }) {
  const [tab, setTab] = useState('queue');
  const [reviewing, setReviewing] = useState(null);
  const [queue, setQueue] = useState(DEMO_QUEUE);
  const [completed, setCompleted] = useState([]);

  const navItems = [
    { id:'queue',     icon:'review',   label:'Review Queue', badge: queue.length },
    { id:'flagged',   icon:'flag',     label:'Flagged',      badge: queue.filter(p => p.flagged).length },
    { id:'completed', icon:'check',    label:'Completed' },
  ];

  const handleAction = (action, id, score, note) => {
    const paper = queue.find(p => p.id === id);
    setQueue(prev => prev.filter(p => p.id !== id));
    setCompleted(prev => [...prev, { ...paper, action, finalScore: score, note, ts: new Date().toLocaleTimeString() }]);
    setReviewing(null);
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-name">Grade<span>Ops</span></div>
          <div className="sidebar-role-badge">TA Review Portal</div>
        </div>
        <nav className="sidebar-nav">
          <div className="sidebar-section-label">Review</div>
          {navItems.map(item => (
            <button key={item.id} className={`sidebar-item ${tab === item.id ? 'active' : ''}`}
              onClick={() => { setTab(item.id); setReviewing(null); }}>
              <Icon name={item.icon} size={15}/>
              {item.label}
              {item.badge > 0 && <span className="sidebar-badge">{item.badge}</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div style={{ padding:'8px 4px 8px', fontSize:11, color:'var(--muted)', fontFamily:'var(--ff-mono)', lineHeight:1.7 }}>
            Shortcuts<br/>
            <span className="kbd">A</span> Approve &nbsp; <span className="kbd">Esc</span> Cancel
          </div>
          <div className="sidebar-user">
            <div className="avatar avatar-blue">TA</div>
            <div>
              <div className="sidebar-user-name">TA Priya S.</div>
              <div className="sidebar-user-email">ta@univ.edu</div>
            </div>
          </div>
          <button className="signout-btn" onClick={onLogout}>Sign out</button>
        </div>
      </aside>

      <main className="main-content">
        <div className="page-header">
          <div>
            <div className="page-title">
              {reviewing ? `Reviewing Paper` : tab === 'queue' ? 'Review Queue' : tab === 'flagged' ? 'Flagged Papers' : 'Completed Reviews'}
            </div>
            <div className="page-sub">
              {tab === 'queue' && `${queue.length} paper${queue.length !== 1 ? 's' : ''} awaiting review`}
              {tab === 'flagged' && `${queue.filter(p=>p.flagged).length} papers flagged for potential plagiarism`}
              {tab === 'completed' && `${completed.length} papers reviewed this session`}
              {reviewing && `${reviewing.student} · ${reviewing.exam}`}
            </div>
          </div>
        </div>

        <div className="page-body">
          {reviewing ? (
            <PaperReviewer paper={reviewing} onAction={handleAction} onBack={() => setReviewing(null)}/>
          ) : (
            <>
              {tab === 'queue' && (
                queue.length === 0 ? (
                  <div className="empty-state fade-up">
                    <div className="empty-state-icon">✅</div>
                    <div className="empty-state-title">Queue is empty</div>
                    <div className="empty-state-sub">All papers reviewed. Great work!</div>
                  </div>
                ) : (
                  <div className="fade-up">
                    <div style={{ marginBottom: 16, padding:'12px 16px', background:'var(--card)', border:'1px solid var(--border)', borderRadius:8, fontSize:13, color:'var(--muted)', display:'flex', gap:8 }}>
                      <Icon name="info" size={15}/> Click a paper to open the side-by-side review view. Press <span className="kbd" style={{ margin:'0 4px' }}>A</span> to quickly approve.
                    </div>
                    {queue.map(p => (
                      <div key={p.id} className="queue-item" onClick={() => setReviewing(p)}>
                        <div className="queue-dot" style={{ background: p.flagged ? 'var(--red)' : 'var(--gold)' }}/>
                        <div className="queue-info">
                          <div className="queue-student">{p.student}</div>
                          <div className="queue-question">{p.question}</div>
                        </div>
                        <div style={{ textAlign:'right', flexShrink:0 }}>
                          <div className="queue-score">{p.aiScore}/{p.maxScore}</div>
                          <div style={{ fontSize:11, color:'var(--muted)', marginTop:2 }}>{Math.round(p.confidence*100)}% conf.</div>
                        </div>
                        {p.flagged && <Tag type="red">⚑</Tag>}
                        <Icon name="chevron_right" size={16}/>
                      </div>
                    ))}
                  </div>
                )
              )}

              {tab === 'flagged' && (
                <div className="fade-up">
                  {queue.filter(p => p.flagged).length === 0 ? (
                    <div className="empty-state">
                      <div className="empty-state-icon">🏁</div>
                      <div className="empty-state-title">No flagged papers</div>
                      <div className="empty-state-sub">No plagiarism flags in the current queue.</div>
                    </div>
                  ) : queue.filter(p => p.flagged).map(p => (
                    <div key={p.id} className="queue-item" onClick={() => setReviewing(p)}>
                      <div className="queue-dot" style={{ background:'var(--red)' }}/>
                      <div className="queue-info">
                        <div className="queue-student">{p.student}</div>
                        <div style={{ fontSize:12, color:'var(--red)', marginTop:2 }}>{p.flagReason}</div>
                      </div>
                      <div className="queue-score" style={{ color:'var(--red)' }}>{p.aiScore}/{p.maxScore}</div>
                      <Icon name="chevron_right" size={16}/>
                    </div>
                  ))}
                </div>
              )}

              {tab === 'completed' && (
                <div className="fade-up">
                  {completed.length === 0 ? (
                    <div className="empty-state">
                      <div className="empty-state-icon">📋</div>
                      <div className="empty-state-title">No reviews yet</div>
                      <div className="empty-state-sub">Your completed reviews will appear here.</div>
                    </div>
                  ) : (
                    <div className="table-card">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Student</th>
                            <th>Question</th>
                            <th>AI Score</th>
                            <th>Final Score</th>
                            <th>Action</th>
                            <th>Time</th>
                          </tr>
                        </thead>
                        <tbody>
                          {completed.map((p, i) => (
                            <tr key={i}>
                              <td><span className="text-mono">{p.student}</span></td>
                              <td><span className="text-muted" style={{ fontSize:12 }}>{p.question.substring(0,48)}…</span></td>
                              <td><span className="text-mono">{p.aiScore}/{p.maxScore}</span></td>
                              <td>
                                <span className="text-mono" style={{ color: p.finalScore !== p.aiScore ? 'var(--blue)' : 'var(--green)' }}>
                                  {p.finalScore}/{p.maxScore}
                                </span>
                              </td>
                              <td>
                                {p.action === 'approved'   && <Tag type="green">Approved</Tag>}
                                {p.action === 'overridden' && <Tag type="blue">Overridden</Tag>}
                                {p.action === 'flagged'    && <Tag type="red">Flagged</Tag>}
                              </td>
                              <td><span className="text-mono text-muted" style={{ fontSize:12 }}>{p.ts}</span></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}

// ─── ROOT APP ─────────────────────────────────────────────────────────────

export default TADashboard;
