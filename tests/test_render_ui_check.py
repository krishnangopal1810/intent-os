import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "render_ui_check", ROOT / "scripts/product/render-ui-check.py"
)
render_ui_check = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(render_ui_check)


class RenderUiCheckTests(unittest.TestCase):
    def test_forbidden_visible_copy_fails(self):
        probe = base_probe()
        probe["copy_policy"]["forbidden_hits"] = ["No rows"]
        self.assertHasFailure(probe, "forbidden product language")

    def test_clipped_text_fails(self):
        probe = base_probe()
        probe["text_layout"]["clipped_text_count"] = 1
        self.assertHasFailure(probe, "clipped inside its container")

    def test_over_budget_first_viewport_fails(self):
        probe = base_probe()
        probe["default_density"]["visible_word_count"] = 361
        self.assertHasFailure(probe, "too much visible text")

    def test_missing_coach_hero_fails(self):
        probe = base_probe()
        probe["coach_hero_present"] = False
        probe["first_viewport"]["coach_hero_present"] = False
        self.assertHasFailure(probe, "plan-vs-actual hero")

    def test_missing_beta_focus_rescue_fails(self):
        probe = base_probe(["beta-ready"])
        probe["mode"] = "beta"
        probe["focus_rescue_present"] = False
        probe["focus_rescue_text"] = ""
        probe["first_viewport"]["focus_rescue_present"] = False
        self.assertHasFailure(probe, "focus rescue state")

    def test_document_scroll_section_jump_fails(self):
        probe = base_probe()
        probe["section_nav"]["document_scroll_delta"] = 12
        self.assertHasFailure(probe, "scrolled the document")

    def test_missing_intent_preview_fails_when_required(self):
        probe = base_probe(["beta-empty", "beta-intent-missing"])
        probe["event_count"] = 0
        probe["stat_count"] = 0
        probe["intent_preview"]["form_visible"] = False
        self.assertHasFailure(probe, "daily intent form", scenario="beta-intent-missing")

    def test_stale_service_raw_error_fails(self):
        probe = base_probe(["beta-service-stale"])
        probe["event_count"] = 0
        probe["stat_count"] = 0
        probe["copy_policy"]["raw_error_hits"] = ["\\bFailed to fetch\\b"]
        probe["service_state"]["notice_visible"] = True
        probe["service_state"]["reconnect_visible"] = True
        self.assertHasFailure(probe, "raw developer error", scenario="beta-service-stale")

    def test_required_workflow_with_no_visible_clicks_fails(self):
        probe = base_probe()
        probe["workflow_expected"] = True
        probe["workflow_probe"]["clicked"] = []
        self.assertHasFailure(probe, "did not click any visible controls")

    def assertHasFailure(self, probe, expected, scenario=""):
        failures = render_ui_check.validate_probe(
            probe,
            min_stat_count=3,
            scenario=scenario,
            copy_policy={"version": 2},
        )
        self.assertIn(expected, "; ".join(failures))


def base_probe(scenarios=None):
    scenarios = scenarios or ["fixture-default"]
    text_layout = {
        "visible_leaf_text_count": 16,
        "visible_word_count": 220,
        "clipped_text_count": 0,
        "cut_off_text_count": 0,
    }
    return {
        "schema_version": 1,
        "mode": "fixture",
        "scenarios": scenarios,
        "root_present": True,
        "body_text_length": 500,
        "panel_count": 2,
        "stat_count": 3,
        "decision_count": 2,
        "event_count": 1,
        "next_move_text": "Review the next action.",
        "coach_hero_present": True,
        "focus_rescue_present": False,
        "focus_rescue_action_count": 0,
        "focus_rescue_text": "",
        "weekly_details_present": True,
        "daily_loop_present": True,
        "daily_loop_text": "Set one focus and one thing to avoid for today's review.",
        "command_center_present": True,
        "command_step_count": 3,
        "command_center_text": "Now Trust Tonight",
        "copy_policy": {
            "policy_version": 2,
            "forbidden_hits": [],
            "raw_error_hits": [],
        },
        "first_viewport": {
            "command_center_present": True,
            "coach_hero_present": True,
            "focus_rescue_present": False,
            "focus_rescue_action_count": 0,
            "focus_rescue_text": "",
            "coach_receipt_count": 1,
            "weekly_details_present": True,
            "next_move_present": True,
            "daily_loop_present": True,
            "visible_word_count": 220,
            "visible_report_panels": 0,
            "visible_stats": 0,
            "nav_visible": True,
        },
        "default_density": {
            "visible_decision_cards": 2,
            "visible_stats": 0,
            "visible_insights": 0,
            "visible_queue_panels": 0,
            "visible_report_panels": 0,
            "supporting_detail_count": 3,
            "collapsed_supporting_detail_count": 3,
            "open_supporting_detail_count": 0,
            "visible_leaf_text_count": 16,
            "visible_word_count": 220,
        },
        "text_layout": copy.deepcopy(text_layout),
        "current_text_layout": copy.deepcopy(text_layout),
        "section_nav": {
            "available": True,
            "activity_required_scroll": True,
            "nav_visible_after_activity": True,
            "workspace_scrolled_after_activity": True,
            "document_scroll_delta": 0,
            "active_href_after_activity": "#activity-title",
            "evidence_open_after_activity": True,
            "visible_report_panels_after_activity": 2,
            "cut_off_text_after_activity": 0,
            "clipped_text_after_activity": 0,
        },
        "intent_preview": {
            "form_visible": False,
            "typed": False,
            "focus_preview_mentions_input": True,
            "avoid_preview_mentions_input": True,
            "review_preview_mentions_note": True,
        },
        "service_state": {"notice_visible": False, "reconnect_visible": False},
        "workflow_probe": {"clicked": []},
        "workflow_expected": False,
        "youtube_visible": False,
        "horizontal_overflow": False,
        "out_of_view_count": 0,
        "clipped_text_count": 0,
        "cut_off_text_count": 0,
    }


if __name__ == "__main__":
    unittest.main()
