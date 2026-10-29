import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import { copyText } from "../lib/api.js";
import { renderCarousel, renderScript } from "../lib/render.js";
import { Block, Cites, Issues, Meter } from "./Blocks.jsx";

const TABS = [
  { id: "linkedin", label: "LinkedIn" },
  { id: "instagram", label: "Instagram" },
  { id: "video", label: "Short video" },
];
const NUM_RE = /((?:₹|\$|€|£|Rs\.?\s?)?\d(?:[\d,]*\d)?(?:\.\d+)?%?)/g;

function withFigures(text) {
  return text.split(NUM_RE).map((part, i) => (i % 2 === 1 ? <mark key={i} className="fig">{part}</mark> : part));
}

function CopyButton({ text, label }) {
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      className="btn btn-small"
      onClick={async () => {
        if (await copyText(text)) {
          setDone(true);
          setTimeout(() => setDone(false), 1600);
        }
      }}
    >
      {done ? "Copied" : label}
    </button>
  );
}

/* ------------------------------------------------------------------ */
function SourcePanel({ analysis, usage, hover, pinned, setPinned }) {
  const listRef = useRef(null);
  const refs = useRef({});
  useEffect(() => {
    const first = hover.find((id) => refs.current[id]);
    const box = listRef.current;
    const el = refs.current[first];
    if (box && el) {
      const y = el.offsetTop;
      if (y < box.scrollTop || y > box.scrollTop + box.clientHeight - 60) {
        box.scrollTo({ top: Math.max(0, y - 40), behavior: "smooth" });
      }
    }
  }, [hover]);

  return (
    <aside className="source-panel" aria-label="Approved source, numbered">
      <div className="source-panel-head">
        <h3>Source, numbered</h3>
        <p>Hover a post line to find its source. Select a source line to see where it was used.</p>
      </div>
      <ol className="seg-list" ref={listRef}>
        {analysis.segments.map((s) => {
          const used = usage[s.id] || [];
          const lit = hover.includes(s.id) || pinned === s.id;
          return (
            <li key={s.id} ref={(el) => (refs.current[s.id] = el)} className={`seg seg-${s.kind}${lit ? " is-lit" : ""}${used.length ? " is-used" : ""}`}>
              <button type="button" onClick={() => setPinned(pinned === s.id ? null : s.id)} aria-pressed={pinned === s.id}>
                <span className="sid">{s.id}</span>
                <span className="seg-text">{withFigures(s.text)}</span>
                {used.length > 0 && (
                  <span className="seg-used" aria-label={`Used in ${used.join(", ")}`}>
                    {used.map((p) => (
                      <span key={p} className={`dot dot-${p}`} />
                    ))}
                  </span>
                )}
              </button>
            </li>
          );
        })}
      </ol>
    </aside>
  );
}

/* ------------------------------------------------------------------ */
function LinkedInView({ out, ctx }) {
  const meta = ctx.checks.__linkedin?.meta || out.meta;
  return (
    <div className="view view-linkedin">
      <div className="meters">
        <Meter label="Characters" value={meta.chars} limit={meta.limit} ok={!meta.over_limit} />
        <Meter label="Before “see more”" value={meta.fold_chars} limit={meta.fold_limit} ok={meta.fold_ok} />
        <Meter label="Hashtags" value={meta.hashtag_count} limit={meta.hashtag_limit} ok={meta.hashtag_count <= meta.hashtag_limit} />
        <Meter label="Readability" value={meta.readability?.label || "—"} />
        <CopyButton text={out.text} label="Copy post" />
      </div>
      <div className="sheet">
        {out.blocks.map((b, i) => {
          const gap = i > 0 && !(["point"].includes(b.kind) && ["point", "framing"].includes(out.blocks[i - 1].kind));
          return (
            <div key={b.id} className={gap ? "gap" : ""}>
              <Block {...ctx.blockProps(b, "linkedin")} />
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SlideEditor({ slide, ctx }) {
  const editing = ctx.editing === slide.id;
  const val = ctx.edits[slide.id] || { headline: slide.headline, body: slide.body };
  const issues = ctx.checks[slide.id]?.issues ?? slide.issues;
  const hl = ctx.pinned && slide.sources.includes(ctx.pinned);
  return (
    <li
      className={`slide slide-${slide.kind}${hl ? " is-hl" : ""}`}
      onMouseEnter={() => ctx.setHover(slide.sources)}
      onMouseLeave={() => ctx.setHover([])}
    >
      <div className="slide-face">
        {editing ? (
          <>
            <input aria-label="Slide headline" value={val.headline} onChange={(e) => ctx.setEdit(slide.id, { ...val, headline: e.target.value }, "instagram", slide.sources, "slide")} />
            <textarea aria-label="Slide text" rows={4} value={val.body} onChange={(e) => ctx.setEdit(slide.id, { ...val, body: e.target.value }, "instagram", slide.sources, "slide")} />
          </>
        ) : (
          <>
            <strong className="slide-h">{slide.headline}</strong>
            <p className="slide-b">{slide.body}</p>
          </>
        )}
      </div>
      <div className="slide-foot">
        <Cites ids={slide.sources} kind={slide.kind} />
        <button type="button" className="tool" onClick={() => ctx.setEditing(editing ? null : slide.id)}>
          {editing ? "Done" : "Edit"}
        </button>
      </div>
      <Issues issues={issues} />
    </li>
  );
}

function InstagramView({ out, ctx }) {
  const meta = ctx.checks.__instagram?.meta || out.meta;
  return (
    <div className="view view-instagram">
      <div className="meters">
        <Meter label="Characters" value={meta.chars} limit={meta.limit} ok={!meta.over_limit} />
        <Meter label="Before the cut" value={meta.fold_chars} limit={meta.fold_limit} ok={meta.fold_ok} />
        <Meter label="Hashtags" value={meta.hashtag_count} limit={meta.hashtag_limit} ok={meta.hashtag_count <= meta.hashtag_limit} />
        <CopyButton text={out.text} label="Copy caption" />
      </div>
      <h4 className="view-sub">Caption</h4>
      <div className="sheet">
        {out.blocks.map((b, i) => (
          <div key={b.id} className={i ? "gap" : ""}>
            <Block {...ctx.blockProps(b, "instagram")} />
          </div>
        ))}
      </div>
      <div className="view-sub-row">
        <h4 className="view-sub">Carousel, {out.slides.length} slides</h4>
        <CopyButton text={renderCarousel(out.slides)} label="Copy slides" />
      </div>
      <ol className="carousel">
        {out.slides.map((s) => (
          <SlideEditor key={s.id} slide={s} ctx={ctx} />
        ))}
      </ol>
      <p className="alt"><strong>Alt text.</strong> {out.alt_text}</p>
    </div>
  );
}

function VideoView({ out, ctx }) {
  const total = out.scenes.length ? out.scenes[out.scenes.length - 1].end : 0;
  const meta = out.meta;
  return (
    <div className="view view-video">
      <div className="meters">
        <Meter label="Length" value={`${total.toFixed(0)} s`} ok={meta.in_range} />
        <Meter label="Target" value={`${meta.ideal[0]}–${meta.ideal[1]} s`} />
        <Meter label="Words" value={out.scenes.reduce((n, s) => n + s.voiceover.split(/\s+/).filter(Boolean).length, 0)} />
        <CopyButton text={renderScript(out.scenes) + `\n\n${out.hashtags.join(" ")}`} label="Copy script" />
      </div>
      <div className="timeline" aria-hidden="true">
        {out.scenes.map((s) => (
          <span key={s.id} style={{ flexGrow: Math.max(s.end - s.start, 0.5) }} className={ctx.pinned && s.sources.includes(ctx.pinned) ? "is-hl" : ""}>
            {s.label}
          </span>
        ))}
      </div>
      <ol className="scenes">
        {out.scenes.map((s) => {
          const editing = ctx.editing === s.id;
          const val = ctx.edits[s.id] || { on_screen: s.on_screen, voiceover: s.voiceover };
          const issues = ctx.checks[s.id]?.issues ?? s.issues;
          const hl = ctx.pinned && s.sources.includes(ctx.pinned);
          return (
            <li key={s.id} className={`scene${hl ? " is-hl" : ""}`} onMouseEnter={() => ctx.setHover(s.sources)} onMouseLeave={() => ctx.setHover([])}>
              <div className="scene-time">
                <strong>{s.start.toFixed(1)}–{s.end.toFixed(1)} s</strong>
                <span>{s.label}</span>
              </div>
              <div className="scene-body">
                {editing ? (
                  <>
                    <label>
                      On screen
                      <input value={val.on_screen} onChange={(e) => ctx.setEdit(s.id, { ...val, on_screen: e.target.value }, "video", s.sources, "scene")} />
                    </label>
                    <label>
                      Voiceover
                      <textarea rows={3} value={val.voiceover} onChange={(e) => ctx.setEdit(s.id, { ...val, voiceover: e.target.value }, "video", s.sources, "scene")} />
                    </label>
                  </>
                ) : (
                  <>
                    <p className="on-screen">{s.on_screen}</p>
                    <p className="vo">
                      {s.voiceover}
                      <Cites ids={s.sources} kind="cta" />
                    </p>
                  </>
                )}
                <p className="visual">Shot: {s.visual}</p>
                <Issues issues={issues} />
              </div>
              <button type="button" className="tool" onClick={() => ctx.setEditing(editing ? null : s.id)}>
                {editing ? "Done" : "Edit"}
              </button>
            </li>
          );
        })}
      </ol>
      <p className="alt"><strong>Hashtags.</strong> {out.hashtags.join(" ")}</p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
function Checks({ result, outputs, checks, onExport, exporting, exportMsg }) {
  const ledger = result.ledger;
  const issues = [];
  const collect = (items, platform, labelFn) =>
    items.forEach((b) => {
      const list = checks[b.id]?.issues ?? b.issues;
      list.forEach((x) => issues.push({ ...x, where: `${platform} ${labelFn(b)}` }));
    });
  collect(outputs.linkedin.blocks, "LinkedIn", (b) => b.kind);
  collect(outputs.instagram.blocks, "Instagram", (b) => b.kind);
  collect(outputs.instagram.slides, "Carousel", (b) => b.id.replace("C", "slide "));
  collect(outputs.video.scenes, "Video", (b) => b.label.toLowerCase());
  const high = issues.filter((x) => x.severity === "high").length;

  return (
    <div className="checks">
      <section className="check-col" aria-labelledby="ledger-h">
        <h3 id="ledger-h">Fact ledger</h3>
        <p className="check-note">Figures, names and quotes found in the source, and the posts that use them.</p>
        <div className="table-scroll">
          <table className="ledger">
            <thead>
              <tr>
                <th scope="col">Fact</th>
                <th scope="col">Line</th>
                <th scope="col" className="c"><span className="dot dot-linkedin" title="LinkedIn" /><span className="sr-only">LinkedIn</span></th>
                <th scope="col" className="c"><span className="dot dot-instagram" title="Instagram" /><span className="sr-only">Instagram</span></th>
                <th scope="col" className="c"><span className="dot dot-video" title="Video" /><span className="sr-only">Video</span></th>
              </tr>
            </thead>
            <tbody>
              {ledger.map((f) => (
                <tr key={f.id} className={f.used_in.length ? "" : "is-unused"}>
                  <th scope="row">
                    <span className={`fact-kind k-${f.kind}`}>{f.kind}</span> {f.value.length > 48 ? f.value.slice(0, 48) + "…" : f.value}
                  </th>
                  <td>{f.source}</td>
                  {["linkedin", "instagram", "video"].map((p) => (
                    <td key={p} className="c">{f.used_in.includes(p) ? <span className={`tick tick-${p}`} aria-label="used">●</span> : <span className="tick-off" aria-label="not used">○</span>}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="check-col" aria-labelledby="voice-h">
        <h3 id="voice-h">Voice fixes</h3>
        <p className="check-note">Changes Relay made automatically to match your brand voice.</p>
        {result.voice_changes.length ? (
          <ul className="changes">
            {result.voice_changes.slice(0, 40).map((c, i) => (
              <li key={i}>
                <span className="change-rule">{c.rule}</span>
                <span>
                  <del>{c.before || "—"}</del> <ins>{c.after || "removed"}</ins>
                </span>
                <span className="change-where">{c.block}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="empty">The source already matched this voice. Nothing needed changing.</p>
        )}
      </section>

      <section className="check-col" aria-labelledby="issues-h">
        <h3 id="issues-h">Needs a look</h3>
        <p className="check-note">{issues.length ? `${issues.length} to review, ${high} that could change a fact.` : "No problems found. Every figure and name traces to the source."}</p>
        {issues.length > 0 && (
          <ul className="issue-list">
            {issues.map((x, i) => (
              <li key={i} className={`sev-${x.severity}`}>
                <span className="issue-where">{x.where}</span>
                {x.message}
              </li>
            ))}
          </ul>
        )}
        <div className="export">
          <h4>Export for review</h4>
          <p className="check-note">Includes your edits, the approval record and a line-by-line source map.</p>
          <div className="export-row">
            {[["md", "Markdown"], ["csv", "CSV"], ["json", "JSON"]].map(([fmt, label]) => (
              <button key={fmt} type="button" className="btn btn-quiet" onClick={() => onExport(fmt)} disabled={exporting}>
                {label}
              </button>
            ))}
          </div>
          {exportMsg && <p className="export-msg" role="status">{exportMsg}</p>}
        </div>
      </section>
    </div>
  );
}

/* ------------------------------------------------------------------ */
export default function Results({ result, outputs, edits, checks, setEdit, resetEdit, onExport, exporting, exportMsg }) {
  const [tab, setTab] = useState("linkedin");
  const [hover, setHover] = useState([]);
  const [pinned, setPinned] = useState(null);
  const [editing, setEditing] = useState(null);

  const usage = useMemo(() => {
    const map = {};
    const add = (ids, p) => ids.forEach((id) => (map[id] = Array.from(new Set([...(map[id] || []), p]))));
    outputs.linkedin.blocks.forEach((b) => add(b.sources, "linkedin"));
    outputs.instagram.blocks.forEach((b) => add(b.sources, "instagram"));
    outputs.instagram.slides.forEach((b) => add(b.sources, "instagram"));
    outputs.video.scenes.forEach((b) => add(b.sources, "video"));
    return map;
  }, [outputs]);

  // when a source line is pinned, jump to a tab that uses it
  useEffect(() => {
    if (!pinned) return;
    const used = usage[pinned] || [];
    if (used.length && !used.includes(tab)) setTab(used[0]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pinned]);

  const original = useMemo(() => {
    const map = {};
    ["linkedin", "instagram"].forEach((p) => result.outputs[p].blocks.forEach((b) => (map[b.id] = b)));
    return map;
  }, [result]);

  const ctx = {
    edits,
    checks,
    pinned,
    editing,
    setEditing,
    setHover,
    setEdit,
    blockProps: (b, platform) => ({
      block: b,
      text: b.text,
      issues: checks[b.id]?.issues ?? original[b.id]?.issues,
      editing: editing === b.id,
      edited: edits[b.id] !== undefined,
      highlighted: pinned && b.sources.includes(pinned),
      onEdit: () => setEditing(editing === b.id ? null : b.id),
      onChange: (v) => setEdit(b.id, v, platform, b.sources, "block"),
      onReset: () => resetEdit(b.id),
      onHover: setHover,
    }),
  };

  const s = result.summary;
  const ap = result.analysis.approval;
  return (
    <section className="results" id="results" aria-labelledby="results-h">
      <div className="results-head">
        <div>
          <h2 id="results-h">{result.analysis.title}</h2>
          <p className="stamp">
            Approved by {ap.approver}
            {ap.date ? `, ${new Date(ap.date + "T00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}` : ""}. Written in the{" "}
            {result.voice.label.toLowerCase()} voice.
          </p>
        </div>
        <dl className="stats">
          <div><dt>Source lines used</dt><dd>{s.segments_used}<small>/{s.segments_total}</small></dd></div>
          <div><dt>Figures carried over</dt><dd>{s.figures_used}<small>/{s.figures_total}</small></dd></div>
          <div><dt>Voice fixes</dt><dd>{s.voice_fixes}</dd></div>
          <div className={s.high_issues ? "is-bad" : ""}><dt>Flags</dt><dd>{s.issues}</dd></div>
        </dl>
      </div>

      <div className="results-grid">
        <SourcePanel analysis={result.analysis} usage={usage} hover={hover} pinned={pinned} setPinned={setPinned} />
        <div className="outputs">
          <div className="tabs" role="tablist" aria-label="Platform">
            {TABS.map((t) => (
              <button
                key={t.id}
                role="tab"
                id={`tab-${t.id}`}
                aria-selected={tab === t.id}
                aria-controls={`panel-${t.id}`}
                className={`tab tab-${t.id}${tab === t.id ? " is-active" : ""}`}
                onClick={() => setTab(t.id)}
              >
                {tab === t.id && <motion.span layoutId="tab-ink" className="tab-ink" transition={{ type: "spring", stiffness: 500, damping: 40 }} />}
                <span className="tab-label">{t.label}</span>
              </button>
            ))}
          </div>
          <motion.div
              key={tab}
              role="tabpanel"
              id={`panel-${tab}`}
              aria-labelledby={`tab-${tab}`}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.22 }}
            >
              {tab === "linkedin" && <LinkedInView out={outputs.linkedin} ctx={ctx} />}
              {tab === "instagram" && <InstagramView out={outputs.instagram} ctx={ctx} />}
              {tab === "video" && <VideoView out={outputs.video} ctx={ctx} />}
          </motion.div>
        </div>
      </div>

      <Checks result={result} outputs={outputs} checks={checks} onExport={onExport} exporting={exporting} exportMsg={exportMsg} />
    </section>
  );
}
