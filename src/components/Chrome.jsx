import { motion, useScroll, useSpring } from "framer-motion";

export function Logo({ size = 28 }) {
  return (
    <svg viewBox="0 0 32 32" width={size} height={size} aria-hidden="true">
      <rect width="32" height="32" rx="7" fill="var(--ink)" />
      <rect x="6" y="8" width="11" height="4" rx="1.5" fill="var(--mark)" />
      <rect x="6" y="15" width="8" height="3" rx="1.5" fill="#8D86A3" />
      <rect x="6" y="21" width="10" height="3" rx="1.5" fill="#8D86A3" />
      <path d="M17 10c5 0 4 12 9 12" stroke="var(--mark)" strokeWidth="2" fill="none" strokeLinecap="round" />
    </svg>
  );
}

export function TopBar() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 200, damping: 40 });
  return (
    <>
      <motion.div className="scroll-meter" style={{ scaleX }} aria-hidden="true" />
      <nav className="topbar" aria-label="Main">
        <a href="#top" className="brand">
          <Logo />
          <span>Relay</span>
        </a>
        <div className="topbar-links">
          <a href="#studio">Studio</a>
          <a href="#trace">Traceability</a>
          <a href="#rules">Platform rules</a>
        </div>
      </nav>
    </>
  );
}

export function Footer() {
  return (
    <footer className="footer">
      <div className="footer-brand">
        <Logo size={24} />
        <p>
          Relay only rewrites what it can trace. Figures and names come from your approved source, and every line can be checked against
          it before anything is published.
        </p>
      </div>
      <p className="footer-meta">Built with React, Framer Motion and a Flask API in Python.</p>
    </footer>
  );
}
