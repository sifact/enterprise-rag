# Design plan: Enterprise RAG demo

## Brief

- **Subject:** an internal company assistant that answers from company documents and only shows each employee what their team is allowed to read.
- **Audience:** potential customers: heads of operations, IT and security, and team leads who buy software but don't build it.
- **Primary job:** make access control something you can *see*. Switch teams, ask the same question, and watch the answer, the sources and the refusals change.

## The one memorable thing

**Clearance colours.** Each of the 7 teams has its own colour. It appears on the team switcher, on every source passage (as small badges for the teams that may read it) and on refusals. Colour carries information: a reader learns "who can see this" at a glance. Everything else stays quiet: neutral surfaces, one type family, no decoration.

## Tokens

### Colour

| Name | Dark (default) | Light | Use |
|---|---|---|---|
| ink | `#141A23` | `#F5F7FA` | page background (cool, not cream; not neutral black) |
| panel | `#1B2330` | `#FFFFFF` | raised areas |
| rule | `#2C3747` | `#D9DFE7` | borders, dividers |
| text | `#E7EBF1` | `#17202B` | body text |
| muted | `#9BA7B6` | `#566273` | secondary text |
| focus | `#7FB0FF` | `#1D5FD1` | keyboard focus ring and links |

Team colours (dark / light, both pass 4.5:1 on their panel for text):

| Team | Dark | Light |
|---|---|---|
| engineering | `#6EA2FF` | `#1F5CC4` |
| hr | `#F08DAE` | `#B03566` |
| marketing | `#F0B04A` | `#8F5A00` |
| legal | `#A493F5` | `#5B43C7` |
| sales | `#4FC79A` | `#137352` |
| finance | `#56C2D8` | `#0D6B80` |
| c_level | `#D9DDE3` | `#3D4654` |

### Type

- One family in two widths: **IBM Plex Sans** for body and UI, **IBM Plex Sans Condensed** for headings and the team names. Plex was drawn for an enterprise context, and the condensed width gives headings a compact, documentary voice without a second typeface.
- Scale (1.25 ratio): 13 / 15 (body) / 19 / 24 / 30 / 38. Body line height 1.55; headings 1.15.
- Sentence case everywhere. No all-caps labels, no eyebrow labels above headings, no monospace data labels.
- Line length: answer and About prose capped at 68 characters.

### Layout

Left-aligned throughout. Desktop Playground:

```
+--------------------------------------------------------------------------+
| Enterprise RAG          Playground   About                    [theme]    |
+-------------------+------------------------------------------------------+
| You are signed in | Ask a question                                       |
| as                | [ text box ...................................  Ask ] |
|                   | Suggested: your team | another team's data | attacks |
| ● Engineering 80  |------------------------------------------------------|
| ● People (HR) 75  | Answer                                               |
| ● Marketing  70   |  Text with [1] [2] citation chips                    |
| ● Legal      65   |  Sources: 1 Title > Section   ●eng ●c_level          |
| ● Sales      70   |------------------------------------------------------|
| ● Finance    65   | How it answered (open by default after first answer) |
| ● Executive 275   |  checks: question check, search, passage check, ... |
|                   |  passages searched, with scores and team badges      |
+-------------------+------------------------------------------------------+
```

Phone (≤ 720 px): the team list becomes a horizontal row of chips under the tabs; the question, answer and "How it answered" stack.

About: a single readable column (68 ch) with a sticky section index on wide screens; the diagram and results tables may run wider than the text column.

### Principles

1. Show the evidence. Every answer sits next to the passages it came from and the teams that may read them.
2. Refusals are information, not failure: say plainly why ("Finance documents aren't shared with Marketing") and suggest what to try.
3. Motion only answers actions: the answer panel fades in when it arrives, and the team switch animates the colour change. Nothing moves on its own; `prefers-reduced-motion` turns transitions off.
4. Quiet surfaces: one radius (6 px) for inputs and buttons, panels separated by rules rather than shadows and cards.

## Review against the brief

- First draft used a gradient hero with three stat tiles on the About page. That is the generic SaaS opener; replaced with a plain statement of the problem and a "try it" link, letting the Playground be the hero.
- First draft numbered the About sections 01-06. Only "How it works" is a real sequence, so only its diagram steps are numbered.
- First draft used a monospace face for scores. Replaced with Plex Sans tabular figures.
