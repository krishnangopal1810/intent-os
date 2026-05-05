# IntentOS Behavior Taxonomy

This taxonomy is the source of truth for behavior classification. Add new labels
only when evaluation examples show that existing labels are insufficient.

## Primary Labels

- `deep_work`: focused creation, coding, writing, analysis, or problem solving.
- `shallow_work`: low-depth work such as inbox triage, lightweight editing, or
  routine tool use.
- `learning`: intentional educational, reference, or skill-building activity.
- `communication`: messages, calls, coordination, or relationship maintenance.
- `admin`: necessary operational work such as taxes, billing, banking, forms,
  travel, product research, personal logistics, or account management.
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
- Treat developer reference sites as `learning` unless the surrounding metadata
  shows active implementation or review.
- Treat local development dashboards and repository pages as `deep_work` when
  the app or title clearly points at the current project.
- Treat shopping, restaurant, visa, and similar planning surfaces as `admin`
  when the metadata shows an explicit lookup rather than feed browsing.
- Treat sports clips and match highlights as `entertainment`.
- Treat social feeds, stories, and individual low-context status pages as
  `passive_consumption` unless stronger research or communication evidence is
  present.

## Example Surfaces

| Surface | Example | Label |
| --- | --- | --- |
| ChatGPT | Debugging a failing Python test | `deep_work` |
| ChatGPT | Asking for a quick joke thread | `entertainment` |
| VS Code | Implementing an IntentOS classifier | `deep_work` |
| Localhost | Reviewing the IntentOS beta dashboard during development | `deep_work` |
| Bazel docs | Reading the BUILD style guide | `learning` |
| WhatsApp | Coordinating a family errand | `communication` |
| Income tax website | Filing a return | `admin` |
| Amazon | Comparing a rice cooker purchase | `admin` |
| Google Search | Looking up a brunch venue | `admin` |
| LinkedIn | Researching a founder profile | `learning` |
| LinkedIn | Scrolling the feed without a search goal | `passive_consumption` |
| YouTube | System design lecture | `learning` |
| YouTube | Cricket match highlights | `entertainment` |
| YouTube | Comedy compilation | `entertainment` |

## Feedback Regression Checklist

When beta corrections or manual product feedback show that an obvious activity
was classified as `unknown` or as the wrong label, run
`make feedback-fixture-candidates` and promote the corrected pattern into a
labeled activity fixture before related classifier work is complete. The
activity evaluation set must keep coverage for developer docs, local IntentOS
review, GitHub repositories, sports videos, product research, personal
logistics, shopping, and social feed/status pages.
