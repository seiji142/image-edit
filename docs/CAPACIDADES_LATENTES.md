# Capacidades latentes — inventario de la caja de herramientas (2026-10-01)

Pinzas que **están en la caja aunque todavía no se usen**. Estados verificados
contra el `.venv` (cv2 4.11.0); no estimados. Si cambia el lock,
re-verificar este inventario.

> Distinción que sostiene todo el documento: **detección ≠ reconocimiento**.
> *Detección* = dibujar cajas ("acá hay una cara"). *Reconocimiento* =
> decir quién es ("es Juan"). Son dos pinzas distintas: la primera es
> liviana y está; la segunda es pesada y no está.

## Detección (liviana — instalada, sin cablear)

| # | Capacidad | Estado | Dónde vive | Qué falta para usarla |
|---|---|---|---|---|
| 1 | Rostros frontales (cajas) | ✅ listo, frágil (solo frontal, sufre perfil/oclusión/luz) | `cv2.CascadeClassifier` + `haarcascade_frontalface_*.xml` en el `.venv` | solo código, ej. `mask --detect faces` (~1 h) |
| 2 | Rostros perfil / ojos / cuerpo parcial | ✅ listo, más frágil | mismos XMLs (`profileface`, `lefteye/righteye`, `upperbody`…) | solo código, con overlay de revisión obligatorio |
| 3 | Personas de cuerpo entero | ✅ listo | `cv2.HOGDescriptor` (no pide descargas) | solo código (~1 h) |

Nota: lo "frágil" no es opinión — Haar es 2001 y HOG es 2005; para screenshots
controlados alcanzan, para fotos salvajes fallan. Cualquier cableado debe
incluir overlay de revisión con ojos (misma disciplina que `mask`).

## Detección moderna (motor sí, pesos no)

| # | Capacidad | Estado | Qué falta |
|---|---|---|---|
| 4 | Objetos generales, ej. YOLO (80 clases) | ⚠️ `cv2.dnn` listo como motor | `onnxruntime` en el venv + pesos (~10-50 MB) + entrada al lock + cableado (medio día) |
| 5 | Texto en imagen (CRAFT, cajas) | ❌ nada instalado | modelo ~80 MB + cableado; ya es candidata v2 si el masking manual se vuelve cuello medido |

## Reconocimiento — decir quién es (pesada — nada instalado)

| # | Capacidad | Estado | Qué falta |
|---|---|---|---|
| 6 | Reconocimiento clásico (LBPH/Eigen) | ❌ `cv2.face` **no existe** en este venv (vive en `opencv-contrib-python`, no instalado) | cambio de paquete + galería de fotos etiquetadas + entrenamiento |
| 7 | Reconocimiento moderno (embeddings, ej. ArcFace) | ❌ nada | detector (fila 1 o YuNet) + modelo ~500 MB + **galería proveída por el usuario** + umbral de decisión + gestión de datos biométricos |

La fila 7 no es solo técnica: guardar embeddings de rostros es gestionar
biométricos (consentimiento, custodia, borrado). Todo corre en local, pero la
decisión se toma a conciencia y por escrito antes de implementarla. Por eso
YuNet —recomendado solo para **tapar** caras (detección → máscara → blur/inpaint,
sin guardar nada de nadie)— nunca fue ni será la vía de reconocimiento.

## Fuera del alcance del toolkit

Tracking en video, reconstrucción 3D, guiado/robótica: los algoritmos existen
en OpenCV, el código no, y no corresponden a un toolkit de imágenes fijas.
No cotizado.

## Mantenimiento de este inventario

- El `selftest` vigila **versiones** (`known-good.txt`), no capacidades:
  si el lock cambia (upgrade de opencv, agregado de `onnxruntime`, etc.),
  re-verificar las filas afectadas con `hasattr` + prueba de humo.
- Toda fila que pase a cableada se mueve a `MANUAL_USO.md` y se marca aquí
  como implementada (con fecha y commit).
