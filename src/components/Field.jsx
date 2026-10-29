import { forwardRef, useId } from "react";
import { motion } from "framer-motion";

export const Field = forwardRef(function Field({ label, hint, error, as = "input", optional, className = "", ...props }, ref) {
  const id = useId();
  const Tag = as;
  const describedBy = hint || error ? `${id}-d` : undefined;
  return (
    <div className={`field ${error ? "has-error" : ""} ${className}`}>
      <label htmlFor={id}>
        <span>{label}</span>
        {optional && <span className="optional">optional</span>}
      </label>
      <Tag ref={ref} id={id} aria-invalid={Boolean(error)} aria-describedby={describedBy} {...props} />
      {(error || hint) && (
        <p id={describedBy} className={error ? "field-error" : "field-hint"}>
          {error || hint}
        </p>
      )}
    </div>
  );
});

export function Segmented({ options, value, onChange, name }) {
  return (
    <div className="segmented" role="radiogroup" aria-label={name}>
      {options.map((o) => {
        const active = o.value === value;
        return (
          <button key={o.value} type="button" role="radio" aria-checked={active} className={active ? "is-active" : ""} onClick={() => onChange(o.value)}>
            {active && <motion.span layoutId={`seg-${name}`} className="seg-pill" transition={{ type: "spring", stiffness: 500, damping: 40 }} />}
            <span className="seg-label">{o.label}</span>
          </button>
        );
      })}
    </div>
  );
}
