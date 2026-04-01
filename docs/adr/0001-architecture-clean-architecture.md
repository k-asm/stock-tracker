# ADR-0001: Clean Architecture の採用

## Status

Accepted

## Context

SBI証券CSVの読み込み・Yahoo Finance APIの呼び出し・ターミナル表示という3つの外部依存を持つCLIツールを構築するにあたり、アーキテクチャを選定する必要があった。

将来的にデータソース（証券会社CSVのフォーマット変更、別APIへの切り替え）や出力形式（Web UI追加など）が変わる可能性がある。

## Decision

Clean Architecture の4層構造を採用する。

```
Domain → Application → Infrastructure
                    → Presentation
```

- **Domain**: エンティティ・Value Objects・リポジトリ抽象（外部依存ゼロ）
- **Application**: ユースケース・DTO（Domainのみ依存）
- **Infrastructure**: SBI CSVパーサー・yfinanceアダプター・JSONキャッシュ
- **Presentation**: Click CLI・Richテーブル描画

依存の方向はすべて内側（Domain）へ向かう。`cli.py` がComposition Rootとして全依存をワイヤリングする。

## Consequences

- `HoldingsRepository` / `StockInfoRepository` の抽象インターフェースを介するため、データソースをモックに差し替えてユニットテストが書ける
- `FileCacheStockInfoRepository` はDecoratorパターンで `YfinanceStockInfoRepository` を包む形にでき、キャッシュの有無を呼び出し側が意識しない
- 単一CLIツールとしては構造がやや重いが、外部依存の多さを考えると層の分離は有効
