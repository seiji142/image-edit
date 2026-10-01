# imgops (repo image-edit)

Toolkit local de edición de imágenes: paquete Python aislado + CLI + docs.
Sin MCP por ahora (veredicto de los 3 auditores en `Page-Transitions/docs/`):
el MCP llega solo si dispara un gatillo medible. Origen del conocimiento:
`Page-Transitions/PASOS.md` (R8–R11, Toolchain, Receta) y `docs/FASE0.md`.

## Qué es / cuándo usarlo / ayuda

- **Qué es:** 6 comandos para limpiar y medir imágenes PNG/JPG/WebP con
  LaMa en CPU (~18-24 s/imagen 855×536), máscaras por ROIs y comparaciones.
- **Cuándo usarlo:** cuando haya que quitar texto/UI horneados de screenshots,
  consultar dimensiones, recortar/redimensionar/convertir o cuantificar un diff.
- **Ayuda:** `imgops --help` (progressive disclosure: el agente lee el help
  solo cuando lo necesita, ~300 tokens, en vez de 1200 de schemas MCP).

## Instalación limpia (Windows, sin GPU, Python 3.10)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.lock.txt `
  --extra-index-url https://download.pytorch.org/whl/cpu
.\imgops.cmd selftest   # 5/5 PASS en ~25 s
```

- `requirements.lock.txt`: pins exactos + hashes (torch/torchvision desde el índice CPU).
- `known-good.txt`: mismo conjunto sin hashes, oráculo del check `lock`.
- El modelo `big-lama.pt` NO se commitea (196 MB): vive en
  `~/.cache/torch/hub/checkpoints/` y `inpaint` verifica su SHA256 al arrancar.
  Sin descarga implícita: si falta o el hash difiere, aborta con mensaje.
- Garantía de intérprete: `imgops.cmd` apunta duro a `.venv\Scripts\python.exe`
  (el agente no debe invocar el Python compartido). `PYTHONUTF8=1` incluido.

## Comandos

| Comando | Ejemplo | Notas |
|---|---|---|
| `info` | `imgops info hero.png` | dims, formato, modo, alfa, bytes, sha256. **No importa torch** (instantáneo). |
| `mask` | `imgops mask hero.png --boxes 315,215,225,100 --dilate 3` | ROIs `x,y,w,h` + `--from-alpha` + `--auto-threshold lo,hi` → `out/<base>-mask.png` + `out/<base>-overlay.png` (**revisar el overlay con ojos antes de pagar la inferencia**). |
| `inpaint` | `imgops inpaint hero.png hero-mask.png` | LaMa + **compositado obligatorio** `out=orig*(1-mask)+lama*mask` (fuera de máscara, bit-idéntico). `--dry-run` devuelve el plan sin ejecutar. |
| `transform` | `imgops transform hero.png --crop 0,0,1440,900 --resize 1440,900 --format png` | crop → resize Lanczos → convert (png/jpg/webp, `--quality`). |
| `compare` | `imgops compare a.png b.png` | `mean_abs_diff`, `%px>40`, `max` + `side-by-side`. Reemplaza "mirar 3 screenshots" por "leer un float". |
| `selftest` | `imgops selftest [--only info mask inpaint transform lock]` | 5 checks sobre fixtures sintéticas 256 px (ver `src/imgops/selftest.py`). |

Contrato de salida (JSON por stdout): `{path|output, width, height, bytes, sha256, ms}`
o `{..., side_by_side, mean_abs_diff, ...}`. **Jamás píxeles, jamás sobrescribe el
input** (salida determinista en `out/` al lado, escritura atómica
tempfile + `os.replace`). Sandbox: cwd + allowlist
`IMAGE_EDIT_READ_ROOTS` / `IMAGE_EDIT_WRITE_ROOTS`; rechaza UNC, `\\?\` y nombres
de dispositivo; `Path.resolve()` verificado en cada llamada.

## Receta: fondos desde video (resumen portable, detalle en PASOS.md)

1. Timestamps desde la transcripción, no a ojo (anotar descartes, ej. end-screens).
2. `yt-dlp -F <url>` antes de asumir resolución; mejor mp4 ≤1080p.
3. Descarga por secciones a Temp (`--download-sections`, `--force-keyframes-at-cuts`).
4. Extracción frame-exacta con `-ss` DESPUÉS de `-i` + `ffprobe` + ojos (no póster/end-card).
5. Si sirve tal cual → crop → upscale Lanczos → swap. Si trae UI horneada → paso 6.
6. **Máscaras por glifos, no rectángulos**: ROI + umbral de color + dilatación 3 px;
   cursor con rectángulo completo; guardar máscara + **revisar `*-overlay.png` (magenta)**.
7. LaMa en una pasada sobre RGB (PNG con alfa → `.convert("RGB")`), **upscale Lanczos
   DESPUÉS**, swap con respaldos `*-orig`, re-shoot del efecto (contraste/legibilidad).
8. Aceptación fijada antes de mirar: sin letras residuales ni manchas que canten a 1440×900.

yt-dlp/ffmpeg son adquisición (churn alto) y **no entran al paquete**: viven en el
Python compartido / WinGet. El paquete empieza donde hay un PNG en disco.

## Troubleshooting Windows

- **Arranque frío lento**: Defender escanea el `.pt` (196 MB) y las DLL de torch;
  excluir `.venv/` y `~/.cache/torch/hub/` en Defender (requiere admin).
- **`import torch` 3-8 s**: normal en CPU; por eso es perezoso (solo `inpaint` lo paga).
- **Paths con espacios**: nunca `shell=True`; el CLI usa argv; probar con comillas.
- **Archivo bloqueado** (visor abierto): Windows no deja sobrescribir; cerrar handles
  (`with Image.open(...)`) y nunca escribir in-place (cubierto por contrato).
- **Logs con acentos/emoji**: `PYTHONUTF8=1` ya va en el shim; JSON siempre ASCII.
- **CPU**: `IMGOPS_THREADS` (default 4) + `torch.set_num_threads`; medir antes de subir.
- **`torch.jit.load` FutureWarning**: cosmético (stderr); importa para el futuro MCP
  stdio (todo log a stderr), no para el CLI.
- Modelo ausente/hash distinto → `inpaint` aborta; restaurarlo a la ruta fija.
- **OneDrive**: este repo vive dentro del árbol OneDrive y el `.venv` son
  ~24k archivos: pausar la sincronización **antes** de `pip install` o
  `selftest` (OneDrive bloquea DLLs → `WinError 5`, y consume 1 núcleo
  hasheando). Comandos: `Get-Process -Name 'OneDrive*' | Stop-Process -Force`
  para pausar; reanudar con el ejecutable de `$env:LOCALAPPDATA\OneDrive`.

## Gatillo MCP (medible, no estimado)

Cada invocación agrega una línea a `logs/imgops-usage.jsonl` (git-ignorada).
Fase 2 (wrapper MCP ~100 líneas, opt-in por proyecto, 1 imagen/llamada, logs a
stderr) solo si: **≥3 proyectos distintos la usan, o ≥10 invocaciones en 60 días,
o ≥2 fallos de intérprete/quoting cada 10 usos**. Revisar el log al pedirlo.

## Mantenimiento (responsable: el usuario, 30 min trimestrales)

Correr `imgops selftest` por calendario. Si pasa, cerrar sin tocar nada
(la higiene del toolchain CPU-only es **no tocar nada**). Si falla, el output dice
qué. Reglas: pins congelados, actualizar solo por necesidad (CVE o fallo);
probar updates de torch/LaMa en un venv nuevo y promover solo tras `selftest`;
trimestral: `selftest` + `pip list --outdated` + `pip-audit` (dev).

## Fuera de alcance (documentado, no olvidado)

yt-dlp+ffmpeg en el paquete · upscale neural (Real-ESRGAN) · CRAFT/`mask_text`
(candidata v2 #1 si el masking manual se vuelve cuello medido) · SDXL ·
thumbnails base64 · URLs/cookies/modelos por parámetro · MCP global.

## Estructura

```
├── cli.py                  # argparse (uso: imgops <cmd> --help)
├── imgops.cmd              # shim -> .venv (garantia de interprete)
├── src/imgops/             # info, mask, inpaint(lazy torch), transform,
│                           # compare, sandbox(3 asserts), selftest, util
├── tests/smoke/            # wrapper pytest del selftest
├── requirements.lock.txt   # pins + hashes (--require-hashes)
├── known-good.txt          # freeze plano (oraculo del check lock)
├── docs/FASE0.md           # reparacion del env compartido
├── docs/FASE1.md           # construccion del paquete (este trabajo)
└── logs/imgops-usage.jsonl # medicion del gatillo MCP (local, ignorada)
```

## Licencia

MIT
