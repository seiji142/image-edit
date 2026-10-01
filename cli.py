#!/usr/bin/env python3
"""imgops CLI. Uso: imgops <comando> --help. Salida JSON por stdout.

Cada invocacion agrega una linea a logs/imgops-usage.jsonl (mide el gatillo MCP).
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from imgops import compare, info, inpaint, mask, selftest, transform  # noqa: E402
from imgops.sandbox import SandboxViolation  # noqa: E402
from imgops.util import emit, log_usage, timed  # noqa: E402


def _box_list(v):
    return v


def build_parser():
    p = argparse.ArgumentParser(prog="imgops",
                                description="Toolkit local de edicion de imagenes")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("info", help="metadata (no usa torch)")
    a.add_argument("input")

    a = sub.add_parser("mask", help="ROIs -> mascara + overlay preview")
    a.add_argument("input")
    a.add_argument("--boxes", nargs="*", default=[],
                   help="lista x,y,w,h (puede repetirse)")
    a.add_argument("--dilate", type=int, default=3)
    a.add_argument("--from-alpha", action="store_true")
    a.add_argument("--auto-threshold", default=None, help="lo,hi en gris")
    a.add_argument("--output", default=None)
    a.add_argument("--overlay", default=None)

    a = sub.add_parser("inpaint", help="LaMa + compositado obligatorio")
    a.add_argument("input")
    a.add_argument("mask")
    a.add_argument("--output", default=None)
    a.add_argument("--dry-run", action="store_true",
                   help="devuelve el plan sin ejecutar (antes de pagar ~24s)")

    a = sub.add_parser("transform", help="crop + resize Lanczos + convert")
    a.add_argument("input")
    a.add_argument("--output", default=None)
    a.add_argument("--crop", default=None, help="x,y,w,h")
    a.add_argument("--resize", default=None, help="WxH")
    a.add_argument("--format", default=None, help="png/jpg/webp")
    a.add_argument("--quality", type=int, default=None)

    a = sub.add_parser("compare", help="diff + metricas + side-by-side")
    a.add_argument("a")
    a.add_argument("b")
    a.add_argument("--output", default=None)

    a = sub.add_parser("selftest", help="suite de humo (~20s)")
    a.add_argument("--only", nargs="*", default=None,
                   choices=["info", "mask", "inpaint", "transform", "lock"])
    return p


def dispatch(ns):
    cwd = os.getcwd()
    if ns.cmd == "info":
        return timed(info.run, ns.input, cwd=cwd)
    if ns.cmd == "mask":
        return timed(mask.run, ns.input, boxes=_box_list(ns.boxes),
                     dilate=ns.dilate, from_alpha=ns.from_alpha,
                     auto_threshold=ns.auto_threshold, output=ns.output,
                     overlay=ns.overlay, cwd=cwd)
    if ns.cmd == "inpaint":
        return timed(inpaint.run, ns.input, ns.mask, output=ns.output,
                     dry_run=ns.dry_run, cwd=cwd)
    if ns.cmd == "transform":
        return timed(transform.run, ns.input, output=ns.output, crop=ns.crop,
                     resize=ns.resize, fmt=ns.format, quality=ns.quality,
                     cwd=cwd)
    if ns.cmd == "compare":
        return timed(compare.run, ns.a, ns.b, output=ns.output, cwd=cwd)
    if ns.cmd == "selftest":
        return timed(selftest.run, only=ns.only)
    raise AssertionError("comando desconocido: %s" % (ns.cmd,))


def main(argv=None):
    ns = build_parser().parse_args(argv)
    try:
        rec, ms = dispatch(ns)
        if ns.cmd == "selftest":
            rec = dict(rec)
        else:
            rec = dict(rec)
            rec["ms"] = ms
        rec["ok"] = rec.get("ok", True) if ns.cmd == "selftest" else True
        log_usage(ns.cmd, ms, rec["ok"])
        emit(rec)
        return 0 if rec["ok"] else 1
    except (SandboxViolation, ValueError, FileNotFoundError) as e:
        log_usage(ns.cmd, 0, False, e)
        emit({"ok": False, "cmd": ns.cmd, "error": str(e)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
