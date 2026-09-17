"use client";
import { useEffect, useState } from 'react';

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    fetch('http://localhost:8000/review/metrics')
      .then(res => res.json())
      .then(data => setMetrics(data))
      .catch(console.error);
  }, []);

  if (!metrics) return <div>Loading...</div>;

  return (
    <div>
      <h1>Performance Metrics</h1>
      <p style={{ opacity: 0.7, marginBottom: '2rem' }}>Insights into the AI Agent's learning and compliance rates.</p>
      
      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))' }}>
        <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center' }}>
          <h3 style={{ opacity: 0.7, fontSize: '1rem' }}>Rejection Rate</h3>
          <div style={{ fontSize: '3rem', fontWeight: 'bold', color: 'var(--primary)', margin: '1rem 0' }}>
            {metrics.rejection_rate.toFixed(1)}%
          </div>
          <p style={{ fontSize: '0.875rem', opacity: 0.7, margin: 0 }}>Assets that required human correction</p>
        </div>
        
        <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center' }}>
          <h3 style={{ opacity: 0.7, fontSize: '1rem' }}>Edit Intensity</h3>
          <div style={{ fontSize: '3rem', fontWeight: 'bold', color: 'var(--success)', margin: '1rem 0' }}>
            {metrics.edit_intensity.toFixed(1)}
          </div>
          <p style={{ fontSize: '0.875rem', opacity: 0.7, margin: 0 }}>Average revisions per asset</p>
        </div>
      </div>
    </div>
  );
}
