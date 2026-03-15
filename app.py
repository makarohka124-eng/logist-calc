import streamlit as st
from datetime import datetime, timedelta
import pytz

# Настройка страницы
st.set_page_config(page_title="Logist Pro Calc", layout="centered", page_icon="🚛")

# Время CET
cet_zone = pytz.timezone('Europe/Berlin')
now_cet = datetime.now(cet_zone)

st.title("🚛 Калькулятор Логиста")

# --- БЛОК 1: ВРЕМЯ ВЫЕЗДА ---
st.subheader("📅 Время выезда")
use_current = st.checkbox("Считать от текущего времени (сейчас)", value=True)

if use_current:
    start_dt = now_cet
    st.info(f"🚀 Старт: **Сегодня, {start_dt.strftime('%H:%M')}** (по CET)")
else:
    col1, col2 = st.columns(2)
    with col1:
        sd = st.date_input("Выбери дату", now_cet.date())
    with col2:
        st_time = st.time_input("Выбери время", now_cet.time())
    start_dt = datetime.combine(sd, st_time)
    start_dt = cet_zone.localize(start_dt)

st.divider()

# --- БЛОК 2: ПАРАМЕТРЫ ---
col_a, col_b = st.columns(2)
with col_a:
    dist = st.number_input("Дистанция (км):", min_value=1, value=1000)
    speed = st.slider("Скорость (км/ч):", 40, 90, 70)
    ferry_option = st.selectbox("Паром:", ["Без парома", "Паром (1 час)", "Паром (2 часа)"])
    
with col_b:
    mode = st.radio("Режим:", ["Одиночка", "Экипаж"])
    already_driven = st.number_input("Уже проехал сегодня (ч):", min_value=0.0, max_value=18.0, value=0.0, step=0.5)

ferry_time = 1 if ferry_option == "Паром (1 час)" else (2 if ferry_option == "Паром (2 часа)" else 0)

# --- МАТЕМАТИКА ---
pure_drive = dist / speed

if "Одиночка" in mode:
    limit = 9.0
    # Сколько осталось до конца первой смены
    left_in_first = max(0.0, limit - already_driven)
    
    if pure_drive <= left_in_first:
        # Приезд в текущую смену
        drive_last_day = already_driven + pure_drive
        total_breaks = 1 if (already_driven < 4.5 and drive_last_day > 4.5) else 0
        total_rests = 0
    else:
        # Нужны отстои
        rem_drive = pure_drive - left_in_first
        full_shifts = rem_drive // limit
        drive_last_day = rem_drive % limit
        # Если остаток 0, значит приехал ровно в конце смены
        if drive_last_day == 0: drive_last_day = limit
        
        total_breaks = (1 if already_driven < 4.5 else 0) + (full_shifts * 2) + (1 if (drive_last_day > 4.5) else 0)
        total_rests = (full_shifts + 1) * 9.0
    
    total_way = pure_drive + total_breaks + total_rests + ferry_time
    dh_val = int(limit - drive_last_day)

else:
    # Экипаж
    limit = 18.0
    left_in_first = max(0.0, limit - already_driven)
    
    if pure_drive <= left_in_first:
        drive_last_day = already_driven + pure_drive
        rests = 0
    else:
        rem_drive = pure_drive - left_in_first
        full_shifts = rem_drive // limit
        drive_last_day = rem_drive % limit
        if drive_last_day == 0: drive_last_day = limit
        
        rests = full_shifts + 1
    
    total_way = pure_drive + (rests * 9.0) + ferry_time
    dh_val = int(limit - drive_last_day)

# Финал
arrival = start_dt + timedelta(hours=total_way)

# Строка для отчета (1/2 или 2/2 по времени на Windows)
check_val = "1/2" if now_cet.hour < 12 else "2/2"
arrival_str = arrival.strftime('%d.%m %H:%M')
work_string = f"{check_val} ETA  {arrival_str}CET D/H {dh_val}"

st.divider()
st.success(f"## 🏁 ПРИБЫТИЕ: {arrival.strftime('%A, %H:%M')} (CET)")

st.subheader("📝 Скопируй строку для отчета:")
st.code(work_string)

st.caption(f"Чистое вождение: {pure_drive:.1f} ч. | Всего в пути: {total_way:.1f} ч.")
