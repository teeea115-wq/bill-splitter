import streamlit as st
import pandas as pd

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="โปรแกรมหารค่าข้าว Pro", page_icon="💸")

st.title("💸 แอปหารค่าข้าว (Vat + Service Charge)")

# --- ส่วนจัดการตัวแปร (Session State) ---
if 'people' not in st.session_state:
    st.session_state.people = []
if 'orders' not in st.session_state:
    st.session_state.orders = []

# --- 1. ตั้งค่าและเพิ่มเพื่อน ---
with st.expander("⚙️ ตั้งค่าภาษีและรายชื่อ", expanded=True):
    st.subheader("1.1 ตั้งค่าภาษี (ถ้าไม่มีให้ใส่ 0)")
    col_vat1, col_vat2 = st.columns(2)
    with col_vat1:
        service_charge_pct = st.number_input("Service Charge (%)", value=10, min_value=0, step=1)
    with col_vat2:
        vat_pct = st.number_input("VAT (%)", value=7, min_value=0, step=1)

    st.divider()
    
    st.subheader("1.2 เพิ่มชื่อเพื่อน")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_person = st.text_input("ใส่ชื่อเพื่อน", key="input_person")
    with col2:
        if st.button("เพิ่มคน"):
            if new_person and new_person not in st.session_state.people:
                st.session_state.people.append(new_person)
                st.success(f"เพิ่ม {new_person} แล้ว")
            elif new_person in st.session_state.people:
                st.warning("ชื่อนี้มีอยู่แล้ว")
                
    # แสดงรายชื่อ
    if st.session_state.people:
        st.info(f"👥 สมาชิก ({len(st.session_state.people)} คน): {', '.join(st.session_state.people)}")

# --- 2. ส่วนสั่งอาหาร ---
st.divider()
st.header("2. เพิ่มรายการอาหาร 🍗🍺")

if st.session_state.people:
    with st.container(border=True):
        menu_name = st.text_input("ชื่อเมนู")
        menu_price = st.number_input("ราคาป้าย (ไม่รวม Vat/Service)", min_value=0.0, step=10.0)
        
        st.write("เลือกคนหารเมนูนี้:")
        who_ate = st.multiselect("ใครกินบ้าง?", st.session_state.people, default=st.session_state.people)
        
        if st.button("บันทึกรายการ", type="primary"):
            if menu_name and menu_price > 0 and who_ate:
                st.session_state.orders.append({
                    "เมนู": menu_name,
                    "ราคาเต็ม": menu_price,
                    "คนกิน": who_ate, # เก็บเป็น List
                    "จำนวนคนหาร": len(who_ate)
                })
                st.success(f"บันทึก {menu_name} เรียบร้อย")
            else:
                st.error("กรุณากรอกข้อมูลให้ครบ")

    # ตารางแสดงรายการที่สั่ง
    if st.session_state.orders:
        st.subheader("รายการที่สั่งไปแล้ว")
        
        # จัดรูปแบบข้อมูลเพื่อแสดงผล
        display_data = []
        for idx, item in enumerate(st.session_state.orders):
            display_data.append({
                "ลำดับ": idx + 1,
                "เมนู": item["เมนู"],
                "ราคา": item["ราคาเต็ม"],
                "คนหาร": ", ".join(item["คนกิน"])
            })
            
        st.dataframe(pd.DataFrame(display_data).set_index("ลำดับ"))
        
        if st.button("ลบรายการล่าสุด ❌"):
            st.session_state.orders.pop()
            st.rerun()

# --- 3. สรุปยอดเงิน ---
st.divider()
st.header("3. สรุปยอดที่ต้องโอน 💰")

if st.session_state.orders and st.session_state.people:
    # คำนวณยอด
    raw_bill = {person: 0.0 for person in st.session_state.people}
    
    # 3.1 คิดราคาดิบ (Raw Cost)
    for order in st.session_state.orders:
        cost_per_head = order['ราคาเต็ม'] / order['จำนวนคนหาร']
        for person in order['คนกิน']:
            raw_bill[person] += cost_per_head
            
    # 3.2 คำนวณ Vat/Service และแสดงผล
    total_table_raw = 0
    total_table_net = 0
    
    # เตรียมข้อมูลใส่ตารางสรุป
    summary_data = []

    for person in st.session_state.people:
        cost = raw_bill[person]
        
        # สูตร: (ค่าอาหาร + Service Charge) + VAT
        service_amt = cost * (service_charge_pct / 100)
        pre_vat_total = cost + service_amt
        vat_amt = pre_vat_total * (vat_pct / 100)
        net_total = pre_vat_total + vat_amt
        
        summary_data.append({
            "ชื่อ": person,
            "ค่าอาหาร": f"{cost:,.2f}",
            f"Sv ({service_charge_pct}%)": f"{service_amt:,.2f}",
            f"Vat ({vat_pct}%)": f"{vat_amt:,.2f}",
            "ยอดสุทธิ (บาท)": f"{net_total:,.2f}"
        })
        
        total_table_raw += cost
        total_table_net += net_total

    # แสดงตารางสรุปสวยๆ
    st.table(pd.DataFrame(summary_data))
    
    st.success(f"**ยอดรวมทั้งโต๊ะ (NET): {total_table_net:,.2f} บาท**")

    # ส่วน Copy ไปวางแชท
    st.markdown("### 📋 Copy ไปวางใน Line/แชท")
    copy_text = f"🧾 สรุปยอดค่าอาหาร\n"
    for item in summary_data:
        copy_text += f"{item['ชื่อ']}: {item['ยอดสุทธิ (บาท)']} บ.\n"
    copy_text += f"---------------\nยอดรวม: {total_table_net:,.2f} บาท"
    
    st.code(copy_text)

# ปุ่ม Reset
st.divider()
if st.button("เริ่มใหม่ทั้งหมด (Reset)"):
    st.session_state.people = []
    st.session_state.orders = []
    st.rerun()
