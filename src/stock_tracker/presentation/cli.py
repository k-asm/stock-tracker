import sys
from pathlib import Path

import click
from rich.console import Console

from ..application.use_cases.analyze_portfolio import (
    AnalyzePortfolioRequest,
    AnalyzePortfolioUseCase,
)
from ..infrastructure.cache.file_cache_stock_info_repository import (
    FileCacheStockInfoRepository,
)
from ..infrastructure.csv.sbi_csv_reader import SbiCsvHoldingsRepository
from ..infrastructure.yfinance.yfinance_stock_info_repository import (
    YfinanceStockInfoRepository,
)
from .json_renderer import JsonRenderer
from .rich_table_renderer import RichTableRenderer

console = Console()


@click.command()
@click.argument("csv_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="キャッシュを無視して Yahoo Finance から再取得する。",
)
@click.option(
    "--ttl",
    default=15,
    show_default=True,
    metavar="MINUTES",
    help="キャッシュの有効期間（分）。",
)
@click.option(
    "--cache-dir",
    type=click.Path(file_okay=False),
    default=None,
    help="キャッシュファイルの保存先ディレクトリ"
    "（デフォルト: ~/.cache/stock-tracker）。",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="出力フォーマット。json を指定すると全指標を JSON で標準出力する。",
)
def main(
    csv_path: str,
    no_cache: bool,
    ttl: int,
    cache_dir: str | None,
    output_format: str,
) -> None:
    """
    SBI証券の保有証券一覧CSVを読み込み、財務指標を一覧表示します。

    \b
    CSV_PATH: SBI証券からエクスポートした保有証券一覧CSVのパス。

    \b
    使用例:
      stock-tracker portfolio.csv
      stock-tracker --no-cache portfolio.csv
      stock-tracker --ttl 60 portfolio.csv
    """
    # Composition Root: wire all dependencies here
    holdings_repo = SbiCsvHoldingsRepository()
    yfinance_repo = YfinanceStockInfoRepository()

    if no_cache:
        stock_info_repo = yfinance_repo
    else:
        cache_path = Path(cache_dir) if cache_dir else None
        stock_info_repo = FileCacheStockInfoRepository(
            inner=yfinance_repo,
            cache_dir=cache_path,
            ttl_minutes=ttl,
        )

    use_case = AnalyzePortfolioUseCase(
        holdings_repo=holdings_repo,
        stock_info_repo=stock_info_repo,
    )

    if output_format == "json":
        renderer = JsonRenderer()
    else:
        renderer = RichTableRenderer(console=console)

    with renderer.status(
        "[bold green]Yahoo Finance からデータを取得中...[/bold green]"
    ):
        try:
            rows = use_case.execute(AnalyzePortfolioRequest(source=csv_path))
        except FileNotFoundError as e:
            console.print(f"[red]エラー: {e}[/red]")
            sys.exit(1)
        except ValueError as e:
            console.print(f"[red]CSVの解析に失敗しました: {e}[/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]予期しないエラーが発生しました: {e}[/red]")
            sys.exit(1)

    renderer.render(rows)
