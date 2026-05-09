import Cocoa
import Foundation

@main
final class IntentOSBetaApp: NSObject, NSApplicationDelegate {
    private static var retainedDelegate: IntentOSBetaApp?
    let statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
    lazy var repoRoot = findRepoRoot()
    var statusMenuItem: NSMenuItem?
    var didOpenDashboardAfterLaunch = false
    var isStartingBeta = false
    let dailyLoopEndpoint = "/api/daily-loop"
    let dailyIntentEndpoint = "/api/daily-intent"
    let reviewCheckinEndpoint = "/api/review-checkin"
    let weeklyPatternsEndpoint = "/api/weekly-patterns"
    let apiTokenHeader = "X-IntentOS-Token"

    static func main() {
        let app = NSApplication.shared
        let delegate = IntentOSBetaApp()
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
}
