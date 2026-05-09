import Cocoa

extension IntentOSBetaApp {
    func showSetupGuidance(_ payload: [String: Any]?) {
        guard let guidance = payload?["guidance"] as? [String: Any] else { return }
        let title = guidance["title"] as? String ?? payload?["label"] as? String ?? "IntentOS Setup"
        let summary = guidance["summary"] as? String
        let steps = (guidance["steps"] as? [Any])?.compactMap { $0 as? String } ?? []
        let verify = guidance["verify"] as? String
        var sections: [String] = []
        if let summary, !summary.isEmpty {
            sections.append(summary)
        }
        if !steps.isEmpty {
            sections.append(
                steps.enumerated()
                    .map { "\($0.offset + 1). \($0.element)" }
                    .joined(separator: "\n")
            )
        }
        if let verify, !verify.isEmpty {
            sections.append("Verify: \(verify)")
        }
        showAlert(title, sections.joined(separator: "\n\n"))
    }

    func showPermissionCheckResult(_ payload: [String: Any]?) {
        guard let payload else {
            showAlert(
                "Permission Check",
                "IntentOS could not read the permission check result. The beta may still be starting; run the check again after the dashboard opens."
            )
            return
        }
        let readiness = payload["readiness"] as? [String: Any]
        let readinessLabel = readiness?["label"] as? String ?? "Unknown"
        let permissions = payload["permissions"] as? [String: Any] ?? [:]
        let keys = [
            "accessibility",
            "browser_automation",
            "native_recorder",
            "chrome_extension",
            "capture",
            "database",
        ]
        let rows = keys.compactMap { key -> String? in
            guard let item = permissions[key] as? [String: Any] else { return nil }
            let label = item["label"] as? String ?? key
            let state = permissionStateLabel(item["state"] as? String)
            let detail = item["detail"] as? String ?? ""
            var parts = [detail.isEmpty ? "\(label): \(state)" : "\(label): \(state)\n\(detail)"]
            if key == "chrome_extension", item["state"] as? String != "ok" {
                parts.append(chromeBridgeInstallInstructions())
            }
            return parts.joined(separator: "\n\n")
        }
        let message = (["Readiness: \(readinessLabel)"] + rows).joined(separator: "\n\n")
        showAlert("Permission Check Complete", message)
    }

    func showPreflightResult(_ preflight: [String: Any]) {
        let state = preflight["state"] as? String ?? "unknown"
        let checks = preflight["checks"] as? [String: Any] ?? [:]
        let rows = checks.keys.sorted().compactMap { key -> String? in
            guard let item = checks[key] as? [String: Any] else { return nil }
            let label = key.replacingOccurrences(of: "_", with: " ").capitalized
            let status = permissionStateLabel(item["state"] as? String)
            let detail = item["detail"] as? String ?? ""
            return detail.isEmpty ? "\(label): \(status)" : "\(label): \(status)\n\(detail)"
        }
        showAlert("IntentOS Preflight: \(permissionStateLabel(state))", rows.joined(separator: "\n\n"))
    }

    func chromeBridgeInstallInstructions() -> String {
        let extensionPath = repoRoot.appendingPathComponent("extension/chrome").path
        return """
        Chrome bridge install:
        1. Click Open Chrome Extension Setup in the IntentOS menu.
        2. Turn on Developer mode in Chrome Extensions.
        3. Click Load unpacked.
        4. Select \(extensionPath).
        5. Keep IntentOS running, then run this permission check again.
        """
    }

    func permissionStateLabel(_ state: String?) -> String {
        switch state {
        case "ok":
            return "Ready"
        case "needs_action":
            return "Action needed"
        case "blocked":
            return "Blocked"
        case "not_applicable":
            return "Not applicable"
        case "unchecked":
            return "Unchecked"
        default:
            return state?.replacingOccurrences(of: "_", with: " ").capitalized ?? "Unknown"
        }
    }

    func showAlert(_ title: String, _ message: String) {
        let alert = NSAlert()
        alert.messageText = title
        alert.informativeText = message
        alert.alertStyle = .informational
        alert.addButton(withTitle: "OK")
        NSApp.activate(ignoringOtherApps: true)
        alert.runModal()
    }

    func showActionFailed(_ title: String) {
        showAlert(
            title,
            "IntentOS could not complete this action. Run Start Beta or make beta-status, then try again."
        )
    }

    func confirmDeleteLocalData() -> Bool {
        let alert = NSAlert()
        alert.messageText = "Delete Local Data?"
        alert.informativeText = "This clears local IntentOS activity data, corrections, " +
            "and generated beta reports from this Mac. This cannot be undone."
        alert.alertStyle = .warning
        alert.addButton(withTitle: "Delete")
        alert.addButton(withTitle: "Cancel")
        NSApp.activate(ignoringOtherApps: true)
        return alert.runModal() == .alertFirstButtonReturn
    }
}
