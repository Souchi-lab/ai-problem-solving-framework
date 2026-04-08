# Result

---

## Status

Completed

---

## Branch Taken

Branch B

- client-side `title` update
- client-side `meta[name="description"]` update
- viewer-page OGP left out of scope

---

## What The Investigation Confirmed

The current SoChi BLOCKS structure already separates two metadata roles:

- viewer page
  - interactive puzzle play
  - currently generic metadata
- share page
  - per-puzzle social metadata
  - redirects into the viewer

This means viewer-page OGP is not the only path for puzzle-specific metadata.
It is already covered by the `docs/share/*.html` path.

So Branch B was not a fallback.
It was the implementation path that correctly matched the current architecture.

---

## What Changed

In the viewer app:

- `document.title` is now updated per puzzle
- `meta[name="description"]` is now updated per puzzle
- the metadata is derived from:
  - puzzle id
  - current difficulty derived from piece count
  - current language

Implementation stayed local:

- one `useEffect` in the viewer app
- no routing redesign
- no SSR / prerender work
- no share-page rewrite

---

## What Was Not Changed

- No viewer-page OGP implementation
- No SSR / prerender introduction
- No full SEO overhaul
- No structured-data work

This is intentional.

Viewer-page OGP would require a broader structural solution than this follow-up
was meant to introduce.

---

## Verification

- The metadata path was investigated before implementation
- The viewer app build passed after the change
- The current architecture now has:
  - share-page OGP
  - viewer-page title/description

Build note:

- `npm run build` succeeded
- only the existing large-chunk warning remained

---

## Stable Baseline

The repo now has a cleaner metadata split:

- `docs/share/*.html` handles per-puzzle OGP / social preview
- the viewer app handles per-puzzle runtime title and description

This is a meaningful improvement without requiring immediate SSR or prerender
work.

---

## Next Trigger

If puzzle-page search/share requirements grow later, the next natural question
is:

- whether viewer-page metadata should move beyond runtime updates into static or
  prerendered output

That would be a broader follow-up.
