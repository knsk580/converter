# HTML to JSON Converter for RAG

業務システムのマニュアルやFAQが記載されているWebサイトのHTMLファイルを、AIチャットのRAG（Retrieval Augmented Generation）用のJSON形式に変換するツールです。

## 概要

このツールは、OpenAI APIのResponsesでfile_searchツールを使用してvector storeを参照するためのJSON形式データを生成します。

## 主な機能

1. **ページURL抽出**: HTMLファイルからcanonical URLやog:urlを自動抽出
2. **共通ノイズ除去**: script、styleタグなどの不要な要素を削除
3. **個別ノイズ除去**: `noise_pattern.txt`で指定した正規表現パターンによる除去
4. **Markdown化**: PandocによるCommonMark準拠のMarkdown変換
5. **JSON化**: LangchainのMarkdownHeaderTextSplitterによる見出し単位での分割とメタデータ付与

## 技術要件

- **実行環境**: Google Colab
- **言語**: Python 3.7+
- **主要ライブラリ**:
  - BeautifulSoup4 (HTMLパース)
  - Pandoc (HTML→Markdown変換)
  - Langchain (MarkdownHeaderTextSplitter)
  - その他: lxml, requests

## ファイル構成

```
converter/
├── html_to_json_converter.py    # メインの変換スクリプト
├── converter_demo.ipynb         # Google Colab用デモnotebook
├── noise_pattern.txt            # ノイズパターン設定ファイル
├── input/                       # HTMLファイル配置フォルダ
├── output/                      # 変換結果出力フォルダ
└── README.md                    # このファイル
```

## 使用方法

### 方法1: Google Colabでの実行（推奨）

1. `converter_demo.ipynb`をGoogle Colabで開く
2. セルを順番に実行して環境を準備
3. HTMLファイルをアップロード
4. 変換処理を実行
5. 結果をダウンロード

### 方法2: ローカル環境での実行

1. 必要なライブラリをインストール:
   ```bash
   pip install beautifulsoup4 lxml requests langchain langchain-text-splitters pypandoc
   ```

2. Pandocをインストール:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install pandoc
   
   # macOS
   brew install pandoc
   
   # Windows
   # https://pandoc.org/installing.html からダウンロード
   ```

3. HTMLファイルを`input/`フォルダに配置

4. 必要に応じて`noise_pattern.txt`を編集

5. 変換を実行:
   ```bash
   python html_to_json_converter.py
   ```

## 設定ファイル

### noise_pattern.txt

個別ノイズ除去用の正規表現パターンを行ごとに記述します。

```
# コメント行は#で始める
<div class="advertisement">.*?</div>
<footer>.*?</footer>
<nav[^>]*>.*?</nav>
```

## 出力形式

変換結果は`output/converted_documents.json`に保存されます。

```json
[
  {
    "id": "filename_0",
    "content": "Markdownで変換されたコンテンツ",
    "metadata": {
      "source": "original_filename",
      "url": "https://example.com/page",
      "section_id": 0,
      "Header 1": "見出しの内容",
      "Header 2": "サブ見出しの内容"
    }
  }
]
```

### メタデータの説明

- `source`: 元のHTMLファイル名
- `url`: 抽出されたページURL
- `section_id`: ドキュメント内のセクション番号
- `Header N`: Markdownの見出しレベルごとの内容

## PowerShell操作例

```powershell
# ディレクトリ作成
New-Item -ItemType Directory -Path "input", "output" -Force

# HTMLファイルの確認
Get-ChildItem -Path "input" -Filter "*.html"

# 変換実行
python html_to_json_converter.py

# 結果確認
Get-Content "output/converted_documents.json" | ConvertFrom-Json | Select-Object -First 1
```

## トラブルシューティング

### Pandocのインストールエラー

```python
# フォールバック機能があるため、Pandocなしでも動作します
# ただし、より良い変換品質のためPandocの使用を推奨
```

### 文字化け問題

```python
# HTMLファイルのエンコーディングを確認
with open('input/file.html', 'r', encoding='utf-8') as f:
    content = f.read()
```

### メモリ不足

```python
# 大量のファイルを処理する場合は、分割処理を検討
# または、Google Colab Proの使用を推奨
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能要望は、GitHubのIssueでお願いします。

## 更新履歴

- v1.0.0: 初回リリース
  - HTML→JSON変換機能
  - Google Colab対応
  - CommonMark準拠
  - LangchainによるMarkdown分割
