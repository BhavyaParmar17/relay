import { useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";

const NONE_LABEL = { hashtags: "tags", cta: "call to action", framing: "framing" };

export function Cites({ ids, kind }) {
  const real = (ids || []).filter(Boolean);
  if (!real.length)
    return (
      <span className="cite cite-none" title="Added by Relay. Contains no facts from the source.">
        {NONE_LABEL[kind] || "framing"}
      </span>
    );
  return real.map((id) => (
    <sup key={id} className="cite">
      {id === "T" ? "Title" : id}
    </sup>
  ));
}

export function Issues({ issues }) {
  if (!issues?.length) return null;
  return (
    <ul className="issues">
      {issues.map((x, i) => (
        <li key={i} className={`sev-${x.severity}`}>
          {x.message}
          {x.excerpt && <span className="excerpt"> {x.excerpt}</span>}
        </li>
      ))}
    </ul>
  );
}

function AutoTextarea(props) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight + 2}px`;
  }, [props.value]);
  return <textarea ref={ref} rows={1} {...props} />;
}

/** One traceable line: text, source chips, edit toggle and its issues. */
export function Block({ block, text, issues, editing, onEdit, onChange, onReset, onHover, highlighted, edited }) {
  return (
    <div
      className={`block kind-${block.kind}${highlighted ? " is-hl" : ""}${edited ? " is-edited" : ""}`}
      onMouseEnter={() => onHover(block.sources)}
      onMouseLeave={() => onHover([])}
      onFocus={() => onHover(block.sources)}
    >
      <div className="block-row">
        {editing ? (
          <AutoTextarea value={text} onChange={(e) => onChange(e.target.value)} aria-label={`Edit ${block.kind} line`} autoFocus />
        ) : (
          <p className="block-text">
            {text}
            <Cites ids={block.sources} kind={block.kind} />
          </p>
        )}
        <div className="block-tools">
          <button type="button" className="tool" onClick={onEdit} aria-pressed={editing}>
            {editing ? "Done" : "Edit"}
          </button>
          {edited && !editing && (
            <button type="button" className="tool" onClick={onReset}>
              Undo edit
            </button>
          )}
        </div>
      </div>
      <AnimatePresence initial={false}>
        {issues?.length > 0 && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }}>
            <Issues issues={issues} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function Meter({ label, value, limit, ok }) {
  return (
    <div className={`meter ${ok === false ? "is-bad" : ""}`}>
      <span className="meter-label">{label}</span>
      <span className="meter-value">
        {value}
        {limit !== undefined && <span className="meter-limit"> / {limit}</span>}
      </span>
    </div>
  );
}
