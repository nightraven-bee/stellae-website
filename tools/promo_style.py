"""Reuse the approved v2 video artwork; no website UI or animation code lives here."""
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS=1920,1080,30
NIGHT0=(7,10,22)
INK1,INK2,INK3=(238,241,248),(163,172,194),(108,118,145)
VIOLET,VIOLET_DEEP,PINK,TEAL=(163,139,248),(110,79,224),(255,111,177),(25,214,172)
SERIF=str(Path.home()/"Library/Fonts/SourceHanSerifSC-Heavy.otf")
PINGFANG="/System/Library/AssetsV2/com_apple_MobileAsset_Font8/86ba2c91f017a3749571a82f2c6d890ac7ffb2fb.asset/AssetData/PingFang.ttc"
MONO="/System/Library/Fonts/SFNSMono.ttf"
SRC_W,SRC_H=620,1344
PH,PW=940,436
PX,PY,TX=440,70,1030


def serif(s): return ImageFont.truetype(SERIF, s)

def sans(s, w="Regular"): return ImageFont.truetype(PINGFANG, s, index={"Regular": 3, "Medium": 7, "Semibold": 11, "Light": 15}[w])

def mono(s): return ImageFont.truetype(MONO, s)

def radial(size, center, radius, color, alpha):
    layer = Image.new("RGBA", size, color + (0,))
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    steps = 60
    for i in range(steps, 0, -1):
        r = radius * i / steps
        a = int(alpha * 255 * (1 - i / steps) ** 1.6)
        d.ellipse((center[0] - r, center[1] - r, center[0] + r, center[1] + r), fill=a)
    layer.putalpha(m.filter(ImageFilter.GaussianBlur(radius / 12)))
    return layer

def four_star(d, x, y, r, fill):
    k = r * 0.22
    d.polygon([(x, y - r), (x + k, y - k), (x + r, y), (x + k, y + k), (x, y + r), (x - k, y + k), (x - r, y), (x - k, y - k)], fill=fill)

def background(glow_center, with_phone=True, seed=7):
    rng = random.Random(seed)
    im = Image.new("RGBA", (W, H), NIGHT0 + (255,))
    im.alpha_composite(radial((W, H), glow_center, 760, VIOLET_DEEP, 0.42))
    im.alpha_composite(radial((W, H), (1700, 140), 620, PINK, 0.10))
    im.alpha_composite(radial((W, H), (1780, 1020), 420, TEAL, 0.05))
    fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))    # 网格和星点画在独立图层上再叠加，半透明才生效
    d = ImageDraw.Draw(fx)
    for x in range(0, W, 120):                      # 细网格（赛博结构）
        d.line((x, 0, x, H), fill=(163, 172, 194, 9))
    for y in range(0, H, 120):
        d.line((0, y, W, y), fill=(163, 172, 194, 9))
    for _ in range(260):                            # 星点
        x, y = rng.randrange(W), rng.randrange(H)
        a = rng.randint(40, 190); s = rng.choice([1, 1, 1, 2])
        d.ellipse((x, y, x + s, y + s), fill=(238, 241, 248, a))
    for _ in range(7):
        four_star(d, rng.randrange(W), rng.randrange(H), rng.choice([5, 7, 9]), (238, 241, 248, rng.randint(70, 140)))
    im.alpha_composite(fx)
    if with_phone:                                  # 手机外框光晕 + 描边
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).rounded_rectangle((PX - 10, PY - 10, PX + PW + 10, PY + PH + 10), 84, fill=VIOLET + (120,))
        im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(38)))
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(frame).rounded_rectangle((PX - 9, PY - 9, PX + PW + 8, PY + PH + 8), 80, fill=(12, 14, 30, 255))
        ImageDraw.Draw(frame).rounded_rectangle((PX - 9, PY - 9, PX + PW + 8, PY + PH + 8), 80, outline=VIOLET + (110,), width=2)
        im.alpha_composite(frame)
        # 左上品牌
        d = ImageDraw.Draw(im)
        d.text((80, 58), "星黎宇宙", font=serif(28), fill=INK1)
        spaced(d, (212, 66), "STELLAE.AI", mono(18), (128, 138, 165), 3)
    return im

def spaced(d, xy, text, font, fill, spacing):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + spacing
    return x

def grad_text(im, xy, text, font, c1=PINK, c2=VIOLET):
    x, y = xy
    w = int(font.getlength(text)) + 4
    bbox = font.getbbox(text)
    h = bbox[3] + 8
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((0, 0), text, font=font, fill=255)
    g = Image.new("RGBA", (w, h))
    gd = ImageDraw.Draw(g)
    for i in range(w):
        t = i / max(w - 1, 1)
        gd.line((i, 0, i, h), fill=tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3)) + (255,))
    g.putalpha(mask)
    im.alpha_composite(g, (int(x), int(y)))
    return x + font.getlength(text)

def draw_title(im, xy, parts, font):
    x, y = xy
    d = ImageDraw.Draw(im)
    for p in parts:
        if isinstance(p, tuple):
            x = grad_text(im, (x, y), p[0], font)
        else:
            d.text((x, y), p, font=font, fill=INK1); x += font.getlength(p)
