import streamlit as st
import json
import os
import math

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

def compute_dart_burden(data, dino_name, parent_of, E):
    child_name, slot = parent_of.get(dino_name, (None, None))
    if child_name is None:
        return 0.0
    amt = fuse_amt_for_slot(data, child_name, slot)
    grandchild_name, _ = parent_of.get(child_name, (None, None))
    if grandchild_name is None:
        child_info = dna_summary(data, child_name)
        raw = (child_info["need_p1_darted"] if slot == "parent_1" else child_info["need_p2_darted"])
        return ceil_to_fuse(raw, amt)
    else:
        child_raw       = compute_dart_burden(data, child_name, parent_of, E)
        child_curr      = data[child_name]["curr_dna"]
        child_remaining = max(0.0, child_raw - child_curr)
        if child_remaining == 0:
            return 0.0
        return ceil_to_fuse(child_remaining * (amt / E), amt)

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

# ── tree HTML renderer ────────────────────────────────────────────────────────
def render_node_html(data, node_name, parent_of, E, is_root=False):
    if node_name not in data:
        return ""
    info     = dna_summary(data, node_name)
    color    = RARITY_COLORS.get(info["rarity"], "#888")
    d        = data[node_name]
    p1       = d.get("parent_1")
    p2       = d.get("parent_2")
    is_hybrid = bool(p1 and p2)
    card_bg  = "#2d1f3d" if is_hybrid else "#161b24"
    uc       = "#51ff00" if info["unlocked"] else "#666"
    ut       = "Unlocked" if info["unlocked"] else "Locked"

    if is_root:
        if info["levels_needed"] > 0:
            sub = f"Need {info['levels_needed']} more levels to unlock"
        elif info["total_dna_needed"] > 0:
            total = int(info["curr_dna"] + info["total_dna_needed"])
            sub = f"{int(info['curr_dna']):,} / {total:,} DNA"
        else:
            sub = f"{info['curr_dna']:,} DNA &mdash; ready"
    else:
        child_name, slot = parent_of.get(node_name, (None, None))
        if child_name and child_name in data:
            needed = compute_dart_burden(data, node_name, parent_of, E)
            if needed == 0:
                sub = f"<span style='color:#51ff00'>Satisfied</span> &middot; have {info['curr_dna']:,}"
            else:
                have     = info["curr_dna"]
                have_col = "#51ff00" if have >= needed else "#f1c40f" if have >= needed * 0.5 else "#ff6b6b"
                sub = (f"Need <strong>{int(needed):,}</strong> darts"
                       f"<br><span style='color:{have_col}'>Have {have:,}</span>")
        else:
            sub = f"{info['curr_dna']:,} DNA"

    card = f"""<div class="jwa-tnode" style="background:{card_bg};border-top-color:{color}">
  <div class="jwa-tnode-name" style="color:{color}">{node_name}</div>
  <div class="jwa-tnode-rarity" style="color:{color}">{info['rarity']}</div>
  <div class="jwa-tnode-stats">Lv {info['level']} &nbsp;&middot;&nbsp; {info['curr_dna']:,} DNA</div>
  <div class="jwa-tnode-sub">{sub}</div>
  <div style="font-size:0.62rem;color:{uc};margin-top:0.25rem;letter-spacing:0.5px">{ut}</div>
</div>"""

    children_html = ""
    if p1 and p1 in data:
        children_html += f"<li>{render_node_html(data, p1, parent_of, E)}</li>"
    if p2 and p2 in data:
        children_html += f"<li>{render_node_html(data, p2, parent_of, E)}</li>"

    if children_html:
        return f"{card}<ul>{children_html}</ul>"
    return card

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="JWA Tracker", page_icon="", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: #0d0f14;
    color: #e8e4dc;
}
h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 2px; }

/* ── visual tree ── */
.jwa-tree-wrap {
    overflow-x: auto;
    padding: 1rem 2rem 3rem;
}
.jwa-tree,
.jwa-tree ul,
.jwa-tree li {
    list-style: none;
    margin: 0;
    padding: 0;
}
.jwa-tree > ul { padding-top: 0; }
.jwa-tree ul {
    display: flex;
    justify-content: center;
    padding-top: 28px;
    position: relative;
}
/* vertical line from ul up to parent */
.jwa-tree ul::before {
    content: '';
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 2px;
    height: 28px;
    background: #3a4555;
}
/* suppress line above root */
.jwa-tree > ul::before { display: none; }
.jwa-tree li {
    position: relative;
    padding: 0 10px;
    display: flex;
    flex-direction: column;
    align-items: center;
}
/* horizontal bar across siblings */
.jwa-tree li::before,
.jwa-tree li::after {
    content: '';
    position: absolute;
    top: 0;
    width: 50%;
    height: 28px;
    border-top: 2px solid #3a4555;
}
.jwa-tree li::before { right: 50%; }
.jwa-tree li::after  { left: 50%; border-left: 2px solid #3a4555; }
/* only child — no horizontal bar */
.jwa-tree li:only-child::before,
.jwa-tree li:only-child::after { display: none; }
/* cap left end and right end */
.jwa-tree li:first-child::before { border: none; }
.jwa-tree li:last-child::after   { border-top: 2px solid #3a4555; border-left: none; }
.jwa-tree li:last-child::before  {
    border-right: 2px solid #3a4555;
    border-radius: 0 6px 0 0;
}
.jwa-tree li:first-child::after  { border-radius: 6px 0 0 0; }
/* vertical line from horizontal bar down to node */
.jwa-tree li > .jwa-tnode {
    position: relative;
    margin-top: 28px;
}
.jwa-tree li > .jwa-tnode::before {
    content: '';
    position: absolute;
    top: -28px;
    left: 50%;
    transform: translateX(-50%);
    width: 2px;
    height: 28px;
    background: #3a4555;
}
.jwa-tree li:only-child > .jwa-tnode::before { display: none; }

/* node card */
.jwa-tnode {
    border: 1px solid #2a2f3a;
    border-top: 3px solid;
    border-radius: 8px;
    padding: 0.65rem 0.9rem 0.6rem;
    min-width: 148px;
    max-width: 190px;
    text-align: center;
    background: #161b24;
}
.jwa-tnode-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.05rem;
    letter-spacing: 1.2px;
    line-height: 1.1;
}
.jwa-tnode-rarity {
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 1.4px;
    opacity: 0.65;
    margin-top: 0.05rem;
}
.jwa-tnode-stats {
    font-size: 0.72rem;
    opacity: 0.55;
    margin-top: 0.3rem;
}
.jwa-tnode-sub {
    font-size: 0.72rem;
    margin-top: 0.25rem;
    line-height: 1.4;
}

/* ── dashboard cards ── */
.dash-card {
    background: #161b24;
    border: 1px solid #2a2f3a;
    border-radius: 12px;
    padding: 1.1rem 1.3rem 1rem;
    position: relative;
    overflow: hidden;
    margin-bottom: 0.2rem;
}
.dash-card .rarity-bar {
    position: absolute; left: 0; top: 0; bottom: 0;
    width: 4px; border-radius: 12px 0 0 12px;
}
.dash-card-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.3rem; letter-spacing: 1.5px; padding-left: 8px;
}
.dash-card-meta {
    font-size: 0.78rem; opacity: 0.6; padding-left: 8px;
    margin-top: 0.1rem; margin-bottom: 0.4rem;
}
.progress-track {
    background: #0d0f14; border-radius: 99px;
    height: 8px; margin: 0.4rem 0 0.25rem; overflow: hidden;
}
.progress-track-thin {
    background: #0d0f14; border-radius: 99px;
    height: 5px; margin: 0.25rem 0 0.2rem; overflow: hidden;
}
.progress-fill { height: 100%; border-radius: 99px; transition: width 0.3s ease; }
.progress-label {
    font-size: 0.7rem; opacity: 0.5; letter-spacing: 0.5px;
    text-transform: uppercase; margin-top: 0.6rem; margin-bottom: 0;
}
.dash-pct { font-family: 'Bebas Neue', sans-serif; font-size: 1.6rem; letter-spacing: 1px; }
.dash-sub-pct { font-family: 'Bebas Neue', sans-serif; font-size: 1rem; letter-spacing: 1px; opacity: 0.85; }
.dash-status {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; border-radius: 4px; padding: 0.1rem 0.4rem;
    display: inline-block; margin-left: 0.4rem; vertical-align: middle;
}
.dash-detail { font-size: 0.78rem; opacity: 0.55; margin-top: 0.1rem; padding-left: 1px; }
.sub-breakdown { margin-top: 0.6rem; padding-top: 0.5rem; border-top: 1px solid #2a2f3a; }
details.sub-details summary { cursor: pointer; list-style: none; outline: none; user-select: none; }
details.sub-details summary::-webkit-details-marker { display: none; }
details.sub-details summary::after { content: " [show]"; font-size: 0.7rem; opacity: 0.4; }
details.sub-details[open] summary::after { content: " [hide]"; }
.sub-row { display: flex; justify-content: space-between; align-items: center; font-size: 0.74rem; opacity: 0.75; margin-top: 0.25rem; }
.sub-row-name { flex: 1; }
.sub-row-nums { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }

/* ── fuse ── */
.fuse-panel {
    background: #0f1a14; border: 1px solid #1e8a5e;
    border-radius: 12px; padding: 1.4rem 1.6rem; margin-bottom: 1.2rem;
}
.fuse-result-good { color: #51ff00; font-weight: 700; }
.fuse-result-avg  { color: #f1c40f; font-weight: 700; }
.fuse-result-bad  { color: #ff6b6b; font-weight: 700; }
.cost-pill {
    display: inline-block; background: #1e2530;
    border-radius: 20px; padding: 0.2rem 0.75rem;
    font-size: 0.82rem; margin: 0.2rem 0.2rem 0 0;
}
.stButton>button {
    background: #1e8a5e; color: white; border: none;
    border-radius: 6px; font-family: 'DM Sans', sans-serif; font-weight: 600;
}
.stButton>button:hover { background: #25a870; }
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
    all_names = list(data.keys())

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

nav_cols = st.columns([1, 1, 1, 5])
with nav_cols[0]:
    if st.button("Dashboard", use_container_width=True,
                 type="primary" if st.session_state.active_page == "dashboard" else "secondary"):
        st.session_state.active_page = "dashboard"
        st.rerun()
with nav_cols[1]:
    if st.button("Tree", use_container_width=True,
                 type="primary" if st.session_state.active_page == "tree" else "secondary"):
        st.session_state.active_page = "tree"
        st.rerun()
with nav_cols[2]:
    if st.button("Fuse", use_container_width=True,
                 type="primary" if st.session_state.active_page == "fuse" else "secondary"):
        st.session_state.active_page = "fuse"
        st.rerun()

st.markdown("---")

if not data:
    st.info("No dinosaurs yet. Add one in the sidebar to get started.")
    st.stop()

top_level = [n for n, d in data.items()
             if not any(d2.get("parent_1") == n or d2.get("parent_2") == n
                        for d2 in data.values())]
if not top_level:
    top_level = list(data.keys())

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
                if status == "MAX":      badge_bg, badge_fg = "#1a3a1a", "#51ff00"
                elif status == "UNLOCKED": badge_bg, badge_fg = "#1a2a3a", "#4a90e2"
                elif status == "FUSING":   badge_bg, badge_fg = "#2a2a0a", "#f1c40f"
                else:                      badge_bg, badge_fg = "#2a1a1a", "#ff6b6b"
                bar_color = "#51ff00" if pct >= 75 else "#f1c40f" if pct >= 40 else "#e05555"
                tree      = build_tree_list(data, name)
                n_parents = len(tree) - 1
                sub_pct, sub_held, sub_required, sub_nodes = tree_dna_progress(data, name)
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
                        rows_html += f"""<div class="sub-row">
  <span class="sub-row-name" style="color:{node_color}">{node_name}</span>
  <span class="sub-row-nums">{val_str} &nbsp;
    <span style="color:{sub_bar_color};min-width:40px;display:inline-block;text-align:right">{node_pct:.0f}%</span>
  </span>
</div>"""
                    sub_section = f"""<div class="sub-breakdown">
  <div class="progress-label">Sub-creature darted DNA &nbsp;<span style="opacity:0.8">{sub_held:,.0f} / {sub_required:,.0f}</span></div>
  <div class="progress-track-thin">
    <div class="progress-fill" style="width:{sub_pct:.1f}%;background:{sub_bar_color}"></div>
  </div>
  <details class="sub-details">
    <summary><span class="dash-sub-pct" style="color:{sub_bar_color}">{sub_pct:.1f}%</span></summary>
    {rows_html}
  </details>
</div>"""

                st.markdown(f"""<div class="dash-card">
  <div class="rarity-bar" style="background:{color}"></div>
  <div style="padding-left:8px">
    <div class="dash-card-name">{name}</div>
    <div class="dash-card-meta">
      <span style="color:{color}">{info['rarity']}</span> &nbsp;·&nbsp; Lv {info['level']}
      {'&nbsp;·&nbsp; ' + str(n_parents) + ' ancestors' if n_parents > 0 else ''}
    </div>
    <div class="progress-label">Root DNA</div>
    <div class="progress-track"><div class="progress-fill" style="width:{pct:.1f}%;background:{bar_color}"></div></div>
    <span class="dash-pct" style="color:{bar_color}">{pct:.1f}%</span>
    <span class="dash-status" style="background:{badge_bg};color:{badge_fg}">{status}</span>
    <div class="dash-detail">{detail}</div>
    {sub_section}
  </div>
</div>""", unsafe_allow_html=True)

                if st.button(f"View {name}", key=f"dash_btn_{name}", use_container_width=True):
                    st.session_state.active_page = "tree"
                    st.session_state.tree_animal = name
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: EVOLUTION TREE
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

    # ── visual tree ───────────────────────────────────────────────────────────
    node_html = render_node_html(data, selected, parent_of, E, is_root=True)
    st.markdown(f"""
<div class="jwa-tree-wrap">
  <div class="jwa-tree">
    <ul><li>{node_html}</li></ul>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── raw data editor ───────────────────────────────────────────────────────
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
            edit_rows,
            use_container_width=True,
            num_rows="fixed",
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
                    st.error(f"Name cannot be empty (was: {old_name})")
                    continue
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
    st.markdown("Select a hybrid, choose your fuse pack, record actual DNA received — parents are deducted automatically.")

    fuseable = [n for n, d in data.items() if d.get("parent_1") and d.get("parent_2")]

    if not fuseable:
        st.warning("No hybrid dinosaurs found. Add a dinosaur with both parents set to use Fuse.")
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
            p1_ok    = p1_have >= total_p1
            p1_color = "#51ff00" if p1_ok else "#ff6b6b"
            st.markdown(f'<span class="cost-pill"><strong>{p1_name}</strong>: '
                        f'<span style="color:{p1_color}">{total_p1} needed</span> / {p1_have} available</span>',
                        unsafe_allow_html=True)
        with c2:
            p2_ok    = p2_have >= total_p2
            p2_color = "#51ff00" if p2_ok else "#ff6b6b"
            st.markdown(f'<span class="cost-pill"><strong>{p2_name}</strong>: '
                        f'<span style="color:{p2_color}">{total_p2} needed</span> / {p2_have} available</span>',
                        unsafe_allow_html=True)

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
            actual_dna = st.number_input(
                "Actual DNA received", min_value=0, value=int(expected), step=10,
                help=f"Total DNA from all {count} fuse(s). Each fuse is a multiple of 10."
            )
            diff = actual_dna - expected
            if count > 1:
                per_avg = round(actual_dna / count, 1)
                if diff > 0:
                    st.markdown(f'<span class="fuse-result-good">+{diff:.0f} above expected ({per_avg} avg/fuse)</span>', unsafe_allow_html=True)
                elif diff < 0:
                    st.markdown(f'<span class="fuse-result-bad">{diff:.0f} below expected ({per_avg} avg/fuse)</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="fuse-result-avg">Exactly average ({per_avg} avg/fuse)</span>', unsafe_allow_html=True)
            else:
                if actual_dna >= 30:   st.markdown('<span class="fuse-result-good">Great fuse!</span>', unsafe_allow_html=True)
                elif actual_dna == 10: st.markdown('<span class="fuse-result-bad">Min roll.</span>', unsafe_allow_html=True)
                else:                  st.markdown('<span class="fuse-result-avg">Average fuse.</span>', unsafe_allow_html=True)

            st.markdown(f"<span style='opacity:0.6;font-size:0.82rem'>"
                        f"Deducts <strong>{total_p1} {p1_name}</strong> and "
                        f"<strong>{total_p2} {p2_name}</strong> DNA, "
                        f"adds <strong>{actual_dna}</strong> DNA to <strong>{fuse_dino_name}</strong>.</span>",
                        unsafe_allow_html=True)

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
                    curr_dna  -= cost; curr_level += 1; leveled_up += 1
                data[fuse_dino_name]["level"]    = curr_level
                data[fuse_dino_name]["curr_dna"] = curr_dna
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
            st.markdown(f"""<div style="background:{banner_color};border-radius:10px;padding:1rem 1.4rem;
                        margin-top:1rem;border:1px solid #2a3a2a">
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