import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = import.meta.env.VITE_API_BASE_URL || "";
const SYNTHETIC = {
  account_name: "Northstar Manufacturing (Synthetic)",
  industry: "Manufacturing",
  website: "",
  opportunity_context: "Sales leadership says opportunity preparation is inconsistent across complex enterprise accounts.",
  business_objectives: "Improve discovery preparation and create a repeatable proof-of-value motion.",
  known_constraints: "Customer data cannot be used for autonomous outreach; seller approval is mandatory.",
  seller_notes: "Need a clear way to separate facts from assumptions."
};

function Field({label, name, value, onChange, area=false}) {
  const Tag = area ? "textarea" : "input";
  return <label className="field"><span>{label}</span><Tag name={name} value={value} onChange={onChange}/></label>;
}

function Section({title, eyebrow, children}) {
  return <section className="card"><h2>{title}</h2>{eyebrow && <p className="hypothesis-note">{eyebrow}</p>}{children}</section>;
}

function List({items=[]}) {
  return <ul>{items.map((item, index) => <li key={index}>{typeof item === "string" ? item : JSON.stringify(item)}</li>)}</ul>;
}

function statusLabel(status) {
  if (status === "approved") return "Approved";
  if (status === "needs_revision") return "Needs revision";
  return "Pending seller review";
}

function App() {
  const [form, setForm] = useState(SYNTHETIC);
  const [analysis, setAnalysis] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [aiStatus, setAiStatus] = useState(null);
  const [ping, setPing] = useState(null);
  const [pingBusy, setPingBusy] = useState(false);
  const [crmEvent, setCrmEvent] = useState(null);
  const [reviewNote, setReviewNote] = useState("");
  const result = analysis?.result;
  const meta = useMemo(() => {
    if (!analysis) return "";
    const provider = analysis.provider === "watsonx.ai" ? "IBM watsonx.ai" : "Local deterministic demo";
    const repair = analysis.repair_attempted ? " · repair attempted" : "";
    return `${provider} · ${analysis.model_id} · ${analysis.latency_ms} ms · ${analysis.prompt_version}${repair}`;
  }, [analysis]);

  useEffect(() => {
    fetch(`${API}/api/ai/status`).then(r => r.json()).then(setAiStatus).catch(() => {});
  }, []);

  const change = (event) => setForm({...form, [event.target.name]: event.target.value});

  async function readError(response) {
    const text = await response.text();
    try {
      const body = JSON.parse(text);
      const detail = body.detail;
      if (detail && typeof detail === "object") {
        const errors = detail.validation_errors ? `\n${JSON.stringify(detail.validation_errors, null, 2)}` : "";
        return `${detail.stage || "error"}: ${detail.error || JSON.stringify(detail)}${errors}`;
      }
      return text;
    } catch {
      return text;
    }
  }

  async function run() {
    setBusy(true);
    setError("");
    setAnalysis(null);
    setCrmEvent(null);
    try {
      let response = await fetch(`${API}/api/opportunities`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(form)
      });
      if (!response.ok) throw new Error(await readError(response));
      const opportunity = await response.json();
      response = await fetch(`${API}/api/opportunities/${opportunity.id}/analyze`, {method: "POST"});
      if (!response.ok) throw new Error(await readError(response));
      setAnalysis(await response.json());
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setBusy(false);
    }
  }

  async function review(status) {
    const response = await fetch(`${API}/api/analysis/${analysis.id}/review`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({status, note: reviewNote})
    });
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    setAnalysis(await response.json());
  }

  async function downloadJson() {
    const response = await fetch(`${API}/api/analysis/${analysis.id}/export`);
    const body = await response.json();
    const blob = new Blob([JSON.stringify(body, null, 2)], {type: "application/json"});
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `opportunity-brief-${analysis.id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function simulateCrm() {
    const response = await fetch(`${API}/api/analysis/${analysis.id}/crm-export`, {method: "POST"});
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    setCrmEvent(await response.json());
  }

  async function testIbm() {
    setPingBusy(true);
    setPing(null);
    try {
      const response = await fetch(`${API}/api/ai/ping`, {method: "POST"});
      setPing(await response.json());
    } catch (err) {
      setPing({connected: false, stage: "client", error: String(err)});
    } finally {
      setPingBusy(false);
    }
  }

  return (
    <main>
      <header>
        <div>
          <p className="eyebrow">PORTFOLIO PROOF OF CONCEPT</p>
          <h1>Enterprise AI Sales Opportunity Copilot</h1>
          <p className="lede">From account context to customer discovery, solution hypothesis, proof of value and business case — with the seller in control.</p>
        </div>
        <span className={`pill ${analysis?.review_status || "pending"}`}>{statusLabel(analysis?.review_status)}</span>
      </header>
      <div className="grid">
        <div className="panel">
          <h2>Discovery intake</h2>
          <p className="muted">Use only known information. The AI must label anything else as a hypothesis or unknown.</p>
          <button className="secondary" type="button" onClick={() => setForm(SYNTHETIC)}>Load synthetic account</button>
          <Field label="Account" name="account_name" value={form.account_name} onChange={change}/>
          <Field label="Industry" name="industry" value={form.industry} onChange={change}/>
          <Field label="Website" name="website" value={form.website} onChange={change}/>
          <Field area label="Opportunity context" name="opportunity_context" value={form.opportunity_context} onChange={change}/>
          <Field area label="Business objectives" name="business_objectives" value={form.business_objectives} onChange={change}/>
          <Field area label="Known technical / business constraints" name="known_constraints" value={form.known_constraints} onChange={change}/>
          <Field area label="Seller notes" name="seller_notes" value={form.seller_notes} onChange={change}/>
          <button onClick={run} disabled={busy}>{busy ? "Preparing brief…" : "Generate discovery brief"}</button>
          {error && <pre className="error">{error}</pre>}
        </div>
        <div className="workspace">
          {!result && <div className="empty"><h2>Opportunity workspace</h2><p>Your structured discovery brief will appear here.</p></div>}
          {result && <>
            <div className="runbar">
              <span>{meta}</span>
              <div className="run-actions">
                <button className="secondary" onClick={() => review("needs_revision")}>Needs revision</button>
                <button className="secondary" onClick={() => review("approved")} disabled={analysis.review_status === "approved"}>
                  {analysis.review_status === "approved" ? "Approved ✓" : "Approve"}
                </button>
                <button className="secondary" onClick={downloadJson}>Download JSON</button>
                <button className="secondary" onClick={simulateCrm} disabled={analysis.review_status !== "approved"}>Simulate CRM handoff</button>
              </div>
            </div>
            <label className="field compact"><span>Seller review note</span><input value={reviewNote} onChange={(e) => setReviewNote(e.target.value)} /></label>
            <aside className="ibm-tester">
              <strong>IBM connection</strong>
              <p>IBM Cloud IAM · watsonx.ai · {aiStatus?.model_id || "ibm/granite-4-h-small"}</p>
              <p>App mode: {aiStatus?.copilot_mode || "unknown"} · credentials present: {String(aiStatus?.credentials_present ?? false)}</p>
              <button className="secondary" onClick={testIbm} disabled={pingBusy}>{pingBusy ? "Testing…" : "Test IBM Connection"}</button>
              {ping && <p className={ping.connected ? "ok" : "warn"}>{ping.connected ? `Connected · ${ping.provider} · ${ping.model_id} · ${ping.latency_ms} ms` : `${ping.stage}: ${ping.error}`}</p>}
            </aside>
            <Section title="Account summary">{result.account_summary}</Section>
            <Section title="Known facts" eyebrow="Deterministic from seller-submitted context. Not generated by the model.">
              <List items={result.account_context?.facts}/>
            </Section>
            <Section title="Unknowns / assumptions" eyebrow="AI hypotheses — validate during discovery">
              <h3>Unknowns</h3>
              <List items={result.account_context?.unknowns}/>
              <h3>Assumptions</h3>
              <List items={result.account_context?.assumptions}/>
            </Section>
            <Section title="Buyer / stakeholder personas" eyebrow="AI hypotheses — validate during discovery">
              {result.stakeholder_hypotheses?.map((persona, index) => (
                <div className="qa" key={index}>
                  <b>{persona.role}</b>
                  <p>Priorities: {(persona.likely_priorities || []).join(", ")}</p>
                  <p>Concerns: {(persona.likely_concerns || []).join(", ")}</p>
                  <small>Decision influence: {persona.decision_influence}</small>
                  <small>Assumptions: {(persona.assumptions || []).join("; ")}</small>
                  <small>Validate: {persona.validation_question}</small>
                </div>
              ))}
            </Section>
            <Section title="Business problems" eyebrow="AI hypotheses unless evidence is seller-supplied">
              {result.business_problems?.map((item, index) => (
                <div className="qa" key={index}>
                  <b>{item.confidence} confidence</b>
                  <p>{item.problem}</p>
                  <small>{item.evidence}</small>
                </div>
              ))}
            </Section>
            <Section title="Discovery questions">
              {result.discovery_questions?.map((item, index) => (
                <div className="qa" key={index}>
                  <b>{item.category}</b>
                  <p>{item.question}</p>
                  <small>{item.why_it_matters}</small>
                </div>
              ))}
            </Section>
            <Section title="Technical constraints">
              {result.technical_constraints?.map((item, index) => (
                <div className="qa" key={index}>
                  <b>{item.status}</b>
                  <p>{item.constraint}</p>
                  <small>{item.validation_question}</small>
                </div>
              ))}
            </Section>
            <Section title="Solution hypotheses" eyebrow="AI hypotheses — not a committed architecture">
              {result.solution_hypotheses?.map((item, index) => (
                <div className="qa" key={index}>
                  <p>{item.hypothesis}</p>
                  <small>Need: {item.customer_need}</small>
                  <small>Capability: {item.capability_needed}</small>
                  <small>Assumptions: {(item.assumptions || []).join("; ")}</small>
                  <small>Risks: {(item.risks || []).join("; ")}</small>
                </div>
              ))}
            </Section>
            <Section title="Personalized outreach / conversation angle" eyebrow="Consultative prep only. Not an email campaign.">
              <dl>
                <dt>Target stakeholder</dt><dd>{result.personalized_outreach?.target_stakeholder}</dd>
                <dt>Business issue</dt><dd>{result.personalized_outreach?.relevant_business_issue}</dd>
                <dt>Conversation angle</dt><dd>{result.personalized_outreach?.conversation_angle}</dd>
                <dt>Next discovery step</dt><dd>{result.personalized_outreach?.suggested_next_discovery_step}</dd>
              </dl>
            </Section>
            <Section title="Proof of value">
              <p>{result.proof_of_value?.hypothesis}</p>
              <h3>In scope</h3><List items={result.proof_of_value?.in_scope}/>
              <h3>Out of scope</h3><List items={result.proof_of_value?.out_of_scope}/>
              <h3>Data requirements</h3><List items={result.proof_of_value?.data_requirements}/>
            </Section>
            <Section title="Success criteria">
              {(result.success_criteria || result.proof_of_value?.success_metrics || []).map((metric, index) => (
                <div className="metric" key={index}>
                  <b>{metric.metric}</b>
                  <span>Baseline needed: {metric.baseline_needed}</span>
                  <span>Target: {metric.target_definition}</span>
                </div>
              ))}
            </Section>
            <Section title="Business-value measurement plan">
              <h3>Value drivers</h3><List items={result.business_value?.value_drivers}/>
              <h3>Assumptions to validate</h3><List items={result.business_value?.assumptions_to_validate}/>
              <h3>Measurement plan</h3><List items={result.business_value?.measurement_plan}/>
            </Section>
            <Section title="Risks / open questions"><List items={result.risks_and_open_questions}/></Section>
            <Section title="CRM-ready opportunity summary">
              <dl>
                {Object.entries(result.crm_brief || {}).map(([key, value]) => (
                  <React.Fragment key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{value}</dd></React.Fragment>
                ))}
              </dl>
              {crmEvent && <p className="ok">CRM-ready export stored locally as a simulated webhook. Not sent to Salesforce.</p>}
            </Section>
          </>}
        </div>
      </div>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App/>);
