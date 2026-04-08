# Static HTML Japanese Fix Pattern
---
## When To Use

Use this when a static HTML file shows unstable Japanese text after scripted edits.

Typical signs:

- terminal output shows `?` or mojibake
- browser rendering is broken or partially broken
- HTML structure near the edited copy may also have been damaged

## Core Rule

Do not trust shell output alone for Japanese copy in static HTML.

Close the change only after:

1. the HTML structure is confirmed intact
2. the browser rendering is confirmed correct

## Repair Order

1. restore the exact HTML block first
2. fix malformed tags before judging copy
3. re-check the browser
4. if Japanese is still unstable, switch the Japanese strings to HTML numeric entities

## Why Numeric Entities Are Acceptable

For static HTML, numeric entities are a valid escape hatch when direct Japanese text becomes unreliable through scripted patching or encoding noise.

They are especially useful when:

- the page is static
- the strings are short
- browser rendering correctness matters more than source readability

## Stable Baseline

For static HTML Japanese edits:

- shell output is not the final verifier
- browser rendering is the final verifier
- numeric entities are an acceptable fallback
