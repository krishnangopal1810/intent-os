# Mac Local Capture and Inference References

Use these references when planning macOS live capture or local model work.
Prefer official Apple documentation for implementation details.

## Capture

- `NSWorkspace.frontmostApplication`: current frontmost app that receives key
  events.
  <https://developer.apple.com/documentation/appkit/nsworkspace/frontmostapplication>
- `NSRunningApplication`: running app metadata such as bundle identifier and
  process information.
  <https://developer.apple.com/documentation/appkit/nsrunningapplication>
- Accessibility `AXUIElement`: accessible UI element inspection for assistive
  applications.
  <https://developer.apple.com/documentation/applicationservices/axuielement>
- ScreenCaptureKit: capture displays, apps, windows, frames, and audio samples
  with user-granted Screen Recording permission.
  <https://developer.apple.com/documentation/screencapturekit/>
- Vision text recognition: on-device OCR for images and video frames.
  <https://developer.apple.com/documentation/vision/recognizing-text-in-images>

## On-Device Inference

- Foundation Models framework: on-device language model for generation,
  understanding, classification, structured output, and tool calling.
  <https://developer.apple.com/documentation/foundationmodels/generating-content-and-performing-tasks-with-foundation-models>
- Foundation Models prompting guidance: use simpler prompts, structured output,
  and small context.
  <https://developer.apple.com/documentation/foundationmodels/prompting-an-on-device-foundation-model>
- Core ML: local model integration optimized for Apple silicon.
  <https://developer.apple.com/machine-learning/core-ml/>
- MLX: Apple silicon machine learning framework for local experimentation.
  <https://opensource.apple.com/projects/mlx>

## Product Interpretation

For IntentOS, the references imply this order:

1. Capture structured metadata first.
2. Normalize everything into `ActivityEvent`.
3. Use screenshots and OCR only when metadata is insufficient.
4. Use local models as second-pass classifiers, not as the primary sensor.
5. Keep personal activity data local by default.
