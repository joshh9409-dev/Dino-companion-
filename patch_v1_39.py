from pathlib import Path
import re

root = Path(".")
main = root / "app/src/main/java/com/example/dinocompanion/MainActivity.kt"

code = r'''package com.example.dinocompanion

import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val screen = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(Color.rgb(18, 35, 55))
            setPadding(40, 40, 40, 40)
        }

        screen.addView(TextView(this).apply {
            text = "DINO COMPANION"
            textSize = 30f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
        })

        screen.addView(TextView(this).apply {
            text = "LAUNCH TEST v1.39\\n\\nIf you can see this screen, Android can launch the app correctly."
            textSize = 17f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
            setPadding(0, 30, 0, 0)
        })

        setContentView(screen)
    }
}
'''

main.write_text(code, encoding="utf-8")

g = root / "app/build.gradle.kts"
if g.exists():
    s = g.read_text(encoding="utf-8")
    s = re.sub(r'versionCode\s*=\s*\d+', 'versionCode = 42', s)
    s = re.sub(r'versionName\s*=\s*"[^"]+"', 'versionName = "1.39"', s)
    g.write_text(s, encoding="utf-8")

print("v1.39 bare launcher test applied")
