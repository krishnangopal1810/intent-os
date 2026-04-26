.PHONY: app-status app-stop cleanup-check dev harness-check harness-lint harness-status observe observe-live validate-ui verify verify-harness new-plan

dev:
	@scripts/harness/dev.sh

app-status:
	@scripts/harness/app-status.sh

app-stop:
	@scripts/harness/app-stop.sh

cleanup-check:
	@scripts/harness/cleanup-check.sh

validate-ui:
	@scripts/harness/validate-ui.sh

observe:
	@scripts/harness/observe.sh

observe-live:
	@scripts/harness/observe-live.sh

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
