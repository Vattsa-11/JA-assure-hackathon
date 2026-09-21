import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Link from 'next/link'
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
        <nav style={{ background: 'var(--sidebar-bg)', padding: '1rem 2rem', display: 'flex', gap: '2rem', alignItems: 'center' }}>
          <div style={{ fontWeight: 800, fontSize: '1.2rem', color: 'white' }}>JA Assure</div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Link href="/" className="nav-link">Dashboard</Link>
            <Link href="/leads" className="nav-link">Leads Intelligence</Link>
            <Link href="/metrics" className="nav-link">Metrics</Link>
            <Link href="/queue" className="nav-link">Review Queue</Link>
          </div>
        </nav>
        {children}
      </body>
    </html>
  )
}
