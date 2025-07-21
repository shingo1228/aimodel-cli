# AI Model CLI

CivitAIからAIモデルをダウンロード・管理するためのスタンドアロン コマンドライン ツール

[English](README.md) | **日本語**

## 概要

AI Model CLIは、CivitAIプラットフォームからStable Diffusion、LORA、その他のAIモデルを効率的に管理するためのコマンドライン ツールです。既存のモデル コレクションの管理と新規ダウンロードの両方に対応した包括的な機能を提供します。

## 特徴

- 🔍 **モデル検索**: コンテンツタイプ、ベースモデルなど高度なフィルターでCivitAIを検索
- 📥 **高速ダウンロード**: レジューム対応の高速HTTPダウンロード
- 📋 **モデル情報表示**: 詳細なモデル情報とメタデータの表示
- ⚙️ **設定管理**: インタラクティブなセットアップで簡単設定
- 🏷️ **メタデータ管理**: モデルメタデータとプレビュー画像の自動保存
- 🔄 **メタデータ補完**: SHA256ハッシュ識別による既存モデルファイルのメタデータ補完
- 📂 **スマート整理**: モデルタイプ別ダウンロードパス（Stable-diffusion、Lora、embeddingsなど）
- 🔐 **APIキー対応**: 制限付きモデルのダウンロード用個人APIキーサポート
- 🆕 **アップデート確認**: バージョン比較によるモデルアップデート確認
- 📊 **Markdownレポート**: プレビュー画像とCivitAIリンク付き詳細レポート生成
- ⚡ **パフォーマンス最適化**: SHA256ハッシュキャッシュによる高速処理

## インストール

### GitHubから

```bash
git clone https://github.com/shingo1228/aimodel-cli.git
cd aimodel-cli
pip install -e .
```

### 動作要件

- Python 3.8以降
- インターネット接続
- オプション: 制限付きダウンロード用のCivitAI個人APIキー

## クイックスタート

1. **初期セットアップ**
   ```bash
   aimodel setup
   ```

2. **モデル検索**
   ```bash
   aimodel search "リアルポートレート"
   aimodel search --type LORA --base-model "SD 1.5"
   ```

3. **モデルダウンロード**
   ```bash
   aimodel download 123456
   aimodel download 123456 --version 234567
   ```

4. **モデル情報表示**
   ```bash
   aimodel info 123456
   aimodel info ./model.safetensors --local
   ```

5. **不足メタデータの補完**
   ```bash
   aimodel metadata complete /path/to/models --recursive
   aimodel metadata complete --model-type LORA
   ```

6. **アップデート確認**
   ```bash
   aimodel update check --model-type LORA --report updates.md
   ```

## コマンド詳細

### 検索 (Search)

CivitAIでモデルを検索:

```bash
aimodel search [QUERY] [オプション]
```

**オプション:**
- `--type`: コンテンツタイプでフィルタ（Checkpoint、LORA等）
- `--base-model`: ベースモデルでフィルタ（SD 1.5、SDXL等）
- `--sort`: ソート順（Most Downloaded、Newest等）
- `--period`: 期間（All Time、Month、Week、Day）
- `--nsfw`: NSFW コンテンツを含める
- `--limit`: 結果数（デフォルト: 20）
- `--page`: ページ番号

**使用例:**
```bash
aimodel search "アニメスタイル"
aimodel search --type LORA --sort "Most Liked" --limit 10
aimodel search --base-model "SDXL 1.0" --nsfw
```

### ダウンロード (Download)

CivitAIからモデルをダウンロード:

```bash
aimodel download MODEL_ID [オプション]
```

**オプション:**
- `--version`: ダウンロードする特定バージョンID
- `--file`: ダウンロードする特定ファイルID
- `--path`: カスタムダウンロードディレクトリ
- `--show-versions`: 利用可能バージョンを表示
- `--show-files`: 利用可能ファイルを表示

**使用例:**
```bash
aimodel download 123456
aimodel download 123456 --version 234567
aimodel download 123456 --path ./my-models
aimodel download 123456 --show-versions
```

URLからのダウンロードも可能:
```bash
aimodel download-url "https://civitai.com/models/123456"
```

### モデル情報 (Model Information)

モデルの詳細情報を表示:

```bash
aimodel info TARGET [オプション]
```

**オプション:**
- `--local`: ターゲットをローカルファイルパスとして扱う

**使用例:**
```bash
aimodel info 123456
aimodel info "https://civitai.com/models/123456"
aimodel info ./model.safetensors --local
```

### メタデータ管理 (Metadata Management)

既存モデルの不足メタデータとプレビューファイルを補完:

```bash
aimodel metadata complete [PATH] [オプション]
```

**オプション:**
- `--model-type, -t`: 特定モデルタイプのパスを処理（Checkpoint、LORA等）
- `--recursive, -r / --no-recursive`: ファイルを再帰的に処理
- `--force, -f`: 既存メタデータファイルを上書き
- `--metadata-only`: メタデータのみダウンロード、プレビュー画像をスキップ
- `--preview-only`: プレビュー画像のみダウンロード、メタデータをスキップ

**使用例:**
```bash
# すべてのTextualInversionモデルを処理
aimodel metadata complete --model-type TextualInversion

# 特定ディレクトリを再帰的に処理
aimodel metadata complete /path/to/models --recursive

# 不足メタデータファイルのみ更新
aimodel metadata complete /path/to/models --metadata-only

# すべてのファイルを強制更新
aimodel metadata complete --model-type LORA --force
```

**SHA256ハッシュ計算:**
```bash
aimodel metadata hash /path/to/model.safetensors
```

### アップデート確認 (Update Checking)

モデルアップデートの確認とレポート生成:

```bash
aimodel update check [PATH] [オプション]
```

**オプション:**
- `--model-type, -t`: 特定モデルタイプのパスを確認（Checkpoint、LORA等）
- `--recursive, -r / --no-recursive`: ファイルを再帰的に処理
- `--download, -d`: 利用可能なアップデートを自動ダウンロード
- `--show-all`: アップデートなしを含むすべてのモデルを表示
- `--report PATH`: プレビュー画像付きMarkdownレポートファイルを生成
- `--report-include-current`: 最新モデルもレポートに含める

**使用例:**
```bash
# LORAモデルのアップデート確認
aimodel update check --model-type LORA

# 自動ダウンロード付き確認
aimodel update check --model-type Checkpoint --download

# 詳細レポート生成
aimodel update check --model-type LORA --report lora_updates.md --show-all

# 特定ディレクトリの確認
aimodel update check /path/to/models --recursive --report updates.md
```

**特定アップデートのダウンロード:**
```bash
aimodel update download /path/to/model.safetensors --version latest
```

### 設定管理 (Configuration)

CLI設定の管理:

```bash
aimodel config COMMAND [オプション]
```

**コマンド:**
- `list`: すべての設定を表示
- `get KEY`: 特定設定値を取得
- `set KEY VALUE`: 設定値を設定
- `reset`: デフォルトにリセット
- `path`: 設定ファイルの場所を表示
- `api-key [KEY]`: APIキーの設定または表示
- `download-path [PATH]`: デフォルトダウンロードパスの設定または表示
- `model-paths`: モデルタイプ別ダウンロードパスの一覧
- `model-path TYPE [PATH]`: 特定モデルタイプのパス設定または表示
- `metadata-recursive [true|false]`: メタデータコマンドのデフォルト再帰動作設定

**使用例:**
```bash
aimodel config list
aimodel config api-key
aimodel config set timeout 120
aimodel config download-path ./models

# モデルタイプ別パス
aimodel config model-paths
aimodel config model-path LORA /path/to/lora/models
aimodel config model-path Checkpoint  # 現在のパスを表示

# メタデータコマンドのデフォルト
aimodel config metadata-recursive true  # デフォルトで再帰処理を有効
```

## モデルタイプ別整理

CLIはモデルタイプに基づいてダウンロードを自動的にフォルダに整理します:

- **Checkpoint** → `Stable-diffusion/` フォルダ
- **LORA** → `Lora/` フォルダ
- **TextualInversion** → `embeddings/` フォルダ
- **Upscaler** → `ESRGAN/` フォルダ
- **Controlnet** → `ControlNet/` フォルダ
- その他のタイプは元の名前を使用

これらのパスはカスタマイズ可能です:
```bash
aimodel config model-path LORA /custom/lora/path
aimodel config model-path Checkpoint /custom/checkpoint/path
```

## 設定

CLIは設定を `~/.aimodel-cli/config.json` に保存します。主要な設定項目:

- `api_key`: CivitAI APIキー
- `default_download_path`: ダウンロードのデフォルトディレクトリ
- `model_paths`: モデルタイプ別ダウンロードパス
- `metadata_recursive_default`: メタデータコマンドのデフォルト再帰動作
- `timeout`: リクエストタイムアウト（秒）
- `show_nsfw`: デフォルトでNSFWコンテンツを含める
- `save_metadata`: モデルメタデータをJSONファイルに保存
- `save_preview`: プレビュー画像を保存

## APIキー

一部のモデル（特に早期アクセスや制限付きコンテンツ）をダウンロードするには、CivitAI個人APIキーが必要です:

1. https://civitai.com/user/account にアクセス
2. APIキーを生成
3. 次のコマンドで設定: `aimodel config api-key YOUR_KEY`

## ダウンロード動作

- モデルはモデルタイプ別フォルダに自動保存
- メタデータはモデルファイルと同じ場所にJSONファイルで保存
- プレビュー画像は自動ダウンロード
- SHA256ハッシュは計算され保存
- 中断されたダウンロードは再開可能
- 最適化されたパフォーマンスのHTTPダウンロード

## メタデータ補完

CLIは既存モデルファイルを分析してCivitAIから不足メタデータを取得できます:

1. **モデルタイプ別**: 特定タイプのすべてのモデルを処理
   ```bash
   aimodel metadata complete --model-type LORA
   ```

2. **ディレクトリ別**: ディレクトリ内のすべてのモデルを処理
   ```bash
   aimodel metadata complete /path/to/models --recursive
   ```

3. **個別ファイル**: 単一モデルファイルを処理
   ```bash
   aimodel metadata complete /path/to/model.safetensors
   ```

ツールはSHA256ハッシュを使用してCivitAI上のモデルを識別し、以下をダウンロードします:
- モデルメタデータ（名前、説明、タグ等）
- プレビュー画像
- バージョン情報

## アップデート確認

CLIはローカルモデルをCivitAI上の最新バージョンと比較してアップデートを確認できます:

- **バージョン検出**: SHA256ハッシュを使用してローカルモデルを識別
- **アップデート検出**: ローカルバージョンと最新利用可能バージョンを比較
- **一括処理**: ディレクトリ全体または特定モデルタイプを確認可能
- **リッチレポート**: プレビュー画像と直接CivitAIリンク付きMarkdownレポートを生成
- **自動ダウンロード**: オプションでアップデートを自動ダウンロード

## Markdownレポート

生成されるレポートには以下が含まれます:
- **モデル情報**: 名前、ID、現在/最新バージョン
- **プレビュー画像**: 読みやすさのためにリサイズされた画像（幅256px）
- **直接リンク**: CivitAIモデルページと特定バージョンへのクリック可能リンク
- **技術詳細**: ファイルサイズ、フォーマット、ダウンロード数
- **統計概要**: 確認済み総数、利用可能アップデート、最新モデル数

## ファイル構造

ダウンロードされたモデルは以下のファイルを作成します:
- `model.safetensors` - モデルファイル
- `model.json` - メタデータ（タグ、説明等）
- `model.preview.png` - プレビュー画像

## トラブルシューティング

### ダウンロード問題
- インターネット接続を確認
- 制限付きコンテンツをダウンロードする場合はAPIキーを確認
- CivitAIサーバーが混雑している場合は後で再試行

### メタデータ補完問題
- モデルファイルが有効（破損していない）ことを確認
- モデルがCivitAI上に存在するか確認
- SHA256ハッシュ計算が動作しているか確認

### アップデート確認問題
- モデルにメタデータファイルがあることを確認（先に `metadata complete` を実行）
- CivitAI APIへのインターネット接続を確認
- モデルがCivitAIプラットフォーム上に存在することを確認

### 権限エラー
- ダウンロードディレクトリが書き込み可能であることを確認
- 適切な権限で実行

### 設定問題
- 設定を確認: `aimodel config list`
- 必要に応じてリセット: `aimodel config reset`
- 設定場所を表示: `aimodel config path`

## パフォーマンス最適化

### SHA256ハッシュキャッシュ
- **初回計算**: SHA256ハッシュを計算してメタデータファイルに保存
- **2回目以降**: 保存されたハッシュを使用して即座に処理
- **効果**: 大きなモデルファイル（数GB）の処理時間が数分から数秒に短縮

### 使用例
```bash
# 初回（ハッシュ計算）
aimodel metadata hash model.safetensors
Calculating SHA256 hash...
SHA256: a1b2c3d4e5f6...

# 2回目以降（キャッシュ利用）
aimodel metadata hash model.safetensors
Using cached SHA256 hash...
SHA256: a1b2c3d4e5f6...
```

## 謝辞

このプロジェクトは、BlafKingによる[sd-civitai-browser-plus](https://github.com/BlafKing/sd-civitai-browser-plus)にインスパイアされました。このCLIツールは完全に異なるアプローチ（スタンドアロンCLI vs SD-WebUI拡張）を採用していますが、AIモデル管理コミュニティへの元プロジェクトの貢献に感謝いたします。

## ライセンス

このプロジェクトはMITライセンスの下でライセンスされています。詳細はLICENSEファイルをご覧ください。

## 貢献

貢献を歓迎します！問題やプルリクエストの提出をお気軽にどうぞ。

### 開発環境セットアップ

```bash
git clone https://github.com/shingo1228/aimodel-cli.git
cd aimodel-cli
pip install -r requirements-dev.txt
pip install -e .
```

### テスト実行

```bash
# 近日公開
pytest
```

## 免責事項

これは非公式ツールであり、CivitAIと提携していません。このツールを使用する際は、CivitAIの利用規約とレート制限を尊重してください。

---

**英語版ドキュメント**: [README.md](README.md)