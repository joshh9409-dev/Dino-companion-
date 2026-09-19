from pathlib import Path
import shutil

main = Path("app/src/main/java/com/example/dinocompanion/MainActivity.kt")
s = main.read_text(encoding="utf-8")
start = s.index("    private fun buildHome() {")
end = s.index("\n    private fun showCare()", start)
s = s[:start] + '''    private fun buildHome() {
        home = DinoGameView(
            this,
            state,
            onOverlay = { overlaySettings() },
            onRename = { renameDino() }
        )
        setContentView(home)
    }
''' + s[end:]

old = '''        hideSystemBars()
        state = DinoState(this).also { it.ensureStarted(); it.applyTimeDecay() }
        buildHome()
        requestNotificationPermissionIfNeeded()'''
new = '''        hideSystemBars()
        try {
            state = DinoState(this).also { it.ensureStarted(); it.applyTimeDecay() }
            buildHome()
            requestNotificationPermissionIfNeeded()
        } catch (t: Throwable) {
            showStartupError(t)
        }'''
if old in s:
    s = s.replace(old, new)

if "private fun showStartupError" not in s:
    marker = "\n    override fun onResume()"
    helper = '''
    private fun showStartupError(t: Throwable) {
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(dp(24), dp(24), dp(24), dp(24))
        }
        box.addView(TextView(this).apply {
            text = "Dino Companion"
            textSize = 28f
            gravity = Gravity.CENTER
        })
        box.addView(TextView(this).apply {
            text = "Startup error: " + t.javaClass.simpleName
            textSize = 15f
            gravity = Gravity.CENTER
            setPadding(0, dp(16), 0, dp(16))
        })
        box.addView(Button(this).apply {
            text = "RETRY"
            setOnClickListener { recreate() }
        })
        setContentView(box)
    }
'''
    s = s.replace(marker, helper + marker)
main.write_text(s, encoding="utf-8")

g = Path("app/build.gradle.kts")
gs = g.read_text(encoding="utf-8")
gs = gs.replace('versionCode = 38', 'versionCode = 39')
gs = gs.replace('versionName = "1.35"', 'versionName = "1.36"')
g.write_text(gs, encoding="utf-8")

overlay = Path("app/src/main/java/com/example/dinocompanion/DinoOverlayService.kt")
o = overlay.read_text(encoding="utf-8")
o = o.replace("private var safeMargin = 4", "private var safeMargin = 0")
o = o.replace("WindowManager.LayoutParams(\n            dp(190), dp(150),", "WindowManager.LayoutParams(\n            dp(220), dp(190),")
overlay.write_text(o, encoding="utf-8")

shutil.copy("DinoGameView.kt", "app/src/main/java/com/example/dinocompanion/DinoGameView.kt")
print("Applied v1.36 visual and interaction overhaul.")
