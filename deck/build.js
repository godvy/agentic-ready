// Builds the Agentic Ready pitch deck (6 slides). Screenshots go in ./shots; missing ones render as labelled placeholders.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const fa = require("react-icons/fa6");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");

const OUT = path.resolve(__dirname, "..", "submission", "AgenticReady_Deck.pptx");
const SHOTS = path.join(__dirname, "shots");

const THEME = {
  name: "Agentic Ready",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1C1B19", lt1: "FFFFFF", dk2: "16263A", lt2: "F2F4F7",
    accent1: "2B4A6F", accent2: "C2553B", accent3: "2F6B4F", accent4: "B8C4D4",
    accent5: "6B7280", accent6: "DCE2EA", hlink: "2B4A6F", folHlink: "6B7280",
  },
};
const HEX = THEME.colors;
const W = 13.333, H = 7.5, M = 0.6;

async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  return "image/png;base64," + (await sharp(Buffer.from(svg)).png().toBuffer()).toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.title = "Agentic Ready";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;

  pres.defineSlideMaster({
    title: "DARK",
    background: { color: C.text2 },
    objects: [{ placeholder: { options: { name: "title", type: "title", x: M, y: 0.55, w: 6.4, h: 0.85, fontSize: 40, bold: true,
      color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } }],
  });
  pres.defineSlideMaster({
    title: "CONTENT",
    background: { color: C.background1 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: M, y: 0.45, w: W - 2 * M, h: 0.85, fontSize: 32, bold: true,
        color: C.text2, valign: "middle", align: "left", margin: 0 }, text: "" } },
      { text: { text: "Agentic Ready", options: { x: M, y: H - 0.45, w: 3, h: 0.3, fontSize: 10, color: C.accent5, margin: 0 } } },
    ],
    slideNumber: { x: W - M - 0.5, y: H - 0.45, w: 0.5, h: 0.3, fontSize: 10, color: C.accent5, align: "right" },
  });

  let s;
  const label = (text, x, y, w, color, name) => s.addText(text, { x, y, w, h: 0.3, fontSize: 11, bold: true, charSpacing: 2, color, margin: 0, isTextBox: true, objectName: name });
  const text = (t, o) => s.addText(t, { margin: 0, isTextBox: true, valign: "top", ...o });
  const circleIcon = async (Comp, x, y, d, fill, name) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" }, objectName: name + " bg" });
    s.addImage({ data: await icon(Comp, "FFFFFF"), x: x + d * 0.25, y: y + d * 0.25, w: d * 0.5, h: d * 0.5, objectName: name });
  };
  // screenshot fitted into a box, or a labelled placeholder until the file exists
  const shot = async (file, x, y, w, h, name, dark) => {
    const p = path.join(SHOTS, file);
    if (fs.existsSync(p)) {
      const { width, height } = await sharp(p).metadata();
      const k = Math.min(w / width, h / height), iw = width * k, ih = height * k;
      s.addImage({ path: p, x: x + (w - iw) / 2, y: y + (h - ih) / 2, w: iw, h: ih, objectName: name, altText: name,
        shadow: { type: "outer", color: "16263A", opacity: 0.18, blur: 12, offset: 3, angle: 90 } });
    } else {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.1, fill: { color: dark ? C.accent1 : C.background2 },
        line: { color: dark ? HEX.accent4 : HEX.accent5, width: 1, dashType: "dash" }, objectName: name + " placeholder" });
      text(`Screenshot: ${name}`, { x: x + 0.2, y, w: w - 0.4, h, fontSize: 13, italic: true, align: "center", valign: "middle",
        color: dark ? C.accent4 : C.accent5, objectName: name + " placeholder text" });
    }
  };

  // ---------- 1. Title & problem ----------
  pres.addSection({ title: "Problem" });
  s = pres.addSlide({ masterName: "DARK", sectionTitle: "Problem" });
  s.addText("Agentic Ready", { placeholder: "title" });
  text("UserTesting for the agentic web", { x: M, y: 1.4, w: 6.4, h: 0.45, fontSize: 22, color: C.accent4, objectName: "Subtitle" });
  text("We make sure AI agents can understand and act on your product documentation",
    { x: M, y: 2.3, w: 6.0, h: 1.6, fontFace: THEME.headFontFace, fontSize: 26, color: C.background1, objectName: "Hook" });
  const problems = [
    [fa.FaComments, "The shift", "Developers paste docs links into Cursor, Copilot and Claude instead of reading them"],
    [fa.FaEyeSlash, "The failure", "Docs are built for human eyes: key steps sit in tooltips, screenshots and scattered text"],
    [fa.FaTriangleExclamation, "The cost", "Agents miss that context and hallucinate broken steps. The developer assumes the product is broken and leaves"],
  ];
  label("THE AI INTEGRATION GAP", 7.3, 0.62, 5.4, C.accent4, "Problem label");
  for (let i = 0; i < problems.length; i++) {
    const y = 1.05 + i * 1.95;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.3, y, w: W - M - 7.3, h: 1.7, rectRadius: 0.12, fill: { color: C.accent1 }, line: { type: "none" }, objectName: `Problem ${i + 1} card` });
    await circleIcon(problems[i][0], 7.6, y + 0.3, 0.55, i === 2 ? C.accent2 : C.text2, `Problem icon ${i + 1}`);
    text([{ text: problems[i][1], options: { bold: true, fontSize: 17, breakLine: true } }, { text: problems[i][2], options: { fontSize: 15 } }],
      { x: 8.4, y: y + 0.22, w: W - M - 8.4 - 0.3, h: 1.3, color: C.background1, objectName: `Problem ${i + 1}` });
  }
  text([{ text: "Impact  ", options: { bold: true, color: C.accent4 } }, { text: "Less integration friction, fewer developer drop-offs, faster customer onboarding" }],
    { x: M, y: 6.0, w: 6.2, h: 0.75, fontSize: 15, color: C.background1, objectName: "Impact" });
  s.addNotes("Agentic Ready is UserTesting for the agentic web. Developers no longer read docs top to bottom: they paste a link into Cursor, Copilot or Claude. " +
    "But docs are designed for eyes: the token setting is in a tooltip, the login command is in a screenshot. The agent never sees those, " +
    "fills the gap by guessing, the setup fails, and the developer decides the product is broken.");

  // ---------- 2. Insight ----------
  pres.addSection({ title: "Insight" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Insight" });
  s.addText("The era of AI Optimization (AIO)", { placeholder: "title" });
  // SEO -> AIO
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M, y: 1.6, w: 2.75, h: 1.05, rectRadius: 0.1, fill: { color: C.background2 }, line: { type: "none" }, objectName: "SEO box" });
  text([{ text: "SEO", options: { bold: true, fontSize: 18, breakLine: true } }, { text: "pages crawlers can read", options: { fontSize: 13 } }],
    { x: M + 0.25, y: 1.6, w: 2.3, h: 1.05, valign: "middle", color: C.text2, objectName: "SEO text" });
  s.addShape(pres.shapes.LINE, { x: M + 2.85, y: 2.125, w: 0.45, h: 0, line: { color: HEX.accent5, width: 1.75, endArrowType: "triangle" }, objectName: "SEO to AIO arrow" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M + 3.4, y: 1.6, w: 2.75, h: 1.05, rectRadius: 0.1, fill: { color: C.accent1 }, line: { type: "none" }, objectName: "AIO box" });
  text([{ text: "AIO", options: { bold: true, fontSize: 18, breakLine: true } }, { text: "docs agents can act on", options: { fontSize: 13 } }],
    { x: M + 3.65, y: 1.6, w: 2.3, h: 1.05, valign: "middle", color: C.background1, objectName: "AIO text" });
  const insight = [
    ["THE RISK", "If an AI assistant can't parse your docs, your product fails at the very first step of implementation"],
    ["THE NEED", "DevEx, product and docs teams need a measurable, automated way to see how well agents use their docs, before a developer tries"],
    ["WHY ME", "I work directly with customers implementing products. I see every day where instructions break, and more often now the reader is an AI assistant"],
  ];
  for (let i = 0; i < insight.length; i++) {
    const y = 3.0 + i * 1.15;
    label(insight[i][0], M, y, 3, C.accent1, `${insight[i][0]} label`);
    text(insight[i][1], { x: M, y: y + 0.32, w: 6.15, h: 0.75, fontSize: 14, color: C.text1, objectName: `${insight[i][0]} text` });
  }
  const stats = [["75 vs 53", "Same page, same task, two agents: one fetching raw HTML, one using reader mode like most assistants", C.accent1],
    ["+47", "points when the same facts are written as plain text instead of tooltips and screenshots", C.accent3]];
  for (let i = 0; i < stats.length; i++) {
    const y = 1.6 + i * 2.55;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.35, y, w: W - M - 7.35, h: 2.25, rectRadius: 0.12, fill: { color: C.background2 }, line: { type: "none" }, objectName: `Stat card ${i + 1}` });
    text(stats[i][0], { x: 7.7, y: y + 0.3, w: 4.6, h: 0.95, fontFace: THEME.headFontFace, fontSize: 54, bold: true, color: stats[i][2], objectName: `Stat ${i + 1}` });
    text(stats[i][1], { x: 7.7, y: y + 1.35, w: 4.6, h: 0.75, fontSize: 14, color: C.text1, objectName: `Stat label ${i + 1}` });
  }
  s.addNotes("Twenty years ago companies learned to make pages readable for search crawlers. Now the reader is an agent, and it needs AIO: AI Optimization. " +
    "Agents don't read like humans, and they don't all read alike. On our sample guide, an agent fetching raw HTML scored 75; a reader-mode agent, which is how most assistants read pages, scored 53. " +
    "Writing the same facts as plain text took it to 100. Nobody measures this today. I see this gap every day working with customers who are implementing products.");

  // ---------- 3. Solution ----------
  pres.addSection({ title: "Solution" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Solution" });
  s.addText("Automated agent usability testing", { placeholder: "title" });
  text("Three agents read your page the way real assistants fetch it (reader mode, llms.txt, raw HTML) and attempt a task using only what they received",
    { x: M, y: 1.35, w: W - 2 * M, h: 0.5, fontSize: 15, color: C.accent5, objectName: "Simulation line" });
  const cols = [
    ["1  INPUT", "01_audit_input.png", "the Audit a page form", "Any technical docs URL (APIs, SDKs, CLIs, deployment guides) and a task: a how-to question, or a job for the agent to do itself"],
    ["2  AIO SCORE", "02_scores.png", "the two score cards", "A 0 to 100 score per agent. Typical guide 53, the same facts written as plain text 100"],
    ["3  DIAGNOSIS", "03_failures.png", "the failure cards", "Every failure with its cause, the evidence and the exact fix, e.g. \"a required CLI flag was only shown in a screenshot\""],
  ];
  const cW = (W - 2 * M - 2 * 0.35) / 3;
  for (let i = 0; i < cols.length; i++) {
    const x = M + i * (cW + 0.35);
    label(cols[i][0], x, 2.05, cW, C.accent1, `${cols[i][0]} label`);
    if (i < 2) {
      await shot(cols[i][1], x, 2.45, cW, 2.85, cols[i][2]);
    } else {
      // a real finding from the sample audit, set as a card instead of a screenshot
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.45, w: cW, h: 2.85, rectRadius: 0.1, fill: { color: C.background2 }, line: { type: "none" }, objectName: "Finding card" });
      text([
        { text: "MAJOR   ", options: { bold: true, fontSize: 11, color: C.accent2, charSpacing: 2 } },
        { text: "The agent invented ‘ducktape connect’ instead of the real login command", options: { bold: true, fontSize: 14, color: C.text1, breakLine: true } },
        { text: "Visible to humans, hidden from this agent", options: { fontSize: 12, color: C.accent5, breakLine: true } },
        { text: " ", options: { fontSize: 6, breakLine: true } },
        { text: "Fix  ", options: { bold: true, fontSize: 13, color: C.accent3 } },
        { text: "Show the command as text: ducktape login --workspace <name> --region eu-west", options: { fontSize: 13, color: C.text1 } },
      ], { x: x + 0.3, y: 2.65, w: cW - 0.6, h: 2.45, paraSpaceAfter: 4, objectName: "Finding text" });
    }
    text(cols[i][3], { x, y: 5.5, w: cW, h: 1.2, fontSize: 14, color: C.text1, objectName: `${cols[i][0]} text` });
  }
  s.addNotes("Live demo here. Paste any technical docs URL and a task. Three agents read the page the way real assistants fetch it and attempt the task. " +
    "A judge scores each attempt: our typical sample guide scores 53, the agent-ready version 100. Every failure says what broke, why, where the real answer was hiding, and the sentence to add.");

  // ---------- 4. Tech & trust ----------
  pres.addSection({ title: "Technology" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Technology" });
  s.addText("Three ways to read a page. One strict judge", { placeholder: "title" });
  const box = (t, sub, x, y, w, h, fill, color, name) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.1, fill: { color: fill }, line: { type: "none" }, objectName: name });
    text([{ text: t, options: { bold: true, fontSize: 15, breakLine: true } }, { text: sub, options: { fontSize: 11 } }],
      { x: x + 0.12, y, w: w - 0.24, h, color, valign: "middle", align: "center", objectName: name + " text" });
  };
  const arrow = (x1, y1, x2, y2, name) => s.addShape(pres.shapes.LINE, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.001, h: Math.abs(y2 - y1) || 0.001,
    flipV: y2 < y1, line: { color: HEX.accent5, width: 1.5, endArrowType: "triangle" }, objectName: name });
  const top = 2.05, rowH = 0.78, gap = 0.22, midY = top + (3 * rowH + 2 * gap) / 2;
  const views = [["Raw HTML", "naive fetch"], ["Reader mode", "most assistants"], ["llms.txt", "AI-friendly docs"]];
  box("Docs page", "URL or pasted", M, midY - 0.55, 1.75, 1.1, C.text2, C.background1, "Docs page");
  for (let i = 0; i < 3; i++) {
    const y = top + i * (rowH + gap);
    box(views[i][0], views[i][1], 3.0, y, 2.15, rowH, C.background2, C.text2, `View ${views[i][0]}`);
    box("Agent", "gpt-4.1-mini", 5.75, y, 2.0, rowH, C.background2, C.text2, `Agent ${i + 1}`);
    arrow(M + 1.75, midY, 3.0, y + rowH / 2, `Arrow page to view ${i + 1}`);
    arrow(5.15, y + rowH / 2, 5.75, y + rowH / 2, `Arrow view to agent ${i + 1}`);
    arrow(7.75, y + rowH / 2, 8.4, midY, `Arrow agent ${i + 1} to judge`);
  }
  box("Judge", "gpt-4.1 · sees the full page as humans do", 8.4, midY - 0.85, 2.1, 1.7, C.accent1, C.background1, "Judge");
  box("AIO Score", "cause and fix for every failure", 11.0, midY - 0.7, 1.73, 1.4, C.accent3, C.background1, "Output");
  arrow(10.5, midY, 11.0, midY, "Arrow judge to output");
  const gy = 1.62;
  s.addShape(pres.shapes.LINE, { x: M + 0.875, y: gy, w: 0, h: midY - 0.55 - gy, line: { color: HEX.accent2, width: 1.5, dashType: "dash" }, objectName: "Ground truth up" });
  s.addShape(pres.shapes.LINE, { x: M + 0.875, y: gy, w: 9.45 - (M + 0.875), h: 0, line: { color: HEX.accent2, width: 1.5, dashType: "dash" }, objectName: "Ground truth across" });
  s.addShape(pres.shapes.LINE, { x: 9.45, y: gy, w: 0, h: midY - 0.85 - gy, line: { color: HEX.accent2, width: 1.5, dashType: "dash", endArrowType: "triangle" }, objectName: "Ground truth down" });
  text("Ground truth: tooltips, hidden tabs, screenshots and scripts the agents never saw",
    { x: 3.0, y: gy - 0.33, w: 6.3, h: 0.3, fontSize: 12, italic: true, color: C.accent2, objectName: "Ground truth label" });
  const trust = [
    [fa.FaShieldHalved, "MODELS & PRIVACY", "OpenAI gpt-4.1-mini agents, gpt-4.1 judge. Only the submitted page is processed; nothing is used for training"],
    [fa.FaLock, "GUARDRAILS", "Agents must use only their fetched text and flag every guess. Generated steps are never executed"],
    [fa.FaMagnifyingGlass, "TRANSPARENT", "See what each agent saw, what it produced, and the evidence behind every finding. Scores computed in code"],
    [fa.FaUserCheck, "HUMAN IN THE LOOP", "The report is advisory. Docs and DevEx teams review the evidence and decide what to fix"],
  ];
  const tW = (W - 2 * M - 3 * 0.3) / 4;
  for (let i = 0; i < trust.length; i++) {
    const x = M + i * (tW + 0.3);
    await circleIcon(trust[i][0], x, 5.15, 0.42, C.accent1, `${trust[i][1]} icon`);
    label(trust[i][1], x + 0.55, 5.21, tW - 0.55, C.accent1, `${trust[i][1]} label`);
    text(trust[i][2], { x, y: 5.68, w: tW, h: 1.2, fontSize: 12, color: C.text1, objectName: `${trust[i][1]} text` });
  }
  s.addNotes("Three fetch profiles mirror how real agents read pages: raw HTML, reader-mode text that most assistants use, and llms.txt when a site publishes it. " +
    "Each feeds an isolated agent on gpt-4.1-mini that must work only from what it received. The judge on gpt-4.1 gets the ground truth: the full page with tooltips, hidden tabs and scripts. " +
    "That's how it can say what each agent couldn't see. Nothing is used for training, nothing is executed, and the report is advisory: teams decide what to fix.");

  // ---------- 5. GTM ----------
  pres.addSection({ title: "Go to market" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Go to market" });
  s.addText("Product-led outbound: the free audit is the pitch", { placeholder: "title" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M, y: 1.6, w: 5.6, h: 3.35, rectRadius: 0.12, fill: { color: C.text2 }, line: { type: "none" }, objectName: "Outreach card" });
  label("WE DON'T SEND COLD EMAILS. WE SEND AUDITS", M + 0.4, 1.9, 5, C.accent4, "Outreach label");
  text("“An AI agent tried to integrate your product. It scored 65/100 and got stuck on the auth step. Here is your free AIO report.”",
    { x: M + 0.4, y: 2.35, w: 4.8, h: 1.7, fontFace: THEME.headFontFace, fontSize: 19, italic: true, color: C.background1, objectName: "Outreach quote" });
  text("Works for any software company with public docs, SMB to enterprise",
    { x: M + 0.4, y: 4.05, w: 4.8, h: 0.6, fontSize: 14, color: C.accent4, objectName: "Outreach scope" });
  const funnel = [
    [fa.FaGauge, "FREE  ·  AIO READINESS GRADER", "Drop in a docs URL, see whether an agent can complete a basic task"],
    [fa.FaFileLines, "PAID  ·  DIAGNOSTIC REPORT", "Where exactly the agent got confused, and how to fix each gap"],
    [fa.FaArrowsRotate, "ENTERPRISE  ·  CONTINUOUS MONITORING", "Agentic Ready runs in CI/CD on every docs change"],
  ];
  for (let i = 0; i < funnel.length; i++) {
    const y = 1.6 + i * 1.15;
    await circleIcon(funnel[i][0], 6.75, y + 0.05, 0.55, i === 2 ? C.accent3 : C.accent1, `Tier ${i + 1} icon`);
    label(funnel[i][1], 7.5, y + 0.03, 5.2, C.accent1, `Tier ${i + 1} label`);
    text(funnel[i][2], { x: 7.5, y: y + 0.38, w: 5.2, h: 0.6, fontSize: 14, color: C.text1, objectName: `Tier ${i + 1} text` });
  }
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M, y: 5.3, w: W - 2 * M, h: 1.35, rectRadius: 0.12, fill: { color: C.background2 }, line: { type: "none" }, objectName: "ROI card" });
  label("WHO PAYS", M + 0.4, 5.5, 3, C.accent1, "Who pays label");
  text("DevRel, docs, developer-experience and support leaders at companies that grow through implementation",
    { x: M + 0.4, y: 5.85, w: 5.4, h: 0.7, fontSize: 14, color: C.text1, objectName: "Who pays text" });
  label("THE ROI", 6.75, 5.5, 3, C.accent3, "ROI label");
  text("Lower support costs from gaps fixed before customers hit them, and fewer drop-offs from integration friction",
    { x: 6.75, y: 5.85, w: 5.6, h: 0.7, fontSize: 14, color: C.text1, objectName: "ROI text" });
  s.addNotes("We don't send cold emails, we send audits. We run a target company's docs through Agentic Ready and reach out with their score and where the agent got stuck. " +
    "Self-serve, a free AIO Readiness Grader is the wedge. Teams upgrade for the full diagnostic report, then to enterprise for continuous monitoring in CI/CD. " +
    "The buyer is DevRel, docs or developer experience; the ROI is lower support costs and fewer integration drop-offs.");

  // ---------- 6. Next steps: features ----------
  pres.addSection({ title: "Next steps" });
  s = pres.addSlide({ masterName: "DARK", sectionTitle: "Next steps" });
  s.addText("What we build next", { placeholder: "title" });
  text("Six features that make the simulation more realistic and close the loop from finding to fix",
    { x: M, y: 1.4, w: 8.5, h: 0.4, fontSize: 16, color: C.accent4, objectName: "Next steps intro" });
  const rows = [
    ["SHARPER SIMULATION", [
      [fa.FaWindowMaximize, "Browser-rendered agent", "Reads the page after JavaScript runs, like browser-using agents"],
      [fa.FaMagnifyingGlassChart, "Retrieval agent", "Sees only the chunks that match its query, like IDE doc indexing"],
      [fa.FaUsers, "Multi-model panel", "Runs several assistants and models, compares them and cuts score variance"],
    ]],
    ["CLOSING THE LOOP", [
      [fa.FaTerminal, "Sandboxed execution", "Runs the agent's steps in a container to prove they actually work"],
      [fa.FaCodePullRequest, "Auto-fix pull requests", "Turns each finding into a ready-to-merge docs change"],
      [fa.FaChartLine, "CI checks and monitoring", "Scores every docs update and the whole site, and alerts when it drops"],
    ]],
  ];
  const fW = (W - 2 * M - 2 * 0.3) / 3;
  for (let r = 0; r < rows.length; r++) {
    const ry = 2.15 + r * 2.35;
    label(rows[r][0], M, ry, 5, C.accent4, `${rows[r][0]} label`);
    for (let i = 0; i < 3; i++) {
      const x = M + i * (fW + 0.3), y = ry + 0.4;
      const [Ico, name, desc] = rows[r][1][i];
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: fW, h: 1.65, rectRadius: 0.12, fill: { color: C.accent1 }, line: { type: "none" }, objectName: `${name} card` });
      await circleIcon(Ico, x + 0.3, y + 0.3, 0.5, r ? C.accent3 : C.text2, `${name} icon`);
      text([{ text: name, options: { bold: true, fontSize: 16, breakLine: true } }, { text: desc, options: { fontSize: 13 } }],
        { x: x + 1.0, y: y + 0.25, w: fW - 1.3, h: 1.2, color: C.background1, objectName: name });
    }
  }
  text([{ text: "Try it  ", options: { bold: true } }, { text: "agentic-ready-gqulkb5ysrtmnhtve284fz.streamlit.app   ·   github.com/godvy/agentic-ready" }],
    { x: M, y: 6.85, w: W - 2 * M, h: 0.35, fontSize: 12, color: C.accent4, objectName: "Links" });
  s.addNotes("Next we make the simulation more realistic and close the loop. A browser-rendered agent and a retrieval agent cover how browser agents and IDE doc indexing actually read docs, " +
    "and a multi-model panel compares assistants and cuts score variance. Then we close the loop: run the agent's steps in a sandbox to prove they work, " +
    "turn every finding into a ready-to-merge docs fix, and run Agentic Ready in CI and across the whole site so the score never silently drops.");

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
