# jakcrimson.github.io

Personal research site of Pierre Lague — PhD student in physics-informed AI at
Inria, Rennes. Live at **https://jakcrimson.github.io**.

Static site, built with Jekyll, deployed to GitHub Pages by
`.github/workflows/jekyll.yml` on every push to `main`. The theme is written for
this site — no theme gem, no CSS or JS framework.

## Running it locally

```bash
bundle install
bundle exec jekyll serve
```

## How the content is organised

Three data files drive the whole site. Editing them is usually all that is
needed; the pages regenerate from them.

| File | Holds |
|---|---|
| `_data/cv.yml` | Positions and degrees — the source for `/work/` and `/cv/` |
| `_data/institutions.yml` | Institutions, their marks and links |
| `_data/taxonomy.yml` | The controlled vocabulary: topics, their groups, and kinds of work |
| `_data/nav.yml` | Primary navigation |

Each post declares:

```yaml
---
title: "…"
description: "…"        # shown in every listing and in search results
date: 2026-04-20 09:45:00
kind: review            # one of taxonomy.yml `kinds`
affiliation: inria      # an id from institutions.yml — files it under /work/
tags: [signal-processing, physics]   # ids from taxonomy.yml `topics` only
lang: en
featured: true          # optional — promotes it to the home page
---
```

`kind`, `affiliation` and `tags` are what place a post on the career page, the
topic index and the map on the home page. Adding a post files it everywhere at
once.

### Adding a topic

Add it to `_data/taxonomy.yml` under `topics` with an `id`, `label`, `group`
(`method`, `domain` or `tool`) and a one-line `note`. Its page and its node on
the map appear as soon as a post uses it.

### Adding an institution logo

Drop an SVG into `assets/img/logos/` named after the institution's `id`
(`inria.svg`, `sudo.svg`, …). Until the file exists the site renders a
typographic wordmark in its place, so nothing breaks while one is missing.
Give the SVG both a `viewBox` and matching `width`/`height` attributes.

## Checks

```bash
python3 tools/check_taxonomy.py
```

Fails the build if any post uses a tag, `kind` or `affiliation` outside the
controlled vocabulary, or is missing a `description`. It runs in CI.

## Licence

Site code under the MIT licence (see `LICENSE`). Written content and figures
are the author's. Institutional marks in `assets/img/logos/` belong to their
owners and are reproduced only to identify affiliations — see
`assets/img/logos/ATTRIBUTION.txt`.
