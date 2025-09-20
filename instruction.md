# 依頼
ある業務システムのマニュアルやFAQが記載されているWebサイトのHTMLファイルが、inputフォルダの中に複数あります。
これらのHTMLファイルを参照して、AIチャットがRAGとして使うためのJSON形式のテキストファイルを作成し、outputフォルダに保存して下さい

## 依頼補足
AIチャットでは、OpenAI APIのResponsesを使い、toolとしてfile_searchを使います。file_searchはvector storeを参照します。

## 技術的な制約
- Pythonを使ってください
- 実行環境は、Google Colabです
- Markdownは、Commonmarkに準拠してください

## HTMLからJSONまでの処理の流れ
1. ページURL抽出：サイト上でのURLが含まれているので、抽出する
2. 共通ノイズ除去：scriptやstyleなど不要な部分を削除する
3. 個別ノイズ除去：noise_pattern.txtを参照して指定されたノイズパターンを削除する
4. Markdown化：Markdown形式にする
5. JSON化：見出しをメタデータとして追加しながらJSON化する

### 各処理で使ってほしいツールや提案
2. BeautifulSoupなどを使う
4. Pandocを使う
5. LangchainのMarkdownHeaderTextSplitterを使う

### 処理の補足
noise_pattern.txtは、改行区切りで、正規表現のパターンが記載されている
