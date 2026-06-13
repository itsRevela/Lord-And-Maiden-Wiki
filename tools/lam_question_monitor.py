#!/usr/bin/env python3
r"""PHASE 2 -- live Knowledge-Quiz answer monitor for Lord & Maiden.

Watches the (unencrypted) server->client stream. On every quiz question it
resolves the question + options from the game's TRANSLATION KEYS, looks up the
correct answer in our data, and prints it. It also LEARNS: every time a question
is answered in-game the server reveals the correct option id, which we store --
so coverage grows toward the full question pool over time.

HOW THE WIRE WORKS (captured + verified, see notes/sim/captures/questions/):
  * SCLogic_GetRandomQuestion  = the daily Knowledge-Quiz push. The question and
    every option are sent as {translation-key} strings (e.g. "{瓦妮莎}"), NOT the
    resolved text and NOT the correct answer. We resolve keys via localization.json.
  * SCLogic_SelectQuestionAnser = reply AFTER you answer. Its `rightId` is the
    correct option id -> we correlate it with the last question to learn the answer.

ANSWER SOURCES (in priority order):
  1. wire `rightId` if the message carries it (ServerQuestionInfo, post-answer) -- ground truth
  2. learned answer key  (data/quiz_answer_key.json, grown from past reveals)
  3. unknown            -> shows the question/options so you can answer; learns on reveal

USAGE (same prereqs as the sniffer; admin only if your Npcap needs it):
  python tools/lam_question_monitor.py --live --iface "Ethernet"
  python tools/lam_question_monitor.py --pcap notes/sim/captures/quiz.pcapng
  python tools/lam_question_monitor.py --list-ifaces
Ctrl+C to stop.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lam_question_capture as cap      # decode_question/decode_answer + capture loops (reused)
from lam_battle_sniffer import list_ifaces  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOC_PATH = os.path.join(ROOT, "data", "localization.json")
DB_PATH = os.path.join(ROOT, "data", "quiz_answer_key.json")

BAR = "=" * 64


# --------------------------------------------------------------------------- translation keys
class Loc:
    """Resolve the game's {translation-key} strings to readable text (any language)."""

    def __init__(self, lang: str = "English_Text"):
        with open(LOC_PATH, encoding="utf-8") as f:
            self.map = json.load(f)
        self.lang = lang

    _TOK = re.compile(r"\{([^{}]*)\}")

    @staticmethod
    def key(s: str) -> str:
        """Canonical key = the brace-stripped Simplified text the wire/CSV use as the id.
        Question/option strings are a single {whole-string} token, so this is exact."""
        return (s or "").strip().strip("{}").strip()

    def _resolve(self, k: str) -> str:
        e = self.map.get(k)
        return (e.get(self.lang) or e.get("English_Text") or k) if e else k

    def text(self, s: str) -> str:
        """Resolve to display text. Handles both a single {whole-string} key (question/
        option) and strings with several embedded {token}s mixed with literals (progress)."""
        s = s or ""
        if "{" not in s:
            return self._resolve(s)
        return self._TOK.sub(lambda m: self._resolve(m.group(1)), s).strip()


# --------------------------------------------------------------------------- answer key store
class AnswerKey:
    """Persistent question -> correct-answer map, keyed by the canonical question key."""

    def __init__(self, path: str = DB_PATH):
        self.path = path
        self.db = {}
        if os.path.exists(path):
            try:
                self.db = json.load(open(path, encoding="utf-8"))
            except Exception:
                self.db = {}

    def get(self, qkey: str):
        return self.db.get(qkey)

    def learn(self, qkey: str, right_key: str, right_en: str, question_en: str):
        rec = self.db.get(qkey)
        if rec and rec.get("right_key") == right_key:
            rec["count"] = rec.get("count", 1) + 1
            new = False
        else:
            self.db[qkey] = {"right_key": right_key, "answer_en": right_en,
                             "question_en": question_en, "count": (rec or {}).get("count", 0) + 1}
            new = True
        self._save()
        return new

    def _save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(tmp, self.path)


# --------------------------------------------------------------------------- the engine
class AnswerEngine:
    """Drop-in 'writer' for lam_question_capture.process_live/process_pcap: it exposes
    .handle(name, body, src), .n_msgs, .n_quiz -- so the whole capture stack is reused."""

    def __init__(self, loc: Loc, key: AnswerKey):
        self.loc = loc
        self.key = key
        self.n_msgs = 0
        self.n_quiz = 0
        self.last_q = None          # {qkey, qen, options:[(id, optkey, opten)]}
        self.hits = 0
        self.misses = 0
        self.learned = 0

    # -- console-safe print (Windows cp1252 can't encode CJK; never let it crash) --
    @staticmethod
    def _p(*parts):
        line = " ".join(str(x) for x in parts)
        try:
            print(line)
        except Exception:
            print(line.encode("ascii", "replace").decode("ascii"))

    def handle(self, name: str, body: bytes, src: str = ""):
        self.n_msgs += 1
        if name in cap.QUESTION_MSGS:
            try:
                self.n_quiz += 1
                self._on_question(cap.decode_question(name, body))
            except Exception as e:
                self._p("[!] question decode failed:", type(e).__name__, e)
        elif name in cap.ANSWER_MSGS:
            try:
                self._on_reveal(cap.decode_answer(name, body))
            except Exception as e:
                self._p("[!] reveal decode failed:", type(e).__name__, e)

    def _on_question(self, q: dict):
        qkey = self.loc.key(q.get("question", ""))
        qen = self.loc.text(q.get("question", ""))
        options = [(o["id"], self.loc.key(o["text"]), self.loc.text(o["text"]))
                   for o in q.get("options", [])]
        # Daily-quiz questions always carry a progress string ("{知识问答} {进度}:N/10 ...");
        # a SHARED/HELP question (answering another player's question for Friendship Points)
        # arrives via the same SCLogic_GetRandomQuestion but with EMPTY progress -- and its
        # result comes back as a reward (SCLogic_AnsweEndBack), with NO answer reveal. So for
        # shared questions there's nothing to wait for: the answer must come from lore/our data.
        progress = self.loc.text(q.get("progress", "")).strip()
        is_shared = not progress
        self.last_q = {"qkey": qkey, "qen": qen, "options": options, "shared": is_shared}

        # resolve the answer: 1) wire rightId  2) learned/seeded key
        answer = None       # (option_id, ordinal, answer_en, source)
        wire_right = q.get("rightId")
        if wire_right:
            answer = self._match_id(options, wire_right, "wire rightId")
        if answer is None:
            rec = self.key.get(qkey)
            if rec:
                answer = self._match_key(options, rec["right_key"], rec.get("answer_en", ""),
                                         "answer key x%d" % rec.get("count", 1))

        # display
        self._p("\n" + BAR)
        if is_shared:
            self._p("Q [SHARED/HELP question -- no reveal will follow; answer from LORE]:")
        else:
            self._p("Q (%s):" % progress)
        self._p("   " + qen)
        for ordinal, (oid, _ok, oen) in enumerate(options, 1):
            mark = "  <===" if (answer and oid == answer[0]) else ""
            self._p("   %d) [id %d] %s%s" % (ordinal, oid, oen, mark))
        if answer:
            self.hits += 1
            self._p(">>> ANSWER: option #%d (id %d)  =  %s   [%s]"
                    % (answer[1], answer[0], answer[2], answer[3]))
        elif is_shared:
            self.misses += 1
            self._p(">>> ANSWER: UNKNOWN -- SHARED/HELP question: NO answer reveal will come. "
                    "Going with a LORE answer (Claude resolves from the wiki).")
        else:
            self.misses += 1
            self._p(">>> ANSWER: UNKNOWN -- pick any option; I'll learn it from the reveal.")
        self._p(BAR)

    def _on_reveal(self, a: dict):
        rid = a.get("rightId")
        if rid is None or not self.last_q:
            return
        m = self._match_id(self.last_q["options"], rid, "")
        if not m:
            return
        oid, ordinal, answer_en, _ = m
        right_key = next((ok for (i, ok, _e) in self.last_q["options"] if i == oid), "")
        new = self.key.learn(self.last_q["qkey"], right_key, answer_en, self.last_q["qen"])
        self.learned += 1 if new else 0
        verb = "LEARNED" if new else "confirmed"
        self._p(">>> %s: \"%s\"  ->  #%d %s   (answer key now %d entries)"
                % (verb, self.last_q["qen"], ordinal, answer_en, len(self.key.db)))

    @staticmethod
    def _match_id(options, oid, source):
        for ordinal, (i, _ok, oen) in enumerate(options, 1):
            if i == oid:
                return (i, ordinal, oen, source)
        return None

    @staticmethod
    def _match_key(options, right_key, answer_en, source):
        for ordinal, (i, ok, oen) in enumerate(options, 1):
            if ok == right_key:
                return (i, ordinal, oen or answer_en, source)
        return None


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="LAM Knowledge-Quiz live answer monitor")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--iface", default=None)
    ap.add_argument("--pcap", default=None)
    ap.add_argument("--filter", default="tcp", help="BPF filter (e.g. 'host 43.159.0.212')")
    ap.add_argument("--lang", default="English_Text",
                    help="display language column (English_Text/Simplified_Text/...)")
    ap.add_argument("--list-ifaces", action="store_true")
    args = ap.parse_args()

    for stream in (sys.stdout, sys.stderr):       # UTF-8 tolerant console
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if args.list_ifaces:
        list_ifaces()
        return
    try:
        import scapy  # noqa
    except ImportError:
        print("ERROR: scapy is required.  pip install scapy")
        sys.exit(1)

    engine = AnswerEngine(Loc(args.lang), AnswerKey())
    print("[*] answer key: %s (%d known)" % (DB_PATH, len(engine.key.db)))
    print("[*] monitoring quiz traffic -- open the Knowledge Quiz. Ctrl+C to stop.")
    if args.pcap:
        cap.process_pcap(args.pcap, engine)
    elif args.live:
        cap.process_live(args.iface, engine, args.filter)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
