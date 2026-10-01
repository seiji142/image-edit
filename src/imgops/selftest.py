"""imgops selftest: 5 checks sobre fixtures sinteticas de 256px, ~20s total.

1. info sobre PNG (sin torch) -> dims/modo + torch NO importado.
2. mask desde ROIs -> area esperada +/-2% + overlay generado.
3. inpaint -> corre, fuera de mascara bit-identico, dentro cambio, sin NaN, <60s.
4. transform -> roundtrip de dims.
5. lock drift -> versiones instaladas == known-good.txt.
"""
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
from PIL import Image

from . import compare, info, inpaint, mask, transform

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
KNOWN_GOOD = REPO_ROOT / "known-good.txt"
INPAINT_BUDGET_S = 60


def _fixture(tmp):
    rng = np.random.default_rng(42)
    img = rng.integers(0, 256, (256, 256, 3), dtype=np.uint8)
    src = tmp / "fix.png"
    Image.fromarray(img).save(src)
    m = np.zeros((256, 256), dtype=np.uint8)
    m[48:80, 48:80] = 255  # 32x32 = 1024 px = 1.5625%
    msk = tmp / "fix-mask.png"
    Image.fromarray(m).save(msk)
    return src, msk, img, m


def check_info(tmp):
    src, _, _, _ = _fixture(tmp)
    rec = info.run(src)
    assert (rec["width"], rec["height"]) == (256, 256), rec
    assert rec["mode"] == "RGB", rec
    assert "torch" not in sys.modules, "info importo torch"
    return "info dims+modo OK, sin torch"


def check_mask(tmp):
    src, _, _, _ = _fixture(tmp)
    rec = mask.run(src, boxes=["48,48,32,32"], dilate=0,
                   output=tmp / "m.png", overlay=tmp / "o.png")
    expected = 100.0 * 1024 / (256 * 256)
    assert abs(rec["coverage_pct"] - expected) <= 2.0, rec
    assert Path(rec["overlay"]).exists(), rec
    return "mask area %.2f%% (esperado %.2f%%) + overlay OK" % (
        rec["coverage_pct"], expected)


def check_inpaint(tmp):
    src, msk, img, m = _fixture(tmp)
    t0 = time.perf_counter()
    rec = inpaint.run(src, msk, output=tmp / "out.png")
    elapsed = time.perf_counter() - t0
    assert elapsed < INPAINT_BUDGET_S, "inpaint tardo %.1fs" % elapsed
    with Image.open(rec["output"]) as im:
        out = np.asarray(im.convert("RGB")).astype(np.int16)
    outside = (m == 0)
    assert (out[outside] == img.astype(np.int16)[outside]).all(), \
        "fuera de mascara no es bit-identico"
    inside_changed = (out[m > 0] != img.astype(np.int16)[m > 0]).mean()
    assert inside_changed > 0.01, "dentro de mascara no cambio"
    return "inpaint bit-identico fuera, cambio dentro, %.1fs" % elapsed


def check_transform(tmp):
    src, _, _, _ = _fixture(tmp)
    rec = transform.run(src, output=tmp / "t.png", resize="128x128")
    assert (rec["width"], rec["height"]) == (128, 128), rec
    rec2 = transform.run(rec["output"], output=tmp / "t2.png", resize="256x256")
    assert (rec2["width"], rec2["height"]) == (256, 256), rec2
    return "transform roundtrip 256->128->256 OK"


def check_lock():
    want = {}
    for line in KNOWN_GOOD.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if "==" in line and not line.startswith("#"):
            name, ver = line.split("==", 1)
            want[name.strip().lower()] = ver.strip()
    try:
        from importlib.metadata import version
    except ImportError:
        from importlib_metadata import version  # noqa: F401
    drift = []
    for name, ver in sorted(want.items()):
        try:
            got = version(name)
        except Exception:
            drift.append("%s ausente (lock %s)" % (name, ver))
            continue
        if got != ver:
            drift.append("%s instalado %s != lock %s" % (name, got, ver))
    assert not drift, "; ".join(drift)
    return "lock sin deriva (%d paquetes)" % len(want)


CHECKS = (
    ("info", check_info),
    ("mask", check_mask),
    ("inpaint", check_inpaint),
    ("transform", check_transform),
    ("lock", check_lock),
)


def run(tmp_dir=None, only=None):
    results = []
    old_read = os.environ.get("IMAGE_EDIT_READ_ROOTS")
    old_write = os.environ.get("IMAGE_EDIT_WRITE_ROOTS")
    with tempfile.TemporaryDirectory(prefix="imgops-selftest-") as td:
        tmp = Path(tmp_dir) if tmp_dir else Path(td)
        tmp.mkdir(parents=True, exist_ok=True)
        # Las fixtures viven en Temp: se habilitan via allowlist con alcance
        # de esta corrida (ademas ejercita el mecanismo de raices extra).
        os.environ["IMAGE_EDIT_READ_ROOTS"] = str(tmp)
        os.environ["IMAGE_EDIT_WRITE_ROOTS"] = str(tmp)
        try:
            for name, fn in CHECKS:
                if only and name not in only:
                    continue
                t0 = time.perf_counter()
                try:
                    if name == "lock":
                        detail = fn()
                    else:
                        detail = fn(tmp)
                    ms = int((time.perf_counter() - t0) * 1000)
                    results.append({"check": name, "status": "PASS",
                                    "ms": ms, "detail": detail})
                except Exception as e:  # noqa: BLE001 -- el reporte lo necesita
                    ms = int((time.perf_counter() - t0) * 1000)
                    results.append({"check": name, "status": "FAIL",
                                    "ms": ms, "detail": "%s: %s"
                                    % (type(e).__name__, e)})
        finally:
            if old_read is None:
                os.environ.pop("IMAGE_EDIT_READ_ROOTS", None)
            else:
                os.environ["IMAGE_EDIT_READ_ROOTS"] = old_read
            if old_write is None:
                os.environ.pop("IMAGE_EDIT_WRITE_ROOTS", None)
            else:
                os.environ["IMAGE_EDIT_WRITE_ROOTS"] = old_write
    passed = sum(1 for r in results if r["status"] == "PASS")
    return {"checks": results, "passed": passed, "total": len(results),
            "ok": passed == len(results)}
