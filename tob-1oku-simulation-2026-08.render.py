#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""out.json -> tob-1oku-simulation-2026-08.html"""
import json, html
D = json.load(open("/tmp/claude-0/-home-user-Output/9b2dbfd1-2f24-55ea-8a56-7a260be367aa/scratchpad/out.json"))
M, SP = D["months"], D["spring"]
SC = D["scen"]
LANE_ORDER = ["ent", "fde", "product"]
LANE_JA = {"ent": "エンプラ", "fde": "FDE", "product": "プロダクト"}
VAR = {"ent": "s1", "fde": "s2", "product": "s3"}
TARGET = 10000/12  # ARR1億 = 月商833万

# ---------------- cash ----------------
CASH0 = 3200.0
def cash_series(sk):
    p = SC[sk]["pnl"]; fix = p["labor"]+p["fixed"]; dc = 1 - p["direct"]/p["mrr"]
    c = CASH0; out = []
    for rev in SC[sk]["totals"]:
        c += rev*dc - fix; out.append(c)
    return out, fix, dc
CASH = {sk: cash_series(sk) for sk in SC}
def breakeven(sk):
    _, fix, dc = CASH[sk]; return fix/dc

def esc(s): return html.escape(str(s))
def f(x, d=0): return f"{x:,.{d}f}"

# ================= SVG helpers =================
def axis_text(x, y, t, anchor="middle", cls="ax"):
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" class="{cls}">{esc(t)}</text>'

# ---- Chart 1: TAM ceiling ----
def chart_tam():
    W, H = 1000, 330
    L, R, T, B = 150, 40, 34, 44
    rows = D["ceiling"]
    lanes = ["プロダクト", "FDE", "エンプラ"]
    mx = 4.0  # cap x at 4.0億 for readability
    pw = W-L-R
    def X(v): return L + min(v, mx)/mx*pw
    s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="レーン別TAM天井">']
    # grid
    for g in [0, 1, 2, 3, 4]:
        x = X(g)
        s.append(f'<line x1="{x:.1f}" y1="{T}" x2="{x:.1f}" y2="{H-B}" class="grid"/>')
        s.append(axis_text(x, H-B+18, f"{g}.0億"))
    bh, gap, grp = 16, 5, 74
    for li, ln in enumerate(lanes):
        sub = [r for r in rows if r["lane"] == ln]
        gy = T + li*grp
        s.append(f'<text x="{L-12}" y="{gy+30}" text-anchor="end" class="lanelab">{esc(ln)}</text>')
        for bi, r in enumerate(sub):
            y = gy + bi*(bh+gap) + 6
            w = X(r["max_arr"])-L
            over = r["max_arr"] > mx
            s.append(f'<rect x="{L}" y="{y}" width="{max(w,2):.1f}" height="{bh}" rx="4" '
                     f'fill="var(--{VAR[{"プロダクト":"product","FDE":"fde","エンプラ":"ent"}[ln]]})" '
                     f'opacity="{0.45+0.275*bi:.3f}"/>')
            lab = f'TAM {r["tam"]}社 → {r["max_arr"]:.2f}億' + ("＋" if over else "")
            if over:   # 上限で頭切れするバーはラベルをバー内に置く
                s.append(f'<text x="{W-R-8:.1f}" y="{y+bh-3}" text-anchor="end" class="seglab">{esc(lab)}</text>')
            else:
                s.append(f'<text x="{X(r["max_arr"])+8:.1f}" y="{y+bh-3}" class="barlab">{esc(lab)}</text>')
    # 1億 reference
    x1 = X(1.0)
    s.append(f'<line x1="{x1:.1f}" y1="{T-8}" x2="{x1:.1f}" y2="{H-B}" class="ref"/>')
    s.append(f'<text x="{x1+6:.1f}" y="{T-12}" class="reflab">ARR 1億</text>')
    s.append('</svg>')
    return "".join(s)

# ---- Chart 2: monthly revenue lines ----
def chart_monthly():
    W, H = 1000, 360
    L, R, T, B = 62, 118, 30, 46
    ymax = 1400.0
    pw, ph = W-L-R, H-T-B
    def X(i): return L + i/(len(M)-1)*pw
    def Y(v): return T + (1-min(v, ymax)/ymax)*ph
    cols = {"A": "var(--s1)", "B": "var(--s3)", "C": "var(--s2)"}
    s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="シナリオ別 月次売上推移">']
    for g in range(0, 1401, 200):
        y = Y(g)
        s.append(f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" class="grid"/>')
        s.append(axis_text(L-10, y+4, f"{g:,}", "end"))
    for i, m in enumerate(M):
        s.append(axis_text(X(i), H-B+18, m[2:].replace("-", "/")))
    # spring marker
    xs = X(SP)
    s.append(f'<rect x="{xs-16:.1f}" y="{T}" width="32" height="{ph:.1f}" class="spring"/>')
    s.append(f'<text x="{xs:.1f}" y="{T-10}" text-anchor="middle" class="reflab">春 2027-03</text>')
    # ARR1億 line
    yt = Y(TARGET)
    s.append(f'<line x1="{L}" y1="{yt:.1f}" x2="{W-R}" y2="{yt:.1f}" class="ref"/>')
    s.append(f'<text x="{W-R+8:.1f}" y="{yt-6:.1f}" class="reflab">ARR 1億</text>')
    s.append(f'<text x="{W-R+8:.1f}" y="{yt+10:.1f}" class="reflab">月商833万</text>')
    for sk in ["A", "B", "C"]:
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(SC[sk]["totals"]))
        s.append(f'<polyline points="{pts}" fill="none" stroke="{cols[sk]}" stroke-width="2.5" '
                 f'stroke-linejoin="round" stroke-linecap="round"/>')
        v = SC[sk]["totals"][SP]
        s.append(f'<circle cx="{X(SP):.1f}" cy="{Y(v):.1f}" r="5" fill="{cols[sk]}" '
                 f'stroke="var(--surface)" stroke-width="2"/>')
        ly = Y(SC[sk]["totals"][-1])
        s.append(f'<text x="{W-R-52:.1f}" y="{ly+4:.1f}" class="serieslab" fill="{cols[sk]}">{sk}</text>')
    s.append('</svg>')
    return "".join(s)

# ---- Chart 3: spring mix stacked ----
def chart_mix():
    W, H = 1000, 216
    L, R, T = 108, 150, 26
    pw = W-L-R
    mx = 1250.0
    s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="シナリオ別 春の売上ミックス">']
    for si, sk in enumerate(["A", "B", "C"]):
        y = T + si*56
        tot = SC[sk]["total"]
        s.append(f'<text x="{L-12}" y="{y+24}" text-anchor="end" class="lanelab">シナリオ {sk}</text>')
        x = L
        for r in SC[sk]["rows"]:
            if r["mrr"] <= 0: continue
            w = r["mrr"]/mx*pw
            s.append(f'<rect x="{x:.1f}" y="{y}" width="{max(w-2,1):.1f}" height="30" rx="3" '
                     f'fill="var(--{VAR[r["key"]]})"/>')
            if w > 62:
                s.append(f'<text x="{x+w/2-1:.1f}" y="{y+19}" text-anchor="middle" class="seglab">'
                         f'{f(r["mrr"])}万</text>')
            x += w
        s.append(f'<text x="{x+10:.1f}" y="{y+20}" class="totlab">計 {f(tot)}万 · ARR {tot*12/10000:.2f}億</text>')
    xt = L + TARGET/mx*pw
    s.append(f'<line x1="{xt:.1f}" y1="{T-10}" x2="{xt:.1f}" y2="{T+3*56-14}" class="ref"/>')
    s.append(f'<text x="{xt:.1f}" y="{T-14}" text-anchor="middle" class="reflab">ARR 1億ライン</text>')
    s.append('</svg>')
    return "".join(s)

# ---- Chart 4: enterprise deadline ----
def chart_deadline():
    W, H = 1000, 268
    L, R, T = 132, 40, 44
    pw = W-L-R
    cols = len(M)
    cw = pw/cols
    s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="エンプラ案件のリード投入期限">']
    for i, m in enumerate(M):
        x = L+i*cw
        s.append(f'<line x1="{x:.1f}" y1="{T-8}" x2="{x:.1f}" y2="{H-30}" class="grid"/>')
        s.append(axis_text(x+cw/2, T-14, m[2:].replace("-", "/")))
    xs = L+SP*cw
    s.append(f'<rect x="{xs:.1f}" y="{T-8}" width="{cw:.1f}" height="{H-30-T+8:.1f}" class="spring"/>')
    for i, d in enumerate(D["deadline"]):
        y = T + 6 + i*33
        ok = "間に合う" in d["ok"]
        si = M.index(d["inject"])
        ei = M.index(d["land"]) if d["land"] in M else cols-1
        x0, x1 = L+si*cw+3, L+ei*cw+cw-3
        s.append(f'<text x="{L-12}" y="{y+17}" text-anchor="end" class="lanelab">投入 {esc(d["inject"][2:])}</text>')
        s.append(f'<rect x="{x0:.1f}" y="{y}" width="{max(x1-x0,4):.1f}" height="22" rx="4" '
                 f'fill="var(--{"ok" if ok else "bad"})" opacity="0.85"/>')
        s.append(f'<text x="{x0+8:.1f}" y="{y+15}" class="seglab">PoC → 本契約 {"✓" if ok else "✕"}</text>')
    s.append(f'<text x="{xs+cw/2:.1f}" y="{H-12}" text-anchor="middle" class="reflab">春の期限</text>')
    s.append('</svg>')
    return "".join(s)

# ---- Chart 5: cash ----
def chart_cash():
    W, H = 1000, 300
    L, R, T, B = 74, 108, 26, 44
    pw, ph = W-L-R, H-T-B
    lo, hi = -3600.0, 3600.0
    def X(i): return L+i/(len(M)-1)*pw
    def Y(v): return T+(hi-max(min(v, hi), lo))/(hi-lo)*ph
    cols = {"A": "var(--s1)", "B": "var(--s3)", "C": "var(--s2)"}
    s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="シナリオ別 現金残高推移">']
    for g in range(-3000, 3601, 1500):
        y = Y(g)
        s.append(f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" class="grid"/>')
        s.append(axis_text(L-10, y+4, f"{g:,}", "end"))
    y0 = Y(0)
    s.append(f'<line x1="{L}" y1="{y0:.1f}" x2="{W-R}" y2="{y0:.1f}" class="zero"/>')
    s.append(f'<text x="{W-R+8:.1f}" y="{y0+4:.1f}" class="reflab">現金 0</text>')
    for i, m in enumerate(M):
        s.append(axis_text(X(i), H-B+18, m[2:].replace("-", "/")))
    xs = X(SP)
    s.append(f'<rect x="{xs-16:.1f}" y="{T}" width="32" height="{ph:.1f}" class="spring"/>')
    s.append(f'<text x="{xs:.1f}" y="{T-8}" text-anchor="middle" class="reflab">春</text>')
    dep = {}   # 枯渇月 -> [シナリオ]  (同月の系列はまとめて1ラベルにする)
    for sk in ["A", "B", "C"]:
        cs = CASH[sk][0]
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(cs))
        s.append(f'<polyline points="{pts}" fill="none" stroke="{cols[sk]}" stroke-width="2.5" '
                 f'stroke-linejoin="round" stroke-linecap="round"/>')
        s.append(f'<text x="{W-R+8:.1f}" y="{Y(cs[-1])+4:.1f}" class="serieslab" fill="{cols[sk]}">{sk}</text>')
        for i, v in enumerate(cs):
            if v < 0:
                s.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="5" fill="var(--bad)" '
                         f'stroke="var(--surface)" stroke-width="2"/>')
                dep.setdefault(i, []).append(sk)
                break
    for i, sks in dep.items():
        s.append(f'<line x1="{X(i):.1f}" y1="{y0+6:.1f}" x2="{X(i):.1f}" y2="{H-B-26:.1f}" class="ref"/>')
        s.append(f'<text x="{X(i):.1f}" y="{H-B-12:.1f}" text-anchor="middle" class="badlab">'
                 f'{"・".join(sks)} 枯渇 {esc(M[i][2:])}</text>')
    s.append('</svg>')
    return "".join(s)

# ---- funnel table (scenario A) ----
def funnel_block(sk):
    rows = SC[sk]["funnel"]
    mxl = max((r["leads"] for r in rows), default=1) or 1
    out = ['<div class="funnels">']
    for r in rows:
        if r["leads"] <= 0:
            continue
        k = r["key"]
        stages = [("リード", r["leads"]), ("商談", r["meetings"])]
        if r["stage2"]:
            stages.append(("PoC", r["stage2"]))
        stages.append(("受注", r["need"]))
        out.append(f'<div class="funnel"><div class="fh"><span class="dot" style="background:var(--{VAR[k]})"></span>'
                   f'{esc(LANE_JA[k])}<span class="fmeta">L→受注 {r["cvr"]}% ／ LT {r["lt"]}ヶ月</span></div>')
        for nm, v in stages:
            w = max(v/mxl*100, 1.2)
            out.append(f'<div class="frow"><span class="fn">{esc(nm)}</span>'
                       f'<span class="fbarwrap"><span class="fbar" style="width:{w:.2f}%;background:var(--{VAR[k]})"></span></span>'
                       f'<span class="fv">{v:,.1f}</span></div>')
        out.append(f'<div class="fnote">月あたり リード {r["leads_pm"]}件 ／ 商談 {r["meet_pm"]}件'
                   f' ・ TAM消費 {r["tam_pct"]}%</div></div>')
    out.append('</div>')
    return "".join(out)

# ================= tables =================
def mix_table(sk):
    rows = SC[sk]["rows"]; tot = SC[sk]["total"]
    h = ['<div class="tw"><table><thead><tr><th>レーン</th><th class="n">稼働社数</th><th class="n">PoC</th>'
         '<th class="n">単価/月</th><th class="n">年間契約</th><th class="n">月商</th><th class="n">構成比</th></tr></thead><tbody>']
    for r in rows:
        h.append(f'<tr><td><span class="dot" style="background:var(--{VAR[r["key"]]})"></span>{esc(LANE_JA[r["key"]])}</td>'
                 f'<td class="n">{r["deals"]}</td><td class="n">{r["poc"] or "—"}</td>'
                 f'<td class="n">{f(r["unit"])}万</td><td class="n">{f(r["annual"])}万</td>'
                 f'<td class="n b">{f(r["mrr"])}万</td><td class="n">{r["share"]}%</td></tr>')
    h.append(f'<tr class="sum"><td>合計</td><td class="n"></td><td class="n"></td><td class="n"></td><td class="n"></td>'
             f'<td class="n b">{f(tot)}万</td><td class="n">ARR {tot*12/10000:.2f}億</td></tr>')
    h.append('</tbody></table></div>')
    return "".join(h)

def funnel_table(sk):
    rows = SC[sk]["funnel"]
    tm = sum(r["meetings"] for r in rows); tl = sum(r["leads"] for r in rows)
    h = ['<div class="tw"><table><thead><tr><th>レーン</th><th class="n">必要受注</th><th class="n">PoC</th>'
         '<th class="n">必要商談</th><th class="n">必要リード</th><th class="n">リード/月</th>'
         '<th class="n">L→受注</th><th class="n">LT</th><th class="n">TAM消費</th></tr></thead><tbody>']
    for r in rows:
        h.append(f'<tr><td><span class="dot" style="background:var(--{VAR[r["key"]]})"></span>{esc(LANE_JA[r["key"]])}</td>'
                 f'<td class="n">{r["need"]:.1f}</td><td class="n">{r["stage2"] if r["stage2"] else "—"}</td>'
                 f'<td class="n">{r["meetings"]:.1f}</td><td class="n b">{r["leads"]:.1f}</td>'
                 f'<td class="n">{r["leads_pm"]:.1f}</td><td class="n">{r["cvr"]}%</td>'
                 f'<td class="n">{r["lt"]}ヶ月</td><td class="n">{r["tam_pct"]}%</td></tr>')
    h.append(f'<tr class="sum"><td>合計</td><td class="n"></td><td class="n"></td><td class="n b">{tm:.1f}</td>'
             f'<td class="n b">{tl:.1f}</td><td class="n">{tl/7:.1f}</td><td class="n"></td><td class="n"></td><td class="n"></td></tr>')
    h.append('</tbody></table></div>')
    return "".join(h)

def monthly_table():
    h = ['<div class="tw"><table><thead><tr><th>月</th>']
    for sk in ["A", "B", "C"]:
        h.append(f'<th class="n">{sk} 月商</th>')
    h.append('<th class="n">A の内訳（エンプラ / FDE / プロダクト）</th></tr></thead><tbody>')
    for t, m in enumerate(M):
        cls = ' class="hl"' if t == SP else ''
        h.append(f'<tr{cls}><td>{esc(m)}{" ← 春" if t==SP else ""}</td>')
        for sk in ["A", "B", "C"]:
            h.append(f'<td class="n">{f(SC[sk]["totals"][t])}</td>')
        s = SC["A"]["series"]
        h.append(f'<td class="n sm">{f(s["ent"][t])} / {f(s["fde"][t])} / {f(s["product"][t])}</td></tr>')
    h.append('</tbody></table></div>')
    return "".join(h)

def pnl_table():
    h = ['<div class="tw"><table><thead><tr><th>シナリオ</th><th class="n">春の月商</th><th class="n">直接原価</th>'
         '<th class="n">人員</th><th class="n">人件費</th><th class="n">営業利益/月</th>'
         '<th class="n">損益分岐 月商</th><th class="n">資金枯渇</th></tr></thead><tbody>']
    for sk in ["A", "B", "C"]:
        p = SC[sk]["pnl"]; cs = CASH[sk][0]
        broke = next((M[i] for i, v in enumerate(cs) if v < 0), None)
        be = breakeven(sk)
        h.append(f'<tr><td class="b">{sk}</td><td class="n b">{f(p["mrr"])}万</td><td class="n">{f(p["direct"])}万</td>'
                 f'<td class="n">{p["head"]}人</td><td class="n">{f(p["labor"])}万</td>'
                 f'<td class="n {"neg" if p["op"]<0 else "pos"}">{p["op"]:+,}万</td>'
                 f'<td class="n">{f(be)}万 <span class="sm">(ARR {be*12/10000:.2f}億)</span></td>'
                 f'<td class="n {"neg" if broke else "pos"}">{esc(broke) if broke else "—"}</td></tr>')
    h.append('</tbody></table></div>')
    return "".join(h)

def lane_table():
    lanes = [
        ("ent", "③ エンプラ大型（年間契約3,000万・東京通信型）", "250万", "3,000万", "35% × 35% × 45%", "5.51%", "5.0ヶ月", "2%", "500社", "紹介（投資家・既存顧客）主体。アウトバウンドでは届かない"),
        ("fde", "② FDE型（社内データ基盤・売上予測／読みて型）", "150万", "1,800万", "15% × 30%", "4.50%", "2.0ヶ月", "3%", "300社", "紹介＋既存顧客アップセル"),
        ("product", "① プロダクト量産（切り抜き自動化・WS型 → タレント事務所）", "30万", "360万", "20% × 25%", "5.00%", "1.5ヶ月", "5%", "500社", "アウトバウンド（テレアポ／フォーム）"),
    ]
    h = ['<div class="tw"><table><thead><tr><th>レーン</th><th class="n">単価/月</th><th class="n">年間契約</th>'
         '<th class="n">ファネル各段</th><th class="n">L→受注</th><th class="n">リードタイム</th>'
         '<th class="n">月次チャーン</th><th class="n">TAM</th><th>主チャネル</th></tr></thead><tbody>']
    for k, nm, u, a, fn, c, lt, ch, tam, chn in lanes:
        h.append(f'<tr><td><span class="dot" style="background:var(--{VAR[k]})"></span>{esc(nm)}</td>'
                 f'<td class="n b">{u}</td><td class="n">{a}</td><td class="n sm">{fn}</td>'
                 f'<td class="n">{c}</td><td class="n">{lt}</td><td class="n">{ch}</td>'
                 f'<td class="n">{tam}</td><td class="sm">{esc(chn)}</td></tr>')
    h.append('</tbody></table></div>')
    return "".join(h)

# ================= page =================
A = SC["A"]; pA = A["pnl"]
springA = A["totals"][SP]
tmA = sum(r["meetings"] for r in A["funnel"])/7
tlA = sum(r["leads"] for r in A["funnel"])/7
brokeA = next((M[i] for i, v in enumerate(CASH["A"][0]) if v < 0), "—")

CSS = """
:root{
  color-scheme: light;
  --ground:#f4f6f8; --surface:#ffffff; --surface2:#eef1f5;
  --ink:#141a21; --sub:#5b6675; --faint:#8a93a1; --line:#dde2e9;
  --s1:#2a78d6; --s2:#1baf7a; --s3:#eb6834;
  --ok:#14733f; --bad:#b3261e; --warn:#a4620d;
  --okbg:#e7f4ec; --badbg:#fdeceb; --warnbg:#fdf3e4;
  --springbg:rgba(42,120,214,.07);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    color-scheme: dark;
    --ground:#12151a; --surface:#191d24; --surface2:#212630;
    --ink:#e7ebf0; --sub:#a3adba; --faint:#78828f; --line:#2c323c;
    --s1:#3987e5; --s2:#199e70; --s3:#d95926;
    --ok:#4ec27f; --bad:#f4796b; --warn:#e0a44a;
    --okbg:#14261c; --badbg:#2a1715; --warnbg:#291f11;
    --springbg:rgba(57,135,229,.12);
  }
}
:root[data-theme="dark"]{
  color-scheme: dark;
  --ground:#12151a; --surface:#191d24; --surface2:#212630;
  --ink:#e7ebf0; --sub:#a3adba; --faint:#78828f; --line:#2c323c;
  --s1:#3987e5; --s2:#199e70; --s3:#d95926;
  --ok:#4ec27f; --bad:#f4796b; --warn:#e0a44a;
  --okbg:#14261c; --badbg:#2a1715; --warnbg:#291f11;
  --springbg:rgba(57,135,229,.12);
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
  font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP",system-ui,sans-serif;
  font-size:14px;line-height:1.72;-webkit-font-smoothing:antialiased}
.mono,.n,.stat .v,.chart text{font-variant-numeric:tabular-nums;
  font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace}
.wrap{max-width:1080px;margin:0 auto;padding:0 22px}

header{background:var(--surface);border-bottom:1px solid var(--line);padding:44px 0 34px}
.kicker{font-size:11px;letter-spacing:.2em;font-weight:700;color:var(--s1);text-transform:uppercase}
h1{margin:12px 0 10px;font-size:34px;line-height:1.24;font-weight:800;letter-spacing:-.02em;text-wrap:balance}
.lede{margin:0;color:var(--sub);font-size:14.5px;max-width:66ch}
.src{margin-top:16px;font-size:12px;color:var(--faint);max-width:70ch}

nav{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--surface) 92%,transparent);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
nav .wrap{display:flex;gap:4px;flex-wrap:wrap;padding-top:9px;padding-bottom:9px}
nav a{text-decoration:none;color:var(--sub);font-size:12px;padding:5px 11px;border-radius:6px;
  border:1px solid transparent}
nav a:hover{background:var(--surface2);color:var(--ink)}
nav a:focus-visible{outline:2px solid var(--s1);outline-offset:2px}

section{padding:38px 0 4px}
.qhead{display:flex;gap:13px;align-items:baseline;margin-bottom:6px}
.qnum{font-size:11px;font-weight:800;letter-spacing:.12em;color:var(--s1);
  border:1px solid var(--s1);border-radius:5px;padding:2px 8px;flex:none}
h2{margin:0;font-size:21px;font-weight:800;letter-spacing:-.01em;text-wrap:balance}
.qsub{margin:0 0 20px 0;color:var(--sub);font-size:13.5px;max-width:72ch}

.card{background:var(--surface);border:1px solid var(--line);border-radius:11px;padding:22px;margin-bottom:16px}
.card h3{margin:0 0 4px;font-size:14.5px;font-weight:700}
.card .note{margin:0 0 16px;font-size:12.5px;color:var(--sub);max-width:74ch}

.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin-bottom:18px}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:11px;padding:16px 18px;
  border-top:3px solid var(--s1)}
.stat.b{border-top-color:var(--bad)} .stat.w{border-top-color:var(--warn)} .stat.g{border-top-color:var(--ok)}
.stat .k{font-size:11px;letter-spacing:.06em;color:var(--sub);font-weight:700}
.stat .v{font-size:27px;font-weight:800;letter-spacing:-.02em;margin:5px 0 3px;line-height:1.1}
.stat .d{font-size:12px;color:var(--sub)}

.tw{overflow-x:auto;margin:0 -4px}
table{border-collapse:collapse;width:100%;font-size:13px;min-width:560px}
th,td{padding:9px 11px;text-align:left;border-bottom:1px solid var(--line);vertical-align:middle}
th{font-size:11px;letter-spacing:.05em;color:var(--sub);font-weight:700;white-space:nowrap;
  border-bottom:1.5px solid var(--line)}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.b,.b{font-weight:700}
td.sm,.sm{font-size:11.5px;color:var(--sub)}
tr.sum td{border-top:1.5px solid var(--line);border-bottom:none;font-weight:700;background:var(--surface2)}
tr.hl td{background:var(--springbg)}
td.neg{color:var(--bad);font-weight:700} td.pos{color:var(--ok);font-weight:700}
.dot{display:inline-block;width:9px;height:9px;border-radius:3px;margin-right:7px;vertical-align:baseline}

.chart{width:100%;height:auto;display:block}
.chart .ax{font-size:10.5px;fill:var(--faint)}
.chart .grid{stroke:var(--line);stroke-width:1}
.chart .zero{stroke:var(--faint);stroke-width:1.5;stroke-dasharray:2 3}
.chart .ref{stroke:var(--faint);stroke-width:1.5;stroke-dasharray:5 4}
.chart .reflab{font-size:10.5px;fill:var(--faint);font-weight:700}
.chart .lanelab{font-size:12px;fill:var(--ink);font-weight:700}
.chart .barlab{font-size:11px;fill:var(--sub)}
.chart .seglab{font-size:11px;fill:#fff;font-weight:700}
.chart .totlab{font-size:11.5px;fill:var(--ink);font-weight:700}
.chart .serieslab{font-size:13px;font-weight:800}
.chart .badlab{font-size:10.5px;fill:var(--bad);font-weight:700}
.chart .spring{fill:var(--springbg)}

.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--sub);margin-top:12px}
.legend span.i{display:inline-flex;align-items:center;gap:6px}

.funnels{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.funnel{border:1px solid var(--line);border-radius:9px;padding:14px 16px;background:var(--surface2)}
.fh{font-size:13px;font-weight:700;margin-bottom:10px;display:flex;align-items:center;flex-wrap:wrap;gap:4px}
.fmeta{font-size:11px;color:var(--sub);font-weight:400;margin-left:auto}
.frow{display:grid;grid-template-columns:52px 1fr 58px;align-items:center;gap:8px;margin-bottom:5px}
.fn{font-size:11.5px;color:var(--sub)}
.fbarwrap{background:var(--line);border-radius:3px;height:13px;overflow:hidden}
.fbar{display:block;height:100%;border-radius:3px}
.fv{font-size:12px;text-align:right;font-weight:700;
  font-variant-numeric:tabular-nums;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.fnote{font-size:11px;color:var(--sub);margin-top:9px;padding-top:8px;border-top:1px solid var(--line)}

.call{border-radius:10px;padding:15px 18px;margin:16px 0;font-size:13.5px;border:1px solid}
.call.bad{background:var(--badbg);border-color:var(--bad)}
.call.ok{background:var(--okbg);border-color:var(--ok)}
.call.warn{background:var(--warnbg);border-color:var(--warn)}
.call .t{font-weight:800;display:block;margin-bottom:4px;font-size:13px}
.call.bad .t{color:var(--bad)} .call.ok .t{color:var(--ok)} .call.warn .t{color:var(--warn)}
.call p{margin:0} .call p+p{margin-top:7px}

ul.tight{margin:8px 0 0;padding-left:19px} ul.tight li{margin-bottom:6px}
ol.tight{margin:8px 0 0;padding-left:20px} ol.tight li{margin-bottom:7px}
footer{border-top:1px solid var(--line);margin-top:44px;padding:26px 0 46px;color:var(--faint);font-size:12px}
@media(max-width:640px){h1{font-size:26px}.stat .v{font-size:23px}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""

HTML = f"""<title>1億円への三本の階段</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>{CSS}</style>

<header><div class="wrap">
  <div class="kicker">Ceed · toB 収益シミュレーション</div>
  <h1>1億円への三本の階段</h1>
  <p class="lede">8/12 投資家定例で決めた「リソースの9割を2Bへ・来年春までに1億」を、案件タイプ別の単価・ファネル・リードタイムに分解して、<b>どの案件を何社取れば届くのか</b>、そのために<b>月何件のリードが要るのか</b>を数字で置いたもの。</p>
  <p class="src">出典: 2026-08-12 投資家定例議事録／2026-08-07・07-24 経営会議／Notion「toBでの1億売上の計画台の叩き作成」。実績値は 2026-08 時点。★印のない数値はすべて仮置きパラメータで、確定値ではない。</p>
</div></header>

<nav><div class="wrap">
  <a href="#q1">Q1 目標定義</a><a href="#q2">Q2 天井</a><a href="#q3">Q3 レーン</a>
  <a href="#q4">Q4 ミックス</a><a href="#q5">Q5 ファネル</a><a href="#q6">Q6 期限</a>
  <a href="#q7">Q7 資金</a><a href="#open">未確定</a>
</div></nav>

<div class="wrap">

<section id="sum">
<div class="stats">
  <div class="stat"><div class="k">シナリオA 春の着地（月次シム）</div><div class="v">{f(springA)}万<span style="font-size:15px">/月</span></div><div class="d">ARR {springA*12/10000:.2f}億 — エンプラ2社が乗る前提</div></div>
  <div class="stat b"><div class="k">エンプラ リード投入期限</div><div class="v">2026-10</div><div class="d">11月以降の投入は春に売上化しない</div></div>
  <div class="stat w"><div class="k">必要商談数</div><div class="v">{tmA:.1f}件<span style="font-size:15px">/月</span></div><div class="d">現状 約26件/月 — 数は足りている</div></div>
  <div class="stat b"><div class="k">資金枯渇（Aで採用実行時）</div><div class="v">{esc(brokeA)}</div><div class="d">春を待たずに現金が尽きる</div></div>
</div>
<div class="call bad"><span class="t">このシミュレーションの結論を3行で</span>
<p>① 春の1億は <b>ARR 1億（月商833万）なら射程、月商1億は算数的に不可能</b>。② 律速は商談数ではなく<b>商談の単価階層</b> — 現状は1商談あたり月5.4万円、必要なのは約300万円。③ 最大のリスクは売上ではなく<b>資金</b>で、採用を先行させると春の前に現金が尽きる。</p></div>
</section>

<section id="q1">
<div class="qhead"><span class="qnum">Q1</span><h2>そもそも「1億」は月商かARRか</h2></div>
<p class="qsub">議事録には「月1億円」と記録されているが、その根拠として引かれた吉田さんの発言（3,000万 × 3〜4社）は<b>年間</b>の積み上げ。Ken さんは「1ヶ月で1〜2億」の前提で話しており、会議の中で定義が割れたまま決議されている。12倍の差なので、まずここを確定させないと計画が引けない。</p>
<div class="card">
  <h3>現状 月商140万円から、7ヶ月（2026-09〜2027-03）で到達するのに必要な月次成長率</h3>
  <p class="note">複利。エンタープライズ営業はリードタイムが5ヶ月あるため、途中月の成長は後ろ倒しに効く。</p>
  <div class="tw"><table><thead><tr><th>解釈</th><th class="n">春の月商</th><th class="n">現状比</th><th class="n">必要成長率</th><th>判定</th></tr></thead><tbody>
  <tr><td class="b">ARR 1億（月商833万）</td><td class="n">833万</td><td class="n">6.0倍</td><td class="n b">+29.0%/月</td><td><span class="b" style="color:var(--ok)">射程内</span> — 大型案件が2社乗れば届く</td></tr>
  <tr><td class="b">月商 1億（ARR 12億）</td><td class="n">10,000万</td><td class="n">71.4倍</td><td class="n b">+84.0%/月</td><td><span class="b" style="color:var(--bad)">不可能</span> — 7ヶ月連続で月+84%は事例がない</td></tr>
  </tbody></table></div>
  <div class="call warn"><span class="t">提案</span><p>春の目標は <b>ARR 1億（月商833万・年間契約ベース3,000万×3社相当）</b> と定義し直す。月商1億は2028年以降の目標として分離する。以降のシミュレーションはすべて ARR 1億基準。</p></div>
</div>
</section>

<section id="q2">
<div class="qhead"><span class="qnum">Q2</span><h2>プロダクト量産だけで1億に届くのか</h2></div>
<p class="qsub">吉田さんの「今のノウハウのままだと3,000〜4,000万で頭打ち」という指摘の検証。各レーンの上限は <b>到達可能な母数（TAM）× リード→受注CVR × 単価 × 12ヶ月</b> で決まる。単価が低いレーンは、CVRを上げても母数の壁に先に当たる。</p>
<div class="card">
  <h3>レーン別の理論上限 ARR</h3>
  <p class="note">タレント事務所のうち切り抜き予算を持つのが200社なら、プロダクト単独の上限は ARR 3,600万 — 吉田さんの指摘とほぼ一致する。500社に広げても9,000万で、1億に「ぎりぎり届かない」帯に留まる。</p>
  {chart_tam()}
  <div class="legend">
    <span class="i"><span class="dot" style="background:var(--s3)"></span>プロダクト</span>
    <span class="i"><span class="dot" style="background:var(--s2)"></span>FDE</span>
    <span class="i"><span class="dot" style="background:var(--s1)"></span>エンプラ</span>
    <span class="i">濃度は TAM 想定の大小</span>
  </div>
  <div class="call bad"><span class="t">読み取り</span><p>プロダクト量産は<b>単価30万 × 母数の壁</b>で1億に構造的に届きにくい。一方エンプラは1社=年3,000万＝プロダクト8.3社分なので、母数が同じ500社でも上限は8.3倍になる。<b>吉田さんの懸念は数字上正しく、エンプラなしで春1億は成立しない</b>。</p></div>
</div>
</section>

<section id="q3">
<div class="qhead"><span class="qnum">Q3</span><h2>三本のレーンをどう置いたか</h2></div>
<p class="qsub">単価とCVRだけでは期限付きの計画は引けない。<b>リードタイム</b>（受注から売上計上まで）・<b>チャーン</b>（積み上がるか流れ落ちるか）・<b>デリバリー人数</b>を合わせた5変数で置いている。★は実績由来、それ以外は仮置き。</p>
<div class="card">
  <h3>レーン定義</h3>
  <p class="note">★実績由来: プロダクト単価30万（現状 月140万 ÷ 稼働4〜5社）、エンプラ年間契約3,000万（吉田さん目線）、FDE = 読みて案件の想定。CVR・リードタイム・チャーンは全て仮置きで、実データによる補正が必要。</p>
  {lane_table()}
  <div class="call warn"><span class="t">エンプラのチャネル前提が効いている</span><p>エンプラは紹介チャネル前提でリード→商談35%と置いた。東京通信は石川さん紹介、読みてはカルタ経由で、どちらも<b>実績として紹介から来ている</b>。これをアウトバウンド（商談化率6%）で取ろうとすると、必要リードは44件から<b>259件</b>に跳ね上がり、テレアポ体制では現実的でなくなる。</p></div>
</div>
</section>

<section id="q4">
<div class="qhead"><span class="qnum">Q4</span><h2>どの案件を何社取れば届くのか</h2></div>
<p class="qsub">3つのミックスを比較する。Aは Ken さんの「大口1〜2社で売上の8割」型、Bは現状の受注ペース（+1社/週）をそのまま延長した型、Cはその中間。</p>

<div class="card">
  <h3>春（2027-03）の売上ミックス比較</h3>
  <p class="note">横軸は月商。ARR 1億ライン（月商833万）を基準線として表示。</p>
  {chart_mix()}
  <div class="legend">
    <span class="i"><span class="dot" style="background:var(--s1)"></span>エンプラ</span>
    <span class="i"><span class="dot" style="background:var(--s2)"></span>FDE</span>
    <span class="i"><span class="dot" style="background:var(--s3)"></span>プロダクト</span>
  </div>
</div>

<div class="card">
  <h3>シナリオA — エンプラ主導（Ken型・エンプラ構成比70%）</h3>
  <p class="note">本契約2社＋PoC実施中1社。投資家に約束した「大口が売上の大半を占める構成」に最も忠実。</p>
  {mix_table("A")}
</div>
<div class="card">
  <h3>シナリオB — プロダクト主導（現状延長）</h3>
  <p class="note">エンプラを取らず、+4社/月のペースを7ヶ月継続した場合。24社まで積むが、必要リードが TAM の85%を消費し、春の着地も伸び切らない。</p>
  {mix_table("B")}
</div>
<div class="card">
  <h3>シナリオC — バランス</h3>
  <p class="note">エンプラ1社＋FDE3社＋プロダクト12社。名目の月商は最大だが、後述のとおり必要人員13.5人で資金が最も早く尽きる。</p>
  {mix_table("C")}
</div>

<div class="card">
  <h3>月次売上推移</h3>
  <p class="note">シナリオAは2027-02にエンプラの本契約が乗るまで横ばいが続き、そこから一気に立ち上がる。Bはなだらかに伸びるが 2027-05 で母数が尽きて頭打ちに転じる。
  なお Q4 のミックス表（A = 903万）は<b>目標とする定常構成</b>、この月次シムの春の値（A = {f(springA)}万）は<b>チャーンとエンプラ本契約の立ち上がりタイミングを織り込んだ着地見込み</b>で、約5%の差はその分。</p>
  {chart_monthly()}
  <div class="legend">
    <span class="i"><span class="dot" style="background:var(--s1)"></span>A エンプラ主導</span>
    <span class="i"><span class="dot" style="background:var(--s3)"></span>B プロダクト主導</span>
    <span class="i"><span class="dot" style="background:var(--s2)"></span>C バランス</span>
  </div>
  {monthly_table()}
</div>
</section>

<section id="q5">
<div class="qhead"><span class="qnum">Q5</span><h2>そのために月何件のリードが要るのか</h2></div>
<p class="qsub">シナリオAを達成するために、7ヶ月で必要な受注数から逆算したファネル。ここが今回いちばん意外な結果になった。</p>
<div class="card">
  <h3>シナリオA のファネル逆算（2026-09〜2027-03 の7ヶ月合計）</h3>
  <p class="note">必要受注数 ÷ 受注率 = 必要商談数 ÷ 商談化率 = 必要リード数。既存稼働分のチャーン補填を含む。</p>
  {funnel_block("A")}
  <div style="height:18px"></div>
  {funnel_table("A")}
  <div class="call bad"><span class="t">律速はリードの「数」ではなく「階層」</span>
  <p>必要商談数は <b>月{tmA:.1f}件</b>。現状すでに <b>約26件/月</b> の商談があり、量は6倍以上足りている。それでも月商が140万に留まっているのは、商談が全て単価30万帯だから。</p>
  <p>現状は <b>1商談あたり月5.4万円</b>（140万 ÷ 26件）。シナリオAが要求するのは <b>1商談あたり月301万円</b> — <b>約56倍</b>。つまり打ち手は「テレアポを増やす」ではなく、<b>年間契約3,000万を出せる相手の商談を月3〜4件作る</b>ことに尽きる。</p></div>
  <div class="call ok"><span class="t">現実的な打ち手</span>
  <p>エンプラ44件のリードは、紹介チャネルなら <b>月6件</b>。石川さん・北原さん・長谷さん（CARTA）・既存顧客（東京通信・読みて）からの紹介で積める水準で、テレアポ体制の拡大とは別ラインの仕事になる。</p></div>
</div>
</section>

<section id="q6">
<div class="qhead"><span class="qnum">Q6</span><h2>いつまでに動けば春に間に合うのか</h2></div>
<p class="qsub">エンプラは 初回商談0.5ヶ月 → PoC契約1.5ヶ月 → PoC実施3ヶ月 → 本契約移行 で、リード投入から売上計上まで<b>約5ヶ月</b>かかる。ここから逆算すると期限が一意に決まる。</p>
<div class="card">
  <h3>エンプラ案件：リード投入月 → 本契約の売上計上月</h3>
  {chart_deadline()}
  <div class="call bad"><span class="t">期限は 2026年10月</span>
  <p>2026年11月以降に着手したエンプラ案件は、<b>どれだけうまく進んでも春には売上計上されない</b>。逆に言えば、春1億の成否は「9月・10月にエンプラの紹介リードを何件立ち上げられたか」でほぼ決まり、年明け以降の営業努力は春の数字には効かない。</p>
  <p>PoC を挟まず年間契約を直接取る、あるいは PoC を有償（400万規模）にして PoC 自体を売上計上する設計にすれば、この期限は1〜2ヶ月後ろにずらせる。</p></div>
</div>
</section>

<section id="q7">
<div class="qhead"><span class="qnum">Q7</span><h2>この計画は資金が持つのか</h2></div>
<p class="qsub">シミュレーションで最も厳しい結果が出たのがここ。売上計画そのものより先に、現金がボトルネックになる。</p>
<div class="card">
  <h3>春時点の損益と、現金が尽きる月</h3>
  <p class="note">人件費は1人80万/月。営業3名＋経営/開発/コーポレート4名にデリバリー要員を加えた構成。現金の初期値は 3,200万（月バーン400万 × ランウェイ8ヶ月、8/12 投資家定例の報告値）。</p>
  {pnl_table()}
  {chart_cash()}
  <div class="legend">
    <span class="i"><span class="dot" style="background:var(--s1)"></span>A</span>
    <span class="i"><span class="dot" style="background:var(--s3)"></span>B</span>
    <span class="i"><span class="dot" style="background:var(--s2)"></span>C</span>
  </div>
  <div class="call bad"><span class="t">採用を先行させると春の前に現金が尽きる</span>
  <p>3シナリオとも、春時点でまだ<b>営業赤字</b>（−264〜−320万/月）。黒字化は <b>ARR 1.5〜1.9億</b> からで、春の1億では届かない。そして採用（セールス責任者・CTO候補・デリバリー要員）のコストが先に立ち上がるため、現金は <b>2026年12月〜2027年1月</b> に尽きる計算になる。</p>
  <p>つまり <b>「春までに1億」と「採用でスケールさせる」は、現状の現金では同時に成立しない</b>。前提として、①調達、②採用ペースを売上の実現に連動させる、③エンプラのPoCを有償化して前倒しで現金化する、のいずれかが要る。</p></div>
  <div class="call warn"><span class="t">ランウェイの前提値が資料間で食い違っている</span>
  <p>この結論は現金3,200万（ランウェイ8ヶ月）を前提にしている。ただし <b>8/7 経営会議の定点表ではランウェイ24〜28ヶ月</b>と記載されており、3倍以上の開きがある。24ヶ月側（現金 約1億）が正であれば上記の枯渇は起きず、計画は成立する。<b>この1点で結論が反転するので、最優先で確定させたい。</b></p></div>
</div>
</section>

<section id="open">
<div class="qhead"><span class="qnum">要確定</span><h2>この計算を実データに寄せるために</h2></div>
<p class="qsub">今回のシミュレーションは仮置きパラメータが多い。実データで置き換えると結論が動く順に並べた。</p>
<div class="card">
  <h3>感度の高い順</h3>
  <ol class="tight">
    <li><b>ランウェイの実数</b> — 8ヶ月か24〜28ヶ月か。Q7の結論が反転する。</li>
    <li><b>「1億」の定義</b> — 月商かARRか。計画の形そのものが変わる。</li>
    <li><b>エンプラのPoC→本契約 転換率（45%と仮置き）</b> — 春の月商が ±250万動く。実績ゼロなので、東京通信・読みての2件が最初のサンプルになる。</li>
    <li><b>タレント事務所の実TAM（200社か500社か）</b> — プロダクト単独路線が生きるかどうかを決める。</li>
    <li><b>現状 月140万の内訳</b> — 何社 × いくらか。プロダクト単価30万の妥当性が検証できる。</li>
    <li><b>商談→受注の実CVR とリードタイム</b> — sales-ops-hub の Firestore／スプレッドシートに商談データがあるはずなので、そこから実測できる。</li>
    <li><b>案件あたりのデリバリー工数</b> — 現在の3案件（カロミー・ホワイトスコーピオン・コンサル）の実工数から逆算できる。</li>
  </ol>
  <div class="call ok"><span class="t">次にやると効くこと</span>
  <p>①〜②は経営会議で決める話。③〜⑦は実データを引けば埋まる。特に <b>⑥は sales-ops-hub 側に商談ログが溜まっている</b>ので、そこを集計すればファネルの仮置きを実測値に置き換えられる。</p></div>
</div>
</section>

<footer><div class="wrap">
Ceed toB 収益シミュレーション ／ 作成 2026-08-17 ／ モデルは月次コホート積み上げ（リードタイム・チャーン・TAM上限・デリバリーキャパを内生化）。
数値は明記のない限り仮置きパラメータであり、意思決定の前に実データでの補正が必要。
</div></footer>
</div>
"""

out = "/home/user/Output/tob-1oku-simulation-2026-08.html"
open(out, "w").write(HTML)
print("written:", out, len(HTML), "bytes")
