# Knowledge-Quiz Scanner — Runbook

Operational guide for the live Knowledge-Quiz answer monitor.

## Trigger phrases
When the user says **"start knowledge quiz scanner"**, **"start question scanner"**, or
**"start the quiz monitor"** → run the monitor (below). When they say **"stop"** it → kill it.

## Start it
The monitor passively reads the game's (unencrypted) server→client TCP stream, decodes each
quiz question, resolves the `{translation-key}` strings to English via `data/localization.json`,
and prints the correct answer. It self-learns every revealed answer.

```bash
# from repo root. PYTHONUTF8=1 keeps the Windows console from choking on CJK keys.
PYTHONUTF8=1 python tools/lam_question_monitor.py --live --iface "Ethernet" --filter "host 43.159.0.212"
```

Run it with `run_in_background: true` (it loops until stopped) and tail its output file to
show the user each decoded question + answer.

- **Npcap & admin:** the scanner needs **Npcap** (a `scapy` dependency on Windows). Npcap's
  installer leaves *"Restrict … to Administrators only"* **off by default**, so capture normally
  needs **no admin** — launch it directly in the background; don't make the user paste a command.
  Only if launch fails with a permission/access error did they enable admin-only mode (then run
  from an elevated terminal). If scapy/Npcap is missing: `pip install scapy` + install Npcap.
  *(This machine: no admin needed — confirmed.)*
- **Interface:** this machine's active NIC is **Ethernet** (Realtek PCIe GbE). Re-derive if
  unsure: `Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Sort RouteMetric | Select -First 1 | Get-NetAdapter | % Name`.
- **`--filter` is optional noise reduction.** The game server seen was `43.159.0.212:9668`,
  but the IP can change; if no quiz traffic appears, drop the filter (defaults to `tcp` and
  auto-detects the game stream by its `SC*/CS*` message-name signature).
- **`--lang`** changes the display language column (default `English_Text`).

## Stop it
```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*lam_question_monitor*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

## What the user sees
```
Q (Knowledge Quiz Progress:5/10 ...):
   <question in English>
   1) [id 1] <option>  <===
   2) [id 2] <option>
   ...
>>> ANSWER: option #1 (id 1) = <answer>   [learned key x3]
```
- **Known question** → answer shown immediately (from the learned key).
- **New question** → shows options + `UNKNOWN`; **learns** the answer when the user submits
  (the post-answer reveal carries the correct option id). The quiz pool repeats daily, so
  coverage climbs toward 100% with play.

## Daily vs shared/help questions
Both arrive via `SCLogic_GetRandomQuestion`, distinguished by the **progress** field:
- **Daily quiz** → progress is populated (`{知识问答} {进度}:N/10 …`). Answering sends
  `SCLogic_SelectQuestionAnser` with the correct `rightId`, so the monitor **learns** it.
- **Shared/help question** (answering another player's question for Friendship Points) →
  **empty progress**. Its result returns as a reward via `SCLogic_AnsweEndBack`, which carries
  **no answer id** — so there is nothing to learn from and nothing to wait for.

The monitor detects empty progress and prints
`Q [SHARED/HELP question -- no reveal will follow; answer from LORE]`. For these it shows the
answer if it's already in our key, otherwise says *"going with a LORE answer (Claude resolves
from the wiki)"* — i.e. **Claude must look the answer up in the hero lore and relay it**; do not
wait for a reveal. (`SendQuestionsHelpInfo` only carries help-point counters, not the question.)

## Answer key (our data)
`data/quiz_answer_key.json` — persistent map keyed by the **canonical Simplified question key**
(language-proof): `{ "<simplified question>": {right_key, answer_en, question_en, count} }`.
Grows automatically from every answered question. Can be bulk-seeded from the wiki's curated
answer key (`wiki/Quests/Knowledge-Quiz.md`) if first-encounter coverage is wanted.

## How it works (protocol — verified by live capture)
- Quiz push = **`SCLogic_GetRandomQuestion`**: question + each option are `{translation-key}`
  strings; **no correct-answer id on the wire**.
- Answer reveal = **`SCLogic_SelectQuestionAnser`** (after you submit): `rightId` = correct
  option id. The monitor correlates it with the last question to learn the answer.
- Keys resolve via `data/localization.json` (`{key} → {Simplified/Traditional/English/Japanese/Korean}_Text`).

## Files
| File | Role |
|---|---|
| `tools/lam_question_monitor.py` | the live monitor (Phase 2) |
| `tools/lam_question_capture.py` | raw capture + decoder (Phase 1) — use to re-verify the protocol |
| `tools/lam_battle_sniffer.py` | shared TCP framing / gzip / `Proto` / flow-reassembly stack |
| `data/quiz_answer_key.json` | the self-learning answer key |
| `notes/sim/captures/questions/` | raw `.bin` + decoded `.json` captures |

To re-verify the protocol (e.g. after a game patch), run the capture tool the same way and
read the decoded `.json` files.
