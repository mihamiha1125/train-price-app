# 鉄道模型 落札相場アプリ

ヤフオクの「落札相場」を **毎日 7時・12時・19時（JST）** に自動取得し、スマホで見られるアプリ（PWA）です。
サーバー代は不要で、GitHub だけで動きます。

```
GitHub Actions（1日3回）──▶ scraper/fetch.py ──▶ docs/data/*.json をコミット
                                                      │
スマホ（ホーム画面のアプリ）◀── GitHub Pages（docs/）◀─┘
```

## セットアップ（初回のみ・約5分）

1. GitHub で新しいリポジトリを作成（例: `train-price-app`）。このフォルダの中身をすべてプッシュ
   ```bash
   git init && git add . && git commit -m "init"
   git branch -M main
   git remote add origin https://github.com/<あなたのID>/train-price-app.git
   git push -u origin main
   ```
2. リポジトリの **Settings → Pages** で Source を「Deploy from a branch」、Branch を `main` / `/docs` にして保存
3. **Actions** タブで「ヤフオク落札相場の取得」→ **Run workflow** を押して動作確認
4. スマホで `https://<あなたのID>.github.io/train-price-app/` を開き、ホーム画面に追加
   - iPhone: Safari の共有ボタン →「ホーム画面に追加」
   - Android: Chrome のメニュー →「ホーム画面に追加 / アプリをインストール」

> 無料プランのリポジトリを **Private** にすると GitHub Pages が使えません。Public で運用してください（公開されるのは価格の集計データのみです）。

## 表示される値

| 項目 | 内容 |
|---|---|
| 直近の落札平均 | 取得時点で新しい順に最大100件の落札価格の平均（朝昼晩で変動を追う指標） |
| 中央値 | 同じ100件の中央値（ジャンク品・高額品の影響を受けにくい） |
| 公式相場平均 | ヤフオクの落札相場ページに表示される平均（過去約120日） |
| 落札件数 | 過去約120日の落札件数 |

## キーワードを変える

`scraper/keywords.json` を編集してプッシュするだけで、アプリのタブも自動で変わります。

```json
{ "id": "kiha", "label": "キハ", "query": "Nゲージ キハ" }
```
`id` は英数字で一意に。過去データは `id` ごとに保存されます。

## ローカルで試す

```bash
python3 scraper/fetch.py
python3 -m http.server 8765 -d docs
```

## 注意

- 取得時刻は GitHub Actions の混雑で数分〜数十分遅れることがあります。
- ヤフオクのページ構造が変わると取得に失敗します（Actions の実行が赤くなります。`fetch.py` の `__NEXT_DATA__` 解析部分を修正してください）。
- 個人利用の範囲で、取得頻度を上げすぎないようにしてください（Yahoo! JAPAN の利用規約に従ってください）。
