const STEPS = [
  ["Approve", "Confirm the source is signed off and who approved it."],
  ["Extract", "Every sentence gets a number. Figures, names and quotes go into a fact ledger."],
  ["Voice", "Preferred terms, banned words, contractions and emoji rules are applied."],
  ["Write", "LinkedIn, Instagram and a timed video script are built from source lines."],
  ["Check", "Edits are re-checked against the source, then exported with traceability."],
];

export default function Steps() {
  return (
    <section className="steps" aria-labelledby="steps-h">
      <h2 id="steps-h" className="sr-only">How Relay works</h2>
      <ol>
        {STEPS.map(([name, text], i) => (
          <li key={name}>
            <span className="step-n">{i + 1}</span>
            <strong>{name}</strong>
            <p>{text}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
