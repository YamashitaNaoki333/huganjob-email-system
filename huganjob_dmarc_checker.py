#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB DMARC設定確認・監視ツール
Gmail 2024年要件対応

作成日時: 2025年06月26日 19:50:00
機能:
1. DMARC設定状況の確認
2. SPF/DKIM/DMARC認証状況の総合チェック
3. 設定推奨事項の提示
4. 継続監視機能
"""

import dns.resolver
import smtplib
import time
import json
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class DMARCChecker:
    """DMARC設定確認・監視クラス"""
    
    def __init__(self, domain="huganjob.jp"):
        self.domain = domain
        self.results = {}
        
    def check_spf_record(self):
        """SPFレコード確認"""
        try:
            print(f"\n🔍 SPFレコード確認: {self.domain}")
            records = dns.resolver.resolve(self.domain, 'TXT')
            
            spf_found = False
            for record in records:
                txt_value = record.to_text().strip('"')
                if txt_value.startswith('v=spf1'):
                    print(f"✅ SPFレコード発見: {txt_value}")
                    self.results['spf'] = {
                        'status': 'found',
                        'record': txt_value,
                        'valid': True
                    }
                    spf_found = True
                    
                    # Xserver設定確認
                    if 'xserver.jp' in txt_value:
                        print("✅ Xserver SPF設定: 正常")
                    else:
                        print("⚠️ Xserver SPF設定: 要確認")
                    break
            
            if not spf_found:
                print("❌ SPFレコードが見つかりません")
                self.results['spf'] = {'status': 'not_found', 'valid': False}
                
        except Exception as e:
            print(f"❌ SPFレコード確認エラー: {e}")
            self.results['spf'] = {'status': 'error', 'error': str(e), 'valid': False}
    
    def check_dkim_record(self):
        """DKIMレコード確認"""
        try:
            print(f"\n🔍 DKIMレコード確認: default._domainkey.{self.domain}")
            records = dns.resolver.resolve(f'default._domainkey.{self.domain}', 'TXT')
            
            dkim_found = False
            for record in records:
                txt_value = record.to_text().strip('"')
                if 'v=DKIM1' in txt_value:
                    print(f"✅ DKIMレコード発見: {txt_value[:100]}...")
                    self.results['dkim'] = {
                        'status': 'found',
                        'record': txt_value,
                        'valid': True
                    }
                    dkim_found = True
                    break
            
            if not dkim_found:
                print("❌ DKIMレコードが見つかりません")
                self.results['dkim'] = {'status': 'not_found', 'valid': False}
                
        except Exception as e:
            print(f"❌ DKIMレコード確認エラー: {e}")
            self.results['dkim'] = {'status': 'error', 'error': str(e), 'valid': False}
    
    def check_dmarc_record(self):
        """DMARCレコード確認"""
        try:
            print(f"\n🔍 DMARCレコード確認: _dmarc.{self.domain}")
            records = dns.resolver.resolve(f'_dmarc.{self.domain}', 'TXT')
            
            dmarc_found = False
            for record in records:
                txt_value = record.to_text().strip('"')
                if txt_value.startswith('v=DMARC1'):
                    print(f"✅ DMARCレコード発見: {txt_value}")
                    self.results['dmarc'] = {
                        'status': 'found',
                        'record': txt_value,
                        'valid': True
                    }
                    dmarc_found = True
                    
                    # DMARC設定解析
                    self.parse_dmarc_policy(txt_value)
                    break
            
            if not dmarc_found:
                print("❌ DMARCレコードが見つかりません")
                print("🚨 Gmail 2024年要件: DMARC設定が必須です")
                self.results['dmarc'] = {'status': 'not_found', 'valid': False}
                
        except Exception as e:
            print(f"❌ DMARCレコード確認エラー: {e}")
            self.results['dmarc'] = {'status': 'error', 'error': str(e), 'valid': False}
    
    def parse_dmarc_policy(self, dmarc_record):
        """DMARC設定解析"""
        print("\n📋 DMARC設定詳細:")
        
        # ポリシー確認
        if 'p=none' in dmarc_record:
            print("📊 ポリシー: none (監視のみ)")
        elif 'p=quarantine' in dmarc_record:
            print("🛡️ ポリシー: quarantine (隔離)")
        elif 'p=reject' in dmarc_record:
            print("🚫 ポリシー: reject (拒否)")
        
        # レポート設定確認
        if 'rua=' in dmarc_record:
            print("📧 集約レポート: 設定済み")
        else:
            print("⚠️ 集約レポート: 未設定")
        
        if 'ruf=' in dmarc_record:
            print("📧 失敗レポート: 設定済み")
        else:
            print("⚠️ 失敗レポート: 未設定")
    
    def generate_dmarc_recommendation(self):
        """DMARC設定推奨事項生成"""
        print("\n" + "="*60)
        print("📋 DMARC設定推奨事項")
        print("="*60)
        
        if not self.results.get('dmarc', {}).get('valid', False):
            print("\n🚨 緊急対応必要: DMARC設定")
            print("-" * 40)
            
            print("📝 推奨DMARCレコード:")
            print("種別: TXT")
            print("ホスト名: _dmarc")
            print("内容: v=DMARC1; p=quarantine; rua=mailto:dmarc@huganjob.jp; ruf=mailto:dmarc@huganjob.jp; sp=quarantine; adkim=r; aspf=r; fo=1; pct=100")
            
            print("\n🔧 設定手順:")
            print("1. Xserver管理画面にログイン")
            print("2. DNS設定 → huganjob.jp → DNSレコード追加")
            print("3. 上記のTXTレコードを追加")
            print("4. 24時間後に設定確認")
            
            print("\n📧 事前準備:")
            print("1. dmarc@huganjob.jp メールアドレス作成")
            print("2. DMARCレポート受信設定")
            
        else:
            print("✅ DMARC設定: 正常")
            
        # 総合評価
        print(f"\n📊 認証設定総合評価:")
        spf_ok = self.results.get('spf', {}).get('valid', False)
        dkim_ok = self.results.get('dkim', {}).get('valid', False)
        dmarc_ok = self.results.get('dmarc', {}).get('valid', False)
        
        print(f"SPF: {'✅' if spf_ok else '❌'}")
        print(f"DKIM: {'✅' if dkim_ok else '❌'}")
        print(f"DMARC: {'✅' if dmarc_ok else '❌'}")
        
        score = sum([spf_ok, dkim_ok, dmarc_ok])
        print(f"\n🎯 認証スコア: {score}/3")
        
        if score == 3:
            print("🏆 Gmail 2024年要件: 完全対応")
            print("📈 迷惑メール判定: 大幅改善期待")
        elif score == 2:
            print("⚠️ Gmail 2024年要件: 部分対応")
            print("📧 迷惑メール判定: 改善余地あり")
        else:
            print("🚨 Gmail 2024年要件: 対応不足")
            print("📧 迷惑メール判定: 高確率でスパム")
    
    def save_results(self):
        """結果保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'huganjob_dmarc_check_{timestamp}.json'
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'domain': self.domain,
            'results': self.results,
            'recommendations': self.generate_recommendations_data()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 結果保存: {filename}")
        return filename
    
    def generate_recommendations_data(self):
        """推奨事項データ生成"""
        recommendations = []
        
        if not self.results.get('dmarc', {}).get('valid', False):
            recommendations.append({
                'priority': 'high',
                'type': 'dmarc_setup',
                'description': 'DMARC設定の追加',
                'action': 'DNS TXTレコード追加',
                'record': 'v=DMARC1; p=quarantine; rua=mailto:dmarc@huganjob.jp; ruf=mailto:dmarc@huganjob.jp; sp=quarantine; adkim=r; aspf=r; fo=1; pct=100'
            })
        
        return recommendations
    
    def run_full_check(self):
        """完全チェック実行"""
        print("="*60)
        print("🔍 HUGANJOB DMARC設定確認ツール")
        print("Gmail 2024年要件対応チェック")
        print("="*60)
        
        # 各種レコード確認
        self.check_spf_record()
        self.check_dkim_record()
        self.check_dmarc_record()
        
        # 推奨事項生成
        self.generate_dmarc_recommendation()
        
        # 結果保存
        report_file = self.save_results()
        
        print(f"\n🏁 チェック完了")
        print(f"📄 詳細レポート: {report_file}")
        
        return self.results

def main():
    """メイン処理"""
    checker = DMARCChecker("huganjob.jp")
    results = checker.run_full_check()
    
    # DMARC未設定の場合、設定ガイド表示
    if not results.get('dmarc', {}).get('valid', False):
        print("\n" + "="*60)
        print("📚 詳細設定ガイド")
        print("="*60)
        print("📖 huganjob_dmarc_setup_guide.md を参照してください")
        print("🔧 Xserver DNS設定での具体的な手順が記載されています")
    
    return results

if __name__ == "__main__":
    main()
