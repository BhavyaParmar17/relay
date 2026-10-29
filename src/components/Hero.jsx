import { motion, useScroll, useTransform } from "framer-motion";

const ease = [0.22, 1, 0.36, 1];
const LINE = "Within one quarter, late payments fell by 41%.";
const ROWS = [
  { platform: "linkedin", label: "LinkedIn hook" },
  { platform: "instagram", label: "Instagram caption" },
  { platform: "video", label: "Video, 0 to 3 s" },
];

export default function Hero({ onStart }) {
  const { scrollY } = useScroll();
  const y = useTransform(scrollY, [0, 600], [0, -50]);

  return (
    <header className="hero" id="top">
      <div className="hero-copy">
        <h1>
          {["Say it once.", "Post it three ways.", "Trace every line."].map((line, i) => (
            <span className="line" key={line}>
              <motion.span initial={{ y: "110%" }} animate={{ y: 0 }} transition={{ duration: 0.85, ease, delay: i * 0.09 }}>
                {line}
              </motion.span>
            </span>
          ))}
        </h1>
        <motion.p className="hero-lede" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5, duration: 0.6 }}>
          Relay takes an approved blog, case study or product page and writes a LinkedIn post, an Instagram caption and carousel, and a
          short-video script. It keeps the source’s facts, applies your brand voice and shows which source line each sentence came from.
        </motion.p>
        <motion.div className="hero-actions" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.62, duration: 0.6 }}>
          <button type="button" className="btn btn-primary" onClick={() => onStart("sample")}>Try it with a sample</button>
          <button type="button" className="btn btn-quiet" onClick={() => onStart("own")}>Paste my own source</button>
        </motion.div>
      </div>

      <motion.figure className="specimen" style={{ y }} aria-label="Example: one source sentence reused in three posts">
        <div className="specimen-source">
          <span className="sid">S12</span>
          <p>
            <motion.span
              className="hl-text"
              initial={{ backgroundSize: "0% 100%" }}
              animate={{ backgroundSize: "100% 100%" }}
              transition={{ delay: 0.75, duration: 0.9, ease }}
            >
              {LINE}
            </motion.span>
          </p>
          <small>From the approved case study</small>
        </div>
        <div className="specimen-tail">
        <svg className="specimen-wires" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          {[17, 50, 83].map((end, i) => (
            <motion.path
              key={end}
              d={`M20 0 C 20 ${end * 0.75}, 40 ${end}, 100 ${end}`}
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ delay: 1.2 + i * 0.18, duration: 0.6, ease }}
              vectorEffect="non-scaling-stroke"
            />
          ))}
        </svg>
        <ul className="specimen-rows">
          {ROWS.map((r, i) => (
            <motion.li
              key={r.platform}
              className={`row-${r.platform}`}
              initial={{ opacity: 0, x: 14 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 1.35 + i * 0.18, duration: 0.5, ease }}
            >
              <span className="row-label">{r.label}</span>
              <span className="row-text">
                {LINE}
                <sup className="cite">S12</sup>
              </span>
            </motion.li>
          ))}
        </ul>
        </div>
      </motion.figure>
    </header>
  );
}
