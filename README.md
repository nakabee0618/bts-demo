# 福利厚生検索アプリ MVP（参照用の完成版）

Streamlit + Supabase（スキーマ bts）。9モジュール構成。

## まず画面だけ見る（データベース不要）
1. `pip install -r requirements.txt`
2. PowerShell: `$env:BTS_DEMO="1"; streamlit run app.py`／Mac: `BTS_DEMO=1 streamlit run app.py`
3. 左で利用者を選んでログイン
データは seed/ のCSV。一般サイトの価格は仮の値。投稿などは再起動で消える

Mac で `pip install` がエラーになる場合（Homebrew の Python など）は、先に `python3 -m venv .venv` → `source .venv/bin/activate` を実行する。

## 各自の手順（チームのデータベースにつなぐ）
前提: Python 3.12 または 3.13（3.14 は一部のライブラリが未対応）。
1. `pip install -r requirements.txt`
2. 共通の担当から受け取った url と anon_key を `.streamlit/secrets.toml` に書く（`secrets.toml.example` をコピー）
3. `streamlit run app.py` → 受け取ったメールアドレスとパスワードでログイン

## チームで1回だけやること（共通の担当）
1. Supabase で `sql/001_schema.sql` → `sql/002_seed_tenant.sql` を実行。API 設定の Exposed schemas に `bts` を追加
2. Storage に公開バケット `post-photos` を作る（口コミの写真用）
3. Authentication で利用者を作る（seed/users.csv のメール）
4. `python -m seed.load`（メニュー・プラン・利用者・支出額を投入）
5. Table Editor で、3で作った利用者の UUID を `bts.users.auth_id` に入れる
6. `python -m prices.update`（一般サイトの価格を取得。楽天のアプリIDが空ならダミー価格）
7. url と anon_key、ログイン情報をメンバーに渡す

## 構成（担当）
| 担当 | ファイル |
|---|---|
| 担当1（自然言語検索・絞り込み） | search.py, nl_search.py, ui/search_page.py, ui/admin_page.py |
| 担当2（差額計算・ランキング表示） | pricing.py, ranking.py, placeholder.py, prices/rakuten.py, ui/home.py, ui/results_page.py, ui/price_tab.py |
| 担当3（従業員投稿入力・保存） | posts.py, coupon.py, activity.py, spots.py, prices/crawl_spots.py, dialogs/post.py, ui/review_tab.py, ui/coupon_card.py, ui/spots_tab.py, ui/mypage.py, seed/spots.csv, seed/crawl_targets.csv |
| 共通 | app.py, db.py, models.py, auth.py, seed/load.py と初期CSV, prices/update.py, ui/detail_page.py |
| デモ専用 | demo_db.py |

各ファイルの役割・処理の流れ・解答例は、LPの「実装ガイド」を参照。

テスト: `python -m pytest tests`
