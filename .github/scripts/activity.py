"""Genera un mapa de actividad minimalista (claro y oscuro) a partir de las contribuciones de GitHub."""
import datetime as dt
import json
import os
import sys
import urllib.request

USER = os.environ.get("GH_USER", "hugoopr04")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist"

QUERY = """query($login:String!){user(login:$login){contributionsCollection{
  contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
)
cal = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = cal["weeks"]
total = cal["totalContributions"]
days = [d for w in weeks for d in w["contributionDays"]]
active = sum(1 for d in days if d["contributionCount"] > 0)
best = max((d["contributionCount"] for d in days), default=0)

# Racha actual (días consecutivos hasta hoy/ayer)
streak = 0
for d in reversed(days):
    if d["contributionCount"] > 0:
        streak += 1
    elif streak or d["date"] != days[-1]["date"]:
        break

THEMES = {
    "dark": dict(fg="#f0f6fc", muted="#8b949e", line="#30363d",
                 levels=["#151b23", "#0c2d6b", "#1158c7", "#388bfd", "#79c0ff"]),
    "light": dict(fg="#1f2328", muted="#59636e", line="#d1d9e0",
                  levels=["#eff2f5", "#b6d7ff", "#6cb6ff", "#218bff", "#0550ae"]),
}
SANS = "ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level(n):
    if n == 0:
        return 0
    if best <= 4:
        return min(n, 4)
    return min(4, 1 + int(3 * n / best))


def render(t):
    W, cell, gap = 1200, 16, 4
    ox = (W - (len(weeks) * (cell + gap) - gap)) / 2
    oy = 150
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="320" viewBox="0 0 {W} 320" '
         f'role="img" aria-label="{total} contributions in the last year">']
    stats = [(f"{total:,}", "contributions in the last year"),
             (f"{active}", "active days"),
             (f"{streak}", "current streak (days)")]
    x = ox
    for value, label in stats:
        o.append(f'<text x="{x}" y="64" font-family="{SANS}" font-size="34" font-weight="600" '
                 f'letter-spacing="-1" fill="{t["fg"]}">{value}</text>')
        o.append(f'<text x="{x}" y="92" font-family="{SANS}" font-size="15" fill="{t["muted"]}">{label}</text>')
        x += 340
    o.append(f'<line x1="{ox}" y1="116" x2="{W-ox}" y2="116" stroke="{t["line"]}"/>')
    last_month = None
    for i, w in enumerate(weeks):
        first = dt.date.fromisoformat(w["contributionDays"][0]["date"])
        if first.month != last_month and i < len(weeks) - 2:
            if last_month is not None or first.day <= 7:
                o.append(f'<text x="{ox + i*(cell+gap)}" y="{oy-10}" font-family="{MONO}" font-size="12" '
                         f'letter-spacing="0.5" fill="{t["muted"]}">{MONTHS[first.month-1]}</text>')
            last_month = first.month
        for d in w["contributionDays"]:
            wd = (dt.date.fromisoformat(d["date"]).weekday() + 1) % 7  # domingo = 0
            o.append(f'<rect x="{ox + i*(cell+gap)}" y="{oy + wd*(cell+gap)}" width="{cell}" height="{cell}" '
                     f'rx="3" fill="{t["levels"][level(d["contributionCount"])]}"/>')
    ly = oy + 7 * (cell + gap) + 18
    lx = W - ox - (5 * (12 + 4)) - 40
    o.append(f'<text x="{lx-10}" y="{ly+10}" text-anchor="end" font-family="{MONO}" font-size="12" fill="{t["muted"]}">Less</text>')
    for k in range(5):
        o.append(f'<rect x="{lx + k*16}" y="{ly}" width="12" height="12" rx="2" fill="{t["levels"][k]}"/>')
    o.append(f'<text x="{lx + 5*16 + 6}" y="{ly+10}" font-family="{MONO}" font-size="12" fill="{t["muted"]}">More</text>')
    o.append("</svg>")
    return "\n".join(o)


os.makedirs(OUT, exist_ok=True)
for name, theme in THEMES.items():
    with open(os.path.join(OUT, f"activity-{name}.svg"), "w") as f:
        f.write(render(theme))
print(f"{total} contributions, {active} active days, streak {streak}")
