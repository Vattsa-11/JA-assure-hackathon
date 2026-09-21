"use client";
import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/review/metrics`);
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      setMetrics(data);
    } catch (e: any) {
      setError(e.message || 'Failed to load metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchMetrics(); }, []);

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '50vh' }}>
      <p style={{ opacity: 0.7 }}>Loading metrics...</p>
    </div>
  );

  if (error) return (
    <div className="page-container">
      <div className="glass-panel" style={{ padding: '2rem', border: '1px solid rgba(255,101,117,0.4)' }}>
        <h3 style={{ color: 'var(--danger)', marginTop: 0 }}>Error</h3>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={fetchMetrics}>Retry</button>
      </div>
    </div>
  );

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Performance Metrics</h1>
          <p className="page-subtitle">Live insights into agent learning and compliance rates.</p>
        </div>
        <button className="btn btn-primary" onClick={fetchMetrics}>↻ Refresh</button>
      </div>

      <div className="grid">
        <div className="glass-panel kpi-card">
          <div className="kpi-accent-bar kpi-accent-purple" />
          <div className="kpi-label">Rejection Rate</div>
          <div className="kpi-value kpi-value-purple">
            {metrics?.rejection_rate?.toFixed(1)}%
          </div>
          <p className="kpi-hint">
            Assets that required human correction
          </p>
        </div>

        <div className="glass-panel kpi-card">
          <div className="kpi-accent-bar kpi-accent-green" />
          <div className="kpi-label">Edit Intensity</div>
          <div className="kpi-value kpi-value-green">
            {metrics?.edit_intensity?.toFixed(2)}
          </div>
          <p className="kpi-hint">
            Avg content versions per asset (&gt;1.0 = edits required)
          </p>
        </div>
      </div>

      <div className="glass-panel" style={{ marginTop: '2rem', padding: '2rem' }}>
        <h3 style={{ marginTop: 0, marginBottom: '1rem' }}>How the Feedback Loop Works</h3>
        <p style={{ opacity: 0.7, lineHeight: 1.7, margin: 0 }}>
          Every time you <strong>reject</strong> an asset and write a feedback note, that lesson is stored in the database 
          and automatically injected into the AI agent&apos;s context the next time it generates content for that brand. 
          The <strong>rejection rate</strong> should trend downward over time as the agent learns your brand&apos;s standards.
          The <strong>edit intensity</strong> tracks how many revisions an asset needs — lower is better.
        </p>
      </div>
    </div>
  );
}
