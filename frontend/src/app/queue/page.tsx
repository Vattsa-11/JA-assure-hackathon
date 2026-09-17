"use client";
import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function QueuePage() {
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rejectingId, setRejectingId] = useState<number | null>(null);
  const [rejectTag, setRejectTag] = useState("tone");
  const [rejectNote, setRejectNote] = useState("");

  const fetchQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/review/queue`);
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      setAssets(data);
    } catch (e: any) {
      setError(e.message || 'Failed to load queue. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchQueue(); }, []);

  const handleApprove = async (id: number) => {
    try {
      const res = await fetch(`${API_URL}/review/${id}/approve`, { method: 'POST' });
      if (!res.ok) throw new Error(`Approve failed: ${res.status}`);
      setAssets(prev => prev.filter(a => a.id !== id));
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleReject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectingId) return;
    try {
      const res = await fetch(`${API_URL}/review/${rejectingId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason_tag: rejectTag, note: rejectNote })
      });
      if (!res.ok) throw new Error(`Reject failed: ${res.status}`);
      setAssets(prev => prev.filter(a => a.id !== rejectingId));
      setRejectingId(null);
      setRejectNote("");
    } catch (e: any) {
      alert(e.message);
    }
  };

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '50vh' }}>
      <div style={{ textAlign: 'center', opacity: 0.7 }}>
        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⏳</div>
        <p>Loading queue...</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="glass-panel" style={{ padding: '2rem', border: '1px solid var(--danger)' }}>
      <h3 style={{ color: 'var(--danger)' }}>Error</h3>
      <p>{error}</p>
      <button className="btn btn-primary" onClick={fetchQueue}>Retry</button>
    </div>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <h1>Approval Queue</h1>
          <p style={{ opacity: 0.7, margin: 0 }}>Content that passed compliance and awaits human review before publishing.</p>
        </div>
        <button className="btn btn-primary" onClick={fetchQueue}>↻ Refresh</button>
      </div>

      {assets.length === 0 ? (
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>✅</div>
          <h3>All caught up!</h3>
          <p style={{ opacity: 0.7 }}>No items pending review. Run the content pipeline to generate new assets.</p>
        </div>
      ) : (
        <div className="grid">
          {assets.map(asset => (
            <div key={asset.id} className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
              <div className="card-content" style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem', alignItems: 'center' }}>
                  <span className="tag" style={{ background: 'var(--primary)' }}>{asset.platform}</span>
                  <span className="tag">{asset.language.toUpperCase()}</span>
                </div>
                <p style={{ whiteSpace: 'pre-wrap', fontSize: '0.9rem', lineHeight: 1.6, margin: 0 }}>
                  {asset.content_text}
                </p>
              </div>
              <div className="card-actions">
                <button className="btn btn-danger" onClick={() => setRejectingId(asset.id)}>✗ Reject</button>
                <button className="btn btn-success" onClick={() => handleApprove(asset.id)}>✓ Approve</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Reject Modal */}
      {rejectingId && (
        <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) setRejectingId(null); }}>
          <div className="glass-panel modal-content">
            <h2 style={{ marginBottom: '1.5rem' }}>Reject & Teach the Agent</h2>
            <p style={{ opacity: 0.7, fontSize: '0.875rem', marginBottom: '1.5rem' }}>
              Your feedback will be injected into the agent's context next time it generates content for this brand.
            </p>
            <form onSubmit={handleReject}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Reason Tag</label>
                <select value={rejectTag} onChange={e => setRejectTag(e.target.value)}>
                  <option value="tone">Tone / Voice mismatch</option>
                  <option value="compliance">Compliance issue</option>
                  <option value="accuracy">Factually incorrect</option>
                  <option value="too_salesy">Too sales-y / pushy</option>
                  <option value="off_brand">Off-brand messaging</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                  Feedback Note <span style={{ opacity: 0.6, fontWeight: 400 }}>(teaches the agent)</span>
                </label>
                <textarea
                  rows={4}
                  required
                  value={rejectNote}
                  onChange={e => setRejectNote(e.target.value)}
                  placeholder="Be specific: e.g. 'Jade is a luxury brand — never use casual language or exclamation points.'"
                />
              </div>
              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)', color: 'white' }} onClick={() => setRejectingId(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-danger">Confirm Rejection</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
