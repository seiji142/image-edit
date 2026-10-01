"""image_compare: diff + metricas + side-by-side. Devuelve un numero,
no tres screenshots (ahorro de contexto). Sin dependencias pesadas."""
import numpy as np
from PIL import Image

from .sandbox import check_read, check_write
from .util import atomic_save_pil, default_out, ensure_different


def run(path_a, path_b, output=None, cwd=None):
    a = check_read(path_a, cwd)
    b = check_read(path_b, cwd)
    with Image.open(a) as ima:
        ima.load()
        ra = np.asarray(ima.convert("RGB")).astype(np.int16)
    with Image.open(b) as imb:
        imb.load()
        rb = np.asarray(imb.convert("RGB")).astype(np.int16)
    if ra.shape != rb.shape:
        raise ValueError(
            "dimensiones distintas: %s=%dx%d vs %s=%dx%d"
            % (a, ra.shape[1], ra.shape[0], b, rb.shape[1], rb.shape[0])
        )
    d = np.abs(ra - rb)
    mean_abs = round(float(d.mean()), 3)
    pct_gt40 = round(100.0 * float((d.max(axis=2) > 40).mean()), 3)
    max_abs = int(d.max())

    if output is None:
        output = default_out(
            a, "-vs-" + b.stem, ".png",
        )
    out = check_write(output, cwd)
    ensure_different(a, out)
    ensure_different(b, out)
    h, w = ra.shape[:2]
    sbs = np.full((h, w * 2 + 8, 3), 128, dtype=np.uint8)
    sbs[:, :w] = ra.astype(np.uint8)
    sbs[:, w + 8:] = rb.astype(np.uint8)
    atomic_save_pil(Image.fromarray(sbs), out)

    return {
        "a": str(a),
        "b": str(b),
        "width": w,
        "height": h,
        "mean_abs_diff": mean_abs,
        "pct_px_gt40": pct_gt40,
        "max_abs_diff": max_abs,
        "side_by_side": str(out),
    }
