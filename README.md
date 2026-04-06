# Trading-Lab

Laboratorio personal de trading algorítmico orientado a eventos en Python.

Este proyecto nace como evolución de un notebook de investigación (`Capital_MVP_MARK_II.ipynb`) hacia una arquitectura más profesional, modular y reproducible. El objetivo es separar claramente datos, estrategia, portafolio, ejecución y métricas, para poder iterar estrategias, correr backtests y más adelante migrar a paper trading o live trading.

## Objetivos

- Migrar lógica de investigación desde notebooks a módulos reutilizables.
- Implementar una arquitectura event-driven para backtesting.
- Mantener un baseline fiel al `Mark II`.
- Poder comparar corridas con datos reales, CSV local o datos sintéticos.
- Crear una base sólida para futuras estrategias, gestión de riesgo y ejecución.

## Estado actual

Actualmente el proyecto ya puede:

- Ejecutar un backtest end-to-end.
- Procesar eventos de mercado, señales, órdenes y fills.
- Generar métricas básicas de desempeño.
- Correr con datos sintéticos reproducibles si falla la descarga remota.

## Estructura

```text
Trading-Lab/
├── src/
│   ├── __init__.py
│   ├── analytics/
│   │   ├── __init__.py
│   │   └── metrics.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── event_queue.py
│   │   ├── events.py
│   │   └── runner.py
│   ├── data/
│   │   ├── __init__.py
│   │   └── loader.py
│   ├── execution/
│   │   ├── __init__.py
│   │   └── simulator.py
│   ├── experiments/
│   │   ├── __init__.py
│   │   └── run_backtest.py
│   ├── portfolio/
│   │   ├── __init__.py
│   │   └── portfolio.py
│   └── strategies/
│       ├── __init__.py
│       ├── base.py
│       └── mark2.py
├── Capital_MVP_MARK_II.ipynb
├── requirements.txt
└── README.md
```

## Arquitectura

El motor sigue un flujo orientado a eventos:

1. El data handler emite `MarketEvent`.
2. La estrategia consume mercado y emite `SignalEvent`.
3. El portfolio transforma señales en `OrderEvent`.
4. El execution handler simula fills y emite `FillEvent`.
5. El portfolio actualiza estado, cash, posición y trades cerrados.

Este diseño busca desacoplar responsabilidades y acercar el proyecto a una base más escalable para investigación y producción.

## Requisitos

- Python 3.11+
- pip actualizado
- Entorno virtual recomendado

Dependencias actuales:

- pandas>=2.0.0
- yfinance>=0.2.0
- numpy>=1.24.0

## Instalación

Clona el repositorio:

```bash
git clone <URL_DEL_REPO>
cd Trading-Lab
```

Crea y activa un entorno virtual:

### Windows PowerShell

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

Instala dependencias:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Ejecución

Corre el backtest con:

```bash
python -m src.experiments.run_backtest
```

## Fuentes de datos

El proyecto está pensado para soportar tres modos de datos:

- `yfinance`: descarga remota de EUR/USD.
- `csv`: datos históricos locales.
- `synthetic`: datos sintéticos reproducibles para testing técnico.

### Nota importante sobre Windows

Si trabajas en Windows y tu ruta contiene acentos o caracteres especiales, puedes encontrar errores SSL/certificados al usar `yfinance`. En ese caso, se recomienda:

- mover el proyecto a una ruta simple, por ejemplo `C:\dev\trading-lab`
- recrear el entorno virtual en esa nueva ruta
- usar CSV local como baseline reproducible

## Estado del baseline Mark II

El baseline actual busca portar la lógica del notebook `Capital_MVP_MARK_II.ipynb`, incluyendo:

- tendencia con EMA21 / EMA55 / EMA100
- pullback dinámico con ATR
- confirmación por vela
- anti-repetición de señales
- stop loss y take profit basados en ATR

Todavía hay diferencias por cerrar entre el notebook y el motor modular, especialmente en:

- fuente exacta de datos
- reglas finas de ejecución
- horizonte de salida y prioridad intrabar

## Próximos pasos

- soporte estable para CSV local
- configuración externa vía YAML o JSON
- exportación de métricas y trades
- tests unitarios
- comparación automática contra baseline
- paper trading / live adapters

## Advertencia

Este proyecto es experimental y educativo. No constituye asesoría financiera ni un sistema listo para producción o trading real.

## Autor

Juan Andrés Cano R
