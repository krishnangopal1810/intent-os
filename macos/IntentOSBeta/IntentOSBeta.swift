import Cocoa
import Foundation

@main
final class AppDelegate: NSObject, NSApplicationDelegate {
    private static var retainedDelegate: AppDelegate?
    private let statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
    private lazy var repoRoot = findRepoRoot()
    private var statusMenuItem: NSMenuItem?
    private var didOpenDashboardAfterLaunch = false
    private var isStartingBeta = false
    private let dailyLoopEndpoint = "/api/daily-loop"
    private let dailyIntentEndpoint = "/api/daily-intent"
    private let reviewCheckinEndpoint = "/api/review-checkin"
    private let weeklyPatternsEndpoint = "/api/weekly-patterns"

    static func main() {
        let app = NSApplication.shared
        let delegate = AppDelegate()
        retainedDelegate = delegate
        app.delegate = delegate
        app.setActivationPolicy(.accessory)
        app.run()
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        rebuildMenu()
        refreshStatus()
        openDashboardAfterLaunch()
        Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { _ in self.refreshStatus() }
    }

    private func rebuildMenu() {
        let menu = NSMenu()
        statusItem.button?.title = "IntentOS"
        statusItem.button?.toolTip = "IntentOS beta"
        let status = NSMenuItem(title: "Capture: unknown", action: nil, keyEquivalent: "")
        status.isEnabled = false
        statusMenuItem = status
        menu.addItem(status)
        menu.addItem(NSMenuItem.separator())
        menu.addItem(item("Open Dashboard", #selector(openDashboard)))
        menu.addItem(item("Set Today's Intent", #selector(setTodaysIntent)))
        menu.addItem(item("Open Evening Review", #selector(openEveningReview)))
        menu.addItem(item("Open Next Block", #selector(openNextBlock)))
        menu.addItem(item("Open Weekly Patterns", #selector(openWeeklyPatterns)))
        menu.addItem(item("Start Beta", #selector(startBeta)))
        menu.addItem(item("Restart Beta", #selector(restartBeta)))
        menu.addItem(item("Stop Beta", #selector(stopBeta)))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(item("Run Preflight", #selector(runPreflight)))
        menu.addItem(item("Run Permission Check", #selector(runPermissionCheck)))
        menu.addItem(item("Restart Onboarding", #selector(restartOnboarding)))
        menu.addItem(item("Copy Setup Report", #selector(copySetupReport)))
        menu.addItem(item("Open Accessibility Settings", #selector(openAccessibilitySettings)))
        menu.addItem(item("Open Automation Settings", #selector(openAutomationSettings)))
        menu.addItem(item("Open Chrome Extension Setup", #selector(openChromeSetup)))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(item("Pause 15 min", #selector(pause15)))
        menu.addItem(item("Pause 1 hour", #selector(pauseHour)))
        menu.addItem(item("Pause until tomorrow", #selector(pauseTomorrow)))
        menu.addItem(item("Resume", #selector(resume)))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(item("Delete Local Data", #selector(deleteLocalData)))
        menu.addItem(item("Open Diagnostics", #selector(openDiagnostics)))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(item("Quit", #selector(quit)))
        statusItem.menu = menu
    }

    private func item(_ title: String, _ action: Selector) -> NSMenuItem {
        let menuItem = NSMenuItem(title: title, action: action, keyEquivalent: "")
        menuItem.target = self
        return menuItem
    }

    @objc private func startBeta() {
        startBetaIfNeeded(openWhenReady: false)
    }

    @objc private func restartBeta() {
        startBetaIfNeeded(openWhenReady: true, forceRestart: true)
    }

    @objc private func stopBeta() {
        runMake("beta-stop") { _ in
            self.refreshStatus()
        }
    }

    @objc private func runPermissionCheck() {
        updateMenuStatus("Checking")
        post("/api/permissions/check", body: "{}") { payload in
            self.refreshStatus()
            self.showPermissionCheckResult(payload)
        }
    }

    @objc private func runPreflight() {
        get("/api/status") { payload in
            guard let preflight = payload?["preflight"] as? [String: Any] else {
                self.showActionFailed("Preflight Failed")
                return
            }
            self.showPreflightResult(preflight)
        }
    }

    @objc private func restartOnboarding() {
        post("/api/onboarding", body: #"{"action":"reset"}"#) { _ in
            self.refreshStatus()
            _ = self.openRecordedDashboard()
        }
    }

    @objc private func copySetupReport() {
        get("/api/setup-report") { payload in
            guard let payload,
                  let data = try? JSONSerialization.data(withJSONObject: payload, options: [.prettyPrinted]),
                  let text = String(data: data, encoding: .utf8)
            else {
                self.showActionFailed("Copy Setup Report Failed")
                return
            }
            NSPasteboard.general.clearContents()
            NSPasteboard.general.setString(text, forType: .string)
            self.showAlert(
                "Setup Report Copied",
                "A redacted setup report was copied. It excludes raw titles, URLs, screenshots, cookies, and page bodies."
            )
        }
    }

    @objc private func openAccessibilitySettings() {
        openSettings("accessibility")
    }

    @objc private func openAutomationSettings() {
        openSettings("automation")
    }

    @objc private func openChromeSetup() {
        openSettings("chrome_extensions")
    }

    private func openSettings(_ target: String) {
        post("/api/open-system-settings", body: #"{"target":"\#(target)"}"#) { payload in
            self.refreshStatus()
            guard let payload else {
                self.showActionFailed("Open Settings Failed")
                return
            }
            self.showSetupGuidance(payload)
        }
    }

    @objc private func openDashboard() {
        if !openRecordedDashboard() {
            startBetaIfNeeded(openWhenReady: true)
        }
    }

    @objc private func setTodaysIntent() {
        openDashboardAnchor("daily-loop-title", endpoint: dailyIntentEndpoint)
    }

    @objc private func openEveningReview() {
        openDashboardAnchor("daily-loop-title", endpoint: reviewCheckinEndpoint)
    }

    @objc private func openNextBlock() {
        openDashboardAnchor("decision-title", endpoint: dailyLoopEndpoint)
    }

    @objc private func openWeeklyPatterns() {
        openDashboardAnchor("weekly-patterns-title", endpoint: weeklyPatternsEndpoint)
    }

    private func openDashboardAnchor(_ anchor: String, endpoint: String) {
        _ = endpoint
        if !openRecordedDashboard(anchor: anchor) {
            startBetaIfNeeded(openWhenReady: false) { success in
                if success {
                    _ = self.openRecordedDashboard(anchor: anchor)
                }
            }
        }
    }

    private func openDashboardAfterLaunch() {
        guard !didOpenDashboardAfterLaunch else { return }
        didOpenDashboardAfterLaunch = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            self.openDashboard()
        }
    }

    private func startBetaIfNeeded(
        openWhenReady: Bool,
        forceRestart: Bool = false,
        completion: ((Bool) -> Void)? = nil
    ) {
        guard !isStartingBeta else {
            completion?(false)
            return
        }
        if !forceRestart && isBetaRecordedRunning() && (!openWhenReady || openRecordedDashboard()) {
            refreshStatus()
            completion?(true)
            return
        }
        isStartingBeta = true
        runMake("beta-dev") { success in
            self.isStartingBeta = false
            self.refreshStatus()
            guard success else {
                self.updateMenuStatus("Capture Issue")
                completion?(false)
                return
            }
            if openWhenReady {
                _ = self.openRecordedDashboard()
            }
            completion?(true)
        }
    }

    @objc private func pause15() {
        pause(minutes: 15)
    }

    @objc private func pauseHour() {
        pause(minutes: 60)
    }

    @objc private func pauseTomorrow() {
        pause(minutes: minutesUntilTomorrow())
    }

    private func pause(minutes: Int) {
        post("/api/pause", body: #"{"minutes":\#(minutes)}"#) { _ in
            self.refreshStatus()
        }
    }

    @objc private func resume() {
        post("/api/resume", body: "{}") { _ in
            self.refreshStatus()
        }
    }

    @objc private func deleteLocalData() {
        guard confirmDeleteLocalData() else { return }
        post("/api/delete-local-data", body: "{}") { payload in
            self.refreshStatus()
            guard payload?["status"] as? String == "deleted" else {
                self.showActionFailed("Delete Local Data Failed")
                return
            }
            self.showAlert(
                "Local Data Deleted",
                "IntentOS local activity data, corrections, and generated beta reports were cleared."
            )
        }
    }

    @objc private func openDiagnostics() {
        let diagnostics = runtimeRoot()
        try? FileManager.default.createDirectory(at: diagnostics, withIntermediateDirectories: true)
        NSWorkspace.shared.open(diagnostics)
    }

    @objc private func quit() {
        runMake("beta-stop") { _ in
            NSApp.terminate(nil)
        }
    }

    private func runMake(_ target: String, completion: ((Bool) -> Void)? = nil) {
        DispatchQueue.global(qos: .utility).async {
            let process = Process()
            process.executableURL = URL(fileURLWithPath: "/bin/bash")
            process.currentDirectoryURL = self.repoRoot
            process.arguments = [self.scriptPath(for: target)]
            process.environment = self.runtimeEnvironment()
            let success: Bool
            do {
                try process.run()
                process.waitUntilExit()
                success = process.terminationStatus == 0
            } catch {
                success = false
            }
            if let completion {
                DispatchQueue.main.async {
                    completion(success)
                }
            }
        }
    }

    private func scriptPath(for target: String) -> String {
        switch target {
        case "beta-dev":
            return "scripts/harness/beta-dev.sh"
        case "beta-stop":
            return "scripts/harness/beta-stop.sh"
        default:
            return "scripts/harness/\(target).sh"
        }
    }

    private func runtimeEnvironment() -> [String: String] {
        var env = ProcessInfo.processInfo.environment
        env["INTENTOS_RUNTIME_DIR"] = runtimeRoot().path
        env["INTENTOS_APP_BUNDLE_PATH"] = Bundle.main.bundleURL.path
        env["INTENTOS_BUNDLED_RUNTIME_PRESENT"] = isBundledRuntime() ? "1" : "0"
        if let runtime = Bundle.main.resourceURL?.appendingPathComponent("intent-os-runtime") {
            env["INTENTOS_BUNDLED_RUNTIME_PATH"] = runtime.path
        }
        return env
    }

    private func post(
        _ path: String,
        body: String,
        completion: (([String: Any]?) -> Void)? = nil,
        retryAfterStart: Bool = true
    ) {
        guard isBetaRecordedRunning(),
              let base = envValue("INTENTOS_BETA_SERVICE_URL"),
              let url = URL(string: base + path)
        else {
            retryPostAfterStart(
                path,
                body: body,
                completion: completion,
                retryAfterStart: retryAfterStart,
                forceRestart: isBetaRecordedRunning()
            )
            return
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = body.data(using: .utf8)
        URLSession.shared.dataTask(with: request) { data, _, error in
            if error != nil && retryAfterStart {
                DispatchQueue.main.async {
                    self.retryPostAfterStart(
                        path,
                        body: body,
                        completion: completion,
                        retryAfterStart: retryAfterStart,
                        forceRestart: true
                    )
                }
                return
            }
            var payload: [String: Any]?
            if let data,
               let object = try? JSONSerialization.jsonObject(with: data),
               let json = object as? [String: Any] {
                payload = json
            }
            if let completion {
                DispatchQueue.main.async {
                    completion(payload)
                }
            }
        }.resume()
    }

    private func get(
        _ path: String,
        completion: (([String: Any]?) -> Void)? = nil,
        retryAfterStart: Bool = true
    ) {
        guard isBetaRecordedRunning(),
              let base = envValue("INTENTOS_BETA_SERVICE_URL"),
              let url = URL(string: base + path)
        else {
            retryGetAfterStart(path, completion: completion, retryAfterStart: retryAfterStart)
            return
        }
        URLSession.shared.dataTask(with: url) { data, _, error in
            if error != nil && retryAfterStart {
                DispatchQueue.main.async {
                    self.retryGetAfterStart(path, completion: completion, retryAfterStart: retryAfterStart)
                }
                return
            }
            var payload: [String: Any]?
            if let data,
               let object = try? JSONSerialization.jsonObject(with: data),
               let json = object as? [String: Any] {
                payload = json
            }
            if let completion {
                DispatchQueue.main.async {
                    completion(payload)
                }
            }
        }.resume()
    }

    private func retryGetAfterStart(
        _ path: String,
        completion: (([String: Any]?) -> Void)?,
        retryAfterStart: Bool
    ) {
        guard retryAfterStart else {
            completion?(nil)
            return
        }
        startBetaIfNeeded(openWhenReady: false, forceRestart: isBetaRecordedRunning()) { success in
            guard success else {
                completion?(nil)
                return
            }
            self.get(path, completion: completion, retryAfterStart: false)
        }
    }

    private func retryPostAfterStart(
        _ path: String,
        body: String,
        completion: (([String: Any]?) -> Void)?,
        retryAfterStart: Bool,
        forceRestart: Bool
    ) {
        guard retryAfterStart else {
            completion?(nil)
            return
        }
        startBetaIfNeeded(openWhenReady: false, forceRestart: forceRestart) { success in
            guard success else {
                completion?(nil)
                return
            }
            self.post(path, body: body, completion: completion, retryAfterStart: false)
        }
    }

    private func showSetupGuidance(_ payload: [String: Any]?) {
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

    private func showPermissionCheckResult(_ payload: [String: Any]?) {
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

    private func showPreflightResult(_ preflight: [String: Any]) {
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

    private func chromeBridgeInstallInstructions() -> String {
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

    private func permissionStateLabel(_ state: String?) -> String {
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

    private func showAlert(_ title: String, _ message: String) {
        let alert = NSAlert()
        alert.messageText = title
        alert.informativeText = message
        alert.alertStyle = .informational
        alert.addButton(withTitle: "OK")
        NSApp.activate(ignoringOtherApps: true)
        alert.runModal()
    }

    private func showActionFailed(_ title: String) {
        showAlert(
            title,
            "IntentOS could not complete this action. Run Start Beta or make beta-status, then try again."
        )
    }

    private func confirmDeleteLocalData() -> Bool {
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

    private func refreshStatus() {
        guard isBetaRecordedRunning(), let base = envValue("INTENTOS_BETA_SERVICE_URL"), let url = URL(string: base + dailyLoopEndpoint) else {
            updateMenuStatus("Stopped")
            return
        }
        URLSession.shared.dataTask(with: url) { data, _, error in
            let label = error == nil ? (self.statusLabel(from: data) ?? "Capture Issue") : "Capture Issue"
            DispatchQueue.main.async {
                self.updateMenuStatus(label)
            }
        }.resume()
    }

    private func updateMenuStatus(_ label: String) {
        statusItem.button?.title = "IntentOS"
        statusItem.button?.toolTip = "IntentOS \(label)"
        statusMenuItem?.title = "Capture: \(label)"
    }

    private func statusLabel(from data: Data?) -> String? {
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

    private func envValue(_ key: String) -> String? {
        let path = runtimeRoot().appendingPathComponent("beta/app.env")
        guard let text = try? String(contentsOf: path, encoding: .utf8) else { return nil }
        for line in text.split(separator: "\n").reversed() {
            let prefix = key + "="
            if line.hasPrefix(prefix) {
                return String(line.dropFirst(prefix.count))
            }
        }
        return nil
    }

    private func isBetaRecordedRunning() -> Bool {
        envValue("INTENTOS_BETA_STATUS") == "running"
    }

    private func openRecordedDashboard(anchor: String? = nil) -> Bool {
        guard isBetaRecordedRunning(),
              var url = envValue("INTENTOS_BETA_UI_URL")
        else {
            return false
        }
        if let anchor, !anchor.isEmpty {
            url += "#\(anchor)"
        }
        guard let dashboard = URL(string: url) else {
            return false
        }
        NSWorkspace.shared.open(dashboard)
        return true
    }

    private func minutesUntilTomorrow(now: Date = Date()) -> Int {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: now)
        guard let tomorrow = calendar.date(byAdding: .day, value: 1, to: today) else {
            return 1440
        }
        let seconds = tomorrow.timeIntervalSince(now)
        return max(1, Int((seconds / 60.0).rounded(.up)))
    }

    private func runtimeRoot() -> URL {
        if let explicit = ProcessInfo.processInfo.environment["INTENTOS_RUNTIME_DIR"], !explicit.isEmpty {
            if explicit.hasPrefix("/") {
                return URL(fileURLWithPath: explicit)
            }
            return repoRoot.appendingPathComponent(explicit)
        }
        if isBundledRuntime() {
            return applicationSupportRoot().appendingPathComponent("runtime")
        }
        return repoRoot.appendingPathComponent(".harness/runtime")
    }

    private func findRepoRoot() -> URL {
        if let bundled = Bundle.main.resourceURL?.appendingPathComponent("intent-os-runtime"),
           FileManager.default.fileExists(atPath: bundled.appendingPathComponent("Makefile").path) {
            return bundled
        }
        if let explicit = ProcessInfo.processInfo.environment["INTENTOS_REPO_ROOT"] {
            let explicitURL = URL(fileURLWithPath: explicit)
            if FileManager.default.fileExists(atPath: explicitURL.appendingPathComponent("Makefile").path) {
                return explicitURL
            }
        }
        if let resource = Bundle.main.url(forResource: "repo-root", withExtension: "txt"),
           let text = try? String(contentsOf: resource, encoding: .utf8) {
            let path = text.trimmingCharacters(in: .whitespacesAndNewlines)
            let resourceURL = URL(fileURLWithPath: path)
            if FileManager.default.fileExists(atPath: resourceURL.appendingPathComponent("Makefile").path) {
                return resourceURL
            }
        }
        var url = Bundle.main.bundleURL
        for _ in 0..<4 {
            url.deleteLastPathComponent()
        }
        return url
    }

    private func isBundledRuntime() -> Bool {
        guard let runtime = Bundle.main.resourceURL?.appendingPathComponent("intent-os-runtime") else {
            return false
        }
        return FileManager.default.fileExists(atPath: runtime.appendingPathComponent("Makefile").path)
    }

    private func applicationSupportRoot() -> URL {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? URL(fileURLWithPath: NSHomeDirectory()).appendingPathComponent("Library/Application Support")
        let root = base.appendingPathComponent("IntentOS", isDirectory: true)
        try? FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        return root
    }
}
