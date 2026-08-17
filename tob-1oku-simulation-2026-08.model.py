#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ceed toB 1億円 到達シミュレーション v2 — 単位: 万円"""
import json
from dataclasses import dataclass

MONTHS = ["2026-09","2026-10","2026-11","2026-12","2027-01","2027-02","2027-03","2027-04","2027-05","2027-06"]
SPRING = 6                      # 2027-03
N = len(MONTHS)
BASE_MRR = 140.0

# ---------------------------------------------------------------- レーン定義
@dataclass
class Lane:
    key:str; short:str; name:str
    mrr:float; annual:float
    l2m:float; m2c:float; stage3:float
    lead_time:float; churn:float
    per_person:float; direct_cost:float      # 直接原価率(外注/生成コスト)
    tam:int; channel:str
    @property
    def l2c(self): return self.l2m*self.m2c*self.stage3

LANES=[
 Lane("product","プロダクト","① プロダクト量産（切り抜き自動化・WS型 → タレント事務所）",
      30,360, 0.20,0.25,1.0, 1.5,0.05, 10.0,0.30, 500,"アウトバウンド(テレアポ/フォーム)"),
 Lane("fde","FDE","② FDE型（社内データ基盤・売上予測 — 読みて型）",
      150,1800, 0.15,0.30,1.0, 2.0,0.03, 0.67,0.15, 300,"紹介＋既存アップセル"),
 Lane("ent","エンプラ","③ エンプラ大型（年間契約3,000万 — 東京通信型）",
      250,3000, 0.35,0.35,0.45, 5.0,0.02, 2.5,0.35, 500,"紹介(投資家/既存)主体"),
]
LM={l.key:l for l in LANES}
ENT_OUT_L2M=0.06     # エンプラをアウトバウンドで取る場合の商談化率

START_DEALS={"product":4.0,"fde":1.0,"ent":0.0}

# ---------------------------------------------------------------- 1. 目標判定
def growth_check():
    out=[]
    for lab,tgt in [("ARR 1億（月商833万）",10000/12),("月商1億（ARR 12億）",10000.0)]:
        m=tgt/BASE_MRR; g=m**(1/(SPRING+1))-1
        out.append(dict(label=lab,target=round(tgt),mult=round(m,1),mom=round(g*100,1)))
    return out

# ---------------------------------------------------------------- 2. TAM天井
def ceiling():
    out=[]
    for l in LANES:
        for tam in sorted({200,l.tam,1000}):
            mx=tam*l.l2c
            out.append(dict(lane=l.short,tam=tam,cvr=round(l.l2c*100,2),
                            max_deals=round(mx,1),max_mrr=round(mx*l.mrr),
                            max_arr=round(mx*l.mrr*12/10000,2)))
    return out

# ---------------------------------------------------------------- 3. シナリオ
SCENARIOS={
 "A": dict(name="A. エンプラ主導（Ken型: 大口1〜2社で売上7〜8割）",
           ent=2, ent_poc=1, fde=1, product=4),
 "B": dict(name="B. プロダクト主導（現状延長: +4社/月を7ヶ月継続）",
           ent=0, ent_poc=0, fde=1, product=24),
 "C": dict(name="C. バランス（エンプラ1社＋FDE3社＋プロダクト12社）",
           ent=1, ent_poc=1, fde=3, product=12),
}

def mix(sc):
    rows=[];tot=0
    spec=[("ent",sc["ent"],sc["ent_poc"]),("fde",sc["fde"],0),("product",sc["product"],0)]
    for k,d,poc in spec:
        l=LM[k]; rev=l.mrr*d+133*poc; tot+=rev
        rows.append(dict(key=k,lane=l.short,deals=d,poc=poc,unit=l.mrr,annual=l.annual,mrr=rev))
    for r in rows: r["share"]=round(r["mrr"]/tot*100,1) if tot else 0
    return rows,tot

# ---------------------------------------------------------------- 4. ファネル逆算
def funnel(rows,horizon=SPRING+1):
    out=[]
    for r in rows:
        l=LM[r["key"]]; ex=START_DEALS[r["key"]]
        net=r["deals"]+r["poc"]-ex
        churn=ex*(1-(1-l.churn)**horizon)
        gross=max(net+churn,0)
        if r["key"]=="ent":
            if gross<=0:
                out.append(dict(key=l.key,lane=l.short,need=0,stage2=0,meetings=0,leads=0,
                                leads_alt=0,leads_pm=0,meet_pm=0,cvr=round(l.l2c*100,2),
                                lt=l.lead_time,tam_pct=0)); continue
            poc=r["deals"]/l.stage3+r["poc"]
            mt=poc/l.m2c; ld=mt/l.l2m; alt=mt/ENT_OUT_L2M
            out.append(dict(key=l.key,lane=l.short,need=round(gross,1),stage2=round(poc,1),
                            meetings=round(mt,1),leads=round(ld,1),leads_alt=round(alt,0),
                            leads_pm=round(ld/horizon,1),meet_pm=round(mt/horizon,1),
                            cvr=round(l.l2c*100,2),lt=l.lead_time,tam_pct=round(ld/l.tam*100,1)))
        else:
            mt=gross/l.m2c; ld=mt/l.l2m
            out.append(dict(key=l.key,lane=l.short,need=round(gross,1),stage2=None,
                            meetings=round(mt,1),leads=round(ld,1),leads_alt=None,
                            leads_pm=round(ld/horizon,1),meet_pm=round(mt/horizon,1),
                            cvr=round(l.l2c*100,2),lt=l.lead_time,tam_pct=round(ld/l.tam*100,1)))
    return out

# ---------------------------------------------------------------- 5. 月次シム
def forward(fn,horizon=SPRING+1):
    plan={k:[0.0]*N for k in LM}
    for r in fn:
        k=r["key"]; L=r["leads"]
        if L<=0: continue
        if k=="ent":
            for t in range(2): plan[k][t]=L/2          # 春に間に合うのは9-10月投入のみ
            for t in range(2,N): plan[k][t]=L/2*0.6
        else:
            for t in range(horizon): plan[k][t]=L/horizon
    series={k:[0.0]*N for k in LM}; deals={k:[0.0]*N for k in LM}
    for k,l in LM.items():
        act=START_DEALS[k]; lt=l.lead_time
        for t in range(N):
            lo,hi=int(lt),int(lt)+1; frac=lt-lo
            new=0.0
            if t-lo>=0: new+=plan[k][t-lo]*(1-frac)*l.l2c
            if t-hi>=0: new+=plan[k][t-hi]*frac*l.l2c
            # TAM上限
            if act+new>l.tam*l.l2c: new=max(l.tam*l.l2c-act,0)
            act=act*(1-l.churn)+new
            deals[k][t]=act; series[k][t]=act*l.mrr
    tot=[sum(series[k][t] for k in LM) for t in range(N)]
    return plan,series,deals,tot

# ---------------------------------------------------------------- 6. 損益
def pnl(rows,tot):
    direct=sum(r["mrr"]*LM[r["key"]].direct_cost for r in rows)
    delivery=sum((r["deals"]+r["poc"])/LM[r["key"]].per_person for r in rows)
    head=delivery+3+4              # 営業3 + 経営/開発/コーポレート4
    labor=head*80
    fixed=80
    op=tot-direct-labor-fixed
    return dict(mrr=round(tot),direct=round(direct),delivery_head=round(delivery,1),
                head=round(head,1),labor=round(labor),fixed=fixed,op=round(op),
                gm=round((tot-direct)/tot*100,1) if tot else 0)

# ---------------------------------------------------------------- 7. エンプラ期限
def ent_deadline():
    l=LM["ent"]; out=[]
    for t in range(6):
        land=t+l.lead_time
        li=int(round(land))
        out.append(dict(inject=MONTHS[t],land=MONTHS[li] if li<N else "2027-07以降",
                        ok="✅ 春に間に合う" if li<=SPRING else "❌ 春に間に合わない"))
    return out

# ================================================================== 出力
def main():
    D={}
    print("="*80); print("【1】目標定義の判定 — 「1億」は月商かARRか"); print("="*80)
    D["growth"]=growth_check()
    for r in D["growth"]:
        print(f"  {r['label']:<22} 現状140万の {r['mult']:>5.1f}倍  → 必要成長率 {r['mom']:>5.1f}%/月 を7ヶ月連続")

    print(); print("="*80); print("【2】レーン別 TAM天井（吉田さん「3-4千万で頭打ち」の検証）"); print("="*80)
    D["ceiling"]=ceiling()
    print(f"  {'レーン':<10}{'TAM(社)':>9}{'L→受注':>9}{'最大受注':>9}{'最大月商':>10}{'最大ARR':>10}")
    for c in D["ceiling"]:
        print(f"  {c['lane']:<10}{c['tam']:>9}{c['cvr']:>8.2f}%{c['max_deals']:>9.1f}{c['max_mrr']:>10}{c['max_arr']:>9.2f}億")

    print(); print("="*80); print("【3】エンプラのリード投入期限（リードタイム5ヶ月）"); print("="*80)
    D["deadline"]=ent_deadline()
    for d in D["deadline"]:
        print(f"  リード投入 {d['inject']} → 本契約売上計上 {d['land']:<12} {d['ok']}")

    D["scen"]={}
    for sk,sc in SCENARIOS.items():
        rows,tot=mix(sc); fn=funnel(rows); plan,series,deals,tt=forward(fn); p=pnl(rows,tot)
        D["scen"][sk]=dict(name=sc["name"],rows=rows,total=tot,funnel=fn,
                           series=series,totals=tt,pnl=p,deals=deals)
        print(); print("="*80); print(f"【シナリオ {sk}】{sc['name']}"); print("="*80)
        print(f"  --- 春(2027-03)の売上ミックス ---")
        print(f"  {'レーン':<10}{'社数':>6}{'PoC':>5}{'単価/月':>9}{'年間契約':>10}{'月商':>8}{'構成比':>8}")
        for r in rows:
            print(f"  {r['lane']:<10}{r['deals']:>6}{r['poc']:>5}{r['unit']:>9.0f}{r['annual']:>10.0f}{r['mrr']:>8.0f}{r['share']:>7.1f}%")
        print(f"  {'合計':<10}{'':>6}{'':>5}{'':>9}{'':>10}{tot:>8.0f}   ARR {tot*12/10000:.2f}億")
        print(f"\n  --- ファネル逆算(7ヶ月合計) ---")
        print(f"  {'レーン':<10}{'必要受注':>9}{'PoC':>7}{'必要商談':>9}{'必要リード':>11}{'/月':>7}{'TAM消費':>9}")
        for r in fn:
            s2=f"{r['stage2']:.1f}" if r['stage2'] else "-"
            print(f"  {r['lane']:<10}{r['need']:>9.1f}{s2:>7}{r['meetings']:>9.1f}{r['leads']:>11.1f}{r['leads_pm']:>7.1f}{r['tam_pct']:>8.1f}%")
        tl=sum(r['leads'] for r in fn); tm=sum(r['meetings'] for r in fn)
        print(f"  {'合計':<10}{'':>9}{'':>7}{tm:>9.1f}{tl:>11.1f}{tl/7:>7.1f}")
        print(f"\n  --- 月次推移 ---")
        print(f"  {'月':<10}{'プロダクト':>10}{'FDE':>8}{'エンプラ':>9}{'合計':>9}{'ARR':>9}")
        for t in range(N):
            mk=" ←春" if t==SPRING else ""
            print(f"  {MONTHS[t]:<10}{series['product'][t]:>10.0f}{series['fde'][t]:>8.0f}{series['ent'][t]:>9.0f}{tt[t]:>9.0f}{tt[t]*12/10000:>8.2f}億{mk}")
        print(f"\n  --- 損益(春時点) ---")
        print(f"  売上 {p['mrr']}万 − 直接原価 {p['direct']}万 − 人件費 {p['labor']}万({p['head']}人) − 固定 {p['fixed']}万 = 営業利益 {p['op']:+}万/月  (粗利率 {p['gm']}%)")
        print(f"  デリバリー必要人数 {p['delivery_head']}人")

    D["months"]=MONTHS; D["spring"]=SPRING
    json.dump(D,open("/tmp/claude-0/-home-user-Output/9b2dbfd1-2f24-55ea-8a56-7a260be367aa/scratchpad/out.json","w"),ensure_ascii=False,indent=1)
    print("\n[saved] out.json")

main()
