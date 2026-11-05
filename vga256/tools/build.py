#!/usr/bin/env python3
"""Rebuild VGA2568088 using a supplied compatible historical toolchain.

Never downloads tools, initializes a lease, or modifies the source checkout.
"""
from pathlib import Path
import argparse
import importlib.util
import os
import re
import shutil
import sys
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TOOLS = ("MASM.EXE", "LINK4.EXE", "EXE2BIN.EXE", "SWINLIBC.LIB")
RESOURCES = ("CONFIG", "COLORTAB", "FONTS")


def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + ".py"))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", type=Path, required=True,
                        help="Directory containing MASM.EXE, LINK4.EXE, EXE2BIN.EXE and SWINLIBC.LIB, possibly in subdirectories")
    parser.add_argument("--dosbox", type=Path, required=True, help="Existing DOSBox-X executable")
    parser.add_argument("--lease", type=Path, required=True,
                        help="Existing nonempty shared emulator lease; never created by this script")
    parser.add_argument("--out", type=Path, required=True, help="New build directory")
    args = parser.parse_args()
    out, toolchain = args.out.resolve(), args.toolchain.resolve()
    if out.exists():
        raise SystemExit("Choose a fresh --out directory")
    if out == ROOT or ROOT in out.parents:
        raise SystemExit("Choose an --out directory outside the source checkout")
    if not args.lease.is_file() or not args.lease.stat().st_size:
        raise SystemExit("--lease must already exist and be nonempty")
    if not args.dosbox.is_file():
        raise SystemExit("Missing DOSBox-X executable: " + str(args.dosbox))

    files = sorted(path for path in toolchain.rglob("*") if path.is_file())
    found = {}
    for name in TOOLS:
        matches = [path for path in files if path.name.upper() == name and path.stat().st_size]
        if not matches:
            raise SystemExit("Missing toolchain input: " + name)
        found[name] = matches[0]

    # The linker response file is the object list used by the actual build.
    names = re.findall(r"\b([a-z0-9_]+)\.obj\b",
                       (ROOT / "src/VGA256.LNK").read_text(), re.I)
    names = [name.upper() for name in names]
    if not names or len(set(names)) != len(names):
        raise SystemExit("VGA256.LNK must list a nonempty, unique set of objects")

    out.mkdir(parents=True)
    for source, destination in (("src", "SRC"), ("include", "INC"), ("resources", "RES")):
        shutil.copytree(ROOT / source, out / destination)
    for directory in ("BIN", "LIB", "run"):
        (out / directory).mkdir()
    for name, path in found.items():
        shutil.copy2(path, out / ("LIB" if name.endswith(".LIB") else "BIN") / name)
    shutil.copy2(ROOT / "BUILD.BAT", out / "BUILD.BAT")
    config = out / "run/BUILD.CONF"
    config.write_text(
        "[sdl]\noutput=surface\nfullscreen=false\n"
        "[dosbox]\nmachine=vgaonly\nmemsize=16\nsplash logo=false\nshow basic information=false\n"
        "[cpu]\ncore=normal\ncputype=386\ncycles=fixed 200000\n"
        "[mixer]\nnosound=true\n[midi]\nmididevice=none\n"
        '[autoexec]\nmount R "' + str(out) + '"\nR:\nBUILD.BAT\nexit\n')
    module("guarded_dosbox").run(args.dosbox.resolve(), config, args.lease.resolve(), 240)

    logs = ([out / "SRC" / (name + ".LOG") for name in names]
            + [out / "SRC/LINK.LOG"]
            + [out / "RES" / (name + ".LOG") for name in RESOURCES])
    errors = []
    for path in logs:
        if not path.is_file():
            errors.append("Missing log: " + str(path))
            continue
        text = path.read_text(errors="replace")
        if (any(int(count) for count in re.findall(r"(\d+)\s+Severe\s+Errors", text))
                or re.search(r"error [AL]\d+|fatal error", text, re.I)):
            errors.append(path.name + ": " + text)
    if not (out / "RES/DONE.TXT").is_file():
        errors.append("BUILD.BAT did not finish successfully; inspect the compiler logs")
    if errors:
        raise SystemExit("\n".join(errors))
    required = [out / "SRC" / (name + suffix) for name in names for suffix in (".OBJ", ".LST")]
    required += [out / "SRC/VGA256.DRV", out / "SRC/VGA256.MAP"]
    required += [out / "RES" / (name + ".BIN") for name in RESOURCES]
    for path in required:
        if not path.is_file() or not path.stat().st_size:
            raise SystemExit("Missing or empty build output: " + str(path))

    os.environ.update(VGA256_RESOURCES=str(out / "RES"), VGA256_WINDOWS_H=str(out / "INC/WINDOWS.H"))
    pack = module("pack_resources")
    records = pack.resource_records()
    resources = pack.write_res(records)
    if pack.read_res(resources) != records:
        raise SystemExit("Resource roundtrip mismatch")
    (out / "VGA.RES").write_bytes(resources)
    binary, _ = pack.attach_ne((out / "SRC/VGA256.DRV").read_bytes(), records)
    (out / "VGA256.DRV").write_bytes(binary)
    print(f"Built {out / 'VGA256.DRV'}: {len(binary):,} bytes, {len(names)} modules, {len(records)} resources")


if __name__ == "__main__":
    main()
