"""image_transform: crop + resize Lanczos + convert. Sin dependencias pesadas."""
from PIL import Image

from .mask import parse_box
from .sandbox import check_read, check_write
from .util import atomic_save_pil, default_out, describe_file, ensure_different

_FORMATS = {"png": "PNG", "jpg": "JPEG", "jpeg": "JPEG", "webp": "WEBP"}


def parse_size(s):
    try:
        w, h = (int(v) for v in str(s).lower().split("x"))
    except ValueError:
        raise ValueError("tamano invalido (esperado WxH): %r" % (s,))
    if w <= 0 or h <= 0:
        raise ValueError("tamano no positivo: %r" % (s,))
    return w, h


def run(input_path, output=None, crop=None, resize=None, fmt=None,
        quality=None, cwd=None):
    src = check_read(input_path, cwd)
    with Image.open(src) as im:
        im.load()
        img = im.convert("RGB")
        applied = []

    if crop is not None:
        x, y, w, h = parse_box(crop)
        img = img.crop((x, y, x + w, y + h))
        applied.append("crop=%s" % crop)

    if resize is not None:
        w, h = parse_size(resize)
        img = img.resize((w, h), Image.Resampling.LANCZOS)
        applied.append("resize=%s" % resize)

    save_kw = {}
    ext = None
    if fmt is not None:
        key = str(fmt).lower().lstrip(".")
        if key not in _FORMATS:
            raise ValueError("formato no soportado (png/jpg/webp): %r" % (fmt,))
        ext = "." + ("jpg" if key == "jpeg" else key)
        applied.append("format=%s" % key)
    if quality is not None:
        q = int(quality)
        if not (1 <= q <= 100):
            raise ValueError("quality fuera de 1-100: %r" % (quality,))
        save_kw["quality"] = q
        applied.append("quality=%d" % q)

    if output is None:
        output = default_out(src, "-transformed", ext)
    out = check_write(output, cwd)
    ensure_different(src, out)
    dest = atomic_save_pil(img, out, **save_kw)
    rec = {
        "output": str(dest),
        "width": img.size[0],
        "height": img.size[1],
        "applied": applied,
    }
    rec.update(describe_file(dest))
    return rec
