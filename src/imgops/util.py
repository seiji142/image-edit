"""Salida JSON, tiempos, escritura atomica y log de uso.

Sin dependencias pesadas: este modulo nunca importa torch.
"""
import hashlib
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = REPO_ROOT / "logs"
USAGE_LOG = LOGS_DIR / "imgops-usage.jsonl"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def emit(obj):
    print(json.dumps(obj, ensure_ascii=True))
    sys.stdout.flush()


def timed(fn, *args, **kwargs):
    t0 = time.perf_counter()
    out = fn(*args, **kwargs)
    ms = int((time.perf_counter() - t0) * 1000)
    return out, ms


def ensure_different(src, dst):
    if Path(src).resolve() == Path(dst).resolve():
        raise ValueError("prohibido escribir sobre el input: %s" % (dst,))


def default_out(input_path, suffix, ext=None):
    """out/ al lado del input, con sufijo. Determinista, nunca in-place."""
    p = Path(input_path)
    return p.parent / "out" / (p.stem + suffix + (ext if ext is not None else p.suffix))


def atomic_save_pil(img, dest, **save_kw):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(dest.parent), suffix=dest.suffix or ".tmp")
    os.close(fd)
    try:
        img.save(tmp, **save_kw)
        os.replace(tmp, dest)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return dest


def describe_file(path):
    p = Path(path)
    st = p.stat()
    return {"path": str(p), "bytes": st.st_size, "sha256": sha256_file(p)}


def log_usage(cmd, ms, ok, err=None):
    """Una linea JSONL por invocacion. Sirve para medir el gatillo MCP
    (>=10 usos/60d). Nunca rompe el comando si el log falla."""
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        rec = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "cmd": cmd,
            "ms": ms,
            "ok": bool(ok),
        }
        if err:
            rec["err"] = str(err)[:300]
        with open(USAGE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=True) + "\n")
    except OSError:
        pass
