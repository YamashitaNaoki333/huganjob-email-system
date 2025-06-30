#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
派生版ウェブサイト分析スクリプト
- 派生版ファイル命名規則を使用: derivative_website_analysis_results_*.csv
- derivative_input.csv を入力ファイルとして使用
- 元システムとの完全分離
- URL正規化: 常にトップページを評価対象とする
- Selenium導入: JavaScript実行後のHTMLを解析
- 評価配点: UX30点 + デザイン40点 + 技術30点 = 最大100点
- ランク基準: A(65点以上) B(55-64点) C(55点以下) - 辛口評価
"""

import csv
import sys
import os
import logging
import argparse
import requests
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Selenium関連のインポート
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logging.warning("Seleniumが利用できません。BeautifulSoupのみで動作します。")

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("new_website_analysis.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('new_website_analyzer')

# 派生版システム用の設定
INPUT_FILE = 'data/derivative_input.csv'
OUTPUT_FILE_PREFIX = 'derivative_website_analysis_results'

class WebsiteAnalyzer:
    """ウェブサイト分析クラス"""

    def __init__(self, timeout=30, use_selenium=True):
        self.timeout = timeout
        self.page_load_timeout = min(timeout, 30)  # ページ読み込み専用タイムアウト
        self.implicit_wait = 10  # 要素待機タイムアウト
        self.use_selenium = use_selenium and SELENIUM_AVAILABLE
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # Seleniumドライバーの初期化（遅延初期化）
        self.driver = None

        if self.use_selenium:
            logger.info(f"Selenium機能が有効です（JavaScript対応）- タイムアウト: {self.timeout}秒")
        else:
            logger.info("BeautifulSoupのみで動作します（静的HTML解析）")

    def normalize_url(self, url):
        """URLを正規化してトップページのURLを取得"""
        if not url or url.strip() == '':
            return url

        # httpスキームを追加
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            # URLをパース
            parsed_url = urlparse(url)

            # スキームとネットロケーションを取得（ドメイン部分）
            scheme = parsed_url.scheme
            netloc = parsed_url.netloc

            # トップページのURLを構築
            homepage_url = f"{scheme}://{netloc}/"

            # 元のURLがトップページと異なる場合は通知
            if url != homepage_url and url != homepage_url[:-1]:
                logger.info(f"サブページURLをトップページに変換: {url} -> {homepage_url}")

            return homepage_url

        except Exception as e:
            logger.warning(f"URL正規化エラー: {url} - {e}")
            return url

    def get_selenium_driver(self):
        """Seleniumドライバーを取得（遅延初期化）"""
        if not self.use_selenium:
            return None

        if self.driver is None:
            try:
                chrome_options = Options()
                chrome_options.add_argument('--headless')  # ヘッドレスモード
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument('--disable-web-security')  # セキュリティ無効化
                chrome_options.add_argument('--disable-features=VizDisplayCompositor')  # 安定性向上
                chrome_options.add_argument('--disable-extensions')  # 拡張機能無効化
                chrome_options.add_argument('--disable-plugins')  # プラグイン無効化
                chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

                self.driver = webdriver.Chrome(options=chrome_options)

                # 複数のタイムアウト設定
                self.driver.set_page_load_timeout(self.page_load_timeout)  # ページ読み込みタイムアウト
                self.driver.implicitly_wait(self.implicit_wait)  # 要素待機タイムアウト

                logger.info(f"Seleniumドライバーを初期化しました (ページ読み込み: {self.page_load_timeout}秒, 要素待機: {self.implicit_wait}秒)")

            except Exception as e:
                logger.error(f"Seleniumドライバーの初期化に失敗: {e}")
                self.use_selenium = False
                return None

        return self.driver

    def get_html_with_selenium(self, url):
        """SeleniumでJavaScript実行後のHTMLを取得（タイムアウト強化版）"""
        driver = self.get_selenium_driver()
        if not driver:
            return None

        try:
            logger.info(f"Seleniumでページを取得中: {url} (タイムアウト: {self.page_load_timeout}秒)")

            # ページ取得の開始時間を記録
            start_time = time.time()

            # ページを取得
            driver.get(url)

            # ページの読み込み完了を待機（短いタイムアウト）
            try:
                WebDriverWait(driver, min(self.implicit_wait, 15)).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                logger.warning(f"body要素の待機がタイムアウト: {url}")
                # body要素が見つからなくても続行

            # 最小限の待機時間（JavaScriptの実行完了）
            time.sleep(1)

            # HTMLソースを取得
            html_source = driver.page_source
            elapsed_time = time.time() - start_time
            logger.info(f"Seleniumでページ取得完了: {len(html_source)}文字 ({elapsed_time:.1f}秒)")

            return html_source

        except TimeoutException:
            elapsed_time = time.time() - start_time if 'start_time' in locals() else 0
            logger.warning(f"Seleniumタイムアウト: {url} ({elapsed_time:.1f}秒経過)")
            return None
        except WebDriverException as e:
            logger.warning(f"Selenium WebDriverエラー: {url} - {e}")
            return None
        except Exception as e:
            logger.error(f"Selenium予期しないエラー: {url} - {e}")
            return None

    def get_html_with_requests(self, url):
        """requestsで静的HTMLを取得"""
        try:
            logger.info(f"requestsでページを取得中: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            logger.info(f"requestsでページ取得完了: {len(response.text)}文字")
            return response.text, response

        except requests.exceptions.Timeout:
            logger.warning(f"requestsタイムアウト: {url}")
            return None, None
        except requests.exceptions.ConnectionError:
            logger.warning(f"requests接続エラー: {url}")
            return None, None
        except Exception as e:
            logger.error(f"requests予期しないエラー: {url} - {e}")
            return None, None

    def analyze_website(self, company_name, url):
        """ウェブサイトを分析してスコアを算出"""
        try:
            logger.info(f"ウェブサイト分析開始: {company_name} - {url}")

            # URLの正規化（トップページに変換）
            normalized_url = self.normalize_url(url)

            # HTMLを取得（Selenium優先、フォールバックでrequests）
            html_content = None
            response = None

            # まずSeleniumで試行
            if self.use_selenium:
                html_content = self.get_html_with_selenium(normalized_url)

            # Seleniumが失敗した場合、またはSeleniumが無効な場合はrequestsを使用
            if html_content is None:
                html_content, response = self.get_html_with_requests(normalized_url)

            if html_content is None:
                logger.error(f"HTMLの取得に失敗: {company_name} - {normalized_url}")
                return self.create_error_result(company_name, normalized_url, 'html_fetch_error')

            # HTMLを解析
            soup = BeautifulSoup(html_content, 'html.parser')

            # responseオブジェクトが無い場合（Seleniumの場合）は疑似的なresponseオブジェクトを作成
            if response is None:
                class MockResponse:
                    def __init__(self, url):
                        self.url = url
                        # elapsed属性を作成
                        class MockElapsed:
                            def total_seconds(self):
                                return 2.0
                        self.elapsed = MockElapsed()
                response = MockResponse(normalized_url)

            # 各項目のスコアを計算
            ux_score = self.analyze_user_experience(soup, response)
            design_score = self.analyze_design_quality(soup)
            technical_score = self.analyze_technical_quality(soup, response)

            # 総合スコアを計算（単純合計）- UX30点 + デザイン40点 + 技術30点 = 最大100点
            total_score = ux_score + design_score + technical_score

            # ランクを決定（新基準：65%以上=A、55-64%=B、55%以下=C）
            if total_score >= 65:
                rank = 'A'  # 高評価（65%以上）
            elif total_score >= 55:
                rank = 'B'  # 中評価（55-64%）
            else:
                rank = 'C'  # 低評価（55%以下）

            result = {
                'company_name': company_name,
                'url': normalized_url,  # 正規化されたURLを記録
                'original_url': url,    # 元のURLも記録
                'ux_score': round(ux_score, 1),
                'design_score': round(design_score, 1),
                'technical_score': round(technical_score, 1),
                'total_score': round(total_score, 1),
                'rank': rank,
                'status': 'success',
                'analysis_method': 'selenium' if self.use_selenium and html_content else 'requests'
            }

            logger.info(f"分析完了: {company_name} - 総合スコア: {total_score:.1f} (ランク: {rank}) - 方法: {result['analysis_method']}")
            return result

        except Exception as e:
            logger.error(f"分析エラー: {company_name} - {url}: {e}")
            return self.create_error_result(company_name, url, 'analysis_error')

    def __del__(self):
        """デストラクタ - Seleniumドライバーをクリーンアップ"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Seleniumドライバーをクリーンアップしました")
            except Exception as e:
                logger.warning(f"Seleniumドライバーのクリーンアップエラー: {e}")

    def create_error_result(self, company_name, url, error_type):
        """エラー結果を作成"""
        return {
            'company_name': company_name,
            'url': url,
            'ux_score': 0,
            'design_score': 0,
            'technical_score': 0,
            'total_score': 0,
            'rank': 'C',
            'status': error_type
        }

    def analyze_user_experience(self, soup, response):
        """ユーザーエクスペリエンス分析（30%）- 改善版"""
        score = 0
        text_content = soup.get_text().lower()

        # 1. ページ読み込み速度（7点）
        if hasattr(response, 'elapsed'):
            response_time = response.elapsed.total_seconds()
            if response_time < 1:
                score += 7
            elif response_time < 2:
                score += 6
            elif response_time < 3:
                score += 4
            elif response_time < 5:
                score += 3
            else:
                score += 1

        # 2. ナビゲーション・メニュー構造（6点）
        nav_score = 0
        nav_elements = soup.find_all(['nav', 'header']) + soup.find_all(class_=lambda x: x and 'nav' in x.lower())
        if nav_elements:
            nav_score += 3
        # メニュー項目の数をチェック
        menu_items = soup.find_all(['a'])
        if len([a for a in menu_items if a.get_text().strip()]) >= 5:
            nav_score += 2
        # パンくずリストの存在
        if any(keyword in text_content for keyword in ['ホーム', 'home', '>', '»', 'breadcrumb']):
            nav_score += 1
        score += nav_score

        # 3. コンテンツの見つけやすさ（5点）
        content_score = 0
        # 見出し構造の確認
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if len(headings) >= 3:
            content_score += 2
        # 検索機能の存在
        search_elements = soup.find_all(['input'], type='search') + soup.find_all(class_=lambda x: x and 'search' in x.lower())
        if search_elements or 'search' in text_content or '検索' in text_content:
            content_score += 2
        # サイトマップやカテゴリ分類
        if any(keyword in text_content for keyword in ['サイトマップ', 'sitemap', 'カテゴリ', 'category']):
            content_score += 1
        score += content_score

        # 4. お問い合わせ・連絡手段（5点）
        contact_score = 0
        contact_keywords = ['お問い合わせ', 'contact', '連絡', 'tel', '電話', 'phone', 'mail', 'メール', 'email']
        if any(keyword in text_content for keyword in contact_keywords):
            contact_score += 2
        # 複数の連絡手段
        contact_methods = sum([
            'tel' in text_content or '電話' in text_content,
            'mail' in text_content or 'メール' in text_content or '@' in text_content,
            'form' in text_content or 'フォーム' in text_content,
            'chat' in text_content or 'チャット' in text_content
        ])
        if contact_methods >= 2:
            contact_score += 3
        score += contact_score

        # 5. 信頼性・透明性（4点）
        trust_score = 0
        # 会社情報の存在
        company_keywords = ['会社概要', 'about', '企業情報', '会社案内', '運営者情報']
        if any(keyword in text_content for keyword in company_keywords):
            trust_score += 2
        # プライバシーポリシー
        if any(keyword in text_content for keyword in ['プライバシー', 'privacy', '個人情報']):
            trust_score += 1
        # 利用規約
        if any(keyword in text_content for keyword in ['利用規約', 'terms', '規約']):
            trust_score += 1
        # 実績・事例は削除（デザイン性に移動）
        score += trust_score

        # 6. モバイル対応（3点）
        mobile_score = 0
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        if viewport_meta:
            mobile_score += 2
        # レスポンシブデザインの兆候
        css_links = soup.find_all('link', rel='stylesheet')
        for link in css_links:
            if link.get('media') and 'screen' in link.get('media'):
                mobile_score += 1
                break
        # モバイル向けメニューの存在は削除（デザイン性に移動）
        score += mobile_score

        return min(score, 30)  # 最大30点

    def analyze_design_quality(self, soup):
        """デザイン品質分析（40%）- 辛口評価版"""
        score = 0
        text_content = soup.get_text().lower()

        # 1. ビジュアルデザイン・レイアウト（16点）- 辛口評価
        visual_score = 0
        # CSSの存在と品質（より厳しい基準）
        css_links = soup.find_all('link', rel='stylesheet')
        if css_links:
            visual_score += 2  # 基本点を5→2に減点
            # 複数のCSSファイル（デザインの複雑さを示唆）
            if len(css_links) >= 3:  # 2→3に厳格化
                visual_score += 2  # 3→2に減点
            # 外部CSSフレームワークの使用（Bootstrap、Tailwindなど）
            css_content = str(soup)
            if any(framework in css_content.lower() for framework in ['bootstrap', 'tailwind', 'foundation', 'bulma']):
                visual_score += 1

        # レイアウト構造の確認（より厳しい基準）
        layout_elements = soup.find_all(['header', 'main', 'footer', 'aside', 'section'])
        if len(layout_elements) >= 4:  # 3→4に厳格化
            visual_score += 3  # 4→3に減点
        elif len(layout_elements) >= 2:
            visual_score += 1  # 部分点を追加

        # フォントの設定（より厳しい基準）
        font_indicators = [
            'font-family' in str(soup),
            any(font in str(soup).lower() for font in ['google fonts', 'web font', 'typekit']),
            any(font in str(soup).lower() for font in ['noto', 'roboto', 'open sans', 'lato', 'montserrat'])
        ]
        font_score = sum(font_indicators)
        if font_score >= 2:
            visual_score += 2  # 3→2に減点
        elif font_score >= 1:
            visual_score += 1

        # カラースキーム（より厳しい基準）
        color_indicators = [
            'color:' in str(soup),
            'background-color:' in str(soup),
            '#' in str(soup) and len([x for x in str(soup).split('#') if len(x) >= 3]) >= 3,  # 複数の色指定
            any(color in str(soup).lower() for color in ['rgb(', 'rgba(', 'hsl(', 'hsla('])
        ]
        if sum(color_indicators) >= 3:
            visual_score += 2
        elif sum(color_indicators) >= 1:
            visual_score += 1

        score += visual_score

        # 2. 画像・メディアの品質（10点）- 辛口評価
        media_score = 0
        images = soup.find_all('img')
        if len(images) > 0:
            media_score += 1  # 基本点を4→1に大幅減点

            # 画像の最適化（alt属性の存在）- より厳しい基準
            images_with_alt = [img for img in images if img.get('alt') and img.get('alt').strip()]
            alt_ratio = len(images_with_alt) / len(images) if len(images) > 0 else 0
            if alt_ratio >= 0.9:  # 90%以上にalt属性（70%→90%に厳格化）
                media_score += 3
            elif alt_ratio >= 0.7:
                media_score += 2  # 部分点を追加
            elif alt_ratio >= 0.5:
                media_score += 1

            # 適切な画像数（より厳しい基準）
            if 5 <= len(images) <= 12:  # 3-15→5-12に厳格化
                media_score += 2
            elif 3 <= len(images) <= 20:
                media_score += 1  # 部分点を追加

            # 画像の最適化指標（新規追加）
            optimization_score = 0
            # 画像のサイズ指定
            images_with_size = [img for img in images if img.get('width') or img.get('height')]
            if len(images_with_size) >= len(images) * 0.7:  # 0.5→0.7に厳格化
                optimization_score += 1

            # レスポンシブ画像（srcset属性）
            images_with_srcset = [img for img in images if img.get('srcset')]
            if len(images_with_srcset) >= len(images) * 0.3:  # 30%以上でsrcset
                optimization_score += 1

            # 画像の遅延読み込み
            lazy_images = [img for img in images if img.get('loading') == 'lazy' or 'lazy' in str(img.get('class', ''))]
            if len(lazy_images) >= len(images) * 0.3:  # 30%以上で遅延読み込み
                optimization_score += 1

            media_score += optimization_score

        score += media_score

        # 3. ブランディング・一貫性（8点）- 辛口評価
        brand_score = 0

        # ロゴの存在（より厳しい基準）
        logo_indicators = [
            len(soup.find_all(class_=lambda x: x and 'logo' in x.lower())) > 0,
            len(soup.find_all('img', alt=lambda x: x and x and 'logo' in x.lower())) > 0,
            len(soup.find_all('img', src=lambda x: x and 'logo' in x.lower())) > 0,
            len(soup.find_all(id=lambda x: x and 'logo' in x.lower())) > 0
        ]
        logo_score = sum(logo_indicators)
        if logo_score >= 2:  # 複数の指標でロゴを確認
            brand_score += 2  # 3→2に減点
        elif logo_score >= 1:
            brand_score += 1

        # 企業名・ブランド名の表示（より厳しい基準）
        title = soup.find('title')
        brand_name_score = 0
        if title and title.get_text().strip():
            title_text = title.get_text().strip()
            # タイトルの品質チェック
            if len(title_text) >= 10 and len(title_text) <= 60:  # 適切な長さ
                brand_name_score += 1
            if any(keyword in title_text.lower() for keyword in ['株式会社', '会社', 'company', 'corp', 'inc']):
                brand_name_score += 1
        brand_score += brand_name_score

        # 統一感のあるデザイン要素（より厳しい基準）
        design_consistency_score = 0
        # CSSクラスの体系的使用
        class_attrs = [elem.get('class', []) for elem in soup.find_all() if elem.get('class')]
        unique_classes = set()
        for classes in class_attrs:
            if isinstance(classes, list):
                unique_classes.update(classes)
            else:
                unique_classes.add(classes)

        if len(unique_classes) >= 10:  # 十分なCSSクラス使用
            design_consistency_score += 1

        # カラーパレットの一貫性（CSS変数の使用など）
        if any(indicator in str(soup) for indicator in ['--', 'var(', ':root']):
            design_consistency_score += 1

        # コンポーネント化の兆候
        if len([elem for elem in soup.find_all() if elem.get('class') and
               any(comp in str(elem.get('class')).lower() for comp in ['btn', 'button', 'card', 'modal', 'nav'])]) >= 3:
            design_consistency_score += 1

        brand_score += design_consistency_score

        # ナビゲーションの一貫性（より厳しい基準）
        nav_elements = soup.find_all(['nav'])  # navタグのみに限定
        structured_nav = soup.find_all(['ul', 'ol'])
        nav_quality_score = 0

        if len(nav_elements) >= 1:
            nav_quality_score += 1
        # 構造化されたナビゲーション
        if len(structured_nav) >= 2:
            nav_quality_score += 1

        brand_score += min(nav_quality_score, 1)  # 最大1点

        score += brand_score

        # 4. 現代的なデザイン要素（6点）- 辛口評価
        modern_score = 0

        # レスポンシブデザイン（より厳しい基準）
        responsive_indicators = [
            soup.find('meta', attrs={'name': 'viewport'}) is not None,
            any(media in str(soup) for media in ['@media', 'media=']),
            any(responsive in str(soup).lower() for responsive in ['responsive', 'mobile-first', 'breakpoint'])
        ]
        responsive_score = sum(responsive_indicators)
        if responsive_score >= 3:
            modern_score += 2  # 3→2に減点
        elif responsive_score >= 2:
            modern_score += 1

        # モダンなHTML5要素の使用（より厳しい基準）
        html5_elements = soup.find_all(['article', 'section', 'aside', 'nav', 'header', 'footer', 'main'])
        semantic_score = 0
        if len(html5_elements) >= 4:  # 2→4に厳格化
            semantic_score += 2  # 2→2維持
        elif len(html5_elements) >= 2:
            semantic_score += 1
        modern_score += semantic_score

        # インタラクティブ要素（より厳しい基準）
        interactive_elements = soup.find_all(['button', 'input', 'select', 'textarea'])
        advanced_interactive = soup.find_all(attrs={'onclick': True}) + \
                              soup.find_all(class_=lambda x: x and any(js in str(x).lower() for js in ['js-', 'interactive', 'toggle', 'dropdown']))

        interactive_score = 0
        if len(interactive_elements) >= 3 and len(advanced_interactive) >= 1:  # より高い基準
            interactive_score += 1
        modern_score += interactive_score

        # モバイル向けメニューの存在（UXから移動）
        mobile_menu_indicators = [
            any(keyword in str(soup).lower() for keyword in ['mobile-menu', 'hamburger', 'toggle-menu']),
            any(keyword in str(soup).lower() for keyword in ['menu-toggle', 'nav-toggle', 'burger']),
            len(soup.find_all(class_=lambda x: x and 'menu' in str(x).lower() and 'mobile' in str(x).lower())) > 0
        ]
        if sum(mobile_menu_indicators) >= 2:  # より厳しい基準
            modern_score += 1

        score += modern_score

        # 5. 実績・事例・コンテンツ充実度（UXから移動）（4点）- 辛口評価
        content_richness_score = 0

        # 実績・事例（より厳しい基準）
        portfolio_indicators = [
            any(keyword in text_content for keyword in ['実績', '事例', 'case study', '導入事例']),
            any(keyword in text_content for keyword in ['portfolio', 'works', '制作実績', 'project']),
            len(soup.find_all(class_=lambda x: x and any(p in str(x).lower() for p in ['portfolio', 'case', 'work']))) > 0
        ]
        if sum(portfolio_indicators) >= 2:  # 複数の指標で確認
            content_richness_score += 1  # 2→1に減点

        # ニュース・ブログ（より厳しい基準）
        news_indicators = [
            any(keyword in text_content for keyword in ['ニュース', 'news', 'お知らせ']),
            any(keyword in text_content for keyword in ['ブログ', 'blog', '記事']),
            any(keyword in text_content for keyword in ['更新', 'update', '最新'])
        ]
        if sum(news_indicators) >= 2:  # より厳しい基準
            content_richness_score += 1

        # サービス・製品紹介（より厳しい基準）
        service_indicators = [
            any(keyword in text_content for keyword in ['サービス', 'service', 'ソリューション']),
            any(keyword in text_content for keyword in ['製品', 'product', 'プロダクト']),
            any(keyword in text_content for keyword in ['事業内容', 'business', '業務内容'])
        ]
        if sum(service_indicators) >= 2:  # より厳しい基準
            content_richness_score += 1

        # 企業情報の充実度（新規追加）
        company_info_indicators = [
            any(keyword in text_content for keyword in ['会社概要', 'about us', '企業情報']),
            any(keyword in text_content for keyword in ['代表', 'ceo', '社長', '代表取締役']),
            any(keyword in text_content for keyword in ['沿革', 'history', '設立'])
        ]
        if sum(company_info_indicators) >= 3:  # 全ての指標で確認
            content_richness_score += 1

        score += content_richness_score

        return min(score, 40)  # 最大40点

    def analyze_technical_quality(self, soup, response):
        """技術品質分析（30%）- 改善版"""
        score = 0
        text_content = soup.get_text().lower()

        # 1. セキュリティ・プロトコル（8点）
        security_score = 0
        # HTTPSの使用
        if response.url.startswith('https://'):
            security_score += 4

        # セキュリティ関連のメタタグ
        security_headers = soup.find_all('meta', attrs={'http-equiv': lambda x: x and 'security' in x.lower()})
        if security_headers:
            security_score += 2

        # プライバシーポリシーの存在
        if any(keyword in text_content for keyword in ['プライバシー', 'privacy', '個人情報保護']):
            security_score += 2

        score += security_score

        # 2. SEO基礎対策（8点）
        seo_score = 0
        # タイトルタグ
        title = soup.find('title')
        if title and title.get_text().strip():
            title_text = title.get_text().strip()
            seo_score += 2
            # タイトルの長さが適切
            if 20 <= len(title_text) <= 60:
                seo_score += 1

        # メタディスクリプション
        description = soup.find('meta', attrs={'name': 'description'})
        if description and description.get('content'):
            desc_content = description.get('content')
            seo_score += 2
            # ディスクリプションの長さが適切
            if 80 <= len(desc_content) <= 160:
                seo_score += 1

        # 見出しタグの適切な使用
        h1_tags = soup.find_all('h1')
        if len(h1_tags) == 1:  # H1は1つが理想
            seo_score += 1

        # 画像のalt属性
        images = soup.find_all('img')
        if images:
            images_with_alt = [img for img in images if img.get('alt')]
            if len(images_with_alt) >= len(images) * 0.8:  # 80%以上
                seo_score += 1

        score += seo_score

        # 3. コード品質・構造（7点）
        code_score = 0
        # HTML5の基本構造
        if soup.find('html') and soup.find('head') and soup.find('body'):
            code_score += 2

        # セマンティックHTML5要素の使用
        semantic_elements = soup.find_all(['header', 'nav', 'main', 'article', 'section', 'aside', 'footer'])
        if len(semantic_elements) >= 3:
            code_score += 2

        # 構造化データ
        structured_data = soup.find_all(['script'], type='application/ld+json')
        if structured_data:
            code_score += 2

        # CSSとJavaScriptの外部ファイル化
        external_css = soup.find_all('link', rel='stylesheet')
        external_js = soup.find_all('script', src=True)
        if external_css and external_js:
            code_score += 1

        score += code_score

        # 4. パフォーマンス・最適化（4点）
        performance_score = 0
        # 画像の最適化（適切な数）
        images = soup.find_all('img')
        if 1 <= len(images) <= 20:  # 適切な画像数
            performance_score += 1

        # CSSファイルの数（多すぎない）
        css_files = soup.find_all('link', rel='stylesheet')
        if 1 <= len(css_files) <= 5:
            performance_score += 1

        # JavaScriptファイルの数（多すぎない）
        js_files = soup.find_all('script', src=True)
        if len(js_files) <= 10:
            performance_score += 1

        # メタviewportの存在（モバイル最適化）
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        if viewport_meta:
            performance_score += 1

        score += performance_score

        # 5. アクセシビリティ（3点）
        accessibility_score = 0
        # 言語設定
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            accessibility_score += 1

        # フォームのラベル
        forms = soup.find_all('form')
        if forms:
            labels = soup.find_all('label')
            if labels:
                accessibility_score += 1

        # 見出し構造の論理性
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if len(headings) >= 2:
            accessibility_score += 1

        score += accessibility_score

        return min(score, 30)  # 最大30点

def load_companies_from_csv(start_id=None, end_id=None):
    """CSVファイルから企業データを読み込む"""
    companies = []

    if not os.path.exists(INPUT_FILE):
        logger.error(f"入力ファイルが見つかりません: {INPUT_FILE}")
        return companies

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                # ID範囲の指定がある場合はフィルタリング
                if start_id is not None and i < start_id:
                    continue
                if end_id is not None and i > end_id:
                    break

                company = {
                    'id': i,
                    'name': row.get('企業名', '').strip(),
                    'url': row.get('企業URL', '').strip(),  # 正しいカラム名: '企業URL'
                    'industry': row.get('業界', '').strip(),
                    'location': row.get('所在地', '').strip()
                }

                if company['name'] and company['url']:
                    companies.append(company)
                else:
                    logger.warning(f"企業ID {i}: 企業名またはURLが空です")

        logger.info(f"企業データを読み込みました: {len(companies)}社")
        return companies

    except Exception as e:
        logger.error(f"企業データの読み込み中にエラーが発生しました: {e}")
        return []

def save_results_to_csv(results, start_id, end_id):
    """結果をCSVファイルに保存"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{OUTPUT_FILE_PREFIX}_id{start_id}-{end_id}_{timestamp}.csv"

    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = [
                '企業ID', '企業名', 'URL', '元URL', 'UXスコア', 'デザインスコア',
                '技術スコア', '総合スコア', 'ランク', 'ステータス', '分析方法'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                writer.writerow({
                    '企業ID': result['id'],
                    '企業名': result['company_name'],
                    'URL': result['url'],
                    '元URL': result.get('original_url', result['url']),
                    'UXスコア': result['ux_score'],
                    'デザインスコア': result['design_score'],
                    '技術スコア': result['technical_score'],
                    '総合スコア': result['total_score'],
                    'ランク': result['rank'],
                    'ステータス': result['status'],
                    '分析方法': result.get('analysis_method', 'requests')
                })

        logger.info(f"結果を保存しました: {filename}")
        return filename

    except Exception as e:
        logger.error(f"結果の保存中にエラーが発生しました: {e}")
        return None

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='新しいダッシュボード専用ウェブサイト分析（URL正規化・JavaScript対応）')
    parser.add_argument('--start-id', type=int, help='開始企業ID')
    parser.add_argument('--end-id', type=int, help='終了企業ID')
    parser.add_argument('--test', action='store_true', help='テストモード（最初の5社のみ処理）')
    parser.add_argument('--no-selenium', action='store_true', help='Seleniumを無効にする（BeautifulSoupのみ）')
    parser.add_argument('--timeout', type=int, default=30, help='タイムアウト時間（秒）デフォルト: 30秒')

    args = parser.parse_args()

    # テストモードの場合
    if args.test:
        args.start_id = 1
        args.end_id = 5
        logger.info("テストモードで実行します（企業ID 1-5）")

    # 企業データを読み込み
    companies = load_companies_from_csv(args.start_id, args.end_id)

    if not companies:
        logger.error("処理対象の企業データがありません")
        sys.exit(1)

    # 実際の開始・終了IDを取得
    actual_start_id = companies[0]['id']
    actual_end_id = companies[-1]['id']

    logger.info(f"ウェブサイト分析を開始します: 企業ID {actual_start_id}-{actual_end_id} ({len(companies)}社)")
    logger.info(f"タイムアウト設定: {args.timeout}秒")

    # ウェブサイト分析を実行（タイムアウト設定を適用）
    analyzer = WebsiteAnalyzer(timeout=args.timeout, use_selenium=not args.no_selenium)
    results = []

    try:
        for i, company in enumerate(companies, 1):
            logger.info(f"進捗: {i}/{len(companies)} - 企業ID {company['id']}: {company['name']}")

            analysis_result = analyzer.analyze_website(company['name'], company['url'])
            analysis_result['id'] = company['id']
            results.append(analysis_result)

            # サーバーに負荷をかけないよう少し待機
            if i < len(companies):
                wait_time = random.uniform(1, 3)
                time.sleep(wait_time)

    except KeyboardInterrupt:
        logger.info("処理が中断されました")
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
    finally:
        # Seleniumドライバーのクリーンアップ
        if hasattr(analyzer, 'driver') and analyzer.driver:
            try:
                analyzer.driver.quit()
                logger.info("Seleniumドライバーをクリーンアップしました")
            except Exception as e:
                logger.warning(f"Seleniumドライバーのクリーンアップエラー: {e}")

    # 結果を保存
    if results:
        output_file = save_results_to_csv(results, actual_start_id, actual_end_id)

        if output_file:
            # 統計情報を表示
            rank_counts = {'A': 0, 'B': 0, 'C': 0}
            method_counts = {'selenium': 0, 'requests': 0}

            for result in results:
                rank_counts[result['rank']] += 1
                method = result.get('analysis_method', 'requests')
                method_counts[method] += 1

            logger.info(f"処理完了:")
            logger.info(f"  - 処理企業数: {len(results)}社")
            logger.info(f"  - Aランク: {rank_counts['A']}社")
            logger.info(f"  - Bランク: {rank_counts['B']}社")
            logger.info(f"  - Cランク: {rank_counts['C']}社")
            logger.info(f"  - Selenium使用: {method_counts['selenium']}社")
            logger.info(f"  - requests使用: {method_counts['requests']}社")
            logger.info(f"  - 出力ファイル: {output_file}")
        else:
            logger.error("結果の保存に失敗しました")
            sys.exit(1)
    else:
        logger.warning("処理された結果がありません")
        sys.exit(1)

if __name__ == '__main__':
    main()
