from pathlib import Path

root = Path(".")
src = root / "app/src/main/java/com/example/dinocompanion"
overlay_path = src / "DinoOverlayService.kt"

overlay = r'''package com.example.dinocompanion

import android.app.*
import android.content.*
import android.graphics.*
import android.os.*
import android.provider.Settings
import android.view.*
import java.util.Calendar
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin

class DinoOverlayService : Service() {
    private var wm: WindowManager? = null
    private var view: OverlayView? = null
    private var params: WindowManager.LayoutParams? = null
    private val prefs by lazy { getSharedPreferences("dino_companion", Context.MODE_PRIVATE) }
    private var lastWander = 0L
    private var wanderDirection = -1
    private var sleepUntil = 0L

    override fun onCreate() {
        super.onCreate()
        DinoLife.init(this)
        DinoLife.tick(prefs)
        createChannel()
        val notification = if (Build.VERSION.SDK_INT >= 26) {
            Notification.Builder(this, "dino_companion")
                .setSmallIcon(android.R.drawable.ic_menu_compass)
                .setContentTitle("Dino Companion")
                .setContentText("Your Dino is nearby")
                .setOngoing(true)
                .build()
        } else {
            Notification.Builder(this)
                .setSmallIcon(android.R.drawable.ic_menu_compass)
                .setContentTitle("Dino Companion")
                .setContentText("Your Dino is nearby")
                .setOngoing(true)
                .build()
        }
        if (Build.VERSION.SDK_INT >= 29) {
            startForeground(22, notification, android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        } else {
            startForeground(22, notification)
        }
        if (Settings.canDrawOverlays(this)) showOverlay()
    }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            getSystemService(NotificationManager::class.java).createNotificationChannel(
                NotificationChannel("dino_companion", "Dino Companion", NotificationManager.IMPORTANCE_LOW)
            )
        }
    }

    private fun showOverlay() {
        wm = getSystemService(WINDOW_SERVICE) as WindowManager
        view = OverlayView(this)
        val type = if (Build.VERSION.SDK_INT >= 26)
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        else WindowManager.LayoutParams.TYPE_PHONE

        val density = resources.displayMetrics.density
        val screenW = resources.displayMetrics.widthPixels
        val screenH = resources.displayMetrics.heightPixels
        val compact = screenW < (700 * density)
        val width = if (compact) (220 * density).toInt() else (260 * density).toInt()
        val height = if (compact) (260 * density).toInt() else (300 * density).toInt()

        val lp = WindowManager.LayoutParams(
            width, height, type,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        )
        lp.gravity = Gravity.TOP or Gravity.START

        val maxX = max(8, screenW - width - 8)
        val maxY = max(80, screenH - height - 8)
        val savedX = prefs.getInt("overlay_x", maxX)
        val savedY = prefs.getInt("overlay_y", 145)
        lp.x = savedX.coerceIn(8, maxX)
        lp.y = savedY.coerceIn(80, maxY)
        params = lp

        try { wm?.addView(view, lp) } catch (_: Exception) {}
    }

    fun moveOverlay(dx: Float, dy: Float) {
        val p = params ?: return
        val screenW = resources.displayMetrics.widthPixels
        val screenH = resources.displayMetrics.heightPixels
        val maxX = max(8, screenW - p.width - 8)
        val maxY = max(80, screenH - p.height - 8)
        p.x = (p.x + dx).toInt().coerceIn(8, maxX)
        p.y = (p.y + dy).toInt().coerceIn(80, maxY)
        savePosition(p)
        try { view?.let { wm?.updateViewLayout(it, p) } } catch (_: Exception) {}
    }

    fun snapToNearestEdge() {
        val p = params ?: return
        val screenW = resources.displayMetrics.widthPixels
        val maxX = max(8, screenW - p.width - 8)
        p.x = if (p.x < maxX / 2) 8 else maxX
        savePosition(p)
        try { view?.let { wm?.updateViewLayout(it, p) } } catch (_: Exception) {}
    }

    private fun savePosition(p: WindowManager.LayoutParams) {
        prefs.edit().putInt("overlay_x", p.x).putInt("overlay_y", p.y).apply()
    }

    fun openMain() {
        startActivity(Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP))
    }

    fun hideOverlay() {
        try { view?.visibility = View.GONE } catch (_: Exception) {}
        Handler(Looper.getMainLooper()).postDelayed({
            try { view?.visibility = View.VISIBLE } catch (_: Exception) {}
        }, 30_000L)
    }

    fun showInfo() {
        val mood = DinoLife.mood(prefs)
        val name = prefs.getString("name", "Rex") ?: "Rex"
        Handler(Looper.getMainLooper()).post {
            Toast.makeText(this, "$name is $mood", Toast.LENGTH_SHORT).show()
        }
    }

    private fun updateWindow() {
        val p = params ?: return
        val now = System.currentTimeMillis()
        val hour = Calendar.getInstance().get(Calendar.HOUR_OF_DAY)
        val battery = try {
            (getSystemService(BATTERY_SERVICE) as BatteryManager)
                .getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        } catch (_: Exception) { 100 }

        if (hour >= 23 || hour < 7 || battery < 15) {
            sleepUntil = max(sleepUntil, now + 1500L)
        }

        if (now >= lastWander + 220L && now >= sleepUntil) {
            lastWander = now
            val screenW = resources.displayMetrics.widthPixels
            val maxX = max(8, screenW - p.width - 8)
            p.x = (p.x + wanderDirection * 2).coerceIn(8, maxX)
            if (p.x == 8 || p.x == maxX) wanderDirection *= -1
            savePosition(p)
        }

        val screenH = resources.displayMetrics.heightPixels
        p.y = p.y.coerceIn(80, max(80, screenH - p.height - 8))
        try { view?.let { wm?.updateViewLayout(it, p) } } catch (_: Exception) {}
    }

    override fun onDestroy() {
        try { view?.let { wm?.removeView(it) } } catch (_: Exception) {}
        view = null
        params = null
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    inner class OverlayView(context: Context) : View(context) {
        private val paint = Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG)
        private var downX = 0f
        private var downY = 0f
        private var lastX = 0f
        private var lastY = 0f
        private var moved = false
        private var menu = false
        private var animation = 0f

        private val loop = object : Runnable {
            override fun run() {
                animation += 0.10f
                DinoLife.tick(prefs)
                updateWindow()
                invalidate()
                postDelayed(this, 90L)
            }
        }

        init {
            setLayerType(View.LAYER_TYPE_SOFTWARE, null)
            post(loop)
        }

        override fun onDraw(c: Canvas) {
            super.onDraw(c)
            val density = resources.displayMetrics.density
            val w = width.toFloat()
            val h = height.toFloat()
            val species = prefs.getString("species", "trex") ?: "trex"
            val stage = prefs.getInt("stage", 1)
            val mood = DinoLife.mood(prefs)
            val drift = sin(animation.toDouble()).toFloat() * 4f

            paint.color = Color.argb(75, 0, 0, 0)
            c.drawOval(w * .20f, h * .78f, w * .80f, h * .86f, paint)

            var id = resources.getIdentifier(
                species + "_stage" + stage + "_f" + ((animation.toInt() % 3) + 1),
                "drawable", packageName
            )
            if (id == 0) id = resources.getIdentifier(species + "_stage" + stage, "drawable", packageName)

            if (id != 0) {
                try {
                    val b = BitmapFactory.decodeResource(resources, id)
                    if (b != null && !b.isRecycled) {
                        val maxW = w * .72f
                        val maxH = h * .72f
                        val scale = min(maxW / b.width, maxH / b.height)
                        val dw = b.width * scale
                        val dh = b.height * scale
                        val left = (w - dw) / 2f + drift
                        val top = h * .08f + (h * .70f - dh) / 2f
                        c.drawBitmap(b, null, RectF(left, top, left + dw, top + dh), paint)
                        b.recycle()
                    }
                } catch (_: Throwable) {}
            }

            val bubble = when (mood) {
                "HUNGRY" -> "Hungry!"
                "SLEEPY" -> "Zzz..."
                "DIRTY" -> "Bath time!"
                "SAD" -> "Pet me"
                "CURIOUS" -> "What's that?"
                else -> "Hi!"
            }
            paint.color = Color.argb(225, 255, 255, 255)
            c.drawRoundRect(w * .15f, 8f, w * .85f, 50f, 18f, 18f, paint)
            paint.color = Color.rgb(42, 72, 80)
            paint.textSize = 14f * density
            paint.textAlign = Paint.Align.CENTER
            c.drawText(bubble, w / 2f, 35f, paint)

            if (menu) {
                val top = h * .72f
                paint.color = Color.argb(235, 26, 57, 62)
                c.drawRoundRect(w * .06f, top, w * .94f, h - 10f, 20f, 20f, paint)
                paint.color = Color.WHITE
                paint.textSize = 11f * density
                c.drawText("MENU", w * .20f, h - 24f, paint)
                c.drawText("SNAP", w * .50f, h - 24f, paint)
                c.drawText("HIDE", w * .80f, h - 24f, paint)
            }
        }

        override fun onTouchEvent(e: MotionEvent): Boolean {
            when (e.actionMasked) {
                MotionEvent.ACTION_DOWN -> {
                    downX = e.rawX
                    downY = e.rawY
                    lastX = downX
                    lastY = downY
                    moved = false
                    return true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = e.rawX - lastX
                    val dy = e.rawY - lastY
                    if (kotlin.math.abs(e.rawX - downX) > 8f || kotlin.math.abs(e.rawY - downY) > 8f) moved = true
                    moveOverlay(dx, dy)
                    lastX = e.rawX
                    lastY = e.rawY
                    return true
                }
                MotionEvent.ACTION_UP -> {
                    if (!moved) {
                        if (menu) {
                            val y = e.y / height
                            if (y > .72f) {
                                when {
                                    e.x < width * .34f -> openMain()
                                    e.x < width * .67f -> snapToNearestEdge()
                                    else -> hideOverlay()
                                }
                                menu = false
                            } else {
                                menu = false
                            }
                        } else {
                            DinoLife.onInteraction(prefs, "pet")
                            prefs.edit().putInt("happiness", min(100, prefs.getInt("happiness", 100) + 5)).apply()
                            menu = true
                        }
                        invalidate()
                    } else {
                        snapToNearestEdge()
                    }
                    return true
                }
            }
            return true
        }
    }
}
'''
overlay_path.write_text(overlay, encoding="utf-8")

# A small marker lets the workflow prove this post-build pass actually ran.
(root / "BUILD_POLISH_VERSION.txt").write_text("overlay-polish-1\n", encoding="utf-8")
