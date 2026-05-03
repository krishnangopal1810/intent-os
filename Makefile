.PHONY: adapter-fixture-check app-status app-stop beta-dev beta-status beta-stop check-ui-screenshot chrome-bridge-smoke cleanup-check dev dev-live diagnose diagnose-json dogfood-smoke feedback-fixture-candidates harness-check harness-lint harness-status install-beta-app new-feature observe observe-live observe-session package-beta package-extension review-status update-ui-screenshot validate-beta validate-ui verify verify-harness new-plan

dev:
	@scripts/harness/dev.sh

dev-live:
	@scripts/harness/dev-live.sh

diagnose:
	@scripts/harness/diagnose.sh

diagnose-json:
	@scripts/harness/diagnose-json.py

app-status:
	@scripts/harness/app-status.sh

app-stop:
	@scripts/harness/app-stop.sh

beta-dev:
	@scripts/harness/beta-dev.sh

beta-status:
	@scripts/harness/beta-status.sh

beta-stop:
	@scripts/harness/beta-stop.sh

cleanup-check:
	@scripts/harness/cleanup-check.sh

validate-ui:
	@scripts/harness/validate-ui.sh

validate-beta:
	@scripts/product/validate-beta.sh

package-beta:
	@scripts/product/package-beta.sh

install-beta-app:
	@scripts/product/install-beta-app.sh

package-extension:
	@scripts/product/package-extension.sh

dogfood-smoke:
	@scripts/product/dogfood-smoke.sh

chrome-bridge-smoke:
	@scripts/product/chrome-bridge-smoke.sh

adapter-fixture-check:
	@scripts/harness/adapter-fixture-check.py

feedback-fixture-candidates:
	@scripts/harness/feedback-fixture-candidates.py

review-status:
	@scripts/harness/review-status.py

update-ui-screenshot:
	@scripts/product/update-ui-screenshot.sh

check-ui-screenshot:
	@scripts/product/check-ui-screenshot.sh

observe:
	@scripts/harness/observe.sh

observe-live:
	@scripts/harness/observe-live.sh

observe-session:
	@scripts/harness/observe-session.sh

harness-check:
	@scripts/harness/check.sh

harness-lint:
	@scripts/harness/lint.py

harness-status:
	@scripts/harness/status.sh

verify:
	@scripts/harness/verify.sh

verify-harness:
	@scripts/harness/check.sh

new-plan:
	@if [ -z "$(name)" ]; then echo "usage: make new-plan name=short-slug"; exit 2; fi
	@scripts/harness/new-plan.sh "$(name)"

new-feature:
	@if [ -z "$(name)" ] || [ -z "$(class)" ]; then echo "usage: make new-feature name=short-slug class=data-source|classifier|report|ui-workflow|permissioned-live|long-running-process|integration-export|agent-workflow"; exit 2; fi
	@scripts/harness/new-feature.sh "$(name)" "$(class)"
