package com.example.dinocompanion

import android.content.Context
import android.graphics.*
import android.view.MotionEvent
import android.view.View
import kotlin.math.sin

class DinoGameView(
    context: Context,
    private val state: DinoState,
    private val onOverlay: () -> Unit,
    private val onRename: () -> Unit
) : View(context) {
    private enum class Page { HOME, CHOOSE, CARE, PLAY, SHOP, INVENTORY, SETTINGS }
    private var page = Page.HOME
    private var selected = index(state.dinoType)
    private var frame = 0
    private var reaction = ""
    private var reactionUntil = 0L
    private val W = 400f
    private val H get() = if (width > 0) height * W / width else 800f
    private val bg = BitmapFactory.decodeResource(resources, R.drawable.home_reference_dynamic)
    private val p = Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG)
    private val t = Paint(Paint.ANTI_ALIAS_FLAG)
    private val c = Paint(Paint.ANTI_ALIAS_FLAG)
    private val species = arrayOf("T-Rex","Triceratops","Pterodactyl","Stegosaurus")
    private val colors = intArrayOf(Color.rgb(55,176,255),Color.rgb(112,76,235),Color.rgb(255,166,48),Color.rgb(54,198,117))

    init {
        setLayerType(LAYER_TYPE_SOFTWARE,null)
        post(object:Runnable{override fun run(){frame=(frame+1)%3;invalidate();postDelayed(this,420)}})
    }

    override fun onDraw(x:Canvas){
        super.onDraw(x)
        val s=width/W
        x.save();x.scale(s,s)
        p.shader=LinearGradient(0f,0f,0f,H,Color.rgb(6,38,72),Color.rgb(7,15,30),Shader.TileMode.CLAMP)
        x.drawRect(0f,0f,W,H,p);p.shader=null
        if(page==Page.HOME)x.drawBitmap(bg,Rect(20,10,bg.width-20,205),RectF(18f,20f,W-18f,205f),p)
        when(page){Page.HOME->home(x);Page.CHOOSE->choose(x);Page.CARE->care(x);Page.PLAY->play(x);Page.SHOP->shop(x);Page.INVENTORY->inventory(x);Page.SETTINGS->settings(x)}
        x.restore()
    }

    private fun header(x:Canvas,s:String){
        box(x,18f,18f,72f,65f,"‹",colors[0],30f)
        t.typeface=Typeface.DEFAULT_BOLD;t.textSize=22f;t.color=Color.WHITE;t.textAlign=Paint.Align.CENTER
        x.drawText(s,W/2,49f,t);t.textAlign=Paint.Align.LEFT
    }

    private fun home(x:Canvas){
        pill(x,20f,220f,205f,265f,"${state.name} • Lv ${state.level}")
        stat(x,"HAPPINESS",state.happiness,225f,220f);stat(x,"HUNGER",state.hunger,225f,258f);stat(x,"ENERGY",state.energy,225f,296f)
        dino(x,W/2,450f,1.55f,selected)
        if(reactionUntil>System.currentTimeMillis())pill(x,108f,330f,292f,372f,reaction)
        t.textSize=12f;t.typeface=Typeface.DEFAULT_BOLD;t.color=Color.WHITE;t.textAlign=Paint.Align.CENTER;x.drawText("Tap your dino to interact",W/2,570f,t);t.textAlign=Paint.Align.LEFT
        val y=H-205f
        box(x,12f,y,126f,y+68f,"FOOD",Color.rgb(225,75,79),12f);box(x,137f,y,263f,y+68f,"PLAY",colors[0],12f);box(x,274f,y,388f,y+68f,"PICK DINO",colors[3],10f)
        box(x,12f,y+78f,126f,y+146f,"OVERLAY",colors[1],11f);box(x,137f,y+78f,263f,y+146f,"SHOP",Color.rgb(255,166,35),12f);box(x,274f,y+78f,388f,y+146f,"INVENTORY",Color.rgb(35,85,120),10f)
        pill(x,55f,y-52f,345f,y-10f,"EVOLUTION  ${state.evolutionProgress()}%")
        p.color=Color.rgb(50,220,105);x.drawRoundRect(68f,y-24f,68f+264f*state.evolutionProgress()/100f,y-17f,4f,4f,p)
    }

    private fun choose(x:Canvas){
        header(x,"CHOOSE YOUR DINOSAUR");pill(x,28f,86f,372f,132f,"${species[selected]} • Stage ${state.stage+1}/4")
        dino(x,W/2,285f,1.85f,selected)
        box(x,15f,250f,75f,320f,"‹",colors[selected],26f);box(x,325f,250f,385f,320f,"›",colors[selected],26f)
        for(i in 0..3){val l=8f+i*98f;mini(x,l,455f,l+91f,555f,i,i==selected)}
        pill(x,28f,580f,372f,638f,when(selected){0->"Strong • loyal • brave";1->"Armoured • bold • gentle";2->"Fast • curious • airborne";else->"Calm • tough • friendly"})
        box(x,30f,665f,370f,735f,"SELECT ${species[selected].uppercase()}",colors[selected],11f)
    }

    private fun care(x:Canvas){
        header(x,"FOOD & CARE");dino(x,W/2,220f,1f,selected)
        val a=arrayOf("FEED","PET","CLEAN","WATER","SLEEP","HEAL")
        for(i in 0..5){val l=15f+(i%2)*195f;val y=315f+(i/2)*92f;card(x,l,y,l+180f,y+78f,a[i],colors[i%4])}
        stat(x,"HAPPINESS",state.happiness,20f,H-105f);stat(x,"HEALTH",state.health,205f,H-105f)
    }

    private fun play(x:Canvas){
        header(x,"PLAY TOGETHER");dino(x,W/2,220f,1.05f,selected)
        val a=arrayOf("BALL","RUN","DANCE","TRICKS")
        for(i in 0..3){val l=15f+(i%2)*195f;val y=320f+(i/2)*105f;card(x,l,y,l+180f,y+90f,a[i],colors[(i+1)%4])}
        pill(x,55f,H-92f,345f,H-42f,"Play earns coins + bond")
    }

    private fun shop(x:Canvas){
        header(x,"SHOP");pill(x,24f,88f,376f,130f,"COINS  ${state.coins}")
        val a=arrayOf("DINO MEAL","MEAT PACK","PLAY TOKEN","EVOLUTION FOOD","BERRY MIX","HEALTH BOOST")
        for(i in 0..5){val l=15f+(i%2)*195f;val y=155f+(i/2)*100f;card(x,l,y,l+180f,y+86f,a[i],colors[i%4])}
    }

    private fun inventory(x:Canvas){
        header(x,"INVENTORY");pill(x,20f,88f,380f,132f,"${state.name} • ${state.dinoType} • Stage ${state.stage+1}")
        val a=arrayOf("EVOLUTION FOOD x${state.evolutionFood}","COINS ${state.coins}","HAPPINESS ${state.happiness.toInt()}%","BOND ${state.bond.toInt()}%","HEALTH ${state.health.toInt()}%","CLEAN ${state.cleanliness.toInt()}%")
        for(i in 0..5){val l=15f+(i%2)*195f;val y=160f+(i/2)*100f;card(x,l,y,l+180f,y+86f,a[i],colors[i%4])}
        box(x,28f,H-90f,372f,H-30f,"SETTINGS",Color.rgb(35,85,120),12f)
    }

    private fun settings(x:Canvas){
        header(x,"SETTINGS")
        val a=arrayOf("OVERLAY","DINO PREFERENCES","NOTIFICATIONS","INTERACTIONS","APPEARANCE","AUDIO & VOICE","ADVANCED")
        for(i in a.indices){val y=90f+i*72f;pill(x,18f,y,382f,y+58f,a[i]);t.textSize=10f;t.color=Color.rgb(175,205,225);x.drawText(when(i){0->"Show, hide and move";1->"Name, species, stage";2->"Battery and charging";3->"Tap, shake, keyboard";4->"Themes and effects";5->"Sounds and reactions";else->"Performance and data"},32f,y+39f,t)}
        box(x,28f,H-82f,372f,H-28f,"OVERLAY SETTINGS",colors[0],12f)
    }

    private fun stat(x:Canvas,label:String,v:Float,l:Float,y:Float){
        pill(x,l,y,l+163f,y+30f,"$label ${v.toInt()}%");p.color=if(v>=65)Color.rgb(52,215,105)else Color.rgb(255,170,35);x.drawRoundRect(l+8f,y+21f,l+8f+135f*v/100f,y+25f,3f,3f,p)
    }

    private fun dino(x:Canvas,cx:Float,cy:Float,scale:Float,idx:Int){
        val b=BitmapFactory.decodeResource(resources,frames(idx,state.stage+1)[frame])?:return
        val bob=sin(System.currentTimeMillis()/350.0).toFloat()*5f;val tilt=sin(System.currentTimeMillis()/520.0).toFloat()*2f
        val w=180f*scale;val h=180f*scale
        p.setShadowLayer(14f,0f,10f,Color.argb(120,0,0,0));x.drawOval(cx-w*.3f,cy+h*.38f+bob,cx+w*.3f,cy+h*.46f+bob,p);p.clearShadowLayer()
        x.save();x.rotate(tilt,cx,cy+bob);x.drawBitmap(b,null,RectF(cx-w/2,cy-h/2+bob,cx+w/2,cy+h/2+bob),p);x.restore()
    }

    private fun mini(x:Canvas,l:Float,t0:Float,r:Float,b:Float,i:Int,active:Boolean){
        c.color=if(active)Color.argb(235,18,86,135)else Color.argb(210,8,30,50);x.drawRoundRect(l,t0,r,b,16f,16f,c);dino(x,(l+r)/2,t0+42f,.48f,i)
        t.color=Color.WHITE;t.textSize=8f;t.typeface=Typeface.DEFAULT_BOLD;t.textAlign=Paint.Align.CENTER;x.drawText(species[i],(l+r)/2,b-10f,t);t.textAlign=Paint.Align.LEFT
    }

    private fun card(x:Canvas,l:Float,y:Float,r:Float,b:Float,s:String,color:Int){
        c.color=Color.argb(230,9,36,60);x.drawRoundRect(l,y,r,b,18f,18f,c);p.color=color;x.drawCircle(l+35f,y+39f,23f,p);t.color=Color.WHITE;t.textSize=12f;t.typeface=Typeface.DEFAULT_BOLD;x.drawText(s,l+68f,y+43f,t)
    }

    private fun pill(x:Canvas,l:Float,y:Float,r:Float,b:Float,s:String){
        c.color=Color.argb(215,8,31,51);x.drawRoundRect(l,y,r,b,16f,16f,c);t.color=Color.WHITE;t.textSize=11f;t.typeface=Typeface.DEFAULT_BOLD;x.drawText(s.take(38),l+12f,y+(b-y)*.65f,t)
    }

    private fun box(x:Canvas,l:Float,y:Float,r:Float,b:Float,s:String,color:Int,size:Float){
        c.color=Color.argb(245,Color.red(color),Color.green(color),Color.blue(color));x.drawRoundRect(l,y,r,b,20f,20f,c);p.color=Color.argb(70,255,255,255);x.drawRoundRect(l+3,y+3,r-3,y+16,14f,14f,p)
        t.color=Color.WHITE;t.textSize=size;t.typeface=Typeface.DEFAULT_BOLD;t.textAlign=Paint.Align.CENTER;x.drawText(s,(l+r)/2,(y+b)/2+size*.35f,t);t.textAlign=Paint.Align.LEFT
    }

    private fun react(s:String){reaction=s;reactionUntil=System.currentTimeMillis()+2200;state.currentAction=s}

    override fun onTouchEvent(e:MotionEvent):Boolean{
        if(e.actionMasked!=MotionEvent.ACTION_UP)return true
        val sc=width/W;val x=e.x/sc;val y=e.y/sc
        when(page){
            Page.HOME->when{
                y in H-205f..H-137f&&x<132f->{page=Page.CARE}
                y in H-205f..H-137f&&x<268f->{page=Page.PLAY}
                y in H-205f..H-137f->{page=Page.CHOOSE}
                y in H-127f..H-59f&&x<132f->{onOverlay()}
                y in H-127f..H-59f&&x<268f->{page=Page.SHOP}
                y in H-127f..H-59f->{page=Page.INVENTORY}
                y in 330f..560f->{state.pet();react("${state.name}: Yay!")}
                y in 215f..275f&&x<210f->{onRename()}
            }
            Page.CHOOSE->when{
                y in 245f..330f&&x<85f->{selected=(selected+3)%4}
                y in 245f..330f&&x>315f->{selected=(selected+1)%4}
                y in 445f..560f->{selected=((x-8f)/98f).toInt().coerceIn(0,3)}
                y in 650f..750f->{state.dinoType=species[selected];state.stage=0;state.name=defaultName(species[selected]);page=Page.HOME;react("${state.name} selected!")}
                y<80f->{page=Page.HOME}
            }
            Page.CARE->when{y<80f->page=Page.HOME;y in 315f..600f->{val i=((y-315f)/92f).toInt()*2+if(x<200)0 else 1;when(i){0->{state.feed();react("Yum!")};1->{state.pet();react("Nice!")};2->{state.clean();react("Sparkly!")};3->{state.thirst=(state.thirst+20).coerceAtMost(100f);react("Refreshing!")};4->{state.energy=(state.energy+20).coerceAtMost(100f);react("Sleepy...")};5->{state.health=(state.health+15).coerceAtMost(100f);react("Better!")}}}}
            Page.PLAY->when{y<80f->page=Page.HOME;y in 310f..540f->{state.play();react("That was fun!")}}
            Page.SHOP->when{y<80f->page=Page.HOME}
            Page.INVENTORY->when{y<80f->page=Page.HOME;y>H-100f->page=Page.SETTINGS}
            Page.SETTINGS->when{y<80f->page=Page.HOME;y>H-100f->onOverlay()}
        }
        invalidate();return true
    }

    private fun frames(i:Int,stage:Int):IntArray{
        val s=stage.coerceIn(1,4)
        return when(i){
            0->when(s){1->intArrayOf(R.drawable.trex_stage1_f1,R.drawable.trex_stage1_f2,R.drawable.trex_stage1_f3);2->intArrayOf(R.drawable.trex_stage2_f1,R.drawable.trex_stage2_f2,R.drawable.trex_stage2_f3);3->intArrayOf(R.drawable.trex_stage3_f1,R.drawable.trex_stage3_f2,R.drawable.trex_stage3_f3);else->intArrayOf(R.drawable.trex_stage4_f1,R.drawable.trex_stage4_f2,R.drawable.trex_stage4_f3)}
            1->when(s){1->intArrayOf(R.drawable.triceratops_stage1_f1,R.drawable.triceratops_stage1_f2,R.drawable.triceratops_stage1_f3);2->intArrayOf(R.drawable.triceratops_stage2_f1,R.drawable.triceratops_stage2_f2,R.drawable.triceratops_stage2_f3);3->intArrayOf(R.drawable.triceratops_stage3_f1,R.drawable.triceratops_stage3_f2,R.drawable.triceratops_stage3_f3);else->intArrayOf(R.drawable.triceratops_stage4_f1,R.drawable.triceratops_stage4_f2,R.drawable.triceratops_stage4_f3)}
            2->when(s){1->intArrayOf(R.drawable.pterodactyl_stage1_f1,R.drawable.pterodactyl_stage1_f2,R.drawable.pterodactyl_stage1_f3);2->intArrayOf(R.drawable.pterodactyl_stage2_f1,R.drawable.pterodactyl_stage2_f2,R.drawable.pterodactyl_stage2_f3);3->intArrayOf(R.drawable.pterodactyl_stage3_f1,R.drawable.pterodactyl_stage3_f2,R.drawable.pterodactyl_stage3_f3);else->intArrayOf(R.drawable.pterodactyl_stage4_f1,R.drawable.pterodactyl_stage4_f2,R.drawable.pterodactyl_stage4_f3)}
            else->when(s){1->intArrayOf(R.drawable.stegosaurus_stage1_f1,R.drawable.stegosaurus_stage1_f2,R.drawable.stegosaurus_stage1_f3);2->intArrayOf(R.drawable.stegosaurus_stage2_f1,R.drawable.stegosaurus_stage2_f2,R.drawable.stegosaurus_stage2_f3);3->intArrayOf(R.drawable.stegosaurus_stage3_f1,R.drawable.stegosaurus_stage3_f2,R.drawable.stegosaurus_stage3_f3);else->intArrayOf(R.drawable.stegosaurus_stage4_f1,R.drawable.stegosaurus_stage4_f2,R.drawable.stegosaurus_stage4_f3)}
        }
    }

    private fun index(s:String)=when(s.lowercase()){"t-rex","trex"->0;"triceratops"->1;"pterodactyl"->2;else->3}
    private fun defaultName(s:String)=when(s){"T-Rex"->"Rex";"Triceratops"->"Trixie";"Pterodactyl"->"Sky";else->"Steggy"}
}
