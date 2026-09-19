from pathlib import Path
import re, shutil

root = Path(".")
pkg = root / "app/src/main/java/com/example/dinocompanion"
main = pkg / "MainActivity.kt"
s = main.read_text(encoding="utf-8")

# Replace AppCompat activity with framework Activity to remove the entire
# AppCompat startup/theme path from the launcher activity.
s = s.replace("import androidx.appcompat.app.AppCompatActivity", "import android.app.Activity")
s = s.replace("class MainActivity : AppCompatActivity()", "class MainActivity : Activity()")
s = s.replace("import android.view.WindowInsetsController", "import android.view.WindowInsetsController")

# Remove AppCompat-only helper references if present.
s = s.replace("androidx.appcompat.app.AlertDialog", "android.app.AlertDialog")

main.write_text(s, encoding="utf-8")

# Use a framework Android theme for the launcher activity/application.
manifest = root / "app/src/main/AndroidManifest.xml"
if manifest.exists():
    ms = manifest.read_text(encoding="utf-8")
    ms = ms.replace('android:theme="@style/Theme.DinoCompanion"', 'android:theme="@style/Theme.DinoCompanion"')
    manifest.write_text(ms, encoding="utf-8")

themes = root / "app/src/main/res/values/themes.xml"
if themes.exists():
    ts = themes.read_text(encoding="utf-8")
    ts = re.sub(r'<style name="Theme\.DinoCompanion" parent="[^"]+">', '<style name="Theme.DinoCompanion" parent="@android:style/Theme.Material.Light.NoActionBar">', ts)
    # AppCompat theme attributes are not needed for the launcher.
    ts = ts.replace('<item name="android:fontFamily">sans</item>', '<item name="android:fontFamily">sans</item>')
    themes.write_text(ts, encoding="utf-8")

g = root / "app/build.gradle.kts"
if g.exists():
    gs = g.read_text(encoding="utf-8")
    gs = re.sub(r'versionCode\s*=\s*\d+', 'versionCode = 41', gs)
    gs = re.sub(r'versionName\s*=\s*"[^"]+"', 'versionName = "1.38"', gs)
    g.write_text(gs, encoding="utf-8")

print("v1.38 framework-only launcher patch applied")
