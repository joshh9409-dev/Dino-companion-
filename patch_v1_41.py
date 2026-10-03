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

private class JungleBackdropDrawable : android.graphics.drawable.Drawable() {
    private val p=Paint(Paint.ANTI_ALIAS_FLAG)
    override fun draw(c:Canvas){
        val w=bounds.width().toFloat();val h=bounds.height().toFloat()
        p.shader=LinearGradient(0f,0f,0f,h,Color.rgb(44,139,181),Color.rgb(20,76,58),Shader.TileMode.CLAMP);c.drawRect(0f,0f,w,h,p);p.shader=null
        p.color=Color.rgb(48,108,91)
        val path=Path();path.moveTo(0f,h*.28f);path.lineTo(w*.18f,h*.18f);path.lineTo(w*.35f,h*.27f);path.lineTo(w*.53f,h*.16f);path.lineTo(w*.72f,h*.25f);path.lineTo(w*.9f,h*.14f);path.lineTo(w,h*.25f);path.lineTo(w,h*.5f);path.lineTo(0f,h*.5f);path.close();c.drawPath(path,p)
        p.color=Color.rgb(91,171,106);c.drawRect(w*.47f,h*.2f,w*.54f,h*.7f,p)
        p.color=Color.argb(110,210,247,255);c.drawRect(w*.48f,h*.2f,w*.53f,h*.7f,p)
        for(i in 0..8){val x=(i*w/8f);p.color=if(i%2==0)Color.rgb(29,89,61)else Color.rgb(38,112,70);c.drawCircle(x,h*.55f,dpScale(w)*.16f,p);c.drawRect(x-dpScale(w)*.16f,h*.55f,x+dpScale(w)*.16f,h,p)}
        p.color=Color.rgb(36,84,51);c.drawRect(0f,h*.83f,w,h,p)
        p.color=Color.argb(80,255,255,255);for(i in 0..5){val x=i*w/5f;val y=h*.08f+(i%2)*h*.08f;c.drawCircle(x,y,dpScale(w)*.05f,p)}
    }
    private fun dpScale(w:Float)=max(12f,w/34f)
    override fun setAlpha(a:Int){p.alpha=a}
    override fun setColorFilter(f:android.graphics.ColorFilter?){p.colorFilter=f}
    override fun getOpacity():Int=android.graphics.PixelFormat.TRANSLUCENT
}\n\nclass MainActivity : Activity() {
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
                game.overlayOn = true
                game.save()
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
        if (::game.isInitialized) {
            game.invalidate()
            if (game.overlayOn && Settings.canDrawOverlays(this)) {
                startDinoOverlay()
            }
        }
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
        paint.alpha = 255
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
    private fun clean(){cleanliness=min(100,cleanliness+28);happiness=min(100,happiness+5);DinoLife.onInteraction(prefs,"clean");addXp(6)}
    private fun rest(){energy=min(100,energy+30);hunger=max(0,hunger-3);DinoLife.onInteraction(prefs,"rest");addXp(4)}
    private fun pet(){happiness=min(100,happiness+12);bond=min(100,bond+5);DinoLife.onInteraction(prefs,"pet");addXp(5)}
    private fun dash(){happiness=min(100,happiness+8);energy=max(0,energy-4);coins+=2;DinoLife.onInteraction(prefs,"play");addXp(15);Toast.makeText(ctx,"Dino Dash complete! +15 XP",Toast.LENGTH_SHORT).show()}
    private fun ball(){if(toys<=0){Toast.makeText(ctx,"Buy a toy in the shop.",Toast.LENGTH_SHORT).show();return};happiness=min(100,happiness+18);energy=max(0,energy-8);bond=min(100,bond+8);coins+=4;DinoLife.onInteraction(prefs,"play");addXp(20);Toast.makeText(ctx,"Great game! +20 XP",Toast.LENGTH_SHORT).show()}
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
    private var params: WindowManager.LayoutParams? = null
    private var wanderDirection = 1
    private var nextWander = 0L

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
        val lp=WindowManager.LayoutParams(220,260,type,WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,PixelFormat.TRANSLUCENT)
        lp.gravity=Gravity.TOP or Gravity.END;lp.x=8;lp.y=170
        params=lp
        try{wm?.addView(view,lp)}catch(_:Exception){}
    }

    private fun wander(){ val p=params?:return; val now=System.currentTimeMillis(); if(now<nextWander)return; nextWander=now+180L
        val hour=java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY)
        val battery=(getSystemService(BATTERY_SERVICE) as? BatteryManager)?.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)?:100
        if((hour>=23||hour<7||battery<15)&&sleepUntil<now)sleepUntil=now+12000L
        if(sleepUntil>now)return
        if(boredUntil<now&&kotlin.random.Random.nextInt(100)<3)boredUntil=now+3000L; val screenW=resources.displayMetrics.widthPixels; val screenH=resources.displayMetrics.heightPixels; val targetW=if(screenW<700)220 else 260; val targetH=if(screenW<700)260 else 300; if(p.width!=targetW||p.height!=targetH){p.width=targetW;p.height=targetH}; val maxX=(screenW-p.width-8).coerceAtLeast(8); p.x=(p.x+wanderDirection*2).coerceIn(8,maxX); p.y=p.y.coerceIn(80,(screenH-p.height-8).coerceAtLeast(80)); if(p.x<=8||p.x>=maxX)wanderDirection=-wanderDirection; try{view?.let{wm?.updateViewLayout(it,p)}}catch(_:Exception){} }

    override fun onDestroy(){try{view?.let{wm?.removeView(it)}}catch(_:Exception){};view=null;super.onDestroy()}
    override fun onBind(intent:Intent?):IBinder?=null
}

class OverlayView(ctx:Context):View(ctx){
    private val prefs=ctx.getSharedPreferences("dino_companion",Context.MODE_PRIVATE)
    private val paint=Paint(Paint.ANTI_ALIAS_FLAG)
    private var tick=0
    private var drift=0f
    private var driftDir=1f
    init{post(object:Runnable{override fun run(){tick++;drift+=driftDir*0.8f;if(drift>18f||drift< -18f)driftDir=-driftDir;service.wander();invalidate();postDelayed(this,90)}})}
    override fun onDraw(c:Canvas){
        val species=prefs.getString("species","trex")?:"trex"
        val stage=prefs.getInt("stage",1)
        var id=resources.getIdentifier(species+"_stage"+stage+"_f"+(tick%3+1),"drawable",context.packageName)
        if(id==0)id=resources.getIdentifier(species+"_stage"+stage,"drawable",context.packageName)
        paint.color=Color.argb(70,0,0,0)
        c.drawOval(35f+drift,190f,155f+drift,212f,paint)
        paint.alpha=255
        if(id!=0){
            val b=BitmapFactory.decodeResource(resources,id)
            c.drawBitmap(b,null,RectF(15f+drift,10f,175f+drift,205f),paint)
            b.recycle()
        }else{
            paint.color=Color.rgb(87,157,91)
            paint.alpha=255
            c.drawCircle(95f+drift,105f,60f,paint)
        }
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
s = re.sub(r'applicationId\s*=\s*"[^"]+"','applicationId = "com.example.dinocompanion.v143"',s)
s = re.sub(r'versionCode\s*=\s*\d+','versionCode = 47',s)
s = re.sub(r'versionName\s*=\s*"[^"]+"','versionName = "1.44"',s)
s = re.sub(r'\s*implementation\("androidx\.appcompat:appcompat:[^"]+"\)','',s)
if 'implementation("androidx.appcompat:appcompat:1.7.0")' not in s:
    s=s.replace('dependencies {', 'dependencies {\n    implementation("androidx.appcompat:appcompat:1.7.0")')
g.write_text(s,encoding="utf-8")
print("Dino Companion v1.42 complete build generated")


# ---------- v1.43 POLISH / RESPONSIVE / OVERLAY PASS ----------
main_path = root / "app/src/main/java/com/example/dinocompanion/MainActivity.kt"
m = main_path.read_text(encoding="utf-8")

# Make the Canvas UI responsive without modifying Android View width/height properties.
start = m.index("class DinoGameView")
head = m[:start]
body = m[start:]
class_open = body.index("{") + 1
body = body[:class_open] + """
    private val uiScale: Float get() = kotlin.math.min(getWidth().toFloat() / 420f, getHeight().toFloat() / 933f)
    private val uiWidth: Float get() = getWidth().toFloat() / uiScale
    private val uiHeight: Float get() = getHeight().toFloat() / uiScale
""" + body[class_open:]

old_draw = '''    override fun onDraw(c: Canvas) {
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
    }'''
new_draw = '''    override fun onDraw(c: Canvas) {
        c.save()
        c.scale(uiScale, uiScale)
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
        c.restore()
    }'''
body = body.replace(old_draw, new_draw)

# Touch coordinates must use the same responsive coordinate system.
body = body.replace('pressX=e.x;pressY=e.y', 'pressX=e.x/uiScale;pressY=e.y/uiScale')
body = body.replace('val dx=e.x-pressX', 'val dx=e.x/uiScale-pressX')
body = body.replace('handleTap(e.x,e.y)', 'handleTap(e.x/uiScale,e.y/uiScale)')

# Home gets quick Inventory/Settings access.
home_old = '''        text(c,"DINO COMPANION",uiWidth/2f,48f,29f,Color.WHITE,true,true)
        text(c,"Your little world, always with you",uiWidth/2f,70f,12f,Color.WHITE,true)'''
home_new = '''        text(c,"DINO COMPANION",uiWidth/2f,48f,29f,Color.WHITE,true,true)
        text(c,"Your little world, always with you",uiWidth/2f,70f,12f,Color.WHITE,true)
        button(c,12f,16f,78f,58f,"INV","",Color.argb(150,35,100,130))
        button(c,342f,16f,408f,58f,"SET","",Color.argb(150,35,100,130))'''
body = body.replace(home_old, home_new)

# Put the Dino into the Care screen so it isn't just a list of bars.
care_old = '''        stat(c,"Bond",bond,325f,Color.rgb(174,101,190))
        button(c,25f,430f,uiWidth/2f-10,505f,"FEED","●",Color.rgb(93,164,92))'''
care_new = '''        stat(c,"Bond",bond,325f,Color.rgb(174,101,190))
        drawDino(c,uiWidth/2f,400f,.68f)
        button(c,25f,455f,uiWidth/2f-10,530f,"FEED","●",Color.rgb(93,164,92))'''
body = body.replace(care_old, care_new)
body = body.replace('button(c,uiWidth/2f+10,430f,uiWidth-25f,505f,"CLEAN"', 'button(c,uiWidth/2f+10,455f,uiWidth-25f,530f,"CLEAN"')
body = body.replace('button(c,25f,525f,uiWidth/2f-10,600f,"REST"', 'button(c,25f,550f,uiWidth/2f-10,625f,"REST"')
body = body.replace('button(c,uiWidth/2f+10,525f,uiWidth-25f,600f,"PET"', 'button(c,uiWidth/2f+10,550f,uiWidth-25f,625f,"PET"')
body = body.replace('text(c,"Food: "+food+"   •   Toys: "+toys,uiWidth/2f,635f', 'text(c,"Food: "+food+"   •   Toys: "+toys,uiWidth/2f,665f')

# Adjust Care touch zones to match.
body = body.replace('y in 425f..515f&&x<uiWidth/2->feed()', 'y in 450f..540f&&x<uiWidth/2->feed()')
body = body.replace('y in 425f..515f->clean()', 'y in 450f..540f->clean()')
body = body.replace('y in 520f..610f&&x<uiWidth/2->rest()', 'y in 545f..635f&&x<uiWidth/2->rest()')
body = body.replace('y in 520f..610f->pet()', 'y in 545f..635f->pet()')

# Bigger, richer Dino rendering.
body = body.replace('190f*scale/bmp.width,190f*scale/bmp.height', '250f*scale/bmp.width,250f*scale/bmp.height')
body = body.replace('paint.color=Color.argb(70,20,50,50)\n        c.drawOval', 'paint.color=Color.argb(70,20,50,50)\n        paint.alpha=255\n        c.drawOval')

# Home navigation for the new quick buttons.
old_home_touch = '''            Page.HOME -> {
                val h=uiHeight.toFloat()
                when{
                    y>h-115 -> page=if(x<uiWidth/2)Page.CARE else Page.PLAY
                    y>h-195 -> page=if(x<uiWidth/2)Page.CHOOSE else Page.SHOP
                    y in 500f..595f -> page=Page.INVENTORY
                }
            }'''
new_home_touch = '''            Page.HOME -> {
                val h=uiHeight.toFloat()
                when{
                    x < 90f && y < 80f -> page=Page.INVENTORY
                    x > uiWidth-90f && y < 80f -> page=Page.SETTINGS
                    y>h-115 -> page=if(x<uiWidth/2)Page.CARE else Page.PLAY
                    y>h-195 -> page=if(x<uiWidth/2)Page.CHOOSE else Page.SHOP
                }
            }'''
body = body.replace(old_home_touch, new_home_touch)

# Version label.
body = body.replace("Dino Companion 1.41", "Dino Companion 1.44")

# Convert every remaining Canvas drawing/touch width/height reference to the 420x933 logical coordinate space.
# getWidth()/getHeight() remain untouched because the regex matches whole words only.
body = re.sub(r"\bwidth\b", "uiWidth", body)
body = re.sub(r"\bheight\b", "uiHeight", body)

m = head + body
main_path.write_text(m, encoding="utf-8")

# Replace the overlay service with a robust draggable floating companion and compact menu.
overlay_path = root / "app/src/main/java/com/example/dinocompanion/DinoOverlayService.kt"
overlay = r'''
package com.example.dinocompanion

import android.app.*
import android.content.*
import android.content.pm.ServiceInfo
import android.graphics.*
import android.os.*
import android.provider.Settings
import android.view.*
import android.widget.Toast
import kotlin.math.abs

class DinoOverlayService : Service() {
    private var wm: WindowManager? = null
    private var view: OverlayView? = null
    private var params: WindowManager.LayoutParams? = null

    override fun onCreate() {
        super.onCreate()
        val id = "dino_companion"
        if (Build.VERSION.SDK_INT >= 26) {
            getSystemService(NotificationManager::class.java).createNotificationChannel(
                NotificationChannel(id, "Dino Companion", NotificationManager.IMPORTANCE_LOW)
            )
        }
        val n = if (Build.VERSION.SDK_INT >= 26)
            Notification.Builder(this, id)
                .setSmallIcon(android.R.drawable.ic_menu_compass)
                .setContentTitle("Dino Companion")
                .setContentText("Your Dino is with you")
                .setOngoing(true).build()
        else Notification.Builder(this)
            .setSmallIcon(android.R.drawable.ic_menu_compass)
            .setContentTitle("Dino Companion")
            .setContentText("Your Dino is with you")
            .setOngoing(true).build()

        if (Build.VERSION.SDK_INT >= 29)
            startForeground(22, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        else startForeground(22, n)

        if (Settings.canDrawOverlays(this)) showOverlay()
    }

    private fun showOverlay() {
        wm = getSystemService(WINDOW_SERVICE) as WindowManager
        view = OverlayView(this)
        val type = if (Build.VERSION.SDK_INT >= 26)
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        else WindowManager.LayoutParams.TYPE_PHONE

        val d = resources.displayMetrics.density
        params = WindowManager.LayoutParams(
            (220 * d).toInt(), (275 * d).toInt(), type,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        )
        params!!.gravity = Gravity.TOP or Gravity.END
        val saved = getSharedPreferences("dino_companion", Context.MODE_PRIVATE)
        val savedX = saved.getInt("overlay_x", (10 * d).toInt())
        val savedY = saved.getInt("overlay_y", (145 * d).toInt())
        val screenW = resources.displayMetrics.widthPixels
        val screenH = resources.displayMetrics.heightPixels
        val maxX = (screenW - params!!.width - 8).coerceAtLeast(8)
        val maxY = (screenH - params!!.height - 8).coerceAtLeast(80)
        params!!.x = savedX.coerceIn(8, maxX)
        params!!.y = savedY.coerceIn(80, maxY)

        try { wm?.addView(view, params) } catch (_: Exception) {}
    }

    fun moveOverlay(dx: Float, dy: Float) {
        val p = params ?: return
        val screenW = resources.displayMetrics.widthPixels
        val screenH = resources.displayMetrics.heightPixels
        val maxX = (screenW - p.width - 8).coerceAtLeast(8)
        val maxY = (screenH - p.height - 8).coerceAtLeast(80)
        p.x = (p.x - dx).coerceIn(8f, maxX.toFloat()).toInt()
        p.y = (p.y + dy).coerceIn(80f, maxY.toFloat()).toInt()
        getSharedPreferences("dino_companion", Context.MODE_PRIVATE).edit()
            .putInt("overlay_x", p.x).putInt("overlay_y", p.y).apply()
        try { view?.let { wm?.updateViewLayout(it, p) } } catch (_: Exception) {}
    }

    fun openMain() {
        startActivity(Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    }

    fun hideOverlay() {
        getSharedPreferences("dino_companion", Context.MODE_PRIVATE).edit().putBoolean("overlay", false).apply()
        stopSelf()
    }

    fun showInfo() {
        Toast.makeText(this, "Dino Companion overlay • drag me to move", Toast.LENGTH_SHORT).show()
    }

    override fun onDestroy() {
        try { view?.let { wm?.removeView(it) } } catch (_: Exception) {}
        view = null
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}

class OverlayView(private val service: DinoOverlayService) : View(service) {
    private val prefs = service.getSharedPreferences("dino_companion", Context.MODE_PRIVATE)
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG)
    private var tick = 0
    private var menu = false
    private var cachedSpecies = ""
    private var cachedStage = 1
    private val frames = ArrayList<Bitmap>()
    private var downX = 0f
    private var downY = 0f
    private var lastX = 0f
    private var lastY = 0f
    private var moved = false

    init {
        post(object : Runnable {
            override fun run() {
                tick++
                invalidate()
                postDelayed(this, 180)
            }
        })
    }

    private fun releaseFrames(){
        frames.forEach{b->try{if(!b.isRecycled)b.recycle()}catch(_:Throwable){}}
        frames.clear()
    }

    private fun loadFrames(species:String,stage:Int){
        releaseFrames()
        cachedSpecies=species
        cachedStage=stage
        for(f in 1..3){
            val id=resources.getIdentifier(
                species+"_stage"+stage+"_f"+f,"drawable",context.packageName
            )
            if(id!=0){
                try{
                    BitmapFactory.decodeResource(resources,id)?.let{
                        it.prepareToDraw()
                        frames.add(it)
                    }
                }catch(_:Throwable){}
            }
        }
        if(frames.isEmpty()){
            val id=resources.getIdentifier(
                species+"_stage"+stage,"drawable",context.packageName
            )
            if(id!=0){
                try{
                    BitmapFactory.decodeResource(resources,id)?.let{
                        it.prepareToDraw()
                        frames.add(it)
                    }
                }catch(_:Throwable){}
            }
        }
    }

    override fun onDraw(c: Canvas) {
        val density = resources.displayMetrics.density
        val w = width.toFloat()
        val h = height.toFloat()
        val species = prefs.getString("species", "trex") ?: "trex"
        DinoLife.init(service)
        DinoLife.tick(prefs)
        val stage = prefs.getInt("stage", 1)
        val mood = DinoLife.mood(prefs)
        if(species!=cachedSpecies || stage!=cachedStage || frames.isEmpty()) loadFrames(species,stage)

        paint.alpha = 255
        paint.color = Color.argb(75, 0, 0, 0)
        c.drawOval(w*.18f, h*.67f, w*.82f, h*.76f, paint)

        val b=frames.getOrNull(if(frames.isEmpty())0 else tick%frames.size)
        if(b!=null && !b.isRecycled){
            val box = RectF(w*.08f, h*.04f, w*.92f, h*.72f)
            c.drawBitmap(b, null, box, paint)
        }

        val bubble = when (mood) { "HUNGRY" -> "Hungry!" "SLEEPY" -> "Zzz..." "DIRTY" -> "Bath?" "SAD" -> "Play?" "CURIOUS" -> "?" else -> "Happy!" }
        paint.color = Color.argb(225,25,70,92)
        c.drawRoundRect(w*.12f,h*.78f,w*.88f,h*.91f,16f*density,16f*density,paint)
        paint.color=Color.WHITE;paint.textAlign=Paint.Align.CENTER;paint.textSize=12f*density;paint.typeface=Typeface.DEFAULT_BOLD
        c.drawText(bubble,w*.50f,h*.86f,paint)
        if (menu) {
            paint.color = Color.argb(235, 25, 70, 92)
            c.drawRoundRect(w*.03f, h*.76f, w*.97f, h*.97f, 18f*density, 18f*density, paint)
            paint.color = Color.WHITE
            paint.textAlign = Paint.Align.CENTER
            paint.textSize = 12f*density
            paint.typeface = Typeface.DEFAULT_BOLD
            c.drawText("MENU", w*.19f, h*.89f, paint)
            c.drawText("HIDE", w*.50f, h*.89f, paint)
            c.drawText("INFO", w*.81f, h*.89f, paint)
        }
    }

    override fun onDetachedFromWindow(){
        releaseFrames()
        super.onDetachedFromWindow()
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
                if (abs(e.rawX - downX) > 8 || abs(e.rawY - downY) > 8) moved = true
                service.moveOverlay(dx, dy)
                lastX = e.rawX
                lastY = e.rawY
                return true
            }
            MotionEvent.ACTION_UP -> {
                if (!moved) {
                    val density = resources.displayMetrics.density
                    val yy = e.y / density
                    if (menu && yy > 0.76f*height/density) {
                        val xx = e.x / width
                        when {
                            xx < .34f -> service.openMain()
                            xx > .66f -> service.showInfo()
                            else -> service.hideOverlay()
                        }
                    } else {
                        DinoLife.onInteraction(prefs,"pet")
                        prefs.edit().putInt("happiness",(prefs.getInt("happiness",100)+5).coerceAtMost(100)).apply()
                        menu = !menu
                        invalidate()
                    }
                }
                return true
            }
        }
        return true
    }
}
'''
overlay_path.write_text(overlay, encoding="utf-8")

print("Dino Companion v1.43 polished build generated")


# ---------- FINAL XML UI REBUILD v1.45 ----------
final_main = r'''
package com.example.dinocompanion

import android.Manifest
import android.app.*
import android.content.*
import android.content.pm.PackageManager
import android.graphics.*
import android.net.Uri
import android.os.*
import android.provider.Settings
import android.view.*
import android.widget.*
import kotlin.math.max
import kotlin.math.min

class MainActivity : Activity() {
    private lateinit var content: FrameLayout
    private lateinit var pageTitle: TextView
    private lateinit var prefs: android.content.SharedPreferences
    private var selectedId = "trex"
    private var dinoName = "Rex"
    private var stage = 1
    private var xp = 32
    private var hunger = 78
    private var happiness = 100
    private var energy = 79
    private var cleanliness = 90
    private var bond = 12
    private var coins = 52
    private var food = 3
    private var toys = 1
    private var gems = 0
    private var overlayOn = false
    private data class Dino(val id:String,val name:String,val accent:Int)
    private val dinos=listOf(
        Dino("trex","T-Rex",Color.rgb(52,112,61)),
        Dino("triceratops","Triceratops",Color.rgb(62,96,128)),
        Dino("pterodactyl","Pterodactyl",Color.rgb(92,59,116)),
        Dino("stegosaurus","Stegosaurus",Color.rgb(151,82,38))
    )
    private val dino get()=dinos.firstOrNull{it.id==selectedId}?:dinos[0]

    override fun onCreate(b:Bundle?){
        super.onCreate(b)
        try {
            prefs = getSharedPreferences("dino_companion", Context.MODE_PRIVATE)
            selectedId = prefs.getString("species","trex") ?: "trex"
            dinoName = prefs.getString("name","Rex") ?: "Rex"
            stage = prefs.getInt("stage",1)
            xp = prefs.getInt("xp",32)
            hunger = prefs.getInt("hunger",78)
            happiness = prefs.getInt("happiness",100)
            energy = prefs.getInt("energy",79)
            cleanliness = prefs.getInt("cleanliness",90)
            bond = prefs.getInt("bond",12)
            coins = prefs.getInt("coins",52)
            food = prefs.getInt("food",3)
            toys = prefs.getInt("toys",1)
            gems = prefs.getInt("gems",0)
            overlayOn = prefs.getBoolean("overlay",false)
            DinoLife.init(this)
            DinoLife.tick(prefs)
            window.statusBarColor=Color.rgb(42,105,150)
            window.navigationBarColor=Color.rgb(19,58,84)
            setContentView(R.layout.activity_main)
            content=findViewById(R.id.content)
            pageTitle=findViewById(R.id.pageTitle)
            findViewById<View>(R.id.root).background = JungleBackdropDrawable()
            pageTitle.background = android.graphics.drawable.GradientDrawable(
                android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM,
                intArrayOf(Color.rgb(105,72,43),Color.rgb(61,43,31))
            ).apply{cornerRadius=dp(18).toFloat();setStroke(dp(2),Color.rgb(157,125,76))}
            val navs=listOf(
                findViewById<Button>(R.id.navHome),
                findViewById<Button>(R.id.navCare),
                findViewById<Button>(R.id.navPlay),
                findViewById<Button>(R.id.navShop),
                findViewById<Button>(R.id.navMore)
            )
            navs.forEach{b->
                b.setTextColor(Color.WHITE)
                b.typeface=Typeface.DEFAULT_BOLD
                b.gravity=Gravity.CENTER
                b.setAllCaps(false)
                b.setTextColor(Color.WHITE)
                b.setPadding(dp(2),dp(2),dp(2),dp(2))
                b.setTextSize(10f)
                b.background=android.graphics.drawable.GradientDrawable().apply{
                    setColor(Color.rgb(49,70,73));cornerRadius=dp(12).toFloat();setStroke(dp(1),Color.rgb(93,116,101))
                }
                b.stateListAnimator=null
                b.elevation=dp(2).toFloat()
            }
            fun styleActiveNav(b:Button){
                b.background=android.graphics.drawable.GradientDrawable().apply{
                    setColor(Color.rgb(73,145,55));cornerRadius=dp(12).toFloat();setStroke(dp(2),Color.rgb(175,239,88))
                }
                b.setTextColor(Color.WHITE);b.elevation=dp(5).toFloat()
            }
            navs.forEach{b->
                b.setTextColor(Color.WHITE)
                b.textSize=11f
                b.minHeight=dp(48);b.minimumHeight=dp(48)
                b.setPadding(dp(3),dp(3),dp(3),dp(3))
                b.background=android.graphics.drawable.GradientDrawable().apply{
                    setColor(0xFFF1FAFD.toInt())
                    cornerRadius=dp(14).toFloat()
                    setStroke(dp(1),0x30609BB0)
                }
                b.stateListAnimator=null
            }
            fun selectNav(index:Int){
                navs.forEachIndexed{i,b->
                    b.background=android.graphics.drawable.GradientDrawable().apply{
                        setColor(if(i==index)Color.rgb(73,145,55) else Color.rgb(49,70,73))
                        cornerRadius=dp(12).toFloat()
                        setStroke(dp(if(i==index)2 else 1),if(i==index)Color.rgb(175,239,88) else Color.rgb(93,116,101))
                    }
                    b.setTextColor(Color.WHITE);b.elevation=if(i==index)dp(5).toFloat() else dp(2).toFloat()
                }
            }
            navs[0].setOnClickListener{selectNav(0);home()}
            navs[1].setOnClickListener{selectNav(1);care()}
            navs[2].setOnClickListener{selectNav(2);play()}
            navs[3].setOnClickListener{selectNav(3);shop()}
            navs[4].setOnClickListener{selectNav(4);settings()}
            selectNav(0)
            try { home() } catch (e:Throwable) {
                showStartupError("HOME",e)
            }
        } catch (e:Throwable) {
            showStartupError("STARTUP",e)
        }
    }

    private fun showStartupError(where:String,e:Throwable){
        android.util.Log.e("DinoCompanion","$where crash",e)
        try {
            val root=LinearLayout(this)
            root.orientation=LinearLayout.VERTICAL
            root.setPadding(24,48,24,24)
            val title=TextView(this)
            title.text="Dino Companion diagnostic"
            title.textSize=22f
            title.setTextColor(Color.rgb(40,90,110))
            root.addView(title)
            val msg=TextView(this)
            msg.text=where+" failed\\n\\n"+e.javaClass.name+"\\n"+(e.message ?: "No message")
            msg.textSize=15f
            msg.setTextColor(Color.DKGRAY)
            root.addView(msg)
            setContentView(root)
        } catch(_:Throwable){}
    }

    override fun onResume(){
        super.onResume()
        // Overlay is never started automatically during app launch/resume.
        // It is started only from the explicit Overlay setting.
    }

    private fun page(title:String):LinearLayout{
        DinoLife.tick(prefs)
        syncLifeFromPrefs()
        pageTitle.text=title+"\n🪙 "+coins+"    💎 "+gems
        pageTitle.textSize=19f
        pageTitle.setTextColor(Color.WHITE)
        pageTitle.gravity=Gravity.CENTER
        pageTitle.setTypeface(null,Typeface.BOLD)
        pageTitle.setShadowLayer(dp(3).toFloat(),0f,dp(2).toFloat(),Color.BLACK)
        pageTitle.background=android.graphics.drawable.GradientDrawable(
            android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM,
            intArrayOf(Color.rgb(105,72,43),Color.rgb(61,43,31))
        ).apply{cornerRadius=dp(18).toFloat();setStroke(dp(2),Color.rgb(157,125,76))}
        return LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(8),dp(8),dp(8),dp(14))
            setBackgroundColor(Color.TRANSPARENT)
        }
    }
    private fun put(p:LinearLayout,v:View,h:Int=-2,weight:Float=0f){
        p.addView(v,LinearLayout.LayoutParams(if(weight>0)0 else -1,h).apply{
            this.weight=weight
            bottomMargin=dp(if(weight>0)5 else 10)
            if(weight>0){marginStart=dp(4);marginEnd=dp(4)}
        })
    }
    private fun text(t:String,size:Float=14f,bold:Boolean=false,color:Int=Color.WHITE)=TextView(this).apply{
        text=t;textSize=size;setTextColor(color);gravity=Gravity.CENTER_VERTICAL
        setTypeface(null,if(bold)Typeface.BOLD else Typeface.NORMAL)
        setShadowLayer(if(bold)dp(2).toFloat() else 0f,0f,dp(1).toFloat(),Color.BLACK)
        setPadding(dp(4),dp(2),dp(4),dp(2))
    }
    private fun button(t:String,color:Int=Color.rgb(73,145,66),action:()->Unit)=Button(this).apply{
        val normal=android.graphics.drawable.GradientDrawable(
            android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM,
            intArrayOf(Color.argb(255,96,177,67),color)
        ).apply{cornerRadius=dp(18).toFloat();setStroke(dp(2),Color.rgb(45,78,39))}
        val pressed=android.graphics.drawable.GradientDrawable(
            android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM,
            intArrayOf(Color.rgb(75,120,55),Color.rgb(45,82,39))
        ).apply{cornerRadius=dp(18).toFloat();setStroke(dp(2),Color.rgb(205,233,124))}
        text=t;textSize=12f;setTextColor(Color.WHITE);isAllCaps=false;gravity=Gravity.CENTER
        minHeight=dp(54);minimumHeight=dp(54);setPadding(dp(8),dp(4),dp(8),dp(4))
        background=android.graphics.drawable.StateListDrawable().apply{
            addState(intArrayOf(android.R.attr.state_pressed),pressed);addState(intArrayOf(),normal)
        }
        elevation=dp(5).toFloat();stateListAnimator=null
        setOnClickListener{performHapticFeedback(android.view.HapticFeedbackConstants.VIRTUAL_KEY);action()}
    }
    private fun card()=LinearLayout(this).apply{
        orientation=LinearLayout.VERTICAL
        setPadding(dp(12),dp(10),dp(12),dp(10))
        background=android.graphics.drawable.GradientDrawable(
            android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM,
            intArrayOf(Color.argb(235,38,58,62),Color.argb(230,18,31,37))
        ).apply{cornerRadius=dp(20).toFloat();setStroke(dp(2),Color.rgb(109,132,118))}
        elevation=dp(6).toFloat()
    }
    private fun bg()=android.graphics.drawable.GradientDrawable().apply{
        setColor(Color.argb(225,37,53,56));cornerRadius=dp(18).toFloat();setStroke(dp(2),Color.rgb(103,125,111))
    }
    private fun stat(name:String,value:Int)=LinearLayout(this).apply{
        orientation=LinearLayout.VERTICAL
        val head=LinearLayout(this@MainActivity).apply{orientation=LinearLayout.HORIZONTAL}
        head.addView(text(name,12f,true,Color.WHITE),LinearLayout.LayoutParams(0,-2,1f))
        head.addView(text(value.coerceIn(0,100).toString()+" / 100",11f,true,Color.rgb(221,239,222)))
        addView(head)
        addView(ProgressBar(this@MainActivity,null,android.R.attr.progressBarStyleHorizontal).apply{
            max=100;progress=value.coerceIn(0,100)
            progressTintList=android.content.res.ColorStateList.valueOf(when(name){
                "Hunger"->Color.rgb(247,181,55);"Happiness"->Color.rgb(92,221,65);"Energy"->Color.rgb(71,167,244)
                "Cleanliness"->Color.rgb(51,201,224);"Health"->Color.rgb(255,92,110);"Bond"->Color.rgb(174,86,245)
                else->Color.rgb(108,205,75)
            })
            progressBackgroundTintList=android.content.res.ColorStateList.valueOf(Color.rgb(24,34,38))
        },LinearLayout.LayoutParams(-1,dp(9)))
    }
    private fun dinoView(h:Int,which:Dino=dino)=DinoView(this,which).apply{
        layoutParams=LinearLayout.LayoutParams(-1,dp(h))
        setBackgroundColor(Color.TRANSPARENT)
    }

    private fun home(){
        val p=page("DINO COMPANION")
        val hero=card()
        put(hero,text(dinoName,24f,true,Color.rgb(255,219,103)))
        put(hero,text(dino.name+"  •  Stage "+stage,13f,true,Color.rgb(222,236,224)))
        put(hero,dinoView(270))
        put(hero,text("A happy dino makes a brighter day! ♥",13f,true,Color.rgb(255,225,142)))
        put(p,hero)
        val stats=card();put(stats,text("DINO STATUS",16f,true,Color.rgb(157,235,94)))
        val health=((happiness+cleanliness)/2).coerceIn(0,100)
        put(stats,stat("Happiness",happiness));put(stats,stat("Hunger",hunger));put(stats,stat("Energy",energy))
        put(stats,stat("Cleanliness",cleanliness));put(stats,stat("Health",health));put(stats,stat("Bond",bond));put(p,stats)
        val evo=card();put(evo,text("EVOLUTION PROGRESS",15f,true,Color.rgb(255,221,101)))
        val need=stage*100;val progress=xp.coerceIn(0,need)
        put(evo,ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal).apply{
            max=need;this.progress=progress;progressTintList=android.content.res.ColorStateList.valueOf(Color.rgb(102,231,58))
            progressBackgroundTintList=android.content.res.ColorStateList.valueOf(Color.rgb(24,31,32))
        },dp(12))
        put(evo,text(if(stage<4)"Next: Stage "+(stage+1)+"   "+xp+" / "+need+" XP" else "MAX EVOLUTION",12f,true,Color.WHITE));put(p,evo)
        put(p,text("YOUR DINOSAURS",16f,true,Color.rgb(157,235,94)))
        val grid=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        for(start in dinos.indices step 2){
            val row=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
            for(i in start until min(start+2,dinos.size)){
                val choice=dinos[i];val mini=card()
                mini.background=android.graphics.drawable.GradientDrawable().apply{
                    setColor(Color.argb(215,28,43,48));cornerRadius=dp(18).toFloat()
                    setStroke(dp(if(choice.id==selectedId)3 else 1),if(choice.id==selectedId)Color.rgb(120,238,70) else Color.rgb(88,112,99))
                }
                put(mini,dinoView(110,choice));put(mini,text((if(choice.id==selectedId)"✓ " else "")+choice.name,13f,true,Color.WHITE))
                mini.setOnClickListener{selectedId=choice.id;save();home()}
                row.addView(mini,LinearLayout.LayoutParams(0,-2,1f).apply{if(i>start)marginStart=dp(4);if(i<start+1)marginEnd=dp(4)})
            }
            put(grid,row)
        }
        put(p,grid)
        val r=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
        put(r,button("🍎  FOOD & CARE",Color.rgb(65,146,72)){care()},-2,1f);put(r,button("🎮  PLAY",Color.rgb(100,82,170)){play()},-2,1f);put(p,r)
        val r2=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
        put(r2,button("🧬  EVOLVE",Color.rgb(91,128,56)){toast("Evolution requirements shown above")},-2,1f);put(r2,button("🛒  SHOP",Color.rgb(161,108,49)){shop()},-2,1f);put(p,r2)
        content.addView(p)
    }

    private fun care(){
        val p=page("FOOD & CARE");val c=card()
        put(c,text("Keep "+dinoName+" happy, healthy and strong!",18f,true,Color.rgb(255,219,103)))
        put(c,dinoView(230));put(c,text("NEEDS",15f,true,Color.rgb(157,235,94)))
        put(c,stat("Hunger",hunger));put(c,stat("Happiness",happiness));put(c,stat("Energy",energy));put(c,stat("Cleanliness",cleanliness))
        val health=((happiness+cleanliness)/2).coerceIn(0,100);put(c,stat("Health",health))
        val r=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
        put(r,button("🍎 FEED  •  "+food,Color.rgb(74,155,67)){feed();care()},-2,1f);put(r,button("🚿 CLEAN",Color.rgb(46,134,168)){clean();care()},-2,1f);put(c,r)
        val r2=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
        put(r2,button("🌙 SLEEP",Color.rgb(71,91,158)){rest();care()},-2,1f);put(r2,button("♥ PET",Color.rgb(153,74,126)){pet();care()},-2,1f);put(c,r2)
        put(c,text("Bond "+bond+"%   •   Food "+food+"   •   Toys "+toys,12f,true,Color.rgb(221,239,222)));put(p,c);content.addView(p)
    }

    private fun choose(){
        val p=page("CHOOSE YOUR DINO");put(p,text("A loyal companion for your journey",14f,true,Color.rgb(255,222,139)))
        dinos.forEach{choice->val c=card();put(c,dinoView(145,choice));put(c,text((if(choice.id==selectedId)"✓ ACTIVE  " else "")+choice.name,17f,true,choice.accent));put(c,text("Happy • Hungry • Energy • Playful",11f,false,Color.rgb(215,230,218)))
            put(c,button(if(choice.id==selectedId)"SELECTED" else "SELECT",Color.rgb(75,161,62)){selectedId=choice.id;save();choose()});put(p,c)}
        content.addView(p)
    }

    private fun play(){
        val p=page("PLAY GAMES");put(p,text("Fun mini-games to keep your Dino happy!",15f,true,Color.rgb(255,222,139)))
        val games=listOf("🫧  BUBBLE POP","🍎  CATCH THE FOOD","🍌  FRUIT TOSS")
        games.forEachIndexed{i,n->val c=card();put(c,text(n,18f,true,if(i==0)Color.rgb(102,199,255)else if(i==1)Color.rgb(255,192,72)else Color.rgb(134,239,74)));put(c,dinoView(150));put(c,text("Tap to play • earn coins, XP and happiness",11f,false,Color.rgb(220,235,221)));put(c,button("PLAY  •  +"+(15+i*5)+" XP",Color.rgb(73,164,60)){happiness=min(100,happiness+8);energy=max(0,energy-4);coins+=2+i;addXp(15+i*5);play()});put(p,c)}
        put(p,text("Higher scores = better rewards!  🪙  🎁  ♥",13f,true,Color.rgb(255,222,139)));content.addView(p)
    }

    private fun shop(){
        val p=page("SHOP");put(p,text("Get food, toys, decorations and more!",15f,true,Color.rgb(255,222,139)))
        put(p,text("🪙 "+coins+"    💎 "+gems,16f,true,Color.WHITE))
        buy(p,"🍎 FOOD PACK","3 meals  •  10 coins",Color.rgb(74,155,67)){if(coins>=10){coins-=10;food+=3;save();shop()}else toast("Not enough coins")}
        buy(p,"⚽ TOY","1 toy  •  18 coins",Color.rgb(91,105,180)){if(coins>=18){coins-=18;toys++;save();shop()}else toast("Not enough coins")}
        buy(p,"💎 GROWTH GEM","1 gem  •  50 coins",Color.rgb(119,75,177)){if(coins>=50){coins-=50;gems++;save();shop()}else toast("Not enough coins")}
        buy(p,"✨ XP BOOST","+50 XP  •  35 coins",Color.rgb(191,129,47)){if(coins>=35){coins-=35;addXp(50);shop()}else toast("Not enough coins")}
        val daily=card();put(daily,text("DAILY REWARD",15f,true,Color.rgb(255,222,139)));put(daily,text("Free coin for today's care session",12f,false,Color.rgb(220,235,221)));put(daily,button("FREE DAILY COIN",Color.rgb(185,125,47)){coins++;save();shop()});put(p,daily);content.addView(p)
    }
    private fun buy(p:LinearLayout,n:String,d:String,color:Int,a:()->Unit){val c=card();put(c,text(n,17f,true,Color.WHITE));put(c,text(d,12f,false,Color.rgb(220,235,221)));put(c,button("BUY",color,a));put(p,c)}

    private fun inventory(){
        val p=page("INVENTORY")
        put(p,text("Items, food, toys, decorations & more!",14f,true,Color.rgb(255,222,139)))
        val items=listOf(
            "🍖 Dino Kibble" to food,
            "🍎 Apple" to (food+2),
            "⚽ Beach Ball" to toys,
            "💎 Growth Crystal" to gems,
            "🦴 Bone Treat" to max(1,food+4),
            "🏆 Special Item" to max(1,gems)
        )
        var start=0
        while(start<items.size){
            val row=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
            val end=(start+2).coerceAtMost(items.size)
            var i=start
            while(i<end){
                val item=items[i]
                val c=card()
                put(c,text(item.first,16f,true,Color.WHITE))
                put(c,text("x"+item.second,13f,true,Color.rgb(157,235,94)))
                put(c,button("USE",Color.rgb(67,136,163)){toast("Item used")},-2)
                row.addView(c,LinearLayout.LayoutParams(0,-2,1f).apply{
                    if(i>start)marginStart=dp(4)
                    if(i<end-1)marginEnd=dp(4)
                })
                i++
            }
            put(p,row)
            start=end
        }
        content.addView(p)
    }

    private fun settings(){
        val p=page("SETTINGS");put(p,text("Dino Companion Settings",20f,true,Color.rgb(255,222,139)))
        val name=card();put(name,text("YOUR DINO",14f,true,Color.rgb(157,235,94)));put(name,text(dinoName,21f,true,Color.WHITE));put(p,name)
        put(p,button("✎  RENAME DINOSAUR",Color.rgb(65,128,172)){rename()})
        val overlay=card();put(overlay,text("FLOATING COMPANION",15f,true,Color.rgb(157,235,94)));put(overlay,text(if(overlayOn)"Your Dino can appear over other apps." else "Overlay is currently off.",12f,false,Color.rgb(220,235,221)));put(overlay,button(if(overlayOn)"OVERLAY: ON" else "OVERLAY: OFF",Color.rgb(73,158,181)){overlaySettings()});put(p,overlay)
        put(p,button("⚠  RESET DINO",Color.rgb(161,73,70)){reset();home()});put(p,text("Dino Companion 1.45",11f,false,Color.rgb(210,225,214)));content.addView(p)
    }
    private fun rename(){
        val e=EditText(this);e.setText(dinoName);e.selectAll()
        AlertDialog.Builder(this).setTitle("Rename your dinosaur").setView(e).setNegativeButton("Cancel",null)
            .setPositiveButton("Save"){_,_->dinoName=e.text.toString().trim().ifEmpty{dinoName}.take(18);save();home()}.show()
    }
    private fun overlaySettings(){
        val permission=Settings.canDrawOverlays(this)
        AlertDialog.Builder(this).setTitle("Overlay Companion")
            .setMessage(if(permission)"Overlay permission is ON." else "Grant Display over other apps permission.")
            .setNegativeButton("Close",null)
            .setPositiveButton(if(permission)"Toggle" else "Open settings"){_,_->
                if(!permission)startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,Uri.parse("package:"+packageName)))
                else{overlayOn=!overlayOn;save();if(overlayOn)startDinoOverlay()else stopDinoOverlay();settings()}
            }.show()
    }
    private fun startDinoOverlay(){
        if(!Settings.canDrawOverlays(this)){
            startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,Uri.parse("package:"+packageName)))
            return
        }
        try{DinoLife.init(this);if(Build.VERSION.SDK_INT>=26)startForegroundService(Intent(this,DinoOverlayService::class.java))else startService(Intent(this,DinoOverlayService::class.java))}catch(_:Exception){overlayOn=false;save()}
    }
    fun stopDinoOverlay(){try{stopService(Intent(this,DinoOverlayService::class.java))}catch(_:Exception){}}
    private fun syncLifeFromPrefs(){hunger=prefs.getInt("hunger",hunger);happiness=prefs.getInt("happiness",happiness);energy=prefs.getInt("energy",energy);cleanliness=prefs.getInt("cleanliness",cleanliness)}
    private fun feed(){if(food<=0){toast("No food. Visit the shop.");return};food--;hunger=min(100,hunger+25);energy=min(100,energy+5);happiness=min(100,happiness+3);DinoLife.onInteraction(prefs,"feed");addXp(8)}
    private fun clean(){cleanliness=min(100,cleanliness+28);happiness=min(100,happiness+5);addXp(6)}
    private fun rest(){energy=min(100,energy+30);hunger=max(0,hunger-3);addXp(4)}
    private fun pet(){happiness=min(100,happiness+12);bond=min(100,bond+5);addXp(5)}
    private fun addXp(n:Int){xp+=n;while(stage<4&&xp>=stage*100){xp-=stage*100;stage++;coins+=25;happiness=min(100,happiness+10);bond=min(100,bond+5);toast("Dino evolved to Stage "+stage+"!")} ; save()}
    private fun reset(){selectedId="trex";dinoName="Rex";stage=1;xp=32;hunger=78;happiness=100;energy=79;cleanliness=90;bond=12;coins=52;food=3;toys=1;gems=0;overlayOn=false;save();stopDinoOverlay()}
    private fun save(){prefs.edit().putString("species",selectedId).putString("name",dinoName).putInt("stage",stage).putInt("xp",xp).putInt("hunger",hunger).putInt("happiness",happiness).putInt("energy",energy).putInt("cleanliness",cleanliness).putInt("bond",bond).putInt("coins",coins).putInt("food",food).putInt("toys",toys).putInt("gems",gems).putBoolean("overlay",overlayOn).apply()}
    private fun toast(s:String)=Toast.makeText(this,s,Toast.LENGTH_SHORT).show()
    private fun dp(n:Int)=(n*resources.displayMetrics.density).toInt()

    private inner class DinoView(c:Context, private val displayDino:Dino):View(c){
        private val paint=Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG)
        private var frame=0
        private var idlePhase=0f
        private val frames=ArrayList<Bitmap>()
        private val handler=Handler(Looper.getMainLooper())
        private val animator=object:Runnable{
            override fun run(){
                if(frames.size>1){frame=(frame+1)%frames.size}
                idlePhase += 0.16f
                translationY=kotlin.math.sin(idlePhase.toDouble()).toFloat()*3f
                rotation=kotlin.math.sin(idlePhase.toDouble()*0.55).toFloat()*1.2f
                scaleX=1f+kotlin.math.sin(idlePhase.toDouble()*0.8).toFloat()*0.012f
                scaleY=1f-kotlin.math.sin(idlePhase.toDouble()*0.8).toFloat()*0.008f
                invalidate()
                handler.postDelayed(this,90)
            }
        }
        init{
            loadFrames()
            isFocusable=false
        }
        private fun loadFrames(){
            releaseFrames()
            for(f in 1..3){
                val name=displayDino.id+"_stage"+stage+"_f"+f
                val id=resources.getIdentifier(name,"drawable",packageName)
                if(id!=0){
                    try{
                        BitmapFactory.decodeResource(resources,id)?.let{
                            it.prepareToDraw()
                            frames.add(it)
                        }
                    }catch(_:Throwable){}
                }
            }
            if(frames.isEmpty()){
                val id=resources.getIdentifier(displayDino.id+"_stage"+stage,"drawable",packageName)
                if(id!=0){
                    try{
                        BitmapFactory.decodeResource(resources,id)?.let{
                            it.prepareToDraw()
                            frames.add(it)
                        }
                    }catch(_:Throwable){}
                }
            }
        }
        private fun releaseFrames(){
            frames.forEach{b->
                try{if(!b.isRecycled)b.recycle()}catch(_:Throwable){}
            }
            frames.clear()
        }
        override fun onAttachedToWindow(){
            super.onAttachedToWindow()
            handler.removeCallbacks(animator)
            handler.postDelayed(animator,180)
        }
        override fun onDetachedFromWindow(){
            handler.removeCallbacks(animator)
            releaseFrames()
            super.onDetachedFromWindow()
        }
        override fun onDraw(c:Canvas){
            val b=frames.getOrNull(frame)
            if(b!=null && !b.isRecycled){
                val scale=min(width.toFloat()/b.width,height.toFloat()/b.height)*.90f
                val w=b.width*scale
                val h=b.height*scale
                val left=(width-w)/2f
                val top=(height-h)/2f
                c.drawBitmap(b,null,RectF(left,top,left+w,top+h),paint)
                return
            }
            val cx=width/2f
            val cy=height/2f
            val s=min(width,height).coerceAtLeast(1)/260f
            paint.color=displayDino.accent
            c.drawOval(cx-72f*s,cy-62f*s,cx+72f*s,cy+76f*s,paint)
            c.drawCircle(cx-48f*s,cy-82f*s,24f*s,paint)
            c.drawCircle(cx+48f*s,cy-82f*s,24f*s,paint)
            paint.color=Color.WHITE
            c.drawCircle(cx-25f*s,cy-12f*s,14f*s,paint)
            c.drawCircle(cx+25f*s,cy-12f*s,14f*s,paint)
            paint.color=Color.DKGRAY
            c.drawCircle(cx-25f*s,cy-12f*s,6f*s,paint)
            c.drawCircle(cx+25f*s,cy-12f*s,6f*s,paint)
            paint.color=Color.argb(55,0,0,0)
            c.drawOval(cx-78f*s,cy+68f*s,cx+78f*s,cy+88f*s,paint)
        }
    }
}
'''
# Ensure the final XML-generated Activity keeps its jungle backdrop class.
jungle = r'''
private class JungleBackdropDrawable : android.graphics.drawable.Drawable() {
    private val p=Paint(Paint.ANTI_ALIAS_FLAG)
    override fun draw(c:Canvas){
        val w=bounds.width().toFloat()
        val h=bounds.height().toFloat()
        p.shader=LinearGradient(0f,0f,0f,h,Color.rgb(37,139,178),Color.rgb(18,78,57),Shader.TileMode.CLAMP)
        c.drawRect(0f,0f,w,h,p)
        p.shader=null
        p.color=Color.rgb(35,96,67)
        val path=Path()
        path.moveTo(0f,h*.35f);path.lineTo(w*.18f,h*.20f);path.lineTo(w*.34f,h*.30f)
        path.lineTo(w*.52f,h*.17f);path.lineTo(w*.72f,h*.28f);path.lineTo(w*.90f,h*.16f)
        path.lineTo(w,h*.30f);path.lineTo(w,h*.55f);path.lineTo(0f,h*.55f);path.close()
        c.drawPath(path,p)
        p.color=Color.rgb(77,163,93)
        c.drawRect(w*.47f,h*.18f,w*.54f,h*.70f,p)
        p.color=Color.argb(110,215,248,255)
        c.drawRect(w*.485f,h*.18f,w*.53f,h*.70f,p)
        for(i in 0..8){
            val x=i*w/8f
            p.color=if(i%2==0)Color.rgb(24,82,55) else Color.rgb(37,111,67)
            c.drawCircle(x,h*.56f,w/28f,p)
            c.drawRect(x-w/28f,h*.56f,x+w/28f,h,p)
        }
        p.color=Color.rgb(31,76,48);c.drawRect(0f,h*.84f,w,h,p)
        p.color=Color.argb(65,255,255,255)
        for(i in 0..5)c.drawCircle(i*w/5f,h*.10f+(i%2)*h*.07f,w/70f,p)
    }
    override fun setAlpha(a:Int){p.alpha=a}
    override fun setColorFilter(f:android.graphics.ColorFilter?){p.colorFilter=f}
    override fun getOpacity():Int=android.graphics.PixelFormat.TRANSLUCENT
}
'''
final_main = final_main.replace("class MainActivity : Activity() {", jungle + "\nclass MainActivity : Activity() {", 1)

layout_dir = root / "app/src/main/res/layout"
layout_dir.mkdir(parents=True, exist_ok=True)
(layout_dir / "activity_main.xml").write_text(r'''<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/root" android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:background="#00000000" android:padding="4dp">
    <TextView android:id="@+id/pageTitle" android:layout_width="match_parent" android:layout_height="78dp"
        android:padding="8dp" android:text="DINO COMPANION" android:textSize="19sp" android:textStyle="bold"
        android:textColor="#FFFFFF" android:gravity="center"/>
    <ScrollView android:layout_width="match_parent" android:layout_height="0dp" android:layout_weight="1"
        android:fillViewport="true" android:background="#00000000" android:overScrollMode="never">
        <FrameLayout android:id="@+id/content" android:layout_width="match_parent" android:layout_height="wrap_content"/>
    </ScrollView>
    <LinearLayout android:layout_width="match_parent" android:layout_height="72dp" android:orientation="horizontal"
        android:padding="3dp" android:background="#D9152427">
        <Button android:id="@+id/navHome" android:layout_width="0dp" android:layout_height="match_parent" android:layout_weight="1" android:text="⌂\nHOME" android:textSize="10sp"/>
        <Button android:id="@+id/navCare" android:layout_width="0dp" android:layout_height="match_parent" android:layout_weight="1" android:text="♥\nCARE" android:textSize="10sp"/>
        <Button android:id="@+id/navPlay" android:layout_width="0dp" android:layout_height="match_parent" android:layout_weight="1" android:text="🎮\nPLAY" android:textSize="10sp"/>
        <Button android:id="@+id/navShop" android:layout_width="0dp" android:layout_height="match_parent" android:layout_weight="1" android:text="🛒\nSHOP" android:textSize="10sp"/>
        <Button android:id="@+id/navMore" android:layout_width="0dp" android:layout_height="match_parent" android:layout_weight="1" android:text="•••\nMORE" android:textSize="10sp"/>
    </LinearLayout>
</LinearLayout>''',encoding="utf-8")

life_path = root / "app/src/main/java/com/example/dinocompanion/DinoLife.kt"
life = r'''
package com.example.dinocompanion

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import kotlin.math.sqrt

import android.os.BatteryManager
import java.util.Calendar
import kotlin.math.max
import kotlin.math.min

object DinoLife {
    private const val LAST_TICK = "life_last_tick"
    private const val MOOD = "life_mood"
    private const val PLAYFUL = "personality_playful"
    private const val AFFECTION = "personality_affection"
    private const val BRAVE = "personality_brave"
    private var appContext: Context? = null

    fun init(context: Context) { appContext = context.applicationContext }

    fun tick(prefs: android.content.SharedPreferences) {
        val now = System.currentTimeMillis()
        val last = prefs.getLong(LAST_TICK, now)
        val elapsed = ((now - last) / 60000L).coerceIn(0L, 24L * 60L)
        if (elapsed <= 0L) {
            prefs.edit().putLong(LAST_TICK, now).apply()
            return
        }
        var hunger = prefs.getInt("hunger", 78)
        var happiness = prefs.getInt("happiness", 100)
        var energy = prefs.getInt("energy", 79)
        var cleanliness = prefs.getInt("cleanliness", 90)
        hunger = max(0, hunger - (elapsed / 30L).toInt())
        happiness = max(0, happiness - (elapsed / 45L).toInt())
        cleanliness = max(0, cleanliness - (elapsed / 90L).toInt())
        energy = if (hour() >= 23 || hour() < 7) min(100, energy + (elapsed / 18L).toInt()) else max(0, energy - (elapsed / 60L).toInt())
        val mood = when {
            hunger < 25 -> "HUNGRY"
            energy < 20 -> "SLEEPY"
            cleanliness < 25 -> "DIRTY"
            happiness < 30 -> "SAD"
            battery() < 15 -> "SLEEPY"
            hour() >= 23 || hour() < 6 -> "SLEEPY"
            happiness > 85 -> "HAPPY"
            else -> "CURIOUS"
        }
        prefs.edit().putInt("hunger",hunger).putInt("happiness",happiness).putInt("energy",energy)
            .putInt("cleanliness",cleanliness).putString(MOOD,mood).putLong(LAST_TICK,now).apply()
    }

    fun mood(prefs: android.content.SharedPreferences): String = prefs.getString(MOOD,"HAPPY") ?: "HAPPY"

    fun onInteraction(prefs: android.content.SharedPreferences, kind: String) {
        val key=when(kind){"play"->PLAYFUL;"pet"->AFFECTION;else->BRAVE}
        prefs.edit().putInt(key,min(100,prefs.getInt(key,50)+2)).putLong(LAST_TICK,System.currentTimeMillis()).apply()
    }

    private fun hour()=Calendar.getInstance().get(Calendar.HOUR_OF_DAY)

    private fun battery():Int {
        return try {
            val bm=appContext?.getSystemService(Context.BATTERY_SERVICE) as? BatteryManager ?: return 100
            bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY).coerceIn(0,100)
        } catch(_:Throwable){100}
    }
}
'''
life_path.write_text(life,encoding="utf-8")

main_path = root / "app/src/main/java/com/example/dinocompanion/MainActivity.kt"
main_path.write_text(final_main,encoding="utf-8")

manifest_path = root / "app/src/main/AndroidManifest.xml"
if manifest_path.exists():
    manifest = manifest_path.read_text(encoding="utf-8")
    if "FOREGROUND_SERVICE_SPECIAL_USE" not in manifest:
        manifest = manifest.replace("</manifest>", '    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE"/>\\n</manifest>')
    if 'PROPERTY_SPECIAL_USE_FGS_SUBTYPE' not in manifest and 'android:name=".DinoOverlayService"' in manifest:
        manifest = manifest.replace("</service>", '        <property android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE" android:value="user-enabled floating virtual companion overlay"/>\\n        </service>', 1)
    manifest_path.write_text(manifest,encoding="utf-8")

g=root/"app/build.gradle.kts";gs=g.read_text(encoding="utf-8")
gs=re.sub(r'applicationId\s*=\s*"[^"]+"','applicationId = "com.example.dinocompanion.v145"',gs)
gs=re.sub(r'versionCode\s*=\s*\d+','versionCode = 48',gs)
gs=re.sub(r'versionName\s*=\s*"[^"]+"','versionName = "1.45"',gs)
g.write_text(gs,encoding="utf-8")
print("Dino Companion v1.45 native XML UI generated")
