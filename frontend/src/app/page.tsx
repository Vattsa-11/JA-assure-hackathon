"use client";
import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const PLATFORM_LIMITS: Record<string, number> = {
  twitter: 280,
  linkedin: 3000,
  facebook: 2200,
  instagram: 2200
};

export default function UnifiedDashboard() {
  const [brands, setBrands] = useState<any[]>([]);
  const [stats, setStats] = useState({ pending: 0, approved: 0, rejected: 0, videos: 0 });
  const [feed, setFeed] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("ALL");

  // Form State
  const [selectedBrand, setSelectedBrand] = useState("");
  const [topic, setTopic] = useState("");
  const [platforms, setPlatforms] = useState({ twitter: true, linkedin: true, facebook: false, instagram: false });
  const [generateVideo, setGenerateVideo] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  // Modal State
  const [viewingItem, setViewingItem] = useState<any>(null);
  const [editText, setEditText] = useState("");
  const [isRejecting, setIsRejecting] = useState(false);
  const [rejectTag, setRejectTag] = useState("tone");
  const [rejectNote, setRejectNote] = useState("");

  const fetchDashboard = async () => {
    try {
      const [statsRes, feedRes, brandsRes] = await Promise.all([
        fetch(`${API_URL}/dashboard/stats`),
        fetch(`${API_URL}/dashboard/feed`),
        fetch(`${API_URL}/dashboard/brands`)
      ]);
      
      if (statsRes.ok) setStats(await statsRes.json());
      if (feedRes.ok) setFeed(await feedRes.json());
      if (brandsRes.ok) {
        const brandsData = await brandsRes.json();
        setBrands(brandsData);
        if (!selectedBrand && brandsData.length > 0) {
          setSelectedBrand(brandsData[0].id.toString());
        }
      }
    } catch (e) {
      console.error("Failed to fetch dashboard data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBrand || !topic) return;
    setIsGenerating(true);
    
    try {
      await fetch(`${API_URL}/pipeline/content/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brand_id: parseInt(selectedBrand), topic })
      });

      if (generateVideo) {
        await fetch(`${API_URL}/pipeline/video/run`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ brand_id: parseInt(selectedBrand), topic })
        });
      }
      
      setTopic("");
      fetchDashboard();
    } catch (e) {
      console.error(e);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApprove = async (id: number) => {
    try {
      await fetch(`${API_URL}/review/${id}/approve`, { method: 'POST' });
      fetchDashboard();
      closeModal();
    } catch (e: any) { alert(e.message); }
  };

  const handleSaveEdit = async () => {
    if (!viewingItem) return;
    try {
      await fetch(`${API_URL}/review/${viewingItem.id}/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_content_text: editText })
      });
      fetchDashboard();
      closeModal();
    } catch (e: any) { alert(e.message); }
  };

  const handleReject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!viewingItem) return;
    try {
      await fetch(`${API_URL}/review/${viewingItem.id}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason_tag: rejectTag, note: rejectNote })
      });
      fetchDashboard();
      closeModal();
    } catch (e: any) { alert(e.message); }
  };

  const openModal = (item: any) => {
    setViewingItem(item);
    setEditText(item.content_text || item.draft_outreach || "");
    setIsRejecting(false);
    setRejectNote("");
    setRejectTag("tone");
  };

  const closeModal = () => {
    setViewingItem(null);
    setIsRejecting(false);
  };

  const getFormattedText = (text: string) => {
    if (!text) return { hook: "", body: "" };
    const firstNewline = text.indexOf('\n');
    const firstPeriod = text.indexOf('. ');
    
    let splitIndex = -1;
    if (firstNewline > -1 && firstPeriod > -1) splitIndex = Math.min(firstNewline, firstPeriod + 1);
    else if (firstNewline > -1) splitIndex = firstNewline;
    else if (firstPeriod > -1) splitIndex = firstPeriod + 1;
    
    if (splitIndex === -1 || splitIndex > 150) return { hook: text, body: "" };
    return { hook: text.slice(0, splitIndex).trim(), body: text.slice(splitIndex).trim() };
  };

  const filteredFeed = feed.filter(item => {
    if (filter === "BLOCKED") return item.status === "blocked";
    return true;
  });

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--background)' }}>
      {/* Sleek Minimalist Sidebar */}
      <div style={{ width: '80px', background: 'white', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2rem 0', gap: '2rem', boxShadow: '2px 0 10px rgba(0,0,0,0.02)', zIndex: 10 }}>
        <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'linear-gradient(135deg, var(--primary) 0%, #8A84FF 100%)', display: 'flex', justifyContent: 'center', alignItems: 'center', color: 'white', fontWeight: 'bold' }}>
          JA
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', opacity: 0.5 }}>
          <div style={{ width: '24px', height: '24px', borderRadius: '50%', border: '2px solid currentColor' }}></div>
          <div style={{ width: '24px', height: '24px', borderRadius: '4px', border: '2px solid currentColor' }}></div>
          <div style={{ width: '24px', height: '24px', borderRadius: '50%', border: '2px dashed currentColor' }}></div>
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1, padding: '3rem', maxWidth: '1400px', margin: '0 auto' }}>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
          <div>
            <h1 style={{ margin: '0 0 0.5rem 0', fontSize: '2rem', fontWeight: 800, color: 'var(--foreground)' }}>
              Welcome back, Judge 👋
            </h1>
            <p style={{ margin: 0, opacity: 0.6, fontSize: '1.1rem' }}>Let's review today's marketing assets.</p>
          </div>
        </div>

        {/* STEP 1: Input (Coral Card) */}
        <div className="coral-card" style={{ padding: '2.5rem', marginBottom: '3rem', position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', right: '-10%', top: '-50%', width: '300px', height: '300px', background: 'rgba(255,255,255,0.1)', borderRadius: '50%' }}></div>
          <div style={{ position: 'absolute', right: '10%', bottom: '-20%', width: '150px', height: '150px', background: 'rgba(255,255,255,0.1)', borderRadius: '50%' }}></div>
          
          <div style={{ position: 'relative', zIndex: 1 }}>
            <h2 style={{ marginTop: 0, marginBottom: '0.5rem', fontSize: '1.8rem' }}>Step 1: Start Campaign</h2>
            <p style={{ opacity: 0.9, marginBottom: '2rem' }}>Enter a topic and watch the AI agents generate drafts, check compliance, and queue them for review.</p>
            
            <form onSubmit={handleGenerate} style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
              <div style={{ flex: '1 1 200px' }}>
                <label style={{ display: 'block', fontSize: '0.9rem', marginBottom: '0.5rem', fontWeight: 600 }}>1. Select Brand</label>
                <select value={selectedBrand} onChange={e => setSelectedBrand(e.target.value)} required>
                  {brands.map(b => (
                    <option key={b.id} value={b.id}>{b.name}</option>
                  ))}
                </select>
              </div>
              <div style={{ flex: '2 1 300px' }}>
                <label style={{ display: 'block', fontSize: '0.9rem', marginBottom: '0.5rem', fontWeight: 600 }}>2. Topic / Brief</label>
                <input type="text" placeholder="e.g. Write about jewellery theft insurance..." value={topic} onChange={e => setTopic(e.target.value)} required />
              </div>
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', height: '45px', paddingBottom: '0.5rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontWeight: 600 }}>
                  <input type="checkbox" checked={generateVideo} onChange={e => setGenerateVideo(e.target.checked)} style={{ width: 'auto' }} />
                  Include Video
                </label>
              </div>
              <button type="submit" className="btn btn-white" disabled={isGenerating} style={{ height: '48px', padding: '0 2rem' }}>
                {isGenerating ? 'Generating...' : 'Go Premium (Run Pipeline)'}
              </button>
            </form>
          </div>
        </div>

        {/* STEPS 2, 3, 6, 7: Pipeline Stats (White Cards) */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ margin: 0, fontSize: '1.5rem' }}>Pipeline Status</h2>
        </div>
        
        <div className="grid" style={{ marginBottom: '3rem', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))' }}>
          <div className="ui-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
                <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'var(--warning)' }}></div>
                Pending Review
              </div>
              <span style={{ color: 'var(--success)', fontSize: '0.8rem', fontWeight: 700 }}>Step 4 & 5</span>
            </div>
            <div style={{ fontSize: '2.5rem', fontWeight: 800 }}>{stats.pending}</div>
            <div style={{ fontSize: '0.85rem', opacity: 0.6 }}>Clean drafts awaiting human decision.</div>
          </div>

          <div className="ui-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
                <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'var(--danger)' }}></div>
                Rejected / Blocked
              </div>
              <span style={{ color: 'var(--success)', fontSize: '0.8rem', fontWeight: 700 }}>Step 3</span>
            </div>
            <div style={{ fontSize: '2.5rem', fontWeight: 800 }}>{stats.rejected}</div>
            <div style={{ fontSize: '0.85rem', opacity: 0.6 }}>Caught by Compliance Inspector.</div>
          </div>

          <div className="ui-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
                <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'var(--primary)' }}></div>
                Active Lessons
              </div>
              <span style={{ color: 'var(--success)', fontSize: '0.8rem', fontWeight: 700 }}>Step 6 & 7</span>
            </div>
            <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--primary)' }}>Auto-Applied</div>
            <div style={{ fontSize: '0.85rem', opacity: 0.6 }}>AI avoids past mistakes on next run.</div>
          </div>
        </div>

        {/* STEP 4 & 5: Inbox (Feed) */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ margin: 0, fontSize: '1.5rem' }}>Inbox <span style={{ background: 'var(--primary)', color: 'white', fontSize: '0.9rem', padding: '0.2rem 0.6rem', borderRadius: '50px', marginLeft: '0.5rem' }}>{stats.pending}</span></h2>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className={`btn ${filter === 'ALL' ? 'btn-primary' : 'btn-white'}`} onClick={() => setFilter('ALL')} style={{ boxShadow: 'none', border: filter === 'ALL' ? 'none' : '1px solid var(--card-border)' }}>All Drafts</button>
            <button className={`btn ${filter === 'BLOCKED' ? 'btn-danger' : 'btn-white'}`} onClick={() => setFilter('BLOCKED')} style={{ boxShadow: 'none', border: filter === 'BLOCKED' ? 'none' : '1px solid var(--card-border)' }}>Blocked by Inspector</button>
          </div>
        </div>

        <div className="ui-card" style={{ padding: '1rem', background: 'white' }}>
          {Object.entries(filteredFeed.reduce((acc: any, item) => {
            const topic = item.topic || "Legacy / Unknown Topic";
            if (!acc[topic]) acc[topic] = [];
            acc[topic].push(item);
            return acc;
          }, {})).map(([topic, items]: [string, any], index) => (
            <details key={topic} style={{ borderBottom: '1px solid var(--card-border)', paddingBottom: '1rem', marginBottom: '1rem' }} open={index === 0}>
              <summary style={{ cursor: 'pointer', fontSize: '1.1rem', fontWeight: 700, padding: '1rem', background: '#f8f9fc', borderRadius: '12px', display: 'flex', justifyContent: 'space-between' }}>
                <span>{topic}</span>
                <span className="tag tag-primary">{items.length} Drafts</span>
              </summary>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1rem', padding: '0 1rem' }}>
                {items.map((item: any, itemIndex: number) => {
                  const isBlocked = item.status === "blocked";
                  const isRejected = item.status === "rejected";
                  const isPending = item.status === "pending_review";
                  const variantCount = items.filter((x: any, i: number) => i <= itemIndex && x.platform === item.platform && x.type === 'TEXT').length;
                  const displayPlatform = (item.platform && item.type === 'TEXT') ? `${item.platform} v${variantCount}` : item.platform;
                  
                  return (
                    <div key={`${item.type}-${item.id}`} style={{ 
                      display: 'flex', alignItems: 'center', padding: '1.25rem', gap: '1.5rem',
                      background: 'white', borderRadius: '12px', transition: 'background 0.2s',
                      opacity: (isBlocked || isRejected) ? 0.5 : 1,
                      border: isBlocked ? '1px solid var(--danger)' : '1px solid transparent',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.02)'
                    }} className="inbox-row">
                      
                      {/* Icon */}
                      <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: isBlocked ? 'rgba(255, 101, 117, 0.1)' : 'rgba(90, 82, 255, 0.1)', display: 'flex', justifyContent: 'center', alignItems: 'center', color: isBlocked ? 'var(--danger)' : 'var(--primary)', fontWeight: 'bold', flexShrink: 0 }}>
                        {item.platform ? item.platform.charAt(0).toUpperCase() : item.type.charAt(0)}
                      </div>

                      {/* Content Preview */}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.25rem', alignItems: 'center' }}>
                          <span style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--foreground)' }}>{item.brand_name || item.business_name}</span>
                          {displayPlatform && <span className="tag tag-gray" style={{ fontSize: '0.65rem' }}>{displayPlatform.toUpperCase()}</span>}
                          {isBlocked && <span className="tag tag-danger" style={{ fontSize: '0.65rem' }}>Inspector Blocked</span>}
                          {isRejected && <span className="tag tag-danger" style={{ fontSize: '0.65rem' }}>Rejected</span>}
                          {isPending && <span className="tag tag-warning" style={{ fontSize: '0.65rem', background: '#fef3c7', color: '#b45309' }}>Requires Human</span>}
                        </div>
                        <div style={{ fontSize: '0.9rem', color: '#636e72', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {item.type === 'TEXT' && item.content_text.replace(/\n/g, ' ')}
                          {item.type === 'LEAD' && item.draft_outreach}
                          {item.type === 'VIDEO' && "Video script generated"}
                        </div>
                        
                        {/* Lessons Visual cue (Step 7) */}
                        {item.lessons && item.lessons.length > 0 && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--primary)', marginTop: '0.25rem', fontWeight: 600 }}>
                            ✨ Generated using {item.lessons.length} learned lessons
                          </div>
                        )}
                      </div>

                      {/* Action */}
                      {(isPending || isBlocked) && (
                        <button className="btn btn-white" style={{ border: '1px solid var(--card-border)', fontSize: '0.8rem', padding: '0.5rem 1rem' }} onClick={() => openModal(item)}>
                          Step 5: Decide
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </details>
          ))}
          {feed.length === 0 && !loading && (
            <div style={{ padding: '3rem', textAlign: 'center', opacity: 0.5 }}>No drafts generated yet. Start a campaign above!</div>
          )}
        </div>
      </div>

      {/* View/Edit Modal (Step 5 & 6) */}
      {viewingItem && (
        <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) closeModal(); }}>
          <div className="modal-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', alignItems: 'center' }}>
              <h2 style={{ margin: 0, fontSize: '1.5rem' }}>Step 5: Human Decision</h2>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <span className="tag tag-primary">{viewingItem.type}</span>
              </div>
            </div>
            
            {!isRejecting ? (
              <>
                <div style={{ marginBottom: '1.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <label style={{ fontWeight: 600 }}>Draft Content</label>
                    {viewingItem.platform && (
                      <span style={{ 
                        fontSize: '0.8rem', 
                        color: editText.length > (PLATFORM_LIMITS[viewingItem.platform.toLowerCase()] || 2000) ? 'var(--danger)' : 'var(--primary)'
                      }}>
                        {editText.length} / {PLATFORM_LIMITS[viewingItem.platform.toLowerCase()] || 2000}
                      </span>
                    )}
                  </div>
                  <textarea
                    rows={8}
                    value={editText}
                    onChange={e => setEditText(e.target.value)}
                    style={{ resize: 'vertical', width: '100%', padding: '1rem', borderRadius: '12px', border: '1px solid var(--card-border)', fontFamily: 'inherit', fontSize: '0.9rem', outline: 'none' }}
                  />
                </div>

                {viewingItem.type === "VIDEO" && viewingItem.video_file_path && (
                  <video controls src={`${API_URL}/media/${viewingItem.video_file_path.split(/[\\/]/).pop()}`} style={{ width: '100%', borderRadius: '12px', marginBottom: '1.5rem' }} />
                )}
                
                <div style={{ display: 'flex', gap: '1rem', justifyContent: 'space-between' }}>
                  <button type="button" className="btn btn-danger" onClick={() => setIsRejecting(true)}>
                    Reject & Teach (Step 6)
                  </button>
                  <div style={{ display: 'flex', gap: '1rem' }}>
                    <button type="button" className="btn btn-white" onClick={closeModal} style={{ border: '1px solid var(--card-border)' }}>
                      Cancel
                    </button>
                    {editText !== (viewingItem.content_text || viewingItem.draft_outreach) ? (
                      <button type="button" className="btn btn-primary" onClick={handleSaveEdit}>
                        Save & Approve
                      </button>
                    ) : (
                      <button type="button" className="btn btn-success" onClick={() => handleApprove(viewingItem.id)}>
                        Approve As-Is
                      </button>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <form onSubmit={handleReject}>
                <h3 style={{ marginBottom: '1rem', color: 'var(--danger)' }}>Step 6: Teach the AI</h3>
                <p style={{ opacity: 0.7, fontSize: '0.9rem', marginBottom: '1.5rem' }}>Your rejection reason is saved as a lesson. The AI reads this next time it generates a draft (Step 7) to avoid making the same mistake twice.</p>
                
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Reason Tag</label>
                  <select value={rejectTag} onChange={e => setRejectTag(e.target.value)} style={{ width: '100%', padding: '0.75rem', borderRadius: '12px', border: '1px solid var(--card-border)', fontFamily: 'inherit' }}>
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
                    Feedback Note (The Lesson)
                  </label>
                  <textarea
                    rows={4}
                    required
                    value={rejectNote}
                    onChange={e => setRejectNote(e.target.value)}
                    placeholder="e.g. 'Jade is a luxury brand — never use casual language or exclamation points.'"
                    style={{ width: '100%', padding: '1rem', borderRadius: '12px', border: '1px solid var(--card-border)', fontFamily: 'inherit', outline: 'none' }}
                  />
                </div>
                <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                  <button type="button" className="btn btn-white" onClick={() => setIsRejecting(false)} style={{ border: '1px solid var(--card-border)' }}>
                    Back
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
