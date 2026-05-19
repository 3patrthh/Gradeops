import React from 'react';

function Tag({ type, children }) {
  return <span className={`tag tag-${type}`}>{children}</span>;
}

function StatusTag({ status }) {
  const map = {
    processing: ['gold',  'Processing'],
    review:     ['blue',  'In Review'],
    complete:   ['green', 'Complete'],
    pending:    ['red',   'Pending'],
  };
  const [color, label] = map[status] || ['gold', status];
  return <Tag type={color}>{label}</Tag>;
}

function ProgressBar({ value, color = '#f0a500' }) {
  return (
    <div className="progress-bar">
      <div className="progress-fill" style={{ width: `${value}%`, background: color }}/>
    </div>
  );
}

// ─── LOGIN PAGE ───────────────────────────────────────────────────────────

export { Tag, StatusTag, ProgressBar };
