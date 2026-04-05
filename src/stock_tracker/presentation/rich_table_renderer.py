from collections.abc import Sequence
from decimal import Decimal

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from ..application.dtos.portfolio_row_dto import PortfolioRowDTO


def _fmt_decimal(value: Decimal | None, decimals: int = 2, suffix: str = "") -> Text:
    if value is None:
        return Text("-", style="dim")
    return Text(f"{value:,.{decimals}f}{suffix}")


def _fmt_money_jpy(value: Decimal | None) -> Text:
    if value is None:
        return Text("-", style="dim")
    return Text(f"¥{value:,.0f}")


def _fmt_market_cap(value: int | None) -> Text:
    if value is None:
        return Text("-", style="dim")
    oku = value / 100_000_000
    return Text(f"{oku:,.0f}億")


def _fmt_gain_loss(value: Decimal | None) -> Text:
    if value is None:
        return Text("-", style="dim")
    sign = "+" if value >= 0 else ""
    style = "green" if value >= 0 else "red"
    return Text(f"{sign}{value:,.0f}", style=style)


def _fmt_gain_loss_pct(value: Decimal | None) -> Text:
    if value is None:
        return Text("-", style="dim")
    sign = "+" if value >= 0 else ""
    style = "green" if value >= 0 else "red"
    return Text(f"{sign}{value:.2f}%", style=style)


class RichTableRenderer:
    """
    Renders PortfolioRowDTOs as a Rich formatted terminal table.
    Only depends on PortfolioRowDTO — no domain types cross this boundary.
    """

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or Console()

    def status(self, message: str):
        return self._console.status(message)

    def render(self, rows: Sequence[PortfolioRowDTO]) -> None:
        if not rows:
            self._console.print("[yellow]保有銘柄が見つかりませんでした。[/yellow]")
            return

        table = self._build_table(rows)
        self._console.print(table)
        self._print_summary(rows)

    def _build_table(self, rows: Sequence[PortfolioRowDTO]) -> Table:
        table = Table(
            title="[bold cyan]株式ポートフォリオ[/bold cyan]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
            border_style="bright_black",
        )

        table.add_column("コード", style="bold white", no_wrap=True)
        table.add_column("銘柄名", max_width=18)
        table.add_column("株数", justify="right")
        table.add_column("取得単価", justify="right")
        table.add_column("現在値", justify="right")
        table.add_column("評価損益", justify="right")
        table.add_column("損益率", justify="right")
        table.add_column("PER(実)", justify="right")
        table.add_column("PER(予)", justify="right")
        table.add_column("PBR", justify="right")
        table.add_column("EV/EBITDA", justify="right")
        table.add_column("EPS", justify="right")
        table.add_column("BPS", justify="right")
        table.add_column("配当利回", justify="right")
        table.add_column("配当性向", justify="right")
        table.add_column("ROE", justify="right")
        table.add_column("営業利益率", justify="right")
        table.add_column("純利益率", justify="right")
        table.add_column("流動比率", justify="right")
        table.add_column("自己資本比", justify="right")
        table.add_column("時価総額", justify="right")
        table.add_column("52W高値", justify="right")
        table.add_column("52W安値", justify="right")
        table.add_column("β", justify="right")

        for row in rows:
            table.add_row(
                row.ticker_symbol.replace(".T", ""),
                row.company_name,
                _fmt_decimal(row.shares, 0),
                _fmt_money_jpy(row.average_cost),
                _fmt_money_jpy(row.current_price),
                _fmt_gain_loss(row.gain_loss),
                _fmt_gain_loss_pct(row.gain_loss_pct),
                _fmt_decimal(row.trailing_pe),
                _fmt_decimal(row.forward_pe),
                _fmt_decimal(row.price_to_book),
                _fmt_decimal(row.enterprise_to_ebitda),
                _fmt_decimal(row.trailing_eps, 1),
                _fmt_decimal(row.book_value, 0),
                _fmt_decimal(row.dividend_yield_pct, 2, "%"),
                _fmt_decimal(row.payout_ratio_pct, 1, "%"),
                _fmt_decimal(row.return_on_equity_pct, 1, "%"),
                _fmt_decimal(row.operating_margins_pct, 1, "%"),
                _fmt_decimal(row.profit_margins_pct, 1, "%"),
                _fmt_decimal(row.current_ratio),
                _fmt_decimal(row.equity_ratio_pct, 1, "%"),
                _fmt_market_cap(row.market_cap),
                _fmt_money_jpy(row.fifty_two_week_high),
                _fmt_money_jpy(row.fifty_two_week_low),
                _fmt_decimal(row.beta),
            )

        return table

    def _print_summary(self, rows: Sequence[PortfolioRowDTO]) -> None:
        total_cost = sum(
            (r.total_cost for r in rows if r.total_cost is not None), Decimal(0)
        )
        total_value_items = [
            r.current_value for r in rows if r.current_value is not None
        ]
        total_value = sum(total_value_items, Decimal(0)) if total_value_items else None
        total_gain = total_value - total_cost if total_value is not None else None
        total_gain_pct = (
            total_gain / total_cost * Decimal("100")
            if total_gain is not None and total_cost != 0
            else None
        )

        self._console.print()
        self._console.print("[bold]ポートフォリオ合計[/bold]")
        self._console.print("  投資額合計  : ", _fmt_money_jpy(total_cost), sep="")
        if total_value is not None:
            self._console.print("  評価額合計  : ", _fmt_money_jpy(total_value), sep="")
        if total_gain is not None:
            self._console.print(
                "  評価損益合計: ",
                _fmt_gain_loss(total_gain),
                "  (",
                _fmt_gain_loss_pct(total_gain_pct),
                ")",
                sep="",
            )
        self._console.print(f"  銘柄数      : {len(rows)}銘柄")
        self._console.print()
        self._console.print("[dim]* 現在値は前営業日終値の場合があります[/dim]")
