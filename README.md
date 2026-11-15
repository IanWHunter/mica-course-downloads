# MICA course experiment apps

MIT 2.132 and 2.133 · Ian Hunter

[Open MICA Sound Speed downloads](https://github.com/IanWHunter/mica-course-downloads/releases/tag/sound-speed-v48)

Choose **Mac — Apple silicon**, **Mac — Intel**, **Windows — x64**, or **Linux — x64** on the experiment's release page. Extract the archive completely and open the app inside it. The download includes the app, its tested Julia runtime and its packages. A separate Julia installation is not required.

Connect the workstation's USB cables. The app checks the vendor software and offers downloads when setup or an update is needed. Complete the vendor installer and reopen the app when prompted.

MICA Sound Speed v48 adds carriage-position plots starting at 0 mm, an apparent source-position estimate from absolute arrival delays, and a separate %VAF-versus-position plot. It retains the Julia measurement engine validated by a complete 250 mm, 51-position Mac workstation sweep in v47. All four v48 builds pass software and packaged startup checks. The v48 instructor test stopped at position 15 mm because the input records contained missing/corrupt samples. A v49 timing-protection correction is being built; its hardware test is pending. The full-sweep-tested [v47 baseline](https://github.com/IanWHunter/mica-course-downloads/releases/tag/sound-speed-v47) remains available. Windows/Linux physical workstation tests remain pending. This is an instructor bench preview. The Mac preview uses the app-specific opening instructions below.

### Mac: opening the app for the first time

For a course app downloaded from this page, if macOS says Apple cannot verify the app:

1. Dismiss the warning after trying to open the extracted app.
2. Open **Apple menu → System Settings → Privacy & Security**.
3. Scroll to **Security**, find the message for this app, and click **Open Anyway**.
4. Authenticate if asked, then confirm **Open**.

This approves this specific app. A new app or updated version may need approval again. If **Open Anyway** is missing, try opening the app again, then return to those settings.

[Apple’s instructions](https://support.apple.com/en-us/102445)

[Browse all experiment releases](https://github.com/IanWHunter/mica-course-downloads/releases)
