import Foundation

extension IntentOSBetaApp {
    func post(
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
        authorize(&request)
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

    func get(
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
        var request = URLRequest(url: url)
        authorize(&request)
        URLSession.shared.dataTask(with: request) { data, _, error in
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

    func retryGetAfterStart(
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

    func retryPostAfterStart(
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

    func authorize(_ request: inout URLRequest) {
        guard let token = envValue("INTENTOS_BETA_API_TOKEN"), !token.isEmpty else { return }
        request.setValue(token, forHTTPHeaderField: apiTokenHeader)
    }
}
