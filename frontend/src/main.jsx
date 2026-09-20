import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = "http://localhost:8000";
const initial = {
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
  return <label className="field"><span>{label}</span><Tag name={name} value={value} onChange={onChange}/></label>
}

function Section({title, children}) { return <section className="card"><h2>{title}</h2>{children}</section> }
function List({items=[]}) { return <ul>{items.map((x,i)=><li key={i}>{typeof x === "string" ? x : JSON.stringify(x)}</li>)}</ul> }

function App(){
  const [form,setForm]=useState(initial), [analysis,setAnalysis]=useState(null), [busy,setBusy]=useState(false), [error,setError]=useState("");
  const result=analysis?.result;
  const meta=useMemo(()=>analysis ? `${analysis.provider} · ${analysis.model_id} · ${analysis.latency_ms} ms · ${analysis.prompt_version}` : "",[analysis]);
  const change=e=>setForm({...form,[e.target.name]:e.target.value});
  async function run(){
    setBusy(true); setError(""); setAnalysis(null);
    try{
      let r=await fetch(`${API}/api/opportunities`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(form)});
      if(!r.ok) throw new Error(await r.text());
      const opp=await r.json();
      r=await fetch(`${API}/api/opportunities/${opp.id}/analyze`,{method:"POST"});
      if(!r.ok) throw new Error(await r.text());
      setAnalysis(await r.json());
    }catch(e){setError(String(e))}finally{setBusy(false)}
  }
  async function review(){
    const r=await fetch(`${API}/api/analysis/${analysis.id}/review`,{method:"POST"});
    setAnalysis(await r.json());
  }
  return <main>
    <header><div><p className="eyebrow">PORTFOLIO PROOF OF CONCEPT</p><h1>Enterprise AI Sales Opportunity Copilot</h1><p className="lede">From account context to customer discovery, solution hypothesis, proof of value and business case — with the seller in control.</p></div><span className="pill">Human-reviewed</span></header>
    <div className="grid">
      <div className="panel">
        <h2>Discovery intake</h2>
        <p className="muted">Use only known information. The AI must label anything else as a hypothesis or unknown.</p>
        <Field label="Account" name="account_name" value={form.account_name} onChange={change}/>
        <Field label="Industry" name="industry" value={form.industry} onChange={change}/>
        <Field area label="Opportunity context" name="opportunity_context" value={form.opportunity_context} onChange={change}/>
        <Field area label="Business objectives" name="business_objectives" value={form.business_objectives} onChange={change}/>
        <Field area label="Known technical / business constraints" name="known_constraints" value={form.known_constraints} onChange={change}/>
        <Field area label="Seller notes" name="seller_notes" value={form.seller_notes} onChange={change}/>
        <button onClick={run} disabled={busy}>{busy?"Preparing brief…":"Generate discovery brief"}</button>
        {error&&<pre className="error">{error}</pre>}
      </div>
      <div className="workspace">
        {!result && <div className="empty"><h2>Opportunity workspace</h2><p>Your structured discovery brief will appear here.</p></div>}
        {result && <>
          <div className="runbar"><span>{meta}</span><button className="secondary" onClick={review} disabled={analysis.human_reviewed}>{analysis.human_reviewed?"Reviewed ✓":"Mark human-reviewed"}</button></div>
          <Section title="Account context"><h3>Facts</h3><List items={result.account_context?.facts}/><h3>Unknowns</h3><List items={result.account_context?.unknowns}/></Section>
          <Section title="Discovery questions">{result.discovery_questions?.map((q,i)=><div className="qa" key={i}><b>{q.category}</b><p>{q.question}</p><small>{q.why_it_matters}</small></div>)}</Section>
          <Section title="Solution hypotheses">{result.solution_hypotheses?.map((x,i)=><div className="qa" key={i}><p>{x.hypothesis}</p><small>Capability: {x.capability_needed}</small></div>)}</Section>
          <Section title="Proof of value"><p>{result.proof_of_value?.hypothesis}</p><h3>Success metrics</h3>{result.proof_of_value?.success_metrics?.map((m,i)=><div className="metric" key={i}><b>{m.metric}</b><span>Baseline needed: {m.baseline_needed}</span><span>Target: {m.target_definition}</span></div>)}</Section>
          <Section title="Business value"><List items={result.business_value?.value_drivers}/><h3>Measurement plan</h3><List items={result.business_value?.measurement_plan}/></Section>
          <Section title="CRM-ready brief"><dl>{Object.entries(result.crm_brief||{}).map(([k,v])=><React.Fragment key={k}><dt>{k.replaceAll("_"," ")}</dt><dd>{v}</dd></React.Fragment>)}</dl></Section>
        </>}
      </div>
    </div>
  </main>
}

createRoot(document.getElementById("root")).render(<App/>);
