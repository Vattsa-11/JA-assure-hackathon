"use client";
import { useEffect, useState } from 'react';
import emailjs from '@emailjs/browser';
import { useLanguage } from '../../i18n/LanguageContext';
import T from '../../i18n/T';
import Select from '../../components/Select';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const EMAILJS_SERVICE_ID = process.env.NEXT_PUBLIC_EMAILJS_SERVICE_ID || '';
const EMAILJS_TEMPLATE_ID = process.env.NEXT_PUBLIC_EMAILJS_TEMPLATE_ID || '';
const EMAILJS_PUBLIC_KEY = process.env.NEXT_PUBLIC_EMAILJS_PUBLIC_KEY || '';
const EMAILJS_CONFIGURED =
  !!EMAILJS_SERVICE_ID &&
  !!EMAILJS_TEMPLATE_ID &&
  !!EMAILJS_PUBLIC_KEY &&
  !EMAILJS_PUBLIC_KEY.startsWith('YOUR_');

type Lead = {
  id: number;
  business_name: string;
  website?: string | null;
  email?: string | null;
  fit_score?: number | null;
  status: string;
  draft_outreach?: string | null;
  fit_reason?: string | null;
  region?: string | null;
  niche?: string | null;
};

export default function LeadsPage() {
  const { t, language } = useLanguage();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [expandedLead, setExpandedLead] = useState<number | null>(null);
  const [niche, setNiche] = useState('jewellery retailers');
  const [region, setRegion] = useState('Singapore');
  const [brandId, setBrandId] = useState('1');
  const [brands, setBrands] = useState<any[]>([]);

  // --- Send-email modal state ---
  const [mailTarget, setMailTarget] = useState<Lead | null>(null);
  const [mailForm, setMailForm] = useState({ from: '', to: '', subject: '', body: '' });
  const [mailState, setMailState] = useState<'editing' | 'sending' | 'sent' | 'error'>('editing');

  // Initialize EmailJS once (safe to call repeatedly, but guard anyway)
  useEffect(() => {
    if (EMAILJS_CONFIGURED) emailjs.init({ publicKey: EMAILJS_PUBLIC_KEY });
  }, []);

  const fetchLeads = async () => {
    setLoading(true);
    try {
      const [leadsRes, brandsRes] = await Promise.all([
        fetch(`${API_URL}/review/leads`),
        fetch(`${API_URL}/dashboard/brands`)
      ]);
      if (leadsRes.ok) setLeads(await leadsRes.json());
      if (brandsRes.ok) setBrands(await brandsRes.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchLeads(); }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    try {
      await fetch(`${API_URL}/pipeline/leads/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brand_id: parseInt(brandId), niche, region, language })
      });
      // Poll for results
      setTimeout(fetchLeads, 5000);
      setTimeout(fetchLeads, 10000);
      setTimeout(fetchLeads, 20000);
    } catch (e) {
      console.error(e);
    } finally {
      setTimeout(() => setGenerating(false), 20000);
    }
  };

  // --- Modal controls ---
  const openMailModal = (lead: Lead) => {
    setMailTarget(lead);
    setMailForm({
      from: '',
      to: lead.email || '',
      subject: `Insurance for ${lead.business_name}`,
      body: lead.draft_outreach || '',
    });
    setMailState('editing');
  };

  const closeMailModal = () => {
    setMailTarget(null);
    setMailState('editing');
  };

  // Approve button: with email -> open the send modal first; without -> approve directly
  const handleApproveClick = (lead: Lead) => {
    if (lead.email) openMailModal(lead);
    else handleApprove(lead.id);
  };

  const handleApprove = async (id: number) => {
    await fetch(`${API_URL}/review/leads/${id}/approve`, { method: 'POST' });
    fetchLeads();
  };

  const handleSendAndApprove = async () => {
    if (!mailTarget) return;
    if (!EMAILJS_CONFIGURED) { setMailState('error'); return; }
    if (!mailForm.from.trim()) { setMailState('error'); return; }
    setMailState('sending');
    try {
      // Params cover the common EmailJS template variable names —
      // map {{subject}}/{{message}}/{{from_email}}/{{to_email}} in your template.
      await emailjs.send(EMAILJS_SERVICE_ID, EMAILJS_TEMPLATE_ID, {
        from_name: 'JA Assure',
        from_email: mailForm.from,
        reply_to: mailForm.from,
        to_email: mailForm.to,
        to_name: mailTarget.business_name,
        subject: mailForm.subject,
        message: mailForm.body,
      });
      setMailState('sent');
      await fetch(`${API_URL}/review/leads/${mailTarget.id}/approve`, { method: 'POST' });
      fetchLeads();
      setTimeout(closeMailModal, 1200);
    } catch (e) {
      console.error('EmailJS send failed:', e);
      setMailState('error');
    }
  };

  const handleReject = async (id: number) => {
    await fetch(`${API_URL}/review/leads/${id}/reject`, { method: 'POST' });
    fetchLeads();
  };

  const scoreColor = (score: number) => {
    if (score >= 80) return '#10b981';
    if (score >= 60) return '#f59e0b';
    return '#ef4444';
  };

  const statusBadge = (status: string) => {
    if (status === 'approved') return { bg: '#d1fae5', color: '#065f46', label: t('leads.approvedBadge') };
    if (status === 'rejected') return { bg: '#fee2e2', color: '#991b1b', label: t('leads.rejectedBadge') };
    return { bg: '#fef3c7', color: '#92400e', label: t('leads.awaitingBadge') };
  };

  const pendingCount = leads.filter(l => l.status === 'pending_review').length;
  const approvedCount = leads.filter(l => l.status === 'approved').length;

  return (
    <div style={{ minHeight: '100vh', background: 'var(--background)', padding: '3rem' }}>
      <div style={{ maxWidth: '1100px', margin: '0 auto' }}>

        {/* Header */}
        <div style={{ marginBottom: '2.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
            <h1 style={{ margin: 0, fontSize: '2rem', fontWeight: 800 }}>{t('leads.title')}</h1>
          </div>
          <p style={{ margin: 0, opacity: 0.6 }}>{t('leads.subtitle')}</p>
        </div>

        {/* Stats Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '2.5rem' }}>
          {[
            { label: t('leads.total'), value: leads.length, color: 'var(--primary)' },
            { label: t('leads.awaiting'), value: pendingCount, color: '#f59e0b' },
            { label: t('leads.approved'), value: approvedCount, color: '#10b981' },
          ].map(s => (
            <div key={s.label} className="ui-card" style={{ padding: '1.5rem', textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: '0.85rem', opacity: 0.6, marginTop: '0.25rem' }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Generate Pipeline Card */}
        <div className="dark-card" style={{ padding: '2rem', marginBottom: '2.5rem', position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', right: '-5%', top: '-60%', width: '250px', height: '250px', background: 'rgba(255,255,255,0.08)', borderRadius: '50%' }} />
          <div style={{ position: 'relative', zIndex: 1 }}>
            <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.4rem' }}>{t('leads.findTitle')}</h2>
            <p style={{ margin: '0 0 1.5rem 0', opacity: 0.85, fontSize: '0.95rem' }}>{t('leads.findDesc')}</p>
            <form onSubmit={handleGenerate} style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
              <div style={{ flex: '1 1 150px' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.4rem', fontWeight: 600 }}>{t('leads.brand')}</label>
                <Select
                  variant="dark"
                  value={brandId}
                  onChange={setBrandId}
                  options={brands.map(b => ({ value: String(b.id), label: b.name }))}
                  style={{ background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.3)' }}
                />
              </div>
              <div style={{ flex: '1 1 200px' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.4rem', fontWeight: 600 }}>{t('leads.niche')}</label>
                <input value={niche} onChange={e => setNiche(e.target.value)} placeholder={t('leads.nichePlaceholder')} style={{ width: '100%', background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.3)', color: 'white', borderRadius: '8px', padding: '0.6rem' }} />
              </div>
              <div style={{ flex: '1 1 150px' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.4rem', fontWeight: 600 }}>{t('leads.region')}</label>
                <input value={region} onChange={e => setRegion(e.target.value)} placeholder={t('leads.regionPlaceholder')} style={{ width: '100%', background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.3)', color: 'white', borderRadius: '8px', padding: '0.6rem' }} />
              </div>
              <button type="submit" disabled={generating} className="btn" style={{ background: 'white', color: 'var(--foreground)', height: '42px', padding: '0 1.5rem', flexShrink: 0, fontWeight: 700 }}>
                {generating ? t('leads.searching') : t('leads.run')}
              </button>
            </form>
          </div>
        </div>

        {/* Leads List */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', opacity: 0.5 }}>{t('leads.loading')}</div>
        ) : leads.length === 0 ? (
          <div className="ui-card" style={{ padding: '3rem', textAlign: 'center' }}>
            <h3 style={{ margin: '0 0 0.5rem 0' }}>{t('leads.emptyTitle')}</h3>
            <p style={{ opacity: 0.6, margin: 0 }}>{t('leads.emptyDesc')}</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {leads.map(lead => {
              const badge = statusBadge(lead.status);
              const isExpanded = expandedLead === lead.id;
              return (
                <div key={lead.id} className="ui-card" style={{ padding: '1.5rem', border: lead.status === 'approved' ? '1px solid #10b981' : lead.status === 'rejected' ? '1px solid #ef4444' : '1px solid var(--border)' }}>
                  {/* Lead Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.4rem', flexWrap: 'wrap' }}>
                        <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700 }}>{lead.business_name}</h3>
                        {/* Fit Score Badge */}
                        <span style={{ background: scoreColor(lead.fit_score ?? 0), color: 'white', borderRadius: '6px', padding: '0.2rem 0.6rem', fontWeight: 700, fontSize: '0.85rem' }}>
                          {lead.fit_score ?? 'N/A'}/100
                        </span>
                        {/* Status Badge */}
                        <span style={{ background: badge.bg, color: badge.color, borderRadius: '6px', padding: '0.2rem 0.6rem', fontWeight: 600, fontSize: '0.8rem' }}>
                          {badge.label}
                        </span>
                        {/* Platform tags */}
                        <span style={{ background: '#f1f5f9', color: '#475569', borderRadius: '6px', padding: '0.2rem 0.6rem', fontSize: '0.75rem' }}>
                          <T text={lead.region || lead.niche} />
                        </span>
                      </div>
                      {lead.website && (
                        <a href={lead.website} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.82rem', color: 'var(--primary)', textDecoration: 'none' }}>
                          {lead.website}
                        </a>
                      )}
                      {lead.fit_reason && (
                        <p style={{ margin: '0.6rem 0 0 0', fontSize: '0.87rem', opacity: 0.75, lineHeight: 1.5 }}>
                          <strong>{t('leads.why')}</strong> <T text={lead.fit_reason} />
                        </p>
                      )}
                    </div>

                    {/* Actions */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flexShrink: 0 }}>
                      {lead.status === 'pending_review' && (
                        <>
                          <button onClick={() => handleApproveClick(lead)} className="btn btn-primary" style={{ fontSize: '0.85rem', padding: '0.4rem 1rem' }}>{t('leads.approve')}</button>
                          <button onClick={() => handleReject(lead.id)} className="btn btn-white" style={{ fontSize: '0.85rem', padding: '0.4rem 1rem', border: '1px solid var(--danger)', color: 'var(--danger)' }}>{t('leads.reject')}</button>
                        </>
                      )}
                      {lead.draft_outreach && (
                        <button onClick={() => setExpandedLead(isExpanded ? null : lead.id)} className="btn btn-white" style={{ fontSize: '0.82rem', padding: '0.4rem 1rem' }}>
                          {isExpanded ? t('leads.hideEmail') : t('leads.viewEmail')}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Expandable Outreach Email */}
                  {isExpanded && lead.draft_outreach && (
                    <div style={{ marginTop: '1.25rem', background: '#f8f9fc', borderRadius: '10px', padding: '1.25rem', borderLeft: '3px solid var(--primary)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', gap: '0.75rem', flexWrap: 'wrap' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--primary)' }}>{t('leads.emailTitle')}</span>
                        {lead.email ? (
                          <a href={`mailto:${lead.email}?subject=Insurance%20for%20${encodeURIComponent(lead.business_name)}&body=${encodeURIComponent(lead.draft_outreach)}`}
                            className="btn btn-primary" style={{ fontSize: '0.8rem', padding: '0.3rem 0.8rem', textDecoration: 'none' }}>
                            {t('leads.sendTo', { email: lead.email })}
                          </a>
                        ) : (
                          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                            {t('leads.noEmail')}
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                        <strong>{t('leads.recipient')}:</strong> {lead.email ?? lead.business_name}
                      </div>
                      <pre style={{ margin: 0, fontSize: '0.83rem', whiteSpace: 'pre-wrap', lineHeight: 1.7, fontFamily: 'inherit', color: '#374151' }}>
                        <T text={lead.draft_outreach} />
                      </pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Send Email + Approve Modal */}
      {mailTarget && (
        <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) closeMailModal(); }}>
          <div className="modal-content" style={{ maxWidth: '640px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.35rem' }}>{t('leads.mailModal.title')}</h2>
              <button onClick={closeMailModal} className="btn btn-white" style={{ padding: '0.2rem 0.7rem', fontSize: '1rem', lineHeight: 1.4 }} aria-label="Close">✕</button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div>
                <label className="modal-label" htmlFor="mail-from">{t('leads.mailModal.from')}</label>
                <input
                  id="mail-from"
                  type="email"
                  value={mailForm.from}
                  onChange={e => setMailForm({ ...mailForm, from: e.target.value })}
                  placeholder="you@jaassure.com"
                  style={{ width: '100%', border: '1px solid var(--border)', borderRadius: '8px', padding: '0.6rem', fontSize: '0.9rem', background: 'white', color: 'var(--foreground)' }}
                />
              </div>

              <div>
                <label className="modal-label" htmlFor="mail-to">{t('leads.mailModal.to')}</label>
                <input
                  id="mail-to"
                  type="email"
                  value={mailForm.to}
                  onChange={e => setMailForm({ ...mailForm, to: e.target.value })}
                  style={{ width: '100%', border: '1px solid var(--border)', borderRadius: '8px', padding: '0.6rem', fontSize: '0.9rem', background: '#f8f9fc', color: 'var(--foreground)' }}
                />
              </div>

              <div>
                <label className="modal-label" htmlFor="mail-subject">{t('leads.mailModal.subject')}</label>
                <input
                  id="mail-subject"
                  value={mailForm.subject}
                  onChange={e => setMailForm({ ...mailForm, subject: e.target.value })}
                  style={{ width: '100%', border: '1px solid var(--border)', borderRadius: '8px', padding: '0.6rem', fontSize: '0.9rem', background: 'white', color: 'var(--foreground)' }}
                />
              </div>

              <div>
                <label className="modal-label" htmlFor="mail-body">{t('leads.mailModal.body')}</label>
                <textarea
                  id="mail-body"
                  value={mailForm.body}
                  onChange={e => setMailForm({ ...mailForm, body: e.target.value })}
                  rows={10}
                  style={{ width: '100%', border: '1px solid var(--border)', borderRadius: '8px', padding: '0.6rem', fontSize: '0.87rem', lineHeight: 1.6, resize: 'vertical', fontFamily: 'inherit', background: 'white', color: 'var(--foreground)' }}
                />
              </div>

              {mailState === 'error' && (
                <div style={{ background: '#fee2e2', border: '1px solid #ef4444', color: '#991b1b', borderRadius: '8px', padding: '0.65rem 1rem', fontSize: '0.85rem' }}>
                  {!EMAILJS_CONFIGURED ? t('leads.mailModal.notConfigured') : mailForm.from.trim() ? t('leads.mailModal.failed') : t('leads.mailModal.sendFirst')}
                </div>
              )}

              <div className="modal-actions" style={{ marginTop: '0.25rem' }}>
                <button onClick={closeMailModal} className="btn" style={{ background: 'white', color: 'var(--foreground)', border: '1px solid var(--border)' }}>
                  {t('dash.modal.cancel')}
                </button>
                <button
                  onClick={handleApprove.bind(null, mailTarget.id)}
                  className="btn"
                  style={{ background: 'white', color: 'var(--foreground)', border: '1px solid var(--border)' }}
                >
                  {t('dash.modal.approveAsIs')}
                </button>
                <button
                  onClick={handleSendAndApprove}
                  disabled={mailState === 'sending' || mailState === 'sent'}
                  className="btn btn-success"
                >
                  {mailState === 'sending' ? t('leads.mailModal.sending') : mailState === 'sent' ? t('leads.mailModal.sent') : t('leads.mailModal.send')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
