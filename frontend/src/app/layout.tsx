import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Link from 'next/link'

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
      <body className={inter.className}>
        <nav className="navbar glass-panel" style={{ borderRadius: 0, borderTop: 'none', borderLeft: 'none', borderRight: 'none' }}>
          <h2 style={{ margin: 0, marginRight: '2rem' }}>JA Assure AI</h2>
          <Link href="/queue">Approval Queue</Link>
          <Link href="/metrics">Metrics</Link>
          <Link href="/leads">Leads</Link>
        </nav>
        <main className="container">
          {children}
        </main>
      </body>
    </html>
  )
}
