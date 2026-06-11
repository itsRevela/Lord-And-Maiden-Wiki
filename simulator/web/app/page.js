"use client";
import { useEffect, useMemo, useRef, useState } from "react";

const TROOPS = ["Infantry", "Archer", "Cavalry", "Chariot"];
const ALLOCS = [
  { v: "atk", label: "ATK" }, { v: "def", label: "DEF" },
  { v: "ruin", label: "Ruin/DES" }, { v: "speed", label: "Speed" },
];
const AXES = [
  { v: "troop", label: "Troop type" }, { v: "skills", label: "Modular skills" },
  { v: "stone", label: "Skill stone" }, { v: "relic", label: "Relic" },
];
const ROLE_COLOR = {
  DPS: "#f0883e", Heal: "#3fb950", "CC (Control)": "#c678dd",
  Buff: "#56b6c2", Debuff: "#d29922",
};
const fmt = (n) => (n >= 1e6 ? (n / 1e6).toFixed(2) + "M" : n >= 1e3 ? (n / 1e3).toFixed(0) + "k" : Math.round(n));
const pct = (x) => (100 * (x || 0)).toFixed(1);

function avatarColor(h) {
  return ROLE_COLOR[h.role] || ["#6e9bff", "#b08bff", "#56b6c2", "#e5c07b", "#f0883e"][h.star % 5];
}
function Portrait({ h, cls }) {
  const [bad, setBad] = useState(false);
  if (bad || !h.has_portrait)
    return <div className={(cls || "") + " avatar"} style={{ background: avatarColor(h) }}>{h.name[0]}</div>;
  return <img className={cls} src={`/portraits/${h.icon}.png`} alt={h.name} onError={() => setBad(true)} />;
}
const Stars = ({ n }) => <span className="stars">{"★".repeat(n)}</span>;

export default function Page() {
  const [heroes, setHeroes] = useState([]);
  const [meta, setMeta] = useState(null);
  const [slots, setSlots] = useState([null, null, null]);
  const [commander, setCommander] = useState(0);                       // FIXED commander slot
  const [allocations, setAllocations] = useState(["atk", "atk", "atk"]); // per-hero max-allocated stat
  const [troopTypes, setTroopTypes] = useState([2, 2, 2]);             // per-hero troop (1..4); used when troop axis off
  const [axes, setAxes] = useState({ troop: true, skills: true, stone: true, relic: true });
  const [workers, setWorkers] = useState(0);                           // 0 = all cores
  const [objective, setObjective] = useState("win");                   // win | casualty | early | mid | late | all
  const [battles, setBattles] = useState(60);
  const [opponents, setOpponents] = useState(40);
  const [topN, setTopN] = useState(20);
  const [pickIdx, setPickIdx] = useState(-1);
  const [filter, setFilter] = useState("");
  const [job, setJob] = useState(null);
  const [result, setResult] = useState(null);
  const [sortBy, setSortBy] = useState("win");                         // win | casualty
  const [openBuild, setOpenBuild] = useState(null);                    // drill-down build index
  const poll = useRef(null);

  useEffect(() => {
    fetch("/api/heroes").then((r) => r.json()).then(setHeroes).catch(() => {});
    fetch("/api/meta").then((r) => r.json()).then(setMeta).catch(() => {});
    return () => clearInterval(poll.current);
  }, []);

  const byId = useMemo(() => Object.fromEntries(heroes.map((h) => [h.id, h])), [heroes]);
  const chosen = slots.filter(Boolean);
  const ready = chosen.length === 3 && !(job && job.status === "running");

  const filtered = useMemo(() => {
    const f = filter.trim().toLowerCase();
    return heroes.filter((h) => !f || h.name.toLowerCase().includes(f) ||
      h.race.toLowerCase().includes(f) || h.rst.toLowerCase().includes(f) ||
      h.role.toLowerCase().includes(f));
  }, [heroes, filter]);

  function choose(h) {
    const s = [...slots]; s[pickIdx] = h.id; setSlots(s);
    const rstIdx = TROOPS.indexOf(h.rst);          // default troop = the hero's natural RST
    if (rstIdx >= 0) { const t = [...troopTypes]; t[pickIdx] = rstIdx + 1; setTroopTypes(t); }
    setPickIdx(-1); setFilter("");
  }
  function setAlloc(i, v) { const a = [...allocations]; a[i] = v; setAllocations(a); }
  function setTroop(i, v) { const t = [...troopTypes]; t[i] = +v; setTroopTypes(t); }

  async function start() {
    setResult(null); setOpenBuild(null);
    const search_axes = AXES.map((a) => a.v).filter((v) => axes[v]);
    const body = {
      heroes: slots, mode: "optimize", objective,
      commander_index: commander, allocated_stats: allocations, troop_types: troopTypes,
      search_axes, workers: +workers || 0, battles, opponents, top_n: topN,
    };
    const r = await fetch("/api/simulate", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then((x) => x.json());
    if (r.error) { alert(r.error); return; }
    setJob({ status: "running", done: 0, total: 24 });
    poll.current = setInterval(async () => {
      const st = await fetch(`/api/jobs/${r.job_id}`).then((x) => x.json());
      setJob(st);
      if (st.status === "done") { clearInterval(poll.current); setResult(st.result); }
      if (st.status === "error") { clearInterval(poll.current); alert("Sim error: " + st.error); }
    }, 350);
  }

  function exportJson() {
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = `lam-sim-${slots.join("-")}.json`; a.click();
  }

  // ranked builds, sorted by chosen metric
  const builds = useMemo(() => {
    if (!result || !result.builds) return [];
    const bs = result.builds.map((b, i) => ({ ...b, _i: i }));
    if (sortBy === "casualty") bs.sort((a, b) => a.casualty_rate - b.casualty_rate || b.win_rate - a.win_rate);
    else bs.sort((a, b) => b.win_rate - a.win_rate || a.casualty_rate - b.casualty_rate);
    return bs;
  }, [result, sortBy]);

  const detail = openBuild != null && result && result.builds ? result.builds[openBuild] : null;

  return (
    <div className="wrap">
      <header className="app">
        <h1>⚔️ Lord &amp; Maiden — Battle Simulator</h1>
        <span className="tag">Monte-Carlo · multi-core · model-relative</span>
      </header>
      {meta && <div className="caveat">{meta.caveat}</div>}

      <div className="grid">
        {/* hero selection + allocation */}
        <div className="panel">
          <h2>Formation — pick 3 heroes · ♛ sets the (fixed) commander · choose each hero's max‑allocated stat</h2>
          <div className="slots">
            {[0, 1, 2].map((i) => {
              const h = slots[i] ? byId[slots[i]] : null;
              return (
                <div key={i} className={"slot" + (h ? "" : " empty")} onClick={() => setPickIdx(i)}>
                  {h ? (
                    <>
                      <Portrait h={h} cls="por" />
                      <div className="meta">
                        <div className="nm">{h.name}</div>
                        <div className="sub"><Stars n={h.star} /> · {h.race} · {h.rst}</div>
                        <div className="row" style={{ marginTop: 4, gap: 6 }} onClick={(e) => e.stopPropagation()}>
                          <span className="muted" style={{ fontSize: 11 }}>Allocate</span>
                          <select className="sel" style={{ padding: "2px 6px" }} value={allocations[i]}
                            onChange={(e) => setAlloc(i, e.target.value)}>
                            {ALLOCS.map((a) => <option key={a.v} value={a.v}>{a.label}</option>)}
                          </select>
                        </div>
                        <div className="row" style={{ marginTop: 4, gap: 6 }} onClick={(e) => e.stopPropagation()}>
                          <span className="muted" style={{ fontSize: 11 }}>Troop</span>
                          <select className="sel" style={{ padding: "2px 6px" }} value={troopTypes[i]}
                            onChange={(e) => setTroop(i, e.target.value)}
                            title={axes.troop ? "Seeds the troop search (axis ON)" : "Used as-is (troop axis OFF)"}>
                            {TROOPS.map((t, ti) => <option key={t} value={ti + 1}>{t}</option>)}
                          </select>
                          {axes.troop && <span className="muted" style={{ fontSize: 10 }}>(searched)</span>}
                        </div>
                      </div>
                      <button
                        className={"cmd-btn" + (commander === i ? " on" : "")}
                        onClick={(e) => { e.stopPropagation(); setCommander(i); }}
                        title="Fixed commander (not permuted by the search)"
                      >♛ {commander === i ? "Commander" : "set CMD"}</button>
                    </>
                  ) : (<span>+ select hero {i + 1}</span>)}
                </div>
              );
            })}
          </div>
        </div>

        {/* controls */}
        <div className="panel">
          <h2>Search settings — top builds (5★ skills/stones, max‑tier troops)</h2>
          <div className="controls">
            <div className="control">
              <label>Maximize</label>
              <select className="sel" value={objective} onChange={(e) => setObjective(e.target.value)}>
                <option value="win">Win rate</option>
                <option value="casualty">Fewest casualties</option>
                <option value="early">Early-round damage (1-2)</option>
                <option value="mid">Mid-round damage (3-4)</option>
                <option value="late">Late-round damage (5+)</option>
                <option value="all">Total damage (all 8)</option>
              </select>
            </div>
            <div className="control">
              <label>CPU cores <span className="muted">(0 = all)</span></label>
              <input className="sel" type="number" min="0" max="64" value={workers}
                onChange={(e) => setWorkers(e.target.value)} />
            </div>
          </div>

          <div className="control" style={{ marginTop: 12 }}>
            <label>Search axes <span className="muted">(toggle what the optimizer varies; commander &amp; allocation stay fixed)</span></label>
            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 6 }}>
              {AXES.map((a) => (
                <button key={a.v}
                  className={"seg-btn" + (axes[a.v] ? " on" : "")}
                  style={{ padding: "6px 12px" }}
                  onClick={() => setAxes({ ...axes, [a.v]: !axes[a.v] })}>{a.label}</button>
              ))}
            </div>
          </div>

          <div className="controls" style={{ marginTop: 12 }}>
            <div className="control">
              <label>Battles per matchup: <b>{battles}</b></label>
              <input type="range" min="20" max="200" step="10" value={battles}
                onChange={(e) => setBattles(+e.target.value)} />
            </div>
            <div className="control">
              <label>Opponent formations: <b>{opponents}</b></label>
              <input type="range" min="10" max="120" step="5" value={opponents}
                onChange={(e) => setOpponents(+e.target.value)} />
            </div>
            <div className="control">
              <label>Top builds to rank: <b>{topN}</b></label>
              <input type="range" min="5" max="50" step="5" value={topN}
                onChange={(e) => setTopN(+e.target.value)} />
            </div>
          </div>

          <div className="row" style={{ marginTop: 16, justifyContent: "space-between" }}>
            <span className="muted">
              {chosen.length !== 3
                ? `select ${3 - chosen.length} more hero(es)`
                : `genetic top-${topN} over ${AXES.filter((a) => axes[a.v]).map((a) => a.label).join(" · ") || "(no axis selected!)"} · objective: ${objective}`}
            </span>
            <button className="go" disabled={!ready} onClick={start}>
              {job && job.status === "running" ? "Simulating…" : "▶ Start search"}
            </button>
          </div>

          {job && (
            <div style={{ marginTop: 16 }}>
              <div className="bar"><div style={{ width: `${(100 * job.done) / (job.total || 24)}%` }} /></div>
              <div className="row" style={{ marginTop: 6 }}>
                {job.status === "running" && <span className="spinner" />}
                <span className="muted">
                  {job.status === "running" ? `${job.done}/${job.total} generations evaluated`
                    : job.status === "done" ? "Done." : "…"}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* results — ranked builds */}
        {result && result.builds && (
          <div className="panel">
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
              <h2 style={{ margin: 0 }}>Top builds — click a row for full detail</h2>
              <button className="ghost" onClick={exportJson}>⬇ Export JSON</button>
            </div>
            <div className="muted" style={{ marginBottom: 10, fontSize: 12 }}>
              Fixed: ♛ {byId[slots[result.commander_index]] ? byId[slots[result.commander_index]].name : "cmd"} ·
              {" "}allocation {result.allocation.map((a, i) => `${byId[slots[i]] ? byId[slots[i]].name : i}:${a || "—"}`).join(" / ")} ·
              {" "}searched {result.search_axes.join(", ")}
            </div>
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Build (♛ = commander)</th>
                  <th className={sortBy === "win" ? "sorted" : ""} onClick={() => setSortBy("win")}>Win&nbsp;%</th>
                  <th className={"right " + (sortBy === "casualty" ? "sorted" : "")} onClick={() => setSortBy("casualty")}>Casualties</th>
                  <th className="right">Units&nbsp;lost</th>
                  <th className="right">All dmg</th>
                </tr>
              </thead>
              <tbody>
                {builds.map((b, i) => (
                  <tr key={b._i} className={"clickable" + (openBuild === b._i ? " sorted" : "")}
                    onClick={() => setOpenBuild(openBuild === b._i ? null : b._i)} style={{ cursor: "pointer" }}>
                    <td className="muted">{i + 1}</td>
                    <td>{b.heroes.map((h, j) => (
                      <span key={j}>
                        {h.is_commander && <span className="crown">♛ </span>}
                        {h.name}<span className={"troop " + h.troop}>{h.troop}</span>
                        {j < 2 && <span className="muted"> · </span>}
                      </span>
                    ))}</td>
                    <td><div className="winbar">
                      <span className="mono">{pct(b.win_rate)}</span>
                      <span className="t"><div style={{ width: `${100 * b.win_rate}%` }} /></span>
                    </div></td>
                    <td className="right mono">{pct(b.casualty_rate)}%</td>
                    <td className="right mono">{(b.avg_units_lost || 0).toFixed(2)}</td>
                    <td className="right mono">{fmt((b.windows && b.windows.all) || 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* drill-down */}
            {detail && (
              <div style={{ marginTop: 16, borderTop: "1px solid var(--line, #2a2f3a)", paddingTop: 14 }}>
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <h2 style={{ margin: 0 }}>Build detail — {detail.label}</h2>
                  <button className="ghost" onClick={() => setOpenBuild(null)}>✕ close</button>
                </div>
                <div className="muted" style={{ margin: "6px 0 12px" }}>
                  win {pct(detail.win_rate)}% · casualties {pct(detail.casualty_rate)}% · units lost {(detail.avg_units_lost || 0).toFixed(2)}/3 ·
                  {" "}early {fmt(detail.windows.early)} · mid {fmt(detail.windows.mid)} · late {fmt(detail.windows.late)} · all {fmt(detail.windows.all)} dmg
                </div>
                <div className="cards" style={{ gridTemplateColumns: "repeat(3,1fr)" }}>
                  {detail.heroes.map((h, j) => (
                    <div className="card" key={j}>
                      <div className="k">
                        {h.is_commander && <span className="crown">♛ </span>}{h.name}
                        <span className={"troop " + h.troop} style={{ marginLeft: 6 }}>{h.troop}</span>
                      </div>
                      <div className="v" style={{ fontWeight: 500 }}>
                        <div className="muted" style={{ fontSize: 11 }}>ALLOCATION</div>{h.allocation}
                        <div className="muted" style={{ fontSize: 11, marginTop: 6 }}>MAIN (fixed)</div>{h.main_skill}
                        <div className="muted" style={{ fontSize: 11, marginTop: 6 }}>MODULAR</div>{h.modular_skills.join(" · ")}
                        <div className="muted" style={{ fontSize: 11, marginTop: 6 }}>SKILL STONE</div>{h.skill_stone}
                        <div className="muted" style={{ fontSize: 11, marginTop: 6 }}>RELIC</div>{h.relic}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <p className="muted" style={{ fontSize: 12, marginTop: 14 }}>
              5★ skills/stones only; stone must match a modular (reinforces it). Space is large, so this is a
              genetic top‑{topN} — strong builds, not a proven global optimum. Re-run for a second opinion.
            </p>
          </div>
        )}
      </div>

      {/* hero picker modal */}
      {pickIdx >= 0 && (
        <div className="picker-back" onClick={() => setPickIdx(-1)}>
          <div className="picker" onClick={(e) => e.stopPropagation()}>
            <div className="top">
              <input autoFocus placeholder="Search name / race / soldier type / role…"
                value={filter} onChange={(e) => setFilter(e.target.value)} />
              <button className="ghost" onClick={() => setPickIdx(-1)}>Close</button>
            </div>
            <div className="list">
              {filtered.map((h) => {
                const taken = slots.includes(h.id) && slots[pickIdx] !== h.id;
                return (
                  <div key={h.id} className={"opt" + (taken ? " dis" : "")} onClick={() => !taken && choose(h)}>
                    <Portrait h={h} />
                    <div>
                      <div className="nm">{h.name} <Stars n={h.star} /></div>
                      <div className="sub">{h.race} · {h.rst} · {h.role}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
