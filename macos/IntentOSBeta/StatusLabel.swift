import Cocoa

extension IntentOSBetaApp {
    func refreshStatus() {
        guard isBetaRecordedRunning(), let base = envValue("INTENTOS_BETA_SERVICE_URL"), let url = URL(string: base + dailyLoopEndpoint) else {
            updateMenuStatus("Stopped")
            return
        }
        var request = URLRequest(url: url)
        authorize(&request)
        URLSession.shared.dataTask(with: request) { data, _, error in
            let label = error == nil ? (self.statusLabel(from: data) ?? "Capture Issue") : "Capture Issue"
            DispatchQueue.main.async {
                self.updateMenuStatus(label)
            }
        }.resume()
    }

    func updateMenuStatus(_ label: String) {
        statusItem.button?.title = "IntentOS"
        statusItem.button?.toolTip = "IntentOS \(label)"
        statusMenuItem?.title = "Capture: \(label)"
    }

    func statusLabel(from data: Data?) -> String? {
        guard let data,
              let object = try? JSONSerialization.jsonObject(with: data),
              let json = object as? [String: Any]
        else {
            return nil
        }
        let status = json["status"] as? [String: Any] ?? json
        if let pause = status["pause"] as? [String: Any], pause["paused"] as? Bool == true {
            return "Paused"
        }
        if let readiness = status["readiness"] as? [String: Any],
           readiness["state"] as? String == "setup_needed" {
            return "Setup Needed"
        }
        if let capture = status["capture"] as? [String: Any],
           let captureState = capture["state"] as? String,
           ["error", "stopped"].contains(captureState) {
            return "Capture Issue"
        }
        if let recorder = status["native_recorder"] as? [String: Any],
           let recorderState = recorder["state"] as? String,
           recorderState != "running" {
            return ["not_started", "disabled"].contains(recorderState) ? "Setup Needed" : "Capture Issue"
        }
        if let rescue = json["focus_rescue"] as? [String: Any],
           let rescueState = rescue["state"] as? String {
            if rescueState == "recovery_available" {
                return "Recovery Available"
            }
            if rescueState == "avoid_leaking" {
                return "Avoid Leaking"
            }
            if rescueState == "focus_protected" {
                return "Focus Protected"
            }
            if rescueState == "evidence_insufficient" {
                return "Need Evidence"
            }
        }
        if let prompt = json["prompt"] as? [String: Any],
           let promptState = prompt["state"] as? String {
            if promptState == "intent_due" {
                return "Intent Due"
            }
            if promptState == "review_due" {
                return "Review Ready"
            }
        }
        if let lowConfidence = json["low_confidence_count"] as? Int, lowConfidence > 0 {
            return "Needs Correction"
        }
        if let block = json["next_block"] as? [String: Any],
           let title = block["title"] as? String {
            let lower = title.lowercased()
            if lower.contains("close") || lower.contains("leak") || lower.contains("cap") {
                return "Avoid Leaking"
            }
        }
        if let plan = json["plan_vs_actual"] as? [String: Any],
           let focusSeconds = plan["focus_seconds"] as? Int,
           let reactiveSeconds = plan["reactive_seconds"] as? Int,
           focusSeconds > 0,
           reactiveSeconds == 0 {
            return "Focus Holding"
        }
        return "Running"
    }
}
