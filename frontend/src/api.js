// '/api' is the default and matches the Nginx reverse-proxy setup, so this
// works unmodified on both localhost and the deployed VM.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

export async function getHealth() {
  const res = await fetch(`${API_BASE_URL}/health`)
  return res.json()
}

export async function createTicket(ticket) {
  const res = await fetch(`${API_BASE_URL}/tickets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(ticket),
  })
  if (!res.ok) throw new Error('Failed to create ticket')
  return res.json()
}

export async function listTickets() {
  const res = await fetch(`${API_BASE_URL}/tickets`)
  return res.json()
}