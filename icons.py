"""Kitty Escape icon set: small cartoon glyphs on glossy 'glass' tiles (hand-written SVG, no libraries).

icon(name)      -> <img> tag with the SVG as a data URI (safe to use many times on one page)
icon_uri(name)  -> the data URI itself (for CSS backgrounds)
"""
import base64

# (light, deep) gradient pairs
PALETTE = {
    "blue": ("#8FDCFF", "#0EA5E9"), "purple": ("#D2C4FF", "#7C3AED"), "green": ("#9AF0B8", "#16A34A"),
    "orange": ("#FFC58A", "#F97316"), "red": ("#FFB0B0", "#E11D48"), "pink": ("#FFB8DD", "#EC4899"),
    "teal": ("#8AF0DF", "#0D9488"), "yellow": ("#FFE38A", "#F59E0B"), "slate": ("#B8C4D6", "#475569"),
    "navy": ("#7FB2E0", "#123F63"),
}

W = "#FFFFFF"
S = f"stroke='{W}' stroke-width='3.2' stroke-linecap='round' stroke-linejoin='round' fill='none'"


def _cat(eyes, deep, extra=""):
    return (f"<path d='M13 34 L13 16 L19.5 21 Q24 19.3 28.5 21 L35 16 L35 34 Q35 38 31 38 L17 38 Q13 38 13 34Z' fill='{W}'/>"
            + eyes + f"<path d='M22.6 30.2 L24 31.6 L25.4 30.2' stroke='{deep}' stroke-width='1.6' fill='none' "
            f"stroke-linecap='round' stroke-linejoin='round'/>"
            f"<ellipse cx='17.6' cy='32' rx='2' ry='1.2' fill='#FFB3C7'/><ellipse cx='30.4' cy='32' rx='2' ry='1.2' fill='#FFB3C7'/>"
            + extra)


def _glyph(name, deep):
    d = deep
    g = {
        "home": f"<path d='M13 24 L24 14.5 L35 24' {S}/><path d='M16.5 22 V34 H31.5 V22' {S}/>"
                f"<rect x='21' y='26.5' width='6' height='7.5' rx='2' fill='{W}'/>",
        "compass": f"<circle cx='24' cy='25' r='11' {S}/><path d='M24 15.5 L27.6 25 L20.4 25Z' fill='{W}'/>"
                   f"<path d='M24 34.5 L27.6 25 L20.4 25Z' fill='{W}' opacity='.55'/><circle cx='24' cy='25' r='1.8' fill='{d}'/>",
        "flame": f"<path d='M24 13 C26 19 33 21 33 29 C33 34.5 29 38 24 38 C19 38 15 34.5 15 29.5 C15 25 18 23 19.5 19.5 "
                 f"C20.5 23 22 24 23 24 C22 20 22.5 16 24 13Z' fill='{W}'/>"
                 f"<path d='M24 26 C25.5 29 28.5 30 28.5 33 C28.5 35.5 26.5 37 24 37 C21.5 37 19.5 35.5 19.5 33 "
                 f"C19.5 30.5 22.5 29.5 24 26Z' fill='#FFD166'/>",
        "chart": f"<rect x='13.5' y='26' width='6' height='10' rx='2.4' fill='{W}' opacity='.75'/>"
                 f"<rect x='21' y='19' width='6' height='17' rx='2.4' fill='{W}'/>"
                 f"<rect x='28.5' y='14' width='6' height='22' rx='2.4' fill='{W}' opacity='.9'/>",
        "book": f"<path d='M24 18 C20.5 15.5 16.5 15 13 15.5 V33.5 C16.5 33 20.5 33.5 24 36 Z' fill='{W}'/>"
                f"<path d='M24 18 C27.5 15.5 31.5 15 35 15.5 V33.5 C31.5 33 27.5 33.5 24 36 Z' fill='{W}' opacity='.75'/>",
        "cat": _cat(f"<circle cx='19.6' cy='27' r='2' fill='{d}'/><circle cx='28.4' cy='27' r='2' fill='{d}'/>"
                    f"<circle cx='20.2' cy='26.4' r='.7' fill='{W}'/><circle cx='29' cy='26.4' r='.7' fill='{W}'/>", d),
        "cat_happy": _cat(f"<path d='M17.6 27.5 Q19.6 24.6 21.6 27.5' stroke='{d}' stroke-width='1.9' fill='none' stroke-linecap='round'/>"
                          f"<path d='M26.4 27.5 Q28.4 24.6 30.4 27.5' stroke='{d}' stroke-width='1.9' fill='none' stroke-linecap='round'/>",
                          d, f"<path d='M36.5 13 l1 2.4 2.4 1 -2.4 1 -1 2.4 -1 -2.4 -2.4 -1 2.4 -1Z' fill='{W}'/>"),
        "cat_hurt": _cat(f"<path d='M18 25.5 L21.4 28.5 M21.4 25.5 L18 28.5' stroke='{d}' stroke-width='1.8' stroke-linecap='round'/>"
                         f"<path d='M26.6 25.5 L30 28.5 M30 25.5 L26.6 28.5' stroke='{d}' stroke-width='1.8' stroke-linecap='round'/>",
                         d, f"<rect x='27.5' y='14.5' width='10' height='4.6' rx='2.3' transform='rotate(-30 32.5 16.8)' fill='#FDE7C8' "
                            f"stroke='{d}' stroke-width='1'/>"),
        "sensor": f"<circle cx='24' cy='30' r='7.5' fill='{W}'/><circle cx='24' cy='30' r='2.4' fill='{d}'/>"
                  f"<path d='M17 18.5 Q24 13 31 18.5' {S}/><path d='M20.5 22 Q24 19.3 27.5 22' {S}/>",
        "camera": f"<rect x='12.5' y='18.5' width='23' height='16' rx='5' fill='{W}'/><rect x='19' y='15' width='10' height='5' rx='2' fill='{W}'/>"
                  f"<circle cx='24' cy='26.5' r='5' fill='{d}'/><circle cx='24' cy='26.5' r='2.4' fill='{W}' opacity='.85'/>"
                  f"<circle cx='31.5' cy='22' r='1.3' fill='{d}'/>",
        "search": f"<circle cx='22' cy='23' r='7.5' {S}/><path d='M27.5 28.5 L34 35' {S}/><circle cx='22' cy='23' r='2.6' fill='{W}'/>",
        "route": f"<path d='M16 33 C16 24 32 27 32 17.5' stroke='{W}' stroke-width='3.2' stroke-linecap='round' fill='none' "
                 f"stroke-dasharray='.5 5.2'/><circle cx='16' cy='33.5' r='3.6' fill='{W}'/>"
                 f"<path d='M32 11.5 C35.3 11.5 37 14 37 16.2 C37 19.5 32 24 32 24 C32 24 27 19.5 27 16.2 C27 14 28.7 11.5 32 11.5Z' fill='{W}'/>"
                 f"<circle cx='32' cy='16.3' r='1.9' fill='{d}'/>",
        "scale": f"<path d='M24 14 V36 M17 36 H31 M13.5 18.5 H34.5' {S}/>"
                 f"<path d='M13.5 18.5 L10.5 26 H16.5Z M34.5 18.5 L31.5 26 H37.5Z' fill='{W}' stroke='{W}' stroke-width='1.6' "
                 f"stroke-linejoin='round'/><circle cx='24' cy='14' r='2.2' fill='{W}'/>",
        "target": f"<circle cx='23' cy='26' r='10' {S}/><circle cx='23' cy='26' r='4.6' fill='{W}'/>"
                  f"<path d='M23 26 L34 15' {S}/><path d='M30 13.5 L35.5 12.5 L34.5 18' {S}/>",
        "bolt": f"<path d='M26.5 12 L15.5 27 H23 L21 37 L32.5 21.5 H25 Z' fill='{W}' stroke='{W}' stroke-width='1.6' stroke-linejoin='round'/>",
        "shield": f"<path d='M24 12.5 L34 16.5 V24 C34 30.5 29.5 35 24 37 C18.5 35 14 30.5 14 24 V16.5Z' fill='{W}'/>"
                  f"<path d='M19.5 24.5 L22.8 27.8 L28.8 21.5' stroke='{d}' stroke-width='2.8' stroke-linecap='round' "
                  f"stroke-linejoin='round' fill='none'/>",
        "hourglass": f"<path d='M16 13.5 H32 M16 36.5 H32' {S}/>"
                     f"<path d='M18 14 C18 21 24 22 24 25 C24 28 18 29 18 36 H30 C30 29 24 28 24 25 C24 22 30 21 30 14Z' fill='{W}' opacity='.45'/>"
                     f"<path d='M20.5 36 C20.5 31.5 24 31 24 29 C24 31 27.5 31.5 27.5 36Z' fill='{W}'/>"
                     f"<path d='M20.5 17.5 H27.5 C27 20 24.6 21 24 22.5 C23.4 21 21 20 20.5 17.5Z' fill='{W}'/>",
        "check": f"<path d='M15 25 L21.5 31.5 L33.5 18.5' stroke='{W}' stroke-width='4.2' stroke-linecap='round' stroke-linejoin='round' fill='none'/>",
        "cross": f"<path d='M17 18 L31 32 M31 18 L17 32' stroke='{W}' stroke-width='4.2' stroke-linecap='round'/>",
        "dice": f"<rect x='13' y='14' width='22' height='22' rx='6.5' fill='{W}'/>"
                + "".join(f"<circle cx='{x}' cy='{y}' r='2.1' fill='{d}'/>" for x, y in
                          ((18.5, 19.5), (29.5, 19.5), (24, 25), (18.5, 30.5), (29.5, 30.5))),
        "bulb": f"<path d='M24 12.5 C29.5 12.5 33 16.5 33 21.2 C33 25 30.5 26.8 29.5 29 H18.5 C17.5 26.8 15 25 15 21.2 "
                f"C15 16.5 18.5 12.5 24 12.5Z' fill='{W}'/><rect x='19' y='30.8' width='10' height='3.2' rx='1.6' fill='{W}'/>"
                f"<rect x='20.5' y='35.2' width='7' height='2.8' rx='1.4' fill='{W}' opacity='.8'/>"
                f"<path d='M21.5 22 Q24 25 26.5 22' stroke='{d}' stroke-width='1.8' fill='none' stroke-linecap='round'/>",
        "plus": f"<path d='M24 15 V35 M14 25 H34' stroke='{W}' stroke-width='4.2' stroke-linecap='round'/>",
        "reset": f"<path d='M32.5 21 A9.5 9.5 0 1 0 33.5 28' {S}/><path d='M33.5 14.5 V21.5 H26.5' {S}/>",
        "steps": f"<ellipse cx='18.5' cy='29' rx='3.6' ry='5.2' fill='{W}'/><ellipse cx='29.5' cy='20' rx='3.6' ry='5.2' fill='{W}'/>"
                 f"<circle cx='18.5' cy='36.2' r='1.8' fill='{W}'/><circle cx='29.5' cy='27.2' r='1.8' fill='{W}'/>",
        "pause": f"<rect x='16.5' y='15.5' width='5.5' height='19' rx='2.6' fill='{W}'/><rect x='26' y='15.5' width='5.5' height='19' rx='2.6' fill='{W}'/>",
        "block": f"<rect x='12' y='19' width='24' height='9' rx='3' fill='{W}'/>"
                 f"<path d='M16 19 L13 28 M23 19 L20 28 M30 19 L27 28' stroke='{d}' stroke-width='2.4' stroke-linecap='round'/>"
                 f"<path d='M16 28 V36 M32 28 V36' {S}/>",
        "brain": f"<rect x='14.5' y='15.5' width='19' height='19' rx='5' fill='{W}'/>"
                 f"<path d='M19 12 V15.5 M24 12 V15.5 M29 12 V15.5 M19 34.5 V38 M24 34.5 V38 M29 34.5 V38 "
                 f"M11 20 H14.5 M11 25 H14.5 M11 30 H14.5 M33.5 20 H37 M33.5 25 H37 M33.5 30 H37' "
                 f"stroke='{W}' stroke-width='2.4' stroke-linecap='round'/>"
                 f"<path d='M19.5 25 H22 L23.5 21.5 L25.5 28.5 L27 25 H28.5' stroke='{d}' stroke-width='2' fill='none' "
                 f"stroke-linecap='round' stroke-linejoin='round'/>",
        "badge": f"<path d='M24 12 L27.4 14.6 L31.6 14.4 L32.8 18.5 L36.2 21 L34.8 25 L36.2 29 L32.8 31.5 L31.6 35.6 "
                 f"L27.4 35.4 L24 38 L20.6 35.4 L16.4 35.6 L15.2 31.5 L11.8 29 L13.2 25 L11.8 21 L15.2 18.5 L16.4 14.4 L20.6 14.6Z' fill='{W}'/>"
                 f"<path d='M19 25 L22.5 28.5 L29 21.5' stroke='{d}' stroke-width='2.8' fill='none' stroke-linecap='round' "
                 f"stroke-linejoin='round'/>",
        "exit": f"<rect x='14' y='13' width='14' height='24' rx='3' fill='{W}' opacity='.55'/>"
                f"<path d='M14 13 L24 15.5 V38 L14 36Z' fill='{W}'/><circle cx='21.5' cy='26' r='1.3' fill='{d}'/>"
                f"<path d='M29 25 H37 M33.5 21 L37 25 L33.5 29' {S}/>",
        "play": f"<path d='M19 15 L34 25 L19 35Z' fill='{W}' stroke='{W}' stroke-width='2' stroke-linejoin='round'/>",
        "next": f"<path d='M14 25 H33 M27 18.5 L33.5 25 L27 31.5' {S}/>",
        "back": f"<path d='M34 25 H15 M21 18.5 L14.5 25 L21 31.5' {S}/>",
        "clock": f"<circle cx='24' cy='25' r='11' {S}/><path d='M24 18.5 V25 L28.5 28' {S}/>",
        "sparkle": f"<path d='M22 13 L24.6 21.4 L33 24 L24.6 26.6 L22 35 L19.4 26.6 L11 24 L19.4 21.4Z' fill='{W}'/>"
                   f"<path d='M33 12 L34.2 15.8 L38 17 L34.2 18.2 L33 22 L31.8 18.2 L28 17 L31.8 15.8Z' fill='{W}' opacity='.85'/>",
        "map": f"<path d='M12 17 L20 14 L28 17 L36 14 V33 L28 36 L20 33 L12 36Z' fill='{W}' opacity='.55'/>"
               f"<path d='M20 14 V33 L28 36 V17Z' fill='{W}'/>",
    }
    return g[name]


# default colour for each icon
DEFAULT_COLOUR = {
    "home": "blue", "compass": "purple", "flame": "orange", "chart": "green", "book": "teal", "cat": "pink",
    "cat_happy": "green", "cat_hurt": "red", "sensor": "slate", "camera": "orange", "search": "blue",
    "route": "green", "scale": "orange", "target": "purple", "bolt": "green", "shield": "orange",
    "hourglass": "blue", "check": "green", "cross": "red", "dice": "purple", "bulb": "yellow", "plus": "blue",
    "reset": "slate", "steps": "teal", "pause": "blue", "block": "red", "brain": "purple", "badge": "green",
    "exit": "green", "play": "purple", "next": "blue", "back": "slate", "clock": "teal", "sparkle": "yellow",
    "map": "teal",
}
NAMES = list(DEFAULT_COLOUR)


def icon_svg(name, colour=None):
    light, deep = PALETTE[colour or DEFAULT_COLOUR[name]]
    uid = f"{name}{light[1:]}"
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'>"
        f"<defs><linearGradient id='g{uid}' x1='0' y1='0' x2='1' y2='1'>"
        f"<stop offset='0' stop-color='{light}'/><stop offset='1' stop-color='{deep}'/></linearGradient>"
        f"<linearGradient id='h{uid}' x1='0' y1='0' x2='0' y2='1'>"
        "<stop offset='0' stop-color='#fff' stop-opacity='.75'/><stop offset='1' stop-color='#fff' stop-opacity='0'/>"
        "</linearGradient></defs>"
        f"<rect x='4' y='6.5' width='40' height='39' rx='14' fill='{deep}' opacity='.28'/>"
        f"<rect x='3' y='3' width='42' height='41' rx='14' fill='url(#g{uid})'/>"
        f"<rect x='3.7' y='3.7' width='40.6' height='39.6' rx='13.3' fill='none' stroke='#fff' stroke-opacity='.6' stroke-width='1.3'/>"
        f"<path d='M10 6.5 H38 Q41.5 6.5 41.5 10 V14 Q24 22 6.5 14 V10 Q6.5 6.5 10 6.5Z' fill='url(#h{uid})' opacity='.75'/>"
        f"<g filter='none'>{_glyph(name, deep)}</g>"
        "</svg>"
    )


def icon_uri(name, colour=None):
    return "data:image/svg+xml;base64," + base64.b64encode(icon_svg(name, colour).encode()).decode()


def icon(name, size=40, colour=None, style=""):
    return (f"<img src='{icon_uri(name, colour)}' width='{size}' height='{size}' alt='' "
            f"style='vertical-align:middle;flex:none;{style}'/>")
