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
        menu.addItem(item("Start Beta", #selector(startBeta)))
        menu.addItem(item("Stop Beta", #selector(stopBeta)))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(item("Run Permission Check", #selector(runPermissionCheck)))
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

    @objc private func stopBeta() {
        runMake("beta-stop")
    }

    @objc private func runPermissionCheck() {
        post("/api/permissions/check", body: "{}")
    }

    @objc private func openAccessibilitySettings() {
        post("/api/open-system-settings", body: #"{"target":"accessibility"}"#)
    }

    @objc private func openAutomationSettings() {
        post("/api/open-system-settings", body: #"{"target":"automation"}"#)
    }

    @objc private func openChromeSetup() {
        post("/api/open-system-settings", body: #"{"target":"chrome_extensions"}"#)
    }

    @objc private func openDashboard() {
        if let url = envValue("INTENTOS_BETA_UI_URL"), let dashboard = URL(string: url) {
            NSWorkspace.shared.open(dashboard)
        } else {
            startBetaIfNeeded(openWhenReady: true)
        }
    }

    private func openDashboardAfterLaunch() {
        guard !didOpenDashboardAfterLaunch else { return }
        didOpenDashboardAfterLaunch = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            self.openDashboard()
        }
    }

    private func startBetaIfNeeded(openWhenReady: Bool) {
        guard !isStartingBeta else { return }
        isStartingBeta = true
        runMake("beta-dev") { success in
            self.isStartingBeta = false
            self.refreshStatus()
            guard success else {
                self.updateMenuStatus("Capture Issue")
                return
            }
            if openWhenReady {
                self.openDashboard()
            }
        }
    }

    @objc private func pause15() {
        post("/api/pause", body: #"{"minutes":15}"#)
    }

    @objc private func pauseHour() {
        post("/api/pause", body: #"{"minutes":60}"#)
    }

    @objc private func pauseTomorrow() {
        post("/api/pause", body: #"{"minutes":1440}"#)
    }

    @objc private func resume() {
        post("/api/resume", body: "{}")
    }

    @objc private func deleteLocalData() {
        post("/api/delete-local-data", body: "{}")
    }

    @objc private func openDiagnostics() {
        NSWorkspace.shared.open(repoRoot.appendingPathComponent(".harness/runtime"))
    }

    @objc private func quit() {
        runMake("beta-stop") { _ in
            NSApp.terminate(nil)
        }
    }

    private func runMake(_ target: String, completion: ((Bool) -> Void)? = nil) {
        DispatchQueue.global(qos: .utility).async {
            let process = Process()
            process.executableURL = URL(fileURLWithPath: "/usr/bin/make")
            process.currentDirectoryURL = self.repoRoot
            process.arguments = [target]
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

    private func post(_ path: String, body: String) {
        guard let base = envValue("INTENTOS_BETA_SERVICE_URL"), let url = URL(string: base + path) else {
            runMake("beta-dev")
            return
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = body.data(using: .utf8)
        URLSession.shared.dataTask(with: request).resume()
    }

    private func refreshStatus() {
        let state = envValue("INTENTOS_BETA_STATUS") ?? "stopped"
        guard state == "running", let base = envValue("INTENTOS_BETA_SERVICE_URL"), let url = URL(string: base + "/api/status") else {
            updateMenuStatus("Stopped")
            return
        }
        URLSession.shared.dataTask(with: url) { data, _, _ in
            let label = self.statusLabel(from: data) ?? "Running"
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
        if let pause = json["pause"] as? [String: Any], pause["paused"] as? Bool == true {
            return "Paused"
        }
        if let readiness = json["readiness"] as? [String: Any],
           readiness["state"] as? String == "setup_needed" {
            return "Setup Needed"
        }
        if let capture = json["capture"] as? [String: Any],
           let captureState = capture["state"] as? String,
           ["error", "stopped"].contains(captureState) {
            return "Capture Issue"
        }
        if let recorder = json["native_recorder"] as? [String: Any],
           let recorderState = recorder["state"] as? String,
           recorderState != "running" {
            return recorderState == "not_started" ? "Setup Needed" : "Capture Issue"
        }
        return "Running"
    }

    private func envValue(_ key: String) -> String? {
        let path = repoRoot.appendingPathComponent(".harness/runtime/beta/app.env")
        guard let text = try? String(contentsOf: path, encoding: .utf8) else { return nil }
        for line in text.split(separator: "\n").reversed() {
            let prefix = key + "="
            if line.hasPrefix(prefix) {
                return String(line.dropFirst(prefix.count))
            }
        }
        return nil
    }

    private func findRepoRoot() -> URL {
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
}
