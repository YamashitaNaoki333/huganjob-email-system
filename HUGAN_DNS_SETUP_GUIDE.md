# HUGAN.co.jp DNS設定手順書

**作成日時**: 2025年6月19日  
**目的**: client@hugan.co.jpからの直接メール送信実現  
**対象**: HUGAN.co.jpドメインのDNS設定

---

## 概要

### 🎯 **目標**
- client@hugan.co.jpアドレスでSMTP認証
- SPF/DKIM認証の正常通過
- 迷惑メール判定の回避
- 現在のSMTPサーバー（f045.sakura.ne.jp）活用

### 📋 **必要な設定**
1. **SPFレコード**: sakura.ne.jp経由送信の許可
2. **MXレコード**: メール受信サーバーの指定
3. **DKIMレコード**: デジタル署名の設定
4. **メールアカウント**: client@hugan.co.jpの作成

---

## 前提条件の確認

### ✅ **確認事項**
- [ ] HUGAN.co.jpドメインの管理権限
- [ ] DNS設定変更の権限
- [ ] sakura.ne.jpアカウントの管理権限
- [ ] 現在のDNS設定のバックアップ

### 🔍 **現状調査**
```bash
# ドメイン調査ツールの実行
python domain_investigation_tool.py
```

---

## DNS設定手順

### 1. SPFレコードの設定

#### 📝 **設定内容**
```
レコードタイプ: TXT
ホスト名: hugan.co.jp
値: "v=spf1 include:_spf.sakura.ne.jp ~all"
TTL: 3600
```

#### 🔧 **設定手順**
1. DNS管理画面にログイン
2. TXTレコード追加を選択
3. 上記の値を入力
4. 設定を保存

#### ✅ **確認方法**
```bash
# SPFレコード確認
nslookup -type=TXT hugan.co.jp

# 期待される結果
hugan.co.jp text = "v=spf1 include:_spf.sakura.ne.jp ~all"
```

### 2. MXレコードの設定

#### 📝 **設定内容**
```
レコードタイプ: MX
ホスト名: hugan.co.jp
優先度: 10
値: f045.sakura.ne.jp
TTL: 3600
```

#### 🔧 **設定手順**
1. DNS管理画面でMXレコード追加
2. 優先度: 10
3. メールサーバー: f045.sakura.ne.jp
4. 設定を保存

#### ✅ **確認方法**
```bash
# MXレコード確認
nslookup -type=MX hugan.co.jp

# 期待される結果
hugan.co.jp mail exchanger = 10 f045.sakura.ne.jp
```

### 3. DKIMレコードの設定

#### 📋 **事前準備**
1. sakura.ne.jpコントロールパネルにログイン
2. DKIM設定画面にアクセス
3. HUGAN.co.jpドメイン用のDKIM鍵を生成
4. 公開鍵をコピー

#### 📝 **設定内容**
```
レコードタイプ: TXT
ホスト名: default._domainkey.hugan.co.jp
値: "v=DKIM1; k=rsa; p=[sakura.ne.jpで生成された公開鍵]"
TTL: 3600
```

#### 🔧 **設定手順**
1. sakura.ne.jpでDKIM鍵生成
2. 公開鍵をコピー
3. DNS管理画面でTXTレコード追加
4. ホスト名: default._domainkey.hugan.co.jp
5. 値に公開鍵を貼り付け
6. 設定を保存

#### ✅ **確認方法**
```bash
# DKIMレコード確認
nslookup -type=TXT default._domainkey.hugan.co.jp

# 期待される結果
default._domainkey.hugan.co.jp text = "v=DKIM1; k=rsa; p=..."
```

---

## sakura.ne.jpでのメールアカウント作成

### 🔧 **作成手順**

#### ステップ1: コントロールパネルアクセス
1. sakura.ne.jpコントロールパネルにログイン
2. 「メール設定」を選択
3. 「メールアドレス追加」をクリック

#### ステップ2: アカウント作成
```
メールアドレス: client@hugan.co.jp
パスワード: [強力なパスワードを設定]
容量: 1GB以上
転送設定: 必要に応じて設定
```

#### ステップ3: SMTP認証設定
```
SMTP認証: 有効
POP before SMTP: 無効（推奨）
IMAP: 有効（推奨）
```

### 📋 **作成後の確認事項**
- [ ] メールアドレスの作成完了
- [ ] SMTP認証の有効化
- [ ] パスワードの記録
- [ ] 接続テストの実行

---

## 設定変更のリスク評価

### ⚠️ **潜在的リスク**

#### 1. DNS設定ミス
- **リスク**: メール受信不可
- **対策**: 設定前のバックアップ取得
- **復旧**: 元の設定に戻す

#### 2. SPF設定エラー
- **リスク**: メール送信失敗
- **対策**: 段階的な設定変更
- **復旧**: SPFレコードの修正

#### 3. DKIM設定問題
- **リスク**: 認証失敗
- **対策**: sakura.ne.jpサポートとの連携
- **復旧**: DKIM無効化

### 🛡️ **リスク軽減策**

#### 1. 段階的移行
```
Phase 1: DNS設定のみ（メール送信は既存のまま）
Phase 2: テストアカウントでの送信テスト
Phase 3: 本格的な設定切り替え
```

#### 2. バックアップ計画
- 現在のDNS設定の記録
- 設定変更前の動作確認
- ロールバック手順の準備

#### 3. 監視体制
- DNS設定の反映確認
- メール送信テストの実行
- エラーログの監視

---

## 設定反映の確認

### 🕐 **反映時間**
- **SPFレコード**: 1-4時間
- **MXレコード**: 1-4時間  
- **DKIMレコード**: 1-4時間
- **完全反映**: 24-48時間

### ✅ **確認コマンド**

#### DNS設定確認
```bash
# 包括的な確認
python domain_investigation_tool.py

# 個別確認
nslookup -type=TXT hugan.co.jp
nslookup -type=MX hugan.co.jp
nslookup -type=TXT default._domainkey.hugan.co.jp
```

#### メール送信テスト
```bash
# SMTP接続テスト
python smtp_connection_test.py

# 実際の送信テスト
python client_hugan_email_test.py
```

---

## トラブルシューティング

### ❌ **問題: SPFレコードが反映されない**

#### 確認事項
1. DNS設定の構文確認
2. TTL設定の確認
3. DNS伝播の待機

#### 解決方法
```bash
# DNS伝播確認
dig TXT hugan.co.jp @8.8.8.8
dig TXT hugan.co.jp @1.1.1.1
```

### ❌ **問題: DKIM認証が失敗する**

#### 確認事項
1. 公開鍵の正確性
2. セレクター名の一致
3. sakura.ne.jp側の設定

#### 解決方法
1. sakura.ne.jpサポートに問い合わせ
2. DKIM鍵の再生成
3. 設定の再確認

### ❌ **問題: メール送信が失敗する**

#### 確認事項
1. SMTP認証情報
2. アカウントの有効性
3. ファイアウォール設定

#### 解決方法
1. 認証情報の再確認
2. アカウント設定の見直し
3. ネットワーク設定の確認

---

## 次のステップ

### 1. **DNS設定実装**
- SPF、MX、DKIMレコードの設定
- 設定反映の確認

### 2. **メールアカウント作成**
- client@hugan.co.jpアカウントの作成
- SMTP認証設定

### 3. **テスト実行**
- 接続テストの実行
- 送信テストの実行

### 4. **本格移行**
- 設定ファイルの更新
- 本格運用の開始

---

**重要**: DNS設定変更は慎重に行い、各ステップで動作確認を実施してください。問題が発生した場合は、即座に元の設定に戻せるよう準備しておくことが重要です。

---

## 参考資料

### 📚 **関連ドキュメント**
- `SMTP_CONFIGURATION_GUIDE.md` - SMTP設定変更手順
- `CLIENT_HUGAN_MIGRATION_PLAN.md` - 段階的移行計画
- `domain_investigation_tool.py` - DNS調査ツール
- `client_hugan_email_test.py` - テスト送信ツール
