import streamlit as st
from datetime import datetime, timedelta
import pytz
import math

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

# --- МАТЕМАТИКА ПО ТВОИМ ПРИМЕРАМ ---
pure_drive = dist / speed
limit = 9.0 if "Одиночка" in mode else 18.0
current_left = max(0.0, limit - already_driven)

if pure_drive <= current_left:
    # Приезд в текущей смене
    drive_remaining = current_left - pure_drive
    rests_count = 0
else:
    # Нужен один или несколько отстоев
    remaining_after_first = pure_drive - current_left
    rests_count = math.ceil(remaining_after_first / limit)
    drive_in_last_shift = remaining_after_first % limit
    if drive_in_last_shift == 0: drive_in_last_shift = limit # если ровно под смену
    drive_remaining = limit - drive_in_last_shift

# Считаем общее время в пути для ETA (с учетом пауз 1ч для одиночки)
if "Одиночка" in mode:
    if pure_drive <= current_left:
        total_breaks = 1 if (already_driven < 4.5 and (already_driven + pure_drive) > 4.5) else 0
        total_rests = 0
    else:
        full_shifts_after = (pure_drive - current_left) // 9
        rem_last = (pure_drive - current_left) % 9
        total_breaks = (1 if already_driven < 4.5 else 0) + (full_shifts_after * 2) + (1 if rem_last > 4.5 else 0)
        total_rests = (full_shifts_after + 1) * 9.0
    total_way = pure_drive + total_breaks + total_rests + ferry_time
else:
    # Экипаж
    total_way = pure_drive + (rests_count * 9.0) + ferry_time

# Финал прибыли
arrival = start_dt + timedelta(hours=total_way)

# --- ЛОГИКА РАБОЧЕЙ СТРОКИ ---
check_val = "1/2" if now_cet.hour < 12 else "2/2"
arrival_str = arrival.strftime('%d.%m %H:%M')
dh_val = int(drive_remaining) # Округление вниз до целого

work_string = f"{check_val} ETA  {arrival_str}CET D/H {dh_val}"

st.divider()
st.success(f"## 🏁 ПРИБЫТИЕ: {arrival.strftime('%A, %H:%M')} (CET)")

st.subheader("📝 Строка для отчета:")
st.code(work_string) 

st.info(f"Чистое руление: {pure_drive:.2f} ч. | Отработано: {already_driven} ч.")
