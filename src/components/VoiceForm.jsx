import { Field } from "./Field.jsx";

const SAMPLE_LINE = {
  expert: "The takeaway: clear terms do not need to be awkward.",
  friendly: "The big takeaway? Clear terms don't need to be awkward. 👉",
  bold: "Bottom line: clear terms don't need to be awkward.",
};

export default function VoiceForm({ brand, setBrand, presets }) {
  const set = (key) => (e) => setBrand((b) => ({ ...b, [key]: e.target.type === "checkbox" ? e.target.checked : e.target.value }));
  return (
    <div className="panel voice-form">
      <div className="panel-head">
        <h3>Brand voice</h3>
      </div>
      <fieldset className="voice-presets">
        <legend className="label-like">Voice</legend>
        {presets.map((p) => (
          <label key={p.id} className={`voice-option ${brand.preset === p.id ? "is-on" : ""}`}>
            <input type="radio" name="preset" value={p.id} checked={brand.preset === p.id} onChange={set("preset")} />
            <span className="voice-name">{p.label}</span>
            <span className="voice-desc">{p.description}</span>
            <span className="voice-sample">{SAMPLE_LINE[p.id]}</span>
          </label>
        ))}
      </fieldset>
      <div className="two">
        <Field label="Brand name" value={brand.brand_name} onChange={set("brand_name")} placeholder="Ledgerly" />
        <Field label="Brand hashtags" value={brand.hashtags} onChange={set("hashtags")} placeholder="#Ledgerly" hint="Up to three, used first." optional />
      </div>
      <Field label="Call to action" value={brand.cta} onChange={set("cta")} placeholder="Read the full case study" optional />
      <Field
        as="textarea"
        rows={3}
        label="Preferred terms"
        value={brand.preferred_terms}
        onChange={set("preferred_terms")}
        placeholder={"customers -> clients\nsoftware -> platform"}
        hint="One per line. Relay swaps these everywhere except links and hashtags."
        optional
      />
      <Field label="Banned words" value={brand.banned_words} onChange={set("banned_words")} placeholder="cheap, guarantee" hint="Comma separated. Flagged for you to rewrite." optional />
      <label className="check">
        <input type="checkbox" checked={brand.avoid_hype} onChange={set("avoid_hype")} />
        <span>Flag hype words like “game-changer” and “unlock”</span>
      </label>
    </div>
  );
}
