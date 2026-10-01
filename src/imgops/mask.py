"""image_mask: ROIs/boxes -> mascara PNG + overlay de preview.

Encapsula el conocimiento dificil de R11 (PASOS.md): mascaras por glifos,
no rectangulos blancos; dilatacion por antialias; preview magenta revisado
con ojos ANTES de pagar la inferencia.
"""
import cv2
import numpy as np
from PIL import Image

from .sandbox import check_read, check_write
from .util import atomic_save_pil, default_out, describe_file, ensure_different


def parse_box(s):
    try:
        x, y, w, h = (int(v) for v in str(s).split(","))
    except ValueError:
        raise ValueError("box invalida (esperado x,y,w,h): %r" % (s,))
    if w <= 0 or h <= 0:
        raise ValueError("box con w/h no positivos: %r" % (s,))
    return x, y, w, h


def parse_range(s):
    try:
        lo, hi = (int(v) for v in str(s).split(","))
    except ValueError:
        raise ValueError("rango invalido (esperado lo,hi): %r" % (s,))
    if not (0 <= lo <= hi <= 255):
        raise ValueError("rango fuera de 0-255 o invertido: %r" % (s,))
    return lo, hi


def _dilate(mask, px):
    if px <= 0:
        return mask
    k = 2 * int(px) + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    return cv2.dilate(mask, kernel)


def run(input_path, boxes=(), dilate=3, from_alpha=False,
        auto_threshold=None, output=None, overlay=None, cwd=None):
    src = check_read(input_path, cwd)
    with Image.open(src) as im:
        rgb = np.asarray(im.convert("RGB"))
    h, w = rgb.shape[:2]

    m = np.zeros((h, w), dtype=np.uint8)
    for b in boxes or ():
        x, y, bw, bh = parse_box(b)
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + bw, w), min(y + bh, h)
        if x1 > x0 and y1 > y0:
            m[y0:y1, x0:x1] = 255

    if from_alpha:
        with Image.open(src) as im:
            if "A" in im.getbands():
                alpha = np.asarray(im.getchannel("A"))
                m[alpha < 128] = 255

    if auto_threshold is not None:
        lo, hi = parse_range(auto_threshold)
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        m[((gray >= lo) & (gray <= hi))] = 255

    m = _dilate(m, dilate)

    if output is None:
        output = default_out(src, "-mask", ".png")
    out_mask = check_write(output, cwd)
    ensure_different(src, out_mask)
    atomic_save_pil(Image.fromarray(m), out_mask)

    if overlay is None:
        overlay = out_mask.parent / (out_mask.stem.replace("-mask", "") + "-overlay.png")
    out_overlay = check_write(overlay, cwd)
    ensure_different(src, out_overlay)
    sel = m > 0
    preview = rgb.copy()
    preview[sel] = (
        0.4 * rgb[sel].astype(np.float32)
        + 0.6 * np.array([255, 0, 255], dtype=np.float32)
    ).astype(np.uint8)
    atomic_save_pil(Image.fromarray(preview), out_overlay)

    area = int((m > 0).sum())
    rec = {
        "mask": str(out_mask),
        "overlay": str(out_overlay),
        "width": w,
        "height": h,
        "area_px": area,
        "coverage_pct": round(100.0 * area / (w * h), 2),
    }
    rec.update(describe_file(out_mask))
    return rec
