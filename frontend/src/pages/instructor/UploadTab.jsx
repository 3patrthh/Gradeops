import React, { useCallback, useRef, useState } from 'react';
import Icon from '../../components/Icon';
import { Tag } from '../../components/Shared';
import { uploadExam } from '../../services/examService';

function UploadTab() {
  const [files, setFiles] = useState([
    { name: 'cs301_midterm_batch1.pdf', size: '12.4 MB', pages: 96,  status: 'complete' },
    { name: 'cs301_midterm_batch2.pdf', size: '11.8 MB', pages: 88,  status: 'processing' },
    { name: 'math202_final_all.pdf',    size: '18.2 MB', pages: 186, status: 'complete' },
  ]);
  const [drag, setDrag] = useState(false);
  const [examName, setExamName] = useState('');
  const [course, setCourse]     = useState('');
  const fileInputRef = useRef(null);

  const handleDrop = useCallback(e => {
    e.preventDefault(); setDrag(false);
    const dropped = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.pdf'));
    addFiles(dropped);
  }, []);

  const handlePick = e => addFiles(Array.from(e.target.files));

  const addFiles = newFiles => {
    const items = newFiles.map(f => ({
      name: f.name,
      size: (f.size / 1048576).toFixed(1) + ' MB',
      pages: Math.floor(Math.random() * 120) + 40,
      status: 'queued',
      rawFile: f,
    }));
    setFiles(prev => [...prev, ...items]);
  };


  const handleStartProcessing = async () => {
    try {
      const uploaded = await uploadExam({
        examName,
        course,
        files,
      });
      console.log('Upload started:', uploaded);
      setFiles(prev => prev.map(file => ({ ...file, status: 'processing' })));
      alert('Upload sent to FastAPI. Check backend logs for processing status.');
    } catch (error) {
      console.error(error);
      alert('Backend is not running yet. Start FastAPI on http://localhost:8000 and try again.');
    }
  };

  return (
    <div>
      <div className="section-card fade-up">
        <div className="section-title">Exam Details</div>
        <div className="two-col">
          <div>
            <div className="form-label">Exam Name</div>
            <input placeholder="e.g. CS301 — Midterm Exam" value={examName} onChange={e => setExamName(e.target.value)}/>
          </div>
          <div>
            <div className="form-label">Course</div>
            <input placeholder="e.g. Data Structures" value={course} onChange={e => setCourse(e.target.value)}/>
          </div>
        </div>
        <div className="two-col mt-12">
          <div>
            <div className="form-label">Semester</div>
            <select>
              <option>Fall 2024</option>
              <option>Spring 2025</option>
              <option>Summer 2025</option>
            </select>
          </div>
          <div>
            <div className="form-label">Grading Model</div>
            <select>
              <option>Qwen-VL (recommended)</option>
              <option>Nougat OCR</option>
              <option>GPT-4V</option>
            </select>
          </div>
        </div>
      </div>

      <div className={`upload-zone fade-up-1 ${drag ? 'drag-over' : ''}`}
        onDragOver={e => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input ref={fileInputRef} type="file" accept=".pdf" multiple style={{ display:'none' }} onChange={handlePick}/>
        <div className="upload-icon">📄</div>
        <div className="upload-title">Drop exam PDFs here or click to browse</div>
        <div className="upload-hint">Supports multi-page scanned PDFs · Max 200MB per file · Bulk upload supported</div>
        <div style={{ marginTop: 16 }}>
          <button className="btn-gold" style={{ padding:'8px 20px' }} onClick={e => { e.stopPropagation(); fileInputRef.current?.click(); }}>
            Choose Files
          </button>
        </div>
      </div>

      {files.length > 0 && (
        <div className="fade-up-2 mt-16">
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:12 }}>
            <div className="section-title" style={{ margin:0 }}>Uploaded Files ({files.length})</div>
            <button className="btn-gold" style={{ padding:'8px 20px' }} onClick={handleStartProcessing}>Start Processing →</button>
          </div>
          {files.map((f, i) => (
            <div key={i} className="file-item">
              <div className="file-icon">📋</div>
              <div>
                <div className="file-name">{f.name}</div>
                <div className="file-meta">{f.size} · ~{f.pages} pages</div>
              </div>
              <div className="file-status">
                {f.status === 'complete'    && <Tag type="green">Ready</Tag>}
                {f.status === 'processing' && <Tag type="gold">Processing</Tag>}
                {f.status === 'queued'     && <Tag type="blue">Queued</Tag>}
              </div>
              <button className="remove-btn" onClick={() => setFiles(prev => prev.filter((_,j) => j !== i))}>✕</button>
            </div>
          ))}
          <div style={{ marginTop: 14, padding: '12px 16px', background: 'var(--card)', borderRadius: 8, fontSize: 13, color: 'var(--muted)', display:'flex', gap:8, alignItems:'flex-start' }}>
            <Icon name="info" size={15} />
            <span>After processing, answers will be automatically extracted, transcribed by the OCR model, and queued for the AI grading pipeline. You will be notified when grading is complete.</span>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── RUBRIC BUILDER TAB ───────────────────────────────────────────────────

export default UploadTab;
