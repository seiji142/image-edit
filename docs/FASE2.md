# Fase 2 — Validación contra Page-Transitions (2026-10-01)

Criterio fijado antes de mirar (PASOS.md Receta paso 8): sin letras residuales
ni manchas que canten a primera vista, a resolución de trabajo.

## Corrida

- Input: `Page-Transitions/assets/orbit.png` (854×536 RGBA → RGB interno;
  solo lectura, regla 13 intacta).
- Máscara: `review/lama-mask-title.png` ∪ `review/lama-mask-ui.png`
  (combinada con `maximum`, 13.257 px = 2,9 % cobertura).
- Comando: `imgops inpaint orbit.png mask-combined.png` (26,4 s, CPU).
- Salida: `Temp/opencode/fase2/orbit-imgops.png` (854×536, SHA256
  `4d0bba45…5995ed`). Artefactos conservados en ese dir (no se borra nada).

## Hallazgo: el misterio de los 856 px

`review/r10-lama-orbit.png` mide 856×536. No es un resize: `simple-lama`
rellena a múltiplo de 8 (abajo/derecha, simétrico) y devuelve con padding;
R11 conservó las 2 columnas extra. `imgops` recorta a dims del input
(`unpadded_from: [856, 536]` en el JSON) y garantiza salida = entrada.
Comportamiento superior y testeado (fixture 250×246 no múltiplo de 8).

## Veredicto: PASS ✅

- Invariante medido: fuera de máscara **bit-idéntico** al input; dentro 93,2 % cambió.
- Ojos: planeta/anillos/cielo continuos, sin letras, sin mancha central.
  Indistinguible de `r10-lama-orbit.png` a primera vista
  (salvo las 2 columnas de padding que R11 dejó y nosotros recortamos).

Con esto el paquete cumple A2. Lo que queda fuera de este repo: MCP (gatillo
en README), limpieza de `requirements.txt` huérfano, desinstalar
`simple-lama` del compartido.
