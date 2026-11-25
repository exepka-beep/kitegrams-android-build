#!/usr/bin/env python3
"""Rebrand a decoded JavaGram APK tree into KiteGrams, pointed at our server.

JavaGram ships as a multi-server client with its own test server hardcoded
(2.26.81.132:2398). This script repoints that default to the KiteGrams server
and replaces the visible JavaGram branding.

Usage: python3 scripts/rebrand_javagram.py <decoded_dir>
"""
import os
import sys

ROOT = sys.argv[1]
OLD_IP = b"2.26.81.132"
NEW_IP = b"2.26.81.165"  # same length as OLD_IP
OLD_PKG = "org.javagram.messenger.web"
NEW_PKG = "com.kitegrams.messenger"


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
