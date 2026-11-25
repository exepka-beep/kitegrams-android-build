#!/usr/bin/env python3
"""Rebrand a decoded JavaGram APK tree into KiteGrams, pointed at our server.

JavaGram ships as a multi-server client with its own test server hardcoded
(2.26.81.132:2398). This script repoints that default to the KiteGrams server
and replaces the visible JavaGram branding.

Usage: python3 scripts/rebrand_javagram.py <decoded_dir>
"""
import base64
import hashlib
import os
import re
import sys

ROOT = sys.argv[1]
OLD_IP = b"2.26.81.132"
NEW_IP = b"2.26.81.165"  # same length as OLD_IP
OLD_PKG = "org.javagram.messenger.web"
NEW_PKG = "com.kitegrams.messenger"

# KiteGrams MTProto RSA public key in PKCS#1 form (same 270-byte DER length as
# the two Telegram keys shipped by JavaGram, so the PEM block can be replaced
# in place without shifting any other bytes in libtmessages).
NEW_RSA_PUBLIC_KEY_B64 = (
    "MIIBCgKCAQEA61rNnUMlo4zCZcm2UXgH/b6sidE4Vl8rYfq20X95UZmOVam9oShO"
    "QlEx6rX1jnwrXCooBjWQmPQGbejx9PBSuGk9M2q+gsmhw/mWizbaltr7pQMv3a1s"
    "OIhZPG6enestT5wyiVxi46+dhTjTUABYgA7Vw+Ys8pRnrm9qbd2GwPyjYdsy5Rhj"
    "5a+wIf8rHSBG46Oyi9zB7fCi5qv1QEqfjbvK7nE0U+qcX70hJUm6hKduG+t6e0Cu"
    "sBXA+ODsbp4TlcJN9m7PZ5lxzvIeC/4vX8JO+uJYdf02GewQ0Qxo+8r9ZwwJ2xd2"
    "ib1iERuTq+mRKsyWyAfTV1CJLLx2NrDzOwIDAQAB"
)


def patch_bytes(path, old, new, label, required=False):
    with open(path, "rb") as f:
        data = f.read()
    n = data.count(old)
    if not n:
        msg = f"  ! {label}: no occurrences ({path})"
        if required:
            raise RuntimeError(msg)
        print(msg)
        return 0
    with open(path, "wb") as f:
        f.write(data.replace(old, new))
    print(f"  {label}: {n} replacement(s) ({os.path.relpath(path, ROOT)})")
    return n


def patch_text(path, pairs, label):
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        return 0
    total = 0
    for old, new in pairs:
        n = text.count(old)
        if n:
            text = text.replace(old, new)
            total += n
            print(f"  {label}: '{old}' -> '{new}' x{n}")
    if total:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    return total


def build_rsa_pem_block(target_len):
    """Build a PKCS#1 PEM block padded with spaces to exactly target_len bytes."""
    lines = [NEW_RSA_PUBLIC_KEY_B64[i:i + 64] for i in range(0, len(NEW_RSA_PUBLIC_KEY_B64), 64)]
    body = "".join(line + "\n" for line in lines)
    block = ("-----BEGIN RSA PUBLIC KEY-----\n" + body + "-----END RSA PUBLIC KEY-----").encode()
    if target_len < len(block):
        raise RuntimeError(f"RSA PEM target {target_len} shorter than key block {len(block)}")
    extra = target_len - len(block)
    if extra:
        body = ""
        for idx, line in enumerate(lines):
            body += line + (" " * extra if idx == len(lines) - 1 else "") + "\n"
        block = ("-----BEGIN RSA PUBLIC KEY-----\n" + body + "-----END RSA PUBLIC KEY-----").encode()
    if len(block) != target_len:
        raise RuntimeError(f"RSA PEM length mismatch: {len(block)} != {target_len}")
    return block


def patch_rsa_keys(path):
    """Replace Telegram RSA public keys in libtmessages with the KiteGrams key."""
    with open(path, "rb") as f:
        data = f.read()
    begin = b"-----BEGIN RSA PUBLIC KEY-----"
    end = b"-----END RSA PUBLIC KEY-----"
    expected = hashlib.sha1(base64.b64decode(NEW_RSA_PUBLIC_KEY_B64)).digest()[-8:].hex()
    count = 0
    pos = 0
    while True:
        i = data.find(begin, pos)
        if i < 0:
            break
        j = data.find(end, i)
        if j < 0:
            raise RuntimeError(f"unterminated RSA PEM block in {path}")
        stop = j + len(end)
        old = data[i:stop]
        replacement = build_rsa_pem_block(len(old))
        data = data[:i] + replacement + data[stop:]
        count += 1
        pos = i + len(replacement)
    if count != 2:
        raise RuntimeError(f"expected 2 RSA PEM blocks in {path}, found {count}")
    with open(path, "wb") as f:
        f.write(data)
    print(f"  RSA public keys -> KiteGrams x{count} ({os.path.relpath(path, ROOT)})")

    # Verify every embedded PEM block now decodes to our key.
    pos = 0
    fingerprints = []
    while True:
        i = data.find(begin, pos)
        if i < 0:
            break
        j = data.find(end, i)
        stop = j + len(end)
        block = data[i:stop]
        body = block.split(b"\n", 1)[1].rsplit(b"\n", 1)[0]
        b64 = b"".join(re.findall(rb"[A-Za-z0-9+/=]+", body))
        fingerprints.append(hashlib.sha1(base64.b64decode(b64)).digest()[-8:].hex())
        pos = stop
    if any(fp != expected for fp in fingerprints):
        raise RuntimeError(f"RSA key verification failed in {path}: {fingerprints} != {expected}")


def main():
    cm = os.path.join(ROOT, "smali_classes3", "org", "telegram", "tgnet", "ConnectionsManager.smali")
    print("== server address in smali ==")
    patch_bytes(cm, OLD_IP, NEW_IP, "server IP", required=True)

    print("== server address in native libs ==")
    lib_root = os.path.join(ROOT, "lib")
    seen = 0
    for abi in sorted(os.listdir(lib_root)):
        p = os.path.join(lib_root, abi, "libtmessages.49.so")
        if os.path.isfile(p):
            seen += patch_bytes(p, OLD_IP, NEW_IP, f"server IP [{abi}]", required=True)
    if seen < 4:
        raise RuntimeError(f"expected 4 native libs patched, got {seen}")

    print("== MTProto RSA public keys in native libs ==")
    rsa_seen = 0
    for abi in sorted(os.listdir(lib_root)):
        p = os.path.join(lib_root, abi, "libtmessages.49.so")
        if os.path.isfile(p):
            patch_rsa_keys(p)
            rsa_seen += 1
    if rsa_seen < 4:
        raise RuntimeError(f"expected 4 native libs RSA-patched, got {rsa_seen}")

    print("== package name ==")
    n = 0
    for dirpath, _, files in os.walk(ROOT):
        for name in files:
            if name.endswith((".smali", ".xml")):
                n += patch_text(os.path.join(dirpath, name), [(OLD_PKG, NEW_PKG)], "package")
    if n < 10:
        raise RuntimeError(f"expected >=10 package replacements, got {n}")

    print("== visible branding ==")
    strings = os.path.join(ROOT, "res", "values", "strings.xml")
    patch_text(strings, [(">javagram<", ">KiteGrams<")], "AppName")
    patch_text(strings, [(">javagram Beta<", ">KiteGrams Beta<")], "AppNameBeta")
    ui = os.path.join(ROOT, "smali_classes3", "org", "telegram", "ui", "bz.smali")
    patch_text(ui, [('const-string v5, "javagram"', 'const-string v5, "KiteGrams"')], "UI wordmark")

    print("== localization binaries (same-length only) ==")
    assets = os.path.join(ROOT, "assets")
    for name in sorted(os.listdir(assets)):
        if name.startswith("localization_") and name.endswith(".bin"):
            p = os.path.join(assets, name)
            patch_bytes(p, b"JavaGram", b"KiteGram", f"localization {name}")
            patch_bytes(p, b"javagram", b"kitegram", f"localization {name} lowercase")

    print("== verifying no leftovers ==")
    leftovers = 0
    for dirpath, _, files in os.walk(ROOT):
        for name in files:
            p = os.path.join(dirpath, name)
            try:
                d = open(p, "rb").read()
            except OSError:
                continue
            for needle in (OLD_IP, OLD_PKG.encode()):
                c = d.count(needle)
                if c:
                    leftovers += c
                    print(f"  ! leftover {needle!r} x{c} in {os.path.relpath(p, ROOT)}")
    if leftovers:
        raise RuntimeError(f"{leftovers} old branding/server leftovers")
    print("== done ==")


if __name__ == "__main__":
    main()
