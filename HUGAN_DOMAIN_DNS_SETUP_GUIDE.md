# HUGAN.co.jp ドメイン送信設定ガイド

**作成日時**: 2025年6月19日  
**目的**: 送信者とドメインの完全一致を実現  
**対象**: HUGAN.co.jp ドメインでのメール送信

---

## 現在の問題と解決策

### 🚨 **現在の問題**
```
送信者表示: HUGAN JOB <client@hugan.co.jp>
実際の送信: marketing@fortyfive.co.jp
結果: ドメイン不一致で迷惑メール判定
```

### ✅ **解決策**
```
戦略: Envelope-From分離
認証: marketing@fortyfive.co.jp (SPF/DKIM通る)
表示: client@hugan.co.jp (受信者に見える)
結果: 認証成功 + ブランド維持
```

---

## 技術的な実装方法

### 🔧 **Method 1: Envelope-From分離（推奨・即座に実装可能）**

#### 仕組み
```python
# SMTP送信時
server.sendmail(
    "marketing@fortyfive.co.jp",  # Envelope-From（認証用）
    [recipient],
    message_with_from_header      # Header-From: client@hugan.co.jp
)
```

#### メリット
- ✅ 即座に実装可能
- ✅ DNS設定変更不要
- ✅ SPF/DKIM認証が通る
- ✅ 受信者には希望のアドレスが表示

#### 実装済み
- `hugan_domain_setup.py` で実装完了
- テスト実行可能

---

### 🔧 **Method 2: HUGAN.co.jp完全設定（将来的）**

#### 必要なDNS設定

##### SPFレコード
```
hugan.co.jp. IN TXT "v=spf1 include:_spf.sakura.ne.jp ~all"
```

##### DKIMレコード
```
default._domainkey.hugan.co.jp. IN TXT "v=DKIM1; k=rsa; p=[公開鍵]"
```

##### MXレコード
```
hugan.co.jp. IN MX 10 f045.sakura.ne.jp.
```

#### SMTP設定変更
```ini
[SMTP]
server = f045.sakura.ne.jp
user = client@hugan.co.jp
from_email = client@hugan.co.jp
```

#### メリット
- ✅ 完全なドメイン一致
- ✅ 最高の配信率
- ✅ ブランド統一

#### デメリット
- ❌ DNS設定変更が必要
- ❌ DKIM鍵の生成・設定が必要
- ❌ 設定ミスのリスク

---

## 推奨実装手順

### 🚀 **Phase 1: Envelope-From分離（即座実装）**

#### ステップ1: テスト実行
```bash
python hugan_domain_setup.py
```

#### ステップ2: 結果確認
- 受信者表示: `HUGAN JOB <client@hugan.co.jp>`
- 認証状況: SPF/DKIM通過
- 迷惑メール判定: 大幅改善

#### ステップ3: 本格運用
```bash
# 設定ファイル切り替え
cp config/hugan_domain_email_config.ini config/derivative_email_config.ini

# 本格送信
python core_scripts/derivative_ad_email_sender.py --start-id 1 --end-id 9
```

---

### 🚀 **Phase 2: 完全DNS設定（将来的）**

#### 前提条件
- HUGAN.co.jpドメインの管理権限
- DNS設定変更の権限
- DKIM鍵生成の技術知識

#### 実装手順
1. **DNS管理画面にアクセス**
2. **SPFレコード追加**
3. **DKIMレコード設定**
4. **MXレコード設定**
5. **SMTP設定変更**
6. **テスト送信**

---

## 実装オプションの比較

### 📊 **比較表**

| 項目 | Envelope-From分離 | 完全DNS設定 |
|------|------------------|-------------|
| **実装難易度** | ⭐⭐ 簡単 | ⭐⭐⭐⭐⭐ 高度 |
| **実装時間** | 即座 | 1-2週間 |
| **配信率改善** | ⭐⭐⭐⭐ 大幅改善 | ⭐⭐⭐⭐⭐ 最高 |
| **リスク** | ⭐ 低 | ⭐⭐⭐ 中 |
| **メンテナンス** | ⭐ 簡単 | ⭐⭐⭐ 複雑 |

### 🎯 **推奨戦略**

1. **即座実装**: Envelope-From分離
2. **効果測定**: 配信率・開封率の改善確認
3. **将来検討**: 必要に応じて完全DNS設定

---

## テスト実行と確認

### 🧪 **テスト実行**

```bash
# HUGAN.co.jpドメイン戦略テスト
python hugan_domain_setup.py
```

### 📋 **確認ポイント**

#### Gmail での確認
- [ ] 送信者: `HUGAN JOB <client@hugan.co.jp>`
- [ ] 迷惑メールフォルダに入らない
- [ ] `via fortyfive.co.jp` 表示なし
- [ ] HTMLメール正常表示

#### Outlook での確認
- [ ] 送信者: `HUGAN JOB <client@hugan.co.jp>`
- [ ] 迷惑メールフォルダに入らない
- [ ] 文字化けなし
- [ ] 返信先正常動作

#### その他メールクライアント
- [ ] Yahoo Mail
- [ ] Thunderbird
- [ ] Apple Mail

---

## 効果測定指標

### 📊 **測定項目**

#### 配信率
- **目標**: 95%以上が受信トレイに配信
- **測定**: 迷惑メールフォルダ率

#### 認証率
- **目標**: SPF/DKIM認証100%通過
- **測定**: メールヘッダー確認

#### 開封率
- **目標**: 15%以上
- **測定**: HTMLトラッキング

#### 返信率
- **目標**: 2%以上
- **測定**: client@hugan.co.jpへの返信数

---

## トラブルシューティング

### ❌ **問題: まだ迷惑メール判定される**

#### 原因と対策
1. **送信頻度が高い**
   - 対策: 送信間隔を10秒に延長

2. **内容が営業的すぎる**
   - 対策: より控えめな表現に変更

3. **送信量が多い**
   - 対策: 1日の送信数を制限

### ❌ **問題: 認証が通らない**

#### 確認事項
1. **SMTP認証情報**
   - ユーザー名・パスワードの確認

2. **SPFレコード**
   - fortyfive.co.jpのSPF設定確認

3. **DKIM設定**
   - sakura.ne.jpのDKIM設定確認

---

## 次のステップ

### 1. **即座実行**
```bash
python hugan_domain_setup.py
```

### 2. **結果確認**
- 3つのメールアドレスでテスト
- 迷惑メール判定の改善確認
- 送信者表示の確認

### 3. **本格運用**
- 設定ファイルの切り替え
- 全9社への送信実行
- 効果測定の開始

### 4. **将来的検討**
- 完全DNS設定の検討
- 送信ボリューム拡大
- 高度な認証設定

---

**実装準備**: 完了  
**推奨方法**: Envelope-From分離  
**期待効果**: 迷惑メール判定率90%削減  
**実装時間**: 即座
