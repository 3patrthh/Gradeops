import React, { useRef, useState } from 'react';
import Icon from '../../components/Icon';
import { saveRubric, uploadRubricJson } from '../../services/rubricService';

function RubricBuilderTab() {
  const [rubricName, setRubricName] = useState('CS301 — Midterm Rubric');
  const [questions, setQuestions] = useState([
    {
      id: 1,
      text: 'Explain the time complexity of merge sort and justify your answer.',
      maxPts: 10,
      criteria: [
        { text: 'Correct O(n log n) stated', pts: 3 },
        { text: 'Recurrence relation T(n)=2T(n/2)+O(n) shown', pts: 3 },
        { text: 'Master Theorem or proof provided', pts: 2 },
        { text: 'Space complexity O(n) discussed', pts: 2 },
      ],
    },
    {
      id: 2,
      text: 'Prove by induction that 1 + 2 + ... + n = n(n+1)/2.',
      maxPts: 15,
      criteria: [
        { text: 'Base case correctly shown', pts: 3 },
        { text: 'Inductive hypothesis explicitly stated', pts: 3 },
        { text: 'Algebraic manipulation correct', pts: 5 },
        { text: 'Formal conclusion with QED', pts: 2 },
        { text: 'Notation clarity', pts: 2 },
      ],
    },
  ]);
  const [saved, setSaved] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [uploadingJson, setUploadingJson] = useState(false);
  const jsonInputRef = useRef(null);

  const addQuestion = () => {
    setQuestions(prev => [...prev, { id: Date.now(), text: '', maxPts: 10, criteria: [] }]);
  };

  const removeQuestion = id => setQuestions(prev => prev.filter(q => q.id !== id));

  const updateQuestion = (id, field, value) =>
    setQuestions(prev => prev.map(q => q.id === id ? { ...q, [field]: value } : q));

  const addCriteria = qid =>
    setQuestions(prev => prev.map(q => q.id === qid ? { ...q, criteria: [...q.criteria, { text: '', pts: 1 }] } : q));

  const updateCriteria = (qid, idx, field, value) =>
    setQuestions(prev => prev.map(q => q.id === qid ? {
      ...q, criteria: q.criteria.map((c, i) => i === idx ? { ...c, [field]: value } : c)
    } : q));

  const removeCriteria = (qid, idx) =>
    setQuestions(prev => prev.map(q => q.id === qid ? {
      ...q, criteria: q.criteria.filter((_, i) => i !== idx)
    } : q));

  const totalPts = questions.reduce((s, q) => s + Number(q.maxPts || 0), 0);

  const handleSave = async () => {
    try {
      setStatusMessage('Saving rubric to MongoDB...');
      await saveRubric({
        name: rubricName,
        exam_id: null,
        questions,
      });
      setSaved(true);
      setStatusMessage('Rubric saved to MongoDB.');
      setTimeout(() => setSaved(false), 2000);
    } catch (error) {
      setStatusMessage(error.message || 'Failed to save rubric.');
    }
  };

  const loadRubricIntoBuilder = (rubric) => {
    const loadedQuestions = (rubric.questions || []).map((question, index) => ({
      id: question.id || question.question_id || Date.now() + index,
      text: question.text || question.question || question.prompt || question.question_text || '',
      maxPts: question.maxPts || question.max_marks || question.maxScore || question.marks || 10,
      criteria: (question.criteria || []).map((criterion) => ({
        text: criterion.text || criterion.description || criterion.label || '',
        pts: criterion.pts || criterion.marks || criterion.points || 1,
      })),
    }));

    if (rubric.name) setRubricName(rubric.name);
    if (loadedQuestions.length > 0) setQuestions(loadedQuestions);
  };

  const handleJsonRubricUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.json')) {
      setStatusMessage('Please select a valid .json rubric file.');
      return;
    }

    try {
      setUploadingJson(true);
      setStatusMessage('Uploading JSON rubric to MongoDB...');

      const rawText = await file.text();
      const parsed = JSON.parse(rawText);
      const response = await uploadRubricJson(file, rubricName);
      const savedRubric = response.rubric || parsed;

      loadRubricIntoBuilder(savedRubric);
      setStatusMessage('JSON rubric uploaded, saved to MongoDB, and loaded into the builder.');
    } catch (error) {
      setStatusMessage(error.message || 'Failed to upload JSON rubric.');
    } finally {
      setUploadingJson(false);
      event.target.value = '';
    }
  };

  return (
    <div>
      <div className="section-card fade-up">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <div>
            <div className="section-title" style={{ marginBottom: 4 }}>Rubric Source</div>
            <div className="text-muted" style={{ fontSize: 13 }}>Create manually or upload an existing JSON rubric file.</div>
          </div>
          <div>
            <input
              ref={jsonInputRef}
              type="file"
              accept=".json,application/json"
              style={{ display: 'none' }}
              onChange={handleJsonRubricUpload}
            />
            <button className="btn-secondary" onClick={() => jsonInputRef.current?.click()} disabled={uploadingJson}>
              {uploadingJson ? 'Uploading JSON…' : 'Upload JSON Rubric'}
            </button>
          </div>
        </div>

        {statusMessage && (
          <div style={{ marginBottom: 14, padding: '10px 12px', background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 13, color: 'var(--muted)' }}>
            {statusMessage}
          </div>
        )}

        <div className="two-col">
          <div>
            <div className="form-label">Rubric Name</div>
            <input value={rubricName} onChange={e => setRubricName(e.target.value)}/>
          </div>
          <div>
            <div className="form-label">Linked Exam</div>
            <select>
              <option>CS301 — Midterm</option>
              <option>MATH202 — Final</option>
              <option>New Exam…</option>
            </select>
          </div>
        </div>
        <div style={{ marginTop: 12, display:'flex', alignItems:'center', gap:8 }}>
          <div style={{ fontSize:13, color:'var(--muted)' }}>Total points: </div>
          <div style={{ fontFamily:'var(--ff-mono)', color:'var(--gold)', fontSize:14 }}>{totalPts} pts across {questions.length} question{questions.length !== 1 ? 's' : ''}</div>
        </div>
      </div>

      {questions.map((q, qi) => (
        <div key={q.id} className="rubric-question fade-up-1">
          <div className="rubric-q-header">
            <div className="q-number">{qi + 1}</div>
            <input
              value={q.text} placeholder="Question prompt…"
              onChange={e => updateQuestion(q.id, 'text', e.target.value)}
              style={{ flex:1 }}
            />
            <div style={{ display:'flex', alignItems:'center', gap:6, flexShrink:0 }}>
              <span style={{ fontSize:12, color:'var(--muted)' }}>Max pts</span>
              <input
                type="number" value={q.maxPts} min={1} max={100}
                onChange={e => updateQuestion(q.id, 'maxPts', e.target.value)}
                style={{ width:64, textAlign:'center' }}
              />
            </div>
            <button className="btn-danger" onClick={() => removeQuestion(q.id)}>
              <Icon name="trash" size={14}/>
            </button>
          </div>

          <div style={{ marginBottom: 8 }}>
            <div style={{ fontSize: 11, color:'var(--muted)', fontFamily:'var(--ff-mono)', textTransform:'uppercase', letterSpacing:.6, marginBottom:8 }}>Grading Criteria</div>
            {q.criteria.map((c, ci) => (
              <div key={ci} className="criteria-item">
                <input
                  value={c.text} placeholder="Criterion description…"
                  onChange={e => updateCriteria(q.id, ci, 'text', e.target.value)}
                  style={{ flex:1 }}
                />
                <div style={{ display:'flex', alignItems:'center', gap:6, flexShrink:0 }}>
                  <div className="criteria-pts">
                    <input
                      type="number" value={c.pts} min={0.5} step={0.5}
                      onChange={e => updateCriteria(q.id, ci, 'pts', e.target.value)}
                      style={{ width:48, textAlign:'center', background:'transparent', border:'none', color:'var(--blue)', padding:'0 2px', fontFamily:'var(--ff-mono)' }}
                    />
                    <span>pts</span>
                  </div>
                  <button className="remove-btn" style={{ fontSize:14 }} onClick={() => removeCriteria(q.id, ci)}>✕</button>
                </div>
              </div>
            ))}
            <button className="btn-add mt-8" onClick={() => addCriteria(q.id)}>
              + Add Criterion
            </button>
          </div>
        </div>
      ))}

      <div style={{ display:'flex', gap:10, marginTop:4 }}>
        <button className="btn-add" onClick={addQuestion} style={{ padding:'10px 18px', fontSize:13 }}>
          + Add Question
        </button>
        <div className="spacer"/>
        <button className="btn-secondary" onClick={() => {
          const blob = new Blob([JSON.stringify({ name: rubricName, questions }, null, 2)], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${rubricName.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.json`;
          a.click();
          URL.revokeObjectURL(url);
        }}>
          Export JSON
        </button>
        <button className="btn-gold" onClick={handleSave}>
          {saved ? '✓ Saved!' : 'Save Rubric'}
        </button>
      </div>
    </div>
  );
}

// ─── EXAM LIBRARY TAB ─────────────────────────────────────────────────────

export default RubricBuilderTab;
