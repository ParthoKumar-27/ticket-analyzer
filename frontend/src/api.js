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

// QueueStorm /sort-ticket helper. Sends a single CRM ticket to the
// rule-based classifier and returns the structured response.
export async function sortTicket(payload) {
  const res = await fetch(`${API_BASE_URL}/sort-ticket`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error('Failed to sort ticket')
  return res.json()
}