#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
優先順位に基づくメールアドレス抽出スクリプト
1. トップページからの抽出（主にフッターに記載されているメールアドレス）
2. 会社概要やお問い合わせのページに移行し取得
3. info@~や会社名@~のドメインメールを生成
4. 生成したドメインメールに対し使われているか確認する
"""

import csv
import random
import time
import re
import json
import os
import sys
import logging
import requests
import urllib.parse
import dns.resolver
import socket
import smtplib
import traceback
import concurrent.futures
import warnings
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from urllib.parse import urljoin
from queue import PriorityQueue, Queue
from threading import Lock

# XMLパースエラーの警告を無効化
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# 動的メール抽出機能をインポート
try:
    from dynamic_email_extractor import DynamicEmailExtractor
    DYNAMIC_EXTRACTION_AVAILABLE = True
except ImportError:
    DYNAMIC_EXTRACTION_AVAILABLE = False
    logging.info("動的メール抽出機能は無効です（オプション機能）")

# ログ管理モジュールをインポート（一時的に無効化）
USE_LOG_MANAGER = False

# 従来のロギング設定を使用
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("prioritized_extraction.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('email_extractor')
logger.info("従来のロギング設定を使用します（ログ管理モジュールを一時的に無効化）")

# ユーザーエージェントのリスト
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
]

# 使い捨てメールドメインのリスト（一部）
DISPOSABLE_DOMAINS = {
    'mailinator.com', 'guerrillamail.com', 'temp-mail.org', 'disposablemail.com',
    'tempmail.com', '10minutemail.com', 'yopmail.com', 'mailnesia.com',
    'tempinbox.com', 'dispostable.com', 'sharklasers.com', 'grr.la',
    'guerrillamail.info', 'guerrillamail.biz', 'guerrillamail.de',
    'spam4.me', 'trashmail.com', 'mailcatch.com', 'anonbox.net',
    'getairmail.com', 'mailexpire.com', 'tempmailaddress.com',
    'fakeinbox.com', 'tempmailer.com', 'temp-mail.ru', 'throwawaymail.com'
}

# ロールベースメールプレフィックスのリスト
ROLE_BASED_PREFIXES = [
    'info', 'contact', 'inquiry', 'support', 'sales', 'webmaster', 'help',
    'office', 'mail', 'postmaster', 'hostmaster', 'abuse', 'noc', 'security',
    'marketing', 'hr', 'jobs', 'career', 'careers', 'recruit', 'recruitment',
    'service', 'services', 'feedback', 'no-reply', 'noreply',
    'no_reply', 'newsletter', 'press', 'media', 'billing', 'account', 'accounts'
]

class PrioritizedEmailExtractor:
    """優先順位に基づくメールアドレス抽出クラス"""

    def __init__(self, timeout=5, max_retries=1, use_dynamic_extraction=False, use_contact_form_analysis=False):
        self.timeout = timeout
        self.max_retries = max_retries
        self.disposable_domains = DISPOSABLE_DOMAINS
        self.role_based_prefixes = ROLE_BASED_PREFIXES
        self.visited_urls = set()

        # 入力例・プレースホルダーとして使用される一般的なドメイン
        self.example_domains = {
            'google.com', 'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'example.com', 'example.org', 'example.net', 'test.com', 'test.org',
            'sample.com', 'demo.com', 'placeholder.com', 'your-email.com',
            'yourdomain.com', 'yourcompany.com', 'company.com', 'domain.com',
            'mail.com', 'email.com', 'address.com'
        }

        # 入力例として使用される一般的なメールアドレス
        self.example_emails = {
            'info@google.com', 'test@example.com', 'sample@sample.com',
            'your-email@example.com', 'email@example.com', 'name@example.com',
            'user@example.com', 'contact@example.com', 'admin@example.com',
            'info@gmail.com', 'test@test.com', 'sample@demo.com'
        }

        # 動的メール抽出の設定
        self.use_dynamic_extraction = use_dynamic_extraction and DYNAMIC_EXTRACTION_AVAILABLE
        self.dynamic_extractor = None
        if self.use_dynamic_extraction:
            try:
                self.dynamic_extractor = DynamicEmailExtractor(timeout=timeout)
                logging.info("動的メール抽出機能を初期化しました")
            except Exception as e:
                logging.error(f"動的メール抽出機能の初期化に失敗しました: {e}")
                self.use_dynamic_extraction = False

        # 問い合わせフォーム解析の設定
        self.use_contact_form_analysis = use_contact_form_analysis
        self.contact_form_analyzer = None
        if self.use_contact_form_analysis:
            try:
                from contact_form_analyzer import ContactFormAnalyzer
                self.contact_form_analyzer = ContactFormAnalyzer(timeout=timeout, use_selenium=False)
                logging.info("問い合わせフォーム解析機能を初期化しました")
            except ImportError:
                logging.warning("問い合わせフォーム解析機能が利用できません（contact_form_analyzer.pyが見つかりません）")
                self.use_contact_form_analysis = False
            except Exception as e:
                logging.error(f"問い合わせフォーム解析機能の初期化に失敗しました: {e}")
                self.use_contact_form_analysis = False

    def get_random_user_agent(self):
        """ランダムなユーザーエージェントを返す"""
        return random.choice(USER_AGENTS)

    def is_valid_email_format(self, email):
        """
        メールアドレスの有効性をチェック（画像ファイル名等の除外を含む）

        Args:
            email (str): チェック対象のメールアドレス

        Returns:
            bool: 有効な場合True
        """
        if not email or not isinstance(email, str):
            return False

        email_str = email.strip()
        if not email_str:
            return False

        # 基本的なメールアドレス形式チェック
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email_str):
            return False

        # 長さチェック
        if len(email_str) > 254:  # RFC 5321の制限
            return False

        # ローカル部とドメイン部の分離
        try:
            local_part, domain_part = email_str.split('@')
            if len(local_part) > 64:  # RFC 5321の制限
                return False
        except ValueError:
            return False

        # 画像ファイル拡張子の除外チェック
        image_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp', '.ico',
            '.tiff', '.tif', '.avif', '.heic', '.heif'
        ]

        # CSS/JSファイル拡張子の除外チェック
        web_file_extensions = [
            '.css', '.js', '.woff', '.woff2', '.otf', '.ttf', '.eot',
            '.map', '.json', '.xml', '.html', '.htm'
        ]

        # レスポンシブ画像パターンの除外チェック（@2x.png, @3x.jpg等）
        responsive_patterns = [
            r'@\d+x\.(jpg|jpeg|png|gif|svg|webp|bmp|ico)$',
            r'@retina\.(jpg|jpeg|png|gif|svg|webp|bmp|ico)$',
            r'@mobile\.(jpg|jpeg|png|gif|svg|webp|bmp|ico)$',
            r'@tablet\.(jpg|jpeg|png|gif|svg|webp|bmp|ico)$'
        ]

        email_lower = email_str.lower()

        # 画像ファイル拡張子チェック
        for ext in image_extensions:
            if email_lower.endswith(ext):
                return False

        # CSS/JSファイル拡張子チェック
        for ext in web_file_extensions:
            if email_lower.endswith(ext):
                return False

        # レスポンシブ画像パターンチェック
        for pattern in responsive_patterns:
            if re.search(pattern, email_lower):
                return False

        # 一般的な無効パターンの除外
        invalid_patterns = [
            r'@\d+x\d+\.',  # @1080x360.jpg等のサイズ指定
            r'@sp\.',       # @sp.jpg等のスマートフォン用
            r'@pc\.',       # @pc.jpg等のPC用
            r'@mobile\.',   # @mobile.jpg等
            r'@tablet\.',   # @tablet.jpg等
            r'banner.*@.*\.(jpg|png|gif|svg)',  # バナー画像
            r'logo.*@.*\.(jpg|png|gif|svg)',    # ロゴ画像
            r'icon.*@.*\.(jpg|png|gif|svg)',    # アイコン画像
            r'hero.*@.*\.(jpg|png|gif|svg)',    # ヒーロー画像
            r'thumb.*@.*\.(jpg|png|gif|svg)',   # サムネイル画像
        ]

        for pattern in invalid_patterns:
            if re.search(pattern, email_lower):
                return False

        # JavaScript/CSS変数パターンの除外
        js_css_patterns = [
            r'window\.',
            r'\.prototype\.',
            r'\.version$',
            r'\.params$',
            r'\.config$',
            r'\.settings$',
            r'\.options$',
            r'@plugin\.',
            r'@custom\.',
            r'@retargeting\.',
            r'@datalayer\.',
            r'@large\.',
            r'@term\.',
            r'@jquery\.',
            r'^summary@',
            r'^search@',
            r'^my@',
            r'^gtm4wp@',
        ]

        # 特定の無効ドメインパターンの除外
        invalid_domain_patterns = [
            r'@.*\.image$',
            r'@.*\.string$',
            r'@.*\.easing$',
            r'@.*\.name$',
            r'@.*\.version$',
            r'@.*\.params$',
            r'@.*\.config$',
            r'@.*\.settings$',
        ]

        for pattern in js_css_patterns:
            if re.search(pattern, email_lower):
                return False

        # 無効ドメインパターンチェック
        for pattern in invalid_domain_patterns:
            if re.search(pattern, email_lower):
                return False

        return True

    def extract_domain_from_url(self, url):
        """URLからドメイン名を抽出する"""
        try:
            if not url or url == '-':
                return None

            # httpスキームを追加
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc

            # www.を削除
            if domain.startswith('www.'):
                domain = domain[4:]

            return domain
        except Exception as e:
            logging.error(f"ドメイン抽出エラー: {e}")
            return None

    def fetch_url(self, url, timeout=None, max_retries=None):
        """URLからコンテンツを取得（リトライ機能付き）"""
        if not url or url == '-':
            return None

        if timeout is None:
            timeout = self.timeout

        if max_retries is None:
            max_retries = self.max_retries

        # URLが http:// または https:// で始まっていない場合、https:// を追加
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # 既に訪問したURLはスキップ
        if url in self.visited_urls:
            logging.info(f"既に訪問済みのURL: {url}")
            return None

        self.visited_urls.add(url)

        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

        for attempt in range(max_retries + 1):
            try:
                response = requests.get(url, headers=headers, timeout=timeout)

                if response.status_code == 200:
                    return response
                elif response.status_code in [301, 302, 303, 307, 308] and 'Location' in response.headers:
                    redirect_url = urllib.parse.urljoin(url, response.headers['Location'])
                    if redirect_url != url:
                        logging.info(f"リダイレクト: {url} -> {redirect_url}")
                        return self.fetch_url(redirect_url, timeout, max_retries - attempt)
                else:
                    # 404エラーの場合はログレベルを下げる
                    if response.status_code == 404:
                        logging.debug(f"HTTPエラー: {response.status_code} - {url}")
                    else:
                        logging.warning(f"HTTPエラー: {response.status_code} - {url}")

                    if attempt < max_retries:
                        time.sleep(1 * (attempt + 1))  # 指数バックオフ
                        continue

                    return None
            except requests.exceptions.Timeout:
                logging.warning(f"タイムアウト: {url}")
                if attempt < max_retries:
                    time.sleep(1 * (attempt + 1))
                    continue
            except requests.exceptions.ConnectionError:
                logging.warning(f"接続エラー: {url}")
                if attempt < max_retries:
                    time.sleep(1 * (attempt + 1))
                    continue
            except Exception as e:
                logging.error(f"URL取得エラー ({url}): {e}")
                if attempt < max_retries:
                    time.sleep(1 * (attempt + 1))
                    continue

        return None

    def extract_emails_from_html(self, html, url=None):
        """HTMLからメールアドレスを抽出（パフォーマンス最適化版）"""
        if not html:
            return []

        # HTMLサイズ制限（1MB以上の場合は先頭部分のみ処理）
        max_html_size = 1024 * 1024  # 1MB
        if len(html) > max_html_size:
            logging.warning(f"HTMLサイズが大きすぎます（{len(html):,}文字）。先頭{max_html_size:,}文字のみ処理します。")
            html = html[:max_html_size]

        # 基本的なメールアドレスパターン
        basic_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

        # 拡張された難読化メールアドレスパターン
        obfuscated_patterns = [
            # [at] や (at) などの置換
            r'([a-zA-Z0-9._%+-]+)\s*[\[\(]at[\]\)]\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+)\s*@\s*([a-zA-Z0-9.-]+)\s*[\[\(]dot[\]\)]\s*([a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+)\s*@\s*([a-zA-Z0-9.-]+)\s*\.\s*([a-zA-Z]{2,})',
            # スペースや文字で分割されたメールアドレス
            r'([a-zA-Z0-9._%+-]+)\s+[@＠]\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+)[@＠]([a-zA-Z0-9.-]+)\s+\.\s+([a-zA-Z]{2,})',
            # 新規追加: より複雑な難読化パターン
            r'([a-zA-Z0-9._%+-]+)\s*\[アット\]\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+)\s*（アット）\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+)\s*\[ドット\]\s*([a-zA-Z0-9.-]+)\s*\[ドット\]\s*([a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+)\s*（ドット）\s*([a-zA-Z0-9.-]+)\s*（ドット）\s*([a-zA-Z]{2,})',
            # HTMLエンティティ
            r'([a-zA-Z0-9._%+-]+)\s*&#64;\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+)\s*&commat;\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            # 画像内テキストでよく見られるパターン
            r'([a-zA-Z0-9._%+-]+)\s*＠\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+)\s*@\s*([a-zA-Z0-9.-]+)\s*．\s*([a-zA-Z]{2,})',
            # 複数のスペースや改行を含むパターン
            r'([a-zA-Z0-9._%+-]+)\s*@\s*([a-zA-Z0-9.-]+)\s*\.\s*([a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+)\s+@\s+([a-zA-Z0-9.-]+)\s+\.\s+([a-zA-Z]{2,})',
            # 記号による難読化パターン（※、★、●、■など）
            r'([a-zA-Z0-9._%+-]+)\s*[※★●■▲▼◆◇○△▽☆]\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+)\s*[※★●■▲▼◆◇○△▽☆]\s*([a-zA-Z0-9.-]+)\s*[※★●■▲▼◆◇○△▽☆]\s*([a-zA-Z]{2,})',
            # 特殊文字による区切り
            r'([a-zA-Z0-9._%+-]+)\s*[＃＄％＆＊＋－＝]\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+)\s*[＃＄％＆＊＋－＝]\s*([a-zA-Z0-9.-]+)\s*[＃＄％＆＊＋－＝]\s*([a-zA-Z]{2,})',
            # アンダースコアやハイフンによる区切り
            r'([a-zA-Z0-9._%+-]+)\s*[_－―─]\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+)\s*[_－―─]\s*([a-zA-Z0-9.-]+)\s*[_－―─]\s*([a-zA-Z]{2,})'
        ]

        emails = []

        # 基本パターンでメールアドレスを抽出（Windows対応版）
        try:
            import platform
            import threading
            import time

            if platform.system() == "Windows":
                # Windows用のタイムアウト処理
                result_container = []
                exception_container = []

                def extract_with_timeout():
                    try:
                        basic_emails = re.findall(basic_pattern, html)
                        # 画像ファイル名の事前フィルタリング
                        filtered_emails = []
                        for email in basic_emails:
                            if self.is_valid_email_format(email):
                                filtered_emails.append(email)
                            else:
                                logging.debug(f"画像ファイル名等のため除外: {email}")
                        result_container.append(filtered_emails)
                    except Exception as e:
                        exception_container.append(e)

                thread = threading.Thread(target=extract_with_timeout)
                thread.daemon = True
                thread.start()
                thread.join(timeout=3)  # 3秒でタイムアウト

                if thread.is_alive():
                    logging.warning("基本パターンのメール抽出がタイムアウトしました（Windows）")
                elif exception_container:
                    raise exception_container[0]
                elif result_container:
                    emails.extend(result_container[0])
            else:
                # Unix系用のタイムアウト処理
                import signal

                def timeout_handler(signum, frame):
                    raise TimeoutError("基本パターン処理がタイムアウトしました")

                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(3)  # 3秒でタイムアウト

                try:
                    basic_emails = re.findall(basic_pattern, html)
                    # 画像ファイル名の事前フィルタリング
                    for email in basic_emails:
                        if self.is_valid_email_format(email):
                            emails.append(email)
                        else:
                            logging.debug(f"画像ファイル名等のため除外: {email}")
                finally:
                    signal.alarm(0)  # タイムアウト解除

        except TimeoutError:
            logging.warning("基本パターンのメール抽出がタイムアウトしました")
        except Exception as e:
            logging.warning(f"基本パターンのメール抽出中にエラー: {e}")

        # 難読化パターンを処理（Windows対応版）
        for pattern in obfuscated_patterns:
            try:
                import platform
                import threading

                if platform.system() == "Windows":
                    # Windows用のタイムアウト処理
                    result_container = []
                    exception_container = []

                    def extract_pattern_with_timeout():
                        try:
                            matches = re.findall(pattern, html)
                            for match in matches:
                                if isinstance(match, tuple):
                                    if len(match) == 2:
                                        # 記号による区切りパターン（※、★、●など）
                                        email = f"{match[0]}@{match[1]}"
                                        # 画像ファイル名の事前フィルタリング
                                        if self.is_valid_email_format(email):
                                            result_container.append(email)
                                            logging.info(f"記号区切りメールアドレスを抽出しました: {email}")
                                        else:
                                            logging.debug(f"画像ファイル名等のため除外: {email}")
                                    elif len(match) == 3:
                                        # ドット区切りパターン
                                        email = f"{match[0]}@{match[1]}.{match[2]}"
                                        # 画像ファイル名の事前フィルタリング
                                        if self.is_valid_email_format(email):
                                            result_container.append(email)
                                            logging.info(f"ドット区切りメールアドレスを抽出しました: {email}")
                                        else:
                                            logging.debug(f"画像ファイル名等のため除外: {email}")
                                else:
                                    # 単一マッチの場合
                                    email = str(match)
                                    # 画像ファイル名の事前フィルタリング
                                    if self.is_valid_email_format(email):
                                        result_container.append(email)
                                        logging.info(f"難読化メールアドレスを抽出しました: {email}")
                                    else:
                                        logging.debug(f"画像ファイル名等のため除外: {email}")
                        except Exception as e:
                            exception_container.append(e)

                    thread = threading.Thread(target=extract_pattern_with_timeout)
                    thread.daemon = True
                    thread.start()
                    thread.join(timeout=5)  # 5秒でタイムアウト

                    if thread.is_alive():
                        logging.warning(f"正規表現パターン処理がタイムアウトしました（Windows）: {pattern[:50]}...")
                        continue
                    elif exception_container:
                        raise exception_container[0]
                    else:
                        emails.extend(result_container)
                else:
                    # Unix系用のタイムアウト処理
                    import signal

                    def timeout_handler(signum, frame):
                        raise TimeoutError("正規表現処理がタイムアウトしました")

                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(5)  # 5秒でタイムアウト

                    try:
                        matches = re.findall(pattern, html)
                        for match in matches:
                            if isinstance(match, tuple):
                                if len(match) == 2:
                                    # 記号による区切りパターン（※、★、●など）
                                    email = f"{match[0]}@{match[1]}"
                                    # 画像ファイル名の事前フィルタリング
                                    if self.is_valid_email_format(email):
                                        emails.append(email)
                                        logging.info(f"記号区切りメールアドレスを抽出しました: {email}")
                                    else:
                                        logging.debug(f"画像ファイル名等のため除外: {email}")
                                elif len(match) == 3:
                                    # ドット区切りパターン
                                    email = f"{match[0]}@{match[1]}.{match[2]}"
                                    # 画像ファイル名の事前フィルタリング
                                    if self.is_valid_email_format(email):
                                        emails.append(email)
                                        logging.info(f"ドット区切りメールアドレスを抽出しました: {email}")
                                    else:
                                        logging.debug(f"画像ファイル名等のため除外: {email}")
                            else:
                                # 単一マッチの場合
                                email = str(match)
                                # 画像ファイル名の事前フィルタリング
                                if self.is_valid_email_format(email):
                                    emails.append(email)
                                    logging.info(f"難読化メールアドレスを抽出しました: {email}")
                                else:
                                    logging.debug(f"画像ファイル名等のため除外: {email}")
                    finally:
                        signal.alarm(0)  # タイムアウト解除

            except TimeoutError:
                logging.warning(f"正規表現パターン処理がタイムアウトしました: {pattern[:50]}...")
                continue
            except Exception as e:
                logging.warning(f"正規表現パターン処理中にエラー: {e}")
                continue

        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(html, 'html.parser')

        # mailto:リンクからメールアドレスを抽出（改善版）
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.lower().startswith('mailto:'):
                try:
                    # URLデコードを行う（%エンコードされた文字に対応）
                    decoded_href = urllib.parse.unquote(href)
                    email = decoded_href[7:].split('?')[0].strip()  # ?以降のパラメータを削除

                    # メールアドレスの検証
                    if email and '@' in email and self.is_valid_email_format(email) and self.verify_email_format(email):
                        logging.info(f"mailto:リンクからメールアドレスを抽出しました: {email}")
                        emails.append(email)
                    elif email and '@' in email:
                        logging.debug(f"画像ファイル名等のため除外: {email}")
                except Exception as e:
                    logging.warning(f"mailto:リンクの処理中にエラーが発生しました: {e}")
                    continue

        # 個人情報の取扱いについての欄からメールアドレスを抽出（新機能）
        privacy_emails = self.extract_emails_from_privacy_sections(soup, url)
        emails.extend(privacy_emails)

        # URLから企業ドメインを抽出（company_domainが指定されていない場合）
        company_domain = None
        if url:
            company_domain = self.extract_domain_from_url(url)

        # メールアドレスをクリーンアップ
        cleaned_emails = []
        for email in emails:
            # 余分な文字を削除
            email = email.strip().lower()
            email = re.sub(r'\s+', '', email)

            # 基本的な検証
            if re.match(basic_pattern, email) and self.is_valid_email_format(email):
                # 入力例・プレースホルダーフィルタリング
                if not self.is_example_email(email):
                    # 企業ドメインとの一致チェック（URLが提供されている場合）
                    if company_domain:
                        if self.verify_email_domain_match(email, company_domain):
                            cleaned_emails.append(email)
                        else:
                            logging.info(f"企業ドメイン({company_domain})と一致しないため除外: {email}")
                    else:
                        # URLが提供されていない場合はそのまま追加
                        cleaned_emails.append(email)
                else:
                    logging.info(f"入力例として除外されたメールアドレス: {email}")
            elif not self.is_valid_email_format(email):
                logging.debug(f"画像ファイル名等のため除外: {email}")

        # 重複を削除
        return list(set(cleaned_emails))

    def extract_emails_from_privacy_sections(self, soup, url=None):
        """個人情報の取扱いについての欄からメールアドレスを抽出"""
        emails = []

        # 個人情報関連のキーワード
        privacy_keywords = [
            '個人情報', 'プライバシー', 'privacy', '個人情報保護', '個人情報の取扱い',
            '個人情報保護管理者', '問合せ窓口', '連絡窓口', 'お問合せ窓口',
            'データ保護', '情報管理', '管理者', 'administrator', 'contact person',
            'Eメール', 'E-mail', 'email', 'メールアドレス', '連絡先'
        ]

        # 1. テキスト内容から個人情報関連セクションを検索
        for keyword in privacy_keywords:
            # キーワードを含むテキストノードを検索
            text_nodes = soup.find_all(string=re.compile(keyword, re.IGNORECASE))

            for text_node in text_nodes:
                if hasattr(text_node, 'parent'):
                    parent = text_node.parent

                    # 親要素とその周辺からメールアドレスを抽出
                    for level in range(5):  # 5階層上まで確認
                        if parent:
                            parent_text = parent.get_text()
                            parent_html = str(parent)

                            # 基本的なメールアドレスパターンで抽出
                            basic_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                            found_emails = re.findall(basic_pattern, parent_text)

                            for email in found_emails:
                                if self.is_valid_email_format(email) and self.verify_email_format(email):
                                    emails.append(email)
                                    logging.info(f"個人情報セクションからメールアドレスを抽出しました: {email}")
                                else:
                                    logging.debug(f"画像ファイル名等のため除外: {email}")

                            parent = parent.parent
                        else:
                            break

        # 2. 特定のHTMLクラス・IDから抽出
        privacy_selectors = [
            '.privacy', '.privacy-policy', '.personal-info', '.contact-info',
            '#privacy', '#privacy-policy', '#personal-info', '#contact-info',
            '[class*="privacy"]', '[class*="contact"]', '[id*="privacy"]', '[id*="contact"]',
            '.policy', '.terms', '.legal', '.compliance'
        ]

        for selector in privacy_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    element_text = element.get_text()

                    # 基本的なメールアドレスパターンで抽出
                    basic_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    found_emails = re.findall(basic_pattern, element_text)

                    for email in found_emails:
                        if self.is_valid_email_format(email) and self.verify_email_format(email):
                            emails.append(email)
                            logging.info(f"プライバシーセクション({selector})からメールアドレスを抽出しました: {email}")
                        else:
                            logging.debug(f"画像ファイル名等のため除外: {email}")
            except Exception as e:
                logging.debug(f"セレクタ {selector} の処理中にエラー: {e}")
                continue

        # 3. フォーム内の個人情報の取扱いについての記述から抽出
        forms = soup.find_all('form')
        for form in forms:
            form_text = form.get_text()

            # 個人情報関連のキーワードが含まれるフォームを対象
            if any(keyword in form_text for keyword in privacy_keywords):
                basic_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                found_emails = re.findall(basic_pattern, form_text)

                for email in found_emails:
                    if self.is_valid_email_format(email) and self.verify_email_format(email):
                        emails.append(email)
                        logging.info(f"フォーム内個人情報セクションからメールアドレスを抽出しました: {email}")
                    else:
                        logging.debug(f"画像ファイル名等のため除外: {email}")

        # 重複を削除
        return list(set(emails))

    def generate_enhanced_autoreply_patterns(self, domain, company_name='', url=''):
        """実例データに基づく強化された自動返信メールアドレスパターン生成"""
        patterns = []

        # 実例データから学習したパターン
        # 1. 企業名ベースのパターン（株式会社タイブレイク → tiebreak@tiebreak.co.jp）
        if company_name:
            # 企業名から英語部分を抽出
            company_english = self.extract_english_from_company_name(company_name)
            if company_english and company_english.lower() in domain.lower():
                patterns.append(f'{company_english.lower()}@{domain}')

        # 2. 一般的な自動返信パターン（実例順）
        common_patterns = [
            f'contact@{domain}',      # 株式会社フルネス実例
            f'info@{domain}',         # 最も一般的
            f'cs@{domain}',           # 株式会社マルホン実例（Customer Service）
            f'support@{domain}',      # サポート系
            f'inquiry@{domain}',      # お問い合わせ系
            f'mail@{domain}',         # シンプル系
            f'office@{domain}',       # オフィス系
            f'rep@{domain}',          # 代表系
            f'reply@{domain}',        # 返信系
        ]
        patterns.extend(common_patterns)

        # 3. ドメイン不一致パターン（株式会社マルホン実例：mokuzai.com → maruhon.com）
        if domain and '.' in domain:
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                # 企業名から推測される別ドメイン
                if company_name:
                    alt_domains = self.generate_alternative_domains(company_name, domain)
                    for alt_domain in alt_domains:
                        patterns.extend([
                            f'cs@{alt_domain}',
                            f'contact@{alt_domain}',
                            f'info@{alt_domain}',
                        ])

        # 4. 日本語企業特有のパターン
        if self.is_japanese_company(company_name):
            jp_patterns = [
                f'otoiawase@{domain}',    # お問い合わせ
                f'eigyo@{domain}',        # 営業
                f'soumu@{domain}',        # 総務
                f'jimu@{domain}',         # 事務
                f'uketsuke@{domain}',     # 受付
            ]
            patterns.extend(jp_patterns)

        return patterns

    def extract_english_from_company_name(self, company_name):
        """企業名から英語部分を抽出"""
        if not company_name:
            return ''

        # 英語部分を抽出（アルファベットのみ）
        import re
        english_parts = re.findall(r'[a-zA-Z]+', company_name)
        if english_parts:
            # 最も長い英語部分を返す
            return max(english_parts, key=len)
        return ''

    def generate_alternative_domains(self, company_name, current_domain):
        """企業名から代替ドメインを生成"""
        alt_domains = []

        if not company_name or not current_domain:
            return alt_domains

        # 企業名から英語部分を抽出
        english_part = self.extract_english_from_company_name(company_name)
        if english_part and len(english_part) > 3:
            # 現在のドメインの拡張子を取得
            domain_parts = current_domain.split('.')
            if len(domain_parts) >= 2:
                extension = '.'.join(domain_parts[1:])

                # 英語部分を使った代替ドメイン
                alt_domain = f'{english_part.lower()}.{extension}'
                if alt_domain != current_domain:
                    alt_domains.append(alt_domain)

        return alt_domains

    def is_japanese_company(self, company_name):
        """企業名が日本企業かどうかを判定"""
        if not company_name:
            return False

        # 日本語文字（ひらがな、カタカナ、漢字）が含まれているかチェック
        import re
        japanese_pattern = r'[ひらがなカタカナ漢字\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]'

        # 株式会社、有限会社などの日本企業の接頭辞・接尾辞
        japanese_company_patterns = [
            '株式会社', '有限会社', '合同会社', '合資会社', '合名会社',
            '一般社団法人', '公益社団法人', '一般財団法人', '公益財団法人',
            'Co.', 'Ltd.', 'Inc.', 'Corp.'
        ]

        # 日本語文字が含まれているか、日本企業の接頭辞・接尾辞が含まれているかチェック
        if re.search(japanese_pattern, company_name):
            return True

        for pattern in japanese_company_patterns:
            if pattern in company_name:
                return True

        return False

    def extract_contact_form_reply_emails(self, soup, url=None):
        """問い合わせフォームの自動返信設定からメールアドレスを抽出（実例データ強化版）"""
        emails = []

        try:
            # 1. フォームのaction属性やJavaScriptから送信先を推定
            forms = soup.find_all('form')
            for form in forms:
                # フォームのaction URLを解析
                action = form.get('action', '')
                if action:
                    # action URLから企業ドメインのメールアドレスを推定
                    if url:
                        domain = self.extract_domain_from_url(url)
                        company_name = getattr(self, 'current_company_name', '')

                        if domain:
                            # 実例データに基づく強化された自動返信メールアドレスパターン
                            reply_patterns = self.generate_enhanced_autoreply_patterns(domain, company_name, url)
                            emails.extend(reply_patterns)

            # 2. JavaScriptコード内の自動返信設定を検索
            scripts = soup.find_all('script')
            for script in scripts:
                script_content = script.string if script.string else ''

                # 自動返信関連のパターンを検索
                auto_reply_patterns = [
                    r'(?:auto[_-]?reply|noreply|no[_-]?reply|contact[_-]?reply).*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                    r'(?:from|sender|reply[_-]?to).*?["\']([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})["\']',
                    r'(?:email|mail)[_-]?(?:from|sender).*?["\']([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})["\']'
                ]

                for pattern in auto_reply_patterns:
                    matches = re.findall(pattern, script_content, re.IGNORECASE)
                    for match in matches:
                        if self.verify_email_format(match):
                            emails.append(match)
                            logging.info(f"JavaScriptから自動返信メールアドレスを抽出: {match}")

            # 3. フォーム周辺のテキストから自動返信の説明を検索
            form_texts = []
            for form in forms:
                # フォームの前後のテキストを取得
                parent = form.parent
                if parent:
                    form_texts.append(parent.get_text())

            for text in form_texts:
                # 自動返信に関する説明文からメールアドレスを抽出
                auto_reply_text_patterns = [
                    r'(?:自動返信|自動応答|確認メール|受付完了).*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                    r'(?:から|より).*?(?:メール|連絡).*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                    r'(?:reply|confirmation|auto).*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
                ]

                for pattern in auto_reply_text_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        if self.verify_email_format(match):
                            emails.append(match)
                            logging.info(f"フォーム説明文から自動返信メールアドレスを抽出: {match}")

        except Exception as e:
            logging.warning(f"問い合わせフォーム返信メール抽出中にエラー: {e}")

        # 重複を削除
        return list(set(emails))

    def is_example_email(self, email):
        """メールアドレスが入力例・プレースホルダーかどうかを判定"""
        if not email or '@' not in email:
            return False

        email = email.lower().strip()

        # 直接的な入力例メールアドレスのチェック
        if email in self.example_emails:
            return True

        # ドメイン部分をチェック
        try:
            local_part, domain = email.split('@', 1)

            # 入力例ドメインのチェック
            if domain in self.example_domains:
                return True

            # 一般的な入力例パターンのチェック
            example_patterns = [
                r'^(test|sample|demo|example|placeholder|your-?email|your-?name|user|admin)@',
                r'@(test|sample|demo|example|placeholder)\.com$',
                r'@your-?(domain|company|email)\.com$'
            ]

            for pattern in example_patterns:
                if re.match(pattern, email):
                    return True

            return False

        except ValueError:
            return False

    def extract_emails_with_contact_form_analysis(self, url):
        """問い合わせフォーム解析によるメールアドレス抽出"""
        if not self.use_contact_form_analysis or not self.contact_form_analyzer:
            logging.debug("問い合わせフォーム解析機能が利用できません")
            return []

        try:
            logging.info(f"問い合わせフォーム解析によるメールアドレス抽出を開始: {url}")
            result = self.contact_form_analyzer.analyze_contact_form(url)

            estimated_emails = result.get('estimated_emails', [])
            confidence_score = result.get('confidence_score', 0.0)
            forms_found = result.get('forms_found', [])

            if estimated_emails:
                logging.info(f"問い合わせフォーム解析により {len(estimated_emails)} 件のメールアドレスを推定しました (信頼度: {confidence_score:.2f}): {url}")

                # 信頼度が一定以上の場合のみ結果を返す
                if confidence_score >= 0.3:
                    # メールアドレス情報を既存の形式に変換
                    email_list = []
                    for email in estimated_emails:
                        email_info = {
                            'email': email,
                            'source': 'contact_form_analysis',
                            'confidence': confidence_score,
                            'url': url,
                            'forms_count': len(forms_found),
                            'contact_forms_count': len([f for f in forms_found if f.get('is_contact_form')]),
                            'analysis_methods': result.get('analysis_method', [])
                        }
                        email_list.append(email_info)

                    logging.info(f"問い合わせフォーム解析で {len(email_list)} 件の有効なメールアドレスを抽出しました")
                    return email_list
                else:
                    logging.info(f"信頼度が低いため結果を除外しました: {confidence_score:.2f}")
            else:
                logging.info(f"問い合わせフォーム解析ではメールアドレスが見つかりませんでした: {url}")

            return []
        except Exception as e:
            logging.error(f"問い合わせフォーム解析中にエラーが発生しました: {e}")
            logging.debug(traceback.format_exc())
            return []

    def extract_emails_from_footer(self, html, url=None):
        """フッター領域からメールアドレスを抽出（強化版）"""
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        emails = []

        # フッター要素を特定（より包括的に）
        footer_elements = []

        # 1. <footer>タグ
        footer_tags = soup.find_all('footer')
        footer_elements.extend(footer_tags)

        # 2. class属性にfooterを含む要素（部分一致も含む）
        footer_classes = soup.find_all(class_=lambda c: c and any('footer' in cls.lower() for cls in c if isinstance(c, list) or isinstance(c, str)))
        footer_elements.extend(footer_classes)

        # 3. id属性にfooterを含む要素
        footer_ids = soup.find_all(id=lambda i: i and 'footer' in i.lower())
        footer_elements.extend(footer_ids)

        # 4. コピーライト情報を含む要素とその親要素
        copyright_elements = soup.find_all(string=lambda s: s and ('©' in s or 'copyright' in s.lower() or '〒' in s))
        for element in copyright_elements:
            parent = element.parent
            if parent:
                footer_elements.append(parent)
                # 親の親も追加（より広範囲をカバー）
                if parent.parent:
                    footer_elements.append(parent.parent)

        # 5. 連絡先情報を示すキーワードを含む要素
        contact_keywords = ['連絡先', 'お問い合わせ', 'contact', 'email', 'mail', 'tel', 'fax', '電話', 'ファックス']
        for keyword in contact_keywords:
            contact_elements = soup.find_all(string=lambda s: s and keyword.lower() in s.lower())
            for element in contact_elements:
                if element.parent:
                    footer_elements.append(element.parent)
                    if element.parent.parent:
                        footer_elements.append(element.parent.parent)

        # 6. ページ下部50%の要素を取得（範囲を拡大）
        all_elements = soup.find_all()
        if len(all_elements) > 10:
            bottom_elements = all_elements[int(len(all_elements) * 0.5):]
            for element in bottom_elements:
                footer_elements.append(element)

        # フッター要素からメールアドレスを抽出
        for element in footer_elements:
            element_html = str(element)
            footer_emails = self.extract_emails_from_html(element_html, url)
            emails.extend(footer_emails)

        # 重複を削除
        unique_emails = list(set(emails))

        if unique_emails:
            logging.info(f"フッター領域から {len(unique_emails)} 件のメールアドレスを抽出: {unique_emails}")

        return unique_emails

    def find_contact_pages(self, base_url):
        """お問い合わせページ、会社概要ページ、およびその他の重要なページのURLを特定"""
        if not base_url:
            return []

        # base_urlが http:// または https:// で始まっていない場合、https:// を追加
        if not base_url.startswith(('http://', 'https://')):
            base_url = 'https://' + base_url

        response = self.fetch_url(base_url)
        if not response:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        contact_pages = []

        # リンクテキストによる検索 - 大幅拡張版
        contact_keywords = ['お問い合わせ', 'お問合せ', 'お問合わせ', 'お問い合せ', 'contact', 'inquiry', 'inquiries', 'contact us', 'support', 'サポート', 'help', 'ヘルプ', 'form', 'フォーム']
        about_keywords = ['会社概要', '企業情報', '会社情報', 'about', 'company', 'corporate', 'profile', 'about us', 'organization', '組織', 'outline', '概要']
        recruit_keywords = ['採用', '採用情報', '求人', '募集', '募集要項', 'キャリア', 'recruit', 'careers', 'jobs', 'recruitment', 'career', 'hr', '人事', 'jinzai', '人材', 'employment', '雇用']

        # 新規追加のページタイプ
        news_keywords = ['news', 'press', 'release', 'ニュース', 'プレスリリース', 'information', '情報', 'topics', 'トピックス', 'what\'s new', 'whats-new', 'お知らせ', 'oshirase', 'announce', '発表']
        privacy_keywords = ['privacy', 'policy', 'プライバシー', 'プライバシーポリシー', 'kojinjouhou', '個人情報', 'protection', '保護', 'terms', '利用規約', 'riyoukiyaku', '個人情報の取扱い', '個人情報保護', '個人情報保護管理者', '問合せ窓口']
        ir_keywords = ['ir', 'investor', 'investors', '投資家', '投資家情報', 'toushika', 'financial', '財務', 'zaimu', 'earnings', 'kessan', '決算']
        sitemap_keywords = ['sitemap', 'site-map', 'サイトマップ', 'map', 'index', 'インデックス', 'navigation', 'ナビゲーション']
        blog_keywords = ['blog', 'ブログ', 'diary', '日記', 'column', 'コラム', 'article', '記事', 'kiji']
        case_keywords = ['case', 'study', '事例', 'jirei', '導入事例', 'dounyuu', 'example', '実例', 'jitsurei', 'success', '成功']
        access_keywords = ['access', 'アクセス', 'map', '地図', 'chizu', 'location', 'basho', '場所', 'address', '住所', 'juusho']

        # キーワードタイプの辞書を作成
        keyword_types = {
            'contact': contact_keywords,
            'about': about_keywords,
            'recruit': recruit_keywords,
            'news': news_keywords,
            'privacy': privacy_keywords,
            'ir': ir_keywords,
            'sitemap': sitemap_keywords,
            'blog': blog_keywords,
            'case': case_keywords,
            'access': access_keywords
        }

        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text().lower()

            # 相対URLを絶対URLに変換
            full_url = urljoin(base_url, href)

            # 同じドメイン内のURLのみを対象
            if not self.is_same_domain(base_url, full_url):
                continue

            # 各タイプのキーワードに対してチェック
            for page_type, keywords in keyword_types.items():
                if any(keyword.lower() in text for keyword in keywords) or any(keyword.lower() in href.lower() for keyword in keywords):
                    contact_pages.append({
                        'url': full_url,
                        'type': page_type,
                        'text': a.get_text().strip()
                    })
                    break  # 一つのタイプに分類されたら次のリンクへ

        # 重複を削除
        unique_pages = []
        seen_urls = set()
        for page in contact_pages:
            if page['url'] not in seen_urls:
                seen_urls.add(page['url'])
                unique_pages.append(page)

        return unique_pages

    def is_same_domain(self, url1, url2):
        """2つのURLが同じドメインかどうかを判定"""
        try:
            domain1 = urllib.parse.urlparse(url1).netloc
            domain2 = urllib.parse.urlparse(url2).netloc

            # www.を削除
            if domain1.startswith('www.'):
                domain1 = domain1[4:]
            if domain2.startswith('www.'):
                domain2 = domain2[4:]

            return domain1 == domain2
        except:
            return False

    def generate_email_patterns(self, domain, company_name=None):
        """ドメインと会社名からメールアドレスパターンを生成（企業ドメイン限定）"""
        if not domain:
            return []

        email_patterns = []

        # 日本語企業かどうかを判定
        is_japanese = self.is_japanese_company(company_name) if company_name else True

        # 実例データに基づく強化された優先順位プレフィックスリスト
        # 自動返信実例: contact@, tiebreak@, cs@
        prioritized_prefixes = [
            'contact',      # 1位 - 株式会社フルネス実例
            'info',         # 2位 - 最も一般的
            'cs',           # 3位 - 株式会社マルホン実例（Customer Service）
            'support',      # 4位 - サポート系
            'inquiry',      # 5位 - お問い合わせ系
            'otoiawase',    # 6位 - 日本語お問い合わせ
            'sales',        # 7位 - 営業系
            'eigyo',        # 8位 - 日本語営業
            'office',       # 9位 - オフィス系
            'mail',         # 10位 - シンプル系
            'soumu',        # 11位 - 総務
            'company',      # 12位 - 会社代表
            'representative', # 13位 - 代表
            'reply'         # 14位 - 返信系
        ]

        # 企業名ベースのパターンを最優先に追加（株式会社タイブレイク実例：tiebreak@tiebreak.co.jp）
        if company_name:
            company_english = self.extract_english_from_company_name(company_name)
            if company_english and len(company_english) > 2:
                # ドメインとの一致度をチェック
                if company_english.lower() in domain.lower():
                    # 企業名ベースを最優先に挿入（実例：tiebreak@tiebreak.co.jp）
                    prioritized_prefixes.insert(0, company_english.lower())
                    logging.info(f"企業名ベースパターンを最優先に設定: {company_english.lower()}@{domain}")
                else:
                    # ドメインと一致しない場合でも、企業名ベースを高優先度で追加
                    prioritized_prefixes.insert(2, company_english.lower())
                    logging.info(f"企業名ベースパターンを高優先度で追加: {company_english.lower()}@{domain}")

        # 優先順位に基づいてメールアドレスを生成（必ず企業ドメインを使用）
        for i, prefix in enumerate(prioritized_prefixes):
            # 優先順位に基づいて順番を保持
            priority_rank = i + 1

            # 企業ドメインのみを使用してメールアドレスを生成
            email_patterns.append({
                'email': f"{prefix}@{domain}",
                'priority': 'high',
                'type': 'common_prefix',
                'priority_rank': priority_rank  # 優先順位を記録
            })

        # 代替ドメインパターンを追加（株式会社マルホン実例：mokuzai.com → maruhon.com）
        if company_name:
            alt_domains = self.generate_alternative_domains(company_name, domain)
            for alt_domain in alt_domains:
                # 代替ドメインでも主要なプレフィックスを試行
                alt_prefixes = ['cs', 'contact', 'info', 'support']
                for j, alt_prefix in enumerate(alt_prefixes):
                    email_patterns.append({
                        'email': f"{alt_prefix}@{alt_domain}",
                        'priority': 'medium',
                        'type': 'alternative_domain',
                        'priority_rank': len(prioritized_prefixes) + j + 1
                    })

        # 日本語企業向けの追加プレフィックス（優先順位は低め）
        japanese_prefixes = []
        if is_japanese:
            japanese_prefixes = [
                'toiawase',    # お問い合わせの別表記
                'inquiry',     # 英語のお問い合わせ
                'mail',        # メール
                'jigyou',      # 事業
                'kouhou',      # 広報
                'web'          # ウェブ
            ]

            # 既に追加したプレフィックスは除外
            japanese_prefixes = [p for p in japanese_prefixes if p not in prioritized_prefixes]

            for prefix in japanese_prefixes:
                email_patterns.append({
                    'email': f"{prefix}@{domain}",
                    'priority': 'medium',
                    'type': 'common_prefix'
                })

        # 低優先度のプレフィックス
        # 既に追加したプレフィックスを除外し、postmasterも除外
        low_priority_prefixes = [p for p in self.role_based_prefixes
                               if p not in prioritized_prefixes
                               and p not in japanese_prefixes
                               and p != 'postmaster']  # postmasterを明示的に除外
        for prefix in low_priority_prefixes:
            email_patterns.append({
                'email': f"{prefix}@{domain}",
                'priority': 'low',
                'type': 'common_prefix'
            })

        # 会社名を使ったパターン（会社名が提供されている場合）
        if company_name:
            # 会社名の処理
            processed_name = self.process_company_name(company_name)

            if processed_name:
                # 会社名をそのまま使用
                email_patterns.append({
                    'email': f"{processed_name}@{domain}",
                    'priority': 'medium',
                    'type': 'company_name'
                })

                # 会社名と一般的なプレフィックスの組み合わせ
                email_patterns.append({
                    'email': f"info-{processed_name}@{domain}",
                    'priority': 'medium',
                    'type': 'company_name'
                })
                email_patterns.append({
                    'email': f"{processed_name}-info@{domain}",
                    'priority': 'medium',
                    'type': 'company_name'
                })

                # 日本語企業向けの追加パターン
                if is_japanese:
                    email_patterns.append({
                        'email': f"{processed_name}.info@{domain}",
                        'priority': 'medium',
                        'type': 'company_name'
                    })
                    email_patterns.append({
                        'email': f"info.{processed_name}@{domain}",
                        'priority': 'medium',
                        'type': 'company_name'
                    })

                # 会社名の頭文字を使用
                if len(processed_name) > 2:
                    initials = ''.join([c[0] for c in processed_name.split() if c])
                    if initials:
                        email_patterns.append({
                            'email': f"{initials}@{domain}",
                            'priority': 'low',
                            'type': 'company_initials'
                        })
                        email_patterns.append({
                            'email': f"info-{initials}@{domain}",
                            'priority': 'low',
                            'type': 'company_initials'
                        })

        return email_patterns

    def is_japanese_company(self, company_name):
        """企業名から日本企業かどうかを判定"""
        if not company_name:
            return True  # デフォルトは日本企業と仮定

        # 日本語の法人形態
        japanese_suffixes = ['株式会社', '有限会社', '合同会社', '合資会社', '協同組合', '一般社団法人', '公益社団法人',
                            '一般財団法人', '公益財団法人', '社会福祉法人', '学校法人', '医療法人', '宗教法人']

        # 日本語の文字が含まれているか
        japanese_chars = re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', company_name)

        # 日本語の法人形態が含まれているか
        has_japanese_suffix = any(suffix in company_name for suffix in japanese_suffixes)

        return has_japanese_suffix or len(japanese_chars) > 0

    def estimate_industry(self, company_name):
        """企業名から業種を推定"""
        if not company_name:
            return None

        # 建設業
        construction_keywords = ['建設', '工務店', '工業', '建築', '土木', '設備', '電気工事', '住宅', '不動産', 'construction', 'builders', 'housing']

        # IT業
        it_keywords = ['システム', 'コンピュータ', 'テクノロジー', 'ソフト', 'IT', 'tech', 'software', 'systems', 'digital', 'web', 'net', 'computer']

        # 小売業
        retail_keywords = ['ショップ', 'ストア', '販売', '商事', '商店', '卸', '小売', 'shop', 'store', 'retail', 'trading']

        # 金融業
        finance_keywords = ['銀行', '証券', '保険', '信用', '金融', 'bank', 'insurance', 'securities', 'finance', 'financial']

        # 業種判定
        company_name_lower = company_name.lower()

        if any(keyword in company_name_lower for keyword in construction_keywords):
            return 'construction'
        elif any(keyword in company_name_lower for keyword in it_keywords):
            return 'it'
        elif any(keyword in company_name_lower for keyword in retail_keywords):
            return 'retail'
        elif any(keyword in company_name_lower for keyword in finance_keywords):
            return 'finance'

        return None

    def process_company_name(self, company_name):
        """会社名をメールアドレス用に処理"""
        if not company_name:
            return None

        # 法人形態を削除
        for suffix in ['株式会社', '有限会社', '合同会社', '社団法人', '財団法人', '一般社団法人', '一般財団法人',
                      '協同組合', '社会福祉法人', '学校法人', '医療法人', '宗教法人', 'Inc.', 'LLC', 'Ltd.', 'Co.,Ltd.', 'Corporation']:
            if company_name.startswith(suffix):
                company_name = company_name[len(suffix):].strip()
            elif company_name.endswith(suffix):
                company_name = company_name[:-len(suffix)].strip()
            else:
                company_name = company_name.replace(suffix, '').strip()

        # 空白と特殊文字を削除
        company_name = company_name.strip().lower()

        # 日本語をローマ字に変換（簡易版）
        japanese_chars = re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', company_name)
        if japanese_chars:
            # 日本語が含まれる場合

            # 一般的な日本語の読みをローマ字に変換（簡易版）
            romaji_mapping = {
                '山田': 'yamada', '鈴木': 'suzuki', '佐藤': 'sato', '田中': 'tanaka', '高橋': 'takahashi',
                '伊藤': 'ito', '渡辺': 'watanabe', '加藤': 'kato', '吉田': 'yoshida', '山本': 'yamamoto',
                '中村': 'nakamura', '小林': 'kobayashi', '松本': 'matsumoto', '井上': 'inoue', '木村': 'kimura',
                '林': 'hayashi', '斎藤': 'saito', '清水': 'shimizu', '山口': 'yamaguchi', '近藤': 'kondo',
                '建設': 'kensetsu', '工業': 'kogyo', '工務店': 'koumuten', '商事': 'shoji', '産業': 'sangyo',
                '開発': 'kaihatsu', 'システム': 'system', 'コンピュータ': 'computer', 'テクノロジー': 'technology',
                '不動産': 'fudosan', '住宅': 'jutaku', '設計': 'sekkei', '設備': 'setsubi', '電気': 'denki',
                '通信': 'tsushin', '運輸': 'unyu', '物流': 'butsuryu', '商会': 'shokai', '製作所': 'seisakusho'
            }

            # 会社名を部分的にローマ字に変換
            romaji_name = company_name
            for jp, romaji in romaji_mapping.items():
                if jp in romaji_name:
                    romaji_name = romaji_name.replace(jp, romaji)

            # 英数字のみを抽出
            safe_name = ''.join(c for c in romaji_name if c.isalnum() or c == '-' or c == '_')

            # 英数字がない場合は、会社名の最初の数文字をそのまま使用
            if not safe_name and company_name:
                # 会社名の先頭部分を使用
                safe_name = company_name[:5]

                # 特殊文字を削除
                safe_name = re.sub(r'[^\w\-]', '', safe_name)
        else:
            # 英語名の場合は、空白をハイフンに置換し、特殊文字を削除
            safe_name = re.sub(r'[^a-z0-9\-_]', '', company_name.replace(' ', '-'))

        # 名前が短すぎる場合は、元の会社名から生成
        if len(safe_name) < 2 and company_name:
            # 会社名のハッシュ値を使用
            import hashlib
            hash_obj = hashlib.md5(company_name.encode('utf-8'))
            safe_name = hash_obj.hexdigest()[:8]

        return safe_name

    def verify_email_format(self, email):
        """メールアドレスの形式を検証（強化版）"""
        if not email:
            return False

        # 基本的な形式チェック
        basic_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(basic_pattern, email):
            return False

        # 無効なパターンを除外
        invalid_patterns = [
            r'\.wp-block-',  # WordPressのCSSクラス名
            r'@link\.',      # 明らかに無効なドメイン
            r'@\d+\.',       # 数字のみのドメイン（例: @200.jp）
            r'^[^a-zA-Z]',   # 英字以外で始まるローカル部
            r'@.*\.(no|test|example|invalid)$',  # テスト用ドメイン
            r'@.*\.(png|jpg|jpeg|gif|css|js)$',  # ファイル拡張子
            r'[<>"\'\s]',    # HTMLタグや引用符、空白文字
        ]

        for pattern in invalid_patterns:
            if re.search(pattern, email, re.IGNORECASE):
                return False

        # @の前後に文字があるか
        try:
            local_part, domain_part = email.split('@')
            if not local_part or not domain_part:
                return False

            # ドメイン部分にピリオドがあるか
            if '.' not in domain_part:
                return False

            # ローカル部分の長さが適切か
            if len(local_part) > 64:
                return False

            # ドメイン部分の長さが適切か
            if len(domain_part) > 255:
                return False

            # ローカル部分が無効なパターンでないかチェック
            if local_part.startswith('.') or local_part.endswith('.'):
                return False

            # ドメイン部分が無効なパターンでないかチェック
            if domain_part.startswith('.') or domain_part.endswith('.'):
                return False

        except:
            return False

        return True

    def verify_mx_record(self, domain):
        """ドメインのMXレコードを確認"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except Exception as e:
            logging.error(f"MXレコード確認エラー ({domain}): {e}")
            return False

    def verify_smtp(self, email):
        """SMTPレベルでメールアドレスの存在を検証（実装版）"""
        result = {
            'is_valid': False,
            'is_catch_all': False,
            'details': '',
            'response_code': None,
            'response_message': ''
        }

        try:
            # ドメイン部分を取得
            parts = email.split('@')
            if len(parts) != 2:
                result['details'] = '無効なメールアドレス形式'
                return result

            local_part, domain = parts

            # MXレコードを確認
            if not self.verify_mx_record(domain):
                result['details'] = 'MXレコードが存在しない'
                return result

            # 一般的なドメインは有効と仮定（SMTPサーバーがブロックする可能性があるため）
            common_domains = ['gmail.com', 'yahoo.co.jp', 'outlook.com', 'hotmail.com', 'icloud.com', 'mail.com', 'aol.com', 'protonmail.com']
            if domain in common_domains:
                result['is_valid'] = True
                result['details'] = '一般的なドメイン'
                return result

            try:
                # MXレコードを取得
                mx_records = dns.resolver.resolve(domain, 'MX')
                mx_hosts = [str(rdata.exchange).rstrip('.') for rdata in mx_records]

                if not mx_hosts:
                    result['details'] = 'MXレコードが存在するが、有効なMXホストがない'
                    return result

                # 最も優先度の高いMXサーバーを使用
                mx_host = mx_hosts[0]

                # SMTPサーバーに接続（短いタイムアウト）
                smtp = smtplib.SMTP(timeout=2)  # タイムアウトを2秒に短縮
                smtp.connect(mx_host)
                smtp.ehlo_or_helo_if_needed()

                # 送信元アドレス（存在する可能性が高いアドレスを使用）
                from_address = f"verify@{domain}"

                # MAIL FROMコマンド
                smtp.mail(from_address)

                # RCPT TOコマンドでメールアドレスを検証
                code, message = smtp.rcpt(email)
                result['response_code'] = code
                result['response_message'] = message.decode('utf-8', errors='ignore') if isinstance(message, bytes) else str(message)

                # 250はOK、それ以外はエラー
                if code == 250:
                    result['is_valid'] = True
                    result['details'] = 'SMTP検証成功'

                    # キャッチオールチェック
                    # ランダムな文字列を生成してテスト
                    random_local = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
                    random_email = f"{random_local}@{domain}"

                    # ランダムアドレスをテスト
                    random_code, _ = smtp.rcpt(random_email)
                    if random_code == 250:
                        result['is_catch_all'] = True
                        result['details'] = 'キャッチオールドメイン'
                else:
                    result['details'] = f"SMTP検証失敗: {code} {result['response_message']}"

                # 接続を閉じる
                smtp.quit()

            except smtplib.SMTPServerDisconnected:
                result['details'] = 'SMTPサーバーが接続を切断'
            except smtplib.SMTPResponseException as e:
                result['response_code'] = e.smtp_code
                result['response_message'] = e.smtp_error.decode('utf-8', errors='ignore') if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
                result['details'] = f"SMTPエラー: {e.smtp_code} {result['response_message']}"
            except smtplib.SMTPException as e:
                result['details'] = f"SMTPエラー: {str(e)}"
            except socket.timeout:
                result['details'] = 'SMTP接続タイムアウト'
            except socket.error as e:
                result['details'] = f"ソケットエラー: {str(e)}"
            except Exception as e:
                result['details'] = f"SMTP検証中の予期しないエラー: {str(e)}"

            return result
        except Exception as e:
            result['details'] = f"SMTP検証エラー: {str(e)}"
            return result

    def verify_email_smtp(self, email, domain=None):
        """SMTPレベルでメールアドレスの存在を検証（シンプル版）"""
        try:
            # ドメインが指定されていない場合はメールアドレスから取得
            if domain is None:
                parts = email.split('@')
                if len(parts) != 2:
                    return False, "無効なメールアドレス形式"
                domain = parts[1]

            # MXレコードを確認
            if not self.verify_mx_record(domain):
                return False, "MXレコードが存在しない"

            # 一般的なドメインは有効と仮定（SMTPサーバーがブロックする可能性があるため）
            common_domains = ['gmail.com', 'yahoo.co.jp', 'outlook.com', 'hotmail.com', 'icloud.com', 'mail.com', 'aol.com', 'protonmail.com']
            if domain in common_domains:
                return True, "一般的なドメイン"

            # MXレコードを取得
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_host = str(mx_records[0].exchange).rstrip('.')

            # SMTPサーバーに接続（短いタイムアウト）
            server = smtplib.SMTP(timeout=2)  # タイムアウトを2秒に短縮
            server.connect(mx_host)
            server.ehlo_or_helo_if_needed()

            # 送信元アドレス
            from_address = f"verify@{domain}"

            # MAIL FROMコマンド
            server.mail(from_address)

            # RCPT TOコマンド
            code, message = server.rcpt(email)

            # 接続を閉じる
            server.quit()

            # 250はOK、それ以外はエラー
            if code == 250:
                return True, "SMTP検証成功"
            else:
                message_str = message.decode('utf-8', errors='ignore') if isinstance(message, bytes) else str(message)
                return False, f"SMTP検証失敗: {code} {message_str}"

        except Exception as e:
            return False, f"SMTP検証中にエラー: {e}"

    def verify_email_domain_match(self, email, company_domain):
        """メールアドレスのドメインが企業ドメインと一致するかチェック"""
        if not email or not company_domain or '@' not in email:
            return False

        try:
            _, email_domain = email.split('@')
            email_domain = email_domain.lower().strip()
            company_domain = company_domain.lower().strip()

            # www.を除去
            if company_domain.startswith('www.'):
                company_domain = company_domain[4:]
            if email_domain.startswith('www.'):
                email_domain = email_domain[4:]

            # 完全一致
            if email_domain == company_domain:
                return True

            # サブドメインの場合も許可（例: mail.example.com と example.com）
            if email_domain.endswith('.' + company_domain):
                return True

            return False
        except:
            return False

    def verify_email(self, email, company_domain=None):
        """メールアドレスの存在を検証（ドメイン検証機能付き）"""
        result = {
            'email': email,
            'is_valid_format': False,
            'has_mx_record': False,
            'smtp_valid': False,
            'is_disposable': False,
            'is_role_based': False,
            'is_catch_all': False,
            'verification_level': 'none',
            'details': '',
            'confidence': 0.0,
            'source': 'generated',
            'domain_match': False
        }

        # 形式の検証
        if not self.verify_email_format(email):
            result['details'] = '無効なメールアドレス形式'
            return result

        result['is_valid_format'] = True
        result['verification_level'] = 'format'
        result['confidence'] = 0.1

        # ドメイン部分を取得
        _, domain = email.split('@')

        # 企業ドメインとの一致チェック
        if company_domain:
            domain_match = self.verify_email_domain_match(email, company_domain)
            result['domain_match'] = domain_match

            if not domain_match:
                result['details'] = f'企業ドメイン({company_domain})と一致しません'
                result['confidence'] = 0.0  # ドメインが一致しない場合は信頼度を0に
                return result
            else:
                result['confidence'] = 0.3  # ドメインが一致する場合は基本信頼度を向上

        # 使い捨てメールアドレスのチェック
        if domain in self.disposable_domains:
            result['is_disposable'] = True
            result['details'] = '使い捨てメールドメイン'
            result['confidence'] = 0.0
            return result

        # ロールベースアドレスのチェック
        local_part = email.split('@')[0]
        if local_part.lower() in self.role_based_prefixes:
            result['is_role_based'] = True
            result['details'] += ' ロールベースアドレス'

            # postmasterアドレスは特別に除外
            if local_part.lower() == 'postmaster':
                result['details'] += ' (postmasterアドレスは除外)'
                result['confidence'] = 0.0
                return result

        # MXレコードの検証
        if self.verify_mx_record(domain):
            result['has_mx_record'] = True
            result['verification_level'] = 'mx'

            # 基本信頼度を向上（MXレコード存在で0.5に）
            result['confidence'] = 0.5

            # 一般的なプレフィックスの場合は信頼度をさらに向上
            common_prefixes = ['info', 'contact', 'mail', 'inquiry', 'support']
            if local_part.lower() in common_prefixes:
                result['confidence'] = 0.7

            # SMTP検証（Spamhausブロック対策のため一時的に無効化）
            # 本番環境では外部SMTPサービス経由で検証を推奨
            skip_smtp_verification = True  # Spamhausブロック対策

            if not skip_smtp_verification:
                smtp_result = self.verify_smtp(email)
                if smtp_result['is_valid']:
                    result['smtp_valid'] = True
                    result['verification_level'] = 'smtp'
                    result['details'] += ' SMTP検証成功'

                    # キャッチオールかどうかで信頼度を調整
                    if smtp_result['is_catch_all']:
                        result['is_catch_all'] = True
                        result['details'] += ' キャッチオールドメイン'
                        result['confidence'] = 0.7
                    else:
                        result['confidence'] = 0.9
                else:
                    result['details'] += f" SMTP検証失敗: {smtp_result['details']}"
                    result['confidence'] = 0.2
            else:
                # SMTP検証をスキップして、MX検証のみで信頼度を設定
                result['details'] += ' SMTP検証スキップ（テストモード）'
                result['confidence'] = 0.6  # MX検証のみの場合の信頼度
        else:
            result['details'] = 'MXレコードなし'
            result['confidence'] = 0.0

        return result

    def extract_emails_with_dynamic_rendering(self, url):
        """JavaScriptによる動的生成メールアドレスを抽出"""
        if not self.use_dynamic_extraction or not self.dynamic_extractor:
            logging.debug("動的メール抽出機能は無効です")
            return []

        try:
            logging.info(f"動的レンダリングによるメールアドレス抽出を開始: {url}")
            emails = self.dynamic_extractor.extract_emails_from_dynamic_page(url)

            if emails:
                logging.info(f"動的レンダリングにより {len(emails)} 件のメールアドレスを抽出しました: {url}")
            else:
                logging.info(f"動的レンダリングではメールアドレスが見つかりませんでした: {url}")

            return emails
        except Exception as e:
            logging.error(f"動的メール抽出中にエラーが発生しました: {e}")
            logging.debug(traceback.format_exc())
            return []

    def is_high_value_page(self, url, link_text=''):
        """URLがメールアドレスを含む可能性が高いページかどうかを判定"""
        url_lower = url.lower()
        link_text_lower = link_text.lower()

        # 優先度の高いページタイプ
        high_value_keywords = {
            # 最優先: お問い合わせページ
            'contact': ['contact', 'inquiry', 'お問い合わせ', 'お問合せ', 'お問合わせ', 'お問い合せ', 'inquiries', 'contact us', 'toiawase', 'otoiawase', 'mail', 'email', 'メール'],

            # 次点: 会社概要ページ
            'about': ['about', 'company', 'profile', 'corporate', '会社概要', '企業情報', '会社情報', 'about us', 'company profile', 'corporate profile', '会社案内'],

            # 採用情報ページ（高優先度）
            'recruit': ['recruit', 'careers', 'jobs', 'recruitment', 'career', '採用', '採用情報', '求人', '募集', '募集要項', 'キャリア'],

            # その他の重要ページ
            'other_important': ['privacy', 'terms', 'ir', 'news', 'ニュース', 'プライバシー', 'サイトマップ', 'ブログ', 'privacy policy']
        }

        # 優先度スコアを計算（高いほど優先）
        score = 0

        # URLに基づくスコア
        if any(keyword in url_lower for keyword in high_value_keywords['contact']):
            score += 10
        elif any(keyword in url_lower for keyword in high_value_keywords['about']):
            score += 5
        elif any(keyword in url_lower for keyword in high_value_keywords['recruit']):
            score += 7  # 採用情報ページは会社概要より優先度高め
        elif any(keyword in url_lower for keyword in high_value_keywords['other_important']):
            score += 3

        # リンクテキストに基づくスコア
        if any(keyword in link_text_lower for keyword in high_value_keywords['contact']):
            score += 5
        elif any(keyword in link_text_lower for keyword in high_value_keywords['about']):
            score += 3
        elif any(keyword in link_text_lower for keyword in high_value_keywords['recruit']):
            score += 4  # 採用情報ページは会社概要より優先度高め
        elif any(keyword in link_text_lower for keyword in high_value_keywords['other_important']):
            score += 1

        return score

    def process_page(self, url, base_url):
        """単一ページを処理してメールアドレスを抽出（並列処理用）"""
        try:
            logging.info(f"ページを処理中: {url}")
            response = self.fetch_url(url)
            if not response:
                return []

            # このページからメールアドレスを抽出
            page_emails = self.extract_emails_from_html(response.text, url)
            if page_emails:
                logging.info(f"{url} から {len(page_emails)} 件のメールアドレスを抽出しました")

            # 新しいリンクを見つける
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)

            new_links = []
            for link in links:
                href = link['href']
                link_text = link.get_text()

                # 相対URLを絶対URLに変換
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)

                # 同じドメイン内のURLのみを対象
                if self.is_same_domain(base_url, href):
                    # 優先度スコアを計算
                    priority_score = self.is_high_value_page(href, link_text)
                    if priority_score > 0:
                        new_links.append((priority_score, href))

            return {
                'emails': page_emails,
                'links': new_links,
                'url': url
            }
        except Exception as e:
            logging.warning(f"ページ {url} の処理中にエラー: {e}")
            logging.debug(traceback.format_exc())
            return {
                'emails': [],
                'links': [],
                'url': url
            }

    def deep_crawl_for_emails(self, base_url, max_pages=15, max_workers=5, adaptive_depth=True):
        """複数のページを並列探索してメールアドレスを抽出（拡張版）

        Args:
            base_url (str): 基本URL
            max_pages (int): 探索する最大ページ数
            max_workers (int): 並列処理するワーカー数
            adaptive_depth (bool): 探索深度を動的に調整するかどうか

        Returns:
            list: 抽出されたメールアドレスのリスト
        """
        if not base_url:
            return []

        # 訪問済みURLと訪問予定URLの管理
        visited = set()
        to_visit = PriorityQueue()  # 優先度付きキュー
        emails = []
        email_lock = Lock()  # メールリストの同期用ロック

        # 初期URLを追加
        to_visit.put((-10, base_url))  # 負の値を使用して高い優先度を表現

        # XMLサイトマップを探索して優先度の高いURLを追加
        try:
            sitemap_url = urljoin(base_url, '/sitemap.xml')
            sitemap_response = self.fetch_url(sitemap_url)
            if sitemap_response and 'xml' in sitemap_response.headers.get('Content-Type', ''):
                logging.info(f"XMLサイトマップを発見: {sitemap_url}")
                soup = BeautifulSoup(sitemap_response.text, 'html.parser')
                # XMLの<loc>タグを探す
                for loc in soup.find_all('loc'):
                    url = loc.text.strip()
                    if self.is_same_domain(base_url, url):
                        # サイトマップから取得したURLの優先度を計算
                        priority = -self.is_high_value_page(url)  # 負の値で優先度を表現
                        to_visit.put((priority, url))
        except Exception as e:
            logging.warning(f"XMLサイトマップの探索中にエラー: {e}")

        # お問い合わせページと会社概要ページを優先的に探索
        contact_pages = self.find_contact_pages(base_url)
        for page in contact_pages:
            url = page['url']
            page_type = page['type']
            if url not in visited:
                # ページタイプに応じた優先度を設定
                if page_type == 'contact':
                    priority = -15  # 最優先
                elif page_type == 'about':
                    priority = -12  # 次点
                elif page_type == 'recruit':
                    priority = -10  # 採用情報ページも高い優先度
                else:
                    priority = -8   # その他の重要ページ
                to_visit.put((priority, url))

        # 並列処理で複数ページを同時に探索
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {}

            # 最初のバッチを処理
            batch_size = min(max_workers, max_pages)
            for _ in range(batch_size):
                if to_visit.empty() or len(visited) >= max_pages:
                    break

                try:
                    _, url = to_visit.get()
                    if url in visited:
                        continue

                    visited.add(url)
                    future = executor.submit(self.process_page, url, base_url)
                    future_to_url[future] = url
                except Exception as e:
                    logging.warning(f"ページのキューイング中にエラー: {e}")

            # 結果を処理しながら新しいページをキューに追加
            high_confidence_emails_found = False
            while future_to_url and len(visited) < max_pages and not high_confidence_emails_found:
                # 完了したタスクを処理
                done, _ = concurrent.futures.wait(
                    future_to_url,
                    timeout=0.5,
                    return_when=concurrent.futures.FIRST_COMPLETED
                )

                for future in done:
                    url = future_to_url.pop(future)
                    try:
                        result = future.result()

                        # メールアドレスを追加
                        with email_lock:
                            emails.extend(result['emails'])

                            # 十分な数の高品質なメールアドレスが見つかった場合、早期終了（条件を緩和）
                            if adaptive_depth and len(emails) >= 1:
                                # メールアドレスの品質を評価（ここでは単純に@前の部分で判断）
                                quality_emails = [email for email in emails if email.split('@')[0].lower() in
                                                ['info', 'contact', 'mail', 'inquiry', 'support', 'sales', 'office']]
                                if len(quality_emails) >= 1:
                                    logging.info(f"高品質なメールアドレスが見つかったため、探索を早期終了します")
                                    high_confidence_emails_found = True
                                    break

                        # 新しいリンクをキューに追加
                        if 'links' in result and isinstance(result['links'], list):
                            for link_info in result['links']:
                                try:
                                    # link_infoが文字列の場合は、デフォルト優先度で処理
                                    if isinstance(link_info, str):
                                        link = link_info
                                        priority = 1  # デフォルト優先度
                                    elif isinstance(link_info, tuple) and len(link_info) == 2:
                                        priority, link = link_info
                                    elif isinstance(link_info, dict) and 'url' in link_info:
                                        link = link_info['url']
                                        priority = link_info.get('priority', 1)
                                    else:
                                        logging.warning(f"予期しないリンク形式: {type(link_info)} - {link_info}")
                                        continue

                                    if link and link not in visited and len(visited) < max_pages:
                                        to_visit.put((-priority, link))  # 負の値で優先度を表現
                                except Exception as link_error:
                                    logging.warning(f"リンク処理エラー: {link_error} - {link_info}")
                                    continue
                    except Exception as e:
                        logging.warning(f"ページ {url} の結果処理中にエラー: {e}")
                        logging.debug(f"エラー詳細: {type(e).__name__}: {str(e)}")
                        # エラーが発生しても処理を続行

                # 新しいタスクをキューに追加
                while len(future_to_url) < max_workers and not to_visit.empty() and len(visited) < max_pages and not high_confidence_emails_found:
                    try:
                        _, url = to_visit.get()
                        if url in visited:
                            continue

                        visited.add(url)
                        future = executor.submit(self.process_page, url, base_url)
                        future_to_url[future] = url
                    except Exception as e:
                        logging.warning(f"新しいページのキューイング中にエラー: {e}")

        # 重複を削除
        unique_emails = list(set(emails))
        logging.info(f"並列探索の結果: {len(unique_emails)} 件のメールアドレスを発見、{len(visited)} ページを探索")
        return unique_emails

    def extract_emails_with_priority(self, company_name, url, company_id=None):
        """優先順位に基づいてメールアドレスを抽出"""
        # 現在の企業名を設定（他のメソッドで参照できるように）
        self.current_company_name = company_name

        result = {
            'company_name': company_name,
            'url': url,
            'domain': None,
            'emails': [],
            'best_email': None,
            'extraction_method': None,
            'company_id': company_id,
            'id': company_id,  # 互換性のために両方のキーで保存
            '企業ID': company_id,  # 日本語キーでも保存
            'continue_search': True  # 信頼度の低いメールアドレスでも探索を続けるフラグ
        }

        # 企業IDがある場合はログに出力
        if company_id:
            logging.info(f"企業ID {company_id}: {company_name} のメールアドレス抽出を開始します")

        # URLが有効かチェック
        if not url or url == '-':
            logging.warning(f"{company_name}: URLが指定されていません")
            return result

        # URLが http:// または https:// で始まっていない場合、https:// を追加
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            logging.info(f"{company_name}: URLを {url} に修正しました")

        # ドメインを抽出
        domain = self.extract_domain_from_url(url)
        if not domain:
            logging.error(f"{company_name}: ドメインを抽出できませんでした: {url}")
            return result

        result['domain'] = domain
        logging.info(f"{company_name}: ドメイン {domain} を抽出しました")

        # 優先順位1: トップページからのメールアドレス抽出（強化版）
        logging.info(f"{company_name}: 優先順位1 - トップページからのメールアドレス抽出")
        response = self.fetch_url(url)
        if response:
            # 全体からメールアドレスを抽出（フッター以外も含む）
            all_emails = self.extract_emails_from_html(response.text, url)
            if all_emails:
                logging.info(f"{company_name}: トップページ全体から {len(all_emails)} 件のメールアドレスを抽出しました")
                for email in all_emails:
                    # 検証（企業ドメインとの一致チェック付き）
                    verification = self.verify_email(email, domain)
                    verification['source'] = 'homepage'
                    result['emails'].append(verification)

            # フッター領域からメールアドレスを抽出（より詳細に）
            footer_emails = self.extract_emails_from_footer(response.text, url)
            if footer_emails:
                logging.info(f"{company_name}: フッターから {len(footer_emails)} 件のメールアドレスを抽出しました")
                for email in footer_emails:
                    # 既に抽出済みのメールアドレスはスキップ
                    if email in [e['email'] for e in result['emails']]:
                        continue
                    # 検証（企業ドメインとの一致チェック付き）
                    verification = self.verify_email(email, domain)
                    verification['source'] = 'footer'
                    result['emails'].append(verification)

            # 有効なメールアドレスがあれば、優先順位1で終了（信頼度が低い場合は探索を続ける）
            valid_emails = [e for e in result['emails'] if e['confidence'] >= 0.5]
            if valid_emails:
                result['extraction_method'] = 'homepage_footer'
                result['best_email'] = self.select_best_email(valid_emails)
                # 信頼度が0.8以上の場合は終了
                if result['best_email']['confidence'] >= 0.8:
                    logging.info(f"{company_name}: 高信頼度のメールアドレスが見つかりました: {result['best_email']['email']}")
                    return result
                else:
                    logging.info(f"{company_name}: 中程度の信頼度のメールアドレスが見つかりましたが、探索を続けます")

            # トップページ全体からメールアドレスを抽出
            page_emails = self.extract_emails_from_html(response.text, url)
            if page_emails:
                logging.info(f"{company_name}: トップページから {len(page_emails)} 件のメールアドレスを抽出しました")
                for email in page_emails:
                    # 既に抽出済みのメールアドレスはスキップ
                    if email in [e['email'] for e in result['emails']]:
                        continue

                    # 検証（企業ドメインとの一致チェック付き）
                    verification = self.verify_email(email, domain)
                    verification['source'] = 'homepage'
                    result['emails'].append(verification)

                # 有効なメールアドレスがあれば、優先順位1で終了（信頼度が低い場合は探索を続ける）
                valid_emails = [e for e in result['emails'] if e['confidence'] >= 0.5]
                if valid_emails:
                    result['extraction_method'] = 'homepage'
                    result['best_email'] = self.select_best_email(valid_emails)
                    # 信頼度が0.5以上だが0.8未満の場合は探索を続ける
                    if result['best_email']['confidence'] >= 0.8:
                        return result
                    else:
                        logging.info(f"{company_name}: トップページから信頼度の低いメールアドレスが見つかりましたが、探索を続けます")

        # 優先順位2: 会社概要・お問い合わせページからのメールアドレス抽出（強化版）
        logging.info(f"{company_name}: 優先順位2 - 会社概要・お問い合わせページからのメールアドレス抽出")

        # 特定の問い合わせページURLパターンを直接試行
        potential_contact_urls = [
            f"{url.rstrip('/')}/sub3.html",  # 北弘機工株式会社のパターン
            f"{url.rstrip('/')}/contact.html",
            f"{url.rstrip('/')}/contact/",
            f"{url.rstrip('/')}/inquiry.html",
            f"{url.rstrip('/')}/toiawase.html",
            f"{url.rstrip('/')}/about.html",
            f"{url.rstrip('/')}/company.html"
        ]

        # 直接URLを試行
        for contact_url in potential_contact_urls:
            if contact_url == url:  # 既に処理済みのURLはスキップ
                continue

            logging.info(f"{company_name}: 直接お問い合わせページを試行: {contact_url}")
            contact_response = self.fetch_url(contact_url)
            if contact_response:
                # ページ全体からメールアドレスを抽出
                contact_emails = self.extract_emails_from_html(contact_response.text, contact_url)

                if contact_emails:
                    logging.info(f"{company_name}: 直接アクセスで {len(contact_emails)} 件のメールアドレスを抽出: {contact_url}")
                    for email in contact_emails:
                        # 既に抽出済みのメールアドレスはスキップ
                        if email in [e['email'] for e in result['emails']]:
                            continue

                        # 検証（企業ドメインとの一致チェック付き）
                        verification = self.verify_email(email, domain)
                        verification['source'] = 'direct_contact'
                        result['emails'].append(verification)

        # 通常の関連ページ検索
        contact_pages = self.find_contact_pages(url)
        if contact_pages:
            logging.info(f"{company_name}: {len(contact_pages)} 件の関連ページを発見しました")
            for page in contact_pages:
                page_url = page['url']
                page_type = page['type']

                logging.info(f"{company_name}: {page_type} ページを分析中: {page_url}")
                page_response = self.fetch_url(page_url)
                if page_response:
                    # 通常のメール抽出
                    page_emails = self.extract_emails_from_html(page_response.text, page_url)

                    # 個人情報の取扱いについての欄からの特別抽出（お問い合わせページの場合）
                    if page_type == 'contact':
                        page_soup = BeautifulSoup(page_response.text, 'html.parser')
                        privacy_emails = self.extract_emails_from_privacy_sections(page_soup, page_url)
                        page_emails.extend(privacy_emails)
                        if privacy_emails:
                            logging.info(f"{company_name}: お問い合わせページの個人情報セクションから {len(privacy_emails)} 件のメールアドレスを抽出")

                        # 問い合わせフォームの自動返信メールアドレスを抽出（新機能）
                        form_reply_emails = self.extract_contact_form_reply_emails(page_soup, page_url)
                        page_emails.extend(form_reply_emails)
                        if form_reply_emails:
                            logging.info(f"{company_name}: お問い合わせフォームから {len(form_reply_emails)} 件の自動返信メールアドレスを抽出")

                    if page_emails:
                        logging.info(f"{company_name}: {page_type} ページから {len(page_emails)} 件のメールアドレスを抽出しました")
                        for email in page_emails:
                            # 既に抽出済みのメールアドレスはスキップ
                            if email in [e['email'] for e in result['emails']]:
                                continue

                            # 検証（企業ドメインとの一致チェック付き）
                            verification = self.verify_email(email, domain)
                            verification['source'] = page_type
                            result['emails'].append(verification)

            # 有効なメールアドレスがあれば、優先順位2で終了（信頼度が低い場合は探索を続ける）
            valid_emails = [e for e in result['emails'] if e['confidence'] >= 0.5]
            if valid_emails:
                result['extraction_method'] = 'contact_pages'
                result['best_email'] = self.select_best_email(valid_emails)
                # 信頼度が0.5以上だが0.8未満の場合は探索を続ける
                if result['best_email']['confidence'] >= 0.8:
                    return result
                else:
                    logging.info(f"{company_name}: お問い合わせページから信頼度の低いメールアドレスが見つかりましたが、探索を続けます")

        # 優先順位2.5: 問い合わせフォーム解析による推定メールアドレス抽出
        if self.use_contact_form_analysis:
            logging.info(f"{company_name}: 優先順位2.5 - 問い合わせフォーム解析による推定メールアドレス抽出")
            form_emails = self.extract_emails_with_contact_form_analysis(url)

            if form_emails:
                logging.info(f"{company_name}: 問い合わせフォーム解析から {len(form_emails)} 件のメールアドレスを抽出しました")
                for email_info in form_emails:
                    # 既に抽出済みのメールアドレスはスキップ
                    if email_info['email'] in [e['email'] for e in result['emails']]:
                        continue

                    result['emails'].append(email_info)

                # 有効なメールアドレスがあれば、優先順位2.5で終了（信頼度が低い場合は探索を続ける）
                valid_emails = [e for e in result['emails'] if e['confidence'] >= 0.5]
                if valid_emails:
                    result['extraction_method'] = 'contact_form_analysis'
                    result['best_email'] = self.select_best_email(valid_emails)
                    # 信頼度が0.5以上だが0.8未満の場合は探索を続ける
                    if result['best_email']['confidence'] >= 0.8:
                        return result
                    else:
                        logging.info(f"{company_name}: 問い合わせフォーム解析から信頼度の低いメールアドレスが見つかりましたが、探索を続けます")

        # 優先順位2.7: 自動返信検出をスキップ（効率化のため）
        logging.info(f"{company_name}: 優先順位2.7 - 自動返信検出をスキップします（効率化のため）")

        # 優先順位3: 関連ページの深い探索（拡張版）
        # 信頼度の高いメールアドレスが見つかっていない場合、または信頼度が低いメールアドレスしか見つかっていない場合は探索を続ける
        if not any(e['confidence'] >= 0.8 for e in result['emails']):
            logging.info(f"{company_name}: 優先順位3 - 関連ページの戦略的拡大探索（並列処理）")

            # 拡張された深い探索を実行（高速化設定：ページ数とワーカー数を削減）
            deep_emails = self.deep_crawl_for_emails(url, max_pages=5, max_workers=3, adaptive_depth=True)

            if deep_emails:
                logging.info(f"{company_name}: 戦略的拡大探索から {len(deep_emails)} 件のメールアドレスを抽出しました")
                for email in deep_emails:
                    # 既に抽出済みのメールアドレスはスキップ
                    if email in [e['email'] for e in result['emails']]:
                        continue

                    # 検証（企業ドメインとの一致チェック付き）
                    verification = self.verify_email(email, domain)
                    verification['source'] = 'deep_crawl'
                    result['emails'].append(verification)

            # 有効なメールアドレスがあれば、優先順位3で終了
            valid_emails = [e for e in result['emails'] if e['confidence'] >= 0.5]
            if valid_emails:
                result['extraction_method'] = 'deep_crawl'
                result['best_email'] = self.select_best_email(valid_emails)
                return result

            # 特定のページタイプからのメールアドレス抽出を試みる
            logging.info(f"{company_name}: 優先順位4 - 特定ページタイプからの抽出")
            contact_pages = self.find_contact_pages(url)

            # 新しく追加されたページタイプを優先的に探索
            special_page_types = ['news', 'privacy', 'terms', 'recruit', 'ir', 'sitemap', 'blog']
            special_pages = [page for page in contact_pages if page['type'] in special_page_types]

            if special_pages:
                logging.info(f"{company_name}: {len(special_pages)} 件の特殊ページを発見")
                for page in special_pages:
                    page_url = page['url']
                    page_type = page['type']

                    logging.info(f"{company_name}: {page_type} ページを分析中: {page_url}")
                    page_response = self.fetch_url(page_url)
                    if page_response:
                        page_emails = self.extract_emails_from_html(page_response.text, page_url)
                        if page_emails:
                            logging.info(f"{company_name}: {page_type} ページから {len(page_emails)} 件のメールアドレスを抽出しました")
                            for email in page_emails:
                                # 既に抽出済みのメールアドレスはスキップ
                                if email in [e['email'] for e in result['emails']]:
                                    continue

                                # 検証
                                verification = self.verify_email(email)
                                verification['source'] = page_type
                                result['emails'].append(verification)

            # 有効なメールアドレスがあれば終了
            valid_emails = [e for e in result['emails'] if e['confidence'] >= 0.5]
            if valid_emails:
                result['extraction_method'] = 'special_pages'
                result['best_email'] = self.select_best_email(valid_emails)
                return result

            # 優先順位5: JavaScriptによる動的生成メールアドレスの抽出
            if self.use_dynamic_extraction:
                logging.info(f"{company_name}: 優先順位5 - 動的レンダリングによるメールアドレス抽出")

                # トップページの動的レンダリング
                dynamic_emails = self.extract_emails_with_dynamic_rendering(url)
                if dynamic_emails:
                    logging.info(f"{company_name}: 動的レンダリングから {len(dynamic_emails)} 件のメールアドレスを抽出しました")
                    for email in dynamic_emails:
                        # 既に抽出済みのメールアドレスはスキップ
                        if email in [e['email'] for e in result['emails']]:
                            continue

                        # 検証
                        verification = self.verify_email(email)
                        verification['source'] = 'dynamic_rendering'
                        result['emails'].append(verification)

                # お問い合わせページの動的レンダリング
                contact_pages = self.find_contact_pages(url)
                contact_urls = [page['url'] for page in contact_pages if page['type'] == 'contact']

                if contact_urls:
                    for contact_url in contact_urls[:2]:  # 最大2つのお問い合わせページを試行
                        logging.info(f"{company_name}: お問い合わせページの動的レンダリング: {contact_url}")
                        contact_dynamic_emails = self.extract_emails_with_dynamic_rendering(contact_url)

                        if contact_dynamic_emails:
                            logging.info(f"{company_name}: お問い合わせページの動的レンダリングから {len(contact_dynamic_emails)} 件のメールアドレスを抽出しました")
                            for email in contact_dynamic_emails:
                                # 既に抽出済みのメールアドレスはスキップ
                                if email in [e['email'] for e in result['emails']]:
                                    continue

                                # 検証
                                verification = self.verify_email(email)
                                verification['source'] = 'dynamic_contact'
                                result['emails'].append(verification)

                # 有効なメールアドレスがあれば終了
                valid_emails = [e for e in result['emails'] if e['confidence'] >= 0.5]
                if valid_emails:
                    result['extraction_method'] = 'dynamic_rendering'
                    result['best_email'] = self.select_best_email(valid_emails)
                    return result

        # 優先順位6: 機械的メール生成（SMTP検証なし）
        logging.info(f"{company_name}: 優先順位6 - 機械的メール生成（info@ドメイン）")

        # info@ドメインを機械的に生成
        generated_email = f"info@{domain}"
        logging.info(f"{company_name}: 機械的に生成されたメールアドレス: {generated_email}")

        # SMTP検証をスキップして、機械的に生成されたメールアドレスを追加
        generated_verification = {
            'email': generated_email,
            'confidence': 0.6,  # 機械的生成なので中程度の信頼度
            'smtp_valid': None,  # SMTP検証をスキップ
            'is_catch_all': None,
            'is_role_based': True,
            'source': 'generated_mechanical',
            'details': 'SMTP検証をスキップして機械的に生成',
            'verification_level': 'mechanical',
            'response_message': 'SMTP検証省略'
        }

        result['emails'].append(generated_verification)
        logging.info(f"{company_name}: 機械的生成メールアドレス {generated_email} を追加しました")

        # 最適なメールアドレスの選定
        valid_emails = [e for e in result['emails'] if e['confidence'] >= 0.5]
        if valid_emails:
            result['best_email'] = self.select_best_email(valid_emails)
            result['extraction_method'] = 'combined'
        else:
            # 有効なメールアドレスがない場合は、最も信頼度の高いものを選択
            if result['emails']:
                result['best_email'] = self.select_best_email(result['emails'])
                result['extraction_method'] = 'low_confidence'

        return result

    def detect_autoreply_address_from_form(self, url, company_name):
        """お問い合わせフォーム送信による自動返信アドレス特定"""
        try:
            # 自動返信検出器が設定されている場合のみ実行
            if not hasattr(self, 'autoreply_detector') or not self.autoreply_detector:
                logging.info(f"{company_name}: 自動返信検出器が設定されていません")
                return None

            # 自動返信アドレスを特定
            result = self.autoreply_detector.detect_autoreply_address(company_name, url)

            if result:
                logging.info(f"{company_name}: 自動返信アドレス特定成功 - {result['autoreply_address']}")
                return result
            else:
                logging.warning(f"{company_name}: 自動返信アドレスを特定できませんでした")
                return None

        except Exception as e:
            logging.error(f"{company_name}: 自動返信アドレス特定エラー: {e}")
            return None

    def set_autoreply_detector(self, monitoring_email_config):
        """自動返信検出器を設定"""
        try:
            from contact_form_autoreply_detector import ContactFormAutoReplyDetector
            self.autoreply_detector = ContactFormAutoReplyDetector(monitoring_email_config)
            self.use_autoreply_detection = True
            logging.info("自動返信検出器を設定しました")
        except ImportError as e:
            logging.error(f"自動返信検出器のインポートに失敗: {e}")
            self.autoreply_detector = None
            self.use_autoreply_detection = False
        except Exception as e:
            logging.error(f"自動返信検出器の設定に失敗: {e}")
            self.autoreply_detector = None
            self.use_autoreply_detection = False

    # バウンス処理関連のメソッドは独立システムに移行
    # handle_bounce_with_form_submission は independent_contact_form_processor.py で処理

    def select_best_email(self, emails):
        """最も信頼性の高いメールアドレスを選定"""
        if not emails:
            return None

        # postmasterアドレスを除外
        filtered_emails = []
        for email in emails:
            email_addr = email.get('email', '')
            if email_addr and email_addr.split('@')[0].lower() == 'postmaster':
                logging.info(f"postmasterアドレスを除外: {email_addr}")
                continue
            filtered_emails.append(email)

        if not filtered_emails:
            return None

        # 以降の処理では、postmasterを除外したリストを使用
        emails = filtered_emails

        # ソース（抽出方法）による優先順位
        source_priority = {
            'footer': 10,
            'homepage': 9,
            'contact_form_analysis': 8.5,  # 問い合わせフォーム解析を高優先度に設定
            'contact': 8,
            'about': 7,
            'generated_common_prefix': 6,
            'generated_company_name': 5
        }

        # 優先順位ランクを持つメールアドレスを優先
        # 優先順位ランクが低いほど優先度が高い（1位が最も優先）
        prioritized_emails = [e for e in emails if 'priority_rank' in e]
        if prioritized_emails:
            # 優先順位ランクでソート（昇順）
            return sorted(
                prioritized_emails,
                key=lambda e: (
                    e.get('priority_rank', 999),  # 優先順位ランク（低いほど優先）
                    -e.get('confidence', 0.0)     # 信頼度（高いほど優先）
                )
            )[0]

        # SMTP検証成功のメールアドレスを優先
        smtp_valid_emails = [e for e in emails if e.get('smtp_valid', False)]
        if smtp_valid_emails:
            # SMTP検証成功の中で、キャッチオールでないものを優先
            non_catchall_emails = [e for e in smtp_valid_emails if not e.get('is_catch_all', False)]
            if non_catchall_emails:
                # ソースと信頼度でソート
                return sorted(
                    non_catchall_emails,
                    key=lambda e: (
                        source_priority.get(e.get('source', ''), 0),
                        e.get('confidence', 0.0)
                    ),
                    reverse=True
                )[0]
            # キャッチオールしかない場合
            return sorted(
                smtp_valid_emails,
                key=lambda e: (
                    source_priority.get(e.get('source', ''), 0),
                    e.get('confidence', 0.0)
                ),
                reverse=True
            )[0]

        # SMTP検証成功がない場合、信頼度とソースでソート
        return sorted(
            emails,
            key=lambda e: (
                e.get('confidence', 0.0),
                source_priority.get(e.get('source', ''), 0)
            ),
            reverse=True
        )[0]

def load_companies_from_csv(file_path, start_id=None, end_id=None):
    """CSVファイルから企業情報を読み込む

    Args:
        file_path: CSVファイルのパス
        start_id: 開始ID（1から始まる）
        end_id: 終了ID（1から始まる）
    """
    companies = []

    # 試すエンコーディングのリスト（より包括的に）
    encodings = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932', 'euc_jp', 'iso2022_jp', 'latin1']

    successful_encoding = None
    file_content = None

    # chardetライブラリを使用してエンコーディングを自動検出
    try:
        import chardet
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            detected = chardet.detect(raw_data)
            if detected['encoding'] and detected['confidence'] > 0.7:
                detected_encoding = detected['encoding']
                logging.info(f"chardetによる検出結果: {detected_encoding} (信頼度: {detected['confidence']:.2f})")
                # 検出されたエンコーディングを最初に試す
                if detected_encoding not in encodings:
                    encodings.insert(0, detected_encoding)
                else:
                    # 既にリストにある場合は最初に移動
                    encodings.remove(detected_encoding)
                    encodings.insert(0, detected_encoding)
    except ImportError:
        logging.info("chardetライブラリが利用できません。手動でエンコーディングを試行します。")
    except Exception as e:
        logging.warning(f"chardetによるエンコーディング検出中にエラー: {e}")

    # 各エンコーディングを試す
    for encoding in encodings:
        try:
            logging.info(f"エンコーディング {encoding} でファイル '{file_path}' を読み込み中...")
            with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                file_content = f.read()
                successful_encoding = encoding
                logging.info(f"エンコーディング {encoding} で正常に読み込みました")
                break
        except UnicodeDecodeError as e:
            logging.warning(f"エンコーディング {encoding} では読み込めませんでした: {e}")
            continue
        except Exception as e:
            logging.error(f"エンコーディング {encoding} での読み込み中にエラー: {e}")
            continue

    # すべてのエンコーディングで失敗した場合、エラーを無視して読み込む
    if not successful_encoding:
        logging.warning("すべてのエンコーディングで失敗しました。エラーを無視してUTF-8で読み込みます。")
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_content = f.read()
                successful_encoding = 'utf-8 (errors ignored)'
                logging.info("UTF-8（エラー無視）で読み込みました")
        except Exception as e:
            logging.error(f"最終的な読み込み試行でもエラー: {e}")
            return []

    if not successful_encoding:
        logging.error(f"ファイル '{file_path}' を読み込めませんでした")
        return []

    try:
        # 成功したエンコーディングでCSVを解析
        from io import StringIO
        csv_file = StringIO(file_content)

        # CSVファイルの最初の行を読み込んでカラム名を確認
        first_line = file_content.split('\n')[0].strip()
        csv_file.seek(0)  # ファイルポインタを先頭に戻す

        # カラム名が指定されていない場合は、最初のカラムを企業名として扱う
        if '企業名' not in first_line:
            logging.info("CSVファイルにカラム名「企業名」が見つかりません。最初のカラムを企業名として扱います。")
            reader = csv.reader(csv_file)
            header = next(reader)  # ヘッダー行をスキップ

            for i, row in enumerate(reader):
                if not row:  # 空行をスキップ
                    continue

                # 1から始まるIDを割り当て
                company_id = i + 1

                # IDの範囲が指定されている場合はフィルタリング
                if start_id is not None and company_id < start_id:
                    continue
                if end_id is not None and company_id > end_id:
                    continue

                company_data = {
                    'id': str(company_id),
                    '企業名': row[0] if len(row) > 0 else '',
                    'URL': row[1] if len(row) > 1 else '',
                    '企業URL': row[1] if len(row) > 1 else ''  # 互換性のため
                }

                # 企業名が存在することを確認
                if not company_data['企業名']:
                    logging.warning(f"ID {company_id} の企業名が見つかりません")

                companies.append(company_data)
        else:
            # 通常のDictReaderを使用
            reader = csv.DictReader(csv_file)
            for i, row in enumerate(reader):
                # 1から始まるIDを割り当て
                company_id = i + 1
                row['id'] = str(company_id)

                # 企業URL列をURL列にマッピング（互換性のため）
                if '企業URL' in row and 'URL' not in row:
                    row['URL'] = row['企業URL']

                # IDの範囲が指定されている場合はフィルタリング
                if start_id is not None and company_id < start_id:
                    continue
                if end_id is not None and company_id > end_id:
                    continue

                # 企業名が存在することを確認
                if '企業名' not in row or not row['企業名']:
                    logging.warning(f"ID {company_id} の企業名が見つかりません")

                companies.append(row)

        if start_id is not None or end_id is not None:
            id_range = f"ID {start_id or 1} から {end_id or '最後'} までの "
        else:
            id_range = ""

        logging.info(f"{id_range}{len(companies)}社の情報を読み込みました")

        # 企業名のカラムを確認
        if companies:
            logging.info(f"CSVファイルのカラム: {', '.join(companies[0].keys())}")

        return companies
    except Exception as e:
        logging.error(f"CSVファイルの読み込みエラー: {e}")
        logging.error(traceback.format_exc())
        return []

def save_results_to_csv(results, output_file):
    """結果をCSVファイルに保存"""
    try:
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            fieldnames = [
                '企業ID', '企業名', 'URL', 'ドメイン', 'メールアドレス', '抽出方法',
                '信頼度', '検証レベル', 'SMTP検証', 'キャッチオール',
                'ロールベース', '詳細'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                company_name = result.get('company_name', '')
                url = result.get('url', '')
                domain = result.get('domain', '') or ''
                best_email = result.get('best_email')
                extraction_method = result.get('extraction_method', '') or ''
                # 企業IDを取得（複数のキーをチェック）
                company_id = result.get('company_id', result.get('id', result.get('企業ID', '')))

                # 企業名が空の場合はログに出力
                if not company_name:
                    logging.warning(f"企業ID {company_id} の企業名が空です")

                row = {
                    '企業ID': company_id,
                    # 'id': company_id,  # 互換性のために両方のキーで保存 - fieldnamesに含まれていないためエラーの原因
                    '企業名': company_name,
                    'URL': url,
                    'ドメイン': domain
                }

                logging.info(f"企業ID {company_id}: {company_name} の結果をCSVに保存します")

                if best_email:
                    row['メールアドレス'] = best_email['email']
                    row['抽出方法'] = best_email.get('source', extraction_method)
                    row['信頼度'] = f"{best_email.get('confidence', 0.0):.2f}"
                    row['検証レベル'] = best_email.get('verification_level', '')
                    row['SMTP検証'] = 'はい' if best_email.get('smtp_valid', False) else 'いいえ'
                    row['キャッチオール'] = 'はい' if best_email.get('is_catch_all', False) else 'いいえ'
                    row['ロールベース'] = 'はい' if best_email.get('is_role_based', False) else 'いいえ'
                    row['詳細'] = best_email.get('details', '')
                else:
                    row['メールアドレス'] = ''
                    row['抽出方法'] = ''
                    row['信頼度'] = ''
                    row['検証レベル'] = ''
                    row['SMTP検証'] = ''
                    row['キャッチオール'] = ''
                    row['ロールベース'] = ''
                    row['詳細'] = '抽出失敗'

                writer.writerow(row)

        logging.info(f"結果を {output_file} に保存しました")
        return True
    except Exception as e:
        logging.error(f"CSVファイルの保存エラー: {e}")
        return False

def main():
    """メイン関数"""
    import argparse

    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='優先順位に基づくメールアドレス抽出')
    parser.add_argument('--start-id', type=int, help='開始企業ID（1から始まる）')
    parser.add_argument('--end-id', type=int, help='終了企業ID（1から始まる）')
    parser.add_argument('--input-file', default='data/derivative_input.csv', help='入力CSVファイル')
    parser.add_argument('--random', action='store_true', help='ランダムに10社を選択する')
    parser.add_argument('--no-dynamic', action='store_true', help='動的メール抽出を無効化する')
    args = parser.parse_args()

    # 現在の時刻を取得（ファイル名用）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 出力ファイル名
    if args.start_id is not None or args.end_id is not None:
        id_suffix = f"_id{args.start_id or 1}-{args.end_id or 'end'}"
    else:
        id_suffix = ""
    output_file = f"derivative_email_extraction_results{id_suffix}_{timestamp}.csv"

    # IDの範囲が指定されている場合はログに出力
    if args.start_id is not None or args.end_id is not None:
        id_range = f"ID {args.start_id or 1} から {args.end_id or '最後'} までの"
        logging.info(f"{id_range} 企業を処理します")

    # CSVファイルを読み込む
    input_file_path = args.input_file
    if not os.path.exists(input_file_path):
        # 相対パスで試す
        input_file_path = os.path.join(os.getcwd(), args.input_file)
        if not os.path.exists(input_file_path):
            logging.error(f"入力ファイル {args.input_file} が見つかりません。終了します。")
            return

    logging.info(f"入力ファイル {input_file_path} を読み込みます")
    companies = load_companies_from_csv(input_file_path, start_id=args.start_id, end_id=args.end_id)
    if not companies:
        logging.error("企業情報を読み込めませんでした。終了します。")
        return

    # URLが指定されている企業のみをフィルタリング
    valid_companies = [company for company in companies if company.get('URL') and company.get('URL') != '-']
    logging.info(f"URLが指定されている企業: {len(valid_companies)}社")

    # ランダムに10社を選択するオプションが指定されている場合
    if args.random and len(valid_companies) > 10:
        selected_companies = random.sample(valid_companies, 10)
        logging.info(f"ランダムに10社を選択しました")
    else:
        selected_companies = valid_companies
        logging.info(f"全{len(valid_companies)}社を処理します")

    # メールアドレス抽出器を初期化（動的メール抽出機能付き）
    extractor = PrioritizedEmailExtractor(use_dynamic_extraction=not args.no_dynamic)

    if args.no_dynamic:
        logging.info("動的メール抽出機能は無効化されています")
    else:
        logging.info("動的メール抽出機能が有効です")

    # 各企業のメールアドレスを抽出
    results = []
    try:
        for i, company in enumerate(selected_companies):
            company_name = company.get('企業名', '')
            url = company.get('URL', '')
            company_id = company.get('id', '')

            logging.info(f"\n企業 {i+1}/{len(selected_companies)}: {company_name} (ID: {company_id})")

            # 企業名が空の場合はログに出力
            if not company_name:
                logging.warning(f"ID {company_id} の企業名が空です。CSVファイルを確認してください。")

            result = extractor.extract_emails_with_priority(company_name, url, company_id)
            results.append(result)

            # 結果を表示
            if result['best_email']:
                email = result['best_email']['email']
                confidence = result['best_email']['confidence']
                source = result['best_email'].get('source', result['extraction_method'])
                logging.info(f"{company_name}: メールアドレス {email} を抽出しました（信頼度: {confidence:.2f}, 抽出方法: {source}）")
            else:
                logging.info(f"{company_name}: メールアドレスを抽出できませんでした")

            # サーバーに負荷をかけないよう少し待機（高速化のため待機時間をさらに短縮）
            if i < len(selected_companies) - 1:
                wait_time = random.uniform(0.1, 0.3)
                logging.info(f"次の企業の分析まで{wait_time:.1f}秒待機します...")
                time.sleep(wait_time)
    finally:
        # 動的メール抽出器のクリーンアップ
        if extractor.use_dynamic_extraction and extractor.dynamic_extractor:
            try:
                extractor.dynamic_extractor.close_driver()
                logging.info("動的メール抽出器のドライバーを正常に終了しました")
            except Exception as e:
                logging.error(f"動的メール抽出器のドライバー終了中にエラーが発生しました: {e}")

    # 結果サマリーを表示
    print("\n===== 抽出結果サマリー =====")
    success_count = sum(1 for r in results if r['best_email'] and r['best_email']['confidence'] >= 0.5)
    low_confidence_count = sum(1 for r in results if r['best_email'] and r['best_email']['confidence'] < 0.5)
    failure_count = sum(1 for r in results if not r['best_email'])

    print(f"処理企業数: {len(results)}")
    if len(results) > 0:
        print(f"メールアドレス抽出成功: {success_count} ({success_count/len(results)*100:.1f}%)")
        print(f"低信頼度メールアドレス: {low_confidence_count} ({low_confidence_count/len(results)*100:.1f}%)")
        print(f"抽出失敗: {failure_count} ({failure_count/len(results)*100:.1f}%)")
    else:
        print("処理対象の企業がありませんでした。")

    # 抽出方法の統計
    extraction_methods = {}
    for result in results:
        if result['best_email']:
            method = result['best_email'].get('source', result['extraction_method'])
            extraction_methods[method] = extraction_methods.get(method, 0) + 1

    print("\n抽出方法の内訳:")
    if len(results) > 0:
        for method, count in sorted(extraction_methods.items(), key=lambda x: x[1], reverse=True):
            print(f"  {method}: {count}件 ({count/len(results)*100:.1f}%)")
    else:
        print("  データがありません")

    # 詳細結果を表示
    print("\n===== 詳細結果 =====")
    for result in results:
        company_name = result['company_name']
        best_email = result['best_email']

        if best_email:
            email = best_email['email']
            confidence = best_email['confidence']
            source = best_email.get('source', result['extraction_method'])
            verification_level = best_email.get('verification_level', '')

            status = "有効" if confidence >= 0.5 else "低信頼度"
            print(f"{company_name}: {email} ({status}, 信頼度: {confidence:.2f}, 抽出方法: {source}, 検証レベル: {verification_level})")
        else:
            print(f"{company_name}: 抽出失敗")

    # 結果をCSVファイルに保存
    save_results_to_csv(results, output_file)

if __name__ == "__main__":
    main()
