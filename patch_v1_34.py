from pathlib import Path

# v1.35 clean-install launcher patch.
p = Path("app/src/main/java/com/example/dinocompanion/MainActivity.kt")
s = p.read_text(encoding="utf-8")

start = s.index("    override fun onCreate(savedInstanceState: Bundle?) {")
end = s.index("\n    override fun onResume()", start)

new_block = '''    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        try {
            state = DinoState(this).also {
                it.ensureStarted()
                it.applyTimeDecay()
            }
            buildHome()
            requestNotificationPermissionIfNeeded()
        } catch (t: Throwable) {
            showStartupError(t)
        }
    }

    private fun showStartupError(t: Throwable) {
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(dp(24), dp(24), dp(24), dp(24))
        }

        box.addView(TextView(this).apply {
            text = "Dino Companion"
            textSize = 30f
            setTextColor(Color.rgb(18, 91, 62))
            gravity = Gravity.CENTER
        })

        box.addView(TextView(this).apply {
            text = "Startup error. Tap Retry to try again."
            textSize = 17f
            setTextColor(Color.DKGRAY)
            gravity = Gravity.CENTER
            setPadding(0, dp(18), 0, dp(18))
        })

        box.addView(Button(this).apply {
            text = "RETRY"
            setOnClickListener { recreate() }
        }, LinearLayout.LayoutParams(-1, dp(52)))

        box.addView(TextView(this).apply {
            text = t.javaClass.simpleName + ": " + (t.message ?: "unknown error")
            textSize = 11f
            setTextColor(Color.GRAY)
            gravity = Gravity.CENTER
            setPadding(0, dp(18), 0, 0)
        })

        setContentView(box)
    }
'''

s = s[:start] + new_block + s[end:]

hs = s.index("    private fun hideSystemBars() {")
hs_end = s.index("\n    }", hs) + len("\n    }")
s = s[:hs] + '''    private fun hideSystemBars() {
        // Intentionally non-immersive for Android 16 startup reliability.
    }''' + s[hs_end:]

p.write_text(s, encoding="utf-8")

g = Path("app/build.gradle.kts")
gs = g.read_text(encoding="utf-8")
gs = gs.replace('applicationId = "com.example.dinocompanion"', 'applicationId = "com.example.dinocompanion.v135"')
gs = gs.replace('versionCode = 37', 'versionCode = 38')
gs = gs.replace('versionName = "1.31"', 'versionName = "1.35"')
g.write_text(gs, encoding="utf-8")

print("Applied v1.35 clean-install launcher patch.")
