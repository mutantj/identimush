// Identimush v1: multiple-choice mushroom ID game.
// Data: data/species.json (features) + photos/photos.json (from fetch_photos.py)

// ---- Level design ---------------------------------------------------------
// mode: "common" or "latin" name buttons
// distractors: "random" picks any species; "lookalike" includes the species' lookalikes
// toNext: correct answers needed to level up
const LEVELS = [
  { mode: "common", choices: 3, distractors: "random",    toNext: 5 },
  { mode: "common", choices: 4, distractors: "random",    toNext: 5 },
  { mode: "common", choices: 4, distractors: "lookalike", toNext: 6 },
  { mode: "latin",  choices: 3, distractors: "random",    toNext: 6 },
  { mode: "latin",  choices: 4, distractors: "random",    toNext: 6 },
  { mode: "latin",  choices: 4, distractors: "lookalike", toNext: Infinity },
];

const FEATURE_LABELS = {
  cap: "Cap",
  underside: "Underside",
  stipe: "Stipe",
  sporePrint: "Spore print",
  habitat: "Habitat",
  other: "Also",
};

const TOXICITY_LABELS = {
  "edible": "Edible",
  "edible-caution": "Edible with caution",
  "inedible": "Inedible",
  "toxic": "Poisonous",
  "deadly": "Deadly",
};

const SAVE_KEY = "identimush-v1";

// ---- State ----------------------------------------------------------------
let species = [];          // species that have at least one photo
let byId = {};
let current = null;        // species being asked
let lastId = null;
let state = loadState();

function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(SAVE_KEY));
    if (saved) return saved;
  } catch (e) { /* ignore broken save */ }
  return { level: 1, progress: 0, correct: 0, answered: 0, misses: {} };
}

function saveState() {
  try { localStorage.setItem(SAVE_KEY, JSON.stringify(state)); } catch (e) { /* storage off */ }
}

// ---- Helpers --------------------------------------------------------------
const $ = (id) => document.getElementById(id);

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const c of children) node.append(c);
  return node;
}

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function levelConfig() {
  return LEVELS[Math.min(state.level, LEVELS.length) - 1];
}

function nameNode(sp, mode) {
  return mode === "latin"
    ? el("span", { class: "latin" }, sp.latin)
    : document.createTextNode(sp.common);
}

function shortLicence(url = "") {
  const u = url.toLowerCase();
  if (u.includes("publicdomain") || u.includes("cc0")) return "CC0";
  const m = u.match(/licenses\/([a-z-]+)\/([\d.]+)/);
  return m ? `CC ${m[1].toUpperCase()} ${m[2]}` : "CC licence";
}

// ---- Loading --------------------------------------------------------------
async function loadData() {
  const [spRes, phRes] = await Promise.all([
    fetch("data/species.json"),
    fetch("photos/photos.json"),
  ]);
  if (!spRes.ok) throw new Error("Couldn't load data/species.json.");
  if (!phRes.ok) throw new Error("Couldn't load photos/photos.json. Run fetch_photos.py and put the photos folder next to index.html.");

  const all = await spRes.json();
  const photos = await phRes.json();

  for (const sp of all) {
    sp.photos = (photos[sp.id] && photos[sp.id].photos) || [];
    byId[sp.id] = sp;
  }
  species = all.filter((sp) => sp.photos.length > 0);
  if (species.length < 4) throw new Error("Fewer than 4 species have photos. Check the photos folder.");
}

// ---- Picking questions ----------------------------------------------------
function pickSpecies() {
  // Species you've missed come up more often.
  const pool = species.filter((sp) => sp.id !== lastId);
  const weights = pool.map((sp) => 1 + 2 * (state.misses[sp.id] || 0));
  let r = Math.random() * weights.reduce((a, b) => a + b, 0);
  for (let i = 0; i < pool.length; i++) {
    r -= weights[i];
    if (r <= 0) return pool[i];
  }
  return pool[pool.length - 1];
}

function buildChoices(target, cfg) {
  const picked = [target];
  if (cfg.distractors === "lookalike") {
    for (const l of target.lookalikes || []) {
      const sp = byId[l.id];
      if (sp && sp.photos.length && picked.length < cfg.choices) picked.push(sp);
    }
  }
  for (const sp of shuffle(species)) {
    if (picked.length >= cfg.choices) break;
    if (!picked.includes(sp)) picked.push(sp);
  }
  return shuffle(picked);
}

// ---- Rendering ------------------------------------------------------------
function showPhoto(photo) {
  $("photo").src = `photos/${photo.file}`;
  const credit = $("credit");
  credit.replaceChildren(
    `Photo by ${photo.creator}, ${shortLicence(photo.license)}. `,
    el("a", { href: photo.source, target: "_blank", rel: "noopener" }, "Source")
  );
}

function renderQuestion() {
  const cfg = levelConfig();
  current = pickSpecies();
  lastId = current.id;

  // Up to 3 photos of this species, shuffled.
  const photos = shuffle(current.photos).slice(0, 3);
  showPhoto(photos[0]);
  const thumbs = $("thumbs");
  thumbs.replaceChildren();
  if (photos.length > 1) {
    photos.forEach((p, i) => {
      const btn = el("button", {
        "aria-label": `Photo ${i + 1}`,
        "aria-pressed": i === 0 ? "true" : "false",
        onclick: () => {
          showPhoto(p);
          thumbs.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", "false"));
          btn.setAttribute("aria-pressed", "true");
        },
      }, el("img", { src: `photos/${p.file}`, alt: "" }));
      thumbs.append(btn);
    });
  }

  $("prompt").textContent = cfg.mode === "latin" ? "Which species is this?" : "What is this?";

  const choices = $("choices");
  choices.replaceChildren();
  for (const sp of buildChoices(current, cfg)) {
    choices.append(el("button", {
      class: "choice",
      "data-id": sp.id,
      onclick: () => answer(sp),
    }, nameNode(sp, cfg.mode)));
  }

  $("feedback").hidden = true;
  updateTopbar();
}

function renderFeedback(chosen, correct) {
  const cfg = levelConfig();
  const fb = $("feedback");
  fb.replaceChildren();

  const heading = correct
    ? el("h3", { class: "result-correct" }, "Correct: ", nameNode(current, "common"))
    : el("h3", { class: "result-wrong" }, "Not quite. This is ", nameNode(current, "common"));
  fb.append(heading, el("div", { class: "latin" }, current.latin));
  fb.append(el("span", { class: `badge ${current.toxicity}` }, TOXICITY_LABELS[current.toxicity] || current.toxicity));

  // Why it's this species
  const dl = el("dl", { class: "features" });
  for (const [key, label] of Object.entries(FEATURE_LABELS)) {
    if (current.features[key]) dl.append(el("dt", {}, label), el("dd", {}, current.features[key]));
  }
  fb.append(dl);

  // Why not the one you picked
  if (!correct) {
    const tell =
      (current.lookalikes || []).find((l) => l.id === chosen.id)?.tell ||
      (chosen.lookalikes || []).find((l) => l.id === current.id)?.tell;
    const box = el("div", { class: "why-not" }, el("h4", {}, "Why not ", nameNode(chosen, cfg.mode), "?"));
    if (tell) {
      box.append(el("p", {}, tell));
    } else {
      box.append(el("p", {},
        `${chosen.common} has: ${chosen.features.cap.toLowerCase()}; underside: ${chosen.features.underside.toLowerCase()}.`));
    }
    fb.append(box);
  }

  fb.append(el("button", { class: "primary", onclick: renderQuestion }, "Next mushroom"));
  fb.hidden = false;
  fb.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
}

function updateTopbar() {
  const cfg = levelConfig();
  $("level-label").textContent = `Level ${state.level}`;
  const pct = cfg.toNext === Infinity ? 100 : Math.min(100, (state.progress / cfg.toNext) * 100);
  $("progress-fill").style.width = `${pct}%`;
}

function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (t.hidden = true), 3500);
}

// ---- Answering ------------------------------------------------------------
function answer(chosen) {
  const correct = chosen.id === current.id;

  document.querySelectorAll(".choice").forEach((b) => {
    b.disabled = true;
    if (b.dataset.id === current.id) b.classList.add("correct");
    else if (b.dataset.id === chosen.id) b.classList.add("wrong");
  });

  state.answered++;
  if (correct) {
    state.correct++;
    state.progress++;
    if (state.misses[current.id]) state.misses[current.id]--;
  } else {
    state.progress = Math.max(0, state.progress - 1);
    state.misses[current.id] = (state.misses[current.id] || 0) + 1;
  }

  const cfg = levelConfig();
  if (state.progress >= cfg.toNext && state.level < LEVELS.length) {
    state.level++;
    state.progress = 0;
    const next = levelConfig();
    toast(next.mode === "latin" && cfg.mode === "common"
      ? `Level ${state.level}: Latin names from now on`
      : `Level ${state.level} reached`);
  }

  saveState();
  updateTopbar();
  renderFeedback(chosen, correct);
}

// ---- Start ----------------------------------------------------------------
function showError(msg) {
  $("start").hidden = true;
  $("question").hidden = true;
  const err = $("error");
  err.replaceChildren(el("h2", {}, "Something's missing"), el("p", {}, msg));
  err.hidden = false;
}

$("start-btn").addEventListener("click", async () => {
  try {
    if (!species.length) await loadData();
    $("start").hidden = true;
    $("question").hidden = false;
    renderQuestion();
  } catch (e) {
    showError(e.message);
  }
});

$("reset-btn").addEventListener("click", () => {
  if (!confirm("Reset your level and progress?")) return;
  state = { level: 1, progress: 0, correct: 0, answered: 0, misses: {} };
  saveState();
  updateTopbar();
  toast("Progress reset");
});

updateTopbar();
