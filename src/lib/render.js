// Mirrors the server's rendering so edited blocks produce the same layout.
export function renderLinkedIn(blocks) {
  const out = [];
  let prev = null;
  blocks.forEach((b) => {
    const joined = (prev === "point" && b.kind === "point") || (prev === "framing" && b.kind === "point");
    if (prev && !joined) out.push("");
    out.push(b.text);
    prev = b.kind;
  });
  return out.join("\n");
}

export function renderCaption(blocks) {
  return blocks.map((b) => b.text).join("\n\n");
}

export function renderScript(scenes) {
  return scenes
    .map((s) => `[${s.start}–${s.end}s] ${s.label.toUpperCase()}\nOn screen: ${s.on_screen}\nVoiceover: ${s.voiceover}\nVisual: ${s.visual}`)
    .join("\n\n");
}

export function renderCarousel(slides) {
  return slides.map((s, i) => `Slide ${i + 1}: ${s.headline}\n${s.body}`).join("\n\n");
}

/** Apply a map of edits {id: text | {headline, body} | {voiceover, on_screen}} to outputs. */
export function applyEdits(outputs, edits) {
  if (!outputs) return outputs;
  const pick = (id, fallback) => (edits[id] !== undefined ? edits[id] : fallback);
  const li = outputs.linkedin.blocks.map((b) => ({ ...b, text: pick(b.id, b.text) }));
  const ig = outputs.instagram.blocks.map((b) => ({ ...b, text: pick(b.id, b.text) }));
  const slides = outputs.instagram.slides.map((s) => ({ ...s, ...(edits[s.id] || {}) }));
  const scenes = outputs.video.scenes.map((s) => ({ ...s, ...(edits[s.id] || {}) }));
  return {
    linkedin: { ...outputs.linkedin, blocks: li, text: renderLinkedIn(li) },
    instagram: { ...outputs.instagram, blocks: ig, slides, text: renderCaption(ig) },
    video: { ...outputs.video, scenes, text: scenes.map((s) => s.voiceover).join("\n") },
  };
}
