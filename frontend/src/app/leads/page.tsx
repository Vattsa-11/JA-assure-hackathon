"use client";
import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function LeadsPage() {
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLeads = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/review/leads`);
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      setLeads(data);
    } catch (e: any) {
      setError(e.message || 'Failed to load leads.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchLeads(); }, []);

  const scoreColor = (score: number) => {
    if (score >= 70) return 'var(--success)';
    if (score >= 40) return 'var(--warning)';
    return 'var(--danger)';
  };

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '50vh' }}>
      <p style={{ opacity: 0.7 }}>Loading leads...</p>
    </div>
  );

  if (error) return (
    <div className="glass-panel" style={{ padding: '2rem', border: '1px solid var(--danger)' }}>
      <h3 style={{ color: 'var(--danger)' }}>Error</h3>
      <p>{error}</p>
      <button className="btn btn-primary" onClick={fetchLeads}>Retry</button>
    </div>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <h1>Generated Leads</h1>
          <p style={{ opacity: 0.7, margin: 0 }}>Real businesses discovered via OpenStreetMap, scored and enriched with personalized outreach drafts.</p>
        </div>
        <button className="btn btn-primary" onClick={fetchLeads}>↻ Refresh</button>
      </div>

      {leads.length === 0 ? (
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🔍</div>
          <h3>No leads yet</h3>
          <p style={{ opacity: 0.7 }}>Run the Lead Generation pipeline to discover real businesses via OpenStreetMap.</p>
        </div>
      ) : (
        <div className="grid">
          {leads.map(lead => (
            <div key={lead.id} className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
              <div className="card-content" style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{lead.business_name}</h3>
                  <div style={{
                    background: scoreColor(lead.fit_score ?? 0),
                    color: 'white',
                    padding: '0.25rem 0.6rem',
                    borderRadius: '8px',
                    fontWeight: 'bold',
                    fontSize: '0.875rem',
                    flexShrink: 0,
                    marginLeft: '0.5rem'
                  }}>
                    {lead.fit_score ?? 'N/A'}/100
                  </div>
                </div>

                {lead.website && (
                  <a href={lead.website} target="_blank" rel="noopener noreferrer"
                    style={{ fontSize: '0.8rem', color: 'var(--primary)', opacity: 0.8 }}>
                    {lead.website}
                  </a>
                )}

                {lead.fit_reason && (
                  <p style={{ fontSize: '0.85rem', opacity: 0.75, marginTop: '0.75rem', marginBottom: '0.75rem', lineHeight: 1.5 }}>
                    <strong>Why:</strong> {lead.fit_reason}
                  </p>
                )}

                {lead.draft_outreach && (
                  <div style={{ background: 'rgba(0,0,0,0.25)', padding: '1rem', borderRadius: '8px', fontSize: '0.8rem', whiteSpace: 'pre-wrap', lineHeight: 1.6, fontFamily: 'monospace' }}>
                    {lead.draft_outreach}
                  </div>
                )}
              </div>

              {lead.email && (
                <div className="card-actions">
                  <a href={`mailto:${lead.email}`} className="btn btn-primary" style={{ textDecoration: 'none', display: 'inline-block' }}>
                    ✉ Send to {lead.email}
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
