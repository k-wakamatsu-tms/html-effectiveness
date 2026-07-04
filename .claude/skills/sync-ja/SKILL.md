---
name: sync-ja
description: upstream (ThariqS/html-effectiveness) の変更を取り込んだ後、ja/ 配下の日本語訳を同期更新するワークフロー。ユーザーが「upstream を取り込む」「本家の更新を反映」「日本語版を更新」「翻訳を同期」「ja を最新化」「フォーク元の変更をマージ」などと言ったとき、または upstream からの merge/pull を行った直後には必ずこのスキルを使うこと。英語 HTML の追加・変更・削除を検出し、対応する日本語訳の作成・更新・削除・検証・公開までを行う。
---

# upstream 取り込み後の日本語訳 (ja/) 同期

## 背景

このリポジトリは ThariqS/html-effectiveness のフォーク。英語の自己完結型 HTML サンプル集が本体で、`ja/` 配下に**同一のディレクトリ構成**で日本語訳を保持している(例: `03-code-review-pr.html` ↔ `ja/03-code-review-pr.html`、`unknowns/index.html` ↔ `ja/unknowns/index.html`)。

翻訳は「DOM 構造・CSS・JS ロジックを一切変えず、画面に表示されるテキストだけを日本語化」した 1:1 対応。この対応関係を保つことが最重要で、構造が英語版とずれると検証スクリプトが検出する。

GitHub Pages (legacy build, main ブランチ / ルート) で公開中:
- 英語: https://k-wakamatsu-tms.github.io/html-effectiveness/
- 日本語: https://k-wakamatsu-tms.github.io/html-effectiveness/ja/

## ワークフロー

### 1. upstream を取り込む(まだの場合)

```bash
git fetch upstream
git merge upstream/main
```

- コンフリクトが出た場合、英語 HTML は upstream 側を採用する。
- `README.md` がコンフリクトしたら、upstream の変更を取り込みつつ、フォーク独自の「## 日本語版」セクション(ja/ への案内と Pages の URL)は必ず残す。
- **マージをコミットしてから**次のステップへ進む(差分検出は git で追跡されたファイルを対象とするため)。

### 2. 差分を検出する

```bash
python .claude/skills/sync-ja/scripts/detect_changes.py
```

JSON で次の 4 つのリストが出力される:

- `add` — 英語版が新規追加され、ja/ に訳がまだないファイル
- `update` — ja/ の最終更新以降に英語版の内容が変わったファイル
- `delete` — 英語版が削除されたのに残っている ja/ ファイル
- `ok` — 同期済みのファイル

すべて `ok` なら何もすることはない。その旨をユーザーに報告して終了。

### 3. ファイルごとに処理する

**add(新規翻訳)**: 後述の翻訳ルールに従って `ja/<同じ相対パス>` に日本語版を作成する。新しいサブディレクトリが必要なら作る。

**update(差分反映)**: まず英語側で何が変わったかを確認する:

```bash
BASE=$(git log -1 --format=%H -- "ja/<path>")
git diff $BASE HEAD -- "<path>"
```

- 変更が部分的なら、対応する箇所だけを ja/ ファイルに Edit で反映する(既存の訳語・文体を踏襲する)。
- ファイルの過半が書き換わっているなら、既存の ja/ ファイルを用語の参考にしつつ全体を再翻訳する。

**delete**: 対応する ja/ ファイルを削除する。

対象が多い場合(目安 5 ファイル超)は、subagent や Workflow でファイル単位に並列化してよい。その際は各エージェントに翻訳ルール全文を渡すこと。

### 4. 検証する

作成・更新した各ファイルについて:

```bash
python .claude/skills/sync-ja/scripts/verify_translation.py "<en-path>" "ja/<path>"
```

全チェックが PASS するまで修正する。加えて、見出し・ボタン・本文から 5 箇所ほど目視で拾い、英語のまま残っていないか・不自然な訳がないかを確認する。

### 5. コミット・push・公開確認

1. `git status` で対象が ja/ (と README 等の意図した変更) だけであることを確認してからコミットする。コミットメッセージ例: `Sync ja/ with upstream (<upstream短縮SHA>)`
2. `git push origin main`
3. GitHub Pages は push で自動的に再ビルドされる。数分待っても反映されない・デプロイが失敗した場合は再キューする(初回や直後は一時的エラー "Deployment failed, try again later." がまれに起きる):

```bash
gh api --method POST repos/k-wakamatsu-tms/html-effectiveness/pages/builds
```

4. 最後に日本語版 URL に実際にアクセスして反映を確認する。

## 翻訳ルール

このルールは全訳・部分更新のどちらにも適用する。並列化する場合は各エージェントにこの節を丸ごと渡すこと。

- 画面に表示されるテキストはすべて自然でプロフェッショナルな日本語に翻訳する: 見出し・段落・リスト・テーブルのセル/ヘッダ・ボタン/リンクのラベル・フォームラベル・ツールチップ・キャプション・バッジ・ステータス表示・チャートの凡例/軸ラベル・SVG の `<text>`/`<tspan>`・`alt`/`title`/`aria-label`/`placeholder` 属性値・`<title>` 要素。
- `<script>` 内: コードのロジック・変数/関数/クラス名・JSON キー・CSS セレクタ・制御フローは**完全に不変**。翻訳するのは末端ユーザーに表示される文字列リテラルだけ(`textContent`/`innerText`/`value` に代入される UI 文字列、画面表示用データ配列内のラベル、alert/confirm のメッセージなど)。`console.log` や実装コメントは翻訳しない。
- `<style>` 内: **一切変更しない**。
- `<html lang="en">` → `<html lang="ja">` に変更する。
- ファイル先頭の著作権コメント(`Copyright 2026 Anthropic PBC …`)は原文のまま保持する。
- 架空ブランド "Acme" や人名などの固有名詞は原文のまま(音訳しない)。
- 数値・パーセント・通貨・日付、およびプログラミング例として表示されるコード(diff やスニペットの中身)は不変。ただしその周辺の説明文・コメンタリーは翻訳する。
- 相対リンク(プロジェクト内の他ファイルを指す `href`/`src`、例: `01-….html`、`../index.html`)は**完全に不変**。
- 翻訳以外で HTML 要素・コメント・属性を追加・削除・並べ替えしない。言語スイッチャーなど新規 UI の追加も禁止。純粋な 1:1 のテキストローカライズであり、DOM 構造は原文と構造的に同一でなければならない。
- インデント・整形スタイルは原文をできるだけ踏襲する。
- 出力は完全で well-formed な HTML であること(途中で切れない)。
