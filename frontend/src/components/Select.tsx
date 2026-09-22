'use client';

import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

export type SelectOption = { value: string; label: string };

type SelectProps = {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  /** dark = for .dark-card / black inputs; light = for white cards */
  variant?: 'dark' | 'light';
  required?: boolean;
  style?: React.CSSProperties;
};

/**
 * Themed dropdown replacing native <select> — the OS popup (black box +
 * system-blue highlight) clashes with the app theme.
 *
 * The options panel renders in a portal on document.body with fixed
 * positioning, so ancestor `overflow: hidden` (e.g. .dark-card) can never
 * clip it, and modal z-indexes can't bury it.
 */
export default function Select({ value, onChange, options, variant = 'light', required, style }: SelectProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const [rect, setRect] = useState<{ left: number; top: number; width: number } | null>(null);

  const selected = options.find((o) => o.value === value);
  const isDark = variant === 'dark';

  const positionPanel = () => {
    const el = triggerRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    setRect({ left: r.left, top: r.bottom + 6, width: r.width });
  };

  // Measure when opening
  useLayoutEffect(() => {
    if (open) positionPanel();
  }, [open]);

  // Reposition on scroll/resize while open; close on Escape / outside pointer
  useEffect(() => {
    if (!open) return;
    const onScroll = () => positionPanel();
    const onResize = () => positionPanel();
    const onDocPointer = (e: PointerEvent) => {
      const t = e.target as Node;
      // Ignore presses inside the trigger/root and inside the portaled panel —
      // otherwise the panel unmounts before the option's click fires.
      if (rootRef.current?.contains(t)) return;
      if (panelRef.current?.contains(t)) return;
      setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    window.addEventListener('scroll', onScroll, true);
    window.addEventListener('resize', onResize);
    document.addEventListener('pointerdown', onDocPointer, true);
    document.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('scroll', onScroll, true);
      window.removeEventListener('resize', onResize);
      document.removeEventListener('pointerdown', onDocPointer, true);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const trigger: React.CSSProperties = {
    width: '100%',
    textAlign: 'left',
    fontFamily: 'inherit',
    fontSize: 'inherit',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '0.5rem',
    padding: isDark ? '0.75rem 1rem' : '0.6rem 0.9rem',
    borderRadius: '8px',
    ...(isDark
      ? { background: '#000', border: '1px solid rgba(255,255,255,0.2)', color: 'white' }
      : { background: '#fff', border: '1px solid var(--border)', color: 'var(--foreground)' }),
    ...style,
  };

  const panelStyle: React.CSSProperties = {
    position: 'fixed',
    left: rect?.left ?? 0,
    top: rect?.top ?? 0,
    width: rect?.width ?? 'auto',
    zIndex: 9999,
    overflow: 'hidden',
    borderRadius: '10px',
    boxShadow: '0 12px 30px rgba(0,0,0,0.25)',
    maxHeight: '280px',
    overflowY: 'auto',
    ...(isDark
      ? { background: '#111', border: '1px solid rgba(255,255,255,0.18)' }
      : { background: '#fff', border: '1px solid var(--border)' }),
  };

  return (
    <div ref={rootRef} style={{ position: 'relative', width: '100%' }}>
      <button
        ref={triggerRef}
        type="button"
        style={trigger}
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-required={required}
      >
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {selected ? selected.label : '\u00A0'}
        </span>
        <span
          aria-hidden="true"
          style={{
            width: 0,
            height: 0,
            borderLeft: '4px solid transparent',
            borderRight: '4px solid transparent',
            borderTop: isDark ? '5px solid rgba(255,255,255,0.6)' : '5px solid rgba(45,52,54,0.6)',
            flexShrink: 0,
            marginTop: 2,
          }}
        />
      </button>

      {open && rect &&
        createPortal(
          <div ref={panelRef} style={panelStyle} role="listbox">
            {options.map((o) => {
              const active = o.value === value;
              return (
                <div
                  key={o.value}
                  role="option"
                  aria-selected={active}
                  onClick={() => {
                    onChange(o.value);
                    setOpen(false);
                  }}
                  style={{
                    padding: isDark ? '0.65rem 1rem' : '0.55rem 0.9rem',
                    cursor: 'pointer',
                    fontSize: '0.95em',
                    fontWeight: active ? 700 : 400,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    background: active ? (isDark ? 'var(--primary)' : 'var(--pastel-blue)') : 'transparent',
                    ...(active
                      ? isDark
                        ? { color: 'white' }
                        : { color: 'var(--foreground)' }
                      : isDark
                        ? { color: 'rgba(255,255,255,0.85)' }
                        : { color: 'var(--foreground)' }),
                  }}
                  onMouseEnter={(e) => {
                    if (!active) e.currentTarget.style.background = isDark ? 'rgba(255,255,255,0.08)' : 'var(--pastel-blue)';
                  }}
                  onMouseLeave={(e) => {
                    if (!active) e.currentTarget.style.background = 'transparent';
                  }}
                >
                  {o.label}
                </div>
              );
            })}
          </div>,
          document.body,
        )}
    </div>
  );
}
