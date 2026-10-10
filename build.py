"""Expands {{fig:slug|alt|caption}}, {{go:中文|English}} and {{credits}} in template.html into index.html."""
import html, json, re
from pathlib import Path
from urllib.parse import quote

root = Path(__file__).parent
credits = json.loads((root / "img/credits.json").read_text())
used = []


def fig(m):
    slug, alt, cap = (m.group(1).split("|") + ["", ""])[:3]
    cls = ""
    if ":" in slug:
        slug, cls = slug.split(":", 1)
    c = credits[slug]
    if slug not in used:
        used.append(slug)
    cap_html = f'<figcaption>{cap}</figcaption>' if cap else ""
    return (
        f'<figure class="ph {cls}"><a href="img/{slug}.jpg" data-cap="{html.escape(cap or alt)}" '
        f'data-credit="{html.escape(c["artist"])} · {html.escape(c["license"])}">'
        f'<img src="img/{slug}-sm.jpg" srcset="img/{slug}-sm.jpg 900w, img/{slug}.jpg 1800w" '
        f'sizes="(max-width:720px) 100vw, 50vw" alt="{html.escape(alt)}" loading="lazy" decoding="async"></a>'
        f"{cap_html}</figure>"
    )


def credit_list(_):
    rows = []
    for slug in used:
        c = credits[slug]
        lic = f'<a href="{c["licenseUrl"]}">{c["license"]}</a>' if c["licenseUrl"] else c["license"]
        name = html.escape(c["title"].rsplit(".", 1)[0])
        rows.append(f'<li><a href="{c["page"]}">{name}</a> — {html.escape(c["artist"]) or "Unknown"}, {lic}</li>')
    return "\n".join(rows)


def src_ref(m):
    slug = m.group(1)
    if slug not in used:
        used.append(slug)
    return f"img/{slug}"


def go(m):
    """{{go:中文名|English name}} -> map links and a show-the-driver button."""
    return go_html(*(m.group(1).split("|") + [""])[:2])


def go_html(zh, en):
    q = quote(zh)
    return (
        f'<span class="go"><a class="mapl" href="https://uri.amap.com/search?keyword={q}" target="_blank" rel="noopener">Amap</a>'
        f'<a class="mapl" href="https://maps.apple.com/?q={q}" target="_blank" rel="noopener">Apple Maps</a>'
        f'<button type="button" class="drv" data-zh="{html.escape(zh)}" data-en="{html.escape(en)}">Show driver</button></span>'
    )


TYPES = {"stay": "Stay", "do": "Do", "eat": "Eat", "shop": "Shop", "rest": "Rest", "watch": "Watch", "tip": "Getting there"}
CLS = {"stay": "t-stay", "do": "t-do", "eat": "t-eat", "shop": "t-shop", "rest": "t-drink", "watch": "t-watch", "tip": "t-tip"}
areas = json.loads((root / "places.json").read_text())


def area_nav():
    return "".join(f'<a href="#{a["id"]}">{html.escape(a["name"])}</a>' for a in areas)


def place_list():
    """places.json -> one collapsible block per area, planned stops first, backups after."""
    out = []
    for a in areas:
        rows = []
        for kind, name, zh, tag, note in sorted(a["items"], key=lambda i: i[3] == "Backup"):
            bk = " bk" if tag == "Backup" else ""
            tag_txt = "Backup" if bk else html.escape(tag)
            rows.append(
                f'<li class="{CLS[kind]}"><span class="pt">{TYPES[kind]}</span><b>{html.escape(name)}<span class="zh">{html.escape(zh)}</span></b>'
                f'<span class="tag{bk}">{tag_txt}</span>' + (f"<p>{html.escape(note)}</p>" if note else "") + go_html(zh, name) + "</li>"
            )
        sub = f'<span>{html.escape(a["zh"])}{" · " + html.escape(a["sub"]) if a["sub"] else ""}</span>'
        out.append(f'<details class="area" id="{a["id"]}"><summary><h3>{html.escape(a["name"])}</h3>{sub}</summary><ul class="pl">{"".join(rows)}</ul></details>')
    return "\n".join(out)


src = (root / "template.html").read_text()
src = src.replace("{{areanav}}", area_nav()).replace("{{places}}", place_list())
out = re.sub(r"\{\{go:([^}]+)\}\}", go, src)
out = re.sub(r"\{\{src:([^}]+)\}\}", src_ref, out)
out = re.sub(r"\{\{fig:([^}]+)\}\}", fig, out)
out = out.replace("{{credits}}", credit_list(None))
(root / "index.html").write_text(out)
print(f"index.html written, {len(used)} photos")
