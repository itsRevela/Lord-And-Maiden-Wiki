#!/usr/bin/env python3
r"""Passive network sniffer/decoder for Lord & Maiden battle reports + battle logs.

WHY: LAM combat is SERVER-AUTHORITATIVE -- the client only replays a battle the server
already computed. The server sends the full battle (per-hit damage, WHO was targeted,
win/loss, per-hero kills) over a PLAIN TCP socket. Server->client messages are NOT
encrypted (only client->server requests are DES-encrypted, which we ignore), so we can
decode the battle data straight off the wire and use it as ground truth to calibrate the
simulator.

PROTOCOL (reverse-engineered from decompiled Assembly-CSharp, class Connection/ProtocolBytes):
  TCP stream framing (server->client):
    [4-byte LE outer length N] [N bytes]
    the N bytes = [1 flag byte][payload];  flag==1 -> payload is raw, else gzip-compressed
    decompressed payload = [4-byte LE inner length M][body (M bytes)]
    body = [4-byte LE name length][UTF-8 message NAME][message fields...]
  Wire encoding (proto.Get*): fixed little-endian -- int=int32, long=int64, float=float32,
    string=[int32 len][utf8], list=[int32 count][elements]. (No varints.)
  The battle log message is name == "SCLogic_DetailsGrand" (handler DetailsGrandBack):
    after the name it reads one int, then the BattleDetails struct (see decode_battle_details).

USAGE:
  pip install scapy        (needs Npcap on Windows -- installed with Wireshark)
  # live capture (run an elevated/admin terminal):
  python tools/lam_battle_sniffer.py --live                 # auto-pick interface
  python tools/lam_battle_sniffer.py --list-ifaces          # list interfaces
  python tools/lam_battle_sniffer.py --live --iface "Wi-Fi"
  # offline (decode a Wireshark capture):
  python tools/lam_battle_sniffer.py --pcap C:\path\lam_capture.pcapng

It auto-detects the game's TCP stream by the SC.../CS... message-name signature -- no
server IP/port config needed. While you play (or run practice battles AND open each
battle's report/log so the client fetches SCLogic_DetailsGrand), every decoded battle is
written to the output dir as JSON + a human-readable .log, with a running index.csv and a
messages.log of all message names seen (to discover other useful messages).

Output: notes/sim/captures/ by default (--out to change).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import io
import json
import os
import struct
import sys

# message names that carry battle data we decode in full
BATTLE_DETAILS_MSG = "SCLogic_DetailsGrand"
START_FIGHT_MSG = "SCLogic_StartFigthBack"

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "notes", "sim", "captures")


# --------------------------------------------------------------------------- proto reader
class Proto:
    """Little-endian reader mirroring the client's ProtocolBytes.Get* methods."""

    def __init__(self, buf: bytes, offset: int = 0):
        self.b = buf
        self.o = offset

    def remaining(self) -> int:
        return len(self.b) - self.o

    def int(self) -> int:
        v = struct.unpack_from("<i", self.b, self.o)[0]
        self.o += 4
        return v

    def long(self) -> int:
        v = struct.unpack_from("<q", self.b, self.o)[0]
        self.o += 8
        return v

    def float(self) -> float:
        v = struct.unpack_from("<f", self.b, self.o)[0]
        self.o += 4
        return v

    def string(self) -> str:
        n = struct.unpack_from("<i", self.b, self.o)[0]
        self.o += 4
        if n < 0 or self.o + n > len(self.b):
            raise ValueError("bad string length %d" % n)
        s = self.b[self.o:self.o + n].decode("utf-8", "replace")
        self.o += n
        return s

    def peek_name(self) -> str:
        return Proto(self.b, 0).string()


# --------------------------------------------------------------------------- battle decode
def decode_battle_details(body: bytes) -> dict:
    """Decode a SCLogic_DetailsGrand body into the full battle log.
    Mirrors DetailsGrandBack (decompiled eb46ed1b3cbb.cs:19429-19590). Parses through the
    RoundDataList (all per-hit data); Awards/MVP tail is best-effort/skipped."""
    p = Proto(body)
    name = p.string()              # message name (== SCLogic_DetailsGrand)
    p.int()                        # leading int (sub/seq) -- discarded by the client too
    d: dict = {"msg": name}
    d["grandId"] = p.long()
    d["where"] = p.int()
    d["viewUserId"] = p.int()
    d["shareId"] = p.int()
    d["fightRet"] = p.int()        # overall result flag (1 = attacker/left win, per client)
    d["playerA"] = p.string()
    d["playerB"] = p.string()
    d["desList"] = [p.string() for _ in range(p.int())]   # battle-log text lines

    def kill_list():
        out = []
        for _ in range(p.int()):
            out.append({"heroNum": p.int(), "skinId": p.int(), "fightPos": p.int(),
                        "normalKill": p.int(), "skillKill": p.int(), "skillCount": p.int()})
        return out

    d["attackKill"] = kill_list()          # per-hero kills (side A) -- the in-game "Kills" table
    d["defenderKill"] = kill_list()        # per-hero kills (side B)

    init = []
    for _ in range(p.int()):
        init.append({"heroNum": p.int(), "skinId": p.int(), "fightPos": p.int(),
                     "st": p.int(), "slv": p.int(),
                     "hpRate1": round(p.float(), 5), "hpRate2": round(p.float(), 5)})
    d["initState"] = init

    def ret_list():
        out = []
        for _ in range(p.int()):
            out.append({"targetPos": p.int(), "retType": p.int(), "retVal": p.int(),
                        "hpRate1": round(p.float(), 5), "hpRate2": round(p.float(), 5)})
        return out

    rounds = []
    for _ in range(p.int()):
        rnd = {"round": p.int(), "behaviours": []}
        for _ in range(p.int()):                       # FightBehaviour list
            fb = {"fightPos": p.int(), "beforeAction": ret_list(), "actions": []}
            for _ in range(p.int()):                   # BehaviourAction list
                fb["actions"].append({
                    "behaviourId": p.int(),
                    "skillKey": p.string(),
                    "rets": ret_list(),
                })
            rnd["behaviours"].append(fb)
        rounds.append(rnd)
    d["rounds"] = rounds
    # ginfo / Awards / GroupRet / MVP tail intentionally not parsed (Awards=PropList is
    # variable and unneeded; fightRet above already gives the result). Record bytes left.
    d["_unparsed_tail_bytes"] = p.remaining()
    return d


# RetType render mapping (decompiled HandleBehaviourRet): <=3 damage, 4 heal, 5 defeated,
# 6/7 buff icon. Used only to label the human-readable log.
def _ret_label(rt: int) -> str:
    if rt <= 3:
        return "DMG"
    return {4: "HEAL", 5: "DEFEAT", 6: "BUFF", 7: "BUFF"}.get(rt, "?%d" % rt)


def battle_to_text(d: dict) -> str:
    """Human-readable reconstruction (like a transcribed battle log)."""
    out = io.StringIO()
    w = lambda *a: out.write(" ".join(str(x) for x in a) + "\n")
    w("=== Battle %s | %s vs %s | fightRet=%s | rounds=%d ==="
      % (d.get("grandId"), d.get("playerA"), d.get("playerB"), d.get("fightRet"),
         len(d.get("rounds", []))))
    if d.get("initState"):
        w("-- init (fightPos: heroNum st/slv hp1 hp2) --")
        for u in d["initState"]:
            w("   pos%d hero%d st%d/lv%d hp1=%.3f hp2=%.3f"
              % (u["fightPos"], u["heroNum"], u["st"], u["slv"], u["hpRate1"], u["hpRate2"]))
    for tag, kl in (("A", d.get("attackKill", [])), ("B", d.get("defenderKill", []))):
        for k in kl:
            w("   [%s] pos%d hero%d kills: normal=%d skill=%d skillsUsed=%d"
              % (tag, k["fightPos"], k["heroNum"], k["normalKill"], k["skillKill"], k["skillCount"]))
    for rnd in d.get("rounds", []):
        w("-- Round %d --" % rnd["round"])
        for fb in rnd["behaviours"]:
            for r in fb["beforeAction"]:
                w("   [pos%d] BEFORE -> pos%d %s %d (hp %.3f->%.3f)"
                  % (fb["fightPos"], r["targetPos"], _ret_label(r["retType"]), r["retVal"],
                     r["hpRate1"], r["hpRate2"]))
            for act in fb["actions"]:
                sk = act["skillKey"] or "NormalATK"
                for r in act["rets"]:
                    w("   [pos%d] %s -> pos%d %s %d (hp %.3f->%.3f)"
                      % (fb["fightPos"], sk, r["targetPos"], _ret_label(r["retType"]),
                         r["retVal"], r["hpRate1"], r["hpRate2"]))
    return out.getvalue()


# --------------------------------------------------------------------------- TCP framing
MAX_FRAME = 64 * 1024 * 1024


def _decode_msg(msg: bytes):
    """Decode one framed message body (the bytes AFTER the 4-byte outer length).
    Returns (name, body_bytes) or None if it doesn't decode to a plausible message."""
    if not msg:
        return None
    flag = msg[0]
    rest = msg[1:]
    try:
        payload = rest if flag == 1 else gzip.decompress(rest)
    except Exception:
        return None
    if len(payload) < 4:
        return None
    inner = struct.unpack_from("<i", payload, 0)[0]
    body = payload[4:4 + inner] if (0 < inner <= len(payload) - 4) else payload[4:]
    try:
        name = Proto(body).peek_name()
    except Exception:
        return None
    if not _plausible_name(name):
        return None
    return name, body


def _plausible_name(name: str) -> bool:
    if not (3 <= len(name) <= 64):
        return False
    if not all(32 <= ord(c) < 127 for c in name):
        return False
    return name[:2] in ("SC", "CS") or name[:3] in ("SCL", "CSL")


class FlowReassembler:
    """Per-TCP-flow byte reassembly using sequence numbers (handles reorder/retransmit)."""

    def __init__(self):
        self.segments = {}      # seq -> bytes
        self.base = None        # next contiguous seq we expect
        self.buffer = bytearray()
        self.is_game = None     # None=unknown, True/False once decided

    def add(self, seq: int, data: bytes):
        if not data:
            return
        if self.base is None:
            self.base = seq
        self.segments[seq] = data
        # drain contiguous
        while self.base in self.segments:
            d = self.segments.pop(self.base)
            self.buffer += d
            self.base = (self.base + len(d)) & 0xFFFFFFFF
        # cap stray segment memory
        if len(self.segments) > 4096:
            self.segments.clear()


# --------------------------------------------------------------------------- output
class BattleWriter:
    def __init__(self, out_dir: str):
        self.dir = out_dir
        os.makedirs(out_dir, exist_ok=True)
        self.msglog = open(os.path.join(out_dir, "messages.log"), "a", encoding="utf-8")
        self.index = open(os.path.join(out_dir, "index.csv"), "a", encoding="utf-8")
        if os.path.getsize(os.path.join(out_dir, "index.csv")) == 0:
            self.index.write("timestamp,grandId,playerA,playerB,fightRet,rounds,file\n")
        self.seen_battles = set()
        self.n_battles = 0
        self.n_msgs = 0

    def note_msg(self, name: str, size: int):
        self.n_msgs += 1
        self.msglog.write("%s\t%d\n" % (name, size))
        self.msglog.flush()

    def write_battle(self, d: dict):
        gid = d.get("grandId")
        key = (gid, len(d.get("rounds", [])))
        if key in self.seen_battles:
            return
        self.seen_battles.add(key)
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        base = "battle_%s_%s" % (ts, gid)
        jpath = os.path.join(self.dir, base + ".json")
        lpath = os.path.join(self.dir, base + ".log")
        with open(jpath, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        with open(lpath, "w", encoding="utf-8") as f:
            f.write(battle_to_text(d))
        self.index.write("%s,%s,%s,%s,%s,%d,%s\n" % (
            ts, gid, d.get("playerA", ""), d.get("playerB", ""), d.get("fightRet"),
            len(d.get("rounds", [])), base + ".json"))
        self.index.flush()
        self.n_battles += 1
        print("[+] battle captured: %s  (%s vs %s, fightRet=%s, %d rounds)  -> %s"
              % (gid, d.get("playerA"), d.get("playerB"), d.get("fightRet"),
                 len(d.get("rounds", [])), base + ".json"))


# --------------------------------------------------------------------------- engine glue
def handle_body(name: str, body: bytes, writer: BattleWriter, dump_raw: bool):
    writer.note_msg(name, len(body))
    if name == BATTLE_DETAILS_MSG:
        try:
            d = decode_battle_details(body)
            writer.write_battle(d)
        except Exception as e:
            print("[!] failed to decode %s: %s" % (name, e))
            if dump_raw:
                raw = os.path.join(writer.dir, "raw_%s_%d.bin" % (name, len(body)))
                open(raw, "wb").write(body)
    elif name == START_FIGHT_MSG and dump_raw:
        # structure TBD; dump raw so it can be reverse-engineered offline
        open(os.path.join(writer.dir, "raw_StartFigthBack_%d.bin" % len(body)), "wb").write(body)


def process_pcap(path: str, writer: BattleWriter, dump_raw: bool):
    from scapy.all import PcapReader, TCP, IP, IPv6  # noqa
    flows = {}
    for pkt in PcapReader(path):
        if TCP not in pkt:
            continue
        l3 = pkt[IP] if IP in pkt else (pkt[IPv6] if IPv6 in pkt else None)
        if l3 is None:
            continue
        tcp = pkt[TCP]
        payload = bytes(tcp.payload)
        if not payload:
            continue
        key = (l3.src, tcp.sport, l3.dst, tcp.dport)
        fr = flows.setdefault(key, FlowReassembler())
        fr.add(int(tcp.seq), payload)
        _drain_flow(fr, writer, dump_raw)
    print("[done] pcap parsed: %d battles, %d messages." % (writer.n_battles, writer.n_msgs))


def _drain_flow(fr: FlowReassembler, writer: BattleWriter, dump_raw: bool):
    """Frame + decode all complete messages in the flow buffer. Robust to starting
    mid-stream: byte-by-byte resync until the first valid frame, then trust the length
    framing once aligned."""
    if not fr.buffer:
        return
    stream = bytes(fr.buffer)
    consumed = 0                          # only advanced once we trust alignment
    o = 0
    n = len(stream)
    while n - o >= 4:
        outer = struct.unpack_from("<i", stream, o)[0]
        if not (0 < outer <= MAX_FRAME):
            o += 1                        # invalid length -> resync (no trim until aligned)
            if fr.is_game:
                consumed = o
            continue
        if n - o - 4 < outer:             # plausible length but frame not fully arrived
            if fr.is_game:
                break                     # aligned -> wait for the rest
            o += 1                        # not aligned -> keep searching (do NOT discard:
            continue                      #   a real frame start may complete with more bytes)
        dec = _decode_msg(stream[o + 4:o + 4 + outer])
        if dec is not None:
            handle_body(dec[0], dec[1], writer, dump_raw)
            fr.is_game = True
            o += 4 + outer
            consumed = o
        elif fr.is_game:
            o += 4 + outer                # aligned but unrecognized -> skip, stay aligned
            consumed = o
        else:
            o += 1                        # not aligned -> resync (no trim)
    if consumed:
        del fr.buffer[:consumed]
    elif not fr.is_game and len(fr.buffer) > 512 * 1024:
        fr.buffer.clear()                 # non-game / un-alignable flow -> stop buffering


def process_live(iface, writer: BattleWriter, dump_raw: bool):
    from scapy.all import sniff, TCP, IP, IPv6  # noqa
    flows = {}

    def cb(pkt):
        if TCP not in pkt:
            return
        l3 = pkt[IP] if IP in pkt else (pkt[IPv6] if IPv6 in pkt else None)
        if l3 is None:
            return
        tcp = pkt[TCP]
        payload = bytes(tcp.payload)
        if not payload:
            return
        key = (l3.src, tcp.sport, l3.dst, tcp.dport)
        fr = flows.setdefault(key, FlowReassembler())
        fr.add(int(tcp.seq), payload)
        _drain_flow(fr, writer, dump_raw)

    print("[*] live sniffing (filter: tcp). Play the game / run practice battles AND open")
    print("    each battle's report/log so the client fetches SCLogic_DetailsGrand. Ctrl+C to stop.")
    try:
        sniff(prn=cb, store=False, filter="tcp", iface=iface)
    except (OSError, RuntimeError) as e:
        print("\nERROR starting live capture: %s" % e)
        print("Live capture needs Npcap (https://npcap.com -- check 'WinPcap API-compatible mode').")
        print("No-install alternative: capture with Wireshark to a .pcapng, then run with --pcap FILE.")
        sys.exit(1)


def list_ifaces():
    try:
        from scapy.arch.windows import get_windows_if_list
        for i in get_windows_if_list():
            print("  %-40s %s" % (i.get("name"), i.get("description")))
    except Exception:
        from scapy.all import get_if_list
        for n in get_if_list():
            print("  " + str(n))


def main():
    ap = argparse.ArgumentParser(description="LAM battle report/log passive sniffer")
    ap.add_argument("--live", action="store_true", help="live capture (needs admin + Npcap)")
    ap.add_argument("--iface", default=None, help="interface name (see --list-ifaces)")
    ap.add_argument("--pcap", default=None, help="decode a saved .pcap/.pcapng instead")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output dir (default notes/sim/captures)")
    ap.add_argument("--dump-raw", action="store_true", help="dump raw bytes of battle/unknown msgs")
    ap.add_argument("--list-ifaces", action="store_true", help="list capture interfaces and exit")
    args = ap.parse_args()

    if args.list_ifaces:
        list_ifaces()
        return
    try:
        import scapy  # noqa
    except ImportError:
        print("ERROR: scapy is required.  pip install scapy   (and Npcap on Windows)")
        sys.exit(1)

    writer = BattleWriter(args.out)
    print("[*] output dir: %s" % args.out)
    if args.pcap:
        process_pcap(args.pcap, writer, args.dump_raw)
    elif args.live:
        try:
            process_live(args.iface, writer, args.dump_raw)
        except KeyboardInterrupt:
            print("\n[done] %d battles, %d messages captured." % (writer.n_battles, writer.n_msgs))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
