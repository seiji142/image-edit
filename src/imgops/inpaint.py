"""image_inpaint_lama: nucleo del toolkit.

- torch se importa SOLO dentro de `_load_model` (perezoso, obligatorio:
  `info` debe seguir instantaneo).
- Modelo desde ruta fija + verificacion de hash. Sin descarga implicita:
  si el .pt falta o el hash difiere, se aborta con mensaje, no se descarga.
- Compositado obligatorio: out = orig*(1-mask) + lama*mask. Invariante
  testeable: fuera de la mascara, bit-identico al input.
"""
import hashlib
import os
from pathlib import Path

import numpy as np
from PIL import Image

from .sandbox import check_read, check_write
from .util import (
    atomic_save_pil,
    default_out,
    describe_file,
    ensure_different,
    sha256_file,
)

LAMA_SHA256 = "7ba7aa7ac37a4d41fdbbeba3a2af7ead18058552997e3a3cd1a3b2210c9e6b4c"
LAMA_PATH = (
    Path.home() / ".cache" / "torch" / "hub" / "checkpoints" / "big-lama.pt"
)
MODEL_THREADS_ENV = "IMGOPS_THREADS"


def _verify_model():
    if not LAMA_PATH.exists():
        raise FileNotFoundError(
            "modelo LaMa no encontrado en %s; sin descarga implicita "
            "(restaurarlo a la ruta fija y reintentar)" % (LAMA_PATH,)
        )
    digest = sha256_file(LAMA_PATH)
    if digest != LAMA_SHA256:
        raise ValueError(
            "hash del modelo distinto al registrado (esperado %s, hallado %s)"
            % (LAMA_SHA256, digest)
        )
    return LAMA_PATH


def _load_model():
    import torch  # noqa: PLC0415 -- perezoso a proposito

    torch.set_num_threads(int(os.environ.get(MODEL_THREADS_ENV, "4")))
    model_path = _verify_model()
    os.environ["LAMA_MODEL"] = str(model_path)
    from simple_lama_inpainting import SimpleLama  # noqa: PLC0415

    return SimpleLama(device=torch.device("cpu"))


def plan(input_path, mask_path, output=None, cwd=None):
    src = check_read(input_path, cwd)
    msk = check_read(mask_path, cwd)
    with Image.open(src) as im:
        im.load()
        sw, sh = im.size
    with Image.open(msk) as mm:
        mm.load()
        mw, mh = mm.size
    if (sw, sh) != (mw, mh):
        raise ValueError(
            "mascara %dx%d no coincide con imagen %dx%d" % (mw, mh, sw, sh)
        )
    if output is None:
        output = default_out(src, "-inpainted")
    out = check_write(output, cwd)
    ensure_different(src, out)
    return {
        "input": str(src),
        "mask": str(msk),
        "output": str(out),
        "width": sw,
        "height": sh,
        "model": str(LAMA_PATH),
        "threads": int(os.environ.get(MODEL_THREADS_ENV, "4")),
    }


def run(input_path, mask_path, output=None, dry_run=False, cwd=None):
    p = plan(input_path, mask_path, output, cwd)
    if dry_run:
        p["dry_run"] = True
        return p
    with Image.open(p["input"]) as im:
        orig = np.asarray(im.convert("RGB"))
    with Image.open(p["mask"]) as mm:
        m = (np.asarray(mm.convert("L")) > 127).astype(np.uint8) * 255
    if not (m > 0).any():
        raise ValueError("mascara vacia: nada que inpaintar")
    lama = _load_model()
    gen = np.asarray(lama(Image.fromarray(orig), Image.fromarray(m)))
    if np.isnan(gen).any():
        raise ValueError("LaMa devolvio NaN")
    # simple-lama rellena a multiplo de 8 (abajo/derecha, simetrico) y devuelve
    # con padding (ej. 854 -> 856). Se recorta a dims del input: la salida del
    # comando siempre mide lo mismo que la entrada (R11 conservo el padding).
    oh, ow = orig.shape[:2]
    gh, gw = gen.shape[:2]
    unpadded_from = None
    if (gh, gw) != (oh, ow):
        if gh < oh or gw < ow:
            raise ValueError(
                "LaMa devolvio %dx%d, menor que el input %dx%d"
                % (gw, gh, ow, oh)
            )
        unpadded_from = [gw, gh]
        gen = gen[:oh, :ow]
    sel = (m > 0)[:, :, None]
    out = np.where(sel, gen, orig).astype(np.uint8)
    dest = atomic_save_pil(Image.fromarray(out), p["output"])
    rec = {
        "output": str(dest),
        "width": p["width"],
        "height": p["height"],
        "method": "lama-big",
        "composited": True,
    }
    if unpadded_from is not None:
        rec["unpadded_from"] = unpadded_from
    rec.update(describe_file(dest))
    return rec
