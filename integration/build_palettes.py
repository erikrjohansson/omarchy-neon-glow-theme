#!/usr/bin/python
"""Build complete palettes using installed Omarchy templates, without changing the desktop."""
from pathlib import Path
import colorsys, hashlib, json, math, os, re, shutil, subprocess, tempfile, tomllib
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'source/emerald-base'
# Readable UI accents derived from the wallpaper colors, rather than emissive white cores.
VARIANTS = {
 'cyberpunk': ('#61e6ff','#ff66cf'),
 'emerald': ('#91ff70','#2d9b58'), 'orchid': ('#e49aff','#ac55d5'),
 'gold': ('#ffd166','#e6a02f'),
 'ice-white': ('#e4f1ff','#a5c8ef'),
 'hot-coral': ('#ff967e','#f35b59'),
 'red-white-blue': ('#71b7ff','#ff7184'),
}
# Yaru folder colour nearest each accent's hue (plain Yaru is orange).
ICONS = {
 'emerald': 'Yaru-olive', 'orchid': 'Yaru-magenta', 'gold': 'Yaru-yellow',
 'ice-white': 'Yaru-blue',
 'hot-coral': 'Yaru', 'cyberpunk': 'Yaru-blue',
 'red-white-blue': 'Yaru-blue',
}
def rgb(hex): return tuple(int(hex[i:i+2],16)/255 for i in (1,3,5))
def hexrgb(values): return '#'+''.join(f'{round(max(0,min(1,x))*255):02x}' for x in values)
def mix(a,b,t): return hexrgb([x*(1-t)+y*t for x,y in zip(rgb(a),rgb(b))])
def hue_distance(a,b): d=abs(a-b)%360; return min(d,360-d)
def hue(hex): return colorsys.rgb_to_hsv(*rgb(hex))[0]*360
def chroma(hex): return colorsys.rgb_to_hsv(*rgb(hex))[1]
def luminance(hex):
    lin=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb(hex)]
    return .2126*lin[0]+.7152*lin[1]+.0722*lin[2]
# Palettes are built in OKLCH with a fixed lightness per terminal slot, so
# every colour reads equally well on the background.
# Colour by role: the palette's own colour(s) are the only strong colours,
# red (errors) and yellow (warnings) stay clear, and the remaining slots are
# soft tints that are still told apart by hue.
ROLE_CHROMA = {'own': .15, 'red': .13, 'yellow': .105, 'quiet': .075}
# Set identity without colouring everything: the background carries a light
# tint of the palette's hue, and the soft slots lean towards its colour.
BG_TINT = .018
QUIET_CAST = .18
# Eye comfort: a lifted background, dimmer text and a narrow lightness range,
# so nothing glares on the dark background.
BG_LIGHTNESS = .17
TEXT_LIGHTNESS = .84
BORDER_STRENGTH = .60
# OKLCH lightness of red, green, yellow, blue, magenta and cyan.
SLOT_LIGHTNESS = [.72, .80, .86, .72, .75, .80]
SLOT_HUES = {'red': 22, 'green': 145, 'yellow': 95, 'blue': 258, 'magenta': 330, 'cyan': 205}
def _linear(v): return v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4
def hex_oklch(hex):
    r,g,b=[_linear(c) for c in rgb(hex)]
    l=(.4122214708*r+.5363325363*g+.0514459929*b)**(1/3)
    m=(.2119034982*r+.6806995451*g+.1073969566*b)**(1/3)
    s=(.0883024619*r+.2817188376*g+.6299787005*b)**(1/3)
    L=.2104542553*l+.7936177850*m-.0040720468*s
    A=1.9779984951*l-2.4285922050*m+.4505937099*s
    B=.0259040371*l+.7827717662*m-.8086757660*s
    return L, math.hypot(A,B), (math.degrees(math.atan2(B,A))+360)%360
def _oklch_linear(L,C,h):
    h=math.radians(h); a,b=C*math.cos(h),C*math.sin(h)
    l=(L+.3963377774*a+.2158037573*b)**3
    m=(L-.1055613458*a-.0638541728*b)**3
    s=(L-.0894841775*a-1.291485548*b)**3
    return [4.0767416621*l-3.3077115913*m+.2309699292*s,
            -1.2684380046*l+2.6097574011*m-.3413193965*s,
            -.0041960863*l-.7034186147*m+1.707614701*s]
def oklch(L,C,h):
    """OKLCH to hex. Chroma drops until the colour fits in sRGB."""
    rgb_=_oklch_linear(L,C,h)
    while C>0 and any(v<-.001 or v>1.001 for v in rgb_):
        C-=.005; rgb_=_oklch_linear(L,C,h)
    return hexrgb([12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055 for v in (min(1,max(0,v)) for v in rgb_)])
def contrast(a,b):
    x,y=sorted((luminance(a),luminance(b)))
    return (y+.05)/(x+.05)
def oklch_palette(neon, second, multicolor):
    _,neon_c,neon_h=hex_oklch(neon)
    _,_,second_h=hex_oklch(second)
    grey = neon_c < .05  # Ice White: pale pastels instead of neon
    hues = dict(SLOT_HUES)
    order=['red','green','yellow','blue','magenta','cyan']
    scale = .7 if grey else 1.0
    # The palette's colour is the accent. In Neovim (aether) it colours the
    # keywords through bright_magenta, the most frequent coloured token, so
    # each set is recognisable in code. The six normal slots keep their true
    # hues, so strings, functions, errors and diffs read the same everywhere.
    accent = oklch(.78, ROLE_CHROMA['own']*scale, 250 if grey else neon_h)
    # Two-colour sets: the second colour takes the blue slot at full strength,
    # which Neovim uses for function names (and ls for directories), the next
    # most frequent token after keywords.
    second_slot = None
    if multicolor:
        second_slot = 'blue'
        hues[second_slot] = second_h
    bh, bl, bc = neon_h, BG_LIGHTNESS, (.010 if grey else BG_TINT)
    def chroma_for(k):
        role = 'own' if k == second_slot else k if k in ('red','yellow') else 'quiet'
        return ROLE_CHROMA[role]*scale
    def cast(colour,k):
        return colour if k in (second_slot, 'red', 'yellow') else mix(colour,accent,QUIET_CAST)
    normal=[cast(oklch(SLOT_LIGHTNESS[i],chroma_for(k),hues[k]),k) for i,k in enumerate(order)]
    bright=[cast(oklch(min(.92,SLOT_LIGHTNESS[i]+.07),chroma_for(k)*.75,hues[k]),k) for i,k in enumerate(order)]
    bg=oklch(bl,bc,bh); fg=oklch(TEXT_LIGHTNESS,.005,bh)
    # Muted carries comments and hints, so it lightens until it reaches 4.5:1.
    muted_l=.5
    while contrast(oklch(muted_l,bc+.01,bh),bg)<4.5 and muted_l<1: muted_l+=.005
    c=[oklch(bl+.06,bc,bh),*normal,oklch(TEXT_LIGHTNESS-.08,.006,bh),oklch(muted_l,bc+.01,bh),*bright,oklch(TEXT_LIGHTNESS+.07,.004,bh)]
    red,yellow=hex_oklch(c[1]),hex_oklch(c[3])
    dh=(yellow[2]-red[2]+180)%360-180
    orange=oklch((red[0]+yellow[0])/2,(red[1]+yellow[1])/2,red[2]+dh/2)
    second=c[1+order.index(second_slot)] if multicolor else accent
    # The focused border sits part-way into the background so it doesn't glare.
    border=lambda colour: mix(bg,colour,BORDER_STRENGTH)
    # Unfocused border: the accent faded to about 2:1 on the background, so it
    # pairs with the focused one (same hue, clearly dimmer).
    t=0.
    while contrast(mix(bg,accent,t),bg)<2.0 and t<1: t+=.01
    inactive=mix(bg,accent,t)
    return (second_slot or 'accent'), {
        'accent': accent, 'selection': mix(bg,accent,.28), 'muted': c[8],
        'background': bg, 'dark_background': mix(bg,'#000000',.25),
        'darker_background': mix(bg,'#000000',.5), 'lighter_background': c[0],
        'foreground': fg, 'dark_foreground': mix(fg,bg,.35),
        'light_foreground': c[7], 'bright_foreground': c[15],
        # Two-colour sets show both colours in the border; the others stay one colour.
        'hyprland_active_border': f'rgba({border(second)[1:]}ee) rgba({border(accent)[1:]}ee) 45deg' if multicolor else f'rgba({border(accent)[1:]}ee)',
        'hyprland_inactive_border': f'rgba({inactive[1:]}ee)',
        'red': c[1], 'yellow': c[3], 'orange': orange, 'green': c[2], 'cyan': c[6],
        'blue': c[4], 'magenta': c[5], 'brown': mix(orange,'#000000',.5),
        # cliamp's default theme only uses 9 (errors, peaks), 10 (title, playing,
        # low spectrum) and 11 (seek bar, mid spectrum). Give 10 and 11 the
        # palette's own colours so cliamp changes with the set; 9 stays red.
        # bright_yellow is also Neovim's constants.
        'bright_red': c[9], 'bright_green': accent,
        'bright_yellow': second if multicolor else mix(accent,'#ffffff',.25),
        'bright_cyan': c[14], 'bright_blue': c[12], 'bright_magenta': accent,
    }
base_colors=tomllib.loads((BASE/'colors.toml').read_text())
files=[p for p in BASE.iterdir() if p.is_file() and (p.suffix in ('.toml','.css','.json','.theme'))]
manifest={}
for slug,(accent,secondary) in VARIANTS.items():
    display_name = 'Red, White & Blue' if slug == 'red-white-blue' else slug.replace('-', ' ').title()
    multicolor = slug in ('cyberpunk', 'red-white-blue')
    second_slot, palette = oklch_palette(accent, secondary, multicolor)
    accent, secondary = palette['accent'], palette[second_slot]
    background = palette['background']
    replacements = {}
    for p in files:
        for color in re.findall(r'#[0-9a-fA-F]{6}', p.read_text()):
            h, saturation, value = colorsys.rgb_to_hsv(*rgb(color))
            if saturation > .015:
                tone = secondary if multicolor and (h < .18 or h > .75) else accent
                # Theme any extra app-specific colors, not just colors.toml roles.
                replacements[color.lower()] = mix(tone, '#ffffff', (1-saturation)*.65)
    replacements.update({base_colors[key]: value for key, value in palette.items()})
    replacements.update({
        '#b9eda8': palette['foreground'],
        '#0b120d': mix(background, '#ffffff', .04), '#2d9b58': secondary,
        # Keep these dim: the tint above ignores lightness. Destructive buttons
        # put light text on error_red; a placeholder must read dimmer than input.
        '#a63743': mix(background, palette['red'], .40),
        '#949e94': palette['muted'],
    })
    target=ROOT/'palettes'/slug
    target.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='neon-glow-build-') as temp:
        home=Path(temp); stage=home/'.local/state/omarchy/current/next-theme'
        stage.mkdir(parents=True)
        user_templates=Path.home()/'.config/omarchy/themed'
        if user_templates.exists():
            shutil.copytree(user_templates,home/'.config/omarchy/themed')
        for p in files:
            text=re.sub(r'#[0-9a-fA-F]{6}',lambda m: replacements.get(m[0].lower(),m[0]),p.read_text())
            text=text.replace('Emerald Glow',f'Neon Glow — {display_name}')
            if p.name=='icons.theme':
                text=ICONS[slug]+'\n'
            if p.name.startswith('shell.'):
                text=re.sub(r'(selected-background\s*=\s*)"#[0-9a-fA-F]{6}"', lambda m: m[1] + '"' + accent + '"', text)
            if p.name == 'gtk.css':
                text=re.sub(r'@define-color accent_light #[0-9a-fA-F]{6};', '@define-color accent_light ' + mix(accent, '#ffffff', .30) + ';', text)
            (stage/p.name).write_text(text)
        env=os.environ|{'HOME':str(home),'OMARCHY_PATH':'/usr/share/omarchy','PATH':'/usr/share/omarchy/bin:/usr/bin:/bin'}
        subprocess.run(['/usr/share/omarchy/bin/omarchy-theme-set-templates'],env=env,check=True,capture_output=True)
        for p in stage.iterdir():
            if p.is_file(): shutil.copy2(p,target/p.name)
    digest=hashlib.sha256(b''.join(p.name.encode()+p.read_bytes() for p in sorted(target.iterdir()) if p.is_file() and p.name!='neon-glow-variant')).hexdigest()
    (target/'neon-glow-variant').write_text(slug+' '+digest+'\n')
    manifest[slug]={'accent':accent,'secondary':secondary,'backgrounds':[p.name for p in sorted((ROOT/'backgrounds').glob('*.png'))
        if re.fullmatch(rf'\d\d-{re.escape(slug)}-wordmark-4k\.png', p.name)]}
    assert len(manifest[slug]['backgrounds'])==1
    print('Built',slug,flush=True)
(ROOT/'palettes.json').write_text(json.dumps(manifest,indent=2)+'\n')

# The initial Neon Glow appearance uses Cyberpunk, the first wallpaper.
for source in files:
    shutil.copy2(ROOT/'palettes/cyberpunk'/source.name, ROOT/source.name)
