# Punto de entrada para correr un experimento desde config y guardar 
# resultados, porque quieres un laboratorio y no un script suelto.

# src/experiments/run_backtest.py

from __future__ import annotations

import pandas as pd
import yfinance as yf

from src.analytics.metrics import compute_backtest_metrics, compute_equity_curve, trades_to_dataframe
from src.core.event_queue import EventQueue
from src.core.runner import BacktestRunner
from src.data.loader import HistoricalCSVDataHandler
from src.execution.simulator import SimulatedExecutionHandler
from src.portfolio.portfolio import Portfolio
from src.strategies.MARK_II import Mark2Strategy

def generate_synthetic_ohlc_data(seed: int = 42) -> pd.DataFrame:
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(seed)
    dates = pd.date_range(start="2015-01-01", end="2024-12-31", freq="D")
    n = len(dates)

    returns = rng.normal(0, 0.0025, n)
    trend = np.sin(np.linspace(0, 12 * np.pi, n)) * 0.0005
    close = 1.10 + np.cumsum(returns + trend)

    open_ = np.roll(close, 1)
    open_[0] = close[0]

    spread = np.abs(rng.normal(0.002, 0.001, n))
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread

    data = pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
        },
        index=dates,
    )

    return data

def load_eurusd_data(use_synthetic_fallback: bool = False) -> pd.DataFrame:
    """
    Carga el dataset baseline de EUR/USD.

    Comportamiento:
    - Intenta descargar datos históricos con yfinance.
    - Si falla y use_synthetic_fallback=True, genera datos sintéticos reproducibles.
    - Si falla y use_synthetic_fallback=False, lanza un error claro.
    """
    try:
        data = yf.download("EURUSD=X", start="2015-01-01", end="2024-12-31", progress=False)

        if data is None or data.empty:
            raise ValueError("yfinance devolvió un DataFrame vacío.")

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data.dropna()
        data = data[["Open", "High", "Low", "Close"]]

        if data.empty:
            raise ValueError("El DataFrame quedó vacío después de limpiar columnas/nulos.")

        return data

    except Exception as e:
        if not use_synthetic_fallback:
            raise RuntimeError(
                "No se pudieron descargar datos de EURUSD con yfinance. "
                "Sugerencia: usa CSV local, cambia a una ruta sin acentos o activa el fallback sintético."
            ) from e

        print(f"[WARN] Falló descarga real. Usando datos sintéticos. Motivo: {e}")
        return generate_synthetic_ohlc_data()


    
def main() -> None:
    symbol = "EURUSD=X"
    initial_cash = 1000.0

    data = load_eurusd_data()

    event_queue = EventQueue()
    data_handler = HistoricalCSVDataHandler(data=data, symbol=symbol, event_queue=event_queue)
    strategy = Mark2Strategy(symbol=symbol)
    portfolio = Portfolio(
        symbol=symbol,
        initial_cash=initial_cash,
        fixed_quantity=1.0,
        stop_atr_multiple=1.0,
        take_profit_atr_multiple=2.0,
    )
    execution_handler = SimulatedExecutionHandler(
        slippage_per_unit=0.0,
        commission_per_order=0.0,
    )

    runner = BacktestRunner(
        data_handler=data_handler,
        strategy=strategy,
        portfolio=portfolio,
        execution_handler=execution_handler,
        event_queue=event_queue,
    )

    stats = runner.run()

    trades_df = trades_to_dataframe(portfolio.closed_trades)
    metrics = compute_backtest_metrics(portfolio.closed_trades, initial_cash=initial_cash)
    equity_curve_df = compute_equity_curve(trades_df, initial_cash=initial_cash)

    print("=== LOOP STATS ===")
    print(stats)

    print("\n=== BACKTEST METRICS ===")
    for key, value in metrics.to_dict().items():
        print(f"{key}: {value}")

    print("\n=== SAMPLE TRADES ===")
    print(trades_df.head())

    print("\n=== EQUITY CURVE SAMPLE ===")
    print(equity_curve_df.head())


if __name__ == "__main__":
    main()