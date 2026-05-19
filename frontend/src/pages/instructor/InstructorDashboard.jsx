import React, { useState } from 'react';
import Icon from '../../components/Icon';
import OverviewTab from './OverviewTab';
import UploadTab from './UploadTab';
import RubricBuilderTab from './RubricBuilderTab';
import ExamLibraryTab from './ExamLibraryTab';

function InstructorDashboard({ onLogout }) {
  const [tab, setTab] = useState('dashboard');

  const navItems = [
    { id:'dashboard', icon:'dashboard', label:'Dashboard' },
    { id:'upload',    icon:'upload',    label:'Upload Exams'    },
    { id:'rubric',    icon:'rubric',    label:'Build Rubric'    },
    { id:'library',   icon:'exams',     label:'Exam Library'    },
    { id:'settings',  icon:'settings',  label:'Settings'        },
  ];

  const titles = {
    dashboard: { title:'Dashboard',    sub:'Pipeline overview and active exams' },
    upload:    { title:'Upload Exams', sub:'Upload bulk scanned PDFs for AI processing' },
    rubric:    { title:'Build Rubric', sub:'Define granular grading criteria per question' },
    library:   { title:'Exam Library', sub:'Browse and manage all exams' },
    settings:  { title:'Settings',     sub:'Configure pipeline and model options' },
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-name">Grade<span>Ops</span></div>
          <div className="sidebar-role-badge">Instructor Portal</div>
        </div>
        <nav className="sidebar-nav">
          <div className="sidebar-section-label">Navigation</div>
          {navItems.map(item => (
            <button key={item.id} className={`sidebar-item ${tab === item.id ? 'active' : ''}`}
              onClick={() => setTab(item.id)}>
              <Icon name={item.icon} size={15}/>
              {item.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="avatar avatar-gold">PR</div>
            <div>
              <div className="sidebar-user-name">Prof. Rajan</div>
              <div className="sidebar-user-email">prof@univ.edu</div>
            </div>
          </div>
          <button className="signout-btn" onClick={onLogout}>Sign out</button>
        </div>
      </aside>

      <main className="main-content">
        <div className="page-header">
          <div>
            <div className="page-title">{titles[tab]?.title}</div>
            <div className="page-sub">{titles[tab]?.sub}</div>
          </div>
          {tab === 'upload' && (
            <button className="btn-gold">+ New Exam</button>
          )}
        </div>
        <div className="page-body">
          {tab === 'dashboard' && <OverviewTab/>}
          {tab === 'upload'    && <UploadTab/>}
          {tab === 'rubric'    && <RubricBuilderTab/>}
          {tab === 'library'   && <ExamLibraryTab/>}
          {tab === 'settings'  && (
            <div className="section-card fade-up">
              <div className="section-title">Pipeline Settings</div>
              <div className="two-col">
                <div>
                  <div className="form-label">OCR Model</div>
                  <select><option>Qwen-VL (Default)</option><option>Nougat</option></select>
                </div>
                <div>
                  <div className="form-label">LLM Grading Model</div>
                  <select><option>GPT-4o</option><option>Claude 3.5 Sonnet</option><option>Local LLaMA</option></select>
                </div>
              </div>
              <div className="two-col mt-12">
                <div>
                  <div className="form-label">Plagiarism Threshold</div>
                  <input type="range" min={0.5} max={1} step={0.01} defaultValue={0.85} style={{ padding:0, background:'transparent', border:'none' }}/>
                  <div style={{ fontSize:12, color:'var(--muted)', marginTop:4 }}>Flag papers with similarity ≥ 0.85</div>
                </div>
                <div>
                  <div className="form-label">Confidence Threshold</div>
                  <input type="range" min={0.5} max={1} step={0.01} defaultValue={0.75} style={{ padding:0, background:'transparent', border:'none' }}/>
                  <div style={{ fontSize:12, color:'var(--muted)', marginTop:4 }}>Route low-confidence to human first</div>
                </div>
              </div>
              <div className="mt-16">
                <button className="btn-gold">Save Settings</button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// ─── TA REVIEW COMPONENT ──────────────────────────────────────────────────

export default InstructorDashboard;
