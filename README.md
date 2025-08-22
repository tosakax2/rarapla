# RaRaPla

![CI](https://img.shields.io/github/actions/workflow/status/tosakax2/rarapla/ci.yml?label=CI&logo=github&logoColor=white)
![Python](https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green?logo=open-source-initiative&logoColor=white)

Windows 11 向けの軽量ラジオプレイヤー。Qt (PySide6) をフル活用したダークテーマ UI で、**radiko の現在地エリアで再生可能なチャンネル一覧**を表示し、選択した局を再生できます。加えて**Radio Browser**からのコミュニティ局も検索・再生に対応。内部では Radiko 向けの軽量プロキシが自動起動し、プレイリストを書き換えて Qt のプレイヤーが安定して再生できるよう補助します。

---

## 主な機能

- **radiko エリア検出 & 番組一覧**
  `https://api.radiko.jp/apparea/area` からエリア ID（例: `JP12`）を取得し、`v3/program/now/{area}.xml` で**放送中番組**とロゴをまとめて表示。詳細パネルでは番組情報（出演・説明・画像）を可能な限り取得して表示します。
- **Radio Browser 統合**
  日本の人気局やタグ（例: `jpop`, `jazz`, `vocaloid`）で検索し、直接ストリーム URL を再生。初回起動時に `rb_presets.json` を生成してプリセットを追加できます。
- **軽量 Radiko プロキシ**
  `http://127.0.0.1:3032`（埋まっていれば順次繰上げ）で待機し、`/live/{station}.m3u8` をローカルに変換・`/seg` 経由でセグメントをプロキシします。エラー時は自動リトライや解像を実施。
- **Qt Multimedia (FFmpeg) での再生**
  出力デバイス選択、音量スライダー、Play/Stop トグル対応。Nuitka ビルドでは Qt の multimedia プラグインを明示的に同梱しています

---

## 動作環境

- **OS**: Windows 11（動作保証）
  ※ macOS / Linux は PySide6/QtMultimedia が動く環境で実験的に動作する可能性があります。
- **Python**: 3.11
- **ランタイム依存関係**: `PySide6`, `qdarkstyle`, `aiohttp`, `requests`, `streamlink`（`pyproject.toml` 参照）

---

## クイックスタート（ソースから）

### 1. 仮想環境の作成と依存関係の導入（Windows）

```bat
setup_env.bat
```

（内部で venv 作成 → 有効化 → `pip install -e .` を実行）

### 2. 起動

```bash
rarapla
# もしくは
python -m rarapla
```

（エントリポイント `rarapla = "rarapla.__main__:main"`）

---

## 使い方

1. 画面右に**Channel**リスト、左に**Detail/Player**。
2. ソースを「radiko (area)」/「RB: プリセット」から選択。初回起動時、`rb_presets.json` が生成されます
3. 局カードを選ぶと詳細が「読み込み中…」に変わり、番組情報/画像が表示されます。
4. **Play** ボタンで再生/停止。**Output** で出力デバイスを切替。

> 注意: radiko の再生は地域制限の影響を受けます。

---

## Windows 用ビルド（Nuitka）

Windows で配布用の単体フォルダ（standalone）を作成します。

```bat
build.bat
```

- オプション例: `--standalone`, `--enable-plugin=pyside6`, `--include-qt-plugins=multimedia`, `--include-package=streamlink.*` などを使用し、`dist` 配下に成果物を出力します。
- 事前に `.venv` が必要です（`setup_env.bat` 参照）。

---

## 設定・ファイル

- **Radiko プロキシ**
  既定: `127.0.0.1:3032`。使用中なら次の空きポートに自動退避します。エンドポイントは以下の通りです。

  - `/live/{station}.m3u8` … master 再書き換え
  - `/seg` / `/seg.{ext}` … メディアセグメントのプロキシ
  - `/clear_cache` … 解決キャッシュのクリア
    （自動ポート選択とルーティング）

- **Radio Browser プリセット**
  実行ディレクトリに `rb_presets.json` が存在しない場合、起動時に生成されます。`label` / `mode`（`jp` or `tag`）/ `query` を編集してカスタマイズ可能。

---

## 開発ガイド

- **設計方針**
  個人開発でも拡張しやすい分割（`data/`, `proxy/`, `services/`, `ui/`）とシンプルなモデル（`Channel`, `Program`）。UI はカードリスト＋詳細＋プレイヤーを疎結合なコントローラで連携。
- **コーディング規約**

  - PEP 8 を基準に**88 桁**で整形（Black 推奨）。`flake8` と `mypy(strict)` を CI で実行
  - Python 3.11 の組込み型ヒント（`list[str]` など）を使用します。

- **テスト**
  `pytest -q`。プロキシの書き換えやポート選択などのユニットテストを含みます。CI（GitHub Actions）は lint & test を OS マトリクスで実行します。

### ディレクトリ構成（抜粋）

```plaintext
src/rarapla
├── app.py                 # アプリのエントリ・スタイル設定・プロキシ起動
├── config.py              # 定数設定（UA/ポート/UI寸法など）
├── data/                  # radiko / Radio Browser クライアント
├── proxy/                 # Radiko向け軽量プロキシ（aiohttp）
├── services/              # QMediaベースのプレイヤー、ICYメタ等
└── ui/                    # MainWindow, widgets, controllers, workers
```

---

## トラブルシュート

- **再生できない / 音が出ない**
  Qt Multimedia (FFmpeg) プラグインが必要です。Nuitka ビルドでは `--include-qt-plugins=multimedia` で同梱しています。
- **radiko が 404 や 403 になる**
  地域制限やセッションの期限切れが原因の場合、プロキシのキャッシュを自動的にクリアして再解決を試みます。

---

## ライセンス

MIT License。詳細は `LICENSE` を参照してください。

---

## 謝辞

- **radiko** の API/番組データ
- **Radio Browser** コミュニティ
- **Qt / PySide6** と関連ライブラリのコミュニティ
