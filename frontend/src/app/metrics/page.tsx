"use client";
import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Shape of GET /review/metrics.
interface Metrics {
  rejection_rate: number;
  edit_intensity: number;
}

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
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
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load metrics.');
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
    <div className="glass-panel" style={{ padding: '2rem', border: '1px solid var(--danger)' }}>
      <h3 style={{ color: 'var(--danger)' }}>Error</h3>
      <p>{error}</p>
      <button className="btn btn-primary" onClick={fetchMetrics}>Retry</button>
    </div>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <h1>Performance Metrics</h1>
          <p style={{ opacity: 0.7, margin: 0 }}>Live insights into agent learning and compliance rates.</p>
        </div>
        <button className="btn btn-primary" onClick={fetchMetrics}>↻ Refresh</button>
      </div>

      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
        <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '0.875rem', opacity: 0.6, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '1rem' }}>
            Rejection Rate
          </div>
          <div style={{ fontSize: '3.5rem', fontWeight: 'bold', color: 'var(--primary)', lineHeight: 1 }}>
            {metrics?.rejection_rate?.toFixed(1)}%
          </div>
          <p style={{ fontSize: '0.875rem', opacity: 0.6, marginTop: '1rem', marginBottom: 0 }}>
            Assets that required human correction
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '0.875rem', opacity: 0.6, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '1rem' }}>
            Edit Intensity
          </div>
          <div style={{ fontSize: '3.5rem', fontWeight: 'bold', color: 'var(--success)', lineHeight: 1 }}>
            {metrics?.edit_intensity?.toFixed(2)}
          </div>
          <p style={{ fontSize: '0.875rem', opacity: 0.6, marginTop: '1rem', marginBottom: 0 }}>
            Avg content versions per asset (&gt;1.0 = edits required)
          </p>
        </div>
      </div>

      <div className="glass-panel" style={{ marginTop: '2rem', padding: '2rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>How the Feedback Loop Works</h3>
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
