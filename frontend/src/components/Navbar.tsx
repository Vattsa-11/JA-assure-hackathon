'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useLanguage } from '../i18n/LanguageContext';
import type { TranslationKey } from '../i18n/translations';
import LanguageSwitcher from './LanguageSwitcher';

const LINKS: { href: string; key: TranslationKey }[] = [
  { href: '/', key: 'nav.dashboard' },
  { href: '/leads', key: 'nav.leads' },
  { href: '/competitors', key: 'nav.competitors' },
  { href: '/metrics', key: 'nav.metrics' },
  { href: '/queue', key: 'nav.queue' },
];

export default function Navbar() {
  const pathname = usePathname();
  const { t } = useLanguage();

  return (
    <nav className="app-nav">
      <Link href="/" className="nav-logo">JA Assure</Link>
      <div className="nav-links">
        {LINKS.map(link => (
          <Link
            key={link.href}
            href={link.href}
            className={`nav-link${pathname === link.href ? ' nav-link-active' : ''}`}
          >
            {t(link.key)}
          </Link>
        ))}
      </div>
      <LanguageSwitcher />
    </nav>
  );
}
