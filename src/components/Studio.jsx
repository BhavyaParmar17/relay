import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import { download, getJson, postJson } from "../lib/api.js";
import { applyEdits } from "../lib/render.js";
import SourceForm from "./SourceForm.jsx";
import VoiceForm from "./VoiceForm.jsx";
import Results from "./Results.jsx";

const EMPTY_BRAND = { brand_name: "", preset: "expert", banned_words: "", preferred_terms: "", hashtags: "", cta: "", avoid_hype: true };
const today = () => new Date().toISOString().slice(0, 10);
const EMPTY_FORM = { sampleId: null, title: "", source_type: "case_study", url: "", source_text: "", approval: { approved: false, approver: "", date: today() } };

export default function Studio({ request, onRequestHandled }) {
  const [config, setConfig] = useState({ presets: [], samples: [] });
  const [form, setForm] = useState(EMPTY_FORM);
  const [brand, setBrand] = useState(EMPTY_BRAND);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [edits, setEdits] = useState({});
  const [checks, setChecks] = useState({});
  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState("");
  const textRef = useRef(null);
  const timers = useRef({});
  const lastRun = useRef(null);

  useEffect(() => {
    getJson("/api/config").then(setConfig).catch((e) => setError(e));
  }, []);

  const loadSample = useCallback(
    (id) => {
      if (!id) {
        setForm({ ...EMPTY_FORM, approval: { approved: false, approver: "", date: today() } });
        setBrand(EMPTY_BRAND);
        return;
      }
      const s = config.samples.find((x) => x.id === id);
      if (!s) return;
      setForm({
        sampleId: s.id,
        title: s.title,
        source_type: s.source_type,
        url: s.url,
        source_text: s.source_text,
        approval: { approved: true, approver: "Riya Shah, Marketing lead", date: today() },
      });
      setBrand({ ...EMPTY_BRAND, ...s.brand });
    },
    [config.samples]
  );

  useEffect(() => {
    if (!request || !config.samples.length) return;
    if (request === "sample") loadSample("case_study");
    document.getElementById("studio")?.scrollIntoView({ behavior: "smooth", block: "start" });
    if (request === "own") setTimeout(() => textRef.current?.focus({ preventScroll: true }), 600);
    onRequestHandled();
  }, [request, config.samples, loadSample, onRequestHandled]);

  const payload = useMemo(
    () => ({
      title: form.title,
      source_type: form.source_type,
      url: form.url,
      source_text: form.source_text,
      approval: form.approval,
      brand,
    }),
    [form, brand]
  );

  const run = async () => {
    setStatus("loading");
    setError(null);
    try {
      const data = await postJson("/api/repurpose", payload);
      lastRun.current = payload;
      setResult(data);
      setEdits({});
      setChecks({});
      setStatus("done");
      setTimeout(() => document.getElementById("results")?.scrollIntoView({ behavior: "smooth", block: "start" }), 120);
    } catch (err) {
      setError(err);
      setStatus("error");
    }
  };

  const outputs = useMemo(() => (result ? applyEdits(result.outputs, edits) : null), [result, edits]);

  const verify = useCallback((items) => {
    if (!lastRun.current) return;
    postJson("/api/verify", { ...lastRun.current, items })
      .then(({ items: res }) => setChecks((c) => ({ ...c, ...Object.fromEntries(res.map((r) => [r.id, r])) })))
      .catch(() => {});
  }, []);

  const setEdit = useCallback(
    (id, value, platform, sources, type) => {
      setEdits((e) => ({ ...e, [id]: value }));
      clearTimeout(timers.current[id]);
      timers.current[id] = setTimeout(() => {
        const text = type === "slide" ? `${value.headline}. ${value.body}` : type === "scene" ? `${value.on_screen}. ${value.voiceover}` : value;
        verify([{ id, platform, text, sources }]);
      }, 380);
    },
    [verify]
  );

  const resetEdit = useCallback((id) => {
    setEdits((e) => {
      const next = { ...e };
      delete next[id];
      return next;
    });
    setChecks((c) => {
      const next = { ...c };
      delete next[id];
      return next;
    });
  }, []);

  // keep whole-post meters (length, fold, hashtags) current after edits
  useEffect(() => {
    if (!outputs || !Object.keys(edits).length) return undefined;
    const t = setTimeout(() => {
      verify([
        { id: "__linkedin", platform: "linkedin", text: outputs.linkedin.text, sources: [] },
        { id: "__instagram", platform: "instagram", text: outputs.instagram.text, sources: [] },
      ]);
    }, 500);
    return () => clearTimeout(t);
  }, [outputs, edits, verify]);

  const onExport = async (format) => {
    setExporting(true);
    setExportMsg("");
    try {
      const name = await download("/api/export", { ...lastRun.current, format, outputs });
      setExportMsg(`Saved ${name}`);
    } catch (err) {
      setExportMsg(err.message);
    } finally {
      setExporting(false);
    }
  };

  const changedSinceRun = result && lastRun.current && JSON.stringify(lastRun.current) !== JSON.stringify(payload);

  return (
    <section className="studio" id="studio" aria-labelledby="studio-h">
      <div className="studio-head">
        <h2 id="studio-h">Studio</h2>
        <p>Paste or import an approved source, set the voice, and Relay writes all three formats. Edit any line; it’s re-checked against the source as you type.</p>
      </div>
      <div className="setup">
        <SourceForm form={form} setForm={setForm} samples={config.samples} loadSample={loadSample} error={error} textRef={textRef} />
        <VoiceForm brand={brand} setBrand={setBrand} presets={config.presets} />
      </div>
      <div className="run-row">
        <button type="button" className="btn btn-primary btn-big" onClick={run} disabled={status === "loading"}>
          {status === "loading" ? "Writing posts…" : result ? "Write them again" : "Write the posts"}
        </button>
        {error && <p className="banner" role="alert">{error.message}</p>}
        {changedSinceRun && !error && <p className="run-note">You’ve changed the source or voice. Write again to update the posts.</p>}
      </div>

      {result && outputs && (
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }} key={result.analysis.title + result.voice.id}>
          <Results
            result={result}
            outputs={outputs}
            edits={edits}
            checks={checks}
            setEdit={setEdit}
            resetEdit={resetEdit}
            onExport={onExport}
            exporting={exporting}
            exportMsg={exportMsg}
          />
        </motion.div>
      )}
    </section>
  );
}
