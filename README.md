# stock-tracker

SBI証券の保有証券一覧CSVを読み込み、Yahoo Finance から財務指標を取得してターミナルに一覧表示するCLIツール。

## 表示される指標

| 列 | 内容 |
|---|---|
| 銘柄コード / 銘柄名 | SBI証券CSVから取得 |
| 株数 / 取得単価 | SBI証券CSVから取得 |
| 現在値 / 評価損益 / 損益率 | Yahoo Finance の現在値で計算 |
| PER(実績) / PER(予想) | trailingPE / forwardPE |
| PBR | priceToBook |
| EV/EBITDA | enterpriseToEbitda |
| EPS / BPS | trailingEps / bookValue |
| 配当利回り | `.dividends` 履歴から自前計算（株式分割対応） |
| 配当性向 / ROE | payoutRatio / returnOnEquity |
| 営業利益率 / 純利益率 | operatingMargins / profitMargins |
| 流動比率 | currentRatio |
| 自己資本比率 | バランスシートから計算（純資産 ÷ 総資産） |
| 時価総額 | marketCap（億円） |
| 52週高値 / 安値 | fiftyTwoWeekHigh / Low |
| ベータ | beta |

## インストール

```bash
git clone https://github.com/k-asm/stock-tracker
cd stock-tracker
pip install -e .
```

## SBI証券からCSVをダウンロード

1. SBI証券にログイン
2. **口座管理** → **保有証券一覧**（または **ポートフォリオ**）を開く
3. ページ下部の **「CSV」ボタン**をクリックしてダウンロード

2種類のエクスポート形式（保有証券一覧・ポートフォリオ一覧）をどちらも自動判別して読み込める。

## 使い方

```bash
# 基本
stock-tracker ~/Downloads/保有証券一覧.csv

# キャッシュを無視して最新データを取得
stock-tracker --no-cache ~/Downloads/保有証券一覧.csv

# キャッシュの有効期間を変更（デフォルト: 15分）
stock-tracker --ttl 60 ~/Downloads/保有証券一覧.csv
```

取得データは `~/.cache/stock-tracker/` にJSON形式でキャッシュされる。

## 注意事項

- **現在値は前営業日終値の場合がある**（Yahoo Finance の更新タイミングによる）
- **配当利回りは参考値**。Yahoo Finance の日本株データは非公式であり、株式分割の調整が不完全な場合がある（→ [ADR-0003](docs/adr/0003-dividend-yield-calculation.md)）
- データがない項目は `-` で表示される
