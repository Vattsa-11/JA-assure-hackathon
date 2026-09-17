"use client";
import { useEffect, useState } from 'react';

export default function QueuePage() {
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [rejectingId, setRejectingId] = useState<number | null>(null);
  const [rejectTag, setRejectTag] = useState("tone");
  const [rejectNote, setRejectNote] = useState("");

  const fetchQueue = async () => {
    try {
      const res = await fetch('http://localhost:8000/review/queue');
      const data = await res.json();
      setAssets(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleApprove = async (id: number) => {
    await fetch(`http://localhost:8000/review/${id}/approve`, { method: 'POST' });
    setAssets(assets.filter(a => a.id !== id));
  };

  const handleReject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectingId) return;
    await fetch(`http://localhost:8000/review/${rejectingId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason_tag: rejectTag, note: rejectNote })
    });
    setAssets(assets.filter(a => a.id !== rejectingId));
    setRejectingId(null);
    setRejectNote("");
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Approval Queue</h1>
      <p style={{ opacity: 0.7, marginBottom: '2rem' }}>Content waiting for human review before publishing.</p>
      
      {assets.length === 0 ? (
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
          <h3>All caught up!</h3>
          <p style={{ opacity: 0.7 }}>No items pending review.</p>
        </div>
      ) : (
        <div className="grid">
          {assets.map(asset => (
            <div key={asset.id} className="glass-panel">
              <div className="card-content">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                  <span className="tag" style={{ background: 'var(--primary)' }}>{asset.platform}</span>
                  <span className="tag">{asset.language}</span>
                </div>
                <p style={{ whiteSpace: 'pre-wrap', fontSize: '0.9rem', lineHeight: 1.5 }}>
                  {asset.content_text}
                </p>
              </div>
              <div className="card-actions">
                <button className="btn btn-danger" onClick={() => setRejectingId(asset.id)}>Reject</button>
                <button className="btn btn-success" onClick={() => handleApprove(asset.id)}>Approve</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Reject Modal */}
      {rejectingId && (
        <div className="modal-overlay">
          <div className="glass-panel modal-content">
            <h2>Reject Content</h2>
            <form onSubmit={handleReject}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Reason Tag</label>
                <select value={rejectTag} onChange={e => setRejectTag(e.target.value)}>
                  <option value="tone">Tone / Voice</option>
                  <option value="compliance">Compliance</option>
                  <option value="accuracy">Factually Incorrect</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Feedback Note (Teaches the Agent)</label>
                <textarea 
                  rows={4} 
                  required 
                  value={rejectNote}
                  onChange={e => setRejectNote(e.target.value)}
                  placeholder="Explain what to avoid next time..."
                />
              </div>
              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)', color: 'white' }} onClick={() => setRejectingId(null)}>Cancel</button>
                <button type="submit" className="btn btn-danger">Confirm Rejection</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
