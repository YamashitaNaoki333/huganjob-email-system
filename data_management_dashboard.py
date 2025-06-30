#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
データ管理ダッシュボード
複数のデータソースを統合・管理するためのWebインターフェース
"""

import os
import csv
import pandas as pd
import json
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class DataManager:
    def __init__(self):
        self.data_directory = 'data'
        self.input_files = ['test_input.csv', 'osaka_input.csv']
        
    def get_available_files(self):
        """利用可能なデータファイル一覧を取得"""
        files = []
        
        # ルートディレクトリのCSVファイル
        for file in os.listdir('.'):
            if file.endswith('.csv') and not file.startswith('.'):
                files.append({
                    'name': file,
                    'path': file,
                    'size': os.path.getsize(file),
                    'modified': datetime.fromtimestamp(os.path.getmtime(file))
                })
        
        # dataディレクトリのファイル
        if os.path.exists(self.data_directory):
            for file in os.listdir(self.data_directory):
                if file.endswith('.csv'):
                    file_path = os.path.join(self.data_directory, file)
                    files.append({
                        'name': file,
                        'path': file_path,
                        'size': os.path.getsize(file_path),
                        'modified': datetime.fromtimestamp(os.path.getmtime(file_path))
                    })
        
        return sorted(files, key=lambda x: x['modified'], reverse=True)
    
    def analyze_file(self, file_path):
        """ファイルを分析"""
        try:
            # 複数エンコーディングで読み込み
            encodings = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                return None
            
            # 基本統計
            analysis = {
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns),
                'sample_data': df.head(5).to_dict('records'),
                'data_types': df.dtypes.to_dict(),
                'null_counts': df.isnull().sum().to_dict()
            }
            
            # 特定カラムの分析
            if '企業名' in df.columns:
                analysis['company_count'] = df['企業名'].notna().sum()
            
            if 'URL' in df.columns:
                analysis['url_count'] = df['URL'].notna().sum()
                analysis['valid_url_count'] = df['URL'].str.contains('http', na=False).sum()
            
            if 'メールアドレス' in df.columns:
                analysis['email_count'] = df['メールアドレス'].notna().sum()
            
            return analysis
            
        except Exception as e:
            logger.error(f"ファイル分析エラー: {e}")
            return None
    
    def merge_files(self, file_paths, output_name):
        """複数ファイルをマージ"""
        try:
            merged_df = pd.DataFrame()
            
            for file_path in file_paths:
                # ファイル読み込み
                encodings = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932']
                df = None
                
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if df is None:
                    continue
                
                # カラム名の標準化
                column_mapping = {
                    '事務所名': '企業名',
                    '会社名': '企業名',
                    '法人名': '企業名',
                    '企業URL': 'URL',
                    'ウェブサイト': 'URL',
                    'ホームページ': 'URL',
                    '担当者メールアドレス': 'メールアドレス',
                    'Email': 'メールアドレス',
                    'email': 'メールアドレス'
                }
                
                df = df.rename(columns=column_mapping)
                
                # 必須カラムの確認
                if '企業名' not in df.columns and len(df.columns) > 0:
                    df = df.rename(columns={df.columns[0]: '企業名'})
                
                if 'URL' not in df.columns:
                    df['URL'] = ''
                
                # データクリーニング
                df = df.dropna(subset=['企業名'])
                df = df[df['企業名'] != '']
                
                # マージ
                if merged_df.empty:
                    merged_df = df
                else:
                    # カラムを統一
                    all_columns = list(set(merged_df.columns) | set(df.columns))
                    for col in all_columns:
                        if col not in merged_df.columns:
                            merged_df[col] = ''
                        if col not in df.columns:
                            df[col] = ''
                    
                    merged_df = pd.concat([merged_df, df], ignore_index=True)
            
            # IDを再採番
            merged_df.insert(0, 'ID', range(1, len(merged_df) + 1))
            
            # 保存
            output_path = f"{output_name}.csv"
            merged_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            return output_path, len(merged_df)
            
        except Exception as e:
            logger.error(f"ファイルマージエラー: {e}")
            return None, 0

data_manager = DataManager()

@app.route('/')
def index():
    """メインページ"""
    files = data_manager.get_available_files()
    
    template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HUGAN JOB データ管理ダッシュボード</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #0078d4 0%, #106ebe 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
        .card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .file-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .file-item { border: 1px solid #ddd; border-radius: 8px; padding: 15px; background: #fafafa; }
        .file-name { font-weight: bold; color: #0078d4; margin-bottom: 10px; }
        .file-info { font-size: 12px; color: #666; margin-bottom: 5px; }
        .btn { background: #0078d4; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; margin: 2px; }
        .btn:hover { background: #106ebe; }
        .btn-success { background: #107c10; }
        .btn-warning { background: #ff8c00; }
        .btn-danger { background: #d13438; }
        .merge-section { background: #e8f4fd; padding: 20px; border-radius: 8px; margin-top: 20px; }
        .checkbox-list { max-height: 200px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 20px; }
        .stat-item { text-align: center; padding: 15px; background: #f0f8ff; border-radius: 8px; }
        .stat-number { font-size: 24px; font-weight: bold; color: #0078d4; }
        .stat-label { font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 HUGAN JOB データ管理ダッシュボード</h1>
            <p>複数のデータソースを統合・管理するためのWebインターフェース</p>
        </div>
        
        <div class="card">
            <h2>📁 利用可能なデータファイル</h2>
            <div class="file-list">
                {% for file in files %}
                <div class="file-item">
                    <div class="file-name">{{ file.name }}</div>
                    <div class="file-info">サイズ: {{ "%.1f"|format(file.size/1024) }} KB</div>
                    <div class="file-info">更新: {{ file.modified.strftime('%Y-%m-%d %H:%M') }}</div>
                    <div style="margin-top: 10px;">
                        <a href="/analyze/{{ file.name }}" class="btn btn-success">分析</a>
                        <a href="/download/{{ file.name }}" class="btn">ダウンロード</a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="card">
            <div class="merge-section">
                <h3>🔗 ファイルマージ機能</h3>
                <p>複数のファイルを統合して新しいデータセットを作成します</p>
                
                <form action="/merge" method="post">
                    <div class="form-group">
                        <label>マージするファイルを選択:</label>
                        <div class="checkbox-list">
                            {% for file in files %}
                            <div>
                                <input type="checkbox" name="files" value="{{ file.path }}" id="file_{{ loop.index }}">
                                <label for="file_{{ loop.index }}" style="display: inline; margin-left: 5px;">{{ file.name }}</label>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="output_name">出力ファイル名:</label>
                        <input type="text" name="output_name" id="output_name" placeholder="merged_data" required>
                    </div>
                    
                    <button type="submit" class="btn btn-warning">マージ実行</button>
                </form>
            </div>
        </div>
        
        <div class="card">
            <h3>🛠️ データ管理ツール</h3>
            <div style="margin-top: 15px;">
                <a href="/upload" class="btn btn-success">新しいファイルをアップロード</a>
                <a href="/convert" class="btn btn-warning">形式変換</a>
                <a href="/validate" class="btn">データ検証</a>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">{{ files|length }}</div>
                <div class="stat-label">データファイル数</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{{ "%.1f"|format((files|sum(attribute='size'))/1024/1024) }}</div>
                <div class="stat-label">総データサイズ (MB)</div>
            </div>
        </div>
    </div>
</body>
</html>
    """
    
    return render_template_string(template, files=files)

@app.route('/analyze/<filename>')
def analyze_file(filename):
    """ファイル分析ページ"""
    file_path = filename
    if not os.path.exists(file_path):
        file_path = os.path.join('data', filename)
    
    if not os.path.exists(file_path):
        return "ファイルが見つかりません", 404
    
    analysis = data_manager.analyze_file(file_path)
    if not analysis:
        return "ファイル分析に失敗しました", 500
    
    template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ファイル分析結果 - {{ filename }}</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #0078d4 0%, #106ebe 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
        .card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-item { text-align: center; padding: 15px; background: #f0f8ff; border-radius: 8px; }
        .stat-number { font-size: 24px; font-weight: bold; color: #0078d4; }
        .stat-label { font-size: 12px; color: #666; }
        .table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .table th, .table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .table th { background-color: #f2f2f2; }
        .btn { background: #0078d4; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; margin: 2px; }
        .btn:hover { background: #106ebe; }
        .column-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px; }
        .column-item { padding: 10px; background: #f9f9f9; border-radius: 5px; border-left: 4px solid #0078d4; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 ファイル分析結果</h1>
            <p>{{ filename }}</p>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">{{ analysis.row_count }}</div>
                <div class="stat-label">データ行数</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{{ analysis.column_count }}</div>
                <div class="stat-label">カラム数</div>
            </div>
            {% if analysis.company_count %}
            <div class="stat-item">
                <div class="stat-number">{{ analysis.company_count }}</div>
                <div class="stat-label">企業名データ</div>
            </div>
            {% endif %}
            {% if analysis.url_count %}
            <div class="stat-item">
                <div class="stat-number">{{ analysis.url_count }}</div>
                <div class="stat-label">URLデータ</div>
            </div>
            {% endif %}
            {% if analysis.email_count %}
            <div class="stat-item">
                <div class="stat-number">{{ analysis.email_count }}</div>
                <div class="stat-label">メールアドレス</div>
            </div>
            {% endif %}
        </div>
        
        <div class="card">
            <h3>📋 カラム情報</h3>
            <div class="column-list">
                {% for column in analysis.columns %}
                <div class="column-item">
                    <strong>{{ column }}</strong><br>
                    <small>NULL数: {{ analysis.null_counts[column] }}</small>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="card">
            <h3>📄 サンプルデータ (先頭5行)</h3>
            <table class="table">
                <thead>
                    <tr>
                        {% for column in analysis.columns %}
                        <th>{{ column }}</th>
                        {% endfor %}
                    </tr>
                </thead>
                <tbody>
                    {% for row in analysis.sample_data %}
                    <tr>
                        {% for column in analysis.columns %}
                        <td>{{ row[column] if row[column] else '' }}</td>
                        {% endfor %}
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div style="margin-top: 20px;">
            <a href="/" class="btn">戻る</a>
        </div>
    </div>
</body>
</html>
    """
    
    return render_template_string(template, filename=filename, analysis=analysis)

@app.route('/merge', methods=['POST'])
def merge_files():
    """ファイルマージ処理"""
    selected_files = request.form.getlist('files')
    output_name = request.form.get('output_name', 'merged_data')
    
    if not selected_files:
        return "マージするファイルが選択されていません", 400
    
    output_path, row_count = data_manager.merge_files(selected_files, output_name)
    
    if output_path:
        return f"""
        <html>
        <head><title>マージ完了</title></head>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>✅ ファイルマージが完了しました</h2>
            <p><strong>出力ファイル:</strong> {output_path}</p>
            <p><strong>データ件数:</strong> {row_count}件</p>
            <p><strong>マージしたファイル:</strong></p>
            <ul>
                {''.join([f'<li>{f}</li>' for f in selected_files])}
            </ul>
            <a href="/" style="background: #0078d4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">戻る</a>
        </body>
        </html>
        """
    else:
        return "マージに失敗しました", 500

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 HUGAN JOB データ管理ダッシュボード")
    print("=" * 80)
    print("📊 URL: http://localhost:5003")
    print("🔧 機能:")
    print("  - ファイル一覧・分析")
    print("  - 複数ファイルマージ")
    print("  - データ統計表示")
    print("=" * 80)
    
    app.run(debug=True, host='0.0.0.0', port=5003)
