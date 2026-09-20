import type { Metadata } from 'next'
import Link from 'next/link'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'JA Assure Dashboard',
  description: 'AI Marketing Agent Dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className} style={{ margin: 0, background: 'var(--background)' }}>
        <nav style={{ background: 'white', padding: '1rem 2rem', borderBottom: '1px solid var(--card-border)', display: 'flex', gap: '2rem', alignItems: 'center' }}>
          <div style={{ fontWeight: 800, fontSize: '1.2rem', color: 'var(--primary)' }}>JA Assure</div>
          <div style={{ display: 'flex', gap: '1.5rem' }}>
            <Link href="/" style={{ textDecoration: 'none', color: '#475569', fontWeight: 600 }}>Dashboard</Link>
            <Link href="/leads" style={{ textDecoration: 'none', color: '#475569', fontWeight: 600 }}>Leads Intelligence</Link>
            <Link href="/metrics" style={{ textDecoration: 'none', color: '#475569', fontWeight: 600 }}>Metrics</Link>
            <Link href="/queue" style={{ textDecoration: 'none', color: '#475569', fontWeight: 600 }}>Review Queue</Link>
          </div>
        </nav>
        {children}
      </body>
    </html>
  )
}
