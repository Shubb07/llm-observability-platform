export default function ProjectDetailPage() {
  return (
    <>
      <div className="page-header">
        <div>
          <h2>Trace Explorer</h2>
          <p>Coming next — view and filter your LLM traces</p>
        </div>
      </div>
      <div className="page-body">
        <div className="state-container">
          <div className="state-icon">🔭</div>
          <p className="state-message">Trace Explorer coming soon</p>
          <p className="state-hint">
            This is where you'll see every LLM call your SDK captured — filter by model,
            status, date, and drill into the full prompt/completion detail.
          </p>
        </div>
      </div>
    </>
  );
}
