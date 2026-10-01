"""Sandbox de filesystem: tres asserts, nada de chroot.

Protege contra el agente escribiendo en el lugar equivocado, no contra
atacantes (maquina local mono-usuario). Reglas:
  1. Raices permitidas: cwd del invocante + allowlist via env.
  2. realpath verificado bajo una raiz (mata `..` y symlinks/junctions).
  3. Prohibido borrar y prohibido escribir sobre el input (esto ultimo en
     `util.ensure_different`). Ademas: rechazo UNC y nombres de dispositivo.
"""
import os
from pathlib import Path

READ_ENV = "IMAGE_EDIT_READ_ROOTS"
WRITE_ENV = "IMAGE_EDIT_WRITE_ROOTS"

DEVICE_NAMES = (
    {"CON", "PRN", "AUX", "NUL"}
    | {"COM%d" % i for i in range(1, 10)}
    | {"LPT%d" % i for i in range(1, 10)}
)


class SandboxViolation(ValueError):
    pass


def _norm(s):
    return os.path.normpath(str(s))


def _is_unc(s):
    n = _norm(s)
    return n.startswith("\\\\") or n.startswith("//")


def _has_device(s):
    parts = _norm(s).replace("/", os.sep).split(os.sep)
    for part in parts:
        base = part.split(".")[0].upper()
        if base in DEVICE_NAMES:
            return True
    return False


def _extra_roots(env_var):
    roots = []
    for raw in (os.environ.get(env_var) or "").split(os.pathsep):
        raw = raw.strip().strip('"')
        if raw:
            roots.append(Path(raw))
    return roots


def _resolve_roots(roots, cwd):
    out = []
    for r in [Path(cwd)] + list(roots):
        try:
            out.append(r.resolve())
        except OSError:
            out.append(r.absolute())
    return out


def _check(path, kind, allowed_env, cwd):
    s = str(path)
    if _is_unc(s):
        raise SandboxViolation("%s UNC prohibida: %s" % (kind, s))
    if _has_device(s):
        raise SandboxViolation("%s con nombre de dispositivo: %s" % (kind, s))
    cwd = Path(cwd or os.getcwd())
    p = Path(s)
    if not p.is_absolute():
        p = cwd / p
    try:
        resolved = p.resolve()
    except OSError as e:
        raise SandboxViolation("%s no resoluble: %s (%s)" % (kind, s, e))
    roots = _resolve_roots(_extra_roots(allowed_env), cwd)
    if not any(resolved == r or r in resolved.parents for r in roots):
        raise SandboxViolation(
            "%s fuera de raices permitidas: %s" % (kind, resolved)
        )
    return resolved


def check_read(path, cwd=None):
    return _check(path, "lectura", READ_ENV, cwd)


def check_write(path, cwd=None):
    return _check(path, "escritura", WRITE_ENV, cwd)
