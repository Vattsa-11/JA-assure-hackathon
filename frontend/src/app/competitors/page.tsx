"use client";
import { useCallback, useEffect, useState } from 'react';
import { useLanguage } from '../../i18n/LanguageContext';
import T from '../../i18n/T';
import { API_URL } from '../../i18n/apiUrl';

type ScanResult = { url: string; status: string; note: string };
type Digest = { id: number; competitor_url: string; suggested_action: string; updated_at: string };
type Tracked = { id: number; competitor_url: string; name: string | null; source: string; status: string };
type Suggestion = { name: string; url: string; why: string };
type ResearchResult = {
  researched: { name: string; url: string; summary: string }[];
  errors: { url: string; note: string }[];
};

export default function CompetitorsPage() {
  const { t } = useLanguage();
  const [digests, setDigests] = useState<Digest[]>([]);
  const [tracked, setTracked] = useState<Tracked[]>([]);
  const [newUrl, setNewUrl] = useState('');
  const [scanning, setScanning] = useState(false);
  const [scanReport, setScanReport] = useState<ScanResult[] | null>(null);
  const [adding, setAdding] = useState(false);

  const [suggestions, setSuggestions] = useState<Suggestion[] | null>(null);
  const [discovering, setDiscovering] = useState(false);
  const [addedUrls, setAddedUrls] = useState<Set<string>>(new Set());

  const [research, setResearch] = useState<ResearchResult | null>(null);
  const [researching, setResearching] = useState(false);

  const fetchDigests = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/dashboard/competitors`);
      if (res.ok) setDigests(await res.json());
    } catch (e) {
      console.error(e);
    }
  }, []);

  const fetchTracked = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/dashboard/competitors/tracked`);
      if (res.ok) setTracked(await res.json());
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    fetchDigests();
    fetchTracked();
  }, [fetchDigests, fetchTracked]);

  const handleAddUrl = async (e: React.FormEvent) => {
    e.preventDefault();
    const url = newUrl.trim();
    if (!url) return;
    setAdding(true);
    try {
      await fetch(`${API_URL}/dashboard/competitors/tracked`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      setNewUrl('');
      await fetchTracked();
    } catch (err) {
      console.error(err);
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (id: number) => {
    try {
      await fetch(`${API_URL}/dashboard/competitors/tracked/${id}`, { method: 'DELETE' });
      await fetchTracked();
    } catch (e) {
      console.error(e);
    }
  };

  const handleScan = async () => {
    setScanning(true);
    setScanReport(null);
    try {
      const res = await fetch(`${API_URL}/dashboard/competitors/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (res.ok) {
        const data = await res.json();
        setScanReport(data.results ?? []);
        await fetchDigests();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setScanning(false);
    }
  };

  const handleDiscover = async () => {
    setDiscovering(true);
    setSuggestions(null);
    try {
      const res = await fetch(`${API_URL}/dashboard/competitors/discover`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data.competitors ?? []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setDiscovering(false);
    }
  };

  const handleResearch = async () => {
    setResearching(true);
    setResearch(null);
    try {
      const res = await fetch(`${API_URL}/dashboard/competitors/research-new`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setResearch({ researched: data.researched ?? [], errors: data.errors ?? [] });
        await fetchDigests();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setResearching(false);
    }
  };

  const trackSuggestion = async (s: Suggestion) => {
    setAddedUrls((prev) => new Set(prev).add(s.url));
    try {
      await fetch(`${API_URL}/dashboard/competitors/tracked`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: s.url, name: s.name, source: 'ai' }),
      });
      await fetchTracked();
    } catch (e) {
      console.error(e);
    }
  };

  const trackResearch = async (r: { name: string; url: string }) => {
    setAddedUrls((prev) => new Set(prev).add(r.url));
    try {
      await fetch(`${API_URL}/dashboard/competitors/tracked`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: r.url, name: r.name, source: 'ai' }),
      });
      await fetchTracked();
    } catch (e) {
      console.error(e);
    }
  };

  const sourceLabel = (source: string) =>
    source === 'major'
      ? t('comp.sourceMajor')
      : source === 'ai'
        ? t('comp.sourceAi')
        : t('comp.sourceManual');

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>{t('comp.title')}</h1>
          <p className="page-subtitle">{t('comp.desc')}</p>
        </div>
      </div>

      {/* Watchlist */}
      <div
        className="dark-card"
        style={{ padding: '2rem', marginBottom: '2.5rem', position: 'relative', overflow: 'hidden' }}
      >
        <div style={{ position: 'absolute', right: '-5%', top: '-60%', width: '250px', height: '250px', background: 'rgba(255,255,255,0.08)', borderRadius: '50%' }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
            <h2 style={{ margin: 0, fontSize: '1.4rem' }}>{t('comp.watchlist')}</h2>
            <span className="tag" style={{ background: 'rgba(255,255,255,0.12)', color: 'white' }}>
              {tracked.length} {t('comp.tracked')}
            </span>
          </div>

          <form onSubmit={handleAddUrl} style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end', marginTop: '1.25rem' }}>
            <div style={{ flex: '3 1 320px' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.4rem', fontWeight: 600 }}>{t('comp.urlsLabel')}</label>
              <input
                value={newUrl}
                onChange={(e) => setNewUrl(e.target.value)}
                placeholder="https://competitor-one.com"
                style={{ width: '100%', background: '#000', border: '1px solid rgba(255,255,255,0.3)', color: 'white', borderRadius: '8px', padding: '0.6rem' }}
              />
            </div>
            <button type="submit" disabled={adding || !newUrl.trim()} className="btn" style={{ background: 'white', color: 'var(--foreground)', height: '42px', padding: '0 1.25rem', flexShrink: 0, fontWeight: 700 }}>
              + {t('comp.addTracked')}
            </button>
            <button type="button" onClick={handleScan} disabled={scanning || tracked.length === 0} className="btn" style={{ background: 'white', color: 'var(--foreground)', height: '42px', padding: '0 1.25rem', flexShrink: 0, fontWeight: 700 }}>
              {scanning ? t('comp.scanning') : t('comp.scan')}
            </button>
          </form>

          <div style={{ marginTop: '0.6rem', fontSize: '0.78rem', opacity: 0.55 }}>{t('comp.autoScanOn')}</div>

          {scanReport && (
            <div style={{ marginTop: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {scanReport.map((r) => (
                <div key={r.url} style={{ display: 'flex', gap: '0.75rem', alignItems: 'baseline', fontSize: '0.85rem', color: 'rgba(255,255,255,0.9)', flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 700 }}>{r.url}</span>
                  <span
                    style={{
                      padding: '0.15rem 0.6rem',
                      borderRadius: '50px',
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      background:
                        r.status === 'digested'
                          ? 'rgba(16,185,129,0.25)'
                          : r.status === 'unchanged'
                            ? 'rgba(90,82,255,0.25)'
                            : 'rgba(255,101,117,0.25)',
                      color: 'white',
                    }}
                  >
                    {r.status === 'digested'
                      ? t('comp.statusDigested')
                      : r.status === 'unchanged'
                        ? t('comp.statusUnchanged')
                        : t('comp.statusUnreachable')}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Watchlist rows */}
          <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            {tracked.map((item) => (
              <div key={item.id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.6rem 0.9rem', background: 'rgba(255,255,255,0.06)', borderRadius: '10px', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'white' }}>{item.name || item.competitor_url}</span>
                <span style={{ fontSize: '0.75rem', opacity: 0.6 }}>{item.competitor_url}</span>
                <span style={{ padding: '0.1rem 0.55rem', borderRadius: '50px', fontSize: '0.68rem', fontWeight: 700, background: 'rgba(255,255,255,0.12)', color: 'white' }}>
                  {sourceLabel(item.source)}
                </span>
                {item.status === 'unreachable' && (
                  <span style={{ padding: '0.1rem 0.55rem', borderRadius: '50px', fontSize: '0.68rem', fontWeight: 700, background: 'rgba(255,101,117,0.3)', color: 'white' }}>
                    {t('comp.statusUnreachable')}
                  </span>
                )}
                <button
                  onClick={() => handleRemove(item.id)}
                  style={{ marginLeft: 'auto', background: 'transparent', border: 'none', color: 'rgba(255,255,255,0.5)', cursor: 'pointer', fontSize: '0.8rem' }}
                  title={t('comp.remove')}
                >
                  × {t('comp.remove')}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI research tools */}
      <div className="page-header" style={{ marginBottom: '1rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.3rem' }}>{t('comp.researchResults')}</h2>
          <p className="page-subtitle" style={{ fontSize: '0.88rem' }}>{t('comp.researchDesc')}</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={handleResearch} disabled={researching}>
            {researching ? t('comp.researching') : t('comp.research')}
          </button>
          <button className="btn" onClick={handleDiscover} disabled={discovering} style={{ background: 'var(--foreground)', color: 'white' }}>
            {discovering ? t('comp.discovering') : t('comp.discover')}
          </button>
        </div>
      </div>

      {/* New-competitor research results */}
      {research && research.researched.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
          {research.researched.map((r) => {
            const isTracked = tracked.some((tr) => tr.competitor_url === r.url);
            const added = isTracked || addedUrls.has(r.url);
            return (
              <div key={r.url} className="ui-card" style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>                    <a href={r.url} target="_blank" rel="noopener noreferrer" style={{ fontWeight: 700, color: 'var(--primary)', textDecoration: 'none' }}>
                      {r.name} — <T text={r.url} />
                    </a>
                  <button
                    className="btn"
                    disabled={added}
                    onClick={() => trackResearch(r)}
                    style={{
                      fontSize: '0.82rem', padding: '0.4rem 1rem', flexShrink: 0,
                      background: added ? 'var(--pastel-green)' : 'var(--foreground)',
                      color: added ? 'var(--foreground)' : 'white',
                    }}
                  >
                    {added ? t('comp.added') : t('comp.addTracked')}
                  </button>
                </div>
                <p style={{ margin: '0.75rem 0 0', fontSize: '0.92rem', lineHeight: 1.65 }}>
                  <T text={r.summary} />
                </p>
              </div>
            );
          })}
        </div>
      )}
      {research && research.errors.length > 0 && (
        <div className="ui-card" style={{ padding: '1rem 1.5rem', marginBottom: '2rem' }}>
          <div style={{ fontWeight: 700, fontSize: '0.85rem', marginBottom: '0.5rem' }}>{t('comp.skipped')}</div>
          {research.errors.map((e, i) => (
            <div key={`${e.url}-${i}`} style={{ fontSize: '0.8rem', opacity: 0.65 }}>
              {e.url} — {e.note}
            </div>
          ))}
        </div>
      )}

      {/* AI discovery suggestions */}
      {suggestions && suggestions.length > 0 && (
        <div className="ui-card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
          <h3 style={{ margin: '0 0 1rem' }}>{t('comp.discoverDesc')}</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {suggestions.map((s) => {
              const isTracked = tracked.some((tr) => tr.competitor_url === s.url);
              const added = isTracked || addedUrls.has(s.url);
              return (
                <div key={s.url} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem 1rem', background: 'var(--background)', borderRadius: '12px', flexWrap: 'wrap' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 700 }}>{s.name}</div>
                    <a href={s.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.82rem', color: 'var(--primary)', textDecoration: 'none' }}>
                      {s.url}
                    </a>
                    <div style={{ fontSize: '0.82rem', opacity: 0.65, marginTop: '0.25rem' }}>{s.why}</div>
                  </div>
                  <button
                    className="btn"
                    disabled={added}
                    onClick={() => trackSuggestion(s)}
                    style={{
                      fontSize: '0.82rem', padding: '0.4rem 1rem', flexShrink: 0,
                      background: added ? 'var(--pastel-green)' : 'var(--foreground)',
                      color: added ? 'var(--foreground)' : 'white',
                    }}
                  >
                    {added ? t('comp.added') : t('comp.addTracked')}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Latest analysis */}
      <h2 style={{ margin: '0 0 1rem', fontSize: '1.3rem' }}>{t('comp.results')}</h2>
      {digests.length === 0 ? (
        <div className="ui-card" style={{ padding: '3rem', textAlign: 'center' }}>
          <h3 style={{ margin: '0 0 0.5rem 0' }}>{t('comp.noneYet')}</h3>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {digests.map((c) => (
            <div key={c.id} className="ui-card" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                <a href={c.competitor_url} target="_blank" rel="noopener noreferrer" style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--primary)', textDecoration: 'none' }}>
                  <T text={c.competitor_url} />
                </a>
                <span style={{ fontSize: '0.75rem', opacity: 0.5 }}>{new Date(c.updated_at).toLocaleString()}</span>
              </div>
              <p style={{ margin: '0.75rem 0 0', fontSize: '0.92rem', lineHeight: 1.65 }}>
                <T text={c.suggested_action} />
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
