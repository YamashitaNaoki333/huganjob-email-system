@echo off
chcp 65001 > nul
echo ========================================
echo 派生版メールマーケティングシステム
echo ダッシュボード起動スクリプト
echo ========================================
echo.

cd /d "%~dp0"

echo 📍 現在のディレクトリ: %CD%
echo.

echo 🚀 派生版ダッシュボードを起動しています...
echo 📊 アクセスURL: http://127.0.0.1:5002/
echo 🔀 派生版システム: 元システムから独立
echo.

python dashboard\derivative_dashboard.py --port 5002

echo.
echo 👋 派生版ダッシュボードが終了しました
pause
