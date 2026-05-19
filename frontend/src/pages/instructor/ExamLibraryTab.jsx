import React, { useState } from 'react';
import Icon from '../../components/Icon';
import { DEMO_EXAMS } from '../../data/demoData';
import { Tag, StatusTag, ProgressBar } from '../../components/Shared';

function ExamLibraryTab() {
  const [search, setSearch] = useState('');
  const filtered = DEMO_EXAMS.filter(e =>
    e.name.toLowerCase().includes(search.toLowerCase()) ||
    e.course.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div style={{ display:'flex', gap:12, marginBottom:20 }} className="fade-up">
        <div style={{ flex:1, position:'relative' }}>
          <div style={{ position:'absolute', left:12, top:'50%', transform:'translateY(-50%)', color:'var(--muted)' }}>
            <Icon name="search" size={15}/>
          </div>
          <input placeholder="Search exams…" value={search} onChange={e => setSearch(e.target.value)}
            style={{ paddingLeft: 36 }}/>
        </div>
        <select style={{ width:160 }}>
          <option>All Courses</option>
          <option>CS301</option>
          <option>MATH202</option>
          <option>PHY101</option>
        </select>
        <select style={{ width:140 }}>
          <option>All Statuses</option>
          <option>Complete</option>
          <option>Processing</option>
          <option>Pending</option>
        </select>
      </div>

      <div className="table-card fade-up-1">
        <table className="data-table">
          <thead>
            <tr>
              <th>Exam</th>
              <th>Course</th>
              <th>Date</th>
              <th>Papers</th>
              <th>Graded</th>
              <th>Flagged</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(ex => (
              <tr key={ex.id}>
                <td><strong style={{ fontWeight:500 }}>{ex.name}</strong></td>
                <td><span className="text-muted">{ex.course}</span></td>
                <td><span className="text-mono text-muted" style={{ fontSize:12 }}>{ex.date}</span></td>
                <td><span className="text-mono">{ex.papers}</span></td>
                <td>
                  <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                    <ProgressBar value={ex.progress} color={ex.status === 'complete' ? 'var(--green)' : 'var(--gold)'}/>
                    <span className="text-mono text-muted" style={{ fontSize:11 }}>{ex.graded}/{ex.papers}</span>
                  </div>
                </td>
                <td>
                  {ex.flagged > 0 ?
                    <Tag type="red">⚑ {ex.flagged}</Tag> :
                    <span className="text-muted" style={{ fontSize:12 }}>—</span>
                  }
                </td>
                <td><StatusTag status={ex.status}/></td>
                <td>
                  <div style={{ display:'flex', gap:6 }}>
                    <button className="btn-secondary" style={{ padding:'5px 10px', fontSize:12 }}>View</button>
                    <button className="btn-secondary" style={{ padding:'5px 10px', fontSize:12 }}>Export</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">🔍</div>
            <div className="empty-state-title">No exams found</div>
            <div className="empty-state-sub">Try a different search term</div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── INSTRUCTOR DASHBOARD ─────────────────────────────────────────────────

export default ExamLibraryTab;
