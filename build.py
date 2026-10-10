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
    zh, en = (m.group(1).split("|") + [""])[:2]
    q = quote(zh)
    return (
        f'<span class="go"><a class="mapl" href="https://uri.amap.com/search?keyword={q}" target="_blank" rel="noopener">Amap</a>'
        f'<a class="mapl" href="https://maps.apple.com/?q={q}" target="_blank" rel="noopener">Apple Maps</a>'
        f'<button type="button" class="drv" data-zh="{html.escape(zh)}" data-en="{html.escape(en)}">Show driver</button></span>'
    )


src = (root / "template.html").read_text()
out = re.sub(r"\{\{go:([^}]+)\}\}", go, src)
out = re.sub(r"\{\{src:([^}]+)\}\}", src_ref, out)
out = re.sub(r"\{\{fig:([^}]+)\}\}", fig, out)
out = out.replace("{{credits}}", credit_list(None))
(root / "index.html").write_text(out)
print(f"index.html written, {len(used)} photos")
