# Tools

Extraction, generation, and live-capture tooling for the *Lord and Maiden* wiki.

| Tool | Purpose |
|---|---|
| `wikigen/` | The wiki generator (`build.py`) + integrity/accuracy checker (`verify.py`). |
| `extract_xml_configs.py`, `extract_scriptableobjects.py`, `extract_prop_assets.py` | Pull configs / icons / assets from the game's (unencrypted) YooAsset bundles. |
| `lam_battle_sniffer.py` | Passive battle-report sniffer — the shared TCP framing / gzip / `Proto` / flow-reassembly stack the quiz tools reuse. |
| `lam_question_capture.py` | Raw capture + decoder for quiz traffic (used to verify the protocol). |
| `lam_question_monitor.py` | **The Knowledge Quiz scanner** — live answer monitor (see below). |

---

## Knowledge Quiz / Question Scanner

`lam_question_monitor.py` passively reads the game's live (unencrypted) server→client stream
and, for each daily Knowledge-Quiz question, prints the correct answer. It **self-learns**:
every answer the server reveals is stored in `data/quiz_answer_key.json`, so coverage grows
toward the full question pool with play.

### For Claude — what to do on "start knowledge quiz scanner" / "start question scanner"

When the user asks to **start the knowledge quiz scanner / question scanner / quiz monitor**,
**run the monitor yourself in the background — do not hand the user a command to paste.**

**Prerequisite — Npcap (Windows).** The scanner uses `scapy`, which needs **Npcap** installed.
Assume the user has it. Crucially, Npcap's installer leaves the *"Restrict Npcap driver's
access to Administrators only"* option **unchecked by default**, so on a typical install
**packet capture does NOT require administrator rights** — you can launch the capture directly
via the background shell. You do **not** need to instruct the user to open an elevated terminal
or paste a PowerShell command. Only if the launch fails with a permission/access error (meaning
they enabled Npcap's admin-only mode) should you then ask them to run it elevated. If `scapy`
or Npcap is missing entirely: `pip install scapy` and install Npcap from <https://npcap.com>.

**Run it (background), then relay each detected question + answer to the user:**

```bash
# 1) find the active NIC (Windows):
#    Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Sort-Object RouteMetric |
#      Select-Object -First 1 | Get-NetAdapter | ForEach-Object Name
# 2) launch in the background:
PYTHONUTF8=1 python tools/lam_question_monitor.py --live --iface "<active NIC>"
```

- `--iface` and `--filter` are **optional**. With no `--filter` it defaults to `tcp` and
  auto-detects the game stream by its `SC*/CS*` message-name signature. Once you know the game
  server IP (it prints in captures, e.g. `43.159.0.212`), add `--filter "host <ip>"` to cut noise.
- The monitor runs in *your* (the agent's) shell, so its output isn't on the user's screen —
  **you relay each question and answer.**

**Stop it:** terminate the `python.exe` whose command line contains `lam_question_monitor`, e.g.

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*lam_question_monitor*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

### Daily vs shared/help questions
- **Daily quiz** questions carry a progress string (`Knowledge Quiz Progress:N/10`) and the
  server reveals the correct answer after you submit — the monitor **auto-learns** these.
- **Shared/help** questions (answering another player's question; **empty progress**) return
  only a reward, with **no answer id** — there's nothing to wait for. The monitor labels these
  `Q [SHARED/HELP question -- no reveal will follow; answer from LORE]`; resolve their answer
  from the hero lore in `wiki/Heroes/roster/` and relay it.

**Full runbook + reverse-engineered protocol:**
[`notes/knowledge-quiz-scanner.md`](../notes/knowledge-quiz-scanner.md).
