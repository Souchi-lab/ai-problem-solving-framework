# Plan

---

## Follow-up Context

- Parent series: SoChi BLOCKS 初回体験改善
- Previous result: how-to-page-relief — 遊び方ページ不安解消化完了。Open Conditional に「動画タブとページ言語トグルが独立している」を記録
- New trigger: 言語切替はテキストに効くが、how-to-play.html の動画タブ（JP/EN）がページ言語に連動していない
- Scope limit: `docs/index.html` と `docs/how-to-play.html` の JS のみ
- Non-goals: i18n ライブラリ導入 / 翻訳内容の見直し / 多言語運用フロー設計

---

## Run Metadata

- Follow-up: language-toggle
- Goal: ページ言語切替と動画タブを同期させ、言語の切り替えを一操作で完結させる
- Output focus: `docs/how-to-play.html` の JS 差分（数行）
- Non-goal reminder: 翻訳管理・i18n 設計には踏み込まない

---

## Goal Readiness Check

- 現状の toggle 実装を確認済み（localStorage + CSS data-lang + applyLang()）
- ギャップが特定できている
- 変更箇所が数行に閉じると確認できている

Decision: Proceed

---

## Problem Structure

### 現状の言語切替状態

| 機能 | 状態 |
|---|---|
| テキスト言語切替（`.ja`/`.en` CSS） | ✅ 動作中 |
| localStorage 共有（`sochi_lang`） | ✅ ページ間で引き継がれる |
| ページ言語ボタン（header の EN/JP） | ✅ 動作中 |
| 動画タブ（JP/EN）のページ言語連動 | ❌ 独立している |

### ギャップの詳細

`how-to-play.html` の `applyLang()` は data-lang をセットするが `switchLangVideo()` を呼ばない:

```javascript
// 現状
function applyLang(lang) {
  document.documentElement.setAttribute('data-lang', lang);
  const btn = document.getElementById('lang-btn');
  if (btn) btn.textContent = lang === 'ja' ? 'EN' : 'JP';
  // ← ここで switchLangVideo が呼ばれない
}
```

結果:
- 英語ユーザーがページを開く → テキストは英語に切り替わる → **動画タブは JP のまま**
- header の EN/JP を押す → テキストは切り替わる → **動画タブは切り替わらない**

---

## Selected Approach

### 変更: `applyLang()` に動画タブ同期を追加（how-to-play.html のみ）

```javascript
function applyLang(lang) {
  document.documentElement.setAttribute('data-lang', lang);
  const btn = document.getElementById('lang-btn');
  if (btn) btn.textContent = lang === 'ja' ? 'EN' : 'JP';
  // 動画タブが存在する場合のみ同期
  if (document.getElementById('tab-ja')) {
    switchLangVideo(lang);
  }
}
```

`document.getElementById('tab-ja')` の存在チェックで、index.html 側に影響しない。
`switchLangVideo()` は既存関数をそのまま再利用。

---

## Scope Policy

この follow-up に含めるもの:
- `how-to-play.html` の `applyLang()` に動画タブ同期を追加（3〜4行）

この follow-up に含めないもの:
- index.html の変更
- i18n ライブラリ導入
- 翻訳内容の変更
- 動画タブの UI デザイン変更

---

## Deliverables

- `docs/how-to-play.html` の JS 差分（3〜4行）
- result での SC 評価

---

## Review Checklist

- 英語ユーザーがページを開いたとき、動画タブが EN になっている
- header の EN/JP を押したとき、動画タブが連動して切り替わる
- index.html に影響していない
- `switchLangVideo()` の autoplay 挙動が問題ないこと

---

## What This Follow-up Decides

- ページ言語と動画タブを 1 つの `applyLang()` で同期させる

## What This Follow-up Does Not Decide

- i18n の全体設計
- 言語検出ロジックの変更
- 動画タブを廃止して page lang toggle に統合するかどうか
