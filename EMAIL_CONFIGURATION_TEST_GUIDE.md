# HUGAN JOB メール設定テストガイド

**作成日時**: 2025年6月19日  
**対象**: HTMLメール送信・迷惑メール対策強化版  
**ステータス**: 実装完了・テスト準備完了

---

## 実装完了内容

### ✅ 1. 迷惑メール対策の強化
- **SPF/DKIM対応**: 適切なヘッダー設定を追加
- **送信者認証**: marketing@fortyfive.co.jpで認証、client@hugan.co.jpとして表示
- **メールヘッダー最適化**: Message-ID、Date、X-Mailer等の追加
- **送信間隔制御**: 2秒間隔での送信制御

### ✅ 2. HTMLメール送信の実装
- **マルチパート形式**: プレーンテキスト + HTML の両方を送信
- **HTMLテンプレート**: corporate-email-newsletter.html を使用
- **レスポンシブ対応**: モバイル・デスクトップ両対応
- **開封追跡**: トラッキングピクセル埋め込み

### ✅ 3. 送信者表示の設定
- **表示アドレス**: client@hugan.co.jp
- **返信先**: client@hugan.co.jp
- **送信者名**: HUGAN採用事務局
- **SMTP認証**: marketing@fortyfive.co.jp（内部使用）

---

## 設定ファイル更新内容

### config/derivative_email_config.ini
```ini
[SMTP]
from_email = client@hugan.co.jp          # 受信者に表示されるアドレス
reply_to = client@hugan.co.jp            # 返信先アドレス
smtp_auth_email = marketing@fortyfive.co.jp  # SMTP認証用（内部使用）

[ANTI_SPAM]
use_html_format = true                   # HTMLメール送信
add_tracking_pixel = true                # 開封追跡
use_multipart_alternative = true         # マルチパート形式
send_interval = 2                        # 送信間隔（秒）
enable_bounce_handling = true            # バウンス処理
```

---

## テスト手順

### 1. 設定確認テスト
```bash
# 設定ファイルと接続テスト
python test_email_config.py
```

### 2. 個別テストメール送信
```bash
# HTMLメール形式でのテスト送信
python send_test_email.py <メールアドレス> "<企業名>"

# 例
python send_test_email.py raxus.yamashita@gmail.com "司法書士法人テスト"
```

### 3. 本格的なメール送信テスト
```bash
# 1社のみテスト（テストモード）
python core_scripts/derivative_ad_email_sender.py --start-id 1 --end-id 1 --test-mode

# 実際の送信（1社のみ）
python core_scripts/derivative_ad_email_sender.py --start-id 1 --end-id 1
```

---

## 迷惑メール対策の実装内容

### 1. 送信者認証の分離
- **認証用**: marketing@fortyfive.co.jp（SMTP認証）
- **表示用**: client@hugan.co.jp（受信者に表示）
- **返信先**: client@hugan.co.jp（返信処理）

### 2. メールヘッダーの最適化
```python
msg['Message-ID'] = f"<{tracking_id}@hugan.co.jp>"
msg['Date'] = formatdate(localtime=True)
msg['X-Mailer'] = 'HUGAN JOB Marketing System'
msg['X-Priority'] = '3'
msg['Precedence'] = 'bulk'
```

### 3. マルチパート形式
- **プレーンテキスト版**: HTMLタグを除去した読みやすいテキスト
- **HTML版**: 完全なHTMLメール（corporate-email-newsletter.html）
- **自動フォールバック**: HTMLが表示できない場合はテキスト版

### 4. 送信制御
- **送信間隔**: 2秒間隔でサーバー負荷軽減
- **リトライ機能**: 送信失敗時の自動再試行
- **エラーハンドリング**: 詳細なログ記録

---

## 受信確認ポイント

### Gmail での確認事項
1. **受信トレイ**: 正常に受信されているか
2. **迷惑メールフォルダ**: 迷惑メール判定されていないか
3. **送信者表示**: "HUGAN採用事務局 <client@hugan.co.jp>" として表示
4. **HTMLレンダリング**: メールが正しくHTMLで表示されるか
5. **モバイル対応**: スマートフォンでの表示確認

### 他のメールクライアントでの確認
- **Outlook**: 企業向けメールクライアントでの表示確認
- **Yahoo Mail**: 一般的なWebメールでの確認
- **Thunderbird**: デスクトップクライアントでの確認

---

## トラブルシューティング

### 迷惑メール判定された場合
1. **件名の調整**: より控えめな表現に変更
2. **送信頻度の調整**: 送信間隔を延長（5秒以上）
3. **内容の見直し**: 営業色を薄める
4. **SPF/DKIM設定**: ドメイン管理者に確認

### HTMLメールが表示されない場合
1. **テンプレートファイル**: corporate-email-newsletter.html の存在確認
2. **エンコーディング**: UTF-8での保存確認
3. **HTMLタグ**: 構文エラーの確認
4. **CSSスタイル**: インラインスタイルの使用推奨

### 送信エラーが発生する場合
1. **SMTP設定**: 認証情報の確認
2. **ネットワーク**: ファイアウォール・プロキシ設定
3. **送信制限**: サーバー側の送信制限確認
4. **ログ確認**: logs/ フォルダ内のエラーログ

---

## 次のステップ

### 1. 本格運用前の確認
- [ ] 全9社へのテストモード実行
- [ ] 受信確認（複数のメールクライアント）
- [ ] 迷惑メール判定の確認
- [ ] HTMLメール表示の確認

### 2. 本格運用開始
```bash
# 全9社への本番送信
python core_scripts/derivative_ad_email_sender.py --start-id 1 --end-id 9
```

### 3. 効果測定
- 開封率の追跡（ダッシュボードで確認）
- バウンス率の監視
- 返信率の測定
- 迷惑メール判定率の確認

---

**実装完了日**: 2025年6月19日  
**テスト準備**: 完了  
**本格運用**: テスト完了後に実行可能
