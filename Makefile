.PHONY: app-status app-stop beta-dev beta-status beta-stop check-ui-screenshot cleanup-check dev dev-live diagnose dogfood-smoke harness-check harness-lint harness-status install-beta-app observe observe-live observe-session package-beta package-extension update-ui-screenshot validate-beta validate-ui verify verify-harness new-plan

dev:
	@scripts/harness/dev.sh

dev-live:
	@scripts/harness/dev-live.sh

diagnose:
	@scripts/harness/diagnose.sh

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
