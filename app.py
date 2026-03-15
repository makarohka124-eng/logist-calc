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

# --- РАСЧЕТ ---
pure_drive = dist / speed

if "Одиночка" in mode:
    limit = 9.0
    left_in_shift = max(0.0, limit - already_driven)
    if pure_drive <= left_in_shift:
        total_breaks = 1 if (already_driven < 4.5 and (already_driven + pure_drive) > 4.5) else 0
        total_rests = 0
        drive_remaining = left_in_shift - pure_drive
    else:
        rem_drive = pure_drive - left_in_shift
        full_shifts = rem_drive // limit
        rem_last = rem_drive % limit
        total_breaks = (1 if already_driven < 4.5 else 0) + (full_shifts * 2) + (1 if rem_last > 4.5 else 0)
        total_rests = (full_shifts + 1) * 9.0
        drive_remaining = limit - rem_last
else:
    # Экипаж
    limit = 18.0
    left_in_shift = max(0.0, limit - already_driven)
    if pure_drive <= left_in_shift:
        rests = 0
        drive_remaining = left_in_shift - pure_drive
    else:
        rem_drive = pure_drive - left_in_shift
        rests = (rem_drive // limit) + 1
        drive_remaining = limit - (rem_drive % limit)
    total_way = pure_drive + (rests * 9.0)
    total_breaks = 0

total_way = (pure_drive + (total_breaks if "Одиночка" in mode else 0) + 
             (total_rests if "Одиночка" in mode else (rests * 9.0)) + ferry_time)

# Финал
arrival = start_dt + timedelta(hours=total_way)

# Формирование строки для работы
check_val = "1/2" if arrival.hour < 12 else "2/2"
arrival_str = arrival.strftime('%d.%m %H:%M')
dh_val = int(drive_remaining)
work_string = f"{check_val} ETA  {arrival_str}CET D/H {dh_val}"

st.divider()
st.success(f"## 🏁 ПРИБЫТИЕ: {arrival.strftime('%A, %H:%M')} (CET)")

# Вывод строки для копирования
st.subheader("📝 Строка для записи:")
st.code(work_string)

st.info(f"Общее время в пути: {total_way:.1f} ч.")
