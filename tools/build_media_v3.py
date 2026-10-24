#!/usr/bin/env python3
"""Build the 84-second 星黎 product film from approved local, redacted clips.

No deleted recordings are read. The original webroot backup is required for
the legacy memory clip and retained gallery images. Use --work to select the
external working/delivery directory; the webroot only receives safe outputs.
"""
import argparse
import concurrent.futures
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageChops
import promo_style as art

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "www/assets"
SOURCE = Path("/Users/ct/Desktop/星黎项目/星黎OS/官网素材/补充-20261022/录屏")
DEFAULT_WORK = Path("/Users/ct/Desktop/星黎项目/星黎OS/官网素材/官网更新-20261023")
MUSIC = Path("/Users/ct/Desktop/星黎项目/星黎OS/app-release/assets/audio/BGM/Cafe LAN Dreamloop.wav")
KV = Path("/Users/ct/Desktop/星黎项目/星黎OS/stellae-design-system/assets/kv-hero.webp")
FPS = 30
FADE = .3
CHAPTERS = [("01", "相遇"), ("02", "交流"), ("03", "靠近"),
            ("04", "羁绊"), ("05", "星轨"), ("06", "日常")]


def run(args):
    command = [str(a) for a in args]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace")[-5000:])
    return result.stdout


def ffmpeg(*args):
    return run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-filter_complex_threads", "2", *args])


def encode():
    return ["-an", "-r", str(FPS), "-c:v", "libx264", "-threads", "3",
            "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart"]


def normalize(parts, target, duration, fade=FADE):
    """Parts are (path, source start, duration); preserve portrait geometry."""
    inputs, filters = [], []
    for i, (path, start, length) in enumerate(parts):
        inputs += ["-ss", str(start), "-t", str(length), "-i", str(path)]
        filters.append(
            f"[{i}:v]setpts=PTS-STARTPTS,fps={FPS},"
            "scale=620:1344:force_original_aspect_ratio=decrease:flags=lanczos,"
            f"pad=620:1344:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[p{i}]")
    current, elapsed = "p0", parts[0][2]
    for i in range(1, len(parts)):
        label = f"x{i}"
        filters.append(f"[{current}][p{i}]xfade=transition=fade:duration={fade}:"
                       f"offset={elapsed-fade:.6f}[{label}]")
        current = label
        elapsed += parts[i][2] - fade
    filters.append(f"[{current}]tpad=stop_mode=clone:stop_duration=2,trim=duration={duration},"
                   "setpts=PTS-STARTPTS[out]")
    ffmpeg(*inputs, "-filter_complex", ";".join(filters), "-map", "[out]",
           "-t", str(duration), *encode(), target)


def sanitize_memory(backup, target):
    # The sensitive paragraph is below the card. Exclude the subsequent card
    # back entirely, then irreversibly pixelate/blur the whole paragraph area.
    graph = (
        "[0:v]trim=0:10.4,setpts=PTS-STARTPTS,fps=30,split[base][region];"
        "[region]crop=332:210:50:650,scale=8:5:flags=area,"
        "scale=332:210:flags=neighbor,gblur=sigma=14[private];"
        "[base][private]overlay=50:650:enable='gte(t,1.5)',"
        "scale=620:1344:force_original_aspect_ratio=decrease:flags=lanczos,"
        "pad=620:1344:(ow-iw)/2:(oh-ih)/2,setsar=1,"
        "tpad=stop_mode=clone:stop_duration=2,trim=duration=12[out]"
    )
    ffmpeg("-i", backup / "www/assets/memory.mp4", "-filter_complex", graph,
           "-map", "[out]", "-t", "12", *encode(), target)


def feature_export(master, name, poster_time=2):
    target = WEB / f"{name}.mp4"
    mask_path=master.parent/'feature-phone-alpha.png'
    rounded_mask((432,930),64,inset=3).save(mask_path)
    graph=("[0:v]scale=432:930:force_original_aspect_ratio=decrease:flags=lanczos,"
           "pad=432:930:(ow-iw)/2:(oh-ih)/2,setsar=1,format=rgba[recording];"
           "[1:v]format=gray[mask];[recording][mask]alphamerge[inside];"
           "[2:v][inside]overlay=0:0:shortest=1,format=yuv420p[out]")
    ffmpeg("-i",master,"-loop","1","-framerate","30","-i",mask_path,
           "-f","lavfi","-i","color=c=black:s=432x930:r=30",
           "-filter_complex",graph,"-map","[out]","-t","12",*encode(),target)
    ffmpeg("-ss", str(poster_time), "-i", target, "-frames:v", "1", "-q:v", "2",
           WEB / f"{name}.jpg")


def rounded_mask(size, radius, inset=0):
    # Antialias the screen opening at 4x, so no rectangular corner survives.
    w,h=size
    mask=Image.new('L',(w*4,h*4))
    ImageDraw.Draw(mask).rounded_rectangle((inset*4,inset*4,w*4-inset*4-1,h*4-inset*4-1),
                                         max(0,radius-inset)*4,fill=255)
    return mask.resize(size,Image.Resampling.LANCZOS)


def phone_layers(folder):
    mask=rounded_mask((art.PW,art.PH),64)
    mask_path=folder/'phone-alpha.png';mask.save(mask_path)
    # This is the foreground bezel. The recording is composited below it.
    shell=Image.new('RGBA',(art.W,art.H))
    d=ImageDraw.Draw(shell)
    d.rounded_rectangle((art.PX-9,art.PY-9,art.PX+art.PW+8,art.PY+art.PH+8),
                        80,fill=(12,14,30,255),outline=art.VIOLET+(110,),width=2)
    alpha=shell.getchannel('A')
    box=(art.PX,art.PY,art.PX+art.PW,art.PY+art.PH)
    # The foreground overlaps three pixels of the recording, hiding native
    # mirroring-window highlights and antialiasing fringes as well as corners.
    opening=rounded_mask((art.PW,art.PH),64,inset=3)
    alpha.paste(ImageChops.multiply(alpha.crop(box),ImageChops.invert(opening)),box)
    shell.putalpha(alpha)
    shell_path=folder/'phone-foreground.png';shell.save(shell_path)
    return mask_path,shell_path


def title_layer(lines, subtitle, chapter, english):
    image = Image.new("RGBA", (art.W, art.H))
    d = ImageDraw.Draw(image)
    art.spaced(d, (art.TX, 350), f"{chapter}  /  {english}", art.mono(25), art.VIOLET, 4)
    d.line((art.TX, 402, art.TX+56, 402), fill=art.VIOLET+(150,), width=2)
    art.four_star(d, art.TX+72, 402, 7, art.VIOLET+(220,))
    for i, line in enumerate(lines):
        if art.serif(72).getlength(line) > 790:
            raise ValueError(f"Title exceeds approved text region: {line}")
        art.draw_title(image, (art.TX, 435+i*93), [(line, True)] if i else [line], art.serif(72))
    if art.sans(29).getlength(subtitle) > 790:
        raise ValueError("Subtitle exceeds text region: "+subtitle)
    d.text((art.TX, 660), subtitle, font=art.sans(29), fill=art.INK2)
    x, y = art.TX, 952
    for number, label in CHAPTERS:
        active = number == chapter
        d.text((x,y+2),number,font=art.mono(20),fill=art.VIOLET if active else art.INK3)
        d.text((x+34,y-2),label,font=art.sans(22),fill=art.INK1 if active else art.INK3)
        if active:
            d.line((x,y+38,x+34+art.sans(22).getlength(label),y+38),fill=art.VIOLET,width=2)
        x += 34+art.sans(22).getlength(label)+40
    return image


def render_segment(spec, folder):
    key, start, end, master, source_start, lines, subtitle, chapter, english = spec
    duration = end-start+FADE
    bg = folder / f"bg-{key}.png"
    text = folder / f"text-{key}.png"
    mask_path,shell_path=folder/'phone-alpha.png',folder/'phone-foreground.png'
    art.background((art.PX+art.PW//2,art.H//2)).save(bg)
    title_layer(lines, subtitle, chapter, english).save(text)
    out = folder / f"segment-{key}.mp4"
    graph = (
        f"[2:v]fps={FPS},scale={art.PW}:{art.PH}:force_original_aspect_ratio=decrease:flags=lanczos,"
        f"pad={art.PW}:{art.PH}:(ow-iw)/2:(oh-ih)/2,setsar=1,"
        "tpad=stop_mode=clone:stop_duration=2,format=rgba[recording];"
        "[3:v]format=gray[screen-mask];[recording][screen-mask]alphamerge[phone];"
        f"[0:v][phone]overlay={art.PX}:{art.PY}:shortest=1[under-frame];"
        "[under-frame][4:v]overlay=0:0:shortest=1[base];"
        "[1:v]format=rgba,fade=in:st=0.25:d=0.7:alpha=1[title];"
        "[base][title]overlay=0:0:shortest=1,format=yuv420p[out]"
    )
    if key == "modes":
        graph = graph.replace("format=yuv420p[out]", "format=yuv420p[labeled]")
        current = "labeled"
        for i,(label,a,b) in enumerate([("2D 动态人物",0,2.4),("3D 模型",2.4,4.8),("微信风格",4.8,8)]):
            label_path = folder/f"mode-label-{i}.png"
            layer=Image.new("RGBA",(art.W,art.H))
            ImageDraw.Draw(layer).text((art.TX,735),label,font=art.sans(35),fill=art.VIOLET)
            layer.save(label_path)
        # Label inputs follow background, titles, recording, mask, and bezel.
        for i,(_,a,b) in enumerate([("",0,2.4),("",2.4,4.8),("",4.8,8)]):
            nxt = "out" if i==2 else f"label{i}"
            graph += f";[{current}][{5+i}:v]overlay=0:0:enable='gte(t,{a})*lt(t,{b})'[{nxt}]"
            current=nxt
    inputs=["-loop","1","-framerate",str(FPS),"-i",bg,
            "-loop","1","-framerate",str(FPS),"-i",text,
            "-ss",str(source_start),"-i",master,
            "-loop","1","-framerate",str(FPS),"-i",mask_path,
            "-loop","1","-framerate",str(FPS),"-i",shell_path]
    if key=="modes":
        for i in range(3):inputs += ["-loop","1","-framerate",str(FPS),"-i",folder/f"mode-label-{i}.png"]
    ffmpeg(*inputs,"-filter_complex",graph,"-map","[out]","-t",str(duration),*encode(),out)
    return out


def render_outro(folder, show_note=True):
    bg=Image.open(KV).convert("RGBA")
    bg=bg.resize((art.W,round(bg.height*art.W/bg.width)))
    canvas=Image.new("RGBA",(art.W,art.H),art.NIGHT0+(255,))
    canvas.alpha_composite(bg,(0,(art.H-bg.height)//2))
    shade=Image.new("RGBA",canvas.size);d=ImageDraw.Draw(shade)
    for x in range(art.W):
        a=int(210*max(0,1-x/1100)**1.4)
        d.line((x,0,x,art.H),fill=art.NIGHT0+(a,))
    canvas.alpha_composite(shade)
    text=Image.new("RGBA",canvas.size);d=ImageDraw.Draw(text)
    art.spaced(d,(120,330),"STELLAE.AI",art.mono(26),art.VIOLET,5)
    d.text((120,390),"让相遇，",font=art.serif(96),fill=art.INK1)
    art.grad_text(text,(120,510),"成为日常。",art.serif(96))
    d.text((124,690),"星黎 · 参与内测",font=art.sans(35),fill=art.INK1)
    if show_note:
        d.text((124,758),"品牌视觉 / AI COMPANION",font=art.sans(22),fill=art.INK2)
    b,t=folder/'outro-bg.png',folder/'outro-text.png';canvas.save(b);text.save(t)
    out=folder/'segment-outro.mp4'
    graph=("[0:v]scale=3840:2160,zoompan=z='1+0.06*on/210':"
           "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30[bg];"
           "[1:v]format=rgba,fade=in:st=0.25:d=0.7:alpha=1[t];"
           "[bg][t]overlay=0:0:shortest=1,format=yuv420p[out]")
    ffmpeg('-loop','1','-framerate','30','-i',b,'-loop','1','-framerate','30','-i',t,
           '-filter_complex',graph,'-map','[out]','-t','7',*encode(),out)
    return out


def sanitize_gallery(backup, audit):
    """Only redact existing personal avatar circles; retain all six scenes."""
    import cv2
    import numpy as np
    base=backup/'www/assets/world-gallery'
    first=cv2.imread(str(base/'01.webp'))
    # Native screenshot: 1179x2556. A padded template contains the avatar ring.
    template=first[1600:1732,1005:1140].copy()
    mask=np.zeros(template.shape[:2],np.uint8)
    cv2.circle(mask,(66,66),48,255,-1)
    report=[]
    for src in sorted(base.glob('*.webp')):
        frame=cv2.imread(str(src)); original=frame.copy(); boxes=[]
        region=frame[1250:2400,970:1179]
        scores=cv2.matchTemplate(region,template,cv2.TM_CCORR_NORMED,mask=mask)
        for _ in range(8):
            _,score,_,loc=cv2.minMaxLoc(scores)
            if score<.98:break
            x,y=loc;x+=970;y+=1250
            x1,y1=max(0,x-6),max(0,y-6)
            x2,y2=min(frame.shape[1],x+141),min(frame.shape[0],y+138)
            patch=frame[y1:y2,x1:x2]
            pixel=cv2.resize(patch,(4,4),interpolation=cv2.INTER_AREA)
            frame[y1:y2,x1:x2]=cv2.GaussianBlur(cv2.resize(pixel,(x2-x1,y2-y1),interpolation=cv2.INTER_NEAREST),(0,0),20)
            boxes.append([x1,y1,x2,y2,round(score,3)])
            sy=loc[1];scores[max(0,sy-110):sy+111,:]=-1
        target=WEB/'world-gallery'/src.name
        if boxes:
            Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).save(target,format='WEBP',quality=96)
        else:
            shutil.copy2(src,target)
        report.append({'file':src.name,'avatar_boxes':boxes,'composition_unchanged':True})
    (audit/'图库隐私处理.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--work',type=Path,default=DEFAULT_WORK)
    parser.add_argument('--reuse',action='store_true',help='Reuse completed local intermediates')
    args=parser.parse_args();work=args.work
    folder=work/'构建';delivery=work/'交付';audit=work/'核查';backup=work/'回退-cc98e0c'
    for p in [folder,delivery,audit]:p.mkdir(parents=True,exist_ok=True)
    phone_layers(folder)
    if not (backup/'www/assets/memory.mp4').is_file():raise FileNotFoundError('Original backup required')
    masters={name:folder/f'{name}-master.mp4' for name in ['outfit','scene','closeness','memory','startrack','modes']}
    tasks=[
        ([(SOURCE/'12-装扮-黑色军装.mp4',.4,5.2),(SOURCE/'12-换装-黑色魔女.mp4',.3,7.1)],masters['outfit'],12),
        ([(SOURCE/'13-黑色军装-客厅白天.mp4',.3,4.3),(SOURCE/'13-黑色魔女-宫殿夜景.mp4',.3,4.3),(SOURCE/'13-黑色魔女-宫殿白天.mp4',.3,4)],masters['scene'],12),
        ([(SOURCE/'09-靠近-阶段切换.mp4',.5,5.6),(SOURCE/'09-靠近-阶段切换.mp4',17.5,3.5),(SOURCE/'09-靠近-阶段切换.mp4',20,3.5)],masters['closeness'],12),
        ([(SOURCE/'10-星轨-任务与未解锁.mp4',0,12)],masters['startrack'],12),
        ([(SOURCE/'02-模式-2D动态人物.mp4',1,2.7),(SOURCE/'02-模式-3D模型.mp4',1,2.7),(SOURCE/'02-模式-微信风格.mp4',1,2.5)],masters['modes'],7.3),
    ]
    for parts,target,duration in tasks:
        print('prepare',target.name,flush=True)
        if not (args.reuse and target.is_file()):normalize(parts,target,duration)
    if not (args.reuse and masters['memory'].is_file()):sanitize_memory(backup,masters['memory'])
    overview_star=folder/'startrack-overview-master.mp4'
    overview_scene=folder/'scene-overview-master.mp4'
    if not (args.reuse and overview_star.is_file()):
        normalize([(SOURCE/'10-星轨-任务与未解锁.mp4',0,3.6),
                   (SOURCE/'10-星轨-任务与未解锁.mp4',8.7,3)],overview_star,6.3)
    if not (args.reuse and overview_scene.is_file()):
        normalize([(SOURCE/'13-黑色军装-客厅白天.mp4',.3,2.7),
                   (SOURCE/'13-黑色魔女-宫殿夜景.mp4',.3,2.7),
                   (SOURCE/'13-黑色魔女-宫殿白天.mp4',.3,2.5)],overview_scene,7.3)
    sanitize_gallery(backup,audit)
    poster_times={'outfit':8,'scene':2,'closeness':2,'memory':5,'startrack':2}
    for name in ['outfit','scene','closeness','memory','startrack']:
        if not (args.reuse and (WEB/f'{name}.mp4').is_file()):
            feature_export(masters[name],name,poster_times[name])
        shutil.copy2(WEB/f'{name}.mp4',delivery/f'星黎-功能-{name}.mp4')
        shutil.copy2(WEB/f'{name}.jpg',delivery/f'星黎-功能-{name}.jpg')
    specs=[
      ('intro',0,4,SOURCE/'03-冷启动-星标到角色.mp4',.5,['星黎'], '让相遇，成为日常。','01','MEET STELLAE'),
      ('her',4,8,SOURCE/'02-模式-3D模型.mp4',1,['与你持续相处的','AI 伙伴。'],'在一次次交流里，慢慢熟悉。','01','AI COMPANION'),
      ('photo',8,16,SOURCE/'06-发照片-发送与回应.mp4',0,['今天的小事，','也想分享给你。'],'照片分享 · 实际发送与回应','02','SHARE'),
      ('call',16,22,SOURCE/'08-主动通话-3D界面.mp4',0,['想聊天时，','换一种靠近的方式。'],'通话界面实录','02','CALL'),
      ('gift',22,29,SOURCE/'07-送礼物-游戏机反馈.mp4',5.6,['一份心意，','一次回应。'],'送出礼物，看看她的反馈。','02','INTERACTION'),
      ('closeness',29,40,masters['closeness'],0,['从陌生，','到一点点熟悉。'],'当前阶段与关系维度 · 含阶段预览','03','CONNECTION'),
      ('memory',40,49,masters['memory'],0,['有些瞬间，','值得留下来。'],'羁绊碎片 · 个人内容已脱敏','04','FRAGMENTS'),
      ('startrack',49,55,overview_star,0,['相处的小进展，','也有迹可循。'],'星轨任务 · 已完成与待解锁','05','STAR TRAIL'),
      ('outfit',55,63,masters['outfit'],2,['今天，','换一种心情见面。'],'军装与魔女 · 装扮切换实录','06','OUTFIT'),
      ('scene',63,70,overview_scene,0,['换个地方，','接着聊。'],'选择此刻喜欢的场景','06','SCENE'),
      ('modes',70,77,masters['modes'],0,['选择你习惯的','相处方式。'],'在设置中切换显示方式','06','DISPLAY MODES'),
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(lambda s: folder/f"segment-{s[0]}.mp4"
                             if args.reuse and (folder/f"segment-{s[0]}.mp4").is_file()
                             else render_segment(s,folder),spec) for spec in specs]
        clips=[]
        for spec,future in zip(specs,futures):
            clips.append(future.result());print('rendered',spec[0],flush=True)
    clips.append(render_outro(folder))
    inputs=[]
    for path in clips:inputs += ['-i',path]
    filters=[];current='0:v'
    for i,start in enumerate([4,8,16,22,29,40,49,55,63,70,77],1):
        label=f'join{i}'
        filters.append(f'[{current}][{i}:v]xfade=transition=fade:duration={FADE}:offset={start}[{label}]')
        current=label
    filters.append(f'[{current}]trim=duration=84,fade=out:st=83.2:d=0.8,format=yuv420p[v]')
    filters.append('[12:a]atrim=0:84,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.8,'
                   'afade=t=out:st=81.4:d=2.6,loudnorm=I=-16:TP=-1.5:LRA=11[a]')
    final=delivery/'星黎-产品介绍-v3.mp4'
    ffmpeg(*inputs,'-i',MUSIC,'-filter_complex',';'.join(filters),'-map','[v]','-map','[a]',
           '-t','84','-r','30','-c:v','libx264','-threads','4','-preset','medium','-crf','19',
           '-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',final)
    shutil.copy2(final,WEB/'trailer.mp4')
    # Select an eyes-open, legible relationship frame for the film cover.
    ffmpeg('-ss','30.5','-i',final,'-frames:v','1','-vf','scale=1600:900','-q:v','2',WEB/'trailer-poster.jpg')
    shutil.copy2(WEB/'trailer-poster.jpg',delivery/'星黎-产品介绍-v3-封面.jpg')
    timeline=[{'start':s[1],'end':s[2],'section':s[0],'title':' '.join(s[5]),'note':s[6],
               'source':str(s[3]),'source_start':s[4]} for s in specs]
    timeline.append({'start':77,'end':84,'section':'outro','title':'让相遇，成为日常。','note':'星黎 · 参与内测；品牌视觉'})
    report={'duration_seconds':84,'frame_rate':30,'resolution':'1920x1080',
            'timeline':timeline,'scene_gallery_status':'原六张保留，仅隐私处理；待用户定义后重新截图',
            'listening_check':'NOT_PERFORMED','source_policy':'Only approved redacted captures and original web backup; no Trash reads',
            'privacy_memory':'Legacy private paragraph irreversibly pixelated and blurred; card-back interval excluded',
            'phone_compositing':'Recording below foreground phone bezel, clipped with antialiased rounded screen mask; feature media corners also masked',
            'audio_source':str(MUSIC),'audio_policy':'Existing BGM only, no fabricated call or character audio'}
    (audit/'视频制作记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('DONE',final,flush=True)


if __name__=='__main__':main()
