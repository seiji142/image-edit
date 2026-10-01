# Fase 0 — Reparación del env compartido (2026-10-01)

Acción prioritaria de `auditor op.md` §0, ejecutada antes de escribir código del paquete.
Objetivo: dejar el Python compartido (3.10.7) en estado conocido y con regla anti-reincidencia.

## F0.1 Freeze del estado degradado

`~/.config/opencode/requirements-shared.lock.txt` (hecho, no deseo):

| Paquete | Versión congelada |
|---|---|
| Pillow | 9.5.0 (degradado desde 12.2.0) |
| opencv-python | 4.11.0.86 (degradado desde 4.13) |
| numpy | 1.26.4 |
| torch / torchvision | 2.14.1+cpu / 0.29.1 |
| simple-lama-inpainting | 0.1.2 |
| yt-dlp | 2026.8.19 |

## F0.2 Template con Pillow 9.5: VIVO

- Superficie usada: `Image.open/convert/resize`, `ImageChops.difference`, `ImageStat`,
  `ImageOps.fit`, `Image.Resampling.LANCZOS/NEAREST`. Cero aliases eliminados en Pillow 10
  (no hay `ANTIALIAS`). Medido con `python -c` sobre `assets/hero-orbit.png` + corrida real
  de `templates/web-design-tutorials/review/diff.py` (`dif-media: 0.0`).

## F0.3 Restauración (con desvío medido respecto a op.md)

Propuesto op.md: Pillow 12 + opencv 4.13. Ejecutado:

1. `pip install Pillow==12.2.0` → OK.
2. `pip install opencv-python==4.13.0.90` → arrastró **numpy 1.26.4 → 2.2.6**
   (opencv 4.13 exige `numpy>=2`), con un `WinError 5` transitorio en el primer intento
   (DLL bloqueado; reintento limpio).
3. Auditoría de daños: `chromadb` 0.5.5 (servicio de memoria `brain-ai-01`, sin `.venv`
   propio) **muerto** bajo numpy 2 (`np.float_` eliminado); `pandas` 1.4.3 **roto**
   (incompatibilidad binaria). `torch`/`playwright` intactos.
4. **Rollback parcial**: `numpy==1.26.4` + `opencv-python==4.11.0.86`. Verificado:
   chromadb add/count/query OK, pandas OK, torch OK, PIL 12 (`fit` Lanczos + `diff.py`),
   cv2 Telea OK sobre sintética. `pip check` solo reporta `sse-starlette/starlette`
   (preexistente, consta en el freeze) y `simple-lama-inpainting` vs Pillow 12
   (intencional: LaMa se muda al `.venv` de este repo en Fase 1).

**Estado final compartido**: Pillow **12.2.0** ✅ restaurado · numpy 1.26.4 · opencv 4.11.0.86
(probado en R10/R11, API suficiente para `inpaint`/capturas) · torch 2.14.1+cpu intacto.
Desvío documentado: opencv queda en 4.11 porque 4.13 exige numpy 2 y eso mata el
servicio de memoria. Si el futuro `imgops` necesitara opencv ≥4.13, vive en su `.venv`.

## F0.4 Regla escrita

`templates/web-design-tutorials/install.ps1` (paso 2): pin `pillow==12.2.0` +
comentario `REGLA-COMPARTIDO` (nada de `pip install` sin pin/manifiesto; pesadas a
`.venv` aislado). Era el vector de reincidencia: instalaba `pillow` sin versión.

## Datos para Fase 1

- `big-lama.pt` en `~/.cache/torch/hub/checkpoints/`, SHA256
  `7BA7AA7A...C9E6B4C` (hash completo en bitácora de sesión). Cargar desde ruta fija,
  sin descarga en inferencia.
- Efecto colateral del smoke de chromadb: descargó `all-MiniLM-L6-v2` (~79 MB) a
  `~/.cache/chroma` (caché, inofensivo).
- `simple-lama-inpainting` 0.1.2 sigue instalado en el compartido pero no funcional
  (Pillow 12); desinstalarlo del compartido cuando el `.venv` de Fase 1 exista.
