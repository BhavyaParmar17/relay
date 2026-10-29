import { useState } from "react";
import { postJson } from "../lib/api.js";
import { Field, Segmented } from "./Field.jsx";

const TYPES = [
  { value: "case_study", label: "Case study" },
  { value: "blog", label: "Blog post" },
  { value: "product_page", label: "Product page" },
];

export default function SourceForm({ form, setForm, samples, loadSample, error, textRef }) {
  const [url, setUrl] = useState("");
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState("");
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target ? e.target.value : e }));
  const setApproval = (key, value) => setForm((f) => ({ ...f, approval: { ...f.approval, [key]: value } }));
  const words = form.source_text.trim() ? form.source_text.trim().split(/\s+/).length : 0;
  const fieldError = (name) => (error?.field === name ? error.message : undefined);

  const runImport = async () => {
    setImporting(true);
    setImportError("");
    try {
      const page = await postJson("/api/import", { url });
      setForm((f) => ({ ...f, title: page.title || f.title, source_text: page.source_text, url: page.url }));
    } catch (err) {
      setImportError(err.message);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="panel source-form">
      <div className="panel-head">
        <h3>Approved source</h3>
        <div className="sample-row" role="group" aria-label="Load a sample source">
          <span className="sample-label">Load a sample:</span>
          {samples.map((s) => (
            <button key={s.id} type="button" className={`chip ${form.sampleId === s.id ? "is-on" : ""}`} onClick={() => loadSample(s.id)}>
              {s.label}
            </button>
          ))}
          <button type="button" className="chip chip-ghost" onClick={() => loadSample(null)}>Clear</button>
        </div>
      </div>

      <div className="import-row">
        <Field
          label="Import from a link"
          optional
          type="url"
          inputMode="url"
          placeholder="https://yoursite.com/blog/post"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          error={importError}
          hint={!importError ? "Pulls the readable text from a public page. You can also paste it below." : undefined}
        />
        <button type="button" className="btn btn-quiet" onClick={runImport} disabled={!url || importing}>
          {importing ? "Importing…" : "Import"}
        </button>
      </div>

      <div className="field">
        <span className="label-like">Source type</span>
        <Segmented name="source-type" options={TYPES} value={form.source_type} onChange={(v) => setForm((f) => ({ ...f, source_type: v }))} />
      </div>

      <Field label="Title" value={form.title} onChange={set("title")} placeholder="Taken from the first heading if left empty" optional />

      <Field
        as="textarea"
        label="Source text"
        rows={13}
        value={form.source_text}
        onChange={set("source_text")}
        placeholder={"Paste the approved article, case study or product page.\nUse ## for headings and - for bullet points if you like."}
        error={fieldError("source_text")}
        hint={`${words} words${words < 60 ? ", at least 60 needed" : ""}`}
        ref={textRef}
      />

      <Field label="Source link" optional type="url" value={form.url} onChange={set("url")} placeholder="Used in the call to action" />

      <fieldset className={`approval ${fieldError("approval") ? "has-error" : ""}`}>
        <legend>Approval</legend>
        <label className="check">
          <input type="checkbox" checked={form.approval.approved} onChange={(e) => setApproval("approved", e.target.checked)} />
          <span>This source is approved for reuse on social</span>
        </label>
        <div className="approval-fields">
          <Field label="Approved by" value={form.approval.approver} onChange={(e) => setApproval("approver", e.target.value)} placeholder="Name or role" />
          <Field label="Date" type="date" value={form.approval.date} onChange={(e) => setApproval("date", e.target.value)} optional />
        </div>
        {fieldError("approval") && <p className="field-error">{fieldError("approval")}</p>}
      </fieldset>
    </div>
  );
}
