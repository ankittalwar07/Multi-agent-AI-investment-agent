// AI Infrastructure Moat Map: static dashboard. Reads data/latest.json, no build step.
(function () {
  "use strict";

  var CATEGORY_LABELS = {
    raw_materials: "Raw materials",
    semiconductor_capex: "Chip-making tools",
    semiconductor_manufacturing: "Chip manufacturing",
    compute_silicon: "Compute silicon",
    memory: "Memory",
    networking: "Networking",
    facilities: "Facilities and power",
    compute_platform: "Cloud platforms",
    model_layer: "Model layer",
    data_layer: "Data layer",
    tooling: "Tooling",
    other: "Other"
  };
  var CATEGORY_ORDER = Object.keys(CATEGORY_LABELS);
  var CONSENSUS = {
    UNANIMOUS_STRONG_BUY: ["Unanimous strong yes", "good"],
    UNANIMOUS_BUY: ["Unanimous yes", "good"],
    MAJORITY_BUY: ["Majority yes", "good"],
    MAJORITY_AVOID: ["Majority pass", "bad"],
    DIVIDED: ["Divided", "mid"]
  };
  var BREAKDOWN = [
    ["sole_source", "Sole source", 30],
    ["share", "Market share", 25],
    ["ip", "IP and tech", 15],
    ["regulatory", "Regulatory", 10],
    ["switching", "Switching costs", 10],
    ["demand", "Demand", 10]
  ];

  var state = { data: null, comps: {} };

  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    attrs = attrs || {};
    Object.keys(attrs).forEach(function (k) {
      if (k === "text") n.textContent = attrs[k];
      else if (k === "cls") n.className = attrs[k];
      else n.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) {
      if (c == null) return;
      n.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return n;
  }
  function $(id) { return document.getElementById(id); }
  function catLabel(c) { return CATEGORY_LABELS[c] || c || "Other"; }
  function safeUrl(u) { return typeof u === "string" && u.indexOf("https://") === 0 ? u : null; }

  function bar(value, max) {
    var pct = Math.max(0, Math.min(100, (value / max) * 100));
    var b = el("span", { cls: "bar" }, [el("span", { cls: "fill" })]);
    b.firstChild.style.width = pct + "%";
    return b;
  }

  function consensusBadge(c) {
    var meta = CONSENSUS[c.consensus] || [c.consensus, "mid"];
    return el("span", { cls: "badge " + meta[1], text: meta[0] + " (" + c.buy_count + " of " + c.n_members + ")" });
  }

  function renderMeta(d) {
    $("s-components").textContent = d.stats.components;
    $("s-companies").textContent = d.stats.companies;
    $("s-sources").textContent = d.stats.cited_sources;
    $("s-sole").textContent = d.stats.sole_source_credited;
    var by = d.generated_by === "claude-routine" ? "weekly Claude routine" : "offline demo mode";
    $("run-meta").textContent = "Run " + d.run_date + ", produced by the " + by + ", rubric " + d.rubric_version;
    $("summary").textContent = d.summary;
    var ul = $("themes");
    ul.innerHTML = "";
    (d.themes || []).forEach(function (t) { ul.appendChild(el("li", { text: t })); });
    if (d.sample) {
      var b = $("banner");
      b.hidden = false;
      b.textContent = "Sample data from the offline demo mode (deterministic mock agents, no web research, so no sources are cited yet). The weekly Claude routine replaces it with cited research.";
    }
  }

  function filtered() {
    var q = $("q").value.trim().toLowerCase();
    var cat = $("cat").value;
    var pub = $("pub").value;
    return state.data.companies.filter(function (c) {
      var comp = state.comps[c.component_id] || {};
      if (cat && comp.category !== cat) return false;
      if (pub === "public" && c.is_public !== true) return false;
      if (pub === "private" && c.is_public !== false) return false;
      if (q && ((c.name || "") + " " + (c.ticker || "")).toLowerCase().indexOf(q) === -1) return false;
      return true;
    });
  }

  function renderBoard() {
    var tbody = document.querySelector("#board tbody");
    tbody.innerHTML = "";
    var rows = filtered();
    if (!rows.length) {
      tbody.appendChild(el("tr", {}, [el("td", { colspan: "6", cls: "muted", text: "No companies match these filters." })]));
      return;
    }
    rows.forEach(function (c) {
      var comp = state.comps[c.component_id] || {};
      var nameCell = el("td", {}, [
        el("div", { cls: "co", text: c.name }),
        el("div", { cls: "muted small", text: (c.ticker ? c.ticker : (c.is_public === false ? "Private" : "")) + (c.hq_country ? ", " + c.hq_country : "") })
      ]);
      var tr = el("tr", { tabindex: "0", role: "button", "aria-label": "Details for " + c.name }, [
        el("td", { cls: "rank", text: String(c.rank) }),
        nameCell,
        el("td", {}, [el("div", { text: comp.name || "" }), el("div", { cls: "muted small", text: catLabel(comp.category) })]),
        el("td", { text: c.market_share_bucket || "n/a" }),
        el("td", { cls: "score" }, [el("b", { text: String(c.score.composite) }), bar(c.score.composite, 100)]),
        el("td", {}, [consensusBadge(c.council)])
      ]);
      tr.addEventListener("click", function () { openDetail(c); });
      tr.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openDetail(c); } });
      tbody.appendChild(tr);
    });
  }

  function list(title, items) {
    if (!items || !items.length) return null;
    return el("div", { cls: "block" }, [el("h4", { text: title }), el("ul", {}, items.map(function (t) { return el("li", { text: t }); }))]);
  }

  function openDetail(c) {
    var comp = state.comps[c.component_id] || {};
    var d = $("detail");
    d.innerHTML = "";
    d.appendChild(el("p", { cls: "muted small", text: "#" + c.rank + " in this run, " + (comp.name || "") }));
    d.appendChild(el("h3", { text: c.name + (c.ticker ? " (" + c.ticker + ")" : "") }));
    if (c.thesis_summary) d.appendChild(el("p", { text: c.thesis_summary }));

    var bd = el("div", { cls: "block" }, [el("h4", { text: "Moat score: " + c.score.composite + " of 100" })]);
    BREAKDOWN.forEach(function (row) {
      var v = c.score.breakdown[row[0]] || 0;
      bd.appendChild(el("div", { cls: "bd" }, [el("span", { text: row[1] }), bar(v, row[2]), el("span", { cls: "muted small", text: v + " / " + row[2] })]));
    });
    var sole = c.single_source_claimed
      ? (c.single_source_credited ? "Sole-source claim confirmed by " + c.independent_domains + " independent domains." : "Sole-source claimed but not credited: needs two independent domains, found " + c.independent_domains + ".")
      : null;
    if (sole) bd.appendChild(el("p", { cls: "small", text: sole }));
    d.appendChild(bd);

    var facts = el("dl", { cls: "facts" });
    [["Share", c.market_share_bucket], ["Market structure", c.structure], ["Supply", c.supply_status],
     ["Switching costs", c.switching_costs], ["Demand", c.demand_signal],
     ["Moat types", (c.moat_types || []).join(", ")]].forEach(function (f) {
      if (!f[1]) return;
      facts.appendChild(el("dt", { text: f[0] }));
      facts.appendChild(el("dd", { text: f[1] }));
    });
    d.appendChild(facts);

    [list("Catalysts", c.catalysts), list("Risks", c.risks)].forEach(function (b) { if (b) d.appendChild(b); });

    var council = el("div", { cls: "block" }, [el("h4", {}, ["Investor council ", consensusBadge(c.council)])]);
    var grid = el("div", { cls: "council" });
    c.council.verdicts.forEach(function (v) {
      var tone = /BUY/.test(v.verdict) ? "good" : (/AVOID|PASS/.test(v.verdict) ? "bad" : "mid");
      grid.appendChild(el("div", { cls: "vote" }, [
        el("div", {}, [el("b", { text: v.investor + " lens" }), " ", el("span", { cls: "badge " + tone, text: v.verdict.replace("_", " ").toLowerCase() })]),
        el("div", { cls: "small", text: v.reason || "" })
      ]));
    });
    council.appendChild(grid);
    council.appendChild(el("p", { cls: "muted small", text: "Each lens is a rule-based rubric inspired by a well-known investing style. It is not the person's view." }));
    d.appendChild(council);

    if (c.signals && c.signals.length) {
      d.appendChild(el("div", { cls: "block" }, [el("h4", { text: "Policy and flow signals" }),
        el("ul", {}, c.signals.map(function (s) {
          var u = safeUrl(s.source_url);
          return el("li", {}, [u ? el("a", { href: u, target: "_blank", rel: "noopener noreferrer", text: s.headline }) : s.headline, s.note ? el("span", { cls: "muted", text: ": " + s.note }) : null]);
        }))]));
    }

    var ev = (c.evidence || []).filter(function (e) { return safeUrl(e.source_url); });
    d.appendChild(el("div", { cls: "block" }, [el("h4", { text: "Sources" }),
      ev.length ? el("ul", {}, ev.map(function (e) {
        return el("li", {}, [el("a", { href: e.source_url, target: "_blank", rel: "noopener noreferrer", text: e.source_name || e.source_url }), e.claim ? el("span", { cls: "muted", text: ": " + e.claim }) : null]);
      })) : el("p", { cls: "muted small", text: "No cited sources in this run." })]));

    $("panel").hidden = false;
    $("close").focus();
  }

  function renderStack() {
    var root = $("stack");
    root.innerHTML = "";
    var groups = {};
    state.data.components.forEach(function (comp) {
      (groups[comp.category] = groups[comp.category] || []).push(comp);
    });
    var cats = Object.keys(groups).sort(function (a, b) {
      return (CATEGORY_ORDER.indexOf(a) + 100) % 100 - (CATEGORY_ORDER.indexOf(b) + 100) % 100;
    });
    cats.forEach(function (cat) {
      var col = el("div", { cls: "layer" }, [el("h4", { text: catLabel(cat) })]);
      groups[cat].forEach(function (comp) {
        var cos = state.data.companies.filter(function (c) { return c.component_id === comp.id; });
        var lead = cos[0];
        var item = el("div", { cls: "comp", title: comp.description || "" }, [
          el("div", { cls: "co", text: comp.name }),
          el("div", { cls: "muted small", text: lead ? "Top: " + lead.name + " (" + lead.score.composite + ")" : "No companies scored" })
        ]);
        if (lead) {
          item.tabIndex = 0;
          item.addEventListener("click", function () { openDetail(lead); });
          item.addEventListener("keydown", function (e) { if (e.key === "Enter") openDetail(lead); });
        }
        col.appendChild(item);
      });
      root.appendChild(col);
    });
  }

  function renderHistory() {
    fetch("data/history/index.json", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : { runs: [] }; })
      .then(function (h) {
        var ul = $("history");
        ul.innerHTML = "";
        (h.runs || []).forEach(function (run) {
          ul.appendChild(el("li", {}, [
            el("a", { href: "data/" + run.file, text: run.run_date }),
            el("span", { cls: "muted", text: ": " + run.companies + " companies" + (run.sample ? " (sample)" : "") + (run.top && run.top.length ? ", top: " + run.top.join(", ") : "") })
          ]));
        });
        if (!ul.children.length) ul.appendChild(el("li", { cls: "muted", text: "No runs yet." }));
      }).catch(function () {});
  }

  function init(d) {
    state.data = d;
    d.components.forEach(function (c) { state.comps[c.id] = c; });
    var cats = {};
    d.components.forEach(function (c) { cats[c.category] = true; });
    var sel = $("cat");
    CATEGORY_ORDER.concat(Object.keys(cats)).forEach(function (c) {
      if (cats[c]) { sel.appendChild(el("option", { value: c, text: catLabel(c) })); delete cats[c]; }
    });
    renderMeta(d);
    renderBoard();
    renderStack();
    renderHistory();
    ["q", "cat", "pub"].forEach(function (id) { $(id).addEventListener("input", renderBoard); });
    $("close").addEventListener("click", function () { $("panel").hidden = true; });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") $("panel").hidden = true; });
  }

  fetch("data/latest.json", { cache: "no-store" })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(init)
    .catch(function () {
      var b = $("banner");
      b.hidden = false;
      b.textContent = "Could not load data/latest.json. If you opened this file directly, serve the docs folder instead: python -m http.server -d docs";
    });
})();
