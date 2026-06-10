# Lord & Maiden — Battle Simulator

Pick **3 heroes**, hit **Start**, and the simulator runs thousands of seeded 8‑round
battles across every build (commander assignment × each hero's troop type) against a
shared pool of opponent formations, then ranks the builds by win rate and by
early / mid / late / all‑round damage. Everything is assumed **maxed** (Lv 80,
advancement, skills, skill stones, equipment, talents, affection, runes).

> **Honest caveat — read this.** *Lord and Maiden* resolves combat on its **servers**;
> the client only receives a replay log, so the exact damage equation is **not**
> extractable. This simulator is therefore a **transparent, configurable, rules‑based
> Monte‑Carlo model**: every value that *is* in the game data (hero/troop stats, skill
> coefficients, trigger probabilities, the restraint triangle, buff families, targeting
> weights, the 8‑round + rematch structure) is used verbatim, and every server‑side
> unknown is a documented, tunable knob on `ModelConfig` (tagged `ASSUMPTION` in
> `engine/model.py`). Rankings are **model‑relative** but directly comparable across
> builds, because the same model is applied to all of them. See
> [`notes/sim/combat_rules.md`](../notes/sim/combat_rules.md) for the full FACT vs
> ASSUMPTION split.

## What it models

* **Troops = health.** A unit's HP = troop count × per‑soldier HP; damage removes
  troops; a side loses when its **Commander's** troops are wiped.
* **8‑round bouts with rematch.** If undecided after 8 rounds, a fresh bout is fought
  with troop counts **carried over**, repeating until a commander falls.
* Turn order by **ATK Spd**; activation order **Passive → Strategic → Tactical →
  Normal → Pursuit**; **restraint** Infantry→Archer→Cavalry→Infantry (Chariot neutral,
  −25 %); 20 / 40 / 40 targeting; status effects (stun / silence / disarm / taunt /
  DoT / shield / lifesteal); soldier + race combination effects; talents; affection.

## Run it

### 1. (one‑time) extract hero portraits — optional but nice
Portraits are copyrighted game art, so they're **not** committed. Extract them from
your local game install (auto‑detected Steam path, or pass `--lam`):
```bash
python -m simulator.tools.extract_portraits
# -> simulator/web/public/portraits/<icon>.png   (113/113 heroes)
```
Without this the UI shows clean lettered avatars instead.

### 2. start the engine API (Python / Flask)
```bash
python -m simulator.web.server          # http://localhost:5000
```

### 3. start the UI (Next.js)
```bash
cd simulator/web
npm install        # first time only
npm run dev        # http://localhost:3000   (or: npm run build && npm start)
```
Open **http://localhost:3000**. The UI proxies `/api/*` and `/portraits/*` to the
Flask backend, so there's one URL to open and no CORS setup.

### CLI (no UI)
```bash
python -m simulator.run --list-heroes
python -m simulator.run --heroes 2 5 9 --battles 80 --opponents 50
python -m simulator.run --heroes 2 5 9 --all-troop-combos      # rank every troop combo
```
Writes a full JSON report to `simulator/runs/` and prints a summary. Uses all CPU cores.

## Layout
```
simulator/
  engine/        pure simulation (no I/O deps)
    data.py        loads data/sim/*.json (the Phase-1 catalogue)
    model.py       maxed-build aggregation + the transparent damage model (ModelConfig)
    combat.py      8-round + rematch resolver, status effects, targeting
    search.py      build × opponent combinatorics, multi-core Monte-Carlo, ranking
  run.py         CLI
  web/
    server.py      Flask API (heroes, meta, async simulate jobs, portraits)
    app/           Next.js front-end (App Router)
    public/portraits/   extracted PNGs (gitignored)
  tools/
    extract_portraits.py   UnityPy bundle → portrait PNG extractor
```

## Tuning the model
All server‑side assumptions live on `ModelConfig` in `engine/model.py`
(`global_lethality`, `def_k`, `hero_ref`, `free_stat_points`, `max_bouts`, …). Change
them in one place; the whole search re‑calibrates. The model is validated to be
**unbiased** (a mirror match is ~50 %).
