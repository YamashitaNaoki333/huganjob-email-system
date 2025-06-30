@echo off
echo Git基本ファイル追加スクリプト
echo ================================

echo 1. .gitignoreを追加...
git add .gitignore

echo 2. README.mdを追加...
git add README.md

echo 3. 設定テンプレートを追加...
git add config/huganjob_email_config.ini.template
git add config/huganjob_dashboard_config.json

echo 4. サンプルデータを追加...
git add data/sample_companies.csv

echo 5. 現在の状況を確認...
git status

echo ================================
echo 基本ファイルの追加が完了しました
pause
