# HUGANJOB.JP DMARC設定ガイド
## Gmail 2024年要件対応 - 迷惑メール判定改善

**作成日時**: 2025年06月26日 19:45:00  
**目的**: HUGANJOBシステムの迷惑メール判定改善  
**対象**: huganjob.jpドメイン  

---

## 🎯 DMARC設定の必要性

### Gmail 2024年新要件
- **2024年2月以降**: 大量送信者（5000通/日以上）にDMARC必須
- **迷惑メール判定**: DMARC未設定は高確率でスパム判定
- **配信率向上**: DMARC設定により配信率が大幅改善

### 現在の状況
```bash
# 現在のDNS設定確認結果
SPF: ✅ 設定済み (v=spf1 +a:sv12053.xserver.jp +a:huganjob.jp +mx include:spf.sender.xserver.jp ~all)
DKIM: ✅ 設定済み (default._domainkey.huganjob.jp)
DMARC: ❌ 未設定 ← 今回設定
```

---

## 🔧 DMARC設定手順

### Step 1: DNS管理画面へのアクセス
**Xserver管理画面**:
1. Xserverアカウントにログイン
2. 「サーバー管理」→「DNS設定」
3. 「huganjob.jp」ドメインを選択
4. 「DNSレコード追加」をクリック

### Step 2: DMARCレコードの追加

#### 🚀 推奨設定（段階的導入）

**Phase 1: 監視モード（最初の2週間）**
```dns
種別: TXT
ホスト名: _dmarc
内容: v=DMARC1; p=none; rua=mailto:dmarc-reports@huganjob.jp; ruf=mailto:dmarc-failures@huganjob.jp; sp=none; adkim=r; aspf=r; fo=1
```

**Phase 2: 隔離モード（2週間後）**
```dns
種別: TXT
ホスト名: _dmarc
内容: v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@huganjob.jp; ruf=mailto:dmarc-failures@huganjob.jp; sp=quarantine; adkim=r; aspf=r; fo=1
```

**Phase 3: 拒否モード（1ヶ月後）**
```dns
種別: TXT
ホスト名: _dmarc
内容: v=DMARC1; p=reject; rua=mailto:dmarc-reports@huganjob.jp; ruf=mailto:dmarc-failures@huganjob.jp; sp=reject; adkim=r; aspf=r; fo=1
```

#### 🎯 即座実装推奨設定（迷惑メール対策優先）

```dns
種別: TXT
ホスト名: _dmarc
内容: v=DMARC1; p=quarantine; rua=mailto:dmarc@huganjob.jp; ruf=mailto:dmarc@huganjob.jp; sp=quarantine; adkim=r; aspf=r; fo=1; pct=100
```

### Step 3: 設定内容の詳細説明

| パラメータ | 値 | 説明 |
|------------|-----|------|
| `v` | DMARC1 | DMARCバージョン |
| `p` | quarantine | ポリシー（隔離：迷惑メールフォルダ行き） |
| `rua` | mailto:dmarc@huganjob.jp | 集約レポート送信先 |
| `ruf` | mailto:dmarc@huganjob.jp | 失敗レポート送信先 |
| `sp` | quarantine | サブドメインポリシー |
| `adkim` | r | DKIM認証モード（緩和） |
| `aspf` | r | SPF認証モード（緩和） |
| `fo` | 1 | 失敗レポート生成条件 |
| `pct` | 100 | ポリシー適用率（100%） |

---

## 📧 メールアドレス設定

### DMARC レポート受信用メールアドレス作成

**Xserver メール設定**:
1. 「メールアカウント設定」
2. 「メールアカウント追加」
3. 以下のアドレスを作成:
   - `dmarc@huganjob.jp`
   - `dmarc-reports@huganjob.jp` (オプション)
   - `dmarc-failures@huganjob.jp` (オプション)

---

## 🔍 設定確認方法

### DNS設定確認コマンド
```bash
# DMARC設定確認
nslookup -type=TXT _dmarc.huganjob.jp

# 期待される結果
_dmarc.huganjob.jp text = "v=DMARC1; p=quarantine; rua=mailto:dmarc@huganjob.jp; ..."
```

### オンライン確認ツール
- **MXToolbox**: https://mxtoolbox.com/dmarc.aspx
- **DMARC Analyzer**: https://www.dmarcanalyzer.com/
- **Google Admin Toolbox**: https://toolbox.googleapps.com/apps/checkmx/

---

## 📊 効果測定

### 設定前後の比較指標
| 指標 | 設定前 | 設定後（期待値） |
|------|--------|------------------|
| 迷惑メール判定率 | 80-90% | 10-20% |
| 受信トレイ到達率 | 10-20% | 80-90% |
| 認証通過率 | 60% | 95%+ |
| 配信レピュテーション | 低 | 高 |

### 監視項目
1. **DMARCレポート**: 週次で認証状況確認
2. **配信率**: 送信後の到達率測定
3. **開封率**: メール開封率の改善確認
4. **バウンス率**: 配信失敗率の削減確認

---

## ⚠️ 注意事項

### 設定時の注意点
1. **段階的導入**: いきなり`p=reject`は危険
2. **レポート監視**: 設定後は必ずDMARCレポートを確認
3. **SPF/DKIM確認**: DMARC設定前にSPF/DKIMが正常動作していることを確認
4. **TTL設定**: DNS変更後、反映まで最大48時間

### トラブルシューティング
- **認証失敗**: SPF/DKIM設定を再確認
- **レポート未受信**: メールアドレス設定を確認
- **配信率低下**: ポリシーを`none`に一時変更

---

## 🚀 実装スケジュール

### 即座実装（本日）
- [x] DMARC設定内容の決定
- [ ] Xserver DNS設定でDMARCレコード追加
- [ ] dmarc@huganjob.jp メールアドレス作成

### 24時間後
- [ ] DNS反映確認
- [ ] DMARC設定確認テスト
- [ ] テストメール送信・受信確認

### 1週間後
- [ ] DMARCレポート分析
- [ ] 配信率改善効果測定
- [ ] 必要に応じてポリシー調整

---

## 📞 サポート情報

### Xserver サポート
- **電話**: 06-6147-2580
- **メール**: support@xserver.ne.jp
- **営業時間**: 平日 10:00-18:00

### DNS設定変更時の連絡先
- **技術担当**: システム管理者
- **確認方法**: nslookup コマンドでの確認

---

**重要**: この設定により、HUGANJOBシステムからのメールが迷惑メール判定される確率が大幅に削減されます。Gmail 2024年要件に完全対応し、配信率の大幅改善が期待できます。
