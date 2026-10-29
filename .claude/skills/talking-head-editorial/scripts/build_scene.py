#!/usr/bin/env python3
"""Assemble <project>/scene.html = engine + timeline, themed by brand.json.

usage: build_scene.py <project_dir> [--timeline timeline.js] [--brand brand.json]
Defaults: <project>/timeline.js and <project>/brand.json (falls back to the skill's default brand).
Fonts named in brand.json are resolved relative to the brand file, then to the skill's assets/.
"""
import json, os, re, shutil, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(SKILL, 'assets')
# engine is authored in the default palette; every occurrence is swapped for the brand value
PALETTE = {'accent': '#DDFF45', 'navy': '#14213D', 'cream': '#F2EDE2', 'ink': '#050505', 'pill': '#1B2A52'}
SLOTS = {'KeySans': 'key_sans', 'KeySerif': 'key_serif', 'Lead': 'lead', 'CardSans': 'card_sans'}


def pace_check(timeline):
    """Warn when the camera breaks the zoom rules (user: zoom too frequent / punchy → slow pushes like talking-head-motion)."""
    src = re.sub(r'//[^\n]*|/\*.*?\*/', '', timeline, flags=re.S)
    if re.search(r'\]\)\s*zoom\(', src): print('WARNING pace: zoom list loop found — write each push as zoom(t, z, dur)')
    pushes = [(float(t), float(z), float(d) if d else 1.2) for t, z, d in
              re.findall(r'\bzoom\(\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+))?\s*\)', src)]
    ins = [p for p in pushes if p[1] > 1.001]
    if len(ins) > 5: print(f'WARNING pace: {len(ins)} zoom push-ins (max 4–5 per clip) — keep only the strongest sentences')
    for t, z, d in ins:
        if d < .8: print(f'WARNING pace: zoom({t}, {z}, {d}) is a snap — use dur 1–1.5')
        if z > 1.08: print(f'WARNING pace: zoom({t}, {z}) — use 1.04–1.06, never above 1.08')
        near = [u for u, y, _ in ins if 0 < u - t < 4]
        if near: print(f'WARNING pace: zoom push-ins at {t} and {near[0]} are < 4 s apart')


def main():
    args = sys.argv[1:]
    if not args: sys.exit(__doc__)
    proj = os.path.abspath(args[0])
    opt = dict(zip(args[1::2], args[2::2]))
    tl = opt.get('--timeline', os.path.join(proj, 'timeline.js'))
    bp = opt.get('--brand', os.path.join(proj, 'brand.json'))
    if not os.path.exists(bp): bp = os.path.join(ASSETS, 'brand.default.json')
    brand = json.load(open(bp))
    pace_check(open(tl).read())
    html = open(os.path.join(ASSETS, 'engine_head.html')).read() + '\n' + open(tl).read() + '\n' + open(os.path.join(ASSETS, 'engine_tail.html')).read()

    os.makedirs(os.path.join(proj, 'fonts'), exist_ok=True)
    for fam, slot in SLOTS.items():
        src = brand['fonts'][slot]
        for base in (os.path.dirname(os.path.abspath(bp)), ASSETS):
            cand = os.path.join(base, src)
            if os.path.exists(cand): break
        else:
            sys.exit(f'font not found for {slot}: {src}')
        dst = os.path.join('fonts', os.path.basename(cand))
        out = os.path.join(proj, dst)
        if not (os.path.exists(out) and os.path.samefile(cand, out)): shutil.copy(cand, out)   # brand.json inside the project already points here
        html = re.sub(r'(@font-face\{font-family:"%s";src:url\()[^)]*(\))' % fam, r'\g<1>%s\2' % dst, html)

    for key, default in PALETTE.items():
        html = re.sub(re.escape(default), brand.get(key, default), html, flags=re.I)
    open(os.path.join(proj, 'scene.html'), 'w').write(html)
    json.dump(brand, open(os.path.join(proj, '.brand.used.json'), 'w'), ensure_ascii=False, indent=1)
    print('built', os.path.join(proj, 'scene.html'))


if __name__ == '__main__':
    main()
