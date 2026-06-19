import { useEffect, useState } from 'react'
import { createTicket, listTickets } from './api'

export default function App() {
  const [title, setTitle] = useState('')
  const [message, setMessage] = useState('')
  const [category, setCategory] = useState('')
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function refresh() {
    try {
      const data = await listTickets()
      setTickets(data)
    } catch {
      setError('Could not load tickets.')
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await createTicket({ title, message, category: category || null })
      setTitle('')
      setMessage('')
      setCategory('')
      await refresh()
    } catch {
      setError('Could not submit ticket.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 640, margin: '40px auto', fontFamily: 'sans-serif' }}>
      <h1>Ticket Analyzer</h1>

      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 8, marginBottom: 32 }}>
        <input
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
        <textarea
          placeholder="Message"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          required
          rows={4}
        />
        <input
          placeholder="Category (optional)"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Analyzing…' : 'Submit Ticket'}
        </button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </form>

      <h2>Tickets</h2>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {tickets.map((t) => (
          <li key={t.id} style={{ border: '1px solid #ddd', borderRadius: 6, padding: 12, marginBottom: 8 }}>
            <strong>{t.title}</strong>
            <div>
              Sentiment: <b>{t.sentiment}</b> ({(t.confidence * 100).toFixed(1)}%)
            </div>
            <small>{new Date(t.created_at).toLocaleString()}</small>
          </li>
        ))}
      </ul>
    </div>
  )
}