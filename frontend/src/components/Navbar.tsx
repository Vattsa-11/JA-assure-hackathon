'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const LINKS = [
  { href: '/', label: 'Dashboard' },
  { href: '/leads', label: 'Leads Intelligence' },
  { href: '/metrics', label: 'Metrics' },
  { href: '/queue', label: 'Review Queue' },
];

export default function Navbar() {
  const pathname = usePathname();

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
            {link.label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
