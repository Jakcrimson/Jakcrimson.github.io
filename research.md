---
layout: page
title: Research
kicker: Current work
permalink: /research/
lede: >-
  Artificial intelligence, machine learning and mathematics applied to concrete
  problems.
description: >-
  Pierre Lague's research — PhD at Inria on AI for the mechanical durability of
  systems under severe vibratory loads, with the DGA and the University of
  Angers.
---

## The thesis

**Artificial intelligence for the optimization of the mechanical durability of
systems subjected to severe vibratory loads** — a military application.

Started October 2025 at **Inria Rennes**, funded by the *Agence de l'innovation
de défense* and run as a consortium between the **DGA**, the **University of
Angers** and the **University of Rennes**.

## Areas

Machine learning and applied mathematics, currently around vibration fatigue and
damage estimation: signal characterisation in the time, frequency and
time–frequency domains, and feature engineering on non-stationary signals.

More recently, **extreme value statistics**.

Earlier: reinforcement learning and multi-agent systems, computer vision and
remote sensing, time-series forecasting.

## Reviews

{% assign reviews = site.posts | where: "kind", "review" %}
<ul class="entries">
{%- for p in reviews %}{% include entry.html post=p %}{% endfor -%}
</ul>

## Earlier research

Theses, research projects and the placements they came out of.

{% assign prior = site.posts | where_exp: "p", "p.kind == 'thesis' or p.kind == 'research' or p.kind == 'internship'" %}
<ul class="entries">
{%- for p in prior %}{% include entry.html post=p %}{% endfor -%}
</ul>

## Contact

<a href="#" data-mail-user="pierre.lague" data-mail-domain="protonmail.com" data-mail-show="true">email</a>
