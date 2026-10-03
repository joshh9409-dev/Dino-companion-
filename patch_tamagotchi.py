from pathlib import Path
import re,shutil
r=Path("."); s=r/"app/src/main/java/com/example/dinocompanion"; s.mkdir(parents=True,exist_ok=True)
for p in s.rglob("*.kt"): p.unlink()
MAIN=r'''package com.example.dinocompanion
import android.app.*;import android.content.*;import android.graphics.*;import android.net.Uri;import android.os.*;import android.provider.Settings;import android.view.*;import android.widget.*;import kotlin.math.*

class MainActivity:Activity(){
 lateinit var game:DinoGameView
 override fun onCreate(b:Bundle?){super.onCreate(b);window.statusBarColor=Color.rgb(18,92,71);window.navigationBarColor=Color.rgb(11,55,44);game=DinoGameView(this);setContentView(game)}
 override fun onResume(){super.onResume();if(::game.isInitialized){DinoLife.tick(this);game.invalidate();if(DinoLife.overlay(this)&&Settings.canDrawOverlays(this))startOverlay()}}
 fun overlaySettings(){if(!Settings.canDrawOverlays(this)){startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,Uri.parse("package:"+packageName)));return};val on=DinoLife.overlay(this);DinoLife.setOverlay(this,!on);if(on)stopOverlay()else startOverlay();game.invalidate()}
 private fun startOverlay(){try{val i=Intent(this,DinoOverlayService::class.java);if(Build.VERSION.SDK_INT>=26)startForegroundService(i)else startService(i)}catch(_:Exception){}}
 fun stopOverlay(){try{stopService(Intent(this,DinoOverlayService::class.java))}catch(_:Exception){}}
 fun rename(){val e=EditText(this);e.setText(DinoLife.name(this));AlertDialog.Builder(this).setTitle("Name your Dino").setView(e).setNegativeButton("Cancel",null).setPositiveButton("Save"){_,_->DinoLife.name(this,e.text.toString().trim().ifEmpty{"Rex"}.take(18));game.invalidate()}.show()}
 override fun onBackPressed(){if(::game.isInitialized&&game.screen!=0){game.screen=0;game.invalidate()}else super.onBackPressed()}
}

class DinoGameView(val c:Context):View(c){
 val p=Paint(1);var a=0f;var x=0f;var y=0f;var screen=0
 init{post(object:Runnable{override fun run(){DinoLife.tick(c);a+=.12f;invalidate();postDelayed(this,250)}})}
 override fun onDraw(z:Canvas){jungle(z);when(screen){0->home(z);1->menu(z);2->page(z,"FEED","FEED",0);3->page(z,"LIGHT",if(DinoLife.light(c))"TURN LIGHT OFF" else "TURN LIGHT ON",1);4->page(z,"TOILET / CLEAN","CLEAN",2);5->health(z);6->page(z,"PLAY","PLAY",4);7->page(z,"MEDICINE","MEDICINE",5);8->page(z,"DISCIPLINE","DISCIPLINE",6);9->attention(z);10->settings(z)}}
 fun jungle(z:Canvas){val w=width.toFloat();val h=height.toFloat();p.shader=LinearGradient(0f,0f,0f,h,Color.rgb(55,181,222),Color.rgb(12,91,65),Shader.TileMode.CLAMP);z.drawRect(0f,0f,w,h,p);p.shader=null;p.color=Color.rgb(65,140,80);z.drawOval(-w*.25f,h*.25f,w*.55f,h*.67f,p);z.drawOval(w*.38f,h*.2f,w*1.25f,h*.65f,p);p.color=Color.rgb(35,119,84);z.drawRect(0f,h*.62f,w,h,p);p.color=Color.rgb(42,149,197);z.drawRect(0f,h*.70f,w,h*.87f,p);p.color=Color.rgb(220,190,108);z.drawRect(0f,h*.87f,w,h,p);p.color=Color.argb(150,255,255,255);z.drawOval(w*.08f,h*.1f,w*.35f,h*.17f,p);z.drawOval(w*.65f,h*.08f,w*.93f,h*.15f,p);palm(z,w*.08f,h*.55f,.9f);palm(z,w*.91f,h*.52f,.75f)}
 fun palm(z:Canvas,x:Float,y:Float,s:Float){p.color=Color.rgb(98,67,42);p.strokeWidth=10*s;z.drawLine(x,y,x+12*s,y-110*s,p);p.color=Color.rgb(35,125,62);for(i in 0..5){z.save();z.rotate(-55f+i*22f,x+10*s,y-110*s);z.drawOval(x-65*s,y-120*s,x+15*s,y-100*s,p);z.restore()}}
 fun home(z:Canvas){val w=width.toFloat();val h=height.toFloat();if(DinoLife.dead(c)){dino(z,w/2,h*.53f,1.15f,true);bubble(z,w/2,110f,"Rex has died");btn(z,w*.18f,h*.79f,w*.82f,h*.88f,"TAP TO START AGAIN",Color.rgb(190,76,64));return};txt(z,DinoLife.name(c),w/2,56f,25f,Color.WHITE,true,true);txt(z,DinoLife.stage(c),w/2,82f,13f,Color.WHITE,true,true);dino(z,w/2,h*.52f,1.18f,false);if(DinoLife.att(c)){p.color=Color.WHITE;z.drawCircle(w*.86f,70f,22f,p);txt(z,"!",w*.86f,80f,28f,Color.rgb(198,63,55),true,true)};if(DinoLife.sleep(c))bubble(z,w*.73f,135f,"Z  z  Z")else if(DinoLife.att(c))bubble(z,w*.72f,135f,"Rex needs you");txt(z,"Tap Rex to open care menu",w/2,h*.80f,13f,Color.WHITE,true,true)}
 fun menu(z:Canvas){panel(z,"CARE MENU");val n=listOf("FEED","LIGHT","TOILET","HEALTH","PLAY","MEDICINE","DISCIPLINE","ATTENTION");for(i in n.indices){val col=i%2;val row=i/2;l@{ };val ww=width.toFloat();val l=18f+col*(ww-45f)/2f;val r=l+(ww-45f)/2f;val t=110f+row*105f;btn(z,l,t,r,t+82f,n[i],bc(i))};btn(z,18f,height-100f,width-18f,height-36f,"SETTINGS",Color.rgb(42,105,82))}
 fun page(z:Canvas,t:String,a:String,i:Int){panel(z,t);dino(z,width/2f,235f,.78f,false);txt(z,if(i==1)a else "Keep Rex healthy and happy",width/2f,390f,15f,Color.WHITE,true,true);btn(z,30f,445f,width-30f,530f,a,bc(i));btn(z,30f,555f,width-30f,625f,"BACK",Color.rgb(55,119,91))}
 fun health(z:Canvas){panel(z,"HEALTH");dino(z,width/2f,215f,.68f,false);txt(z,if(DinoLife.sick(c))"REX IS SICK" else "REX IS HEALTHY",width/2f,370f,20f,Color.WHITE,true,true);btn(z,30f,445f,width-30f,525f,"MEDICINE",Color.rgb(177,73,81));btn(z,30f,550f,width-30f,630f,"BACK",Color.rgb(55,119,91))}
 fun attention(z:Canvas){panel(z,"ATTENTION");dino(z,width/2f,220f,.72f,false);txt(z,if(DinoLife.att(c))"REX NEEDS ATTENTION" else "NO ATTENTION NEEDED",width/2f,385f,18f,Color.WHITE,true,true);btn(z,30f,465f,width-30f,550f,"DISCIPLINE",Color.rgb(143,91,65));btn(z,30f,575f,width-30f,650f,"BACK",Color.rgb(55,119,91))}
 fun settings(z:Canvas){panel(z,"SETTINGS");txt(z,"Name: "+DinoLife.name(c),width/2f,150f,17f,Color.WHITE,true,true);txt(z,"Floating Dino: "+if(DinoLife.overlay(c))"ON" else "OFF",width/2f,205f,14f,Color.WHITE,true);btn(z,30f,300f,width-30f,380f,"RENAME",Color.rgb(60,128,172));btn(z,30f,400f,width-30f,480f,"OVERLAY ON / OFF",Color.rgb(80,139,104));btn(z,30f,500f,width-30f,580f,"RESET TO EGG",Color.rgb(181,76,65))}
 fun panel(z:Canvas,t:String){p.color=Color.argb(190,8,60,46);z.drawRect(0f,0f,width.toFloat(),height.toFloat(),p);txt(z,t,width/2f,55f,25f,Color.WHITE,true,true);btn(z,18f,20f,95f,72f,"BACK",Color.rgb(42,105,82))}
 fun bubble(z:Canvas,x:Float,y:Float,s:String){p.color=Color.argb(235,255,255,255);z.drawRoundRect(x-80f,y-30f,x+80f,y+30f,22f,22f,p);txt(z,s,x,y+8f,14f,Color.rgb(35,75,62),true,true)}
 fun btn(z:Canvas,l:Float,t:Float,r:Float,b:Float,s:String,col:Int){p.color=Color.argb(75,0,30,25);z.drawRoundRect(l,t+6,r,b+6,20f,20f,p);p.color=col;z.drawRoundRect(l,t,r,b,20f,20f,p);txt(z,s,(l+r)/2f,t+(b-t)/2f+6f,14f,Color.WHITE,true,true)}
 fun txt(z:Canvas,s:String,x:Float,y:Float,q:Float,col:Int,cen:Boolean=false,b:Boolean=false){p.color=col;p.textSize=q;p.typeface=if(b)Typeface.DEFAULT_BOLD else Typeface.DEFAULT;p.textAlign=if(cen)Paint.Align.CENTER else Paint.Align.LEFT;z.drawText(s,x,y,p)}
 fun bc(i:Int)=arrayOf(Color.rgb(74,150,88),Color.rgb(198,145,54),Color.rgb(55,143,168),Color.rgb(70,121,176),Color.rgb(125,93,171),Color.rgb(177,73,81),Color.rgb(143,91,65),Color.rgb(56,135,106))[abs(i)%8]
 fun dino(z:Canvas,x:Float,y:Float,s:Float,dead:Boolean){val b=if(dead)0f else sin(a.toDouble()).toFloat()*7f*s;val r=Color.rgb(205,63,49);val d=Color.rgb(139,42,37);p.setShadowLayer(18f*s,0f,10f*s,Color.argb(110,0,0,0));p.color=Color.argb(90,0,0,0);z.drawOval(x-78*s,y+78*s,x+78*s,y+100*s,p);p.clearShadowLayer();p.color=r;z.drawOval(x-62*s,y-70*s+b,x+62*s,y+64*s+b,p);z.drawOval(x-48*s,y-112*s+b,x+67*s,y-22*s+b,p);p.color=Color.rgb(255,190,112);z.drawOval(x-18*s,y-5*s+b,x+35*s,y+58*s+b,p);p.color=d;for(i in -2..2)z.drawCircle(x-28*s+i*17*s,y-80*s+b,7*s,p);p.color=Color.WHITE;z.drawCircle(x-20*s,y-86*s+b,14*s,p);z.drawCircle(x+25*s,y-84*s+b,14*s,p);p.color=Color.DKGRAY;z.drawCircle(x-17*s,y-84*s+b,6*s,p);z.drawCircle(x+28*s,y-82*s+b,6*s,p);p.color=r;val t=Path();t.moveTo(x-48*s,y+28*s+b);t.quadTo(x-118*s,y+38*s+b,x-126*s,y-4*s+b);t.quadTo(x-104*s,y+58*s+b,x-42*s,y+53*s+b);t.close();z.drawPath(t,p);p.color=d;z.drawOval(x-48*s,y+46*s+b,x-18*s,y+86*s+b,p);z.drawOval(x+15*s,y+45*s+b,x+45*s,y+86*s+b,p);if(dead){p.color=Color.WHITE;p.strokeWidth=5f*s;z.drawLine(x-31*s,y-95*s+b,x-12*s,y-76*s+b,p);z.drawLine(x-12*s,y-95*s+b,x-31*s,y-76*s+b,p);z.drawLine(x+14*s,y-93*s+b,x+33*s,y-74*s+b,p);z.drawLine(x+33*s,y-93*s+b,x+14*s,y-74*s+b,p)}}
 override fun onTouchEvent(e:MotionEvent):Boolean{if(e.actionMasked==0){x=e.x;y=e.y;return true};if(e.actionMasked==1){if(abs(e.x-x)>50||abs(e.y-y)>50)return true;tap(e.x,e.y);return true};return true}
 fun tap(x:Float,y:Float){if(screen==0){if(DinoLife.dead(c)){DinoLife.reset(c);invalidate();return};screen=1;invalidate();return};if(screen==1){if(y<90){screen=0}else if(y>height-110){screen=10}else{val col=if(x<width.toFloat()/2f)0 else 1;val row=((y-105)/105).toInt();if(row in 0..3)screen=listOf(2,3,4,5,6,7,8,9)[row*2+col]};invalidate();return};if(y<90){screen=1;invalidate();return};when(screen){2->if(y in 420f..550f)DinoLife.feed(c);3->if(y in 430f..550f)DinoLife.toggleLight(c);4->if(y in 420f..550f)DinoLife.clean(c);5->if(y in 420f..550f)screen=7;6->if(y in 420f..550f)DinoLife.play(c);7->if(y in 420f..550f)DinoLife.medicine(c);8,9->if(y in 420f..570f)DinoLife.discipline(c);10->when{y in 300f..400f->(c as MainActivity).rename();y in 400f..480f->(c as MainActivity).overlaySettings();y in 500f..580f->{DinoLife.reset(c);(c as MainActivity).stopOverlay()}}};invalidate()}
}'''
LIFE=r'''package com.example.dinocompanion
import android.content.Context
import java.util.Calendar
import kotlin.math.*
object DinoLife{
 const val P="dino_tamagotchi";const val M=60000L;const val D=1440L*M
 fun q(c:Context)=c.getSharedPreferences(P,0)
 fun init(c:Context){val q=q(c);if(!q.contains("created"))q.edit().putLong("created",System.currentTimeMillis()).putLong("last",System.currentTimeMillis()).putInt("stage",0).putInt("hunger",100).putInt("happy",100).putInt("health",100).putInt("clean",100).putInt("poop",0).putBoolean("sick",false).putBoolean("light",true).putBoolean("attention",false).putBoolean("dead",false).putBoolean("overlay",false).putString("name","Rex").apply()}
 fun tick(c:Context){init(c);val q=q(c);if(q.getBoolean("dead",false))return;val now=System.currentTimeMillis();val last=q.getLong("last",now);val m=((now-last)/M).coerceAtLeast(0);if(m<1)return;var h=max(0,q.getInt("hunger",100)-m.toInt());var f=max(0,q.getInt("happy",100)-(m/3).toInt());var hp=q.getInt("health",100);var cl=max(0,q.getInt("clean",100)-(m/4).toInt());var poop=q.getInt("poop",0);var sick=q.getBoolean("sick",false);if(m>=60)poop=min(3,poop+max(1,(m/90).toInt()));if(h<20||cl<20||poop>=3)sick=true;if(sick)hp=max(0,hp-(m/20).toInt());val age=now-q.getLong("created",now);val st=when{age<30*M->0;age<3*D->1;age<7*D->2;age<14*D->3;else->4};val att=h<35||f<30||cl<25||sick||poop>0;val dead=(h<10&&m>=120)||hp<=0;q.edit().putLong("last",now).putInt("hunger",h).putInt("happy",f).putInt("health",hp).putInt("clean",cl).putInt("poop",poop).putBoolean("sick",sick).putInt("stage",st).putBoolean("attention",att).putBoolean("dead",dead).apply()}
 fun stage(c:Context)=arrayOf("EGG","BABY","CHILD","TEEN","ADULT")[q(c).getInt("stage",0).coerceIn(0,4)]
 fun name(c:Context)=q(c).getString("name","Rex")?:"Rex";fun name(c:Context,n:String){q(c).edit().putString("name",n).apply()}
 fun dead(c:Context)=q(c).getBoolean("dead",false);fun att(c:Context)=q(c).getBoolean("attention",false);fun sick(c:Context)=q(c).getBoolean("sick",false);fun light(c:Context)=q(c).getBoolean("light",true);fun overlay(c:Context)=q(c).getBoolean("overlay",false);fun setOverlay(c:Context,v:Boolean){q(c).edit().putBoolean("overlay",v).apply()}
 fun sleep(c:Context)=!light(c)||Calendar.getInstance().get(Calendar.HOUR_OF_DAY)>=22||Calendar.getInstance().get(Calendar.HOUR_OF_DAY)<7
 fun feed(c:Context){tick(c);val q=q(c);q.edit().putInt("hunger",min(100,q.getInt("hunger",100)+25)).putInt("happy",min(100,q.getInt("happy",100)+3)).putBoolean("attention",false).apply()}
 fun clean(c:Context){tick(c);q(c).edit().putInt("clean",100).putInt("poop",0).apply()}
 fun play(c:Context){tick(c);val q=q(c);q.edit().putInt("happy",min(100,q.getInt("happy",100)+20)).putInt("hunger",max(0,q.getInt("hunger",100)-5)).apply()}
 fun medicine(c:Context){tick(c);val q=q(c);if(q.getBoolean("sick",false))q.edit().putBoolean("sick",false).putInt("health",100).apply()}
 fun discipline(c:Context){tick(c);q(c).edit().putBoolean("attention",false).apply()}
 fun toggleLight(c:Context){init(c);val q=q(c);q.edit().putBoolean("light",!q.getBoolean("light",true)).apply()}
 fun reset(c:Context){q(c).edit().clear().apply();init(c)}
}'''
OVER=r'''package com.example.dinocompanion
import android.app.*;import android.content.*;import android.content.pm.ServiceInfo;import android.graphics.*;import android.os.*;import android.provider.Settings;import android.view.*;import kotlin.math.*
class DinoOverlayService:Service(){
 var wm:WindowManager?=null;var v:V?=null;var lp:WindowManager.LayoutParams?=null
 override fun onCreate(){super.onCreate();DinoLife.init(this);if(Build.VERSION.SDK_INT>=26)getSystemService(NotificationManager::class.java).createNotificationChannel(NotificationChannel("dino","Dino Companion",NotificationManager.IMPORTANCE_LOW));val n=if(Build.VERSION.SDK_INT>=26)Notification.Builder(this,"dino").setSmallIcon(android.R.drawable.ic_menu_compass).setContentTitle("Dino Companion").setContentText("Rex is nearby").setOngoing(true).build()else Notification.Builder(this).setSmallIcon(android.R.drawable.ic_menu_compass).setContentTitle("Dino Companion").setContentText("Rex is nearby").setOngoing(true).build();if(Build.VERSION.SDK_INT>=29)startForeground(7,n,ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)else startForeground(7,n);if(Settings.canDrawOverlays(this))show()}
 fun show(){wm=getSystemService(WINDOW_SERVICE)as WindowManager;v=V(this);val t=if(Build.VERSION.SDK_INT>=26)WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY else WindowManager.LayoutParams.TYPE_PHONE;val sw=resources.displayMetrics.widthPixels;val w=(sw*.30f).toInt().coerceIn(170,250);val h=(w*1.22f).toInt();lp=WindowManager.LayoutParams(w,h,t,WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,PixelFormat.TRANSLUCENT);lp!!.gravity=Gravity.TOP or Gravity.START;val q=DinoLife.q(this);lp!!.x=q.getInt("ox",sw/2-w/2).coerceIn(8,sw-w-8);lp!!.y=q.getInt("oy",180).coerceIn(80,resources.displayMetrics.heightPixels-h-8);try{wm!!.addView(v,lp)}catch(_:Exception){}}
 fun move(a:Float,b:Float){val q=lp?:return;val sw=resources.displayMetrics.widthPixels;val sh=resources.displayMetrics.heightPixels;q.x=(q.x+a).toInt().coerceIn(8,max(8,sw-q.width-8));q.y=(q.y+b).toInt().coerceIn(80,max(80,sh-q.height-8));DinoLife.q(this).edit().putInt("ox",q.x).putInt("oy",q.y).apply();try{wm?.updateViewLayout(v,q)}catch(_:Exception){}}
 override fun onDestroy(){try{v?.let{wm?.removeView(it)}}catch(_:Exception){};super.onDestroy()};override fun onBind(i:Intent?):IBinder?=null
 inner class V(c:Context):View(c){val p=Paint(1);var sx=0f;var sy=0f;var moved=false;var a=0f
 init{post(object:Runnable{override fun run(){DinoLife.tick(this@DinoOverlayService);a+=.12f;invalidate();postDelayed(this,220)}})}
 override fun onDraw(c:Canvas){val s=min(width,height)/260f;val b=sin(a.toDouble()).toFloat()*5f*s;p.color=Color.argb(80,0,0,0);c.drawOval(width*.24f,height*.76f,width*.76f,height*.86f,p);p.color=Color.rgb(205,63,49);c.drawOval(width*.28f,height*.24f+b,width*.72f,height*.75f+b,p);c.drawOval(width*.34f,height*.10f+b,width*.78f,height*.40f+b,p);p.color=Color.rgb(255,190,112);c.drawOval(width*.47f,height*.44f+b,width*.63f,height*.70f+b,p);p.color=Color.WHITE;c.drawCircle(width*.48f,height*.22f+b,11f*s,p);c.drawCircle(width*.65f,height*.22f+b,11f*s,p);p.color=Color.DKGRAY;c.drawCircle(width*.50f,height*.22f+b,5f*s,p);c.drawCircle(width*.67f,height*.22f+b,5f*s,p);if(DinoLife.sleep(this@DinoOverlayService)){p.color=Color.WHITE;p.textSize=18f*s;p.textAlign=Paint.Align.CENTER;c.drawText("Z z Z",width*.75f,height*.16f,p)}}
 override fun onTouchEvent(e:MotionEvent):Boolean{when(e.actionMasked){0->{sx=e.rawX;sy=e.rawY;moved=false;return true};2->{if(abs(e.rawX-sx)>8||abs(e.rawY-sy)>8)moved=true;move(e.rawX-sx,e.rawY-sy);sx=e.rawX;sy=e.rawY;return true};1->{if(!moved)startActivity(Intent(this@DinoOverlayService,MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP));return true}};return true}}
}'''
(s/"MainActivity.kt").write_text(MAIN,encoding="utf-8")
(s/"DinoLife.kt").write_text(LIFE,encoding="utf-8")
(s/"DinoOverlayService.kt").write_text(OVER,encoding="utf-8")
g=r/"app/build.gradle.kts"
if g.exists():
 x=g.read_text();x=re.sub(r'versionCode\s*=\s*\d+','versionCode = 50',x);x=re.sub(r'versionName\s*=\s*"[^"]+"','versionName = "2.0"',x);g.write_text(x)
(r/"BUILD_VERSION.txt").write_text("Dino Companion 2.0 - Tamagotchi Dino\n")
# Remove obsolete percentage-based XML layout from the base project; the new screen is Canvas-driven.
layout=r/"app/src/main/res/layout"
if layout.exists():
    shutil.rmtree(layout)

