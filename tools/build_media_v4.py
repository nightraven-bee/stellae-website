#!/usr/bin/env python3
"""Update the existing film artwork with the reviewed 2026-10-24 captures.

Only redacted exports are admitted. The phone footage remains beneath a rounded
screen mask and foreground bezel. No website styles or interaction code change.
"""
import argparse
import concurrent.futures
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageChops, ImageFilter
import cv2
import numpy as np
import build_media_v3 as film

REPO = Path(__file__).resolve().parents[1]
ROOT = Path('/Users/ct/Desktop/星黎项目/星黎OS/官网素材')
CAPTURE = ROOT / '重采-20261024'
SOURCE = CAPTURE / '交付'
WORK = ROOT / '官网更新-20261024'
ASSETS = REPO / 'www/assets'
PHOTO = ROOT / '补充-20261022/录屏/06-发照片-发送与回应.mp4'
WECHAT = ROOT / '补充-20261022/录屏/02-模式-微信风格.mp4'
MEET_2D = WORK / '交付/星黎-补录-2D网咖.mp4'
CHAPTERS = [('01', '相遇'), ('02', '交流'), ('03', '靠近'),
            ('04', '羁绊'), ('05', '日常')]
film.CHAPTERS = CHAPTERS


def source(name):
    path = SOURCE / (name + '.mp4')
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def phone_layers(folder):
    # New mirrored captures have larger native rounded corners than old ones.
    # The screen opening must cut inside those corners, hiding their white rim.
    art = film.art
    mask = film.rounded_mask((art.PW, art.PH), 82)
    mask.save(folder / 'phone-alpha.png')
    shell = Image.new('RGBA', (art.W, art.H))
    d = ImageDraw.Draw(shell)
    d.rounded_rectangle((art.PX-9, art.PY-9, art.PX+art.PW+8, art.PY+art.PH+8),
                        80, fill=(12, 14, 30, 255), outline=art.VIOLET+(110,), width=2)
    box = (art.PX, art.PY, art.PX+art.PW, art.PY+art.PH)
    alpha = shell.getchannel('A')
    opening = film.rounded_mask((art.PW, art.PH), 82, inset=3)
    alpha.paste(ImageChops.multiply(alpha.crop(box), ImageChops.invert(opening)), box)
    shell.putalpha(alpha)
    shell.save(folder / 'phone-foreground.png')


def feature_export(master, name, duration, folder, stage, poster_time=2):
    mask_path = folder / 'feature-phone-alpha.png'
    film.rounded_mask((432, 930), 82, inset=3).save(mask_path)
    graph = ('[0:v]scale=432:930:force_original_aspect_ratio=decrease:flags=lanczos,'
             'pad=432:930:(ow-iw)/2:(oh-ih)/2,setsar=1,format=rgba[recording];'
             '[1:v]format=gray[mask];[recording][mask]alphamerge[inside];'
             '[2:v][inside]overlay=0:0:shortest=1,format=yuv420p[out]')
    target = stage / (name + '.mp4')
    film.ffmpeg('-i', master, '-loop', '1', '-framerate', '30', '-i', mask_path,
                '-f', 'lavfi', '-i', 'color=c=black:s=432x930:r=30',
                '-filter_complex', graph, '-map', '[out]', '-t', str(duration),
                *film.encode(), target)
    film.ffmpeg('-ss', str(poster_time), '-i', target, '-frames:v', '1', '-q:v', '2',
                stage / (name + '.jpg'))


def gallery_export(stage, work=WORK):
    gallery = stage / 'world-gallery'
    gallery.mkdir(exist_ok=True)
    rows = json.loads((work / '图库选帧.json').read_text())
    # Derive the exact native screen contour from the new dark cafe shot.
    # Only the light gray window matte connected to the four outside corners
    # is removed; no character pixels or UI content are retouched.
    ref = np.array(Image.open(Path(rows[-1]['source'])).convert('RGB'))
    neutral = (np.min(ref, axis=2) > 190) & ((np.max(ref, axis=2).astype(int)-np.min(ref, axis=2)) < 22)
    _, labels = cv2.connectedComponents(neutral.astype(np.uint8))
    h, w = neutral.shape
    outside_ids = {int(labels[y,x]) for x,y in [(0,0),(w-1,0),(0,h-1),(w-1,h-1)]} - {0}
    outside = np.isin(labels, list(outside_ids))
    native_mask = Image.fromarray((~outside).astype(np.uint8)*255)
    native_mask = native_mask.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(.45))
    native_mask.save(work/'构建/gallery-native-alpha.png')
    result = []
    for i, row in enumerate(rows, 1):
        src = Path(row['source'])
        im = Image.open(src).convert('RGBA')
        # Transparent outside the actual screen. No baked black matte or
        # second painted device outline in the still-image gallery.
        mask = native_mask.resize(im.size, Image.Resampling.LANCZOS)
        im.putalpha(ImageChops.multiply(im.getchannel('A'), mask))
        dst = gallery / f'{i:02d}.webp'
        im.save(dst, 'WEBP', lossless=True, exact=True)
        result.append(dict(row, file=f'assets/world-gallery/{i:02d}.webp',
                           alpha_corners='TRANSPARENT', black_matte=False))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--work', type=Path, default=WORK)
    parser.add_argument('--reuse', action='store_true')
    args = parser.parse_args()
    work = args.work
    folder, delivery, audit, stage = [work / n for n in ['构建', '交付', '核查', '待替换']]
    for p in [folder, delivery, audit, stage]:
        p.mkdir(parents=True, exist_ok=True)
    audit.chmod(0o700)
    backup = work / '回退-089aa55'
    if not (backup / 'www/assets/trailer.mp4').is_file():
        raise FileNotFoundError('Create a complete pre-edit snapshot before rendering')

    meet = source('01B-相遇-校园校服-3D')
    chinese = source('02A-交流-中文-陶杯续聊-已脱敏')
    english = source('02E-交流-未来赛博都市-纯英文重录-已脱敏')
    gift = source('02B-交流-游戏机与真实反馈-已脱敏')
    call = source('02C-交流-电话界面-连接中实录')
    close = source('03-靠近-六维总览与详情-含锁定预览')
    profile = source('04A-羁绊-侧写-蛋糕喜好-已脱敏')
    fragment = source('04B-羁绊-碎片-卡面与翻面-已脱敏')
    prism = source('04C-羁绊-棱镜-选择与回应-昵称已遮')
    looks = [
        (source('05A-装扮-黑白洛丽塔-换装'), 3, source('05A-装扮-黑白洛丽塔-两种姿势'), 32,
         source('05A-场景-洛丽塔与宫殿典礼大厅'), 6),
        (source('05B-装扮-露肩短裙-换装'), 5, source('05B-装扮-露肩短裙-两种姿势'), 33,
         source('05B-场景-短裙与樱花学校走廊'), 6),
        (source('05C-装扮-未来漆皮-换装'), 3, source('05C-装扮-未来漆皮-两种姿势'), 11,
         source('05C-场景-未来与赛博都市夜景'), 6),
        (source('05D-装扮-黑色魔女-换装'), 5, source('05D-装扮-黑色魔女-两种姿势'), 19,
         source('05D-场景-魔女与魔女城堡夜景'), 6),
    ]
    plans = {
        'outfit': ([(p, t, d) for a, at, pose, pt, _, _ in looks
                    for p, t, d in [(a, at, 2.3), (pose, pt, 4)]], 24),
        'scene': ([(s, st, 4.3) for _, _, _, _, s, st in looks], 16),
        'closeness': ([(close, 0, 6.3), (close, 14, 8.3), (close, 28, 4)], 18),
        'memory': ([(profile, 2, 4.3), (fragment, 1, 4.3), (fragment, 20, 3.3),
                    (prism, 26, 4.3), (prism, 38, 3)], 18),
        'close-film': ([(close, 1, 3.6), (close, 15, 4.9), (close, 29, 2.1)], 10.3),
        'fragment-film': ([(fragment, 1, 3.6), (fragment, 20, 3)], 6.3),
        'prism-film': ([(prism, 26, 3.6), (prism, 36, 4)], 7.3),
        'daily-first': ([(p, t, 1.8) for _, _, pose, pt, scene, st in looks[:2]
                         for p, t in [(pose, pt), (scene, st)]], 6.3),
        'daily-last': ([(p, t, 1.8) for _, _, pose, pt, scene, st in looks[2:]
                        for p, t in [(pose, pt), (scene, st)]], 6.3),
    }
    masters = {}
    for key, (parts, duration) in plans.items():
        masters[key] = target = folder / (key + '-master.mp4')
        print('prepare', key, flush=True)
        if not (args.reuse and target.is_file()):
            film.normalize(parts, target, duration)
    phone_layers(folder)
    for name, duration, poster_time in [('outfit', 24, 2), ('scene', 16, 2),
                                         ('closeness', 18, 10), ('memory', 18, 5)]:
        feature_export(masters[name], name, duration, folder, stage, poster_time)
    # The latest request did not recapture Star Trail. Retain its reviewed clip
    # as the fifth existing tab, rather than importing unrelated material.
    for ext in ['mp4', 'jpg']:
        shutil.copy2(backup / f'www/assets/startrack.{ext}', stage / f'startrack.{ext}')

    # Product-facing headlines only. Capture, redaction and review notes stay
    # in the private production report rather than on the rendered picture.
    specs = [
        ('intro', 0, 3, MEET_2D, 1, ['星黎', '让相遇，成为日常。'], '', '01', 'MEET STELLAE / 2D'),
        ('her', 3, 5.5, meet, 6, ['与你相处的', 'AI 伙伴。'], '', '01', 'AI COMPANION / 3D'),
        ('display-modes', 5.5, 8, WECHAT, 1, ['2D、3D、微信风格', '自由切换。'], '', '01', 'DISPLAY MODES'),
        ('chinese', 8, 16, chinese, 7, ['日常小事，', '慢慢聊。'], '', '02', 'EVERYDAY CHAT'),
        ('english', 16, 21, english, 31, ['换种语言，', '继续聊。'], '', '02', 'KEEP TALKING'),
        ('photo', 21, 25, PHOTO, 2, ['分享照片，', '分享此刻。'], '', '02', 'SHARE A MOMENT'),
        ('gift', 25, 30, gift, 8, ['送一份心意，', '收一份回应。'], '', '02', 'A LITTLE GIFT'),
        ('call', 30, 34, call, 2, ['发起通话。'], '', '02', 'START A CALL'),
        ('closeness', 34, 44, masters['close-film'], 0, ['在相处中，', '慢慢靠近。'], '', '03', 'GET CLOSER'),
        ('profile', 44, 48, profile, 3, ['你的偏好，', '慢慢了解。'], '', '04', 'KNOW YOU BETTER'),
        ('fragments', 48, 54, masters['fragment-film'], 0, ['留住相处的瞬间。'], '', '04', 'OUR FRAGMENTS'),
        ('prism', 54, 61, masters['prism-film'], 0, ['你的选择，', '让故事继续。'], '', '04', 'ANOTHER STORY'),
        ('outfit', 61, 67, masters['daily-first'], 0, ['换身装扮，', '换种心情。'], '', '05', 'DRESS FOR THE DAY'),
        ('scene', 67, 73, masters['daily-last'], 0, ['换个地方，', '接着聊。'], '', '05', 'SOMEWHERE WITH YOU'),
        ('wechat', 73, 77, WECHAT, 1, ['微信风格，', '自在聊。'], '', '05', 'WECHAT STYLE'),
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(lambda s: folder / f'segment-{s[0]}.mp4'
                               if args.reuse and (folder / f'segment-{s[0]}.mp4').is_file()
                               else film.render_segment(s, folder), spec) for spec in specs]
        clips = []
        for spec, future in zip(specs, futures):
            clips.append(future.result())
            print('rendered', spec[0], flush=True)
    clips.append(film.render_outro(folder, show_note=False))
    inputs = []
    for path in clips:
        inputs += ['-i', path]
    filters, current = [], '0:v'
    for i, start in enumerate([s[1] for s in specs[1:]] + [77], 1):
        label = f'join{i}'
        filters.append(f'[{current}][{i}:v]xfade=transition=fade:duration=0.3:offset={start}[{label}]')
        current = label
    filters.append(f'[{current}]trim=duration=84,fade=out:st=83.2:d=0.8,format=yuv420p[v]')
    final = delivery / '星黎-产品介绍-v4.mp4'
    # Preserve the existing 84-second music track byte-for-byte. The capture
    # audio was explicitly waived by the user; no synthesized voices are added.
    film.ffmpeg(*inputs, '-i', backup / 'www/assets/trailer.mp4',
                '-filter_complex', ';'.join(filters), '-map', '[v]', '-map', f'{len(clips)}:a',
                '-t', '84', '-r', '30', '-c:v', 'libx264', '-threads', '4',
                '-preset', 'medium', '-crf', '19', '-c:a', 'copy', '-movflags', '+faststart', final)
    shutil.copy2(final, stage / 'trailer.mp4')
    film.ffmpeg('-ss', '4.2', '-i', final, '-frames:v', '1', '-vf', 'scale=1600:900',
                '-q:v', '2', stage / 'trailer-poster.jpg')
    gallery = gallery_export(stage, work)
    timeline = [{'start': s[1], 'end': s[2], 'section': s[0], 'title': ' '.join(s[5]),
                 'note': s[6], 'source': str(s[3]), 'source_start': s[4]} for s in specs]
    timeline.append({'start': 77, 'end': 84, 'section': 'outro', 'title': '让相遇，成为日常。'})
    report = {'duration_seconds': 84, 'resolution': '1920x1080', 'frame_rate': 30,
              'chapters': CHAPTERS, 'timeline': timeline, 'gallery': gallery,
              'features': {k: plans[k][1] for k in ['outfit', 'scene', 'closeness', 'memory']},
              'startrack': 'Retained reviewed 12-second clip',
              'two_d_meeting': 'Restored per latest correction: fresh 2D cyber cafe, followed by 3D campus and WeChat style; no fake 2D campus',
              'call_status': 'Connecting UI only; not a successful call',
              'audio': 'Original BGM stream retained; no capture audio',
              'overlay_copy': 'Product headlines only; no capture, redaction or review annotations',
              'listening_check': 'NOT_PERFORMED', 'publication': 'LOCAL_REVIEW'}
    (audit / '视频制作记录.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    (work / '时间线.json').write_text(json.dumps(timeline, ensure_ascii=False, indent=2))
    # Publish to the local webroot only after every asset finishes successfully.
    for src in stage.rglob('*'):
        if src.is_file():
            dest = ASSETS / src.relative_to(stage)
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_name(dest.name + '.tmp')
            shutil.copy2(src, tmp)
            tmp.replace(dest)
    for name in ['outfit', 'scene', 'closeness', 'memory', 'startrack']:
        for ext in ['mp4', 'jpg']:
            shutil.copy2(stage / f'{name}.{ext}', delivery / f'星黎-功能-{name}.{ext}')
    shutil.copy2(stage / 'trailer-poster.jpg', delivery / '星黎-产品介绍-v4-封面.jpg')
    print('DONE', final, flush=True)


if __name__ == '__main__':
    main()
