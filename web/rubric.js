/*
 * rubric.js — a dependency-free JavaScript port of the Rubric DSL parser.
 *
 * This is a faithful re-implementation of `src/rubric/parser.py` and the
 * coverage logic of `src/rubric/bundle.py`, so a Rubric bank can be parsed and
 * diagnosed entirely in the browser — no backend, no build step, no WASM
 * runtime. The playground (index.html) is built on this file, and it drops onto
 * any static host (GitHub Pages) or opens straight from `file://`.
 *
 * PARITY IS NOT ASSUMED — IT IS TESTED. The one real risk of a second
 * implementation is silent drift from the Python reference. `web/test/parity`
 * runs both parsers over a shared corpus of fixtures generated FROM the Python
 * parser and fails loudly on any divergence. If you change the Python parser,
 * regenerate the fixtures and this port must be updated to match.
 *
 * The file is a UMD-style classic script: it attaches `Rubric` to the global in
 * a browser and also sets `module.exports` under Node (CommonJS) for the test.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api; // Node (CommonJS) — used by the parity test
  }
  if (root) {
    root.Rubric = api; // browser global — used by the playground
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  var VALID_TYPES = [
    "SINGLE_CHOICE",
    "MULTIPLE_CHOICE", // deprecated alias for SINGLE_CHOICE
    "MULTIPLE_SELECT",
    "TRUE_FALSE",
    "HOTSPOT",
    "DRAG_DROP",
    "CASE_STUDY",
    "SIMULATION",
  ];

  var VALID_DIFFICULTIES = ["EASY", "MEDIUM", "HARD"];

  // ---- tiny helpers mirroring the Python semantics we rely on --------------

  function err(line, message, severity) {
    return { line: line, message: message, severity: severity || "error" };
  }

  // Python str.strip(): trims ASCII + Unicode whitespace from both ends.
  // JS String.prototype.trim() matches closely enough for our inputs.
  function strip(s) {
    return s == null ? "" : String(s).trim();
  }

  // Mirror of parser._find_line: 1-based index of the first content line that
  // contains `search`, else 0. Operates on the post-frontmatter content.
  function findLine(content, search) {
    var lines = content.split("\n");
    for (var i = 0; i < lines.length; i++) {
      if (lines[i].indexOf(search) !== -1) return i + 1;
    }
    return 0;
  }

  // parser._parse_images is a pass-through today; kept as a seam.
  function parseImages(text) {
    return text;
  }

  // ---- minimal YAML frontmatter parser -------------------------------------
  //
  // The Python parser calls yaml.safe_load on the frontmatter. Rubric's
  // frontmatter uses a small, well-defined subset — scalars, flow sequences,
  // and literal/folded block scalars — so we parse exactly that subset rather
  // than vendoring a full YAML library. The conformance corpus pins this
  // against real PyYAML output; if a bank needs YAML this does not cover, the
  // corpus is where we would see it fail.

  function YamlError(message) {
    this.message = message;
  }

  function unquoteScalar(raw) {
    var s = strip(raw);
    if (s.length >= 2) {
      var first = s[0];
      var last = s[s.length - 1];
      if (first === '"' && last === '"') {
        // Double-quoted: unescape the common sequences.
        var inner = s.slice(1, -1);
        return inner
          .replace(/\\n/g, "\n")
          .replace(/\\t/g, "\t")
          .replace(/\\"/g, '"')
          .replace(/\\\\/g, "\\");
      }
      if (first === "'" && last === "'") {
        // Single-quoted: only '' -> ' is special.
        return s.slice(1, -1).replace(/''/g, "'");
      }
    }
    return s;
  }

  // Coerce a bare (unquoted) scalar the way YAML core would for the values
  // Rubric uses. Quoted scalars are always strings.
  function coerceBareScalar(raw) {
    var s = strip(raw);
    if (s === "" || s === "~" || s === "null" || s === "Null" || s === "NULL") {
      return null;
    }
    if (s === "true" || s === "True" || s === "TRUE") return true;
    if (s === "false" || s === "False" || s === "FALSE") return false;
    if (/^[+-]?\d+$/.test(s)) return parseInt(s, 10);
    if (/^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$/.test(s) && /[.eE]/.test(s)) {
      return parseFloat(s);
    }
    return s;
  }

  function parseScalarValue(raw) {
    var s = strip(raw);
    if (s.length && (s[0] === '"' || s[0] === "'")) return unquoteScalar(s);
    return coerceBareScalar(s);
  }

  // Split a flow sequence body ("a, b, \"c, d\"") on top-level commas only, so a
  // quoted comma stays inside its item. This is the documented YAML gotcha that
  // `rubric blueprint` surfaces as ORPHAN domains when authors forget to quote.
  function splitFlow(body) {
    var items = [];
    var cur = "";
    var quote = null;
    for (var i = 0; i < body.length; i++) {
      var ch = body[i];
      if (quote) {
        cur += ch;
        if (ch === quote) quote = null;
      } else if (ch === '"' || ch === "'") {
        quote = ch;
        cur += ch;
      } else if (ch === ",") {
        items.push(cur);
        cur = "";
      } else {
        cur += ch;
      }
    }
    if (strip(cur) !== "" || items.length > 0) items.push(cur);
    return items.map(function (it) {
      return parseScalarValue(it);
    });
  }

  function parseFlowSequence(raw) {
    var s = strip(raw);
    // strip the surrounding [ ]
    var body = s.slice(1, -1);
    if (strip(body) === "") return [];
    return splitFlow(body);
  }

  function indentOf(line) {
    var m = /^(\s*)/.exec(line);
    return m ? m[1].length : 0;
  }

  // Parse a literal (|) or folded (>) block scalar starting after `key:`.
  // Returns {value, nextIndex}. Mirrors PyYAML clip/strip/keep chomping.
  function parseBlockScalar(lines, startIdx, keyIndent, style, chomp) {
    var contentLines = [];
    var i = startIdx;
    var blockIndent = null;
    for (; i < lines.length; i++) {
      var line = lines[i];
      if (strip(line) === "") {
        contentLines.push(""); // blank line, indentation-agnostic
        continue;
      }
      var ind = indentOf(line);
      if (ind <= keyIndent) break; // dedent ends the block
      if (blockIndent === null) blockIndent = ind;
      contentLines.push(line.slice(blockIndent));
    }
    // Drop trailing blank lines for chomping decisions, remembering how many.
    var trailingBlanks = 0;
    while (
      contentLines.length &&
      contentLines[contentLines.length - 1] === ""
    ) {
      contentLines.pop();
      trailingBlanks++;
    }

    var body;
    if (style === ">") {
      // Folded: join consecutive non-empty lines with spaces; blank lines
      // become newlines. (Rubric content uses | in practice; this is for
      // completeness.)
      var folded = "";
      for (var j = 0; j < contentLines.length; j++) {
        if (contentLines[j] === "") {
          folded += "\n";
        } else {
          if (folded.length && folded[folded.length - 1] !== "\n") folded += " ";
          folded += contentLines[j];
        }
      }
      body = folded;
    } else {
      body = contentLines.join("\n");
    }

    // Chomping (applied to the trailing newline(s) after the last content line).
    if (chomp === "-") {
      // strip: no trailing newline at all — leave `body` as-is.
    } else if (chomp === "+") {
      // keep: one line-final newline plus every trailing blank line we removed.
      if (contentLines.length) body += "\n";
      for (var k = 0; k < trailingBlanks; k++) body += "\n";
    } else {
      // clip (default): exactly one trailing newline if there was any content.
      if (contentLines.length) body += "\n";
    }
    return { value: body, nextIndex: i };
  }

  // Parse the frontmatter YAML into a plain object (or throw YamlError).
  // Only top-level `key: value` mappings are supported (which is all Rubric
  // frontmatter uses).
  function parseFrontmatter(text) {
    var lines = text.split("\n");
    var obj = {};
    var sawKey = false;
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      if (strip(line) === "") continue;
      if (/^\s*#/.test(line)) continue; // comment line

      var m = /^(\s*)([^:\s][^:]*?)\s*:\s?(.*)$/.exec(line);
      if (!m) {
        // A non-key, non-blank top-level line is not valid mapping YAML here.
        throw new YamlError("could not parse frontmatter line: '" + line + "'");
      }
      var keyIndent = m[1].length;
      var key = strip(m[2]);
      // Unquote a quoted key just in case.
      key = unquoteScalar(key);
      var rest = m[3];
      sawKey = true;

      var restTrim = strip(rest);
      var blockMatch = /^([|>])([+-]?)\s*$/.exec(restTrim);
      if (blockMatch) {
        var res = parseBlockScalar(
          lines,
          i + 1,
          keyIndent,
          blockMatch[1],
          blockMatch[2] || ""
        );
        obj[key] = res.value;
        i = res.nextIndex - 1;
        continue;
      }
      if (restTrim === "") {
        // Either an empty scalar or a nested block/sequence. Rubric frontmatter
        // does not use block sequences, so treat an empty value as null.
        obj[key] = null;
        continue;
      }
      if (restTrim[0] === "[") {
        obj[key] = parseFlowSequence(restTrim);
        continue;
      }
      obj[key] = parseScalarValue(restTrim);
    }
    if (!sawKey) {
      // yaml.safe_load("") -> None; an empty/comment-only frontmatter is "not a
      // dict" in the Python parser's eyes.
      return null;
    }
    return obj;
  }

  // ---- the parser ----------------------------------------------------------

  function ParseResult(success, data, errors, warnings) {
    return {
      success: success,
      data: data === undefined ? null : data,
      errors: errors || [],
      warnings: warnings || [],
    };
  }

  function get(obj, key, dflt) {
    return obj != null && Object.prototype.hasOwnProperty.call(obj, key)
      ? obj[key]
      : dflt;
  }

  function parse(dsl) {
    var errors = [];
    var warnings = [];

    try {
      // Split frontmatter and content on lines that are exactly `---`.
      // Mirrors Python re.split(r'^---\s*$', dsl, flags=re.MULTILINE).
      var parts = dsl.split(/^---\s*$/m);

      if (parts.length < 3) {
        errors.push(
          err(1, "Invalid DSL format: missing frontmatter delimiters (---)")
        );
        return ParseResult(false, null, errors);
      }

      var frontmatter;
      try {
        frontmatter = parseFrontmatter(parts[1]);
      } catch (e) {
        if (e instanceof YamlError) {
          errors.push(err(2, "Invalid YAML in frontmatter: " + e.message));
          return ParseResult(false, null, errors);
        }
        throw e;
      }
      if (
        frontmatter === null ||
        typeof frontmatter !== "object" ||
        Array.isArray(frontmatter)
      ) {
        errors.push(err(2, "Frontmatter must be valid YAML dictionary"));
        return ParseResult(false, null, errors);
      }

      if (!Object.prototype.hasOwnProperty.call(frontmatter, "type")) {
        errors.push(err(2, "Missing required field: 'type'"));
        return ParseResult(false, null, errors);
      }

      var qtype = frontmatter.type;
      if (VALID_TYPES.indexOf(qtype) === -1) {
        errors.push(
          err(
            2,
            "Invalid type '" +
              qtype +
              "'. Must be one of: " +
              VALID_TYPES.join(", ")
          )
        );
        return ParseResult(false, null, errors);
      }

      if (Object.prototype.hasOwnProperty.call(frontmatter, "difficulty")) {
        var difficulty = frontmatter.difficulty;
        if (VALID_DIFFICULTIES.indexOf(difficulty) === -1) {
          warnings.push(
            err(
              2,
              "Invalid difficulty '" + difficulty + "'. Defaulting to MEDIUM",
              "warning"
            )
          );
          frontmatter.difficulty = "MEDIUM";
        }
      }

      var content = parts[2];
      var result;

      if (
        ["SINGLE_CHOICE", "MULTIPLE_CHOICE", "MULTIPLE_SELECT", "TRUE_FALSE"].indexOf(
          qtype
        ) !== -1
      ) {
        result = parseChoiceQuestion(content, frontmatter, errors, warnings);
      } else if (qtype === "HOTSPOT") {
        result = parseHotspotQuestion(content, frontmatter, errors, warnings);
      } else if (qtype === "DRAG_DROP") {
        result = parseDragDropQuestion(content, frontmatter, errors, warnings);
      } else if (qtype === "CASE_STUDY") {
        result = parseCaseStudyQuestion(content, frontmatter, errors, warnings);
      } else if (qtype === "SIMULATION") {
        result = parseSimulationQuestion(content, frontmatter, errors, warnings);
      } else {
        errors.push(err(1, "Parser not implemented for type: " + qtype));
        return ParseResult(false, null, errors);
      }

      if (errors.length) {
        return ParseResult(false, result, errors, warnings);
      }
      return ParseResult(true, result, [], warnings);
    } catch (e) {
      errors.push(err(0, "Unexpected parsing error: " + (e && e.message)));
      return ParseResult(false, null, errors);
    }
  }

  function parseChoiceQuestion(content, frontmatter, errors, warnings) {
    var questionText = "";
    var qMatch = /#\s+Question\s*\n([\s\S]*?)(?=##|$)/.exec(content);
    if (!qMatch) {
      errors.push(err(findLine(content, "# Question"), "Missing '# Question' section"));
    } else {
      questionText = strip(qMatch[1]);
    }
    questionText = parseImages(questionText);

    var choices = [];
    var cMatch = /##\s+Choices\s*\n([\s\S]*?)(?=##|---|$)/.exec(content);
    if (!cMatch) {
      errors.push(err(findLine(content, "## Choices"), "Missing '## Choices' section"));
    } else {
      choices = parseChoices(cMatch[1], errors, warnings);
    }

    var correctCount = choices.filter(function (c) {
      return c.is_correct;
    }).length;
    var qtype = frontmatter.type;

    if (
      (qtype === "SINGLE_CHOICE" || qtype === "MULTIPLE_CHOICE") &&
      correctCount !== 1
    ) {
      errors.push(
        err(
          findLine(content, "## Choices"),
          qtype +
            " must have exactly 1 correct answer, found " +
            correctCount
        )
      );
    } else if (qtype === "MULTIPLE_SELECT" && correctCount < 2) {
      errors.push(
        err(
          findLine(content, "## Choices"),
          "MULTIPLE_SELECT must have at least 2 correct answers, found " +
            correctCount
        )
      );
    } else if (qtype === "TRUE_FALSE") {
      if (choices.length !== 2) {
        errors.push(
          err(
            findLine(content, "## Choices"),
            "TRUE_FALSE must have exactly 2 choices, found " + choices.length
          )
        );
      } else if (correctCount !== 1) {
        errors.push(
          err(
            findLine(content, "## Choices"),
            "TRUE_FALSE must have exactly 1 correct answer, found " +
              correctCount
          )
        );
      }
    }

    var result = {
      type: qtype,
      domains: get(frontmatter, "domains", []),
      difficulty: get(frontmatter, "difficulty", "MEDIUM"),
      tags: get(frontmatter, "tags", []),
      question_text: questionText,
      choices: choices,
      explanation: get(frontmatter, "explanation", ""),
      question_data: {},
    };
    if (qtype === "MULTIPLE_SELECT") result.correct_count = correctCount;
    return result;
  }

  function parseChoices(choicesText, errors, warnings) {
    var choices = [];
    var choicePattern = /^([A-Z])\.\s*([\s\S]*?)(?:\*\[CORRECT\]\*)?$/;
    var lines = choicesText.split("\n");
    for (var idx = 0; idx < lines.length; idx++) {
      var lineNum = idx + 1;
      var line = strip(lines[idx]);
      if (!line) continue;

      if (line.charAt(0) === ">") {
        var rationale = strip(line.replace(/^>+/, ""));
        if (choices.length === 0) {
          warnings.push(
            err(lineNum, "Rationale line '>' appears before any choice", "warning")
          );
        } else if (rationale) {
          var previous = choices[choices.length - 1].rationale;
          choices[choices.length - 1].rationale = previous
            ? previous + " " + rationale
            : rationale;
        }
        continue;
      }

      var match = choicePattern.exec(line);
      if (match) {
        var text = strip(match[2]);
        var isCorrect = line.indexOf("*[CORRECT]*") !== -1;
        text = parseImages(text);
        choices.push({
          letter: match[1],
          text: text,
          is_correct: isCorrect,
          rationale: null,
        });
      } else {
        warnings.push(
          err(
            lineNum,
            "Could not parse choice: '" + line.slice(0, 50) + "...'",
            "warning"
          )
        );
      }
    }
    return choices;
  }

  function parseHotspotQuestion(content, frontmatter, errors, warnings) {
    var questionText = "";
    var qMatch = /#\s+Question\s*\n([\s\S]*?)(?=##|$)/.exec(content);
    if (qMatch) questionText = strip(qMatch[1]);
    questionText = parseImages(questionText);

    var hotspotData = {};
    var jsonMatch = /```json\s*([\s\S]*?)```/.exec(content);
    if (jsonMatch) {
      try {
        hotspotData = JSON.parse(jsonMatch[1]);
      } catch (e) {
        errors.push(
          err(
            findLine(content, "```json"),
            "Invalid JSON in hotspot data: " + (e && e.message)
          )
        );
      }
    } else {
      errors.push(
        err(findLine(content, "## Hotspots"), "Missing hotspot data (```json block)")
      );
    }

    return {
      type: "HOTSPOT",
      domains: get(frontmatter, "domains", []),
      difficulty: get(frontmatter, "difficulty", "MEDIUM"),
      tags: get(frontmatter, "tags", []),
      question_text: questionText,
      choices: [],
      explanation: get(frontmatter, "explanation", ""),
      question_data: hotspotData,
    };
  }

  function parseDragDropQuestion(content, frontmatter, errors, warnings) {
    warnings.push(err(1, "DRAG_DROP parser not yet implemented", "warning"));
    return {
      type: "DRAG_DROP",
      domains: get(frontmatter, "domains", []),
      difficulty: get(frontmatter, "difficulty", "MEDIUM"),
      tags: get(frontmatter, "tags", []),
      question_text: "",
      choices: [],
      explanation: get(frontmatter, "explanation", ""),
      question_data: {},
    };
  }

  function parseSimulationQuestion(content, frontmatter, errors, warnings) {
    warnings.push(err(1, "SIMULATION parser not yet implemented", "warning"));
    return {
      type: "SIMULATION",
      domains: get(frontmatter, "domains", []),
      difficulty: get(frontmatter, "difficulty", "MEDIUM"),
      tags: get(frontmatter, "tags", []),
      question_text: "",
      choices: [],
      explanation: get(frontmatter, "explanation", ""),
      question_data: {},
    };
  }

  function parseCaseStudyQuestion(content, frontmatter, errors, warnings) {
    var scenarioText = "";
    var sMatch = /#\s+Scenario\s*\n([\s\S]*?)(?=##|$)/.exec(content);
    if (!sMatch) {
      errors.push(
        err(findLine(content, "# Scenario"), "Missing '# Scenario' section in case study")
      );
    } else {
      scenarioText = parseImages(strip(sMatch[1]));
    }

    var subQuestions = [];
    var subRe = /##\s+Question\s+(\d+)\s*\n([\s\S]*?)(?=##\s+Question\s+\d+|$)/g;
    var sm;
    while ((sm = subRe.exec(content)) !== null) {
      var questionNum = parseInt(sm[1], 10);
      var qContent = sm[2];

      var subTextMatch = /^([\s\S]*?)(?=###|$)/.exec(qContent);
      var subText = subTextMatch ? strip(subTextMatch[1]) : "";
      subText = parseImages(subText);

      var subChoices = [];
      var subChoicesMatch = /###\s+Choices\s*\n([\s\S]*?)(?=###|$)/.exec(qContent);
      if (!subChoicesMatch) {
        errors.push(
          err(
            findLine(content, "## Question " + questionNum),
            "Missing '### Choices' section in Question " + questionNum
          )
        );
      } else {
        subChoices = parseChoices(subChoicesMatch[1], errors, warnings);
      }

      var explMatch = /###\s+Explanation\s*\n([\s\S]*?)(?=###|##|$)/.exec(qContent);
      var explanation = explMatch ? strip(explMatch[1]) : "";

      var subCorrect = subChoices.filter(function (c) {
        return c.is_correct;
      }).length;
      var subType = subCorrect > 1 ? "MULTIPLE_SELECT" : "SINGLE_CHOICE";

      subQuestions.push({
        question_number: questionNum,
        question_type: subType,
        question_text: subText,
        choices: subChoices,
        explanation: explanation,
        correct_count: subType === "MULTIPLE_SELECT" ? subCorrect : null,
      });
    }

    if (subQuestions.length === 0) {
      errors.push(
        err(findLine(content, "# Scenario"), "Case study must have at least one sub-question")
      );
    }

    return {
      type: "CASE_STUDY",
      domains: get(frontmatter, "domains", []),
      difficulty: get(frontmatter, "difficulty", "MEDIUM"),
      tags: get(frontmatter, "tags", []),
      question_text: scenarioText,
      choices: [],
      explanation: null,
      question_data: { total_sub_questions: subQuestions.length },
      sub_questions: subQuestions,
    };
  }

  function validateDsl(dsl) {
    return parse(dsl);
  }

  // ---- bundle coverage (port of bundle.Bundle.coverage) --------------------

  function coerceWeight(weight) {
    if (typeof weight === "boolean") return null;
    if (typeof weight === "number") return weight;
    if (typeof weight === "string") {
      var t = weight.trim();
      if (/^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/.test(t)) return parseFloat(t);
      return null;
    }
    return null;
  }

  function round1(n) {
    return Math.round(n * 10) / 10;
  }

  function statusFor(row) {
    if (!row.in_blueprint) return "orphan";
    if (row.question_count === 0) return "uncovered";
    if (row.delta === null) return "ok";
    if (row.delta <= -10) return "under";
    if (row.delta >= 10) return "over";
    return "ok";
  }

  // Given a manifest object and the list of parsed question `data` objects,
  // compute the same DomainCoverage rows the Python CLI reports. `parsedData`
  // should contain only successfully-parsed questions' `data` dicts.
  function coverage(manifest, parsedData) {
    var counts = {};
    var total = 0;
    parsedData.forEach(function (data) {
      if (!data) return;
      total += 1;
      var domains = data.domains || [];
      if (typeof domains === "string") domains = [domains];
      else if (!Array.isArray(domains)) domains = [];
      domains.forEach(function (name) {
        counts[name] = (counts[name] || 0) + 1;
      });
    });

    function pct(n) {
      return total ? round1((100.0 * n) / total) : 0.0;
    }

    var blueprint = Array.isArray(manifest && manifest.domains)
      ? manifest.domains
      : [];
    var rows = [];
    var seen = {};
    blueprint.forEach(function (entry) {
      var name = entry && entry.name;
      if (!name) return;
      seen[name] = true;
      var target = coerceWeight(entry.weight);
      var count = counts[name] || 0;
      var actual = pct(count);
      var row = {
        domain: name,
        target_weight: target === undefined ? null : target,
        question_count: count,
        actual_weight: actual,
        in_blueprint: true,
        delta: target === null || target === undefined ? null : round1(actual - target),
      };
      row.status = statusFor(row);
      rows.push(row);
    });
    Object.keys(counts).forEach(function (name) {
      if (!seen[name]) {
        var count = counts[name];
        var row = {
          domain: name,
          target_weight: null,
          question_count: count,
          actual_weight: pct(count),
          in_blueprint: false,
          delta: null,
        };
        row.status = statusFor(row);
        rows.push(row);
      }
    });
    return rows;
  }

  return {
    VALID_TYPES: VALID_TYPES,
    VALID_DIFFICULTIES: VALID_DIFFICULTIES,
    parse: parse,
    validateDsl: validateDsl,
    coverage: coverage,
    coerceWeight: coerceWeight,
    // exported for tests / advanced use
    _parseFrontmatter: parseFrontmatter,
  };
});
