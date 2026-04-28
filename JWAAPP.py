import streamlit as st
import json
import os

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

# Multi-fuse expected values (per fuse, scaled by count but with bonuses)
# In JWA, multi-fuse packs guarantee minimums: 5x=no bonus, 20x=+10%, 50x=+20%, etc.
# We model as flat expected value per fuse attempt × count for simplicity,
# but allow user to override with actual result.
FUSE_PACKS = {
    "1x":   {"count": 1,   "label": "Single Fuse",   "min_guarantee": 10},
    "5x":   {"count": 5,   "label": "5× Fuse",       "min_guarantee": 10},
    "20x":  {"count": 20,  "label": "20× Fuse",      "min_guarantee": 10},
    "50x":  {"count": 50,  "label": "50× Fuse",      "min_guarantee": 10},
    "100x": {"count": 100, "label": "100× Fuse",     "min_guarantee": 10},
    "200x": {"count": 200, "label": "200× Fuse",     "min_guarantee": 10},
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
    "Apex":      "#241d03",
}

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

# ── helpers ───────────────────────────────────────────────────────────────────
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
        if d.get("parent_1"):
            queue.append(d["parent_1"])
        if d.get("parent_2"):
            queue.append(d["parent_2"])
    return result

def dna_summary(data, name):
    d = data[name]
    rarity   = d["rarity"]
    level    = d["level"]
    curr_dna = d["curr_dna"]
    unlocked = d["unlocked"]
    p1_name  = d.get("parent_1")
    p2_name  = d.get("parent_2")
    p1_amt   = d.get("parent_1_amount", 0)
    p2_amt   = d.get("parent_2_amount", 0)

    lvl_needed = levels_needed(rarity, level)
    target = level + lvl_needed if lvl_needed > 0 else level

    total, need_p1, need_p2 = calc_total(rarity, level, target, p1_amt, p2_amt, curr_dna, unlocked)

    return {
        "name": name,
        "rarity": rarity,
        "level": level,
        "curr_dna": curr_dna,
        "unlocked": unlocked,
        "levels_needed": lvl_needed,
        "target_level": target,
        "total_dna_needed": round(total, 2),
        "p1_name": p1_name,
        "p2_name": p2_name,
        "need_p1_darted": round(need_p1, 2),
        "need_p2_darted": round(need_p2, 2),
    }

def compute_dart_burden(data, dino_name, parent_of, E):
    child_name, slot = parent_of.get(dino_name, (None, None))
    if child_name is None:
        return 0.0

    grandchild_name, child_slot_in_gc = parent_of.get(child_name, (None, None))

    if grandchild_name is None:
        child_info = dna_summary(data, child_name)
        return (child_info["need_p1_darted"] if slot == "parent_1"
                else child_info["need_p2_darted"])
    else:
        child_true_burden = compute_dart_burden(data, child_name, parent_of, E)
        fuse_amt = (data[child_name].get("parent_1_amount", 50)
                    if slot == "parent_1"
                    else data[child_name].get("parent_2_amount", 50))
        if child_true_burden == 0:
            return 0.0
        return round(child_true_burden * (fuse_amt / E), 2)

def get_fuse_cost(dino, count):
    """Return (p1_cost, p2_cost) — total DNA consumed from each parent for `count` fuses."""
    p1_amt = dino.get("parent_1_amount", 0)
    p2_amt = dino.get("parent_2_amount", 0)
    return p1_amt * count, p2_amt * count

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="JWA Tracker", page_icon="🦕", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background: #0d0f14; color: #e8e4dc; }
h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 2px; }

.dino-card {
    background: #161b24;
    border: 1px solid #2a2f3a;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    position: relative;
}
.dino-card .rarity-bar {
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 4px;
    border-radius: 10px 0 0 10px;
}
.rarity-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    opacity: 0.7;
}
.dna-badge {
    background: #1e2530;
    border-radius: 6px;
    padding: 0.3rem 0.6rem;
    font-size: 0.85rem;
    display: inline-block;
    margin-top: 0.3rem;
}
.fuse-panel {
    background: #0f1a14;
    border: 1px solid #1e8a5e;
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
}
.fuse-result-good  { color: #51ff00; font-weight: 700; }
.fuse-result-avg   { color: #f1c40f; font-weight: 700; }
.fuse-result-bad   { color: #ff6b6b; font-weight: 700; }
.cost-pill {
    display: inline-block;
    background: #1e2530;
    border-radius: 20px;
    padding: 0.2rem 0.75rem;
    font-size: 0.82rem;
    margin: 0.2rem 0.2rem 0 0;
}
.stButton>button {
    background: #1e8a5e;
    color: white;
    border: none;
    border-radius: 6px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
}
.stButton>button:hover { background: #25a870; }
.fuse-btn>button {
    background: #7c3aed !important;
    font-size: 1rem !important;
    padding: 0.5rem 1.5rem !important;
}
.fuse-btn>button:hover { background: #6d28d9 !important; }
</style>
""", unsafe_allow_html=True)

# ── load state ────────────────────────────────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = load_data()
if "form_key" not in st.session_state:
    st.session_state.form_key = 0
if "fuse_result" not in st.session_state:
    st.session_state.fuse_result = None

data = st.session_state.data

# ── sidebar: add / edit dino ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🦕 JWA Tracker")
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
        with col1:
            submitted = st.form_submit_button("Save")
        with col2:
            cleared = st.form_submit_button("Clear")

        if submitted and name:
            data[name] = {
                "name": name,
                "rarity": rarity,
                "level": level,
                "curr_dna": curr_dna,
                "unlocked": unlocked,
                "parent_1": p1_name or None,
                "parent_2": p2_name or None,
                "parent_1_amount": p1_amt,
                "parent_2_amount": p2_amt,
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
            upd = st.form_submit_button("✏️ Update DNA")
            if upd:
                data[target_dino]["curr_dna"] = new_dna
                save_data(data)
                st.session_state.data = data
                st.success("Updated!")

    st.markdown("---")
    st.markdown("### Delete Dinosaur")
    if all_names:
        with st.form("delete_dino"):
            del_name = st.selectbox("Select to delete", all_names)
            del_btn  = st.form_submit_button("🗑️ Delete")
            if del_btn:
                del data[del_name]
                save_data(data)
                st.session_state.data = data
                st.rerun()

# ── main panel ────────────────────────────────────────────────────────────────
st.markdown("# Jurassic World Alive — DNA Tracker")

if not data:
    st.info("No dinosaurs yet. Add one in the sidebar to get started.")
else:
    top_level = [n for n,d in data.items()
                 if not any(d2.get("parent_1")==n or d2.get("parent_2")==n for d2 in data.values())]
    if not top_level:
        top_level = list(data.keys())

    # ── tabs: Tree view | Fuse ────────────────────────────────────────────────
    tab_tree, tab_fuse = st.tabs([" Evolution Tree", " Fuse"])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1 — TREE
    # ════════════════════════════════════════════════════════════════════════
    with tab_tree:
        col_sel, col_gap = st.columns([2,3])
        with col_sel:
            selected = st.selectbox("View tree for", top_level, key="tree_select")

        tree = build_tree_list(data, selected)

        parent_of = {}
        for n in tree:
            d = data.get(n, {})
            if d.get("parent_1"):
                parent_of[d["parent_1"]] = (n, "parent_1")
            if d.get("parent_2"):
                parent_of[d["parent_2"]] = (n, "parent_2")

        st.markdown("---")
        st.markdown(f"## {selected} — Evolution Tree")

        for i, dino_name in enumerate(tree):
            if dino_name not in data:
                continue
            info  = dna_summary(data, dino_name)
            color = RARITY_COLORS.get(info["rarity"], "#888")

            indent    = "&nbsp;" * (i * 4) if i > 0 else ""
            connector = "┗━ " if i > 0 else ""
            unlocked_icon = "✅" if info["unlocked"] else "🔒"
            is_root = (i == 0)

            if is_root:
                lvl_text = (f"Needs <strong>{info['levels_needed']}</strong> more levels to unlock"
                            if info["levels_needed"] > 0 else "Ready to fuse / already unlocked")
                badge_line = f"🧬 DNA needed to level up: <strong>{info['total_dna_needed']}</strong> &nbsp;→&nbsp; {lvl_text}"
            else:
                child_name, slot = parent_of.get(dino_name, (None, None))
                if child_name and child_name in data:
                    needed = compute_dart_burden(data, dino_name, parent_of, E)
                    badge_line = (f"🧬 DNA needed for <strong>{child_name}</strong>: "
                                  f"<strong>{needed}</strong> darted DNA &nbsp;|&nbsp; Have: {info['curr_dna']}")
                else:
                    badge_line = f"🧬 Current DNA: {info['curr_dna']}"

            p_info = ""
            if info["p1_name"]:
                p1_burden = compute_dart_burden(data, info["p1_name"], parent_of, E)
                p_info += f"&nbsp;&nbsp;🔸 <strong>{info['p1_name']}</strong> darts needed: <code>{p1_burden}</code>"
            if info["p2_name"]:
                p2_burden = compute_dart_burden(data, info["p2_name"], parent_of, E)
                p_info += f"&nbsp;&nbsp;🔸 <strong>{info['p2_name']}</strong> darts needed: <code>{p2_burden}</code>"

            is_hybrid = bool(info["p1_name"] and info["p2_name"])
            card_bg = "#2d1f3d" if is_hybrid else "#161b24"

            st.markdown(f"""
<div class="dino-card" style="background:{card_bg}">
  <div class="rarity-bar" style="background:{color}"></div>
  <div style="padding-left:8px">
    <span style="font-size:1.1rem;font-weight:600">{indent}{connector}{dino_name}</span>
    &nbsp;<span class="rarity-label" style="color:{color}">{info['rarity']}</span>
    &nbsp;{unlocked_icon}
    <br/>
    <span style="opacity:0.6;font-size:0.85rem">Level {info['level']} &nbsp;|&nbsp; DNA: {info['curr_dna']}</span>
    <br/>
    <div class="dna-badge">{badge_line}</div>
    <div style="margin-top:0.3rem;font-size:0.85rem">{p_info}</div>
  </div>
</div>
""", unsafe_allow_html=True)

        with st.expander("📋 Edit raw data"):
            edit_rows = []
            for n in tree:
                if n in data:
                    d = data[n]
                    edit_rows.append({
                        "name":             d["name"],
                        "rarity":           d["rarity"],
                        "level":            d["level"],
                        "curr_dna":         d["curr_dna"],
                        "unlocked":         d["unlocked"],
                        "parent_1":         d.get("parent_1") or "",
                        "parent_2":         d.get("parent_2") or "",
                        "parent_1_amount":  d.get("parent_1_amount", 0),
                        "parent_2_amount":  d.get("parent_2_amount", 0),
                    })

            edited = st.data_editor(
                edit_rows,
                use_container_width=True,
                num_rows="fixed",
                column_config={
                    "name":            st.column_config.TextColumn("Name", disabled=True),
                    "rarity":          st.column_config.SelectboxColumn("Rarity", options=RARITIES),
                    "level":           st.column_config.NumberColumn("Level", min_value=1, max_value=30),
                    "curr_dna":        st.column_config.NumberColumn("Current DNA", min_value=0),
                    "unlocked":        st.column_config.CheckboxColumn("Unlocked?"),
                    "parent_1":        st.column_config.TextColumn("Parent 1"),
                    "parent_2":        st.column_config.TextColumn("Parent 2"),
                    "parent_1_amount": st.column_config.NumberColumn("P1 Fuse Amt", min_value=0),
                    "parent_2_amount": st.column_config.NumberColumn("P2 Fuse Amt", min_value=0),
                },
                key=f"raw_editor_{selected}"
            )

            if st.button("💾 Save table edits"):
                for row in edited:
                    n = row["name"]
                    if n in data:
                        data[n].update({
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

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2 — FUSE
    # ════════════════════════════════════════════════════════════════════════
    with tab_fuse:
        st.markdown("## ⚗️ Fuse DNA")
        st.markdown("Select a hybrid dinosaur, choose your fuse pack, record the actual DNA you received, and the parents' DNA will be deducted automatically.")

        # Only hybrids can be fused (have both parents defined)
        fuseable = [n for n, d in data.items()
                    if d.get("parent_1") and d.get("parent_2")]

        if not fuseable:
            st.warning("No hybrid dinosaurs found. Add a dinosaur with both parents set to use Fuse.")
        else:
            st.markdown('<div class="fuse-panel">', unsafe_allow_html=True)

            col_a, col_b = st.columns([2, 2])
            with col_a:
                fuse_dino_name = st.selectbox(
                    "🦕 Select Dinosaur to Fuse",
                    fuseable,
                    key="fuse_dino_select"
                )
            with col_b:
                pack_key = st.selectbox(
                    "📦 Fuse Pack",
                    list(FUSE_PACKS.keys()),
                    format_func=lambda k: FUSE_PACKS[k]["label"],
                    key="fuse_pack_select"
                )

            fuse_dino = data[fuse_dino_name]
            pack      = FUSE_PACKS[pack_key]
            count     = pack["count"]

            p1_name = fuse_dino["parent_1"]
            p2_name = fuse_dino["parent_2"]
            p1_amt  = fuse_dino.get("parent_1_amount", 50)
            p2_amt  = fuse_dino.get("parent_2_amount", 50)

            total_p1_cost = p1_amt * count
            total_p2_cost = p2_amt * count

            p1_have = data[p1_name]["curr_dna"] if p1_name in data else 0
            p2_have = data[p2_name]["curr_dna"] if p2_name in data else 0

            expected_dna = round(E * count, 1)

            # ── Cost & affordability preview ─────────────────────────────────
            st.markdown("#### 💸 Fuse Cost")

            p1_ok = p1_have >= total_p1_cost
            p2_ok = p2_have >= total_p2_cost

            c1, c2 = st.columns(2)
            with c1:
                p1_color = "#51ff00" if p1_ok else "#ff6b6b"
                st.markdown(
                    f'<span class="cost-pill">🔸 <strong>{p1_name}</strong>: '
                    f'<span style="color:{p1_color}">{total_p1_cost} DNA needed</span> '
                    f'&nbsp;/&nbsp; {p1_have} available</span>',
                    unsafe_allow_html=True
                )
            with c2:
                p2_color = "#51ff00" if p2_ok else "#ff6b6b"
                st.markdown(
                    f'<span class="cost-pill">🔸 <strong>{p2_name}</strong>: '
                    f'<span style="color:{p2_color}">{total_p2_cost} DNA needed</span> '
                    f'&nbsp;/&nbsp; {p2_have} available</span>',
                    unsafe_allow_html=True
                )

            if not p1_ok or not p2_ok:
                st.error(f"⚠️ Not enough parent DNA for {count}× fuse{'s' if count > 1 else ''}.")

            st.markdown("---")

            # ── Expected value display ────────────────────────────────────────
            st.markdown(
                f"#### 📊 Expected DNA from {pack['label']}: "
                f"<span style='color:#f1c40f;font-size:1.2rem'>{expected_dna}</span> "
                f"<span style='opacity:0.6;font-size:0.85rem'>({E:.2f} avg per fuse × {count})</span>",
                unsafe_allow_html=True
            )

            st.markdown("---")

            # ── Actual DNA input ──────────────────────────────────────────────
            st.markdown("#### 🧬 Record Actual Fuse Result")

            with st.form("fuse_form"):
                actual_dna = st.number_input(
                    f"Actual DNA received from {pack['label']}",
                    min_value=0,
                    value=int(expected_dna),
                    step=10,
                    help=f"Enter the total DNA you actually got from all {count} fuse(s). Each fuse gives a multiple of 10."
                )

                # Per-fuse breakdown if multi
                if count > 1:
                    per_fuse_avg = round(actual_dna / count, 1)
                    diff = actual_dna - expected_dna
                    if diff > 0:
                        result_class = "fuse-result-good"
                        verdict = f"🎉 +{diff:.0f} above expected! ({per_fuse_avg} avg/fuse)"
                    elif diff < 0:
                        result_class = "fuse-result-bad"
                        verdict = f"😞 {diff:.0f} below expected ({per_fuse_avg} avg/fuse)"
                    else:
                        result_class = "fuse-result-avg"
                        verdict = f"😐 Exactly average ({per_fuse_avg} avg/fuse)"
                    st.markdown(f'<span class="{result_class}">{verdict}</span>', unsafe_allow_html=True)
                else:
                    diff = actual_dna - E
                    if actual_dna >= 30:
                        result_class = "fuse-result-good"
                        verdict = "🎉 Great fuse!"
                    elif actual_dna == 10:
                        result_class = "fuse-result-bad"
                        verdict = "😞 Min roll — tough luck."
                    else:
                        result_class = "fuse-result-avg"
                        verdict = "😐 Average fuse."
                    st.markdown(f'<span class="{result_class}">{verdict}</span>', unsafe_allow_html=True)

                st.markdown(
                    f"<span style='opacity:0.6;font-size:0.82rem'>"
                    f"This will deduct <strong>{total_p1_cost} {p1_name}</strong> DNA "
                    f"and <strong>{total_p2_cost} {p2_name}</strong> DNA, "
                    f"and add <strong>{actual_dna}</strong> DNA to <strong>{fuse_dino_name}</strong>."
                    f"</span>",
                    unsafe_allow_html=True
                )

                confirm = st.form_submit_button(
                    f"⚗️ Apply {pack['label']}",
                    disabled=(not p1_ok or not p2_ok)
                )

                if confirm:
                    # Deduct parent DNA
                    if p1_name in data:
                        data[p1_name]["curr_dna"] = max(0, data[p1_name]["curr_dna"] - total_p1_cost)
                    if p2_name in data:
                        data[p2_name]["curr_dna"] = max(0, data[p2_name]["curr_dna"] - total_p2_cost)

                    # Add fused DNA to dino
                    data[fuse_dino_name]["curr_dna"] = data[fuse_dino_name].get("curr_dna", 0) + actual_dna

                    # Check if it should level up (consume DNA in blocks)
                    dino_rarity = fuse_dino["rarity"]
                    dna_table   = rarity_map[dino_rarity]
                    curr_level  = data[fuse_dino_name]["level"]
                    curr_dna    = data[fuse_dino_name]["curr_dna"]

                    # Auto-level: consume DNA to level up as many times as possible
                    leveled_up = 0
                    while curr_level < 30:
                        next_level = curr_level + 1
                        cost = dna_table.get(next_level)
                        if cost is None or curr_dna < cost:
                            break
                        curr_dna  -= cost
                        curr_level += 1
                        leveled_up += 1

                    data[fuse_dino_name]["level"]   = curr_level
                    data[fuse_dino_name]["curr_dna"] = curr_dna

                    save_data(data)
                    st.session_state.data = data
                    st.session_state.fuse_result = {
                        "dino":      fuse_dino_name,
                        "actual":    actual_dna,
                        "expected":  expected_dna,
                        "p1_name":   p1_name,
                        "p1_cost":   total_p1_cost,
                        "p2_name":   p2_name,
                        "p2_cost":   total_p2_cost,
                        "leveled_up": leveled_up,
                        "new_level": curr_level,
                        "new_dna":   curr_dna,
                    }
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

            # ── Fuse result banner ────────────────────────────────────────────
            if st.session_state.fuse_result:
                r = st.session_state.fuse_result
                diff = r["actual"] - r["expected"]
                banner_color = "#1a3a1a" if diff >= 0 else "#3a1a1a"
                diff_str = f"+{diff:.0f}" if diff >= 0 else f"{diff:.0f}"

                level_line = ""
                if r["leveled_up"] > 0:
                    level_line = (f"<br/>🏆 <strong>Leveled up {r['leveled_up']}× "
                                  f"→ now Level {r['new_level']}</strong> "
                                  f"(remaining DNA: {r['new_dna']})")

                st.markdown(f"""
<div style="background:{banner_color};border-radius:10px;padding:1rem 1.4rem;margin-top:1rem;border:1px solid #2a3a2a">
  <strong>✅ Fuse applied!</strong><br/>
  🧬 <strong>{r['dino']}</strong> received <strong>{r['actual']} DNA</strong>
  &nbsp;<span style="opacity:0.7">({diff_str} vs expected {r['expected']:.0f})</span><br/>
  🔸 <strong>{r['p1_name']}</strong> −{r['p1_cost']} DNA &nbsp;|&nbsp;
  🔸 <strong>{r['p2_name']}</strong> −{r['p2_cost']} DNA
  {level_line}
</div>
""", unsafe_allow_html=True)

                if st.button("✖ Dismiss"):
                    st.session_state.fuse_result = None
                    st.rerun()

            # ── Fuse history hint ─────────────────────────────────────────────
            st.markdown("---")
            st.markdown("#### 📖 Fuse Pack Reference")
            ref_cols = st.columns(len(FUSE_PACKS))
            for col, (pk, pv) in zip(ref_cols, FUSE_PACKS.items()):
                exp = round(E * pv["count"], 1)
                col.metric(pv["label"], f"{exp} DNA", f"{pv['count']}× fuse")