import Cocoa

extension IntentOSBetaApp {
    func envValue(_ key: String) -> String? {
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

    func isBetaRecordedRunning() -> Bool {
        guard envValue("INTENTOS_BETA_STATUS") == "running" else {
            return false
        }
        return recordedProcessIsAlive("INTENTOS_BETA_SERVICE_PID") &&
            recordedProcessIsAlive("INTENTOS_BETA_UI_PID")
    }

    func openRecordedDashboard(anchor: String? = nil) -> Bool {
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
        return NSWorkspace.shared.open(dashboard)
    }

    func recordedProcessIsAlive(_ key: String) -> Bool {
        guard let value = envValue(key),
              let pid = Int32(value.trimmingCharacters(in: .whitespacesAndNewlines)),
              pid > 0
        else {
            return false
        }
        return kill(pid, 0) == 0
    }

    func minutesUntilTomorrow(now: Date = Date()) -> Int {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: now)
        guard let tomorrow = calendar.date(byAdding: .day, value: 1, to: today) else {
            return 1440
        }
        let seconds = tomorrow.timeIntervalSince(now)
        return max(1, Int((seconds / 60.0).rounded(.up)))
    }

    func runtimeRoot() -> URL {
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

    func findRepoRoot() -> URL {
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

    func isBundledRuntime() -> Bool {
        guard let runtime = Bundle.main.resourceURL?.appendingPathComponent("intent-os-runtime") else {
            return false
        }
        return FileManager.default.fileExists(atPath: runtime.appendingPathComponent("Makefile").path)
    }

    func applicationSupportRoot() -> URL {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? URL(fileURLWithPath: NSHomeDirectory()).appendingPathComponent("Library/Application Support")
        let root = base.appendingPathComponent("IntentOS", isDirectory: true)
        try? FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        return root
    }
}
