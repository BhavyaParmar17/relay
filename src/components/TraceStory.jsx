import { useLayoutEffect, useRef, useState } from "react";
import { useMotionValueEvent, useScroll, useSpring } from "framer-motion";

const SOURCE = [
  { id: "S4", text: "Its founder, Kavya Mehta, spent close to 9 hours a week chasing payments over phone and WhatsApp." },
  { id: "S5", text: "Average payment time had stretched to 38 days." },
  { id: "S9", text: "Reminders go out automatically 3 days before and 2 days after each due date." },
  { id: "S12", text: "Within one quarter, late payments fell by 41%." },
  { id: "S13", text: "Average payment time dropped from 38 days to 22 days." },
];
const POSTS = [
  {
    platform: "linkedin",
    name: "LinkedIn",
    lines: [
      { key: "l1", text: "Within one quarter, late payments fell by 41%.", src: "S12" },
      { key: "l2", text: "• Kavya spent close to 9 hours a week chasing payments…", src: "S4" },
      { key: "l3", text: "• Average payment time dropped from 38 days to 22 days.", src: "S13" },
    ],
  },
  {
    platform: "instagram",
    name: "Instagram carousel",
    lines: [
      { key: "i1", text: "Slide 2: 41%", src: "S12" },
      { key: "i2", text: "Slide 3: 38 days", src: "S5" },
    ],
  },
  {
    platform: "video",
    name: "Short video",
    lines: [
      { key: "v1", text: "0 to 3 s: Within one quarter, late payments fell by 41%.", src: "S12" },
      { key: "v2", text: "3 to 10 s: Reminders go out automatically…", src: "S9" },
    ],
  },
];
const LINKS = POSTS.flatMap((p) => p.lines.map((l) => ({ ...l, platform: p.platform })));

export default function TraceStory() {
  const section = useRef(null);
  const stage = useRef(null);
  const nodes = useRef({});
  const [paths, setPaths] = useState([]);
  const [progress, setProgress] = useState(0);
  const { scrollYProgress } = useScroll({ target: section, offset: ["start start", "end end"] });
  const smooth = useSpring(scrollYProgress, { stiffness: 120, damping: 28, mass: 0.4 });
  useMotionValueEvent(smooth, "change", (v) => setProgress(v));

  useLayoutEffect(() => {
    const measure = () => {
      const box = stage.current?.getBoundingClientRect();
      if (!box) return;
      setPaths(
        LINKS.map((link) => {
          const a = nodes.current[link.src]?.getBoundingClientRect();
          const b = nodes.current[link.key]?.getBoundingClientRect();
          if (!a || !b) return null;
          const x1 = a.right - box.left;
          const y1 = a.top + a.height / 2 - box.top;
          const x2 = b.left - box.left;
          const y2 = b.top + b.height / 2 - box.top;
          const mid = (x1 + x2) / 2;
          return { key: link.key, platform: link.platform, d: `M${x1},${y1} C${mid},${y1} ${mid},${y2} ${x2},${y2}` };
        })
      );
    };
    measure();
    const ro = new ResizeObserver(measure);
    if (stage.current) ro.observe(stage.current);
    window.addEventListener("resize", measure);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, []);

  // each link draws during its own slice of the scroll
  const start = 0.1;
  const span = 0.75 / LINKS.length;
  const amount = (i) => Math.max(0, Math.min(1, (progress - start - i * span) / span));
  const active = new Set(LINKS.filter((_, i) => amount(i) > 0.05).map((l) => l.src));
  const doneLines = new Set(LINKS.filter((_, i) => amount(i) > 0.95).map((l) => l.key));
  const count = doneLines.size;

  return (
    <section className="trace" id="trace" ref={section} aria-labelledby="trace-h">
      <div className="trace-sticky">
        <div className="trace-head">
          <h2 id="trace-h">Every line keeps its receipt</h2>
          <p>
            {count === 0
              ? "Scroll to follow each post line back to the approved sentence it came from."
              : `${count} of ${LINKS.length} post lines traced to the source.`}
          </p>
        </div>
        <div className="trace-stage" ref={stage}>
          <ol className="trace-source" aria-label="Approved source sentences">
            {SOURCE.map((s) => (
              <li key={s.id} ref={(el) => (nodes.current[s.id] = el)} className={active.has(s.id) ? "is-lit" : ""}>
                <span className="sid">{s.id}</span>
                <span>{s.text}</span>
              </li>
            ))}
          </ol>
          <div className="trace-posts">
            {POSTS.map((p) => (
              <div key={p.platform} className={`trace-post post-${p.platform}`}>
                <h3>{p.name}</h3>
                {p.lines.map((l) => (
                  <p key={l.key} ref={(el) => (nodes.current[l.key] = el)} className={doneLines.has(l.key) ? "is-done" : ""}>
                    {l.text}
                    <sup className="cite">{l.src}</sup>
                  </p>
                ))}
              </div>
            ))}
          </div>
          <svg className="trace-wires" aria-hidden="true">
            {paths.map((p, i) =>
              p ? (
                <path
                  key={p.key}
                  d={p.d}
                  className={`wire wire-${p.platform}`}
                  pathLength="1"
                  strokeDasharray="1"
                  strokeDashoffset={1 - amount(i)}
                />
              ) : null
            )}
          </svg>
        </div>
      </div>
    </section>
  );
}
