#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB メールアドレス決定ロジック
CSVの担当者メールアドレス列を優先し、空白の場合はメール抽出を実行

作成日時: 2025年06月20日 22:00:00
作成者: AI Assistant
"""

import pandas as pd
import re
import logging
import sys
import os
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

# ログ設定（高速化のためINFOレベルに設定）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/huganjob_email_resolver.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 高速化のため、詳細ログを無効化
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

class HuganJobEmailResolver:
    """HUGAN JOB メールアドレス決定クラス"""
    
    def __init__(self, csv_file_path="data/new_input_test.csv"):
        """
        初期化
        
        Args:
            csv_file_path (str): 企業データCSVファイルのパス
        """
        self.csv_file_path = csv_file_path
        self.companies_df = None
        self.email_results = []
        
        # ログディレクトリ作成
        os.makedirs('logs', exist_ok=True)
        
    def load_companies_data(self):
        """企業データを読み込み"""
        try:
            logger.info(f"企業データ読み込み開始: {self.csv_file_path}")
            
            # CSVファイルの存在確認
            if not os.path.exists(self.csv_file_path):
                raise FileNotFoundError(f"CSVファイルが見つかりません: {self.csv_file_path}")
            
            # CSVデータ読み込み
            self.companies_df = pd.read_csv(self.csv_file_path, encoding='utf-8')
            
            # 列名の確認と正規化
            expected_columns = ['ID', '企業名', '企業ホームページ', '担当者メールアドレス', '募集職種']
            if list(self.companies_df.columns) != expected_columns:
                logger.warning(f"列名が期待値と異なります: {list(self.companies_df.columns)}")
                logger.info(f"期待値: {expected_columns}")
            
            logger.info(f"企業データ読み込み完了: {len(self.companies_df)}社")
            return True
            
        except Exception as e:
            logger.error(f"企業データ読み込みエラー: {e}")
            return False
    
    def is_valid_email(self, email):
        """
        メールアドレスの有効性をチェック（画像ファイル名等の除外を含む）

        Args:
            email (str): チェック対象のメールアドレス

        Returns:
            bool: 有効な場合True
        """
        if pd.isna(email) or email in ['‐', '-', '', ' ', None]:
            return False

        email_str = str(email).strip()
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
            local_part, domain_part = email_str.split('@', 1)
            if len(local_part) > 64 or len(local_part) == 0:  # RFC 5321の制限
                return False
            if len(domain_part) == 0:
                return False
        except ValueError:
            return False

        # 無効なファイル拡張子の除外チェック（大幅拡張）
        invalid_extensions = {
            # 画像ファイル
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp', '.ico',
            '.tiff', '.tif', '.avif', '.heic', '.heif',
            # ウェブファイル
            '.css', '.js', '.woff', '.woff2', '.otf', '.ttf', '.eot',
            '.map', '.json', '.xml', '.html', '.htm',
            # 無効なドメイン拡張子
            '.print', '.catalog', '.shop', '.contact', '.nav', '.main',
            '.logo', '.banner', '.header', '.footer', '.sidebar', '.content',
            '.image', '.string', '.easing', '.name', '.version', '.params',
            '.config', '.settings', '.options', '.plugin', '.custom',
            '.retargeting', '.datalayer', '.large', '.term', '.jquery',
            # JavaScript/CSS関連
            '.init', '.top', '.bottom', '.post', '.postdata', '.combox',
            '.duration', '.after', '.selector', '.offset', '.areas',
            '.mode', '.me', '.tag', '.captcha', '.mp', '.bg', '.com'
        }

        # レスポンシブ画像パターンの除外チェック（@2x.png, @3x.jpg等）
        responsive_patterns = [
            r'@\d+x\.(jpg|jpeg|png|gif|svg|webp|bmp|ico)$',
            r'@retina\.(jpg|jpeg|png|gif|svg|webp|bmp|ico)$',
            r'@mobile\.(jpg|jpeg|png|gif|svg|webp|bmp|ico)$',
            r'@tablet\.(jpg|jpeg|png|gif|svg|webp|bmp|ico)$'
        ]

        email_lower = email_str.lower()

        # 無効な拡張子の事前チェック（高速化）
        if any(email_lower.endswith(ext) for ext in invalid_extensions):
            return False

        # ドメイン部の基本チェック
        if not domain_part or '.' not in domain_part:
            return False

        # 有効なTLDパターンのチェック
        domain_parts = domain_part.split('.')
        if len(domain_parts) < 2:
            return False

        # 最後の部分（TLD）が有効かチェック
        tld = domain_parts[-1]
        if len(tld) < 2 or not tld.isalpha():
            return False

        # 連続するドットや無効な文字のチェック
        if '..' in email_str or email_str.startswith('.') or email_str.endswith('.'):
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

        # 高速パターンマッチング：JavaScript/CSS変数パターンの除外
        invalid_patterns = [
            'window.', '.prototype.', '.version', '.params', '.config', '.settings', '.options',
            '@plugin.', '@custom.', '@retargeting.', '@datalayer.', '@large.', '@term.', '@jquery.',
            'summary@', 'search@', 'my@', 'gtm4wp@', '@reset.', '@polisy.', '@bg.', '@scroll.',
            '@fade.', '@hide.', '@element.', '@container.', '@widget.', '@reload.', '@check.',
            '@unit.', '@post.', '@challenge.', '@captcha.', '@2.', '@sp.', '@pc.', '@mobile.',
            '@tablet.', 'comp-', 'webpackjsonp', 'self.webpackjsonp', 'thunderbolt.app'
        ]

        # 高速文字列検索（正規表現より高速）
        if any(pattern in email_lower for pattern in invalid_patterns):
            return False

        return True
    
    def extract_email_from_website(self, company_id, company_name, website_url):
        """
        ウェブサイトからメールアドレスを抽出（既存システムを利用）

        Args:
            company_id (int): 企業ID
            company_name (str): 企業名
            website_url (str): 企業ウェブサイトURL

        Returns:
            str or None: 抽出されたメールアドレス、失敗時はNone
        """
        try:
            # 既存のメール抽出結果ファイルをチェック
            extraction_files = [
                'new_email_extraction_results_latest.csv',
                'huganjob_email_extraction_results.csv',
                'derivative_ad_email_extraction_results.csv'
            ]

            for extraction_file in extraction_files:
                if os.path.exists(extraction_file):
                    try:
                        extraction_df = pd.read_csv(extraction_file, encoding='utf-8')

                        # 企業IDまたは企業名で検索
                        if '企業ID' in extraction_df.columns:
                            match = extraction_df[extraction_df['企業ID'] == company_id]
                        elif 'ID' in extraction_df.columns:
                            match = extraction_df[extraction_df['ID'] == company_id]
                        else:
                            # 企業名で検索
                            match = extraction_df[extraction_df['企業名'] == company_name]

                        if not match.empty:
                            email_col = None
                            for col in ['メールアドレス', 'email', 'Email', 'EMAIL']:
                                if col in match.columns:
                                    email_col = col
                                    break

                            if email_col:
                                extracted_email = match.iloc[0][email_col]
                                if self.is_valid_email(extracted_email):
                                    logger.info(f"既存抽出結果から取得: {company_name} -> {extracted_email}")
                                    return extracted_email.strip()

                    except Exception as e:
                        logger.warning(f"抽出結果ファイル読み込みエラー: {extraction_file} - {e}")
                        continue

            # 既存の抽出結果が見つからない場合は、新規抽出を実行
            logger.info(f"新規メール抽出実行: {company_name} ({website_url})")
            return self.run_email_extraction(company_id, company_name, website_url)

        except Exception as e:
            logger.error(f"メール抽出エラー: {company_name} - {e}")
            return None

    def run_email_extraction(self, company_id, company_name, website_url):
        """
        新規メール抽出を実行（既存の高度なシステムを活用）

        Args:
            company_id (int): 企業ID
            company_name (str): 企業名
            website_url (str): 企業ウェブサイトURL

        Returns:
            str or None: 抽出されたメールアドレス、失敗時はNone
        """
        try:
            logger.info(f"🔍 高度メール抽出開始: {company_name}")

            # 既存の高度なメール抽出システムを使用
            extracted_email = self.advanced_email_extraction(company_id, company_name, website_url)
            if extracted_email:
                logger.info(f"✅ 高度抽出成功: {company_name} -> {extracted_email}")
                return extracted_email

            # 高度抽出が失敗した場合は簡易抽出を実行
            logger.info(f"🌐 簡易抽出にフォールバック: {company_name}")
            return self.simple_email_extraction(website_url, company_name)

        except Exception as e:
            logger.error(f"新規メール抽出エラー: {company_name} - {e}")
            return None

    def advanced_email_extraction(self, company_id, company_name, website_url):
        """
        既存の高度なメール抽出システムを活用

        Args:
            company_id (int): 企業ID
            company_name (str): 企業名
            website_url (str): 企業ウェブサイトURL

        Returns:
            str or None: 抽出されたメールアドレス、失敗時はNone
        """
        try:
            # 既存の高度なメール抽出クラスをインポート
            import sys
            import os

            # core_scriptsディレクトリをパスに追加
            core_scripts_path = os.path.join(os.getcwd(), 'core_scripts')
            if core_scripts_path not in sys.path:
                sys.path.append(core_scripts_path)

            from derivative_email_extractor import PrioritizedEmailExtractor

            # 高度なメール抽出器を初期化（高速設定）
            extractor = PrioritizedEmailExtractor(
                timeout=5,
                max_retries=1,
                use_dynamic_extraction=False,  # 高速化のため無効
                use_contact_form_analysis=False  # 高速化のため無効
            )

            # 優先順位に基づくメール抽出を実行
            result = extractor.extract_emails_with_priority(
                company_name=company_name,
                url=website_url,
                company_id=company_id
            )

            # 最適なメールアドレスを取得
            if result and result.get('best_email'):
                best_email = result['best_email']
                email_address = best_email.get('email')
                confidence = best_email.get('confidence', 0.0)
                source = best_email.get('source', 'unknown')

                logger.info(f"高度抽出結果: {company_name} -> {email_address} (信頼度: {confidence:.2f}, ソース: {source})")

                # 信頼度が0.3以上かつ有効なメールアドレスの場合のみ採用
                if confidence >= 0.3 and self.is_valid_email(email_address):
                    logger.info(f"✅ 高度抽出成功: {company_name} -> {email_address} (信頼度: {confidence:.2f})")
                    return email_address
                else:
                    if confidence < 0.3:
                        logger.warning(f"❌ 信頼度が低いため除外: {email_address} (信頼度: {confidence:.2f})")
                    else:
                        logger.warning(f"❌ 画像ファイル名等のため除外: {email_address}")

            # 抽出されたメールアドレスがない場合
            logger.info(f"高度抽出でメールアドレスが見つかりませんでした: {company_name}")
            return None

        except ImportError as e:
            logger.warning(f"高度メール抽出システムのインポートに失敗: {e}")
            return None
        except Exception as e:
            logger.error(f"高度メール抽出エラー: {company_name} - {e}")
            return None

    def parse_extraction_result(self, company_id, company_name):
        """
        抽出結果ファイルから最新の結果を取得

        Args:
            company_id (int): 企業ID
            company_name (str): 企業名

        Returns:
            str or None: 抽出されたメールアドレス
        """
        try:
            # 最新の抽出結果ファイルをチェック
            result_files = [
                'email_extraction_results.csv',
                'derivative_ad_email_extraction_results.csv',
                'huganjob_email_extraction_results.csv'
            ]

            for result_file in result_files:
                if os.path.exists(result_file):
                    try:
                        df = pd.read_csv(result_file, encoding='utf-8')

                        # 企業IDまたは企業名で検索
                        if 'ID' in df.columns:
                            match = df[df['ID'] == company_id]
                        elif '企業ID' in df.columns:
                            match = df[df['企業ID'] == company_id]
                        else:
                            match = df[df['企業名'] == company_name]

                        if not match.empty:
                            # メールアドレス列を探す
                            email_cols = ['メールアドレス', 'email', 'Email', 'EMAIL', 'extracted_email']
                            for col in email_cols:
                                if col in match.columns:
                                    email = match.iloc[-1][col]  # 最新の結果を取得
                                    if self.is_valid_email(email):
                                        return str(email).strip()

                    except Exception as e:
                        logger.warning(f"結果ファイル読み込みエラー: {result_file} - {e}")
                        continue

            return None

        except Exception as e:
            logger.error(f"抽出結果解析エラー: {e}")
            return None

    def simple_email_extraction(self, website_url, company_name):
        """
        簡易メール抽出（ウェブスクレイピング）

        Args:
            website_url (str): 企業ウェブサイトURL
            company_name (str): 企業名

        Returns:
            str or None: 抽出されたメールアドレス
        """
        try:
            import requests

            logger.info(f"🌐 簡易メール抽出: {company_name} ({website_url})")

            # ウェブサイトにアクセス
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(website_url, headers=headers, timeout=10)
            response.raise_for_status()

            # メールアドレスパターンを検索（有効なTLDのみ）
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,6}\b'
            potential_emails = re.findall(email_pattern, response.text)

            # 事前フィルタリング：明らかに無効なパターンを除外
            invalid_extensions = {
                '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp', '.ico',
                '.css', '.js', '.html', '.htm', '.xml', '.json', '.pdf',
                '.print', '.catalog', '.shop', '.contact', '.nav', '.main',
                '.logo', '.banner', '.header', '.footer', '.sidebar', '.content'
            }

            # 高速事前フィルタリング
            filtered_emails = []
            for email in potential_emails:
                email_lower = email.lower()
                if not any(email_lower.endswith(ext) for ext in invalid_extensions):
                    filtered_emails.append(email)

            # 有効なメールアドレスをフィルタリング
            valid_emails = []
            for email in filtered_emails:
                if self.is_valid_email(email):
                    # 一般的でないメールアドレスを優先
                    if not any(generic in email.lower() for generic in ['noreply', 'no-reply', 'donotreply', 'example', 'test']):
                        valid_emails.append(email)
                        logger.info(f"✅ 簡易抽出で有効メール発見: {email}")
                    else:
                        logger.debug(f"❌ 一般的なメールアドレスのため除外: {email}")
                else:
                    logger.debug(f"❌ 無効なメールアドレスのため除外: {email}")

            if valid_emails:
                # 最初の有効なメールアドレスを返す
                selected_email = valid_emails[0]
                logger.info(f"✅ 簡易抽出成功: {company_name} -> {selected_email}")
                return selected_email
            else:
                logger.warning(f"❌ 簡易抽出失敗: {company_name} (有効なメールアドレスなし)")
                return None

        except Exception as e:
            logger.warning(f"❌ 簡易抽出エラー: {company_name} - {e}")
            return None
    
    def resolve_email_addresses(self):
        """
        全企業のメールアドレスを決定
        
        Returns:
            list: メールアドレス決定結果のリスト
        """
        if self.companies_df is None:
            logger.error("企業データが読み込まれていません")
            return []
        
        logger.info("メールアドレス決定処理開始")
        self.email_results = []
        
        for index, row in self.companies_df.iterrows():
            company_id = row['ID']
            company_name = row['企業名']
            website_url = row['企業ホームページ']
            csv_email = row['担当者メールアドレス']
            job_position = row['募集職種']
            
            result = {
                'company_id': company_id,
                'company_name': company_name,
                'website_url': website_url,
                'job_position': job_position,
                'csv_email': csv_email,
                'final_email': None,
                'email_source': None,
                'status': 'pending'
            }
            
            # 第1優先: CSVの担当者メールアドレス
            if self.is_valid_email(csv_email):
                result['final_email'] = csv_email.strip()
                result['email_source'] = 'csv_direct'
                result['status'] = 'success'
                logger.info(f"✅ CSV直接: {company_name} -> {result['final_email']}")
            
            # 第2優先: ウェブサイトからの抽出
            else:
                extracted_email = self.extract_email_from_website(
                    company_id, company_name, website_url
                )
                
                if extracted_email and self.is_valid_email(extracted_email):
                    result['final_email'] = extracted_email.strip()
                    result['email_source'] = 'website_extraction'
                    result['status'] = 'success'
                    logger.info(f"✅ 抽出成功: {company_name} -> {result['final_email']}")
                else:
                    result['status'] = 'failed'
                    logger.warning(f"❌ メール取得失敗: {company_name}")
            
            self.email_results.append(result)
        
        # 統計情報
        success_count = len([r for r in self.email_results if r['status'] == 'success'])
        csv_direct_count = len([r for r in self.email_results if r['email_source'] == 'csv_direct'])
        extraction_count = len([r for r in self.email_results if r['email_source'] == 'website_extraction'])
        
        logger.info("=" * 60)
        logger.info("📊 メールアドレス決定結果統計")
        logger.info("=" * 60)
        logger.info(f"総企業数: {len(self.email_results)}")
        logger.info(f"成功: {success_count} ({success_count/len(self.email_results)*100:.1f}%)")
        logger.info(f"  - CSV直接: {csv_direct_count}")
        logger.info(f"  - ウェブ抽出: {extraction_count}")
        logger.info(f"失敗: {len(self.email_results) - success_count}")
        logger.info("=" * 60)
        
        return self.email_results
    
    def get_sendable_companies(self):
        """
        送信可能な企業リストを取得
        
        Returns:
            list: 送信可能な企業の情報リスト
        """
        if not self.email_results:
            logger.warning("メールアドレス決定処理が実行されていません")
            return []
        
        sendable = [r for r in self.email_results if r['status'] == 'success']
        logger.info(f"送信可能企業数: {len(sendable)}")
        
        return sendable
    
    def save_results_to_csv(self, output_file="huganjob_email_resolution_results.csv"):
        """
        結果をCSVファイルに保存（既存結果を保持しながら追加）

        Args:
            output_file (str): 出力ファイル名
        """
        if not self.email_results:
            logger.warning("保存する結果がありません")
            return False

        try:
            # 新しい結果をDataFrameに変換
            new_results_df = pd.DataFrame(self.email_results)

            # 既存ファイルが存在する場合は読み込み
            if os.path.exists(output_file):
                try:
                    existing_df = pd.read_csv(output_file, encoding='utf-8')
                    logger.info(f"既存の結果ファイルを読み込み: {len(existing_df)}行")

                    # 既存の企業IDを取得
                    existing_ids = set(existing_df['company_id'].tolist()) if 'company_id' in existing_df.columns else set()

                    # 新しい結果から既存IDと重複しないもののみを抽出
                    new_ids = set(new_results_df['company_id'].tolist())
                    duplicate_ids = existing_ids.intersection(new_ids)

                    if duplicate_ids:
                        logger.info(f"重複する企業ID: {sorted(duplicate_ids)}")
                        # 重複するIDの既存データを削除
                        existing_df = existing_df[~existing_df['company_id'].isin(duplicate_ids)]
                        logger.info(f"重複データを削除後: {len(existing_df)}行")

                    # 既存データと新しいデータを結合
                    combined_df = pd.concat([existing_df, new_results_df], ignore_index=True)

                except Exception as e:
                    logger.warning(f"既存ファイル読み込みエラー: {e}、新しいファイルとして保存します")
                    combined_df = new_results_df
            else:
                logger.info("新しい結果ファイルを作成")
                combined_df = new_results_df

            # 企業IDでソート
            combined_df = combined_df.sort_values('company_id')

            # CSVに保存
            combined_df.to_csv(output_file, index=False, encoding='utf-8')
            logger.info(f"結果をCSVに保存: {output_file} (合計: {len(combined_df)}行)")
            return True

        except Exception as e:
            logger.error(f"CSV保存エラー: {e}")
            return False

def main():
    """メイン処理"""
    import argparse

    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='HUGAN JOB メールアドレス決定システム')
    parser.add_argument('--start-id', type=int, help='開始ID（指定した場合、範囲処理）')
    parser.add_argument('--end-id', type=int, help='終了ID（指定した場合、範囲処理）')
    args = parser.parse_args()

    print("=" * 60)
    print("📧 HUGAN JOB メールアドレス決定システム")
    print("=" * 60)

    # メールアドレス決定処理
    resolver = HuganJobEmailResolver()

    # 企業データ読み込み
    if not resolver.load_companies_data():
        print("❌ 企業データの読み込みに失敗しました")
        return False

    # ID範囲指定がある場合はフィルタリング
    if args.start_id is not None and args.end_id is not None:
        print(f"🎯 ID範囲指定: {args.start_id} ～ {args.end_id}")
        original_count = len(resolver.companies_df)
        resolver.companies_df = resolver.companies_df[
            (resolver.companies_df['ID'] >= args.start_id) &
            (resolver.companies_df['ID'] <= args.end_id)
        ]
        filtered_count = len(resolver.companies_df)
        print(f"📊 フィルタリング結果: {original_count}社 → {filtered_count}社")

        if filtered_count == 0:
            print("❌ 指定されたID範囲に該当する企業がありません")
            return False

    # メールアドレス決定
    results = resolver.resolve_email_addresses()

    if not results:
        print("❌ メールアドレス決定処理に失敗しました")
        return False

    # 結果保存
    resolver.save_results_to_csv()

    # 送信可能企業の表示
    sendable = resolver.get_sendable_companies()

    print("\n📋 送信可能企業（最初の10社）:")
    for i, company in enumerate(sendable[:10]):
        print(f"  {i+1:2d}. {company['company_name']} -> {company['final_email']}")

    if len(sendable) > 10:
        print(f"  ... 他 {len(sendable) - 10} 社")

    print(f"\n✅ 処理完了: {len(sendable)} 社が送信可能です")
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ 処理がキャンセルされました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ エラーが発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
