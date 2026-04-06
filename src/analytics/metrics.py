from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List

import pandas as pd


@dataclass
class TradeRecord:
    """
    Registro simplificado de un trade cerrado.
    """
    entry_timestamp: object
    exit_timestamp: object
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    return_pct: float
    exit_reason: str


@dataclass
class BacktestMetrics:
    """
    Métricas principales del backtest.
    """
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_pnl: float
    expectancy: float
    total_pnl: float
    initial_cash: float
    final_equity: float
    max_drawdown_pct: float

    def to_dict(self) -> dict:
        return asdict(self)


def trades_to_dataframe(trades: List[TradeRecord]) -> pd.DataFrame:
    """
    Convierte la lista de trades en DataFrame.
    """
    if not trades:
        return pd.DataFrame(
            columns=[
                "entry_timestamp",
                "exit_timestamp",
                "side",
                "entry_price",
                "exit_price",
                "quantity",
                "pnl",
                "return_pct",
                "exit_reason",
            ]
        )

    return pd.DataFrame([asdict(trade) for trade in trades])


def compute_equity_curve(trades_df: pd.DataFrame, initial_cash: float) -> pd.DataFrame:
    """
    Construye una equity curve acumulando PnL por trade cerrado.
    """
    if trades_df.empty:
        return pd.DataFrame(
            {
                "trade_number": [],
                "pnl": [],
                "equity": [],
                "rolling_peak": [],
                "drawdown_pct": [],
            }
        )

    equity = initial_cash + trades_df["pnl"].cumsum()
    rolling_peak = equity.cummax()
    drawdown_pct = (equity / rolling_peak) - 1.0

    return pd.DataFrame(
        {
            "trade_number": range(1, len(trades_df) + 1),
            "pnl": trades_df["pnl"].values,
            "equity": equity.values,
            "rolling_peak": rolling_peak.values,
            "drawdown_pct": drawdown_pct.values,
        }
    )


def compute_backtest_metrics(trades: List[TradeRecord], initial_cash: float) -> BacktestMetrics:
    """
    Calcula métricas básicas a partir de trades cerrados.
    """
    trades_df = trades_to_dataframe(trades)

    if trades_df.empty:
        return BacktestMetrics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            avg_pnl=0.0,
            expectancy=0.0,
            total_pnl=0.0,
            initial_cash=initial_cash,
            final_equity=initial_cash,
            max_drawdown_pct=0.0,
        )

    total_trades = len(trades_df)
    winning_trades = int((trades_df["pnl"] > 0).sum())
    losing_trades = int((trades_df["pnl"] <= 0).sum())
    win_rate = winning_trades / total_trades
    avg_pnl = float(trades_df["pnl"].mean())
    expectancy = avg_pnl
    total_pnl = float(trades_df["pnl"].sum())

    equity_curve = compute_equity_curve(trades_df, initial_cash)
    final_equity = float(equity_curve["equity"].iloc[-1]) if not equity_curve.empty else initial_cash
    max_drawdown_pct = float(equity_curve["drawdown_pct"].min()) if not equity_curve.empty else 0.0

    return BacktestMetrics(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate,
        avg_pnl=avg_pnl,
        expectancy=expectancy,
        total_pnl=total_pnl,
        initial_cash=initial_cash,
        final_equity=final_equity,
        max_drawdown_pct=max_drawdown_pct,
    )