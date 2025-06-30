#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
変数置換テスト専用スクリプト
{job_position}変数の置換処理を検証
"""

import configparser

def test_variable_replacement():
    """変数置換テスト"""
    print("=" * 60)
    print("🔧 変数置換テスト開始")
    print("=" * 60)
    
    # 設定ファイル読み込み
    config = configparser.ConfigParser()
    config.read('config/huganjob_email_config.ini', encoding='utf-8')
    
    # 件名テンプレート取得
    subject_template = config.get('EMAIL_CONTENT', 'subject')
    print(f"📋 件名テンプレート: {subject_template}")
    
    # テストデータ
    test_positions = [
        "事務スタッフ",
        "製造スタッフ", 
        "技術職",
        "事務系総合職"
    ]
    
    print("\n🔧 変数置換テスト結果:")
    print("-" * 40)
    
    for i, job_position in enumerate(test_positions, 1):
        print(f"\nテスト {i}:")
        print(f"  入力職種: {job_position}")
        print(f"  型: {type(job_position)}")
        
        # 置換実行
        subject = subject_template.replace('{job_position}', str(job_position))
        print(f"  置換結果: {subject}")
        
        # 置換成功判定
        if '{job_position}' in subject:
            print(f"  ❌ 置換失敗: 変数が残っています")
        else:
            print(f"  ✅ 置換成功")
    
    # HTMLテンプレートテスト
    print("\n" + "=" * 60)
    print("🔧 HTMLテンプレート変数置換テスト")
    print("=" * 60)
    
    try:
        with open('corporate-email-newsletter.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"📋 HTMLテンプレート読み込み成功 ({len(html_content)}文字)")
        
        # 変数の存在確認
        if '{{company_name}}' in html_content:
            print("✅ {{company_name}} 変数が見つかりました")
        else:
            print("❌ {{company_name}} 変数が見つかりません")
            
        if '{{job_position}}' in html_content:
            print("✅ {{job_position}} 変数が見つかりました")
        else:
            print("❌ {{job_position}} 変数が見つかりません")
        
        # テスト置換
        test_company = "テスト株式会社"
        test_position = "テスト職種"
        
        replaced_html = html_content.replace('{{company_name}}', test_company)
        replaced_html = replaced_html.replace('{{job_position}}', test_position)
        
        print(f"\n🔧 HTMLテンプレート置換テスト:")
        print(f"  企業名: {test_company}")
        print(f"  職種: {test_position}")
        
        if '{{company_name}}' in replaced_html or '{{job_position}}' in replaced_html:
            print("❌ HTML置換失敗: 変数が残っています")
        else:
            print("✅ HTML置換成功")
            
    except Exception as e:
        print(f"❌ HTMLテンプレート読み込みエラー: {e}")
    
    print("\n" + "=" * 60)
    print("🔧 変数置換テスト完了")
    print("=" * 60)

if __name__ == "__main__":
    test_variable_replacement()
