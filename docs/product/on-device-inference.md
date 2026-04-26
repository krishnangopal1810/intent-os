# On-Device Inference

This spec defines how IntentOS should use local intelligence for behavior
classification. It is not a commitment to add a model before metadata capture
is working.

## Principle

Use rules first. Add local models only when deterministic evidence and fixture
evaluation show that rules are insufficient.

The product should preserve inspectability: every classification needs a label,
confidence, reason, and evidence source.

## Inference Ladder

1. Deterministic rules over app, URL, title, domain, and source metadata.
2. Rules plus bounded visible-text excerpts.
3. Apple Foundation Models for local text classification when available.
4. Core ML model for small custom classifiers when a fixed label set and
   evaluation set justify it.
5. MLX for local LLM experimentation or prototyping on Apple silicon.

Cloud inference is out of scope for current local slices.

## Model Roles

Foundation Models are a good fit for:

- classifying short evidence snippets
- extracting tags from window titles or page titles
- summarizing a short activity segment
- judging whether a ChatGPT conversation appears serious, educational, casual,
  coding-related, admin-related, or entertainment-focused

Core ML is a good fit for:

- small, repeatable classifiers
- lower-latency inference over fixed features
- packaged models with predictable runtime behavior

MLX is a good fit for:

- Apple silicon experimentation
- evaluating open local LLMs
- fine-tuning or prototyping before deciding whether to package a model

## Prompt and Context Limits

Model input should be small and structured:

```json
{
  "app_name": "ChatGPT",
  "domain": null,
  "window_title": "Explain transformers attention mechanism",
  "visible_text_excerpt": "Can you explain attention with examples?",
  "candidate_labels": ["deep_work", "learning", "admin", "entertainment", "unknown"]
}
```

Do not pass full documents, full conversations, raw screenshots, or full browser
history into a model by default.

## Output Contract

All model outputs must normalize into the existing classifier output shape:

- primary behavior label
- confidence
- short reason
- evidence list
- model/runtime identifier when a model was used
- fallback reason when the model is unavailable

The classifier must remain able to return `unknown`.

## Evaluation

Every model-backed behavior change must add or update:

- labeled fixtures
- thresholded evaluation command
- failure examples for ambiguous events
- local fallback behavior when the model is unavailable

`make verify` must not depend on downloading a model or contacting a network
service. If a future optional model is large, CI should use a deterministic fake
or a tiny checked-in fixture model while local manual testing covers the real
runtime.

## Privacy Rules

- Inference is local-only by default.
- No cloud model calls for personal activity data in current slices.
- Do not persist model prompts containing sensitive visible text unless the user
  explicitly enables debug capture.
- Prefer redacted, bounded evidence snippets.
- Preserve user controls for app/domain exclusions.
