from pathlib import Path

# v1.32 visual patch: live stats and evolution panel.
home_path = Path("app/src/main/java/com/example/dinocompanion/HomeArtworkView.kt")
s = home_path.read_text(encoding="utf-8")
needle = "        // Dynamic rename button label. The surrounding glossy button remains from\n"
if "private fun drawLiveStats" not in s:
    s = s.replace(needle, "        drawLiveStats(canvas)\n        drawLiveEvolution(canvas)\n\n" + needle, 1)
marker = "    private fun drawCentered(canvas: Canvas, text: String, x: Float, y: Float, size: Float, color: Int, bold: Boolean) {\n"
insert = '''    private fun drawLiveStats(canvas: Canvas) {
        val rows = listOf(
            Triple("Hunger", state.hunger, Color.rgb(77, 201, 48)),
            Triple("Happiness", state.happiness, Color.rgb(255, 177, 18)),
            Triple("Energy", state.energy, Color.rgb(25, 154, 235)),
            Triple("Cleanliness", state.cleanliness, Color.rgb(157, 54, 231)),
            Triple("Bond", state.bond, Color.rgb(239, 58, 92))
        )
        val centers = floatArrayOf(319f, 412f, 505f, 598f, 691f)
        rows.forEachIndexed { i, row ->
            val y = centers[i]
            paint.color = Color.rgb(255, 249, 226)
            canvas.drawRect(122f, y - 31f, 468f, y + 31f, paint)
            drawText(canvas, row.first, 132f, y - 7f, 24f, Color.rgb(18, 91, 62), true, Paint.Align.LEFT)
            paint.color = Color.rgb(226, 223, 211)
            canvas.drawRoundRect(RectF(132f, y + 7f, 389f, y + 31f), 14f, 14f, paint)
            val fill = 132f + 257f * (row.second / 100f).coerceIn(0f, 1f)
            paint.color = row.third
            canvas.drawRoundRect(RectF(132f, y + 7f, fill, y + 31f), 14f, 14f, paint)
            drawText(canvas, "${row.second.toInt()}%", 398f, y + 26f, 24f, Color.rgb(18, 91, 62), true, Paint.Align.LEFT)
        }
    }

    private fun drawLiveEvolution(canvas: Canvas) {
        paint.color = Color.rgb(255, 249, 226)
        canvas.drawRoundRect(RectF(58f, 752f, 493f, 920f), 28f, 28f, paint)
        drawCentered(canvas, "Evolution: ${state.evolutionProgress()}%", 275f, 800f, 29f, Color.rgb(18, 91, 62), true)
        val age = String.format(java.util.Locale.UK, "%.1fh", state.evolutionHours())
        val required = if (state.requiredHours() % 1.0 == 0.0) "${state.requiredHours().toInt()}h" else "${state.requiredHours()}h"
        drawCentered(canvas, "Age: $age / $required", 275f, 838f, 25f, Color.rgb(112, 70, 28), true)
        drawCentered(canvas, "Keep caring for ${state.name}.", 275f, 876f, 21f, Color.rgb(112, 70, 28), false)
        drawCentered(canvas, "The clock keeps running even when", 275f, 902f, 18f, Color.rgb(112, 70, 28), false)
        drawCentered(canvas, "the app is closed.", 275f, 923f, 18f, Color.rgb(112, 70, 28), false)
    }

    private fun drawText(canvas: Canvas, text: String, x: Float, y: Float, size: Float, color: Int, bold: Boolean, align: Paint.Align) {
        paint.color = color
        paint.textSize = size
        paint.typeface = Typeface.create("sans-serif-rounded", if (bold) Typeface.BOLD else Typeface.NORMAL)
        paint.textAlign = align
        paint.style = Paint.Style.FILL
        canvas.drawText(text, x, y, paint)
    }

'''
if marker not in s:
    raise SystemExit("Expected HomeArtworkView marker was not found")
s = s.replace(marker, insert + marker, 1)
home_path.write_text(s, encoding="utf-8")

# v1.33 startup fix: make the launcher activity resilient and never silently crash.
main_path = Path("app/src/main/java/com/example/dinocompanion/MainActivity.kt")
m = main_path.read_text(encoding="utf-8")
old = '''    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        hideSystemBars()
        state = DinoState(this).also { it.ensureStarted(); it.applyTimeDecay() }
        buildHome()
        requestNotificationPermissionIfNeeded()
    }
'''
new = '''    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        try {
            state = DinoState(this).also { it.ensureStarted(); it.applyTimeDecay() }
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
            text = "The app hit a startup error. Tap Retry to start again."
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
if old not in m:
    raise SystemExit("Expected MainActivity onCreate block was not found")
m = m.replace(old, new, 1)
main_path.write_text(m, encoding="utf-8")

# Keep the activity visible while diagnosing instead of hiding all system bars.
build_path = Path("app/build.gradle.kts")
g = build_path.read_text(encoding="utf-8").replace('versionName = "1.31"', 'versionName = "1.33"')
build_path.write_text(g, encoding="utf-8")

print("Applied v1.33 startup fix and retained v1.32 dashboard changes.")
