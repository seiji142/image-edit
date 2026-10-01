# Fase 1 — Paquete imgops (2026-10-01)

Alcance cerrado: repo `image-edit` + CLI `imgops`, v1 de 6 comandos.
No MCP (gatillo en README). Regla 13 vigente: de `Page-Transitions` solo se lee.

## F1.1 .venv (Python 3.10.7, `pip` actualizado dentro del venv)

`python -m venv .venv` en la raíz. Ignorado por git (`.gitignore`: `.venv/`).
Nada del paquete toca el Python compartido.

## F1.2 Pins + lock real

Instalación por capas (índice CPU solo para torch/torchvision):

```
torch==2.14.1+cpu  torchvision==0.29.1  --index-url .../whl/cpu
simple-lama-inpainting==0.1.2  opencv-python==4.11.0.86  pytest==9.0.3
```

El resolver convergió al combo probado de R11 (numpy 1.26.4, Pillow 9.5.0).
`pip check`: limpio. Artefactos:

- `requirements.lock.txt`: 24 pins + `--require-hashes` (instalación reproducible).
- `known-good.txt`: freeze plano, oráculo del check `lock`.
- `big-lama.pt` verificado por SHA256 al arrancar cada `inpaint`
  (`7ba7aa7a…e6b4c`, hash completo en `docs/FASE0.md`).

## F1.3 Código (`src/imgops/` + `cli.py` + `imgops.cmd`)

| Módulo | Decisiones |
|---|---|
| `info` | Solo PIL. Test exige `torch not in sys.modules`. |
| `mask` | ROIs + `--dilate` + `--from-alpha` + `--auto-threshold lo,hi`; overlay magenta (receta `Máscaras por glifos.md` §1, sin la vía SDXL no ejecutada). |
| `inpaint` | `torch` perezoso + `torch.set_num_threads(4)`; `LAMA_MODEL` a ruta fija tras verificar hash (cero descarga implícita); **compositado obligatorio**; máscara vacía y NaN abortan; `--dry-run`. |
| `transform` | crop → resize Lanczos → convert (png/jpg/webp + quality). |
| `compare` | dims estrictas; `mean_abs_diff`, `%px>40`, `max` + side-by-side. |
| `sandbox` | 3 asserts + rechazo UNC/dispositivos; raíces = cwd + `IMAGE_EDIT_READ/WRITE_ROOTS`. |
| `util` | JSON ASCII, `ms` por comando, escritura atómica, `log_usage` JSONL (ignorado por git). |
| `cli.py` | argparse; errores → `{"ok":false}` + exit 2; `selftest` con `--only`. |
| `imgops.cmd` | shim duro al `.venv` + `PYTHONUTF8=1`. |

API LaMa verificada contra el fuente instalado (`SimpleLama()(rgb, mask)`).

## F1.4 Selftest 5/5 (~24 s, también vía `pytest tests/smoke`)

`info` (86 ms, sin torch) · `mask` (área 1.56% = esperada + overlay) ·
`inpaint` (23.9 s: bit-idéntico fuera, cambio dentro) · `transform` (roundtrip) ·
`lock` (17→24 paquetes, sin deriva). Bugs que cazó el propio selftest:
sandbox bloqueaba fixtures en Temp (allowlist con alcance de corrida),
BOM en el freeze (parse `utf-8-sig` + archivos reescritos sin BOM),
typo en el hash del modelo (el abortador funcionó como diseñado).

Verificado además: shim con **paths con espacios** (allowlist + comillas, 130 ms)
y rechazo sandbox fuera de raíces.

## F1.5 Docs + CI

- `README.md`: qué/cuándo/help, install limpio, tabla de comandos, receta
  (resumen PASOS 1-8), troubleshooting Windows, gatillo MCP, mantenimiento,
  fuera de alcance.
- `.ai/context.md`: 3 líneas imgops.
- `.github/workflows/ci.yml`: reescrito para este repo (install desde lock con
  hashes + `selftest` completo; el anterior pedía scripts de otro dominio).

## Pendiente (no Fase 1)

- `requirements.txt` del esqueleto (fastapi/uvicorn/...) no lo usa nada
  (venv y CI usan el lock): recortar o eliminar con orden explícita.
- `run_all_tests.py` / `tests/{unit,integration,...}` del otro dominio: sin uso.
- `simple-lama-inpainting` en el compartido: desinstalar cuando se confirme que
  nada fuera de este `.venv` lo necesita (hoy solo roto vs Pillow 12, inofensivo).
- Validación visual única vs `review/r10-lama-orbit.png` (Fase 2, con ojos).
