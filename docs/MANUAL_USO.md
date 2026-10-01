# Manual de uso de imgops (desde otro proyecto)

Cómo usar el toolkit **desde cualquier otro proyecto** donde necesites
modificar imágenes: limpiar texto/UI horneados, consultar dimensiones,
recortar/redimensionar/convertir o cuantificar diferencias.

Todo lo de abajo se probó tal cual en Windows, sin GPU, Python 3.10.7.
Los ejemplos usan archivos reales (`orbit.png` 854×536 de Page-Transitions)
con sus outputs medidos: son copiables, no ilustrativos.

## 0. Requisito único (una vez)

Necesitas, en este orden:

1. El repo `image-edit` clonado en disco (ej. `C:\...\Proyecto AI\image-edit`).
2. Su `.venv` instalado (ver `README.md` § Instalación).
3. El modelo `big-lama.pt` en `~/.cache/torch/hub/checkpoints/` (llega solo
   la primera vez que se usó; `inpaint` verifica el hash y aborta si falta).

Verificación en 10 segundos (no toca torch, no descarga nada):

```powershell
C:\...\image-edit\imgops.cmd selftest --only info mask transform lock
# esperado: {"passed": 4, "total": 4, "ok": true}
```

De aquí en adelante, `IMGOPS` = la ruta completa a `imgops.cmd`.
El shim apunta duro al `.venv` del repo: **nunca invoques otro `python`**.

## 1. Uso mínimo (3 comandos)

Trabaja **desde el cwd de tu proyecto**: el sandbox permite leer/escribir
bajo el directorio actual sin configuración extra. Las salidas van a `out/`
al lado del input, con sufijo; el input jamás se toca.

```powershell
Set-Location "C:\ruta\a\mi-proyecto"

# 1) Qué tengo (29 ms, sin torch):
C:\...\image-edit\imgops.cmd info assets\foto.png
# {"width": 854, "height": 536, "format": "PNG", "mode": "RGBA",
#  "has_alpha": true, "bytes": 270038, "sha256": "8ea2e99e...", "ms": 29, "ok": true}

# 2) Máscara desde un rectángulo + preview para revisar con ojos (239 ms):
C:\...\image-edit\imgops.cmd mask assets\foto.png --boxes 315,215,225,100 --dilate 3
# {"mask": "...\out\foto-mask.png", "overlay": "...\out\foto-overlay.png",
#  "area_px": 24470, "coverage_pct": 5.35, "ms": 239, "ok": true}
# ABRÍ foto-overlay.png: el magenta es lo que se va a reemplazar.
# Si cubre de más o de menos, ajusta boxes/dilate y repite (es gratis).

# 3) Inpaint (~18-26 s en CPU, paga solo aquí):
C:\...\image-edit\imgops.cmd inpaint assets\foto.png assets\out\foto-mask.png
# {"output": "...\out\foto-inpainted.png", "method": "lama-big",
#  "composited": true, "unpadded_from": [856, 536], "ms": 26437, "ok": true}
```

Notas del output real de arriba:

- `unpadded_from: [856, 536]` — LaMa rellena a múltiplo de 8 y `imgops`
  recorta a las dims del input. La salida **siempre mide lo mismo que la entrada**.
- Garantía por construcción: fuera de la máscara, el output es **bit-idéntico**
  al input (medido en Fase 2: 100 % igual fuera, 93,2 % cambió dentro).
- ¿Duda antes de pagar los ~24 s? Agrega `--dry-run`: devuelve el plan
  (rutas, dims, modelo, threads) sin ejecutar.

## 2. Casos guiados

### Caso A — Quitar texto horneado de un screenshot (el caso R11)

Receta completa de adquisición en `README.md` § Receta. Aquí solo la limpieza:

```powershell
# a) Máscara por glifos, no por rectángulo blanco: ROI + umbral crema + dilate.
#    (Valores de partida para título crema sobre fondo; calibrar con overlay.)
C:\...\image-edit\imgops.cmd mask orbit.png --boxes 305,210,245,116 `
  --auto-threshold 185,255 --dilate 3
# b) Revisar out\orbit-overlay.png con ojos. Solo cuando el magenta cubre
#    letras + antialias y nada más:
C:\...\image-edit\imgops.cmd inpaint orbit.png out\orbit-mask.png --dry-run
C:\...\image-edit\imgops.cmd inpaint orbit.png out\orbit-mask.png
# c) Si el PNG trae alfa: inpaint convierte a RGB solo (el error clásico
#    `input 5ch vs 4ch` ya está manejado dentro).
# d) Upscale Lanczos DESPUÉS del inpaint, nunca antes:
C:\...\image-edit\imgops.cmd transform out\orbit-inpainted.png --resize 1440x900
```

Corrida real de referencia (Fase 2, `docs/FASE2.md`): 13.257 px de máscara
(2,9 %), 26,4 s, indistinguible de `r10-lama-orbit.png` a primera vista.

### Caso B — Redimensionar / convertir en lote

```powershell
# Un archivo:
C:\...\image-edit\imgops.cmd transform hero.png --crop 0,0,1440,900 --resize 1440x900 --format webp --quality 85
# Lote (PowerShell): recorre PNGs, deja -transformed.webp en out/ de cada uno.
Get-ChildItem assets\*.png | ForEach-Object {
  C:\...\image-edit\imgops.cmd transform $_.FullName --resize 1280x720 --format webp --quality 85
}
```

Orden fijo: crop → resize Lanczos → convert. `--quality` solo aplica a
jpg/webp (1-100). Sin `--format` se conserva la extensión del input.

### Caso C — Cuantificar un cambio (leer un float, no mirar 3 screenshots)

```powershell
C:\...\image-edit\imgops.cmd compare antes.png despues.png
# {"mean_abs_diff": 12.4, "pct_px_gt40": 3.1, "max_abs_diff": 210,
#  "side_by_side": "...\out\antes-vs-despues.png", "ok": true}
```

Regla: las dims deben coincidir o el comando aborta diciéndote ambas.
`mean_abs_diff` ≈ 0 + `%px>40` ≈ 0 = idénticas (útil para "¿cambió algo el render?").
El `side_by_side` es solo para el ojo humano cuando el número canta.

## 3. Desde una sesión opencode (para el agente)

- Invoca el shim por **ruta absoluta**, con el cwd del proyecto activo.
  Salida JSON por stdout → parseable; `ms` viene incluido.
- Exit codes: `0` ok · `1` selftest con fallos · `2` error de uso/sandbox
  (el JSON trae `{"ok": false, "error": "..."}`).
- Archivos **fuera del cwd** (otro repo, Temp): el sandbox los rechaza salvo
  allowlist. Exporta antes de invocar:
  ```powershell
  $env:IMAGE_EDIT_READ_ROOTS = "C:\ruta\externa"
  $env:IMAGE_EDIT_WRITE_ROOTS = "C:\ruta\externa"
  ```
  (separador `;` para varias; siempre absolutas).
- Prohibiciones del sandbox: UNC (`\\server\...`), `\\?\`, dispositivos
  (`NUL`, `CON`, `COM1`…), escribir sobre el input, borrar (no hay comando
  que borre, por diseño).
- **Antes de pagar inferencia**: `mask` + ojos al overlay, luego
  `inpaint --dry-run`, luego `inpaint` real.
- `IMGOPS_THREADS` (default 4) si la máquina va justa; medir antes de subir.
- Cada invocación se loguea sola en `logs/imgops-usage.jsonl` del repo
  (mide el gatillo MCP; no tocar ese archivo a mano).
- `imgops --help` y `imgops <cmd> --help` son la referencia de flags;
  este manual no la duplica.

## 4. Errores comunes (fix en 1 línea)

| Error | Causa | Fix |
|---|---|---|
| `lectura/escritura fuera de raices permitidas` | archivo fuera del cwd sin allowlist | `IMAGE_EDIT_READ/WRITE_ROOTS` o trabajar desde su carpeta |
| `UNC prohibida` / `nombre de dispositivo` | ruta `\\server`, `NUL`, etc. | usar ruta local normal |
| `modelo LaMa no encontrado` | falta el `.pt` | restaurarlo a `~/.cache/torch/hub/checkpoints/` (sin descarga implícita) |
| `hash del modelo distinto` | `.pt` corrupto o cambiado | re-descargar y verificar SHA de `docs/FASE0.md` |
| `mascara WxH no coincide con imagen` | máscara de otra corrida | regenerar con `mask` (mismas dims) |
| `dimensiones distintas` en `compare` | A y B no miden igual | igualar con `transform --resize` primero |
| `mascara vacia` | boxes fuera de la imagen o umbral sin match | revisar overlay (saldrá sin magenta) |
| `WinError 5` instalando | OneDrive bloquea DLLs | pausar sync antes de `pip`/`selftest` (ver `README.md`) |
| primera corrida lenta | Defender + `import torch` frío | normal; excluir `.venv` y caché torch en Defender |

## 5. Mantenimiento y límites

- Trimestral (responsable: el usuario): `imgops selftest` → 5/5 PASS en ~25 s.
  Si pasa, no tocar nada.
- Límites duros: sin GPU (CPU), Windows, Python 3.10. No hay upscale neural,
  ni CRAFT, ni SDXL, ni MCP (llega solo con gatillo medible; ver `README.md`).
- Todo cambio de versiones pasa por `known-good.txt` + `requirements.lock.txt`
  (pins + hashes); el check `lock` del selftest lo vigila.
