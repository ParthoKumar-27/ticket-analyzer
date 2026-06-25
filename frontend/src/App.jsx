import { useEffect, useState } from "react";
import { createTicket, listTickets, sortTicket } from "./api";
import "./styles.css";

export default function App() {
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [category, setCategory] = useState("");

  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // QueueStorm /sort-ticket state.
  const [sortTicketId, setSortTicketId] = useState("T-001");
  const [sortChannel, setSortChannel] = useState("app");
  const [sortLocale, setSortLocale] = useState("en");
  const [sortMessage, setSortMessage] = useState(
    "I sent 5000 taka to a wrong number this morning, please help me get it back"
  );
  const [sortResult, setSortResult] = useState(null);
  const [sortLoading, setSortLoading] = useState(false);
  const [sortError, setSortError] = useState("");

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

  async function handleSort(e) {
    e.preventDefault();
    setSortLoading(true);
    setSortError("");
    try {
      const data = await sortTicket({
        ticket_id: sortTicketId,
        channel: sortChannel || undefined,
        locale: sortLocale || undefined,
        message: sortMessage,
      });
      setSortResult(data);
    } catch {
      setSortError("Could not sort ticket");
    } finally {
      setSortLoading(false);
    }
  }

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

      <div className="sort-section">
        <h2>🛡️ Sort Ticket (QueueStorm)</h2>
        <p className="sort-subtitle">
          Submit one customer message. The backend classifies it into a
          case type, severity, and routing department.
        </p>

        <form className="sort-grid" onSubmit={handleSort}>
          <div className="form-group">
            <label>Ticket ID</label>
            <input
              value={sortTicketId}
              onChange={(e) => setSortTicketId(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label>Channel</label>
            <select
              value={sortChannel}
              onChange={(e) => setSortChannel(e.target.value)}
            >
              <option value="app">app</option>
              <option value="sms">sms</option>
              <option value="call_center">call_center</option>
              <option value="merchant_portal">merchant_portal</option>
            </select>
          </div>

          <div className="form-group">
            <label>Locale</label>
            <select
              value={sortLocale}
              onChange={(e) => setSortLocale(e.target.value)}
            >
              <option value="en">en</option>
              <option value="bn">bn</option>
              <option value="mixed">mixed</option>
            </select>
          </div>

          <div className="form-group sort-message">
            <label>Customer message</label>
            <textarea
              rows={4}
              value={sortMessage}
              onChange={(e) => setSortMessage(e.target.value)}
              required
            />
          </div>

          <div className="sort-submit">
            <button
              type="submit"
              className="submit-btn"
              disabled={sortLoading}
            >
              {sortLoading ? "Sorting..." : "Sort Ticket"}
            </button>
            {sortError && <div className="error">{sortError}</div>}
          </div>
        </form>

        {sortResult && (
          <div
            className={`sort-result ${
              sortResult.human_review_required ? "review" : ""
            }`}
          >
            <div className="sort-row">
              <span className="sort-label">Case type</span>
              <span className="sort-value">{sortResult.case_type}</span>
            </div>
            <div className="sort-row">
              <span className="sort-label">Severity</span>
              <span
                className={`sort-value severity-${sortResult.severity}`}
              >
                {sortResult.severity}
              </span>
            </div>
            <div className="sort-row">
              <span className="sort-label">Department</span>
              <span className="sort-value">{sortResult.department}</span>
            </div>
            <div className="sort-row">
              <span className="sort-label">Confidence</span>
              <span className="sort-value">
                {(sortResult.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="sort-row">
              <span className="sort-label">Human review</span>
              <span className="sort-value">
                {sortResult.human_review_required ? "Required" : "Not required"}
              </span>
            </div>
            <div className="sort-summary">
              <span className="sort-label">Agent summary</span>
              <p>{sortResult.agent_summary}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}