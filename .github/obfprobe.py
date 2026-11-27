#!/usr/bin/env python3
"""Obfuscated-transport MTProto probe (runs on a runner with pycryptodome).

Mirrors exactly what a Telegram client does on the wire, so whatever the
server answers here is what the phone sees.
"""
import os
import socket
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe as P  # noqa: E402

from Crypto.Cipher import AES
from Crypto.Util import Counter


def ctr(key, iv):
    return AES.new(key, AES.MODE_CTR,
                   counter=Counter.new(128, initial_value=int.from_bytes(iv, "big")))


def derive(init, variant):
    rev = init[:56][::-1] if variant == "rev56" else init[:48][::-1]
    if variant == "rev56":
        return (init[8:40], init[40:56], rev[8:40], rev[40:56])
    # rev48: decrypt key/iv taken from the reversed 48-byte prefix padded with
    # the untouched tail, which is what some proxy builds do.
    tail = init[48:56]
    joined = rev + tail
    return (init[8:40], init[40:56], joined[8:40], joined[40:56])


class Obf:
    def __init__(self, sock, tag, variant):
        self.s = sock
        init = bytearray(os.urandom(64))
        init[56:60] = tag
        ek, eiv, dk, div = derive(bytes(init), variant)
        self.enc = ctr(ek, eiv)
        self.dec = ctr(dk, div)
        self.s.sendall(bytes(init))

    def send(self, body, abridged=True):
        if abridged:
            words = (len(body) + 3) // 4
            body = body + b"\x00" * (words * 4 - len(body))
            hdr = bytes([words]) if words < 127 else bytes([0x7F]) + struct.pack("<I", words)[:3]
        else:
            hdr = struct.pack("<I", len(body))
        self.s.sendall(self.enc.encrypt(hdr + body))

    def recv(self, abridged=True):
        def rx(n):
            buf = b""
            while len(buf) < n:
                c = self.s.recv(n - len(buf))
                if not c:
                    raise EOFError("closed after %d/%d" % (len(buf), n))
                buf += c
            return buf
        if abridged:
            b = self.dec.decrypt(rx(1))[0]
            n = b * 4 if b < 127 else int.from_bytes(self.dec.decrypt(rx(3)), "little") * 4
        else:
            n = struct.unpack("<I", self.dec.decrypt(rx(4)))[0]
        return self.dec.decrypt(rx(n))


def try_one(host, port, tag, variant, abridged, label):
    s = socket.create_connection((host, port), timeout=8)
    o = Obf(s, tag, variant)
    nonce = os.urandom(16)
    o.send(struct.pack("<I", 0xBE7E8EF1) + nonce, abridged)
    data = o.recv(abridged)
    info = P.parse_respq(data)
    ok = info["constructor"] == "0x05162463"
    print("[%s] ctor=%s len=%d nonce_ok=%s"
          % (label, info["constructor"], info["len"], info.get("nonce") == nonce.hex()))
    if ok:
        my_fp = P.fingerprint(*P.parse_key(open("/tmp/kgkey.pem").read()))
        print("    pq=%s fp=%s fp_matches_key=%s trailing=%d"
              % (info["pq"], info["fingerprints"], my_fp in info["fingerprints_raw"],
                 info["trailing_bytes"]))
        return s, o, info, nonce, abridged, variant, tag
    s.close()
    return None


def main():
    host = sys.argv[1]
    port = int(sys.argv[2])
    found = None
    for variant in ("rev56", "rev48"):
        for tag, abridged, name in ((b"\xef\xef\xef\xef", True, "abridged"),
                                    (b"\xee\xee\xee\xee", False, "intermediate")):
            try:
                r = try_one(host, port, tag, variant, abridged, "%s/%s" % (variant, name))
            except Exception as ex:
                print("[%s/%s] FAILED %s: %s" % (variant, name, type(ex).__name__, ex))
                continue
            if r and not found:
                found = r

    if not found:
        print("no transport variant produced a ResPQ")
        return

    s, o, info, nonce, abridged, variant, tag = found
    print("\n--- second req_pq on the same socket (server 'again' branch) ---")
    n2 = os.urandom(16)
    o.send(struct.pack("<I", 0xBE7E8EF1) + n2, abridged)
    i2 = P.parse_respq(o.recv(abridged))
    print("ctor=%s nonce_ok=%s pq_changed=%s"
          % (i2["constructor"], i2.get("nonce") == n2.hex(), i2.get("pq") != info.get("pq")))
    s.close()

    print("\n--- full req_DH_params on a fresh socket ---")
    n_bytes, e = P.parse_key(open("/tmp/kgkey.pem").read())
    fac = sorted(P.factor(info["_pq"]))
    print("pq factors:", fac)
    s2 = socket.create_connection((host, port), timeout=8)
    o2 = Obf(s2, tag, variant)
    nn = os.urandom(16)
    o2.send(struct.pack("<I", 0xBE7E8EF1) + nn, abridged)
    r2 = P.parse_respq(o2.recv(abridged))
    r2["_p"], r2["_q"] = fac[0], fac[1]
    body, _ = P.req_dh_params_body(n_bytes, e, r2, dc_id=2, use_dc=True)
    o2.send(body, abridged)
    print("req_DH_params ->", P.parse_dh_params(o2.recv(abridged)))
    s2.close()


if __name__ == "__main__":
    main()
