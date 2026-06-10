"use client";
import { useEffect, useMemo, useRef, useState } from "react";

const TROOPS = ["Infantry", "Archer", "Cavalry", "Chariot"];
const ROLE_COLOR = {
  DPS: "#f0883e", Heal: "#3fb950", "CC (Control)": "#c678dd",
  Buff: "#56b6c2", Debuff: "#d29922",
};
const fmt = (n) => (n >= 1e6 ? (n / 1e6).toFixed(2) + "M" : n >= 1e3 ? (n / 1e3).toFixed(0) + "k" : Math.round(n));

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
  const [commander, setCommander] = useState(0);
  const [optimalTroop, setOptimalTroop] = useState(true);
  const [battles, setBattles] = useState(60);
  const [opponents, setOpponents] = useState(40);
  const [pickIdx, setPickIdx] = useState(-1);
  const [filter, setFilter] = useState("");
  const [job, setJob] = useState(null);     // {status, done, total}
  const [result, setResult] = useState(null);
  const [sortW, setSortW] = useState("win"); // win | early | mid | late | all
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
    const s = [...slots];
    s[pickIdx] = h.id;
    setSlots(s);
    setPickIdx(-1);
    setFilter("");
  }

  async function start() {
    setResult(null);
    const body = {
      heroes: slots, battles, opponents,
      select_optimal_troop: optimalTroop,
      // map UI commander (slot index) — backend re-derives commander per build,
      // but we pass it as the seed preference is irrelevant; commander is searched.
    };
    const r = await fetch("/api/simulate", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then((x) => x.json());
    if (r.error) { alert(r.error); return; }
    setJob({ status: "running", done: 0, total: 192 });
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
    a.href = URL.createObjectURL(blob);
    a.download = `lam-sim-${slots.join("-")}.json`;
    a.click();
  }

  // ranked rows, sorted by chosen column
  const rows = useMemo(() => {
    if (!result) return [];
    const rs = [...result.ranking];
    if (sortW === "win") rs.sort((a, b) => b.win_rate - a.win_rate || b.win_rate_worst_quartile - a.win_rate_worst_quartile);
    else rs.sort((a, b) => b.windows[sortW].mean - a.windows[sortW].mean);
    return rs;
  }, [result, sortW]);

  const heroOrder = result ? result.heroes : chosen.map((id) => byId[id]);
  function BuildLabel({ plan }) {
    return (
      <span>
        {plan.hero_ids.map((hid, i) => (
          <span key={i}>
            {i === plan.commander_index && <span className="crown" title="Commander">♛ </span>}
            {byId[hid] ? byId[hid].name : "#" + hid}
            <span className={"troop " + TROOPS[plan.troop_types[i] - 1]}>{TROOPS[plan.troop_types[i] - 1]}</span>
            {i < 2 && <span className="muted"> · </span>}
          </span>
        ))}
      </span>
    );
  }

  return (
    <div className="wrap">
      <header className="app">
        <h1>⚔️ Lord &amp; Maiden — Battle Simulator</h1>
        <span className="tag">Monte-Carlo · multi-core · model-relative</span>
      </header>
      {meta && <div className="caveat">{meta.caveat}</div>}

      <div className="grid">
        {/* hero selection */}
        <div className="panel">
          <h2>Formation — pick 3 heroes · ♛ sets the commander</h2>
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
                        <div className="sub">{h.role}</div>
                      </div>
                      <button
                        className={"cmd-btn" + (commander === i ? " on" : "")}
                        onClick={(e) => { e.stopPropagation(); setCommander(i); }}
                        title="Commander (the win-anchor; lower target weight)"
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
          <h2>Simulation settings</h2>
          <div className="controls">
            <div className="control">
              <label
                className="switch-label"
                title="ON: report the single best troop assignment. OFF: rank every troop combination (4³ per commander)."
              >
                <span
                  className={"switch" + (optimalTroop ? " on" : "")}
                  onClick={() => setOptimalTroop(!optimalTroop)}
                >
                  <span className="box" />
                </span>
                <span style={{ marginLeft: 10 }}>
                  Select optimal troop type {optimalTroop ? "(auto-pick best)" : "(try every combo)"}
                </span>
              </label>
            </div>
            <div className="control" />
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
          </div>
          <div className="row" style={{ marginTop: 16, justifyContent: "space-between" }}>
            <span className="muted">
              {chosen.length === 3
                ? `≈ ${(192 * battles * opponents).toLocaleString()} battles across 192 builds`
                : `select ${3 - chosen.length} more hero(es)`}
            </span>
            <button className="go" disabled={!ready} onClick={start}>
              {job && job.status === "running" ? "Simulating…" : "▶ Start simulation"}
            </button>
          </div>

          {job && (
            <div style={{ marginTop: 16 }}>
              <div className="bar"><div style={{ width: `${(100 * job.done) / (job.total || 192)}%` }} /></div>
              <div className="row" style={{ marginTop: 6 }}>
                {job.status === "running" && <span className="spinner" />}
                <span className="muted">
                  {job.status === "running"
                    ? `${job.done}/${job.total} builds evaluated`
                    : job.status === "done" ? "Done." : "…"}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* results */}
        {result && (
          <>
            <div className="panel">
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 14 }}>
                <h2 style={{ margin: 0 }}>Recommendation</h2>
                <button className="ghost" onClick={exportJson}>⬇ Export JSON</button>
              </div>
              <div className="hero-rec">
                <div>
                  <div className="muted">BEST OVERALL FORMATION (by win rate)</div>
                  <div className="big" style={{ marginTop: 6 }}>
                    <BuildLabel plan={rows.length ? result.ranking[0].plan : { hero_ids: [], troop_types: [], commander_index: 0 }} />
                  </div>
                  <div className="muted" style={{ marginTop: 6 }}>
                    win {(100 * result.ranking[0].win_rate).toFixed(1)}% · avg {result.ranking[0].avg_bouts.toFixed(1)} bouts ·
                    vs {result.opponent_pool.length} opponent formations · {result.options.total_battles.toLocaleString()} battles
                    {result.elapsed_seconds ? ` · ${result.elapsed_seconds}s` : ""}
                  </div>
                </div>
              </div>
              <div className="cards" style={{ marginTop: 14 }}>
                {["early", "mid", "late", "all"].map((w) => (
                  <div className="card" key={w}>
                    <div className="k">Best for {w} {meta && `(${meta.windows[w]})`}</div>
                    <div className="v">{result.best_by_window[w]}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel">
              <h2>Ranked builds — click a window to sort by its damage</h2>
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Build (♛ = commander)</th>
                    <th className={sortW === "win" ? "sorted" : ""} onClick={() => setSortW("win")}>Win&nbsp;%</th>
                    <th className="right">Bouts</th>
                    {["early", "mid", "late", "all"].map((w) => (
                      <th key={w} className={"right " + (sortW === w ? "sorted" : "")} onClick={() => setSortW(w)}>
                        {w} dmg
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.slice(0, 25).map((r, i) => (
                    <tr key={i}>
                      <td className="muted">{i + 1}</td>
                      <td><BuildLabel plan={r.plan} /></td>
                      <td>
                        <div className="winbar">
                          <span className="mono">{(100 * r.win_rate).toFixed(1)}</span>
                          <span className="t"><div style={{ width: `${100 * r.win_rate}%` }} /></span>
                          <span className="muted mono" style={{ fontSize: 11 }}>±{(100 * r.win_rate_ci95).toFixed(1)}</span>
                        </div>
                      </td>
                      <td className="right mono">{r.avg_bouts.toFixed(1)}</td>
                      {["early", "mid", "late", "all"].map((w) => (
                        <td key={w} className="right mono" title={`p10 ${fmt(r.windows[w].p10)} · p50 ${fmt(r.windows[w].p50)} · p90 ${fmt(r.windows[w].p90)}`}>
                          {fmt(r.windows[w].mean)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ marginTop: 12 }} className="opp-pool">
                <span>Opponent pool:</span>
                {result.opponent_pool.slice(0, 16).map((t, i) => (
                  <span key={i} className="opp-pill">{t.join(" / ")}</span>
                ))}
                {result.opponent_pool.length > 16 && <span>+{result.opponent_pool.length - 16} more</span>}
              </div>
            </div>
          </>
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
                  <div key={h.id} className={"opt" + (taken ? " dis" : "")}
                    onClick={() => !taken && choose(h)}>
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
