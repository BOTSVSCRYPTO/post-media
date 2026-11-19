import json, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont
# Streamer split-screen: facecam on top (1080x860), gameplay below (1080x1060). Keeps original audio.
W, H = 1080, 1920
FONT = sys.argv[3]

def wrap(d, text, f, maxw):
    out, line = [], ''
    for w in text.split():
        t = (line + ' ' + w).strip()
        if d.textlength(t, font=f) <= maxw: line = t
        else: out.append(line); line = w
    out.append(line); return out

def overlay(path, hook, credit):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 66); lines = wrap(d, hook.upper(), f, W - 120); lh = 74
    y = 860 - (lh * len(lines)) // 2 - 10
    bw = max(d.textlength(l, font=f) for l in lines) + 60
    d.rounded_rectangle([(W - bw) / 2, y - 16, (W + bw) / 2, y - 16 + lh * len(lines) + 26], 22, fill=(0, 0, 0, 200))
    for i, l in enumerate(lines):
        col = (255, 61, 166) if i == len(lines) - 1 else (255, 255, 255)
        d.text(((W - d.textlength(l, font=f)) / 2, y + i * lh), l, font=f, fill=col, stroke_width=4, stroke_fill=(0, 0, 0))
    f2 = ImageFont.truetype(FONT, 44)
    for j, t in enumerate(credit):
        tw = d.textlength(t, font=f2); yy = 1500 + j * 56
        d.rounded_rectangle([(W - tw) / 2 - 18, yy - 6, (W + tw) / 2 + 18, yy + 52], 14, fill=(0, 0, 0, 170))
        d.text(((W - tw) / 2, yy), t, font=f2, fill=(83, 252, 24) if j == 0 else (255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
    f3 = ImageFont.truetype(FONT, 34); tag = '@VICEHEATDAILY'
    d.text(((W - d.textlength(tag, font=f3)) / 2, 1640), tag, font=f3, fill=(255, 255, 255, 190), stroke_width=2, stroke_fill=(0, 0, 0))
    im.save(path)

spec = json.load(open(sys.argv[1])); outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True)
for c in spec:
    out = os.path.join(outdir, c['name'] + '.mp4')
    if os.path.exists(out): continue
    cam = c['cam']  # [x,y,w,h] in 1920x1080 source
    gx = c.get('gx', 410)
    ov = f"/tmp/{c['name']}_ov.png"; overlay(ov, c['hook'], c['credit'])
    fc = (f"[0:v]split[a][b];[a]crop={cam[2]}:{cam[3]}:{cam[0]}:{cam[1]},scale=1080:860,setsar=1[top];"
          f"[b]crop=1100:1080:{gx}:0,scale=1080:1060,setsar=1[bot];[top][bot]vstack[st];[st][1:v]overlay=0:0,format=yuv420p[v];"
          f"[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(c['in']), '-to', str(c['out']), '-i', c['src'], '-i', ov,
                    '-filter_complex', fc, '-map', '[v]', '-map', '[aout]', '-r', '30', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
                    '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-movflags', '+faststart', out], check=True)
    print(out, flush=True)
