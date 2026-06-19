import { useEffect, useState } from "react";
import { createTicket, listTickets } from "./api";
import "./styles.css";

export default function App() {
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [category, setCategory] = useState("");

  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function refresh() {
    try {
      const data = await listTickets();
      setTickets(data);
    } catch {
      setError("Could not load tickets");
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();

    setLoading(true);
    setError("");

    try {
      await createTicket({
        title,
        message,
        category: category || null,
      });

      setTitle("");
      setMessage("");
      setCategory("");

      await refresh();
    } catch {
      setError("Could not submit ticket");
    } finally {
      setLoading(false);
    }
  }

  const positives = tickets.filter(
    (t) => t.sentiment?.toLowerCase() === "positive"
  ).length;

  const negatives = tickets.filter(
    (t) => t.sentiment?.toLowerCase() === "negative"
  ).length;

  const neutrals = tickets.filter(
    (t) => t.sentiment?.toLowerCase() === "neutral"
  ).length;

  return (
    <div className="container">
      <div className="header">
        <h1>🎫 Ticket Analyzer</h1>
        <p>AI-powered customer ticket sentiment analysis dashboard</p>
      </div>

      <div className="stats">
        <div className="stat-card">
          <h3>Total Tickets</h3>
          <span>{tickets.length}</span>
        </div>

        <div className="stat-card">
          <h3>Positive</h3>
          <span>{positives}</span>
        </div>

        <div className="stat-card">
          <h3>Neutral</h3>
          <span>{neutrals}</span>
        </div>

        <div className="stat-card">
          <h3>Negative</h3>
          <span>{negatives}</span>
        </div>
      </div>

      <div className="main-grid">
        <div className="form-card">
          <h2>Create Ticket</h2>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Title</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Message</label>
              <textarea
                rows={5}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Category</label>
              <input
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="Optional"
              />
            </div>

            <button
              type="submit"
              className="submit-btn"
              disabled={loading}
            >
              {loading ? "Analyzing..." : "Submit Ticket"}
            </button>

            {error && <div className="error">{error}</div>}
          </form>
        </div>

        <div className="ticket-section">
          <h2>Recent Tickets</h2>

          <div className="ticket-list">
            {tickets.map((ticket) => {
              const sentiment = ticket.sentiment?.toLowerCase();

              return (
                <div className="ticket-card" key={ticket.id}>
                  <div className="ticket-header">
                    <div className="ticket-title">
                      {ticket.title}
                    </div>

                    <span className={`badge ${sentiment}`}>
                      {ticket.sentiment}
                    </span>
                  </div>

                  <div className="confidence">
                    Confidence:
                    {" "}
                    {(ticket.confidence * 100).toFixed(1)}%
                  </div>

                  <div className="progress">
                    <div
                      className="progress-fill"
                      style={{
                        width: `${ticket.confidence * 100}%`,
                      }}
                    />
                  </div>

                  <div className="date">
                    {new Date(
                      ticket.created_at
                    ).toLocaleString()}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}