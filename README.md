# 福利厚生検索アプリ MVP（参照用の完成版）

Streamlit + Supabase（スキーマ bts）。9モジュール構成。

## まず画面だけ見る（Supabase不要）
1. `pip install -r requirements.txt`
2. 環境変数でデモを指定して起動: PowerShell `$env:BTS_DEMO="1"; streamlit run app.py`／Mac `BTS_DEMO=1 streamlit run app.py`（secrets.toml に `demo = true` を書いてもよい）
3. 左で利用者を選んでログイン
データは seed/ のCSV。実勢価格はダミー。投稿やクーポン取得は再起動で消える

## 本番の手順（Supabase）
前提: Python 3.12 または 3.13（3.14 はライブラリが未対応）。

1. Supabase で `sql/001_schema.sql` → `sql/002_seed_tenant.sql` を実行。ダッシュボードの API 設定で Exposed schemas に `bts` を追加
2. Supabase Auth で利用者アカウントを作る（seed/users.csv のメール）。作成後、`bts.users.auth_id` に Auth の user id を入れる
3. Storage に公開バケット `post-photos` を作る（口コミの写真用）
4. `.streamlit/secrets.toml.example` を `secrets.toml` にコピーして値を入れる
5. `pip install -r requirements.txt`（Windowsで複数版がある場合は `py -3.12 -m venv .venv` で仮想環境を作る）
6. `python -m seed.load`（メニュー・プラン・利用者・支出額を投入）
7. `python -m prices.update`（一般サイトの価格を取得。楽天のアプリIDが空ならダミー価格）
8. `streamlit run app.py`

## 構成
| モジュール | ファイル |
|---|---|
| A 基盤 | db.py, models.py, auth.py, activity.py, app.py |
| B1 データ投入 | seed/*.csv, seed/load.py, ui/admin_page.py |
| B2 価格取得 | prices/rakuten.py, prices/update.py |
| C1 差額計算 | pricing.py |
| C2 検索 | search.py, ui/search_page.py |
| C3 一覧 | ui/results_page.py |
| D1 詳細 | ui/detail_page.py |
| D2 クーポン | coupon.py |
| D3 投稿・声 | posts.py, dialogs/post.py |

テスト: `python -m pytest tests`
