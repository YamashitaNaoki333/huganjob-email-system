#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HUGAN.co.jpドメイン調査ツール
DNS設定、メール設定の現状確認
"""

import subprocess
import socket
import smtplib
import dns.resolver
import dns.exception
from datetime import datetime
import json

class DomainInvestigator:
    def __init__(self, domain="hugan.co.jp"):
        self.domain = domain
        self.results = {}
        
    def investigate_dns_records(self):
        """DNS レコードの調査"""
        print(f"🔍 {self.domain} DNS レコード調査")
        print("=" * 60)
        
        record_types = ['A', 'MX', 'TXT', 'CNAME', 'NS']
        dns_results = {}
        
        for record_type in record_types:
            try:
                print(f"\n📋 {record_type} レコード:")
                answers = dns.resolver.resolve(self.domain, record_type)
                records = []
                for answer in answers:
                    record_data = str(answer)
                    records.append(record_data)
                    print(f"  {record_data}")
                dns_results[record_type] = records
            except dns.exception.DNSException as e:
                print(f"  ❌ {record_type} レコードが見つかりません: {e}")
                dns_results[record_type] = []
        
        self.results['dns'] = dns_results
        return dns_results
    
    def check_spf_record(self):
        """SPF レコードの詳細確認"""
        print(f"\n🛡️ SPF レコード詳細分析")
        print("-" * 40)
        
        try:
            txt_records = dns.resolver.resolve(self.domain, 'TXT')
            spf_records = []
            
            for record in txt_records:
                record_str = str(record).strip('"')
                if record_str.startswith('v=spf1'):
                    spf_records.append(record_str)
                    print(f"✅ SPF レコード発見: {record_str}")
                    
                    # SPF レコードの解析
                    self.analyze_spf_record(record_str)
            
            if not spf_records:
                print("❌ SPF レコードが見つかりません")
                print("📝 推奨SPFレコード:")
                print('   "v=spf1 include:_spf.sakura.ne.jp ~all"')
            
            self.results['spf'] = spf_records
            return spf_records
            
        except dns.exception.DNSException as e:
            print(f"❌ TXT レコード取得エラー: {e}")
            return []
    
    def analyze_spf_record(self, spf_record):
        """SPF レコードの解析"""
        print(f"  📊 SPF レコード解析:")
        
        if 'include:_spf.sakura.ne.jp' in spf_record:
            print("    ✅ sakura.ne.jp SPF 設定済み")
        else:
            print("    ❌ sakura.ne.jp SPF 設定なし")
        
        if spf_record.endswith('~all'):
            print("    ✅ ソフトフェイル設定 (~all)")
        elif spf_record.endswith('-all'):
            print("    ⚠️ ハードフェイル設定 (-all)")
        elif spf_record.endswith('+all'):
            print("    ⚠️ 全許可設定 (+all) - 推奨されません")
    
    def check_dkim_record(self):
        """DKIM レコードの確認"""
        print(f"\n🔐 DKIM レコード確認")
        print("-" * 40)
        
        # 一般的なDKIMセレクター
        selectors = ['default', 'mail', 'dkim', 'google', 'selector1', 'selector2']
        dkim_results = {}
        
        for selector in selectors:
            dkim_domain = f"{selector}._domainkey.{self.domain}"
            try:
                txt_records = dns.resolver.resolve(dkim_domain, 'TXT')
                for record in txt_records:
                    record_str = str(record).strip('"')
                    if 'v=DKIM1' in record_str:
                        print(f"✅ DKIM レコード発見 ({selector}): {record_str[:100]}...")
                        dkim_results[selector] = record_str
            except dns.exception.DNSException:
                pass
        
        if not dkim_results:
            print("❌ DKIM レコードが見つかりません")
            print("📝 DKIM設定が必要です")
        
        self.results['dkim'] = dkim_results
        return dkim_results
    
    def check_mx_records(self):
        """MX レコードの詳細確認"""
        print(f"\n📬 MX レコード詳細分析")
        print("-" * 40)
        
        try:
            mx_records = dns.resolver.resolve(self.domain, 'MX')
            mx_list = []
            
            for mx in mx_records:
                priority = mx.preference
                server = str(mx.exchange)
                mx_list.append({'priority': priority, 'server': server})
                print(f"  優先度 {priority}: {server}")
                
                # sakura.ne.jp サーバーかチェック
                if 'sakura.ne.jp' in server:
                    print(f"    ✅ sakura.ne.jp メールサーバー")
                else:
                    print(f"    ℹ️ 外部メールサーバー")
            
            self.results['mx'] = mx_list
            return mx_list
            
        except dns.exception.DNSException as e:
            print(f"❌ MX レコード取得エラー: {e}")
            return []
    
    def test_smtp_connection(self, smtp_server="f045.sakura.ne.jp", port=587):
        """SMTP接続テスト"""
        print(f"\n🔗 SMTP接続テスト ({smtp_server}:{port})")
        print("-" * 40)
        
        try:
            server = smtplib.SMTP(smtp_server, port, timeout=10)
            print(f"✅ SMTP接続成功: {smtp_server}:{port}")
            
            # STARTTLS サポート確認
            server.starttls()
            print("✅ STARTTLS サポート確認")
            
            # 認証方法確認
            auth_methods = server.esmtp_features.get('auth', '')
            print(f"🔐 認証方法: {auth_methods}")
            
            server.quit()
            
            self.results['smtp'] = {
                'server': smtp_server,
                'port': port,
                'connection': 'success',
                'starttls': True,
                'auth_methods': auth_methods
            }
            return True
            
        except Exception as e:
            print(f"❌ SMTP接続失敗: {e}")
            self.results['smtp'] = {
                'server': smtp_server,
                'port': port,
                'connection': 'failed',
                'error': str(e)
            }
            return False
    
    def generate_dns_recommendations(self):
        """DNS設定推奨事項の生成"""
        print(f"\n📝 {self.domain} DNS設定推奨事項")
        print("=" * 60)
        
        recommendations = []
        
        # SPF レコード推奨
        if not self.results.get('spf'):
            recommendations.append({
                'type': 'SPF',
                'record': f'{self.domain}. IN TXT "v=spf1 include:_spf.sakura.ne.jp ~all"',
                'description': 'sakura.ne.jp経由でのメール送信を許可'
            })
        
        # MX レコード推奨
        mx_records = self.results.get('mx', [])
        has_sakura_mx = any('sakura.ne.jp' in mx['server'] for mx in mx_records)
        if not has_sakura_mx:
            recommendations.append({
                'type': 'MX',
                'record': f'{self.domain}. IN MX 10 f045.sakura.ne.jp.',
                'description': 'sakura.ne.jpメールサーバーを設定'
            })
        
        # DKIM レコード推奨
        if not self.results.get('dkim'):
            recommendations.append({
                'type': 'DKIM',
                'record': 'default._domainkey.hugan.co.jp. IN TXT "v=DKIM1; k=rsa; p=[公開鍵]"',
                'description': 'DKIM署名用の公開鍵（sakura.ne.jpで生成）'
            })
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec['type']} レコード:")
            print(f"   {rec['record']}")
            print(f"   説明: {rec['description']}\n")
        
        self.results['recommendations'] = recommendations
        return recommendations
    
    def save_investigation_report(self):
        """調査結果をファイルに保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'domain_investigation_report_{timestamp}.json'
        
        report = {
            'domain': self.domain,
            'investigation_date': datetime.now().isoformat(),
            'results': self.results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 調査結果を保存しました: {filename}")
        return filename

def main():
    """メイン調査処理"""
    print("🔍 HUGAN.co.jp ドメイン包括調査")
    print("=" * 80)
    
    investigator = DomainInvestigator("hugan.co.jp")
    
    # DNS レコード調査
    investigator.investigate_dns_records()
    
    # SPF レコード詳細確認
    investigator.check_spf_record()
    
    # DKIM レコード確認
    investigator.check_dkim_record()
    
    # MX レコード詳細確認
    investigator.check_mx_records()
    
    # SMTP接続テスト
    investigator.test_smtp_connection()
    
    # 推奨事項生成
    investigator.generate_dns_recommendations()
    
    # 調査結果保存
    report_file = investigator.save_investigation_report()
    
    print("\n" + "=" * 80)
    print("🎯 調査完了")
    print("=" * 80)
    print("次のステップ:")
    print("1. DNS設定の実装")
    print("2. メールアカウントの作成")
    print("3. SMTP設定の変更")
    print("4. テスト送信の実行")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 調査中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
