"use client";
import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const PLATFORM_LIMITS: Record<string, number> = {
  twitter: 280,
  linkedin: 3000,
  facebook: 2200,
  instagram: 2200
};

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
      closeModal();
    } catch (e: any) {
      alert(e.message);
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
      setAssets(prev => prev.filter(a => a.id !== viewingAsset.id));
      closeModal();
    } catch (e: any) {
      alert(e.message);
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
          <p style={{ opacity: 0.7, margin: 0 }}>
            {assets.length} item{assets.length === 1 ? '' : 's'} awaiting review.
          </p>
        </div>
        <button className="btn btn-primary" onClick={fetchQueue}>↻ Refresh</button>
      </div>

      {assets.length === 0 ? (
        <div className="glass-panel" style={{ padding: '4rem', textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✅</div>
          <h3>All caught up!</h3>
          <p style={{ opacity: 0.7, maxWidth: '400px', margin: '0 auto' }}>
            There are no items pending review right now. Run the pipeline to generate new assets.
          </p>
        </div>
      ) : (
        <div className="grid">
          {assets.map(asset => {
            const { hook, body } = getFormattedText(asset.content_text);
            return (
              <div key={asset.id} className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <div className="card-content" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem', alignItems: 'center' }}>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <span className="tag" style={{ background: 'rgba(255,153,0,0.2)', color: 'var(--primary)' }}>
                        {asset.platform}
                      </span>
                      {asset.brand_name && (
                        <span className="tag" style={{ background: 'rgba(255,255,255,0.1)' }}>
                          {asset.brand_name}
                        </span>
                      )}
                    </div>
                    <span className="tag">{asset.language.toUpperCase()}</span>
                  </div>
                  <div className="line-clamp-4" style={{ flex: 1 }}>
                    <span style={{ fontWeight: 600, fontSize: '1rem', display: 'block', marginBottom: body ? '0.5rem' : '0' }}>
                      {hook}
                    </span>
                    {body && (
                      <span style={{ fontSize: '0.9rem', opacity: 0.7, whiteSpace: 'pre-wrap' }}>
                        {body}
                      </span>
                    )}
                  </div>
                </div>
                <div className="card-actions">
                  <button className="btn" style={{ background: 'rgba(255,255,255,0.1)', color: 'white', width: '100%' }} onClick={() => openModal(asset)}>
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
          <div className="glass-panel modal-content" style={{ maxWidth: '600px', width: '90%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem', alignItems: 'center' }}>
              <h2 style={{ margin: 0 }}>Review Content</h2>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <span className="tag" style={{ background: 'var(--primary)', color: '#16191f' }}>{viewingAsset.platform}</span>
                {viewingAsset.brand_name && <span className="tag">{viewingAsset.brand_name}</span>}
              </div>
            </div>
            
            {!isRejecting ? (
              <>
                <div style={{ marginBottom: '1.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <label style={{ fontWeight: 600 }}>Content Text</label>
                    <span style={{ 
                      fontSize: '0.8rem', 
                      color: editText.length > (PLATFORM_LIMITS[viewingAsset.platform.toLowerCase()] || 2000) ? 'var(--danger)' : 'rgba(255,255,255,0.5)'
                    }}>
                      {editText.length} / {PLATFORM_LIMITS[viewingAsset.platform.toLowerCase()] || 2000} chars
                    </span>
                  </div>
                  <textarea
                    rows={10}
                    value={editText}
                    onChange={e => setEditText(e.target.value)}
                    style={{ resize: 'vertical' }}
                  />
                </div>
                
                <div style={{ display: 'flex', gap: '1rem', justifyContent: 'space-between' }}>
                  <button type="button" className="btn btn-danger" onClick={() => setIsRejecting(true)}>
                    ✗ Reject
                  </button>
                  <div style={{ display: 'flex', gap: '1rem' }}>
                    <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)', color: 'white' }} onClick={closeModal}>
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
                <h3 style={{ marginBottom: '1rem', color: 'var(--danger)' }}>Reject & Teach Agent</h3>
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
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)', color: 'white' }} onClick={() => setIsRejecting(false)}>
                    Back to Edit
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
