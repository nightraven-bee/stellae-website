#!/usr/bin/env python3
"""Check actual media, retained UI code, asset references and local delivery."""
import concurrent.futures
import hashlib
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import cv2
import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
WORK = Path('/Users/ct/Desktop/星黎项目/星黎OS/官网素材/官网更新-20261024')
WEB = REPO / 'www'
BACKUP = WORK / '回退-089aa55/www'
AUDIT = WORK / '核查'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


class Structure(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tokens, self.inline, self.assets = [], [], []
        self.special = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tokens.append(('start', tag, attrs))
        attr = dict(attrs)
        for key in ['src', 'href']:
            value = attr.get(key, '')
            if value and not value.startswith(('#', 'http', 'data:', 'mailto:')):
                self.assets.append(value.split('?')[0])
        if tag in ['script', 'style']:
            self.special = tag

    def handle_endtag(self, tag):
        self.tokens.append(('end', tag))
        if tag == self.special:
            self.special = None

    def handle_data(self, data):
        if self.special:
            self.inline.append((self.special, data))


def inspect_media(name, expected_duration):
    p = WEB / 'assets' / (name + '.mp4')
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format',
                                             '-show_streams', '-of', 'json', str(p)]))
    video = next(s for s in info['streams'] if s['codec_type'] == 'video')
    duration = float(info['format']['duration'])
    if expected_duration is not None:
        assert abs(duration-expected_duration) < .04, (name, duration)
    result = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-f', 'null', '-'],
                            capture_output=True, text=True)
    assert result.returncode == 0 and not result.stderr, (name, result.stderr)
    return {'file': str(p.relative_to(REPO)), 'duration': duration,
            'size': [video['width'], video['height']], 'decode': 'PASS', 'sha256': digest(p)}


def inspect_corners(name):
    p = WEB / 'assets' / (name + '.mp4')
    c = cv2.VideoCapture(str(p))
    fps = c.get(cv2.CAP_PROP_FPS)
    y, x = np.mgrid[0:80, 0:80]
    # This narrow diagonal band lies on the opaque bezel, outside its screen.
    # It catches the native white crescent that escaped the earlier small mask.
    band = (x >= 9) & (y >= 9) & (x+y >= 33) & (x+y <= 44)
    checked = leaks = frames = 0
    while True:
        ok, frame = c.read()
        if not ok:
            break
        t = frames / fps
        frames += 1
        if name == 'trailer':
            if t >= 76.9:
                continue
            phone = frame[70:1010, 440:876]
        else:
            phone = frame
        corners = [phone[:80, :80], phone[:80, -80:][:, ::-1],
                   phone[-80:, :80][::-1], phone[-80:, -80:][::-1, ::-1]]
        leaks += sum(int(np.any(np.min(corner[band], axis=1) > 205)) for corner in corners)
        checked += 1
    c.release()
    assert checked and leaks == 0, (name, checked, leaks)
    return {'file': name, 'frames_checked': checked, 'corner_checks': checked*4,
            'white_corner_leaks': leaks}


def main():
    def unchanged_markup(text):
        # Explicitly authorized entry/footer changes are the only structural exclusions.
        text = re.sub(r'<div class="platform-row">.*?</div>', '', text, flags=re.S)
        text = re.sub(r'<dialog id="download-dialog".*?</dialog>', '', text, flags=re.S)
        text = re.sub(r'<a id="public-security".*?</a>', '', text, flags=re.S)
        text = text.replace('src="assets/char-avatar-glasses.jpg" alt="星黎真人版眼镜校服头像" loading="lazy" width="1122" height="1402"', 'src="assets/char-avatar.webp" alt="星黎角色头像" loading="lazy" width="300" height="300"')
        for sheet in ['channel-entry.css', 'media-review.css']:
            text = text.replace(f'  <link rel="stylesheet" href="assets/{sheet}">\n', '')
        return text
    before = Structure(unchanged_markup((BACKUP/'index.html').read_text()))
    after = Structure(unchanged_markup((WEB/'index.html').read_text()))
    full_after = Structure((WEB/'index.html').read_text())
    assert before.tokens == after.tokens, 'Unapproved HTML structure or attributes changed'
    assert before.inline == after.inline, 'Inline scripts/styles changed'
    protected = [p for p in WEB.rglob('*') if p.suffix in ['.js', '.css']
                 and p.name not in ['site-config.js', 'app.js', 'channel-entry.css', 'media-review.css']]
    changed = [str(p.relative_to(WEB)) for p in protected if digest(p) != digest(BACKUP/p.relative_to(WEB))]
    assert not changed, changed
    def unchanged_app(text):
        start = text.index('  const openDownloads =')
        end = text.index('  const heroVideo=', start)
        return text[:start] + text[end:]
    assert unchanged_app((WEB/'app.js').read_text()) == unchanged_app((BACKUP/'app.js').read_text()), 'Non-entry app logic changed'
    html = (WEB/'index.html').read_text()
    assert 'data-platform=' not in html and 'class="platform-row"' not in html
    assert '沪公网安备31011502406956号' in html
    assert 'https://beian.mps.gov.cn/#/query/webSearch?code=31011502406956' in html
    assert digest(WEB/'assets/channel-qrcode.jpg') == digest(Path('/Users/ct/Downloads/qrcode_1792816733132.jpg')), 'QR source modified'
    assert digest(WEB/'assets/char-avatar-glasses.jpg') == digest(Path('/Users/ct/Desktop/星黎素材/00_角色标准设定/星黎真人版-眼镜.jpg')), 'Requested avatar source modified'
    assert 'char-avatar-real.png' not in html and not (WEB/'assets/char-avatar-real.png').exists()
    timeline = json.loads((WORK/'时间线.json').read_text())
    text_checks = []
    for entry in timeline:
        if entry['section'] == 'outro':
            continue
        assert entry['note'] == '', 'An editorial subtitle remains in the timeline'
        overlay = Image.open(WORK/'构建'/f"text-{entry['section']}.png").convert('RGBA')
        assert overlay.getchannel('A').crop((1030,640,1850,720)).getbbox() is None, 'Subtitle pixels remain'
        text_checks.append(entry['section'])
    outro = Image.open(WORK/'构建/outro-text.png').convert('RGBA')
    assert outro.getchannel('A').crop((120,750,1000,810)).getbbox() is None, 'Outro editorial annotation remains'

    node = ('const fs=require("fs"),vm=require("vm");const s={window:{}};'
            'vm.runInNewContext(fs.readFileSync("www/site-config.js","utf8"),s);'
            'console.log(JSON.stringify(s.window.STELLAE_CONFIG))')
    config = json.loads(subprocess.check_output(['node', '-e', node], cwd=REPO))
    assert [f['key'] for f in config['features']] == ['outfit', 'scene', 'closeness', 'memory', 'startrack']
    assert len(config['worldGallery']) == 6 and len(config['memories']) == 3
    assert 'id="download-note"' not in html and '内测开放时间' not in html
    assert '2D' in config['worldGallery'][4]['alt'] and '2D' in config['worldGallery'][5]['alt']
    gallery_alpha = []
    for shot in config['worldGallery']:
        img = cv2.imread(str(WEB/shot['image']), cv2.IMREAD_UNCHANGED)
        assert img.shape[2] == 4
        assert all(img[y,x,3] == 0 for y,x in [(0,0),(0,img.shape[1]-1),(img.shape[0]-1,0),(img.shape[0]-1,img.shape[1]-1)])
        gallery_alpha.append({'file':shot['image'], 'outside_corners':'TRANSPARENT'})
    local_refs = full_after.assets + [f[k] for f in config['features'] for k in ['video', 'poster']]
    local_refs += [s['image'] for s in config['worldGallery']]
    assert all((WEB/path).is_file() for path in local_refs), 'Missing page asset'
    assert digest(WEB/'assets/startrack.mp4') == digest(BACKUP/'assets/startrack.mp4')
    assert digest(WEB/'assets/hero-loop-1080p.mp4') == digest(BACKUP/'assets/hero-loop-1080p.mp4')
    work = [('trailer', 84), ('outfit', 24), ('scene', 16), ('closeness', 18),
            ('memory', 18), ('startrack', 12), ('hero-loop-1080p', None)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        media = list(pool.map(lambda item: inspect_media(*item), work))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        corners = list(pool.map(inspect_corners, ['trailer', 'outfit', 'scene', 'closeness', 'memory']))
    audio = []
    for p in [BACKUP/'assets/trailer.mp4', WEB/'assets/trailer.mp4']:
        audio.append(subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(p),
                                             '-map', '0:a', '-f', 'streamhash',
                                             '-hash', 'sha256', '-']))
    assert audio[0] == audio[1], 'Approved music changed'
    manifest = {str(p.relative_to(WEB)): {'bytes': p.stat().st_size, 'sha256': digest(p)}
                for p in sorted(WEB.rglob('*')) if p.is_file()}
    (REPO/'docs/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    report = {'html_structure': 'UNCHANGED_EXCEPT_AUTHORIZED_BETA_ENTRY_LEGAL_LINK_AND_AVATAR_SOURCE', 'inline_code': 'UNCHANGED',
              'entry_js_only': 'Beta dialog block only; all remaining app.js unchanged',
              'new_css_scope': 'QR dialog, legal footer, gallery outer frame and avatar framing only', 'qr_source_unchanged': True, 'requested_avatar_source_unchanged': True,
              'editorial_subtitles_removed': text_checks, 'outro_annotation_removed': True,
              'protected_css_js_count': len(protected), 'protected_css_js_changed': changed,
              'feature_order': [f['key'] for f in config['features']],
              'gallery_count': 6, 'gallery_alpha': gallery_alpha, 'memory_card_count': 3, 'local_asset_references': 'PASS',
              'media': media, 'corners': corners, 'approved_bgm_decoded_hash': audio[1].decode().strip(),
              'music_unchanged': True, 'listening_check': 'NOT_PERFORMED',
              'publication': 'LOCAL_REVIEW', 'manifest_files': len(manifest)}
    (AUDIT/'媒体与界面保留核查.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({'media': len(media), 'protected_files': len(protected),
                      'corner_frames': sum(x['frames_checked'] for x in corners),
                      'white_corner_leaks': 0, 'manifest_files': len(manifest)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
