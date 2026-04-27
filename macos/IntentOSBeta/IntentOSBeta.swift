import Cocoa
import Foundation

@main
final class AppDelegate: NSObject, NSApplicationDelegate {
    private let statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
    private lazy var repoRoot = findRepoRoot()
    private var statusMenuItem: NSMenuItem?

    func applicationDidFinishLaunching(_ notification: Notification) {
        rebuildMenu()
        refreshStatus()
        Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { _ in self.refreshStatus() }
    }

    private func rebuildMenu() {
        let menu = NSMenu()
        let status = NSMenuItem(title: "Capture: unknown", action: nil, keyEquivalent: "")
        status.isEnabled = false
        statusMenuItem = status
        menu.addItem(status)
        menu.addItem(NSMenuItem.separator())
        menu.addItem(item("Open Dashboard", #selector(openDashboard)))
        menu.addItem(item("Start Beta", #selector(startBeta)))
        menu.addItem(item("Stop Beta", #selector(stopBeta)))
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
        runMake("beta-dev")
    }

    @objc private func stopBeta() {
        runMake("beta-stop")
    }

    @objc private func openDashboard() {
        if let url = envValue("INTENTOS_BETA_UI_URL"), let dashboard = URL(string: url) {
            NSWorkspace.shared.open(dashboard)
        } else {
            runMake("beta-dev")
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { self.openDashboard() }
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
        runMake("beta-stop")
        NSApp.terminate(nil)
    }

    private func runMake(_ target: String) {
        DispatchQueue.global(qos: .utility).async {
            let process = Process()
            process.executableURL = URL(fileURLWithPath: "/usr/bin/make")
            process.currentDirectoryURL = self.repoRoot
            process.arguments = [target]
            try? process.run()
            process.waitUntilExit()
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
        let capture = state == "running" ? "Running" : "Stopped"
        statusItem.button?.title = "IntentOS \(capture)"
        statusMenuItem?.title = "Capture: \(capture)"
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
            return URL(fileURLWithPath: explicit)
        }
        var url = Bundle.main.bundleURL
        for _ in 0..<4 {
            url.deleteLastPathComponent()
        }
        return url
    }
}
