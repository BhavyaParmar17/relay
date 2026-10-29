const RULES = [
  {
    platform: "LinkedIn",
    cls: "linkedin",
    items: [
      ["3,000 characters", "Maximum post length. Relay reports the count as you edit."],
      ["About 210 characters", "Shown before “see more”, so the opening line carries the strongest source figure."],
      ["Three to five hashtags", "Brand tags first, then tags drawn from the source’s own keywords."],
    ],
  },
  {
    platform: "Instagram",
    cls: "instagram",
    items: [
      ["2,200 characters", "Maximum caption length."],
      ["125 characters", "Visible before the caption is cut off, so the hook is chosen to fit."],
      ["Five hashtags", "Instagram’s limit since December 2025, across caption and comments together."],
    ],
  },
  {
    platform: "Short video",
    cls: "video",
    items: [
      ["25 to 50 seconds", "Target length for Reels, Shorts and TikTok. Longer scripts drop middle scenes first."],
      ["2.5 words a second", "Speaking pace used to time each scene from its voiceover."],
      ["Hook in 3 seconds", "The first scene leads with a result or figure from the source."],
    ],
  },
];

export default function Rules() {
  return (
    <section className="rules" id="rules" aria-labelledby="rules-h">
      <div className="rules-intro">
        <h2 id="rules-h">The platform rules Relay writes to</h2>
        <p>Limits checked against platform help pages and 2026 guidance. Relay flags a post the moment an edit breaks one.</p>
      </div>
      <div className="rules-grid">
        {RULES.map((r) => (
          <div key={r.platform} className={`rule-col rule-${r.cls}`}>
            <h3>{r.platform}</h3>
            <dl>
              {r.items.map(([k, v]) => (
                <div key={k}>
                  <dt>{k}</dt>
                  <dd>{v}</dd>
                </div>
              ))}
            </dl>
          </div>
        ))}
      </div>
    </section>
  );
}
