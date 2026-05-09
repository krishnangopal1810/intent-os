import Cocoa

extension IntentOSBetaApp {
    func startBetaIfNeeded(
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

    func runMake(_ target: String, completion: ((Bool) -> Void)? = nil) {
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

    func scriptPath(for target: String) -> String {
        switch target {
        case "beta-dev":
            return "scripts/harness/beta-dev.sh"
        case "beta-stop":
            return "scripts/harness/beta-stop.sh"
        default:
            return "scripts/harness/\(target).sh"
        }
    }

    func runtimeEnvironment() -> [String: String] {
        var env = ProcessInfo.processInfo.environment
        env["INTENTOS_RUNTIME_DIR"] = runtimeRoot().path
        env["INTENTOS_APP_BUNDLE_PATH"] = Bundle.main.bundleURL.path
        env["INTENTOS_BUNDLED_RUNTIME_PRESENT"] = isBundledRuntime() ? "1" : "0"
        if let runtime = Bundle.main.resourceURL?.appendingPathComponent("intent-os-runtime") {
            env["INTENTOS_BUNDLED_RUNTIME_PATH"] = runtime.path
        }
        return env
    }
}
