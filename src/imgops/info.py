"""image_info: metadata rapida. NO importa torch (ver selftest)."""
from PIL import Image

from .sandbox import check_read
from .util import describe_file

_ALPHA_MODES = ("RGBA", "LA", "PA")


def run(input_path, cwd=None):
    p = check_read(input_path, cwd)
    with Image.open(p) as im:
        im.load()
        width, height = im.size
        rec = {
            "width": width,
            "height": height,
            "format": im.format,
            "mode": im.mode,
            "has_alpha": im.mode in _ALPHA_MODES or "transparency" in im.info,
        }
    rec.update(describe_file(p))
    return rec
