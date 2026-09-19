from pathlib import Path
import re
import shutil

root = Path(".")
src = root / "app/src/main/java/com/example/dinocompanion"
src.mkdir(parents=True, exist_ok=True)

for p in list(src.rglob("*.kt")):
    p.unlink()
layout = root / "app/src/main/res/layout"
if layout.exists():
    shutil.rmtree(layout)

main = r'''
package com.example.dinocompanion

import android.Manifest
import android.app.*
import android.content.*
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.graphics.*
import android.net.Uri
import android.os.*
import android.provider.Settings
import android.view.*
import android.widget.EditText
import android.widget.Toast
import kotlin.math.max
import kotlin.math.min

class MainActivity : Activity() {
    private lateinit var game: DinoGameView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(42, 105, 150)
        window.navigationBarColor = Color.rgb(19, 58, 84)
        window.decorView.systemUiVisibility = 0
        game = DinoGameView(this)
        setContentView(game)
    }

    fun renameDino() {
        val input = EditText(this)
        input.setText(game.dinoName)
        input.selectAll()
        val dialog = AlertDialog.Builder(this)
            .setTitle("Rename your dinosaur")
            .setView(input)
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Save", DialogInterface.OnClickListener { _, _ ->
                game.dinoName = input.text.toString().trim().ifEmpty { game.dinoName }.take(18)
                game.save()
                game.invalidate()
            })
            .create()
        dialog.show()
    }

    fun overlaySettings() {
        val permission = Settings.canDrawOverlays(this)
        val openSettings = DialogInterface.OnClickListener { _, _ ->
            startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:" + packageName)))
        }
        val toggle = DialogInterface.OnClickListener { _, _ ->
            if (!Settings.canDrawOverlays(this)) {
                startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:" + packageName)))
            } else {
                game.overlayOn = !game.overlayOn
                game.save()
                if (game.overlayOn) startDinoOverlay() else stopDinoOverlay()
                game.invalidate()
            }
        }
        val dialog = AlertDialog.Builder(this)
            .setTitle("Overlay Companion")
            .setMessage(if (permission) "Overlay permission is ON. Your Dino can float above other apps." else "The floating Dino needs Display over other apps permission.")
            .setNegativeButton("Close", null)
            .setNeutralButton(if (permission) "Open settings" else "Grant permission", openSettings)
            .setPositiveButton(if (game.overlayOn) "Turn off" else "Turn on", toggle)
            .create()
        dialog.show()
    }

    private fun startDinoOverlay() {
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 41)
            Toast.makeText(this, "Allow notifications, then turn the overlay on again.", Toast.LENGTH_LONG).show()
            game.overlayOn = false
            game.save()
            return
        }
        try {
            val i = Intent(this, DinoOverlayService::class.java)
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(i) else startService(i)
        } catch (_: Exception) {
            game.overlayOn = false
            game.save()
            Toast.makeText(this, "Overlay could not be started.", Toast.LENGTH_SHORT).show()
        }
    }

    fun stopDinoOverlay() {
        try { stopService(Intent(this, DinoOverlayService::class.java)) } catch (_: Exception) {}
    }

    override fun onResume() {
        super.onResume()
        if (::game.isInitialized) game.invalidate()
    }

    override fun onBackPressed() {
        if (::game.isInitialized && game.page != Page.HOME) {
            game.page = Page.HOME
            game.invalidate()
        } else super.onBackPressed()
    }
}

enum class Page { HOME, CHOOSE, CARE, PLAY, SHOP, INVENTORY, SETTINGS }

data class DinoDef(val id: String, val title: String, val color: Int, val accent: Int)

class DinoGameView(private val ctx: Context) : View(ctx) {
    private val prefs = ctx.getSharedPreferences("dino_companion", Context.MODE_PRIVATE)
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val dinos = listOf(
        DinoDef("trex", "T-Rex", Color.rgb(87,157,91), Color.rgb(52,112,61)),
        DinoDef("triceratops", "Triceratops", Color.rgb(104,147,181), Color.rgb(62,96,128)),
        DinoDef("pterodactyl", "Pterodactyl", Color.rgb(143,100,171), Color.rgb(92,59,116)),
        DinoDef("stegosaurus", "Stegosaurus", Color.rgb(215,137,73), Color.rgb(151,82,38))
    )

    var page = Page.HOME
    var selectedId = prefs.getString("species", "trex") ?: "trex"
    var dinoName = prefs.getString("name", "Rex") ?: "Rex"
    var stage = prefs.getInt("stage", 1)
    var xp = prefs.getInt("xp", 32)
    var hunger = prefs.getInt("hunger", 78)
    var happiness = prefs.getInt("happiness", 100)
    var energy = prefs.getInt("energy", 79)
    var cleanliness = prefs.getInt("cleanliness", 90)
    var bond = prefs.getInt("bond", 12)
    var coins = prefs.getInt("coins", 52)
    var overlayOn = prefs.getBoolean("overlay", false)
    var food = prefs.getInt("food", 3)
    var toys = prefs.getInt("toys", 1)
    var gems = prefs.getInt("gems", 0)

    private var frame = 0
    private var tick = 0
    private var pressX = 0f
    private var pressY = 0f
    private var lastTap = 0L
    private val dino: DinoDef get() = dinos.firstOrNull { it.id == selectedId } ?: dinos[0]

    init {
        post(object : Runnable {
            override fun run() {
                frame = (frame + 1) % 3
                tick++
                if (tick % 90 == 0) {
                    energy = max(0, energy - 1)
                    hunger = max(0, hunger - 1)
                    save()
                }
                invalidate()
                postDelayed(this, 180L)
            }
        })
    }

    fun save() {
        prefs.edit().putString("species", selectedId).putString("name", dinoName)
            .putInt("stage", stage).putInt("xp", xp).putInt("hunger", hunger)
            .putInt("happiness", happiness).putInt("energy", energy)
            .putInt("cleanliness", cleanliness).putInt("bond", bond)
            .putInt("coins", coins).putBoolean("overlay", overlayOn)
            .putInt("food", food).putInt("toys", toys).putInt("gems", gems).apply()
    }

    override fun onDraw(c: Canvas) {
        drawBackground(c)
        when (page) {
            Page.HOME -> drawHome(c)
            Page.CHOOSE -> drawChoose(c)
            Page.CARE -> drawCare(c)
            Page.PLAY -> drawPlay(c)
            Page.SHOP -> drawShop(c)
            Page.INVENTORY -> drawInventory(c)
            Page.SETTINGS -> drawSettings(c)
        }
    }

    private fun drawBackground(c: Canvas) {
        val h = height.toFloat()
        paint.shader = LinearGradient(0f,0f,0f,h,Color.rgb(112,199,238),Color.rgb(230,248,255),Shader.TileMode.CLAMP)
        c.drawRect(0f,0f,width.toFloat(),h,paint)
        paint.shader = null
        paint.color = Color.argb(120,255,255,255)
        for (i in 0..5) {
            val x = (i * 190 + 25).toFloat()
            val y = 82f + (i % 3) * 52f
            c.drawOval(x,y,x+105,y+32,paint)
            c.drawOval(x+34,y-14,x+138,y+35,paint)
        }
        paint.color = Color.rgb(113,181,99)
        c.drawRect(0f,h-112f,width.toFloat(),h,paint)
        paint.color = Color.rgb(87,151,77)
        c.drawRect(0f,h-112f,width.toFloat(),h-103f,paint)
    }

    private fun text(c: Canvas,s:String,x:Float,y:Float,size:Float,color:Int=Color.WHITE,center:Boolean=false,bold:Boolean=false) {
        paint.shader=null; paint.color=color; paint.textSize=size
        paint.typeface=if(bold) Typeface.DEFAULT_BOLD else Typeface.DEFAULT
        paint.textAlign=if(center) Paint.Align.CENTER else Paint.Align.LEFT
        c.drawText(s,x,y,paint)
    }

    private fun round(c:Canvas,l:Float,t:Float,r:Float,b:Float,rad:Float,color:Int) {
        paint.shader=null; paint.color=color; c.drawRoundRect(l,t,r,b,rad,rad,paint)
    }

    private fun button(c:Canvas,l:Float,t:Float,r:Float,b:Float,label:String,icon:String="",color:Int=Color.rgb(75,139,171)) {
        round(c,l,t+5,r,b+5,22f,Color.argb(70,20,70,90))
        round(c,l,t,r,b,22f,color)
        if(icon.isNotEmpty()) text(c,icon,(l+r)/2f,t+31f,24f,Color.WHITE,true)
        text(c,label,(l+r)/2f,b-13f,12f,Color.WHITE,true,true)
    }

    private fun header(c:Canvas,title:String) {
        text(c,title,width/2f,48f,24f,Color.WHITE,true,true)
        button(c,18f,18f,75f,63f,"","‹",Color.argb(100,40,100,130))
    }

    private fun stat(c:Canvas,label:String,value:Int,y:Float,color:Int) {
        text(c,label,28f,y,12f,Color.rgb(35,75,90),false,true)
        text(c,value.toString()+"%",width-28f,y,12f,Color.rgb(35,75,90),false,true)
        round(c,28f,y+8,width-28f,y+19,7f,Color.LTGRAY)
        round(c,28f,y+8,28f+(width-56f)*value/100f,y+19,7f,color)
    }

    private fun drawHome(c:Canvas) {
        text(c,"DINO COMPANION",width/2f,48f,29f,Color.WHITE,true,true)
        text(c,"Your little world, always with you",width/2f,70f,12f,Color.WHITE,true)
        round(c,18f,88f,width-18f,310f,28f,Color.argb(235,248,253,255))
        text(c,dinoName,36f,118f,20f,dino.color,false,true)
        text(c,dino.title+"  •  Stage "+stage,36f,140f,13f,Color.DKGRAY)
        stat(c,"Hunger",hunger,166f,Color.rgb(242,165,62))
        stat(c,"Happiness",happiness,194f,Color.rgb(88,190,119))
        stat(c,"Energy",energy,222f,Color.rgb(88,151,224))
        stat(c,"Cleanliness",cleanliness,250f,Color.rgb(85,189,202))
        stat(c,"Bond",bond,278f,Color.rgb(174,101,190))
        drawDino(c,width/2f,405f,1f)
        round(c,24f,510f,width-24f,584f,20f,Color.argb(235,255,255,255))
        text(c,"EVOLUTION",42f,536f,11f,Color.GRAY,false,true)
        val need=stage*100
        val progress=min(1f,xp/need.toFloat())
        text(c,if(stage<4) "Stage "+stage+" → "+(stage+1) else "MAX EVOLUTION",42f,559f,15f,dino.color,false,true)
        round(c,175f,548f,width-42f,562f,7f,Color.LTGRAY)
        round(c,175f,548f,175f+(width-217f)*progress,562f,7f,dino.color)
        text(c,xp.toString()+" / "+need+" XP",width-48f,537f,10f,Color.GRAY,false)
        val y=height-103f
        button(c,18f,y,width/2f-9,y+64,"FOOD & CARE","♡",Color.rgb(80,160,115))
        button(c,width/2f+9,y,width-18f,y+64,"PLAY","★",Color.rgb(126,100,181))
        button(c,18f,y-73,width/2f-9,y-9,"CHOOSE DINO","◆",Color.rgb(65,128,172))
        button(c,width/2f+9,y-73,width-18f,y-9,"SHOP","◇",Color.rgb(190,130,67))
    }

    private fun drawChoose(c:Canvas) {
        header(c,"CHOOSE YOUR DINOSAUR")
        text(c,"Swipe or tap a dinosaur",width/2f,88f,14f,Color.WHITE,true)
        dinos.forEachIndexed { i,d ->
            val top=112f+i*105f
            round(c,20f,top,width-20f,top+91f,22f,if(d.id==selectedId) Color.WHITE else Color.argb(190,255,255,255))
            drawDino(c,74f,top+47f,.45f,d)
            text(c,d.title,125f,top+39f,18f,d.accent,false,true)
            text(c,"4 evolution stages",125f,top+61f,12f,Color.DKGRAY)
            if(d.id==selectedId) text(c,"ACTIVE",width-42f,top+50f,10f,d.color,true,true)
        }
        button(c,35f,height-100f,width-35f,height-36f,"USE THIS DINOSAUR","✓",dino.color)
    }

    private fun drawCare(c:Canvas) {
        header(c,"FOOD & CARE")
        text(c,"Keep "+dinoName+" healthy and happy",width/2f,89f,14f,Color.WHITE,true)
        round(c,20f,108f,width-20f,395f,26f,Color.argb(235,248,253,255))
        stat(c,"Hunger",hunger,145f,Color.rgb(242,165,62))
        stat(c,"Happiness",happiness,190f,Color.rgb(88,190,119))
        stat(c,"Energy",energy,235f,Color.rgb(88,151,224))
        stat(c,"Cleanliness",cleanliness,280f,Color.rgb(85,189,202))
        stat(c,"Bond",bond,325f,Color.rgb(174,101,190))
        button(c,25f,430f,width/2f-10,505f,"FEED","●",Color.rgb(93,164,92))
        button(c,width/2f+10,430f,width-25f,505f,"CLEAN","✦",Color.rgb(73,158,181))
        button(c,25f,525f,width/2f-10,600f,"REST","☾",Color.rgb(76,122,181))
        button(c,width/2f+10,525f,width-25f,600f,"PET","♥",Color.rgb(175,91,135))
        text(c,"Food: "+food+"   •   Toys: "+toys,width/2f,635f,13f,Color.WHITE,true,true)
    }

    private fun drawPlay(c:Canvas) {
        header(c,"PLAY")
        text(c,"Mini-games build XP, happiness and bond",width/2f,89f,14f,Color.WHITE,true)
        round(c,22f,113f,width-22f,360f,28f,Color.argb(235,248,253,255))
        drawDino(c,width/2f,232f,.82f)
        text(c,"DINO DASH",width/2f,330f,21f,dino.accent,true,true)
        text(c,"Tap the button to train your dinosaur",width/2f,350f,12f,Color.DKGRAY,true)
        button(c,35f,405f,width-35f,485f,"TAP DINO!","★",dino.color)
        button(c,35f,510f,width-35f,580f,"PLAY BALL","●",Color.rgb(126,100,181))
        text(c,"Games award XP and coins.",width/2f,620f,12f,Color.WHITE,true)
    }

    private fun drawShop(c:Canvas) {
        header(c,"SHOP")
        text(c,"Coins: "+coins+"   •   Gems: "+gems,width/2f,89f,14f,Color.WHITE,true,true)
        shopCard(c,20f,112f,"FOOD PACK","3 meals","10 coins")
        shopCard(c,20f,220f,"TOY","Boost happiness","18 coins")
        shopCard(c,20f,328f,"GEM","Rare currency","50 coins")
        shopCard(c,20f,436f,"XP BOOST","+50 XP","35 coins")
        button(c,30f,565f,width-30f,635f,"FREE DAILY COIN","+1",Color.rgb(190,130,67))
    }

    private fun shopCard(c:Canvas,x:Float,y:Float,title:String,desc:String,price:String) {
        round(c,x,y,width-x,y+90f,22f,Color.argb(235,248,253,255))
        text(c,title,x+18f,y+31f,16f,dino.accent,false,true)
        text(c,desc,x+18f,y+55f,12f,Color.DKGRAY)
        button(c,width-130f,y+13f,width-35f,y+77f,price,"◇",Color.rgb(190,130,67))
    }

    private fun drawInventory(c:Canvas) {
        header(c,"INVENTORY")
        text(c,"Everything you've collected",width/2f,89f,14f,Color.WHITE,true)
        item(c,22f,115f,"FOOD",food.toString(),"Meals ready to use")
        item(c,22f,220f,"TOYS",toys.toString(),"Play items")
        item(c,22f,325f,"GEMS",gems.toString(),"Rare currency")
        item(c,22f,430f,"COINS",coins.toString(),"Shop currency")
        button(c,30f,560f,width-30f,630f,"BACK HOME","⌂",dino.color)
    }

    private fun item(c:Canvas,x:Float,y:Float,title:String,count:String,desc:String) {
        round(c,x,y,width-x,y+86f,20f,Color.argb(235,248,253,255))
        round(c,x+15f,y+15f,x+68f,y+68f,17f,dino.color)
        text(c,count,x+41f,y+49f,18f,Color.WHITE,true,true)
        text(c,title,x+88f,y+34f,15f,dino.accent,false,true)
        text(c,desc,x+88f,y+57f,12f,Color.DKGRAY)
    }

    private fun drawSettings(c:Canvas) {
        header(c,"SETTINGS")
        setting(c,112f,"Dinosaur name",dinoName)
        setting(c,210f,"Overlay companion",if(overlayOn) "ON" else "OFF")
        setting(c,308f,"Animations","ON")
        setting(c,406f,"Sound","READY")
        button(c,30f,525f,width-30f,595f,"RESET DINO","↻",Color.rgb(170,79,78))
        text(c,"Dino Companion 1.41",width/2f,640f,12f,Color.WHITE,true)
    }

    private fun setting(c:Canvas,y:Float,title:String,value:String) {
        round(c,20f,y,width-20f,y+76f,20f,Color.argb(235,248,253,255))
        text(c,title,38f,y+32f,15f,dino.accent,false,true)
        text(c,value,width-38f,y+32f,13f,Color.DKGRAY,false,true)
    }

    private fun drawDino(c:Canvas,cx:Float,cy:Float,scale:Float,def:DinoDef=dino) {
        val bounce=kotlin.math.sin(tick/5.0).toFloat()*5f*scale
        val res=resources
        var id=res.getIdentifier(def.id+"_stage"+stage+"_f"+(frame+1),"drawable",ctx.packageName)
        if(id==0) id=res.getIdentifier(def.id+"_stage"+stage,"drawable",ctx.packageName)
        if(id==0) id=res.getIdentifier(def.id+"_stage1","drawable",ctx.packageName)
        paint.color=Color.argb(70,20,50,50)
        c.drawOval(cx-72f*scale,cy+82f*scale,cx+72f*scale,cy+103f*scale,paint)
        if(id!=0) {
            val bmp=BitmapFactory.decodeResource(res,id)
            if(bmp!=null) {
                val factor=min(190f*scale/bmp.width,190f*scale/bmp.height)
                val dw=bmp.width*factor; val dh=bmp.height*factor
                c.drawBitmap(bmp,null,RectF(cx-dw/2f,cy-dh/2f+bounce,cx+dw/2f,cy+dh/2f+bounce),paint)
                bmp.recycle()
                return
            }
        }
        paint.color=def.color
        c.drawOval(cx-62f*scale,cy-55f*scale+bounce,cx+62f*scale,cy+70f*scale+bounce,paint)
        paint.color=Color.WHITE
        c.drawCircle(cx-22f*scale,cy-18f*scale+bounce,10f*scale,paint)
        c.drawCircle(cx+22f*scale,cy-18f*scale+bounce,10f*scale,paint)
        paint.color=Color.DKGRAY
        c.drawCircle(cx-22f*scale,cy-18f*scale+bounce,4f*scale,paint)
        c.drawCircle(cx+22f*scale,cy-18f*scale+bounce,4f*scale,paint)
    }

    override fun onTouchEvent(e:MotionEvent):Boolean {
        if(e.action==MotionEvent.ACTION_DOWN){pressX=e.x;pressY=e.y;return true}
        if(e.action==MotionEvent.ACTION_UP){
            val dx=e.x-pressX
            if(page==Page.CHOOSE && kotlin.math.abs(dx)>80f){
                val i=dinos.indexOfFirst{it.id==selectedId}.let{if(it<0)0 else it}
                selectedId=dinos[if(dx<0)(i+1)%dinos.size else(i-1+dinos.size)%dinos.size].id
                save();invalidate();return true
            }
            handleTap(e.x,e.y);return true
        }
        return true
    }

    private fun handleTap(x:Float,y:Float) {
        val now=System.currentTimeMillis()
        if(now-lastTap<120)return
        lastTap=now
        if(page!=Page.HOME && x<95 && y<85){page=Page.HOME;invalidate();return}
        when(page){
            Page.HOME -> {
                val h=height.toFloat()
                when{
                    y>h-115 -> page=if(x<width/2)Page.CARE else Page.PLAY
                    y>h-195 -> page=if(x<width/2)Page.CHOOSE else Page.SHOP
                    y in 500f..595f -> page=Page.INVENTORY
                }
            }
            Page.CHOOSE -> {
                dinos.forEachIndexed{i,d->val top=112f+i*105f;if(y in top..top+91f){selectedId=d.id;save();invalidate()}}
                if(y>height-115){page=Page.HOME;save()}
            }
            Page.CARE -> when{
                y in 425f..515f&&x<width/2->feed()
                y in 425f..515f->clean()
                y in 520f..610f&&x<width/2->rest()
                y in 520f..610f->pet()
            }
            Page.PLAY -> when{y in 395f..495f->dash();y in 500f..590f->ball()}
            Page.SHOP -> when{
                y in 110f..210f&&coins>=10->{coins-=10;food+=3;save()}
                y in 215f..320f&&coins>=18->{coins-=18;toys+=1;save()}
                y in 325f..430f&&coins>=50->{coins-=50;gems+=1;save()}
                y in 430f..535f&&coins>=35->{coins-=35;xp+=50;evolve();save()}
                y in 555f..650f->{coins+=1;save()}
            }
            Page.INVENTORY -> if(y>550)page=Page.HOME
            Page.SETTINGS -> when{
                y in 100f..195f->(ctx as? MainActivity)?.renameDino()
                y in 195f..295f->(ctx as? MainActivity)?.overlaySettings()
                y in 510f..610f->resetDino()
            }
        }
        invalidate()
    }

    private fun addXp(n:Int){xp+=n;evolve();save()}
    private fun evolve(){
        val need=stage*100
        if(stage<4&&xp>=need){
            xp-=need;stage++;happiness=min(100,happiness+12);bond=min(100,bond+10);coins+=25
            Toast.makeText(ctx,dinoName+" evolved to Stage "+stage+"!",Toast.LENGTH_LONG).show()
        }
    }
    private fun feed(){if(food<=0){Toast.makeText(ctx,"No food left. Visit the shop.",Toast.LENGTH_SHORT).show();return};food--;hunger=min(100,hunger+25);energy=min(100,energy+5);happiness=min(100,happiness+3);addXp(8)}
    private fun clean(){cleanliness=min(100,cleanliness+28);happiness=min(100,happiness+5);addXp(6)}
    private fun rest(){energy=min(100,energy+30);hunger=max(0,hunger-3);addXp(4)}
    private fun pet(){happiness=min(100,happiness+12);bond=min(100,bond+5);addXp(5)}
    private fun dash(){happiness=min(100,happiness+8);energy=max(0,energy-4);coins+=2;addXp(15);Toast.makeText(ctx,"Dino Dash complete! +15 XP",Toast.LENGTH_SHORT).show()}
    private fun ball(){if(toys<=0){Toast.makeText(ctx,"Buy a toy in the shop.",Toast.LENGTH_SHORT).show();return};happiness=min(100,happiness+18);energy=max(0,energy-8);bond=min(100,bond+8);coins+=4;addXp(20);Toast.makeText(ctx,"Great game! +20 XP",Toast.LENGTH_SHORT).show()}
    private fun resetDino(){
        dinoName="Rex";selectedId="trex";stage=1;xp=32;hunger=78;happiness=100;energy=79;cleanliness=90;bond=12;coins=52;food=3;toys=1;gems=0;overlayOn=false
        save();(ctx as? MainActivity)?.stopDinoOverlay();invalidate()
    }
}
'''

(src / "MainActivity.kt").write_text(main, encoding="utf-8")

overlay = r'''
package com.example.dinocompanion

import android.app.*
import android.content.*
import android.content.pm.ServiceInfo
import android.graphics.*
import android.os.*
import android.provider.Settings
import android.view.*

class DinoOverlayService : Service() {
    private var wm: WindowManager? = null
    private var view: OverlayView? = null

    override fun onCreate() {
        super.onCreate()
        val id="dino_companion"
        if(Build.VERSION.SDK_INT>=26){
            getSystemService(NotificationManager::class.java).createNotificationChannel(
                NotificationChannel(id,"Dino Companion",NotificationManager.IMPORTANCE_LOW)
            )
        }
        val n=if(Build.VERSION.SDK_INT>=26)
            Notification.Builder(this,id).setSmallIcon(android.R.drawable.ic_menu_compass).setContentTitle("Dino Companion").setContentText("Your dinosaur is nearby").setOngoing(true).build()
        else Notification.Builder(this).setSmallIcon(android.R.drawable.ic_menu_compass).setContentTitle("Dino Companion").setContentText("Your dinosaur is nearby").setOngoing(true).build()
        if(Build.VERSION.SDK_INT>=29) startForeground(22,n,ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE) else startForeground(22,n)
        if(Settings.canDrawOverlays(this)) showOverlay()
    }

    private fun showOverlay(){
        wm=getSystemService(WINDOW_SERVICE) as WindowManager
        view=OverlayView(this)
        val type=if(Build.VERSION.SDK_INT>=26)WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY else WindowManager.LayoutParams.TYPE_PHONE
        val lp=WindowManager.LayoutParams(190,230,type,WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,PixelFormat.TRANSLUCENT)
        lp.gravity=Gravity.TOP or Gravity.END;lp.x=8;lp.y=160
        try{wm?.addView(view,lp)}catch(_:Exception){}
    }

    override fun onDestroy(){try{view?.let{wm?.removeView(it)}}catch(_:Exception){};view=null;super.onDestroy()}
    override fun onBind(intent:Intent?):IBinder?=null
}

class OverlayView(ctx:Context):View(ctx){
    private val prefs=ctx.getSharedPreferences("dino_companion",Context.MODE_PRIVATE)
    private val paint=Paint(Paint.ANTI_ALIAS_FLAG)
    private var tick=0
    init{post(object:Runnable{override fun run(){tick++;invalidate();postDelayed(this,180)}})}
    override fun onDraw(c:Canvas){
        val species=prefs.getString("species","trex")?:"trex"
        val stage=prefs.getInt("stage",1)
        var id=resources.getIdentifier(species+"_stage"+stage+"_f"+(tick%3+1),"drawable",context.packageName)
        if(id==0)id=resources.getIdentifier(species+"_stage"+stage,"drawable",context.packageName)
        paint.color=Color.argb(70,0,0,0);c.drawOval(35f,190f,155f,212f,paint)
        if(id!=0){
            val b=BitmapFactory.decodeResource(resources,id)
            c.drawBitmap(b,null,RectF(25f,20f,165f,195f),paint);b.recycle()
        }else{paint.color=Color.rgb(87,157,91);c.drawCircle(95f,105f,60f,paint)}
    }
    override fun onTouchEvent(e:MotionEvent):Boolean{
        if(e.action==MotionEvent.ACTION_UP){
            context.startActivity(Intent(context,MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        }
        return true
    }
}
'''
(src / "DinoOverlayService.kt").write_text(overlay, encoding="utf-8")

manifest = root / "app/src/main/AndroidManifest.xml"
manifest.write_text(r'''<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW"/>
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE"/>
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>
    <application android:allowBackup="false" android:icon="@drawable/ic_dino" android:roundIcon="@drawable/ic_dino"
        android:label="Dino Companion" android:theme="@style/Theme.DinoCompanion" android:supportsRtl="true">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter>
        </activity>
        <service android:name=".DinoOverlayService" android:exported="false" android:foregroundServiceType="specialUse">
            <property android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE" android:value="Persistent virtual companion overlay"/>
        </service>
    </application>
</manifest>
''', encoding="utf-8")

values = root / "app/src/main/res/values"
values.mkdir(parents=True, exist_ok=True)
(values / "themes.xml").write_text(r'''<resources>
<style name="Theme.DinoCompanion" parent="@android:style/Theme.Material.Light.NoActionBar">
<item name="android:fontFamily">sans</item>
<item name="android:windowActionModeOverlay">true</item>
<item name="android:statusBarColor">#2A6996</item>
<item name="android:navigationBarColor">#133A54</item>
<item name="android:windowLightStatusBar">false</item>
<item name="android:windowNoTitle">true</item>
</style>
</resources>
''', encoding="utf-8")

g = root / "app/build.gradle.kts"
s = g.read_text(encoding="utf-8")
s = re.sub(r'namespace\s*=\s*"[^"]+"','namespace = "com.example.dinocompanion"',s)
s = re.sub(r'applicationId\s*=\s*"[^"]+"','applicationId = "com.example.dinocompanion.v142"',s)
s = re.sub(r'versionCode\s*=\s*\d+','versionCode = 45',s)
s = re.sub(r'versionName\s*=\s*"[^"]+"','versionName = "1.42"',s)
s = re.sub(r'\s*implementation\("androidx\.appcompat:appcompat:[^"]+"\)','',s)
if 'implementation("androidx.appcompat:appcompat:1.7.0")' not in s:
    s=s.replace('dependencies {', 'dependencies {\n    implementation("androidx.appcompat:appcompat:1.7.0")')
g.write_text(s,encoding="utf-8")
print("Dino Companion v1.42 complete build generated")
