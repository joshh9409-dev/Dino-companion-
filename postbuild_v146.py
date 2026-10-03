from pathlib import Path
import re

root = Path(".")
main_path = root / "app/src/main/java/com/example/dinocompanion/MainActivity.kt"
s = main_path.read_text(encoding="utf-8")

# v1.46 page and state
s = s.replace(
    "enum class Page { HOME, CHOOSE, CARE, PLAY, SHOP, INVENTORY, SETTINGS }",
    "enum class Page { HOME, CHOOSE, CARE, PLAY, SHOP, INVENTORY, EVOLVE, SETTINGS }"
)
s = s.replace(
    'private var lastTap=0L',
    'private var lastTap=0L\n    private var gameActive=false\n    private var gameScore=0\n    private var gameKind=0\n    private var gameEnds=0L\n    private var dailyClaimedDay=prefs.getInt("daily_claim_day",-1)'
)

# Draw evolution page
evolve_method = r'''
    private fun drawEvolve(c: Canvas) {
        header(c,"EVOLUTION")
        text(c,"Grow "+dinoName+" through four stages",width/2f,88f,13f,Color.WHITE,true)
        round(c,18f,105f,width-18f,390f,26f,Color.argb(238,248,253,249))
        drawDino(c,width/2f,220f,.82f)
        text(c,"STAGE "+stage+" / 4",width/2f,310f,20f,dino.accent,true,true)
        val need=stage*100
        text(c,if(stage<4) xp.toString()+" / "+need+" XP" else "MAX EVOLUTION",width/2f,338f,14f,Color.DKGRAY,true,true)
        round(c,45f,350f,width-45f,364f,7f,Color.LTGRAY)
        round(c,45f,350f,45f+(width-90f)*min(1f,xp/need.toFloat()),364f,7f,dino.color)
        if(stage<4) {
            button(c,35f,420f,width-35f,490f,if(xp>=need)"EVOLVE NOW" else "NEED MORE XP","◆",if(xp>=need)dino.color else Color.GRAY)
        } else {
            text(c,"FINAL STAGE REACHED",width/2f,460f,14f,Color.WHITE,true,true)
        }
        text(c,"Evolution rewards XP progress, happiness, bond and coins.",width/2f,525f,12f,Color.WHITE,true)
        text(c,"Stages: Baby  •  Juvenile  •  Adolescent  •  Adult",width/2f,550f,11f,Color.WHITE,true)
    }
'''
s = s.replace('    private fun drawSettings(c:Canvas) {', evolve_method + '\n    private fun drawSettings(c:Canvas) {')
s = s.replace(
    'Page.INVENTORY -> drawInventory(c)\n            Page.SETTINGS',
    'Page.INVENTORY -> drawInventory(c)\n            Page.EVOLVE -> drawEvolve(c)\n            Page.SETTINGS'
)

# Replace Play screen with three actual tap games.
play_method = r'''
    private fun drawPlay(c:Canvas) {
        header(c,"PLAY")
        if(gameActive && System.currentTimeMillis() < gameEnds) {
            text(c,"TIME "+((gameEnds-System.currentTimeMillis()+999)/1000)+"s",width/2f,92f,18f,Color.WHITE,true,true)
            text(c,"SCORE "+gameScore,width/2f,122f,16f,Color.WHITE,true,true)
            round(c,18f,145f,width-18f,420f,28f,Color.argb(238,248,253,249))
            drawDino(c,width/2f,270f,.85f)
            button(c,30f,450f,width-30f,535f,
                when(gameKind){0->"POP BUBBLES!";1->"CATCH FOOD!";else->"TOSS FRUIT!"},
                "★",dino.color)
            text(c,"Tap repeatedly to score",width/2f,570f,13f,Color.WHITE,true)
            invalidate()
            return
        }
        if(gameActive) finishMiniGame()
        text(c,"Three mini-games. Earn XP, coins and bond.",width/2f,88f,13f,Color.WHITE,true)
        gameCard(c,20f,112f,"BUBBLE POP","Tap fast for points",0)
        gameCard(c,20f,225f,"CATCH THE FOOD","Feed your Dino",1)
        gameCard(c,20f,338f,"FRUIT TOSS","Build your bond",2)
        text(c,"Games played and rewards are saved.",width/2f,470f,12f,Color.WHITE,true)
    }

    private fun gameCard(c:Canvas,x:Float,y:Float,title:String,desc:String,id:Int) {
        round(c,x,y,width-x,y+94f,22f,Color.argb(238,248,253,249))
        text(c,title,x+18f,y+31f,16f,dino.accent,false,true)
        text(c,desc,x+18f,y+56f,11f,Color.DKGRAY)
        button(c,width-125f,y+14f,width-32f,y+77f,"PLAY","▶",dino.color)
    }

    private fun startMiniGame(kind:Int) {
        gameKind=kind;gameScore=0;gameActive=true;gameEnds=System.currentTimeMillis()+15000L;invalidate()
    }

    private fun finishMiniGame() {
        if(!gameActive)return
        gameActive=false
        val reward=5+(gameScore.coerceAtMost(20))
        coins+=reward
        happiness=min(100,happiness+10)
        bond=min(100,bond+if(gameKind==2)8 else 4)
        addXp(8+gameScore/2)
        save()
        Toast.makeText(ctx,"Game complete! +"+reward+" coins",Toast.LENGTH_SHORT).show()
    }
'''
s = re.sub(r'    private fun drawPlay(c:Canvas) {.*?\n    private fun drawShop', play_method + '\n    private fun drawShop', s, flags=re.S)

# Add a richer inventory grid while retaining existing data.
inventory_method = r'''
    private fun drawInventory(c:Canvas) {
        header(c,"INVENTORY")
        text(c,"Your collected items",width/2f,88f,13f,Color.WHITE,true)
        val items=arrayOf(
            arrayOf("FOOD",food.toString(),"Meals"),
            arrayOf("TOYS",toys.toString(),"Play"),
            arrayOf("COINS",coins.toString(),"Currency"),
            arrayOf("GEMS",gems.toString(),"Rare"),
            arrayOf("XP",""+xp,"Progress"),
            arrayOf("BOND",""+bond,"Friendship")
        )
        for(i in items.indices) {
            val col=i%2;val row=i/2
            val l=18f+col*(width-44f)/2f;val t=110f+row*105f
            round(c,l,t,l+(width-44f)/2f,t+88f,20f,Color.argb(238,248,253,249))
            text(c,items[i][0],l+16f,t+28f,12f,dino.accent,false,true)
            text(c,items[i][1],l+16f,t+63f,25f,dino.color,false,true)
            text(c,items[i][2],l+82f,t+60f,10f,Color.DKGRAY)
        }
        text(c,"Items and progress persist automatically.",width/2f,445f,12f,Color.WHITE,true)
    }
'''
s = re.sub(r'    private fun drawInventory(c:Canvas) {.*?\n    private fun drawSettings', inventory_method + '\n    private fun drawSettings', s, flags=re.S)

# Touch additions
s = s.replace(
    'if(page==Page.CHOOSE && kotlin.math.abs(dx)>80f){',
    'if(page==Page.PLAY && gameActive){ gameScore++; happiness=min(100,happiness+1); invalidate(); return true }\n            if(page==Page.CHOOSE && kotlin.math.abs(dx)>80f){'
)
s = s.replace(
    'Page.PLAY -> when{y in 395f..495f->dash();y in 500f..590f->ball()}',
    'Page.PLAY -> when{y in 100f..210f->startMiniGame(0);y in 215f..325f->startMiniGame(1);y in 330f..445f->startMiniGame(2)}'
)
s = s.replace(
    'Page.INVENTORY -> if(y>550)page=Page.HOME',
    'Page.INVENTORY -> {}\n            Page.EVOLVE -> if(y in 400f..505f && stage<4 && xp>=stage*100){evolve();save()}'
)
s = s.replace(
    'y in 500f..595f -> page=Page.INVENTORY',
    'y in 500f..595f -> page=Page.INVENTORY\n                    y in 400f..495f -> page=Page.EVOLVE'
)

# Daily reward in shop, once per calendar day.
s = s.replace(
    'y in 555f..650f->{coins+=1;save()}',
    'y in 555f..650f->{val day=java.util.Calendar.getInstance().get(java.util.Calendar.DAY_OF_YEAR);if(dailyClaimedDay!=day){coins+=10;dailyClaimedDay=day;prefs.edit().putInt("daily_claim_day",day).apply();save();Toast.makeText(ctx,"Daily reward claimed! +10 coins",Toast.LENGTH_SHORT).show()}else Toast.makeText(ctx,"Daily reward already claimed.",Toast.LENGTH_SHORT).show()}'
)

# Version and reset.
s = s.replace('Dino Companion 1.41','Dino Companion 1.46')
s = s.replace(
    'dinoName="Rex";selectedId="trex";stage=1;xp=32;',
    'gameActive=false;gameEnds=0L;dinoName="Rex";selectedId="trex";stage=1;xp=32;'
)
main_path.write_text(s,encoding="utf-8")

g=root/"app/build.gradle.kts"
gs=g.read_text(encoding="utf-8")
gs=re.sub(r'applicationId\s*=\s*"[^"]+"','applicationId = "com.example.dinocompanion.v146"',gs)
gs=re.sub(r'versionCode\s*=\s*\d+','versionCode = 49',gs)
gs=re.sub(r'versionName\s*=\s*"[^"]+"','versionName = "1.46"',gs)
g.write_text(gs,encoding="utf-8")
(root/"BUILD_VERSION.txt").write_text("Dino Companion v1.46 complete interactive upgrade\n",encoding="utf-8")
