from pathlib import Path
import re

root = Path(".")
pkg = root / "app/src/main/java/com/example/dinocompanion"
main = pkg / "MainActivity.kt"

main.write_text(r'''package com.example.dinocompanion

import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val screen = LinearLayout(this)
        screen.orientation = LinearLayout.VERTICAL
        screen.gravity = Gravity.CENTER
        screen.setBackgroundColor(Color.rgb(30, 90, 140))
        screen.setPadding(40, 40, 40, 40)

        val title = TextView(this)
        title.text = "DINO COMPANION"
        title.textSize = 32f
        title.setTextColor(Color.WHITE)
        title.gravity = Gravity.CENTER
        screen.addView(title)

        val message = TextView(this)
        message.text = "CLEAN LAUNCH TEST\\n\\nThis is a completely fresh Android package.\\nIf this screen appears, the phone can launch the app."
        message.textSize = 17f
        message.setTextColor(Color.WHITE)
        message.gravity = Gravity.CENTER
        message.setPadding(0, 30, 0, 0)
        screen.addView(message)

        setContentView(screen)
    }
}
''', encoding="utf-8")

manifest = root / "app/src/main/AndroidManifest.xml"
manifest.write_text(r'''<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:theme="@style/Theme.DinoCompanion"
        android:label="Dino Companion Clean"
        android:allowBackup="false"
        android:supportsRtl="true">
        <activity
            android:name="com.example.dinocompanion.MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>
''', encoding="utf-8")

themes = root / "app/src/main/res/values/themes.xml"
themes.write_text(r'''<resources>
    <style name="Theme.DinoCompanion" parent="@android:style/Theme.Material.Light.NoActionBar">
        <item name="android:fontFamily">sans</item>
        <item name="android:windowActionModeOverlay">true</item>
        <item name="android:colorAccent">#77A85B</item>
        <item name="android:navigationBarColor">#1E5A8C</item>
        <item name="android:statusBarColor">#1E5A8C</item>
        <item name="android:windowLightStatusBar">false</item>
    </style>
</resources>
''', encoding="utf-8")

g = root / "app/build.gradle.kts"
s = g.read_text(encoding="utf-8")
s = re.sub(r'namespace\s*=\s*"[^"]+"', 'namespace = "com.example.dinocompanion"', s)
s = re.sub(r'applicationId\s*=\s*"[^"]+"', 'applicationId = "com.example.dinocompanion.clean"', s)
s = re.sub(r'versionCode\s*=\s*\d+', 'versionCode = 43', s)
s = re.sub(r'versionName\s*=\s*"[^"]+"', 'versionName = "1.40"', s)
# Remove all dependencies except the Android/Kotlin plugins already supplied.
s = re.sub(r'\ndependencies\s*\{.*?\}\s*', '\n', s, flags=re.S)
g.write_text(s, encoding="utf-8")
print("v1.40 completely fresh package launcher test applied")
