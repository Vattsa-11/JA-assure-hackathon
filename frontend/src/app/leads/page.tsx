"use client";
import { useEffect, useState } from 'react';

export default function LeadsPage() {
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/review/leads')
      .then(res => res.json())
      .then(data => {
        setLeads(data);
        setLoading(false);
      })
      .catch(console.error);
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Generated Leads</h1>
      <p style={{ opacity: 0.7, marginBottom: '2rem' }}>Qualified leads matching your criteria, complete with drafted outreach.</p>
      
      {leads.length === 0 ? (
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
          <h3>No leads yet</h3>
          <p style={{ opacity: 0.7 }}>Run the Lead Generation pipeline to populate this list.</p>
        </div>
      ) : (
        <div className="grid">
          {leads.map(lead => (
            <div key={lead.id} className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
              <div className="card-content" style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h3 style={{ margin: 0 }}>{lead.business_name}</h3>
                  <div style={{ 
                    background: lead.fit_score > 70 ? 'var(--success)' : 'var(--warning)', 
                    color: 'white', 
                    padding: '0.25rem 0.5rem', 
                    borderRadius: '8px',
                    fontWeight: 'bold',
                    fontSize: '0.875rem'
                  }}>
                    Score: {lead.fit_score}
                  </div>
                </div>
                
                <p style={{ fontSize: '0.875rem', opacity: 0.8, marginBottom: '1rem' }}>
                  <strong>Why:</strong> {lead.fit_reason}
                </p>
                
                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', fontSize: '0.875rem', whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                  {lead.draft_outreach}
                </div>
              </div>
              <div className="card-actions">
                <button className="btn btn-primary" onClick={() => window.open(`mailto:${lead.email}`)}>Send Email</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
