#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTMLファイルをRAG用のJSONに変換するスクリプト
Google Colab環境での実行を想定
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse
import subprocess
import sys

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_requirements():
    """必要なライブラリをインストール"""
    packages = [
        'beautifulsoup4',
        'lxml',
        'requests',
        'langchain',
        'langchain-text-splitters'
    ]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            logger.info(f"Successfully installed {package}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install {package}: {e}")

def install_pandoc():
    """Pandocをインストール"""
    try:
        # Pandocがすでにインストールされているかチェック
        subprocess.run(['pandoc', '--version'], check=True, capture_output=True)
        logger.info("Pandoc is already installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.info("Installing Pandoc...")
        try:
            subprocess.check_call(['apt-get', 'update'])
            subprocess.check_call(['apt-get', 'install', '-y', 'pandoc'])
            logger.info("Successfully installed Pandoc")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Pandoc: {e}")
            logger.info("Trying alternative installation method...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pypandoc'])

# ライブラリインストール
install_requirements()
install_pandoc()

# インポート
from bs4 import BeautifulSoup
from langchain.text_splitter import MarkdownHeaderTextSplitter
import pypandoc

class HTMLToJSONConverter:
    """HTMLファイルをRAG用のJSONに変換するクラス"""
    
    def __init__(self, input_dir: str, output_dir: str, noise_pattern_file: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.noise_pattern_file = Path(noise_pattern_file)
        self.noise_patterns = self._load_noise_patterns()
        
        # 出力ディレクトリを作成
        self.output_dir.mkdir(exist_ok=True)
        
    def _load_noise_patterns(self) -> List[str]:
        """ノイズパターンファイルを読み込み"""
        patterns = []
        if self.noise_pattern_file.exists():
            try:
                with open(self.noise_pattern_file, 'r', encoding='utf-8') as f:
                    patterns = [line.strip() for line in f if line.strip()]
                logger.info(f"Loaded {len(patterns)} noise patterns")
            except Exception as e:
                logger.warning(f"Failed to load noise patterns: {e}")
        else:
            logger.warning(f"Noise pattern file not found: {self.noise_pattern_file}")
        return patterns
    
    def extract_page_url(self, html_content: str) -> str:
        """HTMLコンテンツからページURLを抽出"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # canonical URLを探す
        canonical = soup.find('link', rel='canonical')
        if canonical and canonical.get('href'):
            return canonical['href']
        
        # og:urlを探す
        og_url = soup.find('meta', property='og:url')
        if og_url and og_url.get('content'):
            return og_url['content']
        
        # ページ内のリンクから推測（最初のhttp(s)リンク）
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http'):
                parsed = urlparse(href)
                return f"{parsed.scheme}://{parsed.netloc}"
        
        return ""
    
    def remove_common_noise(self, soup: BeautifulSoup) -> BeautifulSoup:
        """共通ノイズ（script、styleなど）を除去"""
        # 削除対象のタグ
        noise_tags = ['script', 'style', 'noscript', 'iframe', 'object', 'embed']
        
        for tag in noise_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        # コメントを削除
        from bs4 import Comment
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        logger.info("Removed common noise elements")
        return soup
    
    def remove_pattern_noise(self, html_content: str) -> str:
        """個別ノイズパターンを除去"""
        for pattern in self.noise_patterns:
            try:
                html_content = re.sub(pattern, '', html_content, flags=re.MULTILINE | re.DOTALL)
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")
        
        if self.noise_patterns:
            logger.info(f"Applied {len(self.noise_patterns)} noise patterns")
        
        return html_content
    
    def html_to_markdown(self, html_content: str) -> str:
        """HTMLをMarkdownに変換（Pandoc使用）"""
        try:
            # Pandocを使用してHTML→Markdown変換
            markdown = pypandoc.convert_text(
                html_content, 
                'commonmark',  # CommonMark準拠
                format='html',
                extra_args=['--wrap=none']  # 行の自動折り返しを無効
            )
            logger.info("Successfully converted HTML to Markdown")
            return markdown
        except Exception as e:
            logger.error(f"Failed to convert HTML to Markdown: {e}")
            # フォールバック: 簡単なHTML→Markdownコンバータ
            return self._simple_html_to_markdown(html_content)
    
    def _simple_html_to_markdown(self, html_content: str) -> str:
        """簡単なHTML→Markdown変換（フォールバック）"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 見出しの変換
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                heading.string = f"{'#' * i} {heading.get_text()}\n\n"
        
        # パラグラフの変換
        for p in soup.find_all('p'):
            p.string = f"{p.get_text()}\n\n"
        
        # リストの変換
        for ul in soup.find_all('ul'):
            for li in ul.find_all('li'):
                li.string = f"- {li.get_text()}\n"
            ul.string = f"{ul.get_text()}\n"
        
        for ol in soup.find_all('ol'):
            for i, li in enumerate(ol.find_all('li'), 1):
                li.string = f"{i}. {li.get_text()}\n"
            ol.string = f"{ol.get_text()}\n"
        
        return soup.get_text()
    
    def markdown_to_json(self, markdown_content: str, url: str, filename: str) -> List[Dict[str, Any]]:
        """Markdownを見出しごとに分割してJSONに変換"""
        # Markdownヘッダーで分割
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
            ("#####", "Header 5"),
            ("######", "Header 6"),
        ]
        
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False
        )
        
        try:
            docs = markdown_splitter.split_text(markdown_content)
            logger.info(f"Split markdown into {len(docs)} sections")
        except Exception as e:
            logger.warning(f"Failed to split markdown with headers: {e}")
            # フォールバック: 単一のドキュメントとして扱う
            from langchain.schema import Document
            docs = [Document(page_content=markdown_content, metadata={})]
        
        # JSON形式に変換
        json_docs = []
        for i, doc in enumerate(docs):
            json_doc = {
                "id": f"{filename}_{i}",
                "content": doc.page_content.strip(),
                "metadata": {
                    "source": filename,
                    "url": url,
                    "section_id": i,
                    **doc.metadata
                }
            }
            json_docs.append(json_doc)
        
        return json_docs
    
    def process_html_file(self, html_file: Path) -> List[Dict[str, Any]]:
        """単一のHTMLファイルを処理"""
        logger.info(f"Processing {html_file.name}")
        
        try:
            # HTMLファイルを読み込み
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 1. ページURL抽出
            url = self.extract_page_url(html_content)
            logger.info(f"Extracted URL: {url}")
            
            # 2. 共通ノイズ除去
            soup = BeautifulSoup(html_content, 'html.parser')
            soup = self.remove_common_noise(soup)
            
            # 3. 個別ノイズ除去
            clean_html = self.remove_pattern_noise(str(soup))
            
            # 4. Markdown化
            markdown_content = self.html_to_markdown(clean_html)
            
            # 5. JSON化
            json_docs = self.markdown_to_json(markdown_content, url, html_file.stem)
            
            logger.info(f"Successfully processed {html_file.name} -> {len(json_docs)} documents")
            return json_docs
            
        except Exception as e:
            logger.error(f"Failed to process {html_file.name}: {e}")
            return []
    
    def convert_all(self):
        """inputディレクトリ内のすべてのHTMLファイルを変換"""
        html_files = list(self.input_dir.glob('*.html')) + list(self.input_dir.glob('*.htm'))
        
        if not html_files:
            logger.warning(f"No HTML files found in {self.input_dir}")
            return
        
        logger.info(f"Found {len(html_files)} HTML files")
        
        all_documents = []
        
        for html_file in html_files:
            docs = self.process_html_file(html_file)
            all_documents.extend(docs)
        
        # 結果をJSONファイルに保存
        output_file = self.output_dir / 'converted_documents.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_documents, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(all_documents)} documents to {output_file}")
        
        # 統計情報を表示
        self._print_statistics(all_documents)
    
    def _print_statistics(self, documents: List[Dict[str, Any]]):
        """変換結果の統計情報を表示"""
        total_docs = len(documents)
        total_chars = sum(len(doc['content']) for doc in documents)
        sources = set(doc['metadata']['source'] for doc in documents)
        
        print(f"\n=== 変換結果統計 ===")
        print(f"総ドキュメント数: {total_docs}")
        print(f"総文字数: {total_chars:,}")
        print(f"処理ファイル数: {len(sources)}")
        print(f"平均文字数/ドキュメント: {total_chars // total_docs if total_docs > 0 else 0}")
        print("===================\n")

def main():
    """メイン関数"""
    # 設定
    input_dir = "input"
    output_dir = "output"
    noise_pattern_file = "noise_pattern.txt"
    
    # 変換器を作成して実行
    converter = HTMLToJSONConverter(input_dir, output_dir, noise_pattern_file)
    converter.convert_all()

if __name__ == "__main__":
    main()
