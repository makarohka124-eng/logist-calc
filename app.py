import streamlit as st
from datetime import datetime, timedelta
import pytz

# Настройка страницы
st.set_page_config(page_title="Logist Pro v3", layout="centered", page_icon="🚛")

# Настройка времени CET
cet_zone = pytz.timezone('Europe/Berlin')
now_cet = datetime.now(cet_zone)

st.title("🚛 Профи-Калькулятор v3")

# --- БЛОК 1: ВРЕМЯ ВЫЕЗДА ---
st.subheader("📅 Время старта")
use_current_time = st.checkbox("Считать от текущего времени (сейчас)", value=True)

if use_current_time:
    start_dt = now_cet
    st.info(f"🚀 Старт будет посчитан от: **{now_cet.strftime('%H:%M')}** (CET)")
else:
    col_d, col_t = st.columns(2)
    with col_d:
        start_date = st.date_input("Дата выезда", now_cet.date())
    with col_t:
        start_time = st.time_input("Время выезда (CET)", now_cet.time())
    start_dt = datetime.combine(start_date, start_time)
    start_dt = cet_zone.localize(start_dt)

st.divider()

# --- БЛОК 2: ПАРАМЕТРЫ РЕЙСА ---
col1, col2 = st.columns(2)
with col1:
    dist = st.number_input("Дистанция (км):", min_value=1, value=1000)
    speed = st.slider("Скорость (км/ч):", 40, 90, 70)
    drive_limit = st.selectbox("Лимит вождения в смену:", [9, 10], index=0)
    st.caption(f"Водитель будет ехать по {drive_limit}ч до отстоя")

with col2:
    mode = st.radio("Режим:", ["Одиночка", "Экипаж"])
    already_driven = st.number_input("Уже проехал сегодня (ч):", min_value=0.0, max_value=float(drive_limit), value=0.0, step=0.5)

ferry = st.checkbox("🚢 Паром (+2 часа)")

# --- МАТЕМАТИКА ---
pure_drive_needed = dist / speed
extra = 2.0 if ferry else 0.0

if "Одиночка" in mode:
    # Сколько осталось до конца ПЕРВОЙ смены
    drive_left_in_first_shift = max(0.0, float(drive_limit) - already_driven)
    
    if pure_drive_needed <= drive_left_in_first_shift:
        # Успевает доехать в этой смене
        total_breaks = 1 if (already_driven < 4.5 and (already_driven + pure_drive_needed) > 4.5) else 0
        total_rests = 0
    else:
        # Нужен отстой
        remaining_drive = pure_drive_needed - drive_left_in_first_shift
        
        # Пауза в первой смене (если еще не было 45-ки)
        breaks_in_first = 1 if (already_driven < 4.5) else 0
        
        # Считаем последующие полные смены
        full_shifts = remaining_drive // drive_limit
        remainder_last = remaining_drive % drive_limit
        
        # Паузы по твоей схеме (2 на смену)
        total_breaks = breaks_in_first + (full_shifts * 2) + (1 if remainder_last > 4.5 else 0)
        total_rests = (full_shifts + 1) * 9.0
        
    total_way = pure_drive_needed + total_breaks + total_rests + extra
else:
    # Экипаж (18ч едут, 9ч стоят)
    drive_left_in_shift = max(0.0, 18.0 - already_driven)
    if pure_drive_needed > drive_left_in_shift:
        remaining = pure_drive_needed - drive_left_in_shift
        rests = (remaining // 18.0) + 1
    else:
        rests = 0
    total_way = pure_drive_needed + (rests * 9.0) + extra

# Итоговое прибытие
arrival = start_dt + timedelta(hours=total_way)

st.divider()
st.success(f"## 🏁 ПРИБЫТИЕ: {arrival.strftime('%A, %H:%M')} (CET)")
st.info(f"📅 Дата: {arrival.strftime('%d.%m.%Y')}")

# Детали
c1, c2, c3 = st.columns(3)
c1.metric("Ехать чисто", f"{pure_drive_needed:.1f}ч")
c2.metric("Паузы", f"{int(total_breaks)}ч")
c3.metric("Отстои", f"{int(total_way//9) if 'Одиночка' in mode else int(total_way//27)}")
