import { useState } from "react";

export default function Home() {
  const [message, setMessage] = useState("click a button to see a message");
  const [busy, setBusy] = useState(false);

  async function call(url) {
    setBusy(true);
    try {
      const res = await fetch(url);
      const data = await res.json();
      setMessage(JSON.stringify(data, null, 2));
    } catch (err) {
      setMessage("Error: " + err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ fontFamily: "sans-serif", padding: "2rem", maxWidth: 800, margin: "0 auto" }}>
      <h1>My App — Service Tester</h1>

      <pre
        style={{
          background: "#f4f4f4",
          padding: "1rem",
          borderRadius: 6,
          minHeight: 80,
          whiteSpace: "pre-wrap",
        }}
      >
        {message}
      </pre>

      <h2>Backend (FastAPI)</h2>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 16 }}>
        <button onClick={() => call("/api/")} disabled={busy}>
          GET /api/  (hello)
        </button>
        <button onClick={() => call("/api/health")} disabled={busy}>
          GET /api/health
        </button>
        <button onClick={() => call("/api/data")} disabled={busy}>
          GET /api/data  (users — Postgres + Redis cache)
        </button>
        <button onClick={() => call("/api/posts")} disabled={busy}>
          GET /api/posts  (posts join — Postgres)
        </button>
        <button onClick={() => call("/api/ai")} disabled={busy}>
          GET /api/ai  (backend → ai-service)
        </button>
      </div>

      <h2>AI Service (direct via nginx /ai/)</h2>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        <button onClick={() => call("/ai/health")} disabled={busy}>
          GET /ai/health
        </button>
        <button onClick={() => call("/ai/predict")} disabled={busy}>
          GET /ai/predict
        </button>
        <button onClick={() => call("/ai/info")} disabled={busy}>
          GET /ai/info
        </button>
        <button onClick={() => call("/ai/metrics")} disabled={busy}>
          GET /ai/metrics
        </button>
      </div>

      {busy && <p>Loading…</p>}
    </div>
  );
}
