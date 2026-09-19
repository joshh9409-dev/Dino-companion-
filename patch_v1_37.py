from pathlib import Path
import shutil

root = Path(".")
main = root / "app/src/main/java/com/example/dinocompanion/MainActivity.kt"
s = main.read_text(encoding="utf-8")

s = s.replace("private lateinit var home: HomeArtworkView", "private lateinit var home: View")

start = s.index("    override fun onCreate(savedInstanceState: Bundle?) {")
end = s.index("\n    override fun onResume()", start)
new_oncreate = '''    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Put a guaranteed-safe Android view on screen before loading the game.
        setContentView(LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(Color.rgb(12, 28, 48))
            addView(TextView(this@MainActivity).apply {
                text = "Dino Companion"
                textSize = 30f
                setTextColor(Color.WHITE)
                gravity = Gravity.CENTER
            })
            addView(TextView(this@MainActivity).apply {
                text = "Loading your dino..."
                textSize = 16f
                setTextColor(Color.LTGRAY)
                gravity = Gravity.CENTER
                setPadding(0, dp(14), 0, 0)
            })
            addView(ProgressBar(this@MainActivity).apply {
                isIndeterminate = true
            }, LinearLayout.LayoutParams(dp(48), dp(48)).apply {
                gravity = Gravity.CENTER
                topMargin = dp(20)
            })
        })

        window.decorView.post {
            try {
                hideSystemBars()
                state = DinoState(this).also { it.ensureStarted(); it.applyTimeDecay() }
                buildHome()
                requestNotificationPermissionIfNeeded()
            } catch (t: Throwable) {
                showStartupError(t)
            }
        }
    }
'''
s = s[:start] + new_oncreate + s[end:]

old_resume = '''    override fun onResume() {
        super.onResume()
        if (::state.isInitialized) {
            state.applyTimeDecay()
            home.invalidate()
        }
    }'''
new_resume = '''    override fun onResume() {
        super.onResume()
        if (::state.isInitialized) {
            try {
                state.applyTimeDecay()
                if (::home.isInitialized) home.invalidate()
            } catch (_: Throwable) { }
        }
    }'''
s = s.replace(old_resume, new_resume)

start = s.index("    private fun buildHome() {")
end = s.index("\n    private fun showCare()", start)
new_home = '''    private fun buildHome() {
        home = DinoGameView(
            this,
            state,
            onOverlay = { overlaySettings() },
            onRename = { renameDino() }
        )
        setContentView(home)
    }

    private fun showStartupError(t: Throwable) {
        val detail = t.message?.take(160)?.replace("\\n", " ") ?: "Unknown startup error"
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(dp(24), dp(24), dp(24), dp(24))
            setBackgroundColor(Color.rgb(12, 28, 48))
        }
        box.addView(TextView(this).apply {
            text = "Dino Companion"
            textSize = 28f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
        })
        box.addView(TextView(this).apply {
            text = "Startup error: " + t.javaClass.simpleName + "\\n" + detail
            textSize = 15f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
            setPadding(0, dp(18), 0, dp(18))
        })
        box.addView(Button(this).apply {
            text = "RETRY"
            setOnClickListener { recreate() }
        })
        setContentView(box)
    }
'''
s = s[:start] + new_home + s[end:]

main.write_text(s, encoding="utf-8")
src = root / "DinoGameView.kt"
if src.exists():
    shutil.copy(src, root / "app/src/main/java/com/example/dinocompanion/DinoGameView.kt")

# Version 1.37 / code 40
g = root / "app/build.gradle.kts"
if g.exists():
    gs = g.read_text(encoding="utf-8")
    import re
    gs = re.sub(r'versionCode\s*=\s*\d+', 'versionCode = 40', gs)
    gs = re.sub(r'versionName\s*=\s*"[^"]+"', 'versionName = "1.37"', gs)
    g.write_text(gs, encoding="utf-8")
print("v1.37 safe launcher patch applied")
