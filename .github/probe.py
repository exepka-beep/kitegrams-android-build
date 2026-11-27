#!/usr/bin/env python3
"""Raw MTProto handshake probe for the KiteGrams edge.

Talks to the edge exactly like a Telegram client would, stopping short of
set_client_DH_params, and reports what the server actually puts on the wire.
"""
import base64
import hashlib
import json
import os
import re
import socket
import struct
import sys

# ---------------------------------------------------------------- DER / PEM


def _der_len(b, i):
    l = b[i]
    i += 1
    if l & 0x80:
        n = l & 0x7F
        l = int.from_bytes(b[i:i + n], "big")
        i += n
    return l, i


def parse_key(pem):
    """Return (n, e) from an SPKI or PKCS#1 PEM/DER blob."""
    m = re.search(r"-----BEGIN[^-]*-----(.*?)-----END", pem, re.S)
    body = m.group(1) if m else pem
    body = re.sub(r"[^A-Za-z0-9+/=]", "", body)
    der = base64.b64decode(body + "=" * (-len(body) % 4))

    i = 0
    if der[i] != 0x30:
        raise ValueError("not a DER SEQUENCE: first byte 0x%02x" % der[i])
    i += 1
    _, i = _der_len(der, i)

    if der[i] == 0x30:  # SubjectPublicKeyInfo: skip AlgorithmIdentifier
        i += 1
        l, i = _der_len(der, i)
        i += l
        if der[i] != 0x03:
            raise ValueError("expected BIT STRING at %d, got 0x%02x" % (i, der[i]))
        i += 1
        l, i = _der_len(der, i)
        i += 1  # unused-bits count
        if der[i] != 0x30:
            raise ValueError("expected inner SEQUENCE at %d, got 0x%02x" % (i, der[i]))
        i += 1
        _, i = _der_len(der, i)

    out = []
    for _ in range(2):
        if der[i] != 0x02:
            raise ValueError("expected INTEGER at %d, got 0x%02x" % (i, der[i]))
        i += 1
        l, i = _der_len(der, i)
        v = der[i:i + l]
        i += l
        if v[0] == 0 and len(v) > 1:
            v = v[1:]
        out.append(v)
    return out[0], out[1]


# ------------------------------------------------------------------- crypto


def tl_str(b):
    n = len(b)
    if n < 254:
        return bytes([n]) + b + b"\x00" * ((4 - (n + 1) % 4) % 4)
    return (bytes([0xFE, n & 0xFF, (n >> 8) & 0xFF, (n >> 16) & 0xFF])
            + b + b"\x00" * ((4 - n % 4) % 4))


def fingerprint(n, e):
    h = hashlib.sha1(tl_str(n) + tl_str(e)).digest()
    return struct.unpack("<Q", h[-8:])[0]


def _is_prime(n):
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _rho(n):
    if n % 2 == 0:
        return 2
    import random
    while True:
        x = random.randrange(2, n)
        y, c, d = x, random.randrange(1, n), 1
        while d == 1:
            x = (x * x + c) % n
            y = (y * y + c) % n
            y = (y * y + c) % n
            d = __import__("math").gcd(abs(x - y), n)
        if d != n:
            return d


def factor(n):
    if n == 1:
        return []
    if _is_prime(n):
        return [n]
    d = _rho(n)
    return factor(d) + factor(n // d)


# ------------------------------------------------------------------ framing

HEADERS = {
    "abridged": b"\xef",
    "intermediate": b"\xee\xee\xee\xee",
    "padded": b"\xdd\xdd\xdd\xdd",
}


def read_exact(s, n):
    buf = b""
    while len(buf) < n:
        c = s.recv(n - len(buf))
        if not c:
            raise EOFError("connection closed after %d/%d bytes" % (len(buf), n))
        buf += c
    return buf


def send_pkt(s, transport, body):
    if transport == "abridged":
        words = (len(body) + 3) // 4
        body = body + b"\x00" * (words * 4 - len(body))
        if words < 127:
            hdr = bytes([words])
        else:
            hdr = bytes([0x7F]) + struct.pack("<I", words)[:3]
    else:
        hdr = struct.pack("<I", len(body))
    s.sendall(hdr + body)


def recv_pkt(s, transport):
    if transport == "abridged":
        b = read_exact(s, 1)[0]
        if b < 127:
            n = b * 4
        else:
            n = int.from_bytes(read_exact(s, 3), "little") * 4
    else:
        n = struct.unpack("<I", read_exact(s, 4))[0]
    return read_exact(s, n)


# ------------------------------------------------------------------- parsing


def parse_respq(data):
    cid = struct.unpack("<I", data[:4])[0]
    out = {"constructor": "0x%08x" % cid, "len": len(data)}
    if cid != 0x05162463:
        out["raw_hex"] = data[:80].hex()
        return out
    i = 4
    nonce = data[i:i + 16]
    i += 16
    server_nonce = data[i:i + 16]
    i += 16
    l = data[i]
    i += 1
    if l >= 254:
        l = int.from_bytes(data[i:i + 3], "little")
        i += 3
    pq = int.from_bytes(data[i:i + l], "big")
    i += l
    i += (-(1 + l)) % 4
    vec = struct.unpack("<I", data[i:i + 4])[0]
    i += 4
    cnt = struct.unpack("<I", data[i:i + 4])[0]
    i += 4
    fps = []
    for _ in range(cnt):
        fps.append(struct.unpack("<Q", data[i:i + 8])[0])
        i += 8
    out.update({
        "nonce": nonce.hex(),
        "server_nonce": server_nonce.hex(),
        "pq": str(pq),
        "pq_bytes": l,
        "vector_ctor": "0x%08x" % vec,
        "fingerprints": ["%016x" % f for f in fps],
        "fingerprints_raw": fps,
        "trailing_bytes": len(data) - i,
        "_nonce": nonce,
        "_server_nonce": server_nonce,
        "_pq": pq,
    })
    return out


def parse_dh_params(data):
    cid = struct.unpack("<I", data[:4])[0]
    names = {
        0xD0E8075C: "server_DH_params_ok",
        0x79CB045D: "server_DH_params_fail",
    }
    out = {"constructor": names.get(cid, "0x%08x" % cid), "len": len(data)}
    if cid in names:
        i = 4
        out["nonce"] = data[i:i + 16].hex()
        i += 16
        out["server_nonce"] = data[i:i + 16].hex()
        i += 16
        if cid == 0xD0E8075C:
            l = data[i]
            i += 1
            if l >= 254:
                l = int.from_bytes(data[i:i + 3], "little")
                i += 3
            out["encrypted_answer_len"] = l
        else:
            out["new_nonce_hash"] = data[i:i + 16].hex()
    else:
        out["raw_hex"] = data[:80].hex()
    return out


# --------------------------------------------------------------------- main


def req_dh_params_body(n, e, info, dc_id=2, use_dc=True):
    pq, p, q = info["_pq"], info["_p"], info["_q"]
    nonce, server_nonce = info["_nonce"], info["_server_nonce"]
    new_nonce = os.urandom(32)

    if use_dc:
        inner = (struct.pack("<I", 0xA9F55F95)
                 + tl_str(pq.to_bytes(8, "big"))
                 + tl_str(p.to_bytes(4, "big"))
                 + tl_str(q.to_bytes(4, "big"))
                 + nonce + server_nonce + new_nonce
                 + struct.pack("<i", dc_id))
    else:
        inner = (struct.pack("<I", 0x83C95AEC)
                 + tl_str(pq.to_bytes(8, "big"))
                 + tl_str(p.to_bytes(4, "big"))
                 + tl_str(q.to_bytes(4, "big"))
                 + nonce + server_nonce + new_nonce)

    payload = hashlib.sha1(inner).digest() + inner
    if len(payload) > 256:
        raise ValueError("p_q_inner_data too large: %d" % len(payload))
    payload += os.urandom(256 - len(payload))
    encrypted = pow(int.from_bytes(payload, "big"), int.from_bytes(e, "big"), int.from_bytes(n, "big"))
    enc = encrypted.to_bytes(256, "big")

    body = (struct.pack("<I", 0xD712E4BE)
            + nonce + server_nonce
            + tl_str(p.to_bytes(4, "big"))
            + tl_str(q.to_bytes(4, "big"))
            + struct.pack("<Q", fingerprint(n, e))
            + tl_str(enc))
    return body, new_nonce


def load_pem(port):
    """Prefer /tmp/kgkey.pem, otherwise ask the edge for its own key."""
    try:
        pem = open("/tmp/kgkey.pem", encoding="utf-8").read()
        if "BEGIN" in pem:
            return pem
    except OSError:
        pass
    import urllib.request
    url = "http://127.0.0.1:%d/owpengram/server-info" % port
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.load(r)["rsa_public_key_pem"]


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 2398
    transports = sys.argv[3].split(",") if len(sys.argv) > 3 else ["abridged"]

    pem = load_pem(port)
    print("pem bytes=%d first=%r" % (len(pem), pem[:34]))
    n, e = parse_key(pem)
    my_fp = fingerprint(n, e)
    print("key bits=%d e=%d computed_fingerprint=%016x"
          % (len(n) * 8, int.from_bytes(e, "big"), my_fp))

    for tr in transports:
        print("\n=== transport: %s ===" % tr)
        try:
            s = socket.create_connection((host, port), timeout=10)
            s.sendall(HEADERS[tr])

            nonce = os.urandom(16)
            send_pkt(s, tr, struct.pack("<I", 0xBE7E8EF1) + nonce)
            data = recv_pkt(s, tr)
            info = parse_respq(data)
            info["nonce_matches"] = info.get("nonce") == nonce.hex()
            info["server_fp_matches_key"] = my_fp in info.get("fingerprints_raw", [])
            info.pop("fingerprints_raw", None)
            print("ResPQ:", json.dumps(info, indent=2))

            if info["constructor"] != "0x05162463":
                s.close()
                continue

            # Second ReqPQ on the same connection exercises the "again" branch.
            nonce2 = os.urandom(16)
            send_pkt(s, tr, struct.pack("<I", 0xBE7E8EF1) + nonce2)
            d2 = recv_pkt(s, tr)
            i2 = parse_respq(d2)
            i2.pop("fingerprints_raw", None)
            i2.pop("_nonce", None)
            i2.pop("_server_nonce", None)
            i2.pop("_pq", None)
            print("2nd ResPQ:", json.dumps(i2, indent=2))
            print("pq_changed_on_repeat:", i2.get("pq") != info.get("pq"))

            # Continue the real handshake on a fresh connection.
            factors = sorted(factor(info["_pq"]))
            if len(factors) != 2:
                print("pq does not factor into two primes: %s" % factors)
                s.close()
                continue
            info["_p"], info["_q"] = factors[0], factors[1]
            print("pq factors: %d * %d" % (factors[0], factors[1]))

            for use_dc in (True, False):
                s2 = socket.create_connection((host, port), timeout=10)
                s2.sendall(HEADERS[tr])
                nn = os.urandom(16)
                send_pkt(s2, tr, struct.pack("<I", 0xBE7E8EF1) + nn)
                r2 = parse_respq(recv_pkt(s2, tr))
                r2["_p"], r2["_q"] = factors[0], factors[1]
                body, new_nonce = req_dh_params_body(n, e, r2, dc_id=2, use_dc=use_dc)
                send_pkt(s2, tr, body)
                try:
                    resp = recv_pkt(s2, tr)
                    print("req_DH_params(use_dc=%s) -> %s"
                          % (use_dc, json.dumps(parse_dh_params(resp))))
                except Exception as ex:
                    print("req_DH_params(use_dc=%s) FAILED: %s: %s"
                          % (use_dc, type(ex).__name__, ex))
                s2.close()

            s.close()
        except Exception as ex:
            print("FAILED: %s: %s" % (type(ex).__name__, ex))


if __name__ == "__main__":
    main()
