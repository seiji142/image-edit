# image-edit

Proyecto de edición de imágenes con comportamiento de agente personalizado (estructura adaptada desde `personalizar-comportamiento-01`).

Stack aún sin definir — ver `.ai/context.md` para placeholders.

## Estructura

```
├── .ai/                          # Configuración de comportamiento del agente
│   ├── system.md                 #   Rol, tono, estilo y estructura de respuestas
│   ├── rules.md                  #   Reglas obligatorias (código, git, seguridad, calidad)
│   ├── context.md                #   Stack técnico, dependencias, variables de entorno
│   ├── agents.md                 #   Agentes especialistas (frontend, backend, devops, etc.)
│   ├── commands.md               #   Comandos personalizados / herramientas MCP
│   └── MEMORY.md                 #   Memoria persistente (proyecto: image-edit)
│
├── opencode.json                 # Config principal de OpenCode (modelo, provider, instrucciones)
│
├── src/                          # Código fuente (esqueleto vacío)
│   ├── api/
│   ├── components/
│   ├── config/
│   ├── data/
│   ├── doc/
│   ├── services/
│   └── utils/
│
├── tests/                        # Tests (esqueleto vacío, sin datos)
│   ├── unit/
│   ├── integration/
│   ├── lib/
│   ├── scripts/
│   ├── questions/
│   ├── answers/
│   ├── fixtures/
│   └── example/
│
├── scripts/                      # Tooling (gh-publish.ps1)
├── docs/                         # Documentación y reportes
└── logs/                         # Logs (vacío)
```

## Cómo funciona

1. OpenCode carga los archivos `.ai/` como system prompt vía `opencode.json`.
2. El agente sigue las reglas de `rules.md` como **hard constraint inquebrantable**.
3. La suite de validación (a definir para este dominio) vivirá en `tests/`.

## Requisitos

- [OpenCode](https://opencode.ai) instalado
- Python 3.x (para scripts de validación)

## Uso

```bash
# Iniciar OpenCode con la configuración del proyecto
opencode

# Ejecutar suite completa (cuando se defina)
python run_all_tests.py
```

## Variables de entorno

Copiar `.env.example` a `.env` y completar.

## Licencia

MIT
