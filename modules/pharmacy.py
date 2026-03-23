"""
Pharmacy Module — Premium Rebuild
Tabs: Alerts · Verify (ID + QR) · Orders · Inventory · Dispensing Log
"""
import streamlit as st
import json
import pandas as pd
from datetime import datetime

from modules.utils.qr_scanner import scan_qr
from modules.utils.db import (
    get_prescription_by_id, get_all_orders,
    get_orders_by_status, update_order_status,
    get_order_by_prescription, get_inventory,
    update_order, get_low_stock_items, update_inventory_stock
)
from modules.alerts import show_pharmacy_alerts

# ─────────────────── CSS ───────────────────
PHARMACY_CSS = """
<style>
/* Status pills */
.status-pill {
    display:inline-block; padding:3px 12px; border-radius:20px;
    font-size:11px; font-weight:700; letter-spacing:.6px; text-transform:uppercase;
}
.pill-pending    { background:#1a1000; color:#ffaa00; border:1px solid #ffaa0050; }
.pill-processing { background:#001020; color:#00aaff; border:1px solid #00aaff50; }
.pill-dispensed  { background:#150028; color:#cc44ff; border:1px solid #cc44ff50; }
.pill-completed  { background:#001a05; color:#00cc44; border:1px solid #00cc4450; }
.pill-cancelled  { background:#1a0000; color:#ff4444; border:1px solid #ff444450; }

/* Prescription card */
.rx-card {
    background:#0a0a0a; border:1px solid #1e1e1e; border-radius:12px;
    padding:20px; margin-bottom:16px;
}
.rx-card-header {
    display:flex; justify-content:space-between; align-items:center;
    margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid #1a1a1a;
}
.rx-id { font-size:18px; font-weight:800; color:#fff; letter-spacing:-0.5px; }
.rx-field-label { color:#555; font-size:11px; text-transform:uppercase; letter-spacing:.5px; margin:0; }
.rx-field-value { color:#e0e0e0; font-size:14px; font-weight:500; margin:3px 0 12px; }

/* QR drop zone */
.qr-dropzone {
    border:2px dashed #222; border-radius:12px; padding:40px 20px;
    text-align:center; background:#050505;
    transition:border-color .2s;
}

/* Scan result badge */
.scan-ok  { color:#00cc44; font-size:13px; font-weight:700; }
.scan-err { color:#ff4444; font-size:13px; font-weight:700; }

/* Inventory bar */
.inv-bar-wrap { background:#111; border-radius:4px; height:6px; margin-top:4px; }
.inv-bar      { height:6px; border-radius:4px; transition:width .3s; }

/* Timeline step */
.timeline {
    display:flex; gap:0; margin:16px 0;
    border:1px solid #1a1a1a; border-radius:10px; overflow:hidden;
}
.timeline-step {
    flex:1; padding:10px 8px; text-align:center; font-size:11px;
    font-weight:600; letter-spacing:.4px; color:#333; background:#0a0a0a;
    border-right:1px solid #1a1a1a; transition:all .2s;
}
.timeline-step:last-child { border-right:none; }
.ts-active   { color:#fff !important; background:#181818 !important; }
.ts-done     { color:#00cc44 !important; }
.ts-current  { color:#ffaa00 !important; background:#120e00 !important; }
</style>
"""


def _pill(status: str) -> str:
    cls = f"pill-{status}"
    icons = {"pending":"🟡","processing":"🔵","dispensed":"🟣","completed":"🟢","cancelled":"🔴"}
    return f'<span class="status-pill {cls}">{icons.get(status,"")} {status}</span>'


def show():
    st.markdown(PHARMACY_CSS, unsafe_allow_html=True)
    st.markdown("""
<div style="margin-bottom:8px;">
    <h1 style="margin:0;">💊 Pharmacy</h1>
    <p style="color:#555;font-size:13px;margin:4px 0 0;">
        Prescription verification · Order management · Inventory · Dispensing
    </p>
</div>""", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🚨 Alerts", "🔍 Verify & Dispense", "📦 Orders", "🗃️ Inventory", "📋 Dispense Log"
    ])

    with tab1:
        show_pharmacy_alerts()
    with tab2:
        show_verification()
    with tab3:
        show_orders()
    with tab4:
        show_inventory_enhanced()
    with tab5:
        show_dispense_log()


# ──────────────────────────────────────────────
# VERIFY & DISPENSE  (ID + QR)
# ──────────────────────────────────────────────

def show_verification():
    st.markdown("#### 🔍 Verify Prescription")

    method = st.radio(
        "", ["🆔 Prescription ID", "📷 Scan QR Code"],
        horizontal=True, label_visibility="collapsed", key="verify_method"
    )

    st.markdown("---")

    if method == "🆔 Prescription ID":
        col1, col2 = st.columns([3, 1])
        with col1:
            rx_id = st.text_input("Enter Prescription ID", placeholder="e.g. RX1a2b3c",
                                  label_visibility="collapsed")
        with col2:
            verify_btn = st.button("🔍 Verify", use_container_width=True)

        if verify_btn and rx_id:
            result = get_prescription_by_id(rx_id.strip())
            if result:
                st.markdown('<p class="scan-ok">✔ Valid Prescription Found</p>', unsafe_allow_html=True)
                _display_prescription_card(result)
                _dispense_controls(result.get("prescription_id"))
            else:
                st.markdown('<p class="scan-err">✘ Prescription not found</p>', unsafe_allow_html=True)
                st.caption("Double-check the ID or switch to QR scan.")

    else:
        # QR SCAN
        st.markdown("""
<div class="qr-dropzone">
    <p style="font-size:28px;margin:0">📷</p>
    <p style="color:#555;font-size:14px;margin:8px 0 0">Upload a QR code image to verify the prescription</p>
</div>""", unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Upload QR Image", type=["png", "jpg", "jpeg"],
            label_visibility="collapsed", key="ph_qr_upload"
        )

        if uploaded:
            with st.spinner("Scanning QR code…"):
                with open("temp_qr.png", "wb") as f:
                    f.write(uploaded.read())
                qr_data = scan_qr("temp_qr.png")

            col_img, col_result = st.columns([1, 2])
            with col_img:
                st.image("temp_qr.png", caption="Uploaded QR", use_container_width=True)

            with col_result:
                if not qr_data:
                    st.markdown('<p class="scan-err">✘ Could not read QR code. Try a clearer image.</p>',
                                unsafe_allow_html=True)
                else:
                    st.markdown('<p class="scan-ok">✔ QR Code Scanned Successfully</p>',
                                unsafe_allow_html=True)
                    try:
                        data = json.loads(qr_data)
                        _display_prescription_card_qr(data)
                        _dispense_controls(data.get("prescription_id"))
                    except json.JSONDecodeError:
                        # Plain prescription ID in QR
                        result = get_prescription_by_id(qr_data.strip())
                        if result:
                            _display_prescription_card(result)
                            _dispense_controls(result.get("prescription_id"))
                        else:
                            st.markdown(f'<p class="scan-err">✘ No prescription matches: <code>{qr_data}</code></p>',
                                        unsafe_allow_html=True)


def _display_prescription_card(result: dict):
    """Rich prescription card from DB record."""
    rx_id   = result.get("prescription_id", "—")
    patient = result.get("patient_name", "—")
    doctor  = result.get("doctor_name", "—")
    meds    = result.get("medicines", "—")
    dosage  = result.get("dosage", "—")
    caregiver = result.get("caregiver", "—")
    treatment = result.get("treatment_type", "—")
    date    = str(result.get("created_at", "—"))[:10]

    order = get_order_by_prescription(rx_id)
    status = order.get("status", "pending") if order else "untracked"

    st.markdown(f"""
<div class="rx-card">
    <div class="rx-card-header">
        <span class="rx-id">Rx {rx_id}</span>
        {_pill(status)}
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <div>
            <p class="rx-field-label">Patient</p>
            <p class="rx-field-value">👤 {patient}</p>
            <p class="rx-field-label">Doctor</p>
            <p class="rx-field-value">👨‍⚕️ Dr. {doctor}</p>
            <p class="rx-field-label">Caregiver</p>
            <p class="rx-field-value">👨‍👩‍👦 {caregiver}</p>
        </div>
        <div>
            <p class="rx-field-label">Treatment</p>
            <p class="rx-field-value">🏥 {treatment}</p>
            <p class="rx-field-label">Dosage Instructions</p>
            <p class="rx-field-value">📋 {dosage}</p>
            <p class="rx-field-label">Date Issued</p>
            <p class="rx-field-value">📅 {date}</p>
        </div>
    </div>
    <div style="margin-top:4px;">
        <p class="rx-field-label">Medicines</p>
        <p class="rx-field-value" style="color:#fff;font-size:15px;">💊 {meds}</p>
    </div>
</div>""", unsafe_allow_html=True)

    qr = result.get("qr_code_url")
    if qr:
        with st.expander("📱 View QR Code"):
            st.image(qr, width=180)


def _display_prescription_card_qr(data: dict):
    """Rich prescription card from QR JSON data."""
    rx_id   = data.get("prescription_id", "—")
    patient = data.get("patient_name", "—")
    doctor  = data.get("doctor_name", "—")
    meds    = data.get("medicines", "—")
    dosage  = data.get("dosage", "—")
    treatment = data.get("treatment_type", "—")
    date    = str(data.get("generated_date", "—"))[:10]

    order = get_order_by_prescription(rx_id) if rx_id != "—" else None
    status = order.get("status", "pending") if order else "untracked"

    st.markdown(f"""
<div class="rx-card">
    <div class="rx-card-header">
        <span class="rx-id">Rx {rx_id}</span>
        {_pill(status)}
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <div>
            <p class="rx-field-label">Patient</p>
            <p class="rx-field-value">👤 {patient}</p>
            <p class="rx-field-label">Doctor</p>
            <p class="rx-field-value">👨‍⚕️ Dr. {doctor}</p>
        </div>
        <div>
            <p class="rx-field-label">Treatment</p>
            <p class="rx-field-value">🏥 {treatment}</p>
            <p class="rx-field-label">Date Issued</p>
            <p class="rx-field-value">📅 {date}</p>
        </div>
    </div>
    <div>
        <p class="rx-field-label">Medicines</p>
        <p class="rx-field-value" style="color:#fff;font-size:15px;">💊 {meds}</p>
        <p class="rx-field-label">Dosage</p>
        <p class="rx-field-value">📋 {dosage}</p>
    </div>
</div>""", unsafe_allow_html=True)


def _dispense_controls(presc_id: str):
    """Order status timeline + dispense buttons."""
    if not presc_id:
        return
    order = get_order_by_prescription(presc_id)
    if not order:
        st.info("No order record found for this prescription.")
        return

    username = st.session_state.get("username", "pharmacy")
    status   = order.get("status", "pending")
    stages   = ["pending", "processing", "dispensed", "completed"]

    # Visual timeline
    def _ts_cls(s):
        idx_cur = stages.index(status) if status in stages else 0
        idx_s   = stages.index(s)
        if idx_s < idx_cur:  return "ts-done"
        if idx_s == idx_cur: return "ts-current"
        return ""

    labels = {"pending":"⏳ Pending","processing":"⚙️ Processing","dispensed":"📦 Dispensed","completed":"✅ Completed"}
    steps_html = "".join(
        f'<div class="timeline-step {_ts_cls(s)}">{labels[s]}</div>' for s in stages
    )
    st.markdown(f'<div class="timeline">{steps_html}</div>', unsafe_allow_html=True)

    if status == "completed":
        st.success("✅ This prescription has been fully completed.")
        return
    if status == "cancelled":
        st.error("❌ This order was cancelled.")
        return

    st.markdown("**Update Order Status:**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if status == "pending" and st.button("▶ Processing", key=f"proc_{presc_id}", use_container_width=True):
            update_order_status(presc_id, "processing", username)
            st.success("Status → Processing")
            st.rerun()
    with col2:
        if status in ("pending","processing") and st.button("📦 Dispense", key=f"disp_{presc_id}", use_container_width=True):
            update_order_status(presc_id, "dispensed", username)
            st.success("Status → Dispensed")
            st.rerun()
    with col3:
        if status != "completed" and st.button("✅ Complete", key=f"comp_{presc_id}", use_container_width=True):
            update_order_status(presc_id, "completed", username)
            st.success("Status → Completed")
            st.rerun()
    with col4:
        if status not in ("completed","cancelled") and st.button("❌ Cancel", key=f"canc_{presc_id}", use_container_width=True):
            update_order_status(presc_id, "cancelled", username)
            st.warning("Order cancelled.")
            st.rerun()

    # Pharmacy notes
    st.markdown("---")
    order_id = str(order.get("_id",""))
    current_notes = order.get("pharmacy_notes","")
    notes = st.text_area("📝 Pharmacy Notes", value=current_notes, key=f"ph_notes_{order_id}",
                         placeholder="Add dispensing notes, remarks…")
    if st.button("💾 Save Notes", key=f"save_notes_{order_id}"):
        update_order(order_id, {"pharmacy_notes": notes})
        st.success("Notes saved.")


# ──────────────────────────────────────────────
# ORDERS
# ──────────────────────────────────────────────

def show_orders():
    all_orders = get_all_orders()
    if not all_orders:
        st.info("No orders in the system yet.")
        return

    # Summary metrics
    def _cnt(s): return len([o for o in all_orders if o.get("status")==s])
    col1,col2,col3,col4,col5 = st.columns(5)
    col1.metric("📋 Total",      len(all_orders))
    col2.metric("🟡 Pending",    _cnt("pending"))
    col3.metric("🔵 Processing", _cnt("processing"))
    col4.metric("🟣 Dispensed",  _cnt("dispensed"))
    col5.metric("🟢 Completed",  _cnt("completed"))

    st.markdown("---")

    col1, col2, col3 = st.columns([2,2,2])
    with col1:
        status_filter = st.selectbox("Filter by Status",
            ["All","pending","processing","dispensed","completed","cancelled"],
            key="ph_status_filter")
    with col2:
        search_q = st.text_input("Search patient / Rx ID", placeholder="Type to filter…",
                                 label_visibility="collapsed")
    with col3:
        sort_by = st.selectbox("Sort by", ["Newest First","Oldest First","Patient A-Z"],
                               label_visibility="collapsed")

    orders = all_orders if status_filter=="All" else get_orders_by_status(status_filter)

    if search_q:
        q = search_q.lower()
        orders = [o for o in orders if q in o.get("patient_name","").lower()
                  or q in o.get("prescription_id","").lower()]

    if sort_by == "Oldest First":
        orders = sorted(orders, key=lambda o: o.get("created_at", datetime.min))
    elif sort_by == "Patient A-Z":
        orders = sorted(orders, key=lambda o: o.get("patient_name","").lower())

    if not orders:
        st.info("No orders match your filter.")
        return

    username = st.session_state.get("username","pharmacy")

    for order in orders:
        status   = order.get("status","pending")
        order_id = str(order.get("_id",""))
        presc_id = order.get("prescription_id","")
        patient  = order.get("patient_name","")
        doctor   = order.get("doctor_name","")
        age_h    = ""
        created  = order.get("created_at")
        if created:
            diff = (datetime.utcnow()-created).total_seconds()/3600
            age_h = f" · {round(diff,1)}h old"

        label = f"{presc_id}  ·  {patient}  ·  {status.upper()}{age_h}"

        with st.expander(label):
            # Status pill
            st.markdown(_pill(status), unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Patient:** {patient}")
                st.markdown(f"**Doctor:** {doctor}")
                st.markdown(f"**Treatment:** {order.get('treatment_type','—')}")
                st.markdown(f"**Created:** {str(created)[:16] if created else '—'}")
            with col2:
                st.markdown(f"**Medicines:** {order.get('medicines','—')}")
                st.markdown(f"**Dosage:** {order.get('dosage','—')}")
                if order.get("updated_by"):
                    st.markdown(f"**Last updated by:** {order['updated_by']}")
                if order.get("pharmacy_notes"):
                    st.info(f"📝 {order['pharmacy_notes']}")

            # Order timeline
            stages = ["pending","processing","dispensed","completed"]
            labels = {"pending":"⏳ Pending","processing":"⚙️ Processing",
                      "dispensed":"📦 Dispensed","completed":"✅ Done"}
            def _ts(s):
                if status not in stages: return ""
                i_cur = stages.index(status)
                i_s   = stages.index(s)
                if i_s < i_cur:  return "ts-done"
                if i_s == i_cur: return "ts-current"
                return ""
            steps = "".join(f'<div class="timeline-step {_ts(s)}">{labels[s]}</div>' for s in stages)
            st.markdown(f'<div class="timeline">{steps}</div>', unsafe_allow_html=True)

            st.markdown("---")

            # Edit fields
            curr_notes = order.get("pharmacy_notes","")
            curr_meds  = order.get("medicines","")
            notes     = st.text_area("Notes", value=curr_notes, key=f"n_{order_id}", height=68)
            edited_m  = st.text_input("Edit Medicines", value=curr_meds, key=f"m_{order_id}")

            c1,c2,c3,c4,c5 = st.columns(5)
            with c1:
                if status=="pending" and st.button("▶ Process", key=f"p_{order_id}"):
                    update_order_status(presc_id,"processing",username)
                    _save_changes(order_id,notes,curr_notes,edited_m,curr_meds)
                    st.rerun()
            with c2:
                if status in ("pending","processing") and st.button("📦 Dispense", key=f"d_{order_id}"):
                    update_order_status(presc_id,"dispensed",username)
                    _save_changes(order_id,notes,curr_notes,edited_m,curr_meds)
                    st.rerun()
            with c3:
                if status!="completed" and st.button("✅ Complete", key=f"c_{order_id}"):
                    update_order_status(presc_id,"completed",username)
                    _save_changes(order_id,notes,curr_notes,edited_m,curr_meds)
                    st.rerun()
            with c4:
                if status not in ("completed","cancelled") and st.button("❌ Cancel", key=f"x_{order_id}"):
                    update_order_status(presc_id,"cancelled",username)
                    st.rerun()
            with c5:
                if st.button("💾 Save", key=f"s_{order_id}"):
                    _save_changes(order_id,notes,curr_notes,edited_m,curr_meds)
                    st.success("Saved")
                    st.rerun()


def _save_changes(order_id, notes, old_notes, meds, old_meds):
    data={}
    if notes != old_notes: data["pharmacy_notes"]=notes
    if meds  != old_meds:  data["medicines"]=meds
    if data:
        update_order(order_id,data)


# ──────────────────────────────────────────────
# INVENTORY  (enhanced)
# ──────────────────────────────────────────────

def show_inventory_enhanced():
    from modules.alerts import INVENTORY
    from modules.utils.db import seed_inventory, update_inventory_stock

    inventory = get_inventory()
    if not inventory:
        seed_inventory(INVENTORY)
        inventory = get_inventory()

    if not inventory:
        st.info("No inventory data.")
        return

    # Metrics
    total  = len(inventory)
    low    = [i for i in inventory if i.get("stock",0) <= 15]
    crit   = [i for i in inventory if i.get("stock",0) <= 5]
    ok_cnt = total - len(low)

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("📦 Total Items", total)
    col2.metric("✅ In Stock",    ok_cnt)
    col3.metric("⚠️ Low Stock",  len(low))
    col4.metric("🔴 Critical",   len(crit))

    st.markdown("---")

    # Filter
    col1,col2 = st.columns([2,2])
    with col1:
        inv_filter = st.selectbox("Filter", ["All","Low Stock","Critical","In Stock"], key="inv_filter")
    with col2:
        search_inv = st.text_input("Search medicine", placeholder="Type to filter…",
                                   label_visibility="collapsed")

    display = inventory
    if inv_filter == "Low Stock":    display = low
    elif inv_filter == "Critical":   display = crit
    elif inv_filter == "In Stock":   display = [i for i in inventory if i.get("stock",0)>15]
    if search_inv:
        s = search_inv.lower()
        display = [i for i in display if s in i.get("medicine_name","").lower()]

    # Table view
    view_mode = st.radio("", ["📊 Table", "🃏 Cards"], horizontal=True,
                         label_visibility="collapsed", key="inv_view_mode")

    if view_mode == "📊 Table":
        df = pd.DataFrame([{
            "Medicine":   i.get("medicine_name",""),
            "Stock":      i.get("stock",0),
            "Status":     "🔴 Critical" if i.get("stock",0)<=5
                           else ("🟡 Low" if i.get("stock",0)<=15 else "🟢 OK"),
            "Reorder At": i.get("reorder_level",15),
            "Category":   i.get("category","—"),
            "Last Updated": str(i.get("updated_at",""))[:10] or "—",
        } for i in display])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        # Card view with inline stock edit
        for i in display:
            name  = i.get("medicine_name","")
            stock = i.get("stock",0)
            pct   = min(stock/100*100, 100)
            bar_c = "#ff2d2d" if stock<=5 else ("#ffaa00" if stock<=15 else "#00cc44")
            status_cls = "Critical" if stock<=5 else ("Low" if stock<=15 else "OK")

            with st.expander(f"{name}  ·  {stock} units  ·  {status_cls}"):
                col1,col2 = st.columns([3,1])
                with col1:
                    st.markdown(f"""
<div class="inv-bar-wrap"><div class="inv-bar" style="width:{pct}%;background:{bar_c}"></div></div>
<p style="color:#555;font-size:11px;margin:4px 0">{stock} / 100 units</p>""", unsafe_allow_html=True)
                with col2:
                    new_stock = st.number_input("Set stock", min_value=0, max_value=9999,
                                                value=stock, key=f"stk_{name}")
                    if st.button("Update", key=f"upd_{name}"):
                        update_inventory_stock(name, new_stock)
                        st.success(f"Updated → {new_stock}")
                        st.rerun()

    # CSV download
    df_all = pd.DataFrame([{
        "Medicine": i.get("medicine_name",""),
        "Stock": i.get("stock",0),
        "Category": i.get("category",""),
    } for i in inventory])
    st.download_button("⬇️ Export Inventory CSV", df_all.to_csv(index=False).encode(),
                       "inventory.csv", "text/csv", key="inv_csv_dl")


# ──────────────────────────────────────────────
# DISPENSE LOG
# ──────────────────────────────────────────────

def show_dispense_log():
    """Show all dispensed/completed orders as a log."""
    all_orders = get_all_orders()
    dispensed = [o for o in all_orders if o.get("status") in ("dispensed","completed")]

    if not dispensed:
        st.info("No dispensed orders yet.")
        return

    st.markdown(f"**{len(dispensed)} dispensed orders**")

    # Stats
    completed = [o for o in dispensed if o.get("status")=="completed"]
    col1,col2 = st.columns(2)
    col1.metric("📦 Dispensed",  len([o for o in dispensed if o.get("status")=="dispensed"]))
    col2.metric("✅ Completed",  len(completed))

    st.markdown("---")

    rows = []
    for o in dispensed:
        rows.append({
            "Rx ID":    o.get("prescription_id","—"),
            "Patient":  o.get("patient_name","—"),
            "Doctor":   o.get("doctor_name","—"),
            "Medicines":o.get("medicines","—"),
            "Status":   o.get("status","—").upper(),
            "Updated":  str(o.get("updated_at",""))[:16] or "—",
            "By":       o.get("updated_by","—"),
            "Notes":    o.get("pharmacy_notes",""),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇️ Export Dispense Log CSV",
        df.to_csv(index=False).encode(),
        f"dispense_log_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv", key="disp_log_csv"
    )