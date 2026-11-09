# Build a renderer on Rubric

You have a bank of Rubric questions — Markdown files in a git repo — and you want to
put them in front of a learner in your own UI. This page is everything you need: the
parser, the object it hands you, how to grade an answer, and the three things a
renderer has to get right. Five minutes.

You do not need the Python package, a build step, a bundler, or a server.

---

## 1. Load the parser

[`web/rubric.js`](../web/rubric.js) is a dependency-free classic script — a JavaScript
port of the reference Python parser, held byte-for-byte in step with it by a shared
[conformance corpus](../tests/conformance/) that fails CI on any drift.

```html
<script src="rubric.js"></script>
<script>
  var result = Rubric.parse(markdownString);
</script>
```

It sets a `Rubric` global in a browser and `module.exports` under Node, so
`require("./rubric.js")` works too. Copy the file next to your HTML and open it from
`file://` — nothing else is required. (How you *get* the Markdown is yours: `fetch`, a
string literal, a bundler import, your CMS.)

Every call returns the same envelope:

```js
{
  success: true,      // false if the question is not renderable
  data: { ... },      // the question — shape below
  errors:   [ { line, message, severity } ],
  warnings: [ { line, message, severity } ]
}
```

**Check `success` before you render.** A bank is someone else's file; on `false`,
`data` may be partial. Show the errors to an author, skip the question for a learner.

## 2. What `data` looks like

Common to every type:

```js
{
  type: "SINGLE_CHOICE",             // see the four shapes below
  domains: ["Number and Numeration"],// used for the blueprint diagnosis
  difficulty: "EASY",                // EASY | MEDIUM | HARD (normalised)
  tags: ["fractions"],
  question_text: "A farmer harvests 200 mangoes ...",
  explanation: "Three-fifths of 200 is ...",   // shown after answering; may be ""
  choices: [],                       // empty for non-choice types
  question_data: {}                  // type-specific payload
}
```

### Multiple choice — `SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `MULTIPLE_SELECT`, `TRUE_FALSE`

Everything is in `choices`; `question_data` is `{}`.

```js
choices: [
  { letter: "A", text: "120", is_correct: true,
    rationale: "(3 / 5) * 200 = 120. \"Three-fifths of 200\" is the fraction times the whole." },
  { letter: "B", text: "40", is_correct: false,
    rationale: "This is one-fifth of 200 — you found one part but forgot the 3." }
]
```

`rationale` is `null` when the author did not write one — always guard it. Notes:

- `MULTIPLE_CHOICE` is a deprecated alias of `SINGLE_CHOICE` and is **not** rewritten:
  handle both type strings identically, exactly one `is_correct`.
- `MULTIPLE_SELECT` has two or more correct choices and adds a top-level
  `correct_count`; render checkboxes and require all of them.
- `TRUE_FALSE` is a choice question with exactly two choices. It is not a boolean —
  read the choices.
- `CASE_STUDY` (a fifth type, not covered here) carries a scenario plus a
  `sub_questions` array, each entry a choice question of the shape above.

### `DRAG_DROP`

```js
question_data: {
  draggables: [{ id: "d1", text: "HTTP" }, { id: "d2", text: "SSH" }],
  dropzones:  [{ id: "z1", text: "80"   }, { id: "z2", text: "22"  }],
  pairs: [
    { draggable: "HTTP", dropzone: "80", rationale: "Unencrypted web traffic uses port 80." },
    { draggable: "SSH",  dropzone: "22", rationale: null }
  ]
}
```

`pairs` reference draggables and dropzones **by their `text`**, not by id (the parser
has already validated that every reference resolves). A draggable named in no pair is a
distractor; a dropzone may appear in several pairs (bucketing).

### `SIMULATION`

An ordered task sequence — the learner builds the right sequence from steps mixed with
distractors.

```js
question_data: {
  steps: [
    { order: 1, text: "Back up the current sshd_config",
      rationale: "Always snapshot before changing a live service." },
    { order: 2, text: "Set PasswordAuthentication to no", rationale: null },
    { order: 3, text: "Restart the SSH daemon", rationale: null }
  ],
  distractors: [
    { text: "Open port 23 for Telnet", rationale: "Telnet is plaintext; it undoes the hardening." }
  ],
  total_steps: 3
}
```

Order is significant. Shuffle `steps.concat(distractors)` for display; grade against
`order`.

### `HOTSPOT`

```js
question_data: {
  image: { src: "diagram.svg", alt: "Network diagram" },   // or just "diagram.png"
  correctRegions: [
    { x: 0.325, y: 0.39, width: 0.1625, height: 0.222, label: "Firewall",
      rationale: "First device inbound traffic reaches." }
  ],
  distractorRegions: [
    { cx: 0.65, cy: 0.5, r: 0.08, label: "Switch",
      rationale: "Forwards frames; does not filter internet traffic." },
    { points: [[0.8, 0.14], [0.96, 0.14], [0.96, 0.33], [0.8, 0.33]], label: "Server" }
  ]
}
```

- `image` is **either an object** (`{src, alt, width?, height?}`) **or a bare string**.
  Normalise: `var img = typeof d.image === "string" ? { src: d.image } : d.image;`
- Three shapes: rect (`x, y, width, height`), circle (`cx, cy, r`), polygon (`points`).
- Coordinates are **fractions of the image, 0–1**, so hit-test against the *rendered*
  size: `var fx = (event.clientX - rect.left) / rect.width;`. A circle's `r` is a
  fraction of the image **width**.
- Pixel coordinates are legal too; they scale by `image.width/height`, or — with a
  warning in `result.warnings` — by the image's natural size.
- Several `correctRegions` means the learner must find them all.

## 3. Grade an answer, reveal the rationale

Grading is a property of the data, not of your UI. The whole answer key is in the
object you already have.

```js
// choice questions
var picked = q.choices.filter(function (c) { return c.letter === letter; })[0];
var correct = picked.is_correct;
show(picked.rationale);            // why THIS option — the point of the format

// MULTIPLE_SELECT: compare sets
var chosen = letters.slice().sort().join("");
var key = q.choices.filter(function (c) { return c.is_correct; })
           .map(function (c) { return c.letter; }).sort().join("");

// DRAG_DROP: one pair at a time
var pair = q.question_data.pairs.filter(function (p) { return p.draggable === token; })[0];
var ok = pair && pair.dropzone === zoneText;
show(pair && pair.rationale);

// SIMULATION: compare the learner's sequence to `order`
var key = q.question_data.steps.slice()
  .sort(function (a, b) { return a.order - b.order; })
  .map(function (s) { return s.text; });

// HOTSPOT: hit-test the click, then reveal the region's own rationale
var hit = regions.filter(function (r) { return contains(r, fx, fy); })[0];
show(hit ? hit.rationale : "You clicked outside every marked region.");
```

Then show `q.explanation` — the overall working, as opposed to the per-option
correction.

**The per-choice `rationale` is the reason this format exists.** A learner did not get
it wrong in the abstract; they picked B, for a reason, and `rationale` on B is the
sentence that addresses *that* misconception. A renderer that shows only
"the answer was A" has thrown away the payload. If you build one thing well, build this.

## 4. Score against the blueprint

A bundle's `manifest.json` declares the exam's domains and their syllabus weights.
`Rubric.coverage(manifest, parsedData)` computes the same rows the `rubric blueprint`
CLI reports, in the browser — give it the manifest object and the array of
successfully-parsed `data` objects:

```js
var rows = Rubric.coverage(manifest, parsed.map(function (r) { return r.data; }));
// [{ domain, target_weight, actual_weight, question_count, delta, in_blueprint, status }]
```

`status` is `ok` | `over` | `under` | `uncovered` | `orphan`. That tells you whether the
*bank* matches the syllabus. To diagnose a *learner*, tally their wrong answers by
`data.domains` and rank the domains by exam weight × miss rate: "you're solid on
Algebra, thin on Geometry — drill here next." That ranking is what the
[playground](../web/index.html) does, and it is the whole reason the weights are in the
manifest.

(The CLI can hand you the same numbers as JSON for a server-side pipeline — see
[JSON-OUTPUT.md](JSON-OUTPUT.md).)

## 5. What a renderer must handle

Three things that will otherwise bite you on a real bank:

1. **Missing or unresolvable images.** An image reference in prose survives parsing as
   a literal `[IMAGE: name]` marker inside `question_text`, and a `HOTSPOT`'s
   `image.src` may be a URL, a bundle-relative path or a `data:` URI. Resolving them is
   *your* job, there is no resolver contract yet, and a bank you did not author will
   have references you cannot resolve. Set `onerror` on every `<img>` and fall back to
   the `alt`/label text; never leave a hotspot question un-answerable with a broken
   image and no explanation.
2. **Maths is TeX source.** `$x^2$` is passed through verbatim; the parser does not
   render it and neither does the playground today. Showing the source is an acceptable
   renderer — silently dropping it is not. If you want typeset maths, run
   `question_text`, `choices[].text` and the rationales through KaTeX or MathJax
   yourself.
3. **Unknown types.** The format has grown types before and will again. Switch on
   `data.type` with a real `default` branch that still shows `question_text` and
   `explanation`, rather than rendering nothing or throwing. And escape everything: a
   question file is untrusted input, so build the DOM with `textContent` or escape
   before `innerHTML`.

## 6. A complete, working example

The file below is a whole renderer: parse, render, grade, reveal the rationale for the
picked option, and degrade gracefully on a type it does not handle. Save it next to
`rubric.js` and open it from disk — no server, no build.

Both this page and a slightly fuller version of it —
[`web/renderer-example.html`](../web/renderer-example.html), which adds a second question
to exercise the unsupported-type branch — were run from `file://` and checked;
`tests/test_docs_examples.py` keeps the questions embedded in them parsing.

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Rubric — minimal renderer</title>
  </head>
  <body>
    <div id="app"></div>
    <script src="rubric.js"></script>
    <script>
      var DSL = [
        "---",
        "type: SINGLE_CHOICE",
        "domains: [Number and Numeration]",
        "explanation: Three-fifths of 200 is (3 / 5) * 200 = 120.",
        "---",
        "",
        "# Question",
        "",
        "A farmer harvests 200 mangoes and sells three-fifths of them. How many?",
        "",
        "## Choices",
        "",
        "A. 120 *[CORRECT]*",
        "> (3 / 5) * 200 = 120 — the fraction times the whole.",
        "B. 40",
        "> This is one-fifth of 200; you forgot to multiply by the 3.",
      ].join("\n");

      function esc(s) {
        return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
          return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
        });
      }

      var app = document.getElementById("app");
      var result = Rubric.parse(DSL);

      if (!result.success) {
        app.textContent = "Cannot render: " + result.errors[0].message;
      } else if (result.data.choices.length === 0) {
        // Unknown or non-choice type: still show the prompt and the teaching.
        app.innerHTML = "<p>" + esc(result.data.question_text) + "</p><p>" +
          esc(result.data.explanation) + "</p>";
      } else {
        var q = result.data;
        var html = "<p>" + esc(q.question_text) + "</p>";
        q.choices.forEach(function (c) {
          html += '<label style="display:block"><input type="radio" name="q" value="' +
            c.letter + '"> ' + c.letter + ". " + esc(c.text) + "</label>";
        });
        html += '<button id="go">Check answer</button><div id="out"></div>';
        app.innerHTML = html;

        document.getElementById("go").onclick = function () {
          var picked = app.querySelector('input[name="q"]:checked');
          var out = document.getElementById("out");
          if (!picked) { out.textContent = "Pick an option first."; return; }

          var choice = q.choices.filter(function (c) { return c.letter === picked.value; })[0];
          var html = "<p><strong>" + (choice.is_correct ? "Correct." : "Not quite.") + "</strong></p>";
          if (choice.rationale) {
            html += "<p>Why " + choice.letter + ": " + esc(choice.rationale) + "</p>";
          }
          if (!choice.is_correct) {
            var right = q.choices.filter(function (c) { return c.is_correct; })[0];
            html += "<p>The answer is " + right.letter + ". " + esc(right.text) + "</p>";
          }
          if (q.explanation) html += "<p><em>" + esc(q.explanation) + "</em></p>";
          out.innerHTML = html;
        };
      }
    </script>
  </body>
</html>
```

---

**Next:** [`FORMAT.md`](FORMAT.md) is the full syntax reference,
[`JSON-OUTPUT.md`](JSON-OUTPUT.md) the CLI's machine-readable reports, and
[`web/index.html`](../web/index.html) a fuller renderer — all four interactive types
plus the domain diagnosis — in one dependency-free file you can read end to end.
