#!/usr/bin/env python3
r"""PHASE 1 -- raw capture + best-effort decode of Lord & Maiden quiz traffic.

WHY: before building the live answer monitor we want GROUND TRUTH bytes for the
Knowledge-Quiz messages, to confirm (a) exactly which message the quiz uses and
(b) that the byte layout reverse-engineered from the decompiled handlers is right.

This reuses the proven framing/flow/gzip/Proto stack from `lam_battle_sniffer.py`
(server->client is unencrypted) and adds question-specific handling: every quiz
message is dumped RAW (.bin -- nothing lost even if the decode is wrong) AND
best-effort decoded to JSON + a readable console line.

Quiz protocol (decompiled Assembly-CSharp eb46ed1b3cbb.cs):
  SCLogic_GetRandomQuestion  (daily Knowledge Quiz push -- NO answer on the wire):
     string name, int seq, int ID, string QuestionContent, string QuestionProgress,
     PropList RightRewards, PropList ErrorRewards, bool CantShare,
     int N, N*(int optID, string optText)
  SCLogic_ServerQuestionInfo / SCLogic_DesertAdventureQuestionInfo:
     ... same head + int Time after ID ..., then int SelectID, int RightID
        (RightID is typically 0 until the question is answered)
  SCLogic_SelectQuestionAnser (reply AFTER you answer -- REVEALS the answer):
     string name, int seq, int RightOptID, int SelectID, string Progress
  SCLogic_RightAnsweBack:
     string name, int seq, int RightOptID, int (extra)
  PropList = int count, count*(int PropId, long PropCount)

USAGE (same prereqs as the battle sniffer -- admin + Npcap for --live):
  python tools/lam_question_capture.py --live
  python tools/lam_question_capture.py --live --iface "Wi-Fi"
  python tools/lam_question_capture.py --pcap C:\path\quiz.pcapng
  python tools/lam_question_capture.py --list-ifaces

Open the Knowledge Quiz in-game and answer ONE question while capturing. Output
(raw .bin + decoded .json + names.log) lands in notes/sim/captures/questions/.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import struct
import sys

# Reuse the proven low-level stack from the battle sniffer (same directory).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lam_battle_sniffer import Proto, FlowReassembler, _decode_msg, MAX_FRAME, list_ifaces  # noqa: E402

# Quiz message names (from the SCLogic listener table, lines 12251-12253 / 36842+).
QUESTION_MSGS = {
    "SCLogic_GetRandomQuestion",
    "SCLogic_ServerQuestionInfo",
    "SCLogic_DesertAdventureQuestionInfo",
}
ANSWER_MSGS = {
    "SCLogic_SelectQuestionAnser",   # reply after answering -- reveals correct option id
    "SCLogic_RightAnsweBack",
    "SCLogic_SelectAnsweBack",
}
ALL_QUIZ_MSGS = QUESTION_MSGS | ANSWER_MSGS

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "notes", "sim", "captures", "questions")


# --------------------------------------------------------------------------- decode helpers
def _read_bool(p: Proto) -> bool:
    v = p.b[p.o]
    p.o += 1
    return bool(v)


def _read_proplist(p: Proto) -> list:
    out = []
    for _ in range(p.int()):
        out.append({"propId": p.int(), "count": p.long()})
    return out


def decode_question(name: str, body: bytes) -> dict:
    """Best-effort decode of a question message. Errors are caught by the caller."""
    p = Proto(body)
    p.string()                       # message name
    p.int()                          # seq / sub
    q: dict = {"msg": name, "id": p.int()}
    if name == "SCLogic_GetRandomQuestion":
        q["question"] = p.string()
        q["progress"] = p.string()
        q["rightRewards"] = _read_proplist(p)
        q["errorRewards"] = _read_proplist(p)
        q["cantShare"] = _read_bool(p)
        n = p.int()
        q["options"] = [{"id": p.int(), "text": p.string()} for _ in range(n)]
        q["selectId"] = None
        q["rightId"] = None          # not present in this message
    else:                            # ServerQuestionInfo / DesertAdventureQuestionInfo
        q["time"] = p.int()
        q["question"] = p.string()
        q["progress"] = p.string()
        q["rightRewards"] = _read_proplist(p)
        q["errorRewards"] = _read_proplist(p)
        n = p.int()
        q["options"] = [{"id": p.int(), "text": p.string()} for _ in range(n)]
        q["selectId"] = p.int()
        q["rightId"] = p.int()
    q["_unparsed_tail_bytes"] = p.remaining()
    return q


def decode_answer(name: str, body: bytes) -> dict:
    """Decode the post-answer reveal messages (the server tells us the right option)."""
    p = Proto(body)
    p.string()
    p.int()
    a: dict = {"msg": name}
    if name == "SCLogic_SelectQuestionAnser":
        a["rightId"] = p.int()
        a["selectId"] = p.int()
        a["progress"] = p.string()
    elif name == "SCLogic_RightAnsweBack":
        a["rightId"] = p.int()
        a["extra"] = p.int()
    elif name == "SCLogic_SelectAnsweBack":
        a["selectId"] = p.int()
        a["progress"] = p.string()
    a["_unparsed_tail_bytes"] = p.remaining()
    return a


# --------------------------------------------------------------------------- writer
class QuestionWriter:
    def __init__(self, out_dir: str):
        self.dir = out_dir
        os.makedirs(out_dir, exist_ok=True)
        self.names = open(os.path.join(out_dir, "names.log"), "a", encoding="utf-8")
        self.n_msgs = 0
        self.n_quiz = 0
        self._seen = set()

    def _ascii(self, x) -> str:
        return str(x).encode("ascii", "replace").decode("ascii")

    def note(self, name: str, size: int, src: str):
        self.n_msgs += 1
        self.names.write("%s\t%d\t%s\n" % (name, size, src))
        self.names.flush()

    def handle(self, name: str, body: bytes, src: str):
        self.note(name, len(body), src)
        if name not in ALL_QUIZ_MSGS:
            return
        digest = (name, len(body), bytes(body[:32]))
        if digest in self._seen:
            return
        self._seen.add(digest)
        self.n_quiz += 1
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        base = "%s_%s" % (ts, name)
        # 1) RAW dump -- never lose the bytes even if our decode is wrong
        with open(os.path.join(self.dir, base + ".bin"), "wb") as f:
            f.write(body)
        # 2) best-effort decode
        decoded, err = None, None
        try:
            decoded = decode_question(name, body) if name in QUESTION_MSGS else decode_answer(name, body)
        except Exception as e:
            err = "%s: %s" % (type(e).__name__, e)
        rec = {"name": name, "src": src, "raw_len": len(body),
               "raw_hex_head": body[:64].hex(), "decoded": decoded, "decode_error": err}
        with open(os.path.join(self.dir, base + ".json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
        try:                              # a console-encoding error must NEVER kill the capture
            self._print(name, decoded, err, base)
        except Exception as e:
            print("   [print suppressed: %s] -- data saved to %s.json" % (type(e).__name__, base))

    def _print(self, name, decoded, err, base):
        print("\n[QUIZ] %s  -> %s.bin/.json" % (name, base))
        if err:
            print("   decode FAILED (%s) -- raw bytes saved for offline analysis" % err)
            return
        if name in QUESTION_MSGS:
            print("   id=%s progress=%s" % (decoded.get("id"), self._ascii(decoded.get("progress"))))
            print("   Q: %s" % self._ascii(decoded.get("question")))
            for o in decoded.get("options", []):
                mark = ""
                if decoded.get("rightId") and o["id"] == decoded["rightId"]:
                    mark = "  <== RIGHT (on wire)"
                print("     [%s] %s%s" % (o["id"], self._ascii(o["text"]), mark))
            if not decoded.get("rightId"):
                print("   (no correct-answer id on the wire -- monitor must look it up)")
            print("   tail bytes left: %s" % decoded.get("_unparsed_tail_bytes"))
        else:
            extra = {k: self._ascii(v) for k, v in decoded.items()
                     if k not in ("msg", "rightId", "_unparsed_tail_bytes")}
            print("   ANSWER REVEAL: rightId=%s  %s" % (decoded.get("rightId"), extra))


# --------------------------------------------------------------------------- capture loops
def _drain(fr: FlowReassembler, writer: QuestionWriter, src: str):
    """Frame + decode every complete message in the buffer (scan-and-resync; never hard-stop).
    Mirrors the battle sniffer's robust drain, but routes bodies to QuestionWriter.handle."""
    if not fr.buffer:
        return
    stream = bytes(fr.buffer)
    consumed = 0
    o = 0
    n = len(stream)
    while o <= n - 4:
        outer = struct.unpack_from("<i", stream, o)[0]
        if 0 < outer <= MAX_FRAME and o + 4 + outer <= n:
            dec = _decode_msg(stream[o + 4:o + 4 + outer])
            if dec is not None:
                writer.handle(dec[0], dec[1], src)
                fr.is_game = True
                o += 4 + outer
                consumed = o
                continue
        o += 1
    if consumed:
        del fr.buffer[:consumed]
    if fr.is_game is None and len(fr.buffer) > 65536:
        fr.is_game = False
        fr.buffer.clear()
    elif fr.is_game and len(fr.buffer) > 1048576:
        del fr.buffer[:len(fr.buffer) - 262144]


def process_pcap(path: str, writer: QuestionWriter):
    from scapy.all import PcapReader, TCP, IP, IPv6  # noqa
    flows = {}
    for pkt in PcapReader(path):
        if TCP not in pkt:
            continue
        l3 = pkt[IP] if IP in pkt else (pkt[IPv6] if IPv6 in pkt else None)
        if l3 is None:
            continue
        payload = bytes(pkt[TCP].payload)
        if not payload:
            continue
        key = (l3.src, pkt[TCP].sport, l3.dst, pkt[TCP].dport)
        fr = flows.setdefault(key, FlowReassembler())
        fr.add(payload)
        _drain(fr, writer, "%s:%d->%s:%d" % (l3.src, pkt[TCP].sport, l3.dst, pkt[TCP].dport))
    print("\n[done] pcap parsed: %d quiz msgs of %d total." % (writer.n_quiz, writer.n_msgs))


def process_live(iface, writer: QuestionWriter, bpf: str = "tcp"):
    from scapy.all import AsyncSniffer, TCP, IP, IPv6  # noqa
    import time
    flows, srcs = {}, {}

    def cb(pkt):
        if TCP not in pkt:
            return
        l3 = pkt[IP] if IP in pkt else (pkt[IPv6] if IPv6 in pkt else None)
        if l3 is None:
            return
        payload = bytes(pkt[TCP].payload)
        if not payload:
            return
        key = (l3.src, pkt[TCP].sport, l3.dst, pkt[TCP].dport)
        fr = flows.get(key)
        if fr is None:
            fr = flows[key] = FlowReassembler()
            srcs[key] = "%s:%d->%s:%d" % (l3.src, pkt[TCP].sport, l3.dst, pkt[TCP].dport)
        elif fr.is_game is False:
            return
        fr.add(payload)

    try:
        sniffer = AsyncSniffer(filter=bpf, prn=cb, store=False, iface=iface)
        sniffer.start()
    except (OSError, RuntimeError) as e:
        print("\nERROR starting live capture: %s" % e)
        print("Live capture needs Npcap (https://npcap.com). Or capture to a .pcapng and use --pcap.")
        sys.exit(1)
    print("[*] live capturing (filter: %s)." % bpf)
    print("    -> Open the Knowledge Quiz in-game and answer ONE question. Ctrl+C to stop.")
    last_hb = time.time()
    try:
        while True:
            time.sleep(0.6)
            for key in list(flows.keys()):
                _drain(flows[key], writer, srcs.get(key, ""))
            if time.time() - last_hb >= 5:
                print("[hb] flows=%d  msgs=%d  quiz=%d" % (len(flows), writer.n_msgs, writer.n_quiz))
                last_hb = time.time()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            sniffer.stop()
        except Exception:
            pass
        for key in list(flows.keys()):
            _drain(flows[key], writer, srcs.get(key, ""))
        print("\n[done] %d quiz msgs of %d total. Output: %s" % (writer.n_quiz, writer.n_msgs, writer.dir))


def main():
    ap = argparse.ArgumentParser(description="LAM quiz raw capture + best-effort decode (Phase 1)")
    ap.add_argument("--live", action="store_true", help="live capture (admin + Npcap)")
    ap.add_argument("--iface", default=None, help="interface name (see --list-ifaces)")
    ap.add_argument("--pcap", default=None, help="decode a saved .pcap/.pcapng instead")
    ap.add_argument("--filter", default="tcp", help="BPF capture filter")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output dir")
    ap.add_argument("--list-ifaces", action="store_true", help="list capture interfaces and exit")
    args = ap.parse_args()

    # Make the console UTF-8 tolerant so CJK question/option text can't crash a print
    # (Windows defaults to cp1252). errors='replace' keeps it lossless-enough for display.
    for stream in (sys.stdout, sys.stderr):
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
        print("ERROR: scapy is required.  pip install scapy   (and Npcap on Windows)")
        sys.exit(1)

    writer = QuestionWriter(args.out)
    print("[*] output dir: %s" % args.out)
    if args.pcap:
        process_pcap(args.pcap, writer)
    elif args.live:
        process_live(args.iface, writer, args.filter)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
