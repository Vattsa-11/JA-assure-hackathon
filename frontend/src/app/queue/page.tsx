"use client";
import { useEffect, useState, useCallback } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const CHAR_LIMITS: Record<string, number> = {
  twitter: 280,
  linkedin: 3000,
  facebook: 2200,
  instagram: 2200
};

const platformTagClass = (platform: string) =>
  `tag tag-platform-${(platform || '').toLowerCase().replace(/^x$/, 'x').replace(/\s+/g, '-')}`;
export default function QueuePage() {
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Modal State
  const [viewingAsset, setViewingAsset] = useState<any>(null);
  const [editText, setEditText] = useState("");
  
  // Reject State (inside modal)
  const [isRejecting, setIsRejecting] = useState(false);
  const [rejectTag, setRejectTag] = useState("tone");
  const [rejectNote, setRejectNote] = useState("");

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/review/queue`);
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      setAssets(data);
    } catch (e: unknown) {
      setError((e as Error).message || 'Failed to load queue. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchQueue(); }, [fetchQueue]);

  const handleApprove = async (id: number) => {
    try {
      const res = await fetch(`${API_URL}/review/${id}/approve`, { method: 'POST' });
      if (!res.ok) throw new Error(`Approve failed: ${res.status}`);
      setAssets(prev => prev.filter((a: Record<string,unknown>) => a.id !== id));
      closeModal();
    } catch (e: unknown) {
      alert((e as Error).message);
    }
  };

  const handleSaveEdit = async () => {
    if (!viewingAsset) return;
    try {
      const res = await fetch(`${API_URL}/review/${viewingAsset.id}/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_content_text: editText })
      });
      if (!res.ok) throw new Error(`Edit failed: ${res.status}`);
      setAssets(prev => prev.filter(a => a.id !== viewingAsset.id));
      closeModal();
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleReject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!viewingAsset) return;
    try {
      const res = await fetch(`${API_URL}/review/${viewingAsset.id}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason_tag: rejectTag, note: rejectNote })
      });
      if (!res.ok) throw new Error(`Reject failed: ${res.status}`);
      setAssets(prev => prev.filter((a: Record<string,unknown>) => a.id !== viewingAsset.id));
      closeModal();
    } catch (e: unknown) {
      alert((e as Error).message);
    }
  };

  const openModal = (asset: any) => {
    setViewingAsset(asset);
    setEditText(asset.content_text);
    setIsRejecting(false);
    setRejectNote("");
    setRejectTag("tone");
  };

  const closeModal = () => {
    setViewingAsset(null);
    setIsRejecting(false);
  };

  const getFormattedText = (text: string) => {
    const firstNewline = text.indexOf('\n');
    const firstPeriod = text.indexOf('. ');
    
    let splitIndex = -1;
    if (firstNewline > -1 && firstPeriod > -1) {
      splitIndex = Math.min(firstNewline, firstPeriod + 1);
    } else if (firstNewline > -1) {
      splitIndex = firstNewline;
    } else if (firstPeriod > -1) {
      splitIndex = firstPeriod + 1;
    }
    
    if (splitIndex === -1 || splitIndex > 150) {
      return { hook: text, body: "" };
    }
    return { 
      hook: text.slice(0, splitIndex).trim(), 
      body: text.slice(splitIndex).trim() 
    };
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
    <div className="page-container">
      <div className="glass-panel" style={{ padding: '2rem', border: '1px solid rgba(255,101,117,0.4)' }}>
        <h3 style={{ color: 'var(--danger)', marginTop: 0 }}>Error</h3>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={fetchQueue}>Retry</button>
      </div>
    </div>
  );

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Approval Queue</h1>
          <p className="page-subtitle">
            {assets.length} item{assets.length === 1 ? '' : 's'} awaiting review.
          </p>
        </div>
        <button className="btn" style={{ background: 'var(--foreground)', color: 'white' }} onClick={fetchQueue}>↻ Refresh</button>
      </div>

      {assets.length === 0 ? (
        <div className="ui-card" style={{ padding: '4rem', textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✅</div>
          <h3>All caught up!</h3>
          <p style={{ opacity: 0.6, maxWidth: '400px', margin: '0 auto' }}>
            There are no items pending review right now. Run the pipeline to generate new assets.
          </p>
        </div>
      ) : (
        <div className="grid">
          {assets.map((asset: Record<string,unknown>) => {
            const { hook, body } = getFormattedText(asset.content_text as string);
            return (
              <div key={asset.id} className="glass-panel queue-card">
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '1.5rem 1.5rem 0.75rem' }}>
                  <div className="queue-card-top">
                    <div className="queue-card-tags">
                      <span className={platformTagClass(asset.platform)}>
                        {asset.platform}
                      </span>
                      {asset.brand_name && (
                        <span className="tag tag-gray">{asset.brand_name}</span>
                      )}
                    </div>
                    <span className="tag tag-language">{(asset.language || '').toUpperCase()}</span>
                  </div>
                  <div className="queue-card-body">
                    <span className="queue-card-hook">{hook}</span>
                    {body && <span className="queue-card-body-text">{body}</span>}
                  </div>
                </div>
                <div style={{ padding: '0 1.5rem 1.5rem' }}>
                  <button className="btn queue-card-btn" onClick={() => openModal(asset)}>
                    View / Edit
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* View/Edit Modal */}
      {viewingAsset && (
        <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) closeModal(); }}>
          <div className="modal-content" style={{ maxWidth: '640px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', marginBottom: '1.5rem', alignItems: 'center' }}>
              <h2 style={{ margin: 0, fontSize: '1.35rem' }}>Review Content</h2>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <span className={platformTagClass(viewingAsset.platform)}>{viewingAsset.platform}</span>
                {viewingAsset.brand_name && <span className="tag tag-gray">{viewingAsset.brand_name}</span>}
                <span className="tag tag-language">{(viewingAsset.language || '').toUpperCase()}</span>
                <button
                  type="button"
                  onClick={closeModal}
                  aria-label="Close"
                  className="tag tag-gray"
                  style={{ border: 'none', cursor: 'pointer', fontFamily: 'inherit', padding: '0.25rem 0.65rem', fontSize: '0.8rem' }}
                >
                  ✕
                </button>
              </div>
            </div>
            
            {!isRejecting ? (
              <>
                <div>
                  <div className="modal-label">
                    <label htmlFor="review-textarea">Content Text</label>
                    <span className={`char-count${editText.length > (CHAR_LIMITS[(viewingAsset.platform || '').toLowerCase()] || 2000) ? ' char-count-over' : ''}`}>
                      {editText.length} / {CHAR_LIMITS[(viewingAsset.platform || '').toLowerCase()] || 2000} chars
                    </span>
                  </div>
                  <textarea
                    id="review-textarea"
                    rows={10}
                    value={editText}
                    onChange={e => setEditText(e.target.value)}
                  />
                </div>
                
                <div className="modal-actions">
                  <button type="button" className="btn btn-danger" onClick={() => setIsRejecting(true)}>
                    ✗ Reject
                  </button>
                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <button type="button" className="btn btn-ghost" onClick={closeModal}>
                      Cancel
                    </button>
                    {editText !== viewingAsset.content_text ? (
                      <button type="button" className="btn btn-primary" onClick={handleSaveEdit}>
                        ✓ Save & Approve
                      </button>
                    ) : (
                      <button type="button" className="btn btn-success" onClick={() => handleApprove(viewingAsset.id)}>
                        ✓ Approve As-Is
                      </button>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <form onSubmit={handleReject}>
                <h3 style={{ marginTop: 0, marginBottom: '0.5rem', color: 'var(--danger)' }}>Reject & Teach Agent</h3>
                <p style={{ margin: '0 0 1.25rem 0', fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                  Your note is saved as a lesson — the agent reads it before generating content for this brand again.
                </p>
                <div style={{ marginBottom: '1.25rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 700, fontSize: '0.92rem' }}>Reason Tag</label>
                  <select value={rejectTag} onChange={e => setRejectTag(e.target.value)}>
                    <option value="tone">Tone / Voice mismatch</option>
                    <option value="compliance">Compliance issue</option>
                    <option value="accuracy">Factually incorrect</option>
                    <option value="too_salesy">Too sales-y / pushy</option>
                    <option value="off_brand">Off-brand messaging</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 700, fontSize: '0.92rem' }}>
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
                <div className="modal-actions">
                  <button type="button" className="btn btn-ghost" onClick={() => setIsRejecting(false)}>
                    ← Back to Edit
                  </button>
                  <button type="submit" className="btn btn-danger">Confirm Rejection</button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
