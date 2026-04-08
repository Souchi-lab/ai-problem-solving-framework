# Build

---

## Branch Taken: B

Client-side title + meta description update only.

OGP is already handled by the share page path (`docs/share/*.html`).
Viewer-page OGP requires SSR or prerender and is out of scope for this run.

---

## Investigation Summary

| Item | Finding |
|---|---|
| Current `<title>` | Generic: "SoChi BLOCKS — 3D Viewer" in `viewer.html` |
| Head management | None — static HTML head, no Helmet, no `document.title` update |
| Prerender / SSR | Not present — standard Vite static build |
| OGP coverage | Already exists on `docs/share/*.html` per-puzzle share pages |
| Share → viewer flow | Share page sets OGP, then redirects to `viewer.html?puzzle_id=...` |

---

## What to Implement

### Target

`frontend/src/App.tsx` (or the component that receives `puzzle_id`)

### Change

Add a `useEffect` that updates `document.title` and the meta description tag
when `puzzle_id` is available.

```ts
useEffect(() => {
  if (!puzzleId) return;

  document.title = `Puzzle ${puzzleId} — SoChi BLOCKS`;

  const metaDesc = document.querySelector('meta[name="description"]');
  if (metaDesc) {
    metaDesc.setAttribute(
      'content',
      `Play SoChi BLOCKS puzzle ${puzzleId}. Place all pieces to solve it.`
    );
  }
}, [puzzleId]);
```

Adjust the title/description strings to match the actual puzzle naming
convention used in the app.

---

## What Was Not Done

- OGP tags on viewer page (social crawlers need SSR — not this run)
- Helmet or head-management library introduction
- Routing changes
- Changes to share page OGP (already correct)
- SSR / prerender introduction

---

## Scope Confirmation

| Change | Allowed | Status |
|---|---|---|
| `document.title` per puzzle | ✅ | Implement |
| `meta[name="description"]` per puzzle | ✅ | Implement |
| OGP on viewer page | ❌ (needs SSR) | Out of scope |
| Share page OGP | already done | No change |

---

## Verification Steps

1. Open `viewer.html?puzzle_id=XXX` in browser
2. Check browser tab title — should show puzzle-specific title
3. Inspect `<meta name="description">` in DevTools — should be per-puzzle
4. Confirm `npm run build` passes
5. Confirm share page OGP is unchanged

---

## Result Evaluation Frame

result.md should answer:

1. Is the browser tab title now per-puzzle?
2. Is the meta description now per-puzzle?
3. Did OGP stay covered by the share page path?
4. Did the change stay in one component?
5. What still remains (viewer-page OGP) and what would it require?
