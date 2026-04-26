# IntentOS Behavior Taxonomy

This taxonomy is the source of truth for behavior classification. Add new labels
only when evaluation examples show that existing labels are insufficient.

## Primary Labels

- `deep_work`: focused creation, coding, writing, analysis, or problem solving.
- `shallow_work`: low-depth work such as inbox triage, lightweight editing, or
  routine tool use.
- `learning`: intentional educational or skill-building activity.
- `communication`: messages, calls, coordination, or relationship maintenance.
- `admin`: necessary operational work such as taxes, billing, banking, forms,
  travel, or account management.
- `passive_consumption`: feed scrolling, recommendation loops, clips, short
  videos, or low-intent browsing.
- `active_creation`: creating public or personal output outside core work, such
  as posts, notes, designs, or drafts.
- `entertainment`: deliberate leisure, games, shows, comedy, sports, or music.
- `unknown`: insufficient or conflicting metadata.

## Cross-Cutting Dimensions

These are not primary labels yet, but future classifiers should expose them:

- `intentionality`: `intentional`, `drift`, or `unknown`
- `energy`: `high_focus`, `low_focus`, `fragmented`, or `unknown`
- `work_relevance`: `core_work`, `support_work`, `personal`, or `unknown`

## Label Guidance

- Prefer `unknown` over forced certainty.
- Distinguish communication from passive consumption even when both occur in
  social apps.
- Treat coding tools as deep work only when window titles or metadata indicate
  active implementation, review, debugging, or design.
- Treat ChatGPT by conversation intent, not by app name. Coding, learning, admin
  drafting, and casual/fun conversations should classify differently.
- Treat admin work as valuable but not deep work.

## Example Surfaces

| Surface | Example | Label |
| --- | --- | --- |
| ChatGPT | Debugging a failing Python test | `deep_work` |
| ChatGPT | Asking for a quick joke thread | `entertainment` |
| VS Code | Implementing an IntentOS classifier | `deep_work` |
| WhatsApp | Coordinating a family errand | `communication` |
| Income tax website | Filing a return | `admin` |
| LinkedIn | Researching a founder profile | `learning` |
| LinkedIn | Scrolling the feed without a search goal | `passive_consumption` |
| YouTube | System design lecture | `learning` |
| YouTube | Comedy compilation | `entertainment` |
