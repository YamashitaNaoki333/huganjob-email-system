@echo off
chcp 65001 > nul
echo ========================================
echo 派生版メールマーケティングシステム
echo 統合ワークフロー実行スクリプト
echo ========================================
echo.

cd /d "%~dp0"

echo 📍 現在のディレクトリ: %CD%
echo.

echo 🔀 派生版システム: 元システムから独立
echo 📊 入力ファイル: data\derivative_input.csv
echo 📁 出力先: data\results\
echo.

set /p START_ID="開始企業ID (1-5): "
set /p END_ID="終了企業ID (1-5): "

echo.
echo 🚀 派生版統合ワークフローを実行しています...
echo 📋 処理範囲: ID %START_ID% から %END_ID% まで
echo.

python core_scripts\derivative_integrated_workflow.py --start-id %START_ID% --end-id %END_ID%

echo.
echo ✅ 派生版統合ワークフローが完了しました
echo 📊 結果を確認するには派生版ダッシュボードを起動してください
echo 🌐 http://127.0.0.1:5002/
echo.
pause
