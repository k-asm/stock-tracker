# CLAUDE.md

## プロジェクト概要

SBI証券の保有証券CSVと Yahoo Finance を組み合わせて国内株式の財務指標を一覧表示するPython CLIツール。

## アーキテクチャ

Clean Architecture 4層構造。依存の方向は必ず内側（Domain）へ。

```
src/stock_tracker/
├── domain/          # エンティティ・Value Objects・リポジトリ抽象（外部依存ゼロ）
├── application/     # ユースケース・DTO
├── infrastructure/  # SBI CSVパーサー・yfinanceアダプター・JSONキャッシュ
└── presentation/    # Click CLI（Composition Root）・Richテーブル
```

`presentation/cli.py` がComposition Rootとして全依存をワイヤリングする唯一の場所。

詳細は `docs/adr/` を参照。

## 開発

```bash
pip install -e ".[dev]"
pytest
```

## 重要な実装上の注意

### SBI証券CSVの2フォーマット

SBI証券のエクスポートには2種類ある（→ ADR-0002）。
- フォーマットA: `銘柄コード` 列が独立
- フォーマットB: `銘柄（コード）` 列に `"1414 ショーボンド"` 形式で銘柄名も含まれる

`SbiCsvHoldingsRepository._find_header_row()` がヘッダーをスキャンして自動判別する。新しいフォーマットが見つかった場合はここに追加する。

### 配当利回りの計算（要注意）

yfinance の `dividendYield` / `trailingAnnualDividendYield` は日本株に対して信頼性が低い（→ ADR-0003）。

現在の実装は `YfinanceStockInfoRepository._compute_dividend_yield()` で `.dividends` 履歴から自前計算している。

**株式分割ロジック**:
- 過去24ヶ月以内に分割あり かつ 分割後の配当実績あり → 分割後配当を年換算
- 過去24ヶ月以内に分割あり かつ 分割後の配当実績なし（分割直後）→ 12ヶ月ウィンドウにフォールバック（`.dividends` は調整済みのため）
- 分割なし → 過去12ヶ月の合計

異常値が出た場合はまず対象銘柄の `t.splits` と `t.dividends` を確認すること。

### キャッシュ

`FileCacheStockInfoRepository` が Decorator パターンで `YfinanceStockInfoRepository` を包む。TTLはデフォルト15分。開発中は `rm -rf ~/.cache/stock-tracker/` でクリアできる。

### Decimal の使用

金額・利回りの計算には必ず `Decimal` を使う。`float` への暗黙の変換が入っていないか注意。
