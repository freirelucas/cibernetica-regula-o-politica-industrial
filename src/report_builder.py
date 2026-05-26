"""
Geração do HTML report a partir dos objetos vivos do pipeline.

build_html_report(df, cc_nodes, df_bc, burst_df, beauty_df,
                  cluster_labels, part_bc, part_cc, cite_counts,
                  keep_refs, SEEDS, P, n_bursting) -> str

A injeção dos dados no template está isolada em ``inject_template(js,
template_path=None)``, reutilizada pelo regenerador offline
(``report_from_json.py``).
"""
import json
import os
import sys
import numpy as np
import pandas as pd
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_template import inject_template  # noqa: E402

def _j(obj):
    return json.dumps(obj, ensure_ascii=False, default=str)

def _safe_int(v):
    try: return None if (v is None or (isinstance(v, float) and np.isnan(v))) else int(v)
    except: return None

def build_html_report(df, cc_nodes, df_bc, burst_df, beauty_df,
                      cluster_labels, part_bc, part_cc, cite_counts,
                      keep_refs, SEEDS, P, n_bursting):

    # Temporal
    for ax in ["Cyb","Reg","PolInd"]:
        df[f"_has_{ax}"] = df["axes"].apply(lambda s: 1 if ax in (s or "") else 0)
    td = {}
    for ax in ["Cyb","Reg","PolInd"]:
        for y,v in df[df.year.between(1960,2025)].groupby("year")[f"_has_{ax}"].sum().items():
            y=int(y)
            if y not in td: td[y]={"year":y,"Cyb":0,"Reg":0,"PolInd":0}
            td[y][ax]=int(v)
    temporal = sorted(td.values(), key=lambda x: x["year"])

    top20 = [{"year":_safe_int(r.year),"cited_by":int(r.cited_by),"axes":str(r.axes),
              "authors":str(r.authors)[:55],"title":str(r.title)[:85]}
             for r in df[~df.is_seed&(df.n_axes>=1)].nlargest(20,"cited_by").itertuples()]

    bridges = [{"year":_safe_int(r.year),"cited_by":int(r.cited_by),"axes":str(r.axes),
                "authors":str(r.authors)[:45],"title":str(r.title)[:80]}
               for r in df[df.n_axes>=2].sort_values("cited_by",ascending=False).head(15).itertuples()]

    burst_list = []
    if len(burst_df):
        top_b = (burst_df.sort_values("weight",ascending=False).drop_duplicates("ref_id").head(20)
                 .merge(cc_nodes[["ref_id","title","n_citations","authors"]], on="ref_id", how="left"))
        for r in top_b.itertuples():
            burst_list.append({"begin":_safe_int(r.begin),"end":_safe_int(r.end),
                "weight":round(float(r.weight),1),"title":str(getattr(r,"title",""))[:65],
                "authors":str(getattr(r,"authors",""))[:30]})

    csizes = Counter(part_bc.membership)
    clusters = []
    for cid,lbl in sorted(cluster_labels.items()):
        n=csizes.get(cid,0)
        if n<3: continue
        top3=df_bc[df_bc.cluster==cid].sort_values("cited_by",ascending=False).head(3)
        clusters.append({"id":cid,"label":lbl,"size":n,
            "papers":[{"title":str(r.title)[:60],"cited_by":int(r.cited_by),"year":_safe_int(r.year)}
                      for r in top3.itertuples()]})

    beauties=[{"year":int(r.year),"cited_by":int(r.cited_by),"B":round(float(r.B),1),
               "t_m":int(r.t_m),"axes":str(r.axes),"title":str(r.title)[:80]}
              for r in beauty_df.head(15).itertuples()]

    seeds=[{"id":wid,"ref":ref,
            "axis":"Cyb" if any(x in ref for x in ["Beer","Ashby","Espejo"]) else
                   "Reg" if any(x in ref for x in ["Hood","Margetts"]) else "PolInd"}
           for _,(wid,ref) in SEEDS.items()]

    stats={"corpus":int(len(df)),"seeds":len(SEEDS),
           "axes2":int((df.n_axes>=2).sum()),"axes3":int((df.n_axes==3).sum()),
           "cocit_n":int(len(keep_refs)),"cocit_e":int(cc_nodes.shape[0]),
           "clusters":int(len([c for c in clusters if c["size"]>=3])),
           "bursts":int(len(burst_df)),"bursting_refs":int(n_bursting),
           "generated":datetime.now().strftime("%Y-%m-%d %H:%M")}

    JS = (f"const STATS={_j(stats)};\n"
          f"const TEMPORAL={_j(temporal)};\n"
          f"const TOP20={_j(top20)};\n"
          f"const BRIDGES={_j(bridges)};\n"
          f"const BURSTS={_j(burst_list)};\n"
          f"const CLUSTERS={_j(clusters)};\n"
          f"const BEAUTIES={_j(beauties)};\n"
          f"const SEEDS={_j(seeds)};\n")

    return inject_template(JS)
