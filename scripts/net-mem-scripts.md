# net-mem スクリプト使い方ガイド

macOS 上でネットワーク累積転送量とメモリ使用量を取得する2つのスクリプト。

---

## ファイル一覧

| ファイル | 役割 |
|---|---|
| `net-mem-stat.sh` | ワンショット。1行出力して終了 |
| `net-mem-monitor.sh` | 常駐デーモン。ログローテーション付き |

---

## net-mem-stat.sh — ワンショット

### 使い方

```bash
# 権限付与（初回のみ）
chmod +x scripts/net-mem-stat.sh

# 実行
bash scripts/net-mem-stat.sh
```

### 出力例

```
2026-04-22 11:45:00 rx=1234567890 tx=987654321 mem_total_mb=16384.0 mem_used_mb=8192.3 mem_free_mb=4096.1 mem_compressed_mb=512.0
```

### フィールド説明

| フィールド | 内容 |
|---|---|
| `rx` | 全インターフェース合計受信バイト数（ lo0 除く） |
| `tx` | 全インターフェース合計送信バイト数（ lo0 除く） |
| `mem_total_mb` | 物理メモリ総量 (MB) |
| `mem_used_mb` | 使用中メモリ = active + inactive + wired + compressed (MB) |
| `mem_free_mb` | 空きメモリ = free + speculative (MB) |
| `mem_compressed_mb` | Compressor が圧縮中のメモリ (MB) |

### 使用例: cron で毎分1行を追記

```bash
* * * * * bash /path/to/scripts/net-mem-stat.sh >> /var/log/net-mem.log
```

---

## net-mem-monitor.sh — 常駐デーモン

### 使い方

```bash
# 権限付与（初回のみ）
chmod +x scripts/net-mem-monitor.sh

# デフォルト設定で起動（60秒間隔 / 60分ローテ / 24時間保持）
bash scripts/net-mem-monitor.sh

# 引数指定
bash scripts/net-mem-monitor.sh [LOG_DIR] [INTERVAL] [ROTATE_MINUTES] [KEEP_HOURS]
```

### 引数

| 引数 | デフォルト | 説明 |
|---|---|---|
| `LOG_DIR` | `$HOME/logs` | ログ出力ディレクトリ |
| `INTERVAL` | `60` | 計測間隔（秒） |
| `ROTATE_MINUTES` | `60` | ログローテーション間隔（分） |
| `KEEP_HOURS` | `24` | ログ保持時間（時間）。超えたファイルは自動削除 |

### 起動例

```bash
# バックグラウンドで起動
bash scripts/net-mem-monitor.sh ~/logs 60 60 24 &

# 10秒間隔・1分ローテ・1時間保持（検証用）
bash scripts/net-mem-monitor.sh ~/logs 10 1 1 &
```

### 停止方法

```bash
# PID ファイルを使って停止（推奨）
kill $(cat ~/logs/.monitor.pid)

# または Ctrl-C（フォアグラウンド起動時）
```

### ログファイル

```
~/logs/
  network_202604221100.log   # 11:00〜11:59 の計測データ
  network_202604221200.log   # 12:00〜12:59 の計測データ
  .monitor.pid               # 起動中の PID（停止時に自動削除）
```

ファイル名の数値部分は `YYYYMMDDHHMM` 形式で、`ROTATE_MINUTES` 境界に切り下げた時刻。  
例: `ROTATE_MINUTES=60` なら時間単位、`ROTATE_MINUTES=10` なら10分単位。

### ログ内容例

```
2026-04-22 11:00:00 rx=1234567890 tx=987654321 mem_total_mb=16384.0 mem_used_mb=8192.3 mem_free_mb=4096.1 mem_compressed_mb=512.0
2026-04-22 11:01:00 rx=1234580000 tx=987660000 mem_total_mb=16384.0 mem_used_mb=8210.5 mem_free_mb=4077.9 mem_compressed_mb=514.2
```

### 起動ログ例

```
[monitor] started — interval=60s rotate=60min keep=24h log=/Users/you/logs
```

---

## 動作環境

- macOS（`netstat -ibn` / `vm_stat` / `sysctl` を使用）
- Bash 3.2 以上
- Linux 非対応（`netstat -ibn` と `vm_stat` は macOS 専用）
