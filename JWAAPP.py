import streamlit as st
import json
import os
import math
from datetime import datetime

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ── persistence ──────────────────────────────────────────────────────────────
DATA_FILE = "dinos.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def record_fuse(data, dino_name, pack_label, count, actual, expected,
                p1_name, p1_cost, p2_name, p2_cost, leveled_up, new_level):
    if "fuse_history" not in data:
        data["fuse_history"] = []
    data["fuse_history"].append({
        "ts":         datetime.now().strftime("%Y-%m-%d %H:%M"),
        "dino":       dino_name,
        "pack":       pack_label,
        "count":      count,
        "actual":     actual,
        "expected":   round(expected, 1),
        "diff":       round(actual - expected, 1),
        "p1_name":    p1_name,
        "p1_cost":    p1_cost,
        "p2_name":    p2_name,
        "p2_cost":    p2_cost,
        "leveled_up": leveled_up,
        "new_level":  new_level,
    })
    return data

# ── game data ─────────────────────────────────────────────────────────────────
dna_prob = {10:0.404,20:0.242,30:0.198,40:0.081,50:0.056,
            60:0.008,70:0.006,80:0.003,90:0.002,100:0.001}
E = sum(dna_prob[k]*k for k in dna_prob)

FUSE_PACKS = {
    "1x":   {"count": 1,   "label": "Single Fuse"},
    "5x":   {"count": 5,   "label": "5x Fuse"},
    "20x":  {"count": 20,  "label": "20x Fuse"},
    "50x":  {"count": 50,  "label": "50x Fuse"},
    "100x": {"count": 100, "label": "100x Fuse"},
    "200x": {"count": 200, "label": "200x Fuse"},
}

Common_dna_needed    = {1:50,2:100,3:150,4:200,5:250,6:300,7:350,8:400,9:500,10:750,11:1000,12:1250,13:1500,14:2000,15:2500,16:3000,17:3500,18:4000,19:5000,20:7500,21:10000,22:12500,23:15000,24:20000,25:25000,26:30000,27:35000,28:40000,29:50000,30:75000}
Rare_dna_needed      = {6:100,7:100,8:150,9:200,10:250,11:300,12:350,13:400,14:500,15:750,16:1000,17:1250,18:1500,19:2000,20:2500,21:3000,22:3500,23:4000,24:5000,25:7500,26:10000,27:12500,28:15000,29:20000,30:25000}
Epic_dna_needed      = {11:150,12:100,13:150,14:200,15:250,16:300,17:350,18:400,19:500,20:750,21:1000,22:1250,23:1500,24:2000,25:2500,26:3000,27:3500,28:4000,29:5000,30:7500}
Legendary_dna_needed = {16:200,17:100,18:150,19:200,20:250,21:300,22:350,23:400,24:500,25:750,26:1000,27:1250,28:1500,29:2000,30:2500}
Unique_dna_needed    = {21:250,22:100,23:150,24:200,25:250,26:300,27:350,28:400,29:500,30:750}
Apex_dna_needed      = {26:300,27:100,28:150,29:200,30:250}

rarity_map = {"Common":Common_dna_needed,"Rare":Rare_dna_needed,
              "Epic":Epic_dna_needed,"Legendary":Legendary_dna_needed,
              "Unique":Unique_dna_needed,"Apex":Apex_dna_needed}

rarity_unlock_levels = {"Rare":5,"Epic":10,"Legendary":15,"Unique":20,"Apex":25}

RARITIES = ["Common","Rare","Epic","Legendary","Unique","Apex"]
RARITY_COLORS = {
    "Common":    "#aaaaaa",
    "Rare":      "#4a90e2",
    "Epic":      "#f1c40f",
    "Legendary": "#ff0000",
    "Unique":    "#51ff00",
    "Apex":      "#c8a951",
}

CHART_PALETTE = [
    "#4a90e2","#51ff00","#f1c40f","#ff6b6b","#c8a951",
    "#a78bfa","#34d399","#fb923c","#f472b6","#22d3ee",
]

# ── core functions ─────────────────────────────────────────────────────────────
def cumulative_sum(dna_dict, curr_level, target_level, current_dna):
    return sum(dna_dict[k] for k in range(curr_level + 1, target_level + 1)) - current_dna

def calc_total(dino_rarity, curr_level, target_level, p1_amt, p2_amt, curr_dna, unlocked):
    d = rarity_map[dino_rarity]
    adj = curr_level if unlocked else curr_level - 1
    x = cumulative_sum(d, adj, target_level, curr_dna)
    x = max(0, x)
    return (x, max(0, p1_amt*(x/E)), max(0, p2_amt*(x/E)))

def levels_needed(rarity, curr_level):
    req = rarity_unlock_levels.get(rarity, 0)
    return max(0, req - curr_level)

def build_tree_list(data, root_name):
    if root_name not in data:
        return []
    result, queue = [], [root_name]
    visited = set()
    while queue:
        name = queue.pop(0)
        if name in visited or name not in data:
            continue
        visited.add(name)
        result.append(name)
        d = data[name]
        if d.get("parent_1"): queue.append(d["parent_1"])
        if d.get("parent_2"): queue.append(d["parent_2"])
    return result

def build_parent_of(data, tree):
    parent_of = {}
    for n in tree:
        d = data.get(n, {})
        if d.get("parent_1"): parent_of[d["parent_1"]] = (n, "parent_1")
        if d.get("parent_2"): parent_of[d["parent_2"]] = (n, "parent_2")
    return parent_of

def dna_summary(data, name):
    d        = data[name]
    rarity   = d["rarity"]
    level    = d["level"]
    curr_dna = d["curr_dna"]
    unlocked = d["unlocked"]
    p1_name  = d.get("parent_1")
    p2_name  = d.get("parent_2")
    p1_amt   = d.get("parent_1_amount", 0)
    p2_amt   = d.get("parent_2_amount", 0)
    lvl_needed = levels_needed(rarity, level)
    target     = level + lvl_needed if lvl_needed > 0 else level
    total, need_p1, need_p2 = calc_total(rarity, level, target, p1_amt, p2_amt, curr_dna, unlocked)
    return {
        "name": name, "rarity": rarity, "level": level,
        "curr_dna": curr_dna, "unlocked": unlocked,
        "levels_needed": lvl_needed, "target_level": target,
        "total_dna_needed": round(total, 2),
        "p1_name": p1_name, "p2_name": p2_name,
        "need_p1_darted": round(need_p1, 2),
        "need_p2_darted": round(need_p2, 2),
    }

def fuse_amt_for_slot(data, child_name, slot):
    return (data[child_name].get("parent_1_amount", 50) if slot == "parent_1"
            else data[child_name].get("parent_2_amount", 50))

def ceil_to_fuse(raw, fuse_amt):
    if raw <= 0 or fuse_amt <= 0:
        return 0.0
    return float(math.ceil(raw / fuse_amt) * fuse_amt)

def leveling_cost_gross(data, name, child_rarity):
    """
    Gross DNA this creature needs to level up to the minimum level required
    to fuse into a hybrid of child_rarity — WITHOUT subtracting curr_dna,
    so the caller can offset leveling + fusing needs from the same DNA pool.

    The threshold is driven by the CHILD HYBRID's rarity, not this
    creature's own rarity.  e.g. a Common ingredient fusing into a Unique
    needs to be level 20; one fusing into an Epic only needs level 10.
    """
    d_info    = data[name]
    rarity    = d_info["rarity"]
    level     = d_info["level"]
    unlocked  = d_info["unlocked"]
    dna_table = rarity_map.get(rarity, {})

    req_level  = rarity_unlock_levels.get(child_rarity, 0)
    lvl_needed = max(0, req_level - level)
    if lvl_needed == 0:
        return 0
    target = level + lvl_needed
    adj    = level if unlocked else level - 1
    return max(0, sum(dna_table.get(k, 0) for k in range(adj + 1, target + 1)))

def compute_dart_burden(data, dino_name, parent_of, E):
    """
    Returns the TOTAL DNA burden for this creature (gross, before subtracting curr_dna):
      = leveling cost to reach the level the child hybrid requires
      + fuse DNA contribution up the chain.

    Level requirement is looked up from the CHILD hybrid's rarity so that,
    e.g., a Common ingredient fusing into a Unique must be level 20.
    """
    child_name, slot = parent_of.get(dino_name, (None, None))
    if child_name is None:
        return 0.0
    amt = fuse_amt_for_slot(data, child_name, slot)

    # Level requirement is set by what the child hybrid demands of its ingredients
    child_rarity = data[child_name]["rarity"]
    own_leveling = leveling_cost_gross(data, dino_name, child_rarity)

    grandchild_name, _ = parent_of.get(child_name, (None, None))
    if grandchild_name is None:
        # child_name is the root; derive fuse need from its dna_summary
        child_info = dna_summary(data, child_name)
        raw_fuse = (child_info["need_p1_darted"] if slot == "parent_1" else child_info["need_p2_darted"])
        return ceil_to_fuse(raw_fuse + own_leveling, amt)
    else:
        # child_raw already accounts for child's own leveling + child's fuse contribution
        child_raw       = compute_dart_burden(data, child_name, parent_of, E)
        child_curr      = data[child_name]["curr_dna"]
        child_remaining = max(0.0, child_raw - child_curr)
        fuse_part = ceil_to_fuse(child_remaining * (amt / E), amt) if child_remaining > 0 else 0.0
        return fuse_part + own_leveling

def unlock_progress(data, root_name):
    if root_name not in data:
        return 0.0, "unknown", ""
    info = dna_summary(data, root_name)
    if info["level"] >= 30:
        return 100.0, "MAX", "Level 30"
    if info["unlocked"] and info["total_dna_needed"] == 0:
        return 100.0, "READY", "Fully leveled"
    total_needed = info["total_dna_needed"]
    curr         = info["curr_dna"]
    if total_needed == 0 and curr == 0:
        return 0.0, "LOCKED", "No DNA"
    total_required = curr + total_needed
    pct = min(100.0, (curr / total_required) * 100) if total_required > 0 else 100.0
    if info["unlocked"]:
        status = "UNLOCKED"
        detail = f"Lv {info['level']} to Lv 30 needs {int(total_needed)} more DNA"
    elif info["levels_needed"] > 0:
        status = "LOCKED"
        detail = f"Needs {info['levels_needed']} more levels to unlock"
    else:
        status = "FUSING"
        detail = f"{int(curr)} / {int(total_required)} DNA"
    return pct, status, detail

def tree_dna_progress(data, root_name):
    tree = build_tree_list(data, root_name)
    sub  = tree[1:]
    if not sub:
        return None, 0, 0, []
    parent_of      = build_parent_of(data, tree)
    total_held     = 0.0
    total_required = 0.0
    per_node       = []
    for name in sub:
        if name not in data:
            continue
        curr_dna = data[name]["curr_dna"]
        burden   = compute_dart_burden(data, name, parent_of, E)
        contributed = min(curr_dna, burden)
        node_pct    = min(100.0, (curr_dna / burden * 100)) if burden > 0 else 100.0
        total_held     += contributed
        total_required += burden
        per_node.append((name, curr_dna, round(burden, 1), round(node_pct, 1)))
    pct = min(100.0, (total_held / total_required * 100)) if total_required > 0 else 100.0
    return round(pct, 1), round(total_held, 1), round(total_required, 1), per_node

def rename_dino(data, old_name, new_name):
    if old_name == new_name or old_name not in data or not new_name:
        return data
    data[new_name] = dict(data[old_name])
    data[new_name]["name"] = new_name
    del data[old_name]
    for d in data.values():
        if d.get("parent_1") == old_name: d["parent_1"] = new_name
        if d.get("parent_2") == old_name: d["parent_2"] = new_name
    return data

# ── chart builder ─────────────────────────────────────────────────────────────
def build_cumulative_chart(history_by_creature, mode, window):
    fig = go.Figure()
    layout_cfg = dict(
        plot_bgcolor  = "#0d0f14",
        paper_bgcolor = "#0d0f14",
        font          = dict(family="DM Sans", color="#e8e4dc", size=12),
        legend        = dict(bgcolor="#161b24", bordercolor="#2a2f3a",
                             borderwidth=1, font=dict(size=11)),
        xaxis = dict(
            title      = "Fuse event #",
            gridcolor  = "#1e2530",
            zerolinecolor = "#2a2f3a",
            tickfont   = dict(size=10),
        ),
        yaxis = dict(
            title      = "Cumulative DNA" if mode == "cumulative" else "DNA per event",
            gridcolor  = "#1e2530",
            zerolinecolor = "#2a2f3a",
            tickfont   = dict(size=10),
        ),
        hovermode  = "x unified",
        margin     = dict(l=50, r=20, t=30, b=50),
    )
    color_idx = 0
    drawn_expected = set()
    for dino_name, records in history_by_creature.items():
        windowed = records[-window:] if window else records
        if not windowed:
            continue
        color = CHART_PALETTE[color_idx % len(CHART_PALETTE)]
        color_idx += 1
        xs       = list(range(1, len(windowed) + 1))
        actuals  = [r["actual"]   for r in windowed]
        expecteds= [r["expected"] for r in windowed]
        if mode == "cumulative":
            cum_actual   = []
            cum_expected = []
            run_a = run_e = 0
            for a, e in zip(actuals, expecteds):
                run_a += a; run_e += e
                cum_actual.append(run_a)
                cum_expected.append(run_e)
            y_actual   = cum_actual
            y_expected = cum_expected
        else:
            y_actual   = actuals
            y_expected = expecteds
        fig.add_trace(go.Scatter(
            x=xs, y=y_actual,
            name=f"{dino_name} — actual",
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=5, color=color),
            hovertemplate="%{y:,.0f}<extra>" + dino_name + " actual</extra>",
        ))
        exp_key = dino_name
        if exp_key not in drawn_expected:
            drawn_expected.add(exp_key)
            fig.add_trace(go.Scatter(
                x=xs, y=y_expected,
                name=f"{dino_name} — expected",
                mode="lines",
                line=dict(color=color, width=1.5, dash="dot"),
                opacity=0.45,
                hovertemplate="%{y:,.0f}<extra>" + dino_name + " expected</extra>",
            ))
    fig.update_layout(**layout_cfg)
    return fig

# ── tree renderer ─────────────────────────────────────────────────────────────
LINE   = "#3a4555"
LINE_H = 32

def render_tree_html(data, node_name, parent_of, E, is_root=False):
    if node_name not in data:
        return ""
    info      = dna_summary(data, node_name)
    color     = RARITY_COLORS.get(info["rarity"], "#888")
    d         = data[node_name]
    p1        = d.get("parent_1")
    p2        = d.get("parent_2")
    is_hybrid = bool(p1 and p2)
    card_bg   = "#2d1f3d" if is_hybrid else "#161b24"

    if is_root:
        if info["levels_needed"] > 0:
            sub = f"Need {info['levels_needed']} more levels to unlock"
        elif info["total_dna_needed"] > 0:
            total = int(info["curr_dna"] + info["total_dna_needed"])
            sub = f"{int(info['curr_dna']):,} / {total:,} DNA"
        else:
            sub = f"{info['curr_dna']:,} DNA — ready"
    else:
        needed = compute_dart_burden(data, node_name, parent_of, E)
        have   = info["curr_dna"]
        if needed == 0:
            sub = '<span style="color:#51ff00">Satisfied</span>'
        else:
            pct_have = have / needed
            hcol = "#51ff00" if pct_have >= 1.0 else "#f1c40f" if pct_have >= 0.5 else "#ff6b6b"
            sub = f"Need <b>{int(needed):,}</b> darts<br><span style='color:{hcol}'>Have {have:,}</span>"

    uc = "#51ff00" if info["unlocked"] else "#555"
    ut = "Unlocked" if info["unlocked"] else "Locked"

    children = []
    if p1 and p1 in data: children.append(render_tree_html(data, p1, parent_of, E, False))
    if p2 and p2 in data: children.append(render_tree_html(data, p2, parent_of, E, False))
    has_ch = len(children) > 0

    card_html = f"""<div class="t-card {'t-card-parent' if has_ch else ''}"
  style="background:{card_bg};border-top:3px solid {color}">
  <div class="t-name"  style="color:{color}">{node_name}</div>
  <div class="t-rar"   style="color:{color}">{info['rarity']}</div>
  <div class="t-stats">Lv {info['level']} &nbsp;·&nbsp; {info['curr_dna']:,} DNA</div>
  <div class="t-sub">{sub}</div>
  <div class="t-lock"  style="color:{uc}">{ut}</div>
</div>"""

    if not has_ch:
        return f'<div class="t-node">{card_html}</div>'

    wraps = "".join(f'<div class="t-cwrap">{c}</div>' for c in children)
    return f"""<div class="t-node">
{card_html}
<div class="t-children">{wraps}</div>
</div>"""

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="JWA Tracker", page_icon="", layout="wide")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;600&display=swap');
html, body, [class*="css"] {{ font-family:'DM Sans',sans-serif; background:#0d0f14; color:#e8e4dc; }}
h1, h2, h3 {{ font-family:'Bebas Neue',sans-serif; letter-spacing:2px; }}

/* tree */
.t-scroll {{ overflow-x:auto; overflow-y:visible; padding:2rem 2rem 3rem; }}
.t-node {{ display:inline-flex; flex-direction:column; align-items:center; position:relative; }}
.t-card {{ border:1px solid #2a2f3a; border-radius:10px; padding:.7rem 1rem .65rem; min-width:150px; max-width:200px; text-align:center; position:relative; background:#161b24; flex-shrink:0; }}
.t-name  {{ font-family:'Bebas Neue',sans-serif; font-size:1.05rem; letter-spacing:1.2px; line-height:1.1; }}
.t-rar   {{ font-size:.6rem; text-transform:uppercase; letter-spacing:1.4px; opacity:.65; margin-top:.05rem; }}
.t-stats {{ font-size:.72rem; opacity:.55; margin-top:.3rem; }}
.t-sub   {{ font-size:.72rem; margin-top:.3rem; line-height:1.45; min-height:1.8em; }}
.t-lock  {{ font-size:.62rem; margin-top:.3rem; letter-spacing:.5px; }}
.t-card-parent::after {{ content:''; position:absolute; bottom:-{LINE_H}px; left:50%; transform:translateX(-50%); width:2px; height:{LINE_H}px; background:{LINE}; z-index:1; }}
.t-children {{ display:flex; flex-direction:row; align-items:flex-start; justify-content:center; padding-top:{LINE_H}px; position:relative; }}
.t-cwrap {{ display:inline-flex; flex-direction:column; align-items:center; padding:0 16px; position:relative; }}
.t-cwrap::before {{ content:''; position:absolute; top:0; left:0; right:0; height:2px; background:{LINE}; }}
.t-cwrap:first-child::before {{ left:50%; }}
.t-cwrap:last-child::before  {{ right:50%; }}
.t-cwrap:only-child::before  {{ display:none; }}
.t-cwrap::after {{ content:''; position:absolute; top:0; left:50%; transform:translateX(-50%); width:2px; height:{LINE_H}px; background:{LINE}; }}
.t-cwrap > .t-node {{ margin-top:{LINE_H}px; }}

/* dashboard */
.dash-card {{ background:#161b24; border:1px solid #2a2f3a; border-radius:12px; padding:1.1rem 1.3rem 1rem; position:relative; overflow:hidden; margin-bottom:.2rem; }}
.dash-card .rarity-bar {{ position:absolute; left:0; top:0; bottom:0; width:4px; border-radius:12px 0 0 12px; }}
.dash-card-name {{ font-family:'Bebas Neue',sans-serif; font-size:1.3rem; letter-spacing:1.5px; padding-left:8px; }}
.dash-card-meta {{ font-size:.78rem; opacity:.6; padding-left:8px; margin-top:.1rem; margin-bottom:.4rem; }}
.progress-track {{ background:#0d0f14; border-radius:99px; height:8px; margin:.4rem 0 .25rem; overflow:hidden; }}
.progress-track-thin {{ background:#0d0f14; border-radius:99px; height:5px; margin:.25rem 0 .2rem; overflow:hidden; }}
.progress-fill {{ height:100%; border-radius:99px; transition:width .3s ease; }}
.progress-label {{ font-size:.7rem; opacity:.5; letter-spacing:.5px; text-transform:uppercase; margin-top:.6rem; margin-bottom:0; }}
.dash-pct {{ font-family:'Bebas Neue',sans-serif; font-size:1.6rem; letter-spacing:1px; }}
.dash-sub-pct {{ font-family:'Bebas Neue',sans-serif; font-size:1rem; letter-spacing:1px; opacity:.85; }}
.dash-status {{ font-size:.7rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; border-radius:4px; padding:.1rem .4rem; display:inline-block; margin-left:.4rem; vertical-align:middle; }}
.dash-detail {{ font-size:.78rem; opacity:.55; margin-top:.1rem; padding-left:1px; }}
.sub-breakdown {{ margin-top:.6rem; padding-top:.5rem; border-top:1px solid #2a2f3a; }}
details.sub-details summary {{ cursor:pointer; list-style:none; outline:none; user-select:none; }}
details.sub-details summary::-webkit-details-marker {{ display:none; }}
details.sub-details summary::after {{ content:" [show]"; font-size:.7rem; opacity:.4; }}
details.sub-details[open] summary::after {{ content:" [hide]"; }}
.sub-row {{ display:flex; justify-content:space-between; align-items:center; font-size:.74rem; opacity:.75; margin-top:.25rem; }}
.sub-row-name {{ flex:1; }}
.sub-row-nums {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}

/* fuse */
.fuse-panel {{ background:#0f1a14; border:1px solid #1e8a5e; border-radius:12px; padding:1.4rem 1.6rem; margin-bottom:1.2rem; }}
.fuse-result-good {{ color:#51ff00; font-weight:700; }}
.fuse-result-avg  {{ color:#f1c40f; font-weight:700; }}
.fuse-result-bad  {{ color:#ff6b6b; font-weight:700; }}
.cost-pill {{ display:inline-block; background:#1e2530; border-radius:20px; padding:.2rem .75rem; font-size:.82rem; margin:.2rem .2rem 0 0; }}

/* history */
.hist-row {{
    display:grid;
    grid-template-columns:90px 80px 1fr 70px 70px 70px 90px;
    gap:0 .6rem; align-items:center;
    padding:.45rem .7rem; border-radius:7px;
    font-size:.78rem; margin-bottom:.2rem;
    background:#161b24; border:1px solid #1e2530;
}}
.hist-header {{
    font-size:.65rem; text-transform:uppercase; letter-spacing:.8px; opacity:.4;
    padding:.2rem .7rem .3rem;
    display:grid;
    grid-template-columns:90px 80px 1fr 70px 70px 70px 90px;
    gap:0 .6rem;
}}
.hist-good {{ color:#51ff00; }}
.hist-bad  {{ color:#ff6b6b; }}
.hist-avg  {{ color:#f1c40f; }}
.hist-summary {{
    background:#0d1a0f; border:1px solid #1e3a1e;
    border-radius:10px; padding:.9rem 1.2rem;
    display:grid; grid-template-columns:repeat(4,1fr);
    gap:.5rem; margin-bottom:1rem; font-size:.82rem;
}}
.hist-summary-item {{ text-align:center; }}
.hist-summary-val {{ font-family:'Bebas Neue',sans-serif; font-size:1.4rem; letter-spacing:1px; }}
.hist-summary-lbl {{ font-size:.65rem; opacity:.5; text-transform:uppercase; letter-spacing:.7px; }}

.stButton>button {{ background:#1e8a5e; color:white; border:none; border-radius:6px; font-family:'DM Sans',sans-serif; font-weight:600; }}
.stButton>button:hover {{ background:#25a870; }}
</style>
""", unsafe_allow_html=True)

# ── session state ──────────────────────────────────────────────────────────────
if "data"        not in st.session_state: st.session_state.data        = load_data()
if "form_key"    not in st.session_state: st.session_state.form_key    = 0
if "fuse_result" not in st.session_state: st.session_state.fuse_result = None
if "active_page" not in st.session_state: st.session_state.active_page = "dashboard"
if "tree_animal" not in st.session_state: st.session_state.tree_animal = None

data = st.session_state.data

# ── sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# JWA Tracker")
    st.markdown("---")
    st.markdown("### Add / Update Dinosaur")
    all_names = [k for k in data.keys() if k != "fuse_history"]

    with st.form(f"add_dino_{st.session_state.form_key}"):
        name     = st.text_input("Name", placeholder="e.g. Indoraptor")
        rarity   = st.selectbox("Rarity", RARITIES)
        level    = st.number_input("Current Level", min_value=1, max_value=30, value=10)
        curr_dna = st.number_input("Current DNA", min_value=0, value=0)
        unlocked = st.checkbox("Already Unlocked?")
        st.markdown("**Parents** *(leave blank if none)*")
        p1_name = st.selectbox("Parent 1", [""] + all_names)
        p1_amt  = st.number_input("Parent 1 fuse amount", min_value=0, value=50)
        p2_name = st.selectbox("Parent 2", [""] + all_names)
        p2_amt  = st.number_input("Parent 2 fuse amount", min_value=0, value=50)
        col1, col2 = st.columns(2)
        with col1: submitted = st.form_submit_button("Save")
        with col2: cleared   = st.form_submit_button("Clear")

        if submitted and name:
            data[name] = {
                "name": name, "rarity": rarity, "level": level,
                "curr_dna": curr_dna, "unlocked": unlocked,
                "parent_1": p1_name or None, "parent_2": p2_name or None,
                "parent_1_amount": p1_amt, "parent_2_amount": p2_amt,
            }
            save_data(data)
            st.session_state.data = data
            st.session_state.form_key += 1
            st.rerun()
        if cleared:
            st.session_state.form_key += 1
            st.rerun()

    st.markdown("---")
    st.markdown("### Update DNA")
    if all_names:
        with st.form("update_dna"):
            target_dino = st.selectbox("Dinosaur", all_names)
            new_dna     = st.number_input("New DNA amount", min_value=0, value=0)
            if st.form_submit_button("Update DNA"):
                data[target_dino]["curr_dna"] = new_dna
                save_data(data)
                st.session_state.data = data
                st.success("Updated!")

    st.markdown("---")
    st.markdown("### Delete Dinosaur")
    if all_names:
        with st.form("delete_dino"):
            del_name = st.selectbox("Select to delete", all_names)
            if st.form_submit_button("Delete"):
                del data[del_name]
                save_data(data)
                st.session_state.data = data
                st.rerun()

# ── main ───────────────────────────────────────────────────────────────────────
st.markdown("# Jurassic World Alive — DNA Tracker")

nav_cols = st.columns([1, 1, 1, 1, 4])
with nav_cols[0]:
    if st.button("Dashboard", use_container_width=True,
                 type="primary" if st.session_state.active_page == "dashboard" else "secondary"):
        st.session_state.active_page = "dashboard"; st.rerun()
with nav_cols[1]:
    if st.button("Tree", use_container_width=True,
                 type="primary" if st.session_state.active_page == "tree" else "secondary"):
        st.session_state.active_page = "tree"; st.rerun()
with nav_cols[2]:
    if st.button("Fuse", use_container_width=True,
                 type="primary" if st.session_state.active_page == "fuse" else "secondary"):
        st.session_state.active_page = "fuse"; st.rerun()
with nav_cols[3]:
    if st.button("History", use_container_width=True,
                 type="primary" if st.session_state.active_page == "history" else "secondary"):
        st.session_state.active_page = "history"; st.rerun()

st.markdown("---")

if not data or all(k == "fuse_history" for k in data.keys()):
    st.info("No dinosaurs yet. Add one in the sidebar to get started.")
    st.stop()

top_level = [n for n, d in data.items()
             if n != "fuse_history" and
             not any(d2.get("parent_1") == n or d2.get("parent_2") == n
                     for k2, d2 in data.items() if k2 != "fuse_history")]
if not top_level:
    top_level = [k for k in data.keys() if k != "fuse_history"]

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.active_page == "dashboard":
    st.markdown("## Dashboard")
    st.markdown("Click any card to open its evolution tree.")

    cards = []
    for name in top_level:
        pct, status, detail = unlock_progress(data, name)
        cards.append((name, pct, status, detail))
    cards.sort(key=lambda x: (x[2] == "MAX", x[1]))

    cols_per_row = 3
    for row_start in range(0, len(cards), cols_per_row):
        row_cards = cards[row_start : row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, (name, pct, status, detail) in zip(cols, row_cards):
            with col:
                info  = dna_summary(data, name)
                color = RARITY_COLORS.get(info["rarity"], "#888")
                if status == "MAX":        badge_bg, badge_fg = "#1a3a1a", "#51ff00"
                elif status == "UNLOCKED": badge_bg, badge_fg = "#1a2a3a", "#4a90e2"
                elif status == "FUSING":   badge_bg, badge_fg = "#2a2a0a", "#f1c40f"
                else:                      badge_bg, badge_fg = "#2a1a1a", "#ff6b6b"
                bar_color = "#51ff00" if pct >= 75 else "#f1c40f" if pct >= 40 else "#e05555"
                tree      = build_tree_list(data, name)
                n_parents = len(tree) - 1
                sub_pct, sub_held, sub_required, sub_nodes = tree_dna_progress(data, name)

                # ── build sub-section HTML (no newlines to avoid markdown parse breaks) ──
                sub_section = ""
                if sub_pct is not None:
                    sub_bar_color = "#51ff00" if sub_pct >= 75 else "#f1c40f" if sub_pct >= 40 else "#e05555"
                    rows_html = ""
                    for node_name, node_curr, node_burden, node_pct in sub_nodes:
                        node_color = RARITY_COLORS.get(data[node_name]["rarity"] if node_name in data else "Common", "#888")
                        if node_burden == 0:
                            val_str = "<span style='opacity:0.4'>not needed</span>"
                        elif node_pct >= 100:
                            val_str = f"{int(node_curr):,} / {int(node_burden):,} &nbsp;<span style='color:{sub_bar_color}'>done</span>"
                        else:
                            still = max(0, node_burden - node_curr)
                            val_str = f"{int(node_curr):,} / {int(node_burden):,} &nbsp;<span style='opacity:0.5'>need {int(still):,}</span>"
                        rows_html += (
                            f'<div class="sub-row">'
                            f'<span class="sub-row-name" style="color:{node_color}">{node_name}</span>'
                            f'<span class="sub-row-nums">{val_str}&nbsp;'
                            f'<span style="color:{sub_bar_color};min-width:40px;display:inline-block;text-align:right">{node_pct:.0f}%</span>'
                            f'</span></div>'
                        )
                    sub_section = (
                        f'<div class="sub-breakdown">'
                        f'<div class="progress-label">Sub-creature darted DNA &nbsp;<span style="opacity:.8">{sub_held:,.0f} / {sub_required:,.0f}</span></div>'
                        f'<div class="progress-track-thin"><div class="progress-fill" style="width:{sub_pct:.1f}%;background:{sub_bar_color}"></div></div>'
                        f'<details class="sub-details">'
                        f'<summary><span class="dash-sub-pct" style="color:{sub_bar_color}">{sub_pct:.1f}%</span></summary>'
                        f'{rows_html}'
                        f'</details></div>'
                    )

                # ── ancestors badge text ──
                ancestors_text = f'&nbsp;·&nbsp; {n_parents} ancestors' if n_parents > 0 else ''

                # ── card HTML as a single concatenated string — avoids blank lines
                #    that would cause Streamlit's markdown parser to escape HTML ──
                card_html = (
                    f'<div class="dash-card">'
                    f'<div class="rarity-bar" style="background:{color}"></div>'
                    f'<div style="padding-left:8px">'
                    f'<div class="dash-card-name">{name}</div>'
                    f'<div class="dash-card-meta"><span style="color:{color}">{info["rarity"]}</span>'
                    f' &nbsp;·&nbsp; Lv {info["level"]}{ancestors_text}</div>'
                    f'<div class="progress-label">Root DNA</div>'
                    f'<div class="progress-track"><div class="progress-fill"'
                    f' style="width:{pct:.1f}%;background:{bar_color}"></div></div>'
                    f'<span class="dash-pct" style="color:{bar_color}">{pct:.1f}%</span>'
                    f'<span class="dash-status" style="background:{badge_bg};color:{badge_fg}">{status}</span>'
                    f'<div class="dash-detail">{detail}</div>'
                    f'{sub_section}'
                    f'</div></div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

                if st.button(f"View {name}", key=f"dash_btn_{name}", use_container_width=True):
                    st.session_state.active_page = "tree"
                    st.session_state.tree_animal = name
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: TREE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_page == "tree":
    default_idx = 0
    if st.session_state.tree_animal and st.session_state.tree_animal in top_level:
        default_idx = top_level.index(st.session_state.tree_animal)

    col_sel, col_gap = st.columns([2, 3])
    with col_sel:
        selected = st.selectbox("View tree for", top_level, index=default_idx, key="tree_select")
    st.session_state.tree_animal = None

    tree      = build_tree_list(data, selected)
    parent_of = build_parent_of(data, tree)

    st.markdown(f"## {selected} — Evolution Tree")
    tree_html = render_tree_html(data, selected, parent_of, E, is_root=True)
    st.markdown(
        f'<div class="t-scroll"><div style="display:inline-flex;justify-content:center;width:100%">'
        f'{tree_html}</div></div>',
        unsafe_allow_html=True
    )

    with st.expander("Edit raw data"):
        st.caption("Editing the Name column will rename the dinosaur and update all parent references automatically.")
        edit_rows = []
        for n in tree:
            if n in data:
                d = data[n]
                edit_rows.append({
                    "original_name":   d["name"],
                    "name":            d["name"],
                    "rarity":          d["rarity"],
                    "level":           d["level"],
                    "curr_dna":        d["curr_dna"],
                    "unlocked":        d["unlocked"],
                    "parent_1":        d.get("parent_1") or "",
                    "parent_2":        d.get("parent_2") or "",
                    "parent_1_amount": d.get("parent_1_amount", 0),
                    "parent_2_amount": d.get("parent_2_amount", 0),
                })
        edited = st.data_editor(
            edit_rows, use_container_width=True, num_rows="fixed",
            column_config={
                "original_name":   st.column_config.TextColumn("original_name", disabled=True),
                "name":            st.column_config.TextColumn("Name"),
                "rarity":          st.column_config.SelectboxColumn("Rarity", options=RARITIES),
                "level":           st.column_config.NumberColumn("Level", min_value=1, max_value=30),
                "curr_dna":        st.column_config.NumberColumn("Current DNA", min_value=0),
                "unlocked":        st.column_config.CheckboxColumn("Unlocked?"),
                "parent_1":        st.column_config.TextColumn("Parent 1"),
                "parent_2":        st.column_config.TextColumn("Parent 2"),
                "parent_1_amount": st.column_config.NumberColumn("P1 Fuse Amt", min_value=0),
                "parent_2_amount": st.column_config.NumberColumn("P2 Fuse Amt", min_value=0),
            },
            column_order=["name","rarity","level","curr_dna","unlocked",
                          "parent_1","parent_2","parent_1_amount","parent_2_amount"],
            key=f"raw_editor_{selected}"
        )
        if st.button("Save table edits"):
            for row in edited:
                old_name = row["original_name"]
                new_name = row["name"].strip()
                if not new_name:
                    st.error(f"Name cannot be empty (was: {old_name})"); continue
                if new_name != old_name and old_name in data:
                    data = rename_dino(data, old_name, new_name)
                target = new_name if new_name in data else old_name
                if target in data:
                    data[target].update({
                        "name":            target,
                        "rarity":          row["rarity"],
                        "level":           int(row["level"]),
                        "curr_dna":        int(row["curr_dna"]),
                        "unlocked":        row["unlocked"],
                        "parent_1":        row["parent_1"] or None,
                        "parent_2":        row["parent_2"] or None,
                        "parent_1_amount": int(row["parent_1_amount"]),
                        "parent_2_amount": int(row["parent_2_amount"]),
                    })
            save_data(data)
            st.session_state.data = data
            st.success("Saved!")
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: FUSE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_page == "fuse":
    st.markdown("## Fuse DNA")
    fuseable = [n for n, d in data.items()
                if n != "fuse_history" and d.get("parent_1") and d.get("parent_2")]

    if not fuseable:
        st.warning("No hybrid dinosaurs found.")
    else:
        st.markdown('<div class="fuse-panel">', unsafe_allow_html=True)

        col_a, col_b = st.columns([2, 2])
        with col_a:
            fuse_dino_name = st.selectbox("Select Dinosaur to Fuse", fuseable, key="fuse_dino_select")
        with col_b:
            pack_key = st.selectbox("Fuse Pack", list(FUSE_PACKS.keys()),
                                    format_func=lambda k: FUSE_PACKS[k]["label"],
                                    key="fuse_pack_select")

        fuse_dino = data[fuse_dino_name]
        pack      = FUSE_PACKS[pack_key]
        count     = pack["count"]
        p1_name   = fuse_dino["parent_1"]
        p2_name   = fuse_dino["parent_2"]
        p1_amt    = fuse_dino.get("parent_1_amount", 50)
        p2_amt    = fuse_dino.get("parent_2_amount", 50)
        total_p1  = p1_amt * count
        total_p2  = p2_amt * count
        p1_have   = data[p1_name]["curr_dna"] if p1_name in data else 0
        p2_have   = data[p2_name]["curr_dna"] if p2_name in data else 0
        expected  = round(E * count, 1)

        st.markdown("#### Fuse Cost")
        c1, c2 = st.columns(2)
        with c1:
            p1_ok = p1_have >= total_p1
            st.markdown(f'<span class="cost-pill"><strong>{p1_name}</strong>: '
                        f'<span style="color:{"#51ff00" if p1_ok else "#ff6b6b"}">{total_p1} needed</span>'
                        f' / {p1_have} available</span>', unsafe_allow_html=True)
        with c2:
            p2_ok = p2_have >= total_p2
            st.markdown(f'<span class="cost-pill"><strong>{p2_name}</strong>: '
                        f'<span style="color:{"#51ff00" if p2_ok else "#ff6b6b"}">{total_p2} needed</span>'
                        f' / {p2_have} available</span>', unsafe_allow_html=True)

        if not p1_ok or not p2_ok:
            st.error(f"Not enough parent DNA for {count}x fuse(s).")

        st.markdown("---")
        st.markdown(f"#### Expected DNA from {pack['label']}: "
                    f"<span style='color:#f1c40f;font-size:1.2rem'>{expected}</span> "
                    f"<span style='opacity:0.6;font-size:0.85rem'>({E:.2f} avg/fuse x {count})</span>",
                    unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("#### Record Actual Fuse Result")

        with st.form("fuse_form"):
            actual_dna = st.number_input("Actual DNA received", min_value=0,
                                         value=int(expected), step=10)
            diff = actual_dna - expected
            if count > 1:
                per_avg = round(actual_dna / count, 1)
                if diff > 0:   st.markdown(f'<span class="fuse-result-good">+{diff:.0f} above expected ({per_avg} avg/fuse)</span>', unsafe_allow_html=True)
                elif diff < 0: st.markdown(f'<span class="fuse-result-bad">{diff:.0f} below expected ({per_avg} avg/fuse)</span>', unsafe_allow_html=True)
                else:          st.markdown(f'<span class="fuse-result-avg">Exactly average ({per_avg} avg/fuse)</span>', unsafe_allow_html=True)
            else:
                if actual_dna >= 30:   st.markdown('<span class="fuse-result-good">Great fuse!</span>', unsafe_allow_html=True)
                elif actual_dna == 10: st.markdown('<span class="fuse-result-bad">Min roll.</span>', unsafe_allow_html=True)
                else:                  st.markdown('<span class="fuse-result-avg">Average fuse.</span>', unsafe_allow_html=True)

            st.markdown(f"<span style='opacity:0.6;font-size:0.82rem'>Deducts <strong>{total_p1} {p1_name}</strong> and "
                        f"<strong>{total_p2} {p2_name}</strong> DNA, adds <strong>{actual_dna}</strong> DNA to "
                        f"<strong>{fuse_dino_name}</strong>.</span>", unsafe_allow_html=True)

            if st.form_submit_button(f"Apply {pack['label']}", disabled=(not p1_ok or not p2_ok)):
                if p1_name in data: data[p1_name]["curr_dna"] = max(0, data[p1_name]["curr_dna"] - total_p1)
                if p2_name in data: data[p2_name]["curr_dna"] = max(0, data[p2_name]["curr_dna"] - total_p2)
                data[fuse_dino_name]["curr_dna"] = data[fuse_dino_name].get("curr_dna", 0) + actual_dna
                dna_table  = rarity_map[fuse_dino["rarity"]]
                curr_level = data[fuse_dino_name]["level"]
                curr_dna   = data[fuse_dino_name]["curr_dna"]
                leveled_up = 0
                while curr_level < 30:
                    cost = dna_table.get(curr_level + 1)
                    if cost is None or curr_dna < cost: break
                    curr_dna -= cost; curr_level += 1; leveled_up += 1
                data[fuse_dino_name]["level"]    = curr_level
                data[fuse_dino_name]["curr_dna"] = curr_dna
                data = record_fuse(data, fuse_dino_name, pack["label"], count,
                                   actual_dna, expected, p1_name, total_p1,
                                   p2_name, total_p2, leveled_up, curr_level)
                save_data(data)
                st.session_state.data = data
                st.session_state.fuse_result = {
                    "dino": fuse_dino_name, "actual": actual_dna, "expected": expected,
                    "p1_name": p1_name, "p1_cost": total_p1,
                    "p2_name": p2_name, "p2_cost": total_p2,
                    "leveled_up": leveled_up, "new_level": curr_level, "new_dna": curr_dna,
                }
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.fuse_result:
            r = st.session_state.fuse_result
            diff         = r["actual"] - r["expected"]
            banner_color = "#1a3a1a" if diff >= 0 else "#3a1a1a"
            diff_str     = f"+{diff:.0f}" if diff >= 0 else f"{diff:.0f}"
            level_line   = (f"<br/><strong>Leveled up {r['leveled_up']}x to Lv {r['new_level']}</strong> "
                            f"(remaining DNA: {r['new_dna']})" if r["leveled_up"] > 0 else "")
            st.markdown(f"""<div style="background:{banner_color};border-radius:10px;
                            padding:1rem 1.4rem;margin-top:1rem;border:1px solid #2a3a2a">
  <strong>Fuse applied.</strong><br/>
  <strong>{r['dino']}</strong> +{r['actual']} DNA
  <span style="opacity:0.7">({diff_str} vs expected {r['expected']:.0f})</span><br/>
  <strong>{r['p1_name']}</strong> -{r['p1_cost']} &nbsp;|&nbsp;
  <strong>{r['p2_name']}</strong> -{r['p2_cost']}{level_line}
</div>""", unsafe_allow_html=True)
            if st.button("Dismiss"):
                st.session_state.fuse_result = None
                st.rerun()

        st.markdown("---")
        st.markdown("#### Fuse Pack Reference")
        ref_cols = st.columns(len(FUSE_PACKS))
        for col, (pk, pv) in zip(ref_cols, FUSE_PACKS.items()):
            col.metric(pv["label"], f"{round(E * pv['count'], 1)} DNA", f"{pv['count']}x fuse")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: HISTORY
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_page == "history":
    st.markdown("## Fuse History")

    history = data.get("fuse_history", [])

    if not history:
        st.info("No fuse history yet. Apply some fuses and they will appear here.")
        st.stop()

    all_fused = sorted(set(h["dino"] for h in history))

    ctrl1, ctrl2, ctrl3 = st.columns([3, 2, 2])

    with ctrl1:
        selected_creatures = st.multiselect(
            "Creatures",
            options=all_fused,
            default=all_fused[:1] if all_fused else [],
            help="Select one or more creatures to compare"
        )

    with ctrl2:
        window_label = st.selectbox(
            "Window",
            options=["Last 10", "Last 20", "Last 30", "All time"],
            index=3,
        )
        window_map = {"Last 10": 10, "Last 20": 20, "Last 30": 30, "All time": None}
        window = window_map[window_label]

    with ctrl3:
        chart_mode = st.selectbox(
            "View",
            options=["Cumulative sum", "Per fuse event"],
        )
        mode = "cumulative" if chart_mode == "Cumulative sum" else "per_fuse"

    if not selected_creatures:
        st.info("Select at least one creature above to see the chart.")
    elif not HAS_PLOTLY:
        st.warning("Install plotly to see the chart: `pip install plotly`")
    else:
        history_by_creature = {}
        for dino in selected_creatures:
            records = [h for h in history if h["dino"] == dino]
            history_by_creature[dino] = records

        fig = build_cumulative_chart(history_by_creature, mode, window)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")

    filtered_all = [h for h in history
                    if not selected_creatures or h["dino"] in selected_creatures]
    filtered_all = filtered_all[-window:] if window else filtered_all

    if filtered_all:
        total_fuses    = sum(h["count"]    for h in filtered_all)
        total_actual   = sum(h["actual"]   for h in filtered_all)
        total_expected = sum(h["expected"] for h in filtered_all)
        total_diff     = total_actual - total_expected
        avg_per_fuse   = total_actual / total_fuses if total_fuses else 0
        diff_color     = "#51ff00" if total_diff >= 0 else "#ff6b6b"
        diff_str       = f"+{total_diff:.0f}" if total_diff >= 0 else f"{total_diff:.0f}"

        st.markdown(f"""<div class="hist-summary">
  <div class="hist-summary-item">
    <div class="hist-summary-val">{total_fuses:,}</div>
    <div class="hist-summary-lbl">Total fuses</div>
  </div>
  <div class="hist-summary-item">
    <div class="hist-summary-val">{int(total_actual):,}</div>
    <div class="hist-summary-lbl">Total DNA</div>
  </div>
  <div class="hist-summary-item">
    <div class="hist-summary-val" style="color:{diff_color}">{diff_str}</div>
    <div class="hist-summary-lbl">vs Expected</div>
  </div>
  <div class="hist-summary-item">
    <div class="hist-summary-val">{avg_per_fuse:.1f}</div>
    <div class="hist-summary-lbl">Avg DNA / fuse</div>
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown("#### Log")
    filter_dino = st.selectbox("Filter table by creature",
                               ["All"] + all_fused, key="hist_table_filter")
    table_rows = [h for h in history if filter_dino == "All" or h["dino"] == filter_dino]
    table_rows = list(reversed(table_rows))

    st.markdown("""<div class="hist-header">
  <span>Date</span><span>Creature</span><span>Pack</span>
  <span>Got</span><span>Expected</span><span>Diff</span><span>Level after</span>
</div>""", unsafe_allow_html=True)

    for h in table_rows:
        diff     = h["diff"]
        diff_cls = "hist-good" if diff > 0 else "hist-bad" if diff < 0 else "hist-avg"
        diff_disp= f"+{diff:.0f}" if diff > 0 else f"{diff:.0f}"
        lvl_str  = (f"Lv {h['new_level']} <span style='color:#51ff00;font-size:.65rem'>(+{h['leveled_up']})</span>"
                    if h["leveled_up"] > 0 else f"Lv {h['new_level']}")
        dino_color = RARITY_COLORS.get(
            data[h["dino"]]["rarity"] if h["dino"] in data else "Common", "#aaa"
        )
        st.markdown(f"""<div class="hist-row">
  <span style="opacity:.5">{h['ts']}</span>
  <span style="color:{dino_color};font-weight:600">{h['dino']}</span>
  <span style="opacity:.7">{h['pack']}</span>
  <span><strong>{h['actual']}</strong></span>
  <span style="opacity:.5">{h['expected']:.0f}</span>
  <span class="{diff_cls}">{diff_disp}</span>
  <span>{lvl_str}</span>
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("Danger zone"):
        target_clear = st.selectbox("Clear history for", ["All"] + all_fused, key="clear_sel")
        if st.button("Clear selected history"):
            if target_clear == "All":
                data["fuse_history"] = []
            else:
                data["fuse_history"] = [h for h in history if h["dino"] != target_clear]
            save_data(data)
            st.session_state.data = data
            st.rerun()