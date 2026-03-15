import streamlit as st
from datetime import datetime, timedelta
import pytz

# Настройка страницы
st.set_page_config(page_title="Logist Pro Calc v2", layout="centered", page_icon="🚛")

# Настройка времени CET
cet_zone = pytz.timezone('Europe/Berlin')
now_cet = datetime.now(cet_zone)

st.title("🚛 Профи-Калькулятор Логиста")

# --- БЛОК 1: ВРЕМЯ ВЫЕЗДА ---
st.subheader("📅 Когда выезд?")
col_d, col_t = st.columns(2)
with col_d:
    start_date = st.date_input("Дата выезда", now_cet.date())
with col_t:
    start_time = st.time_input("Время выезда (CET)", now_cet.time())

# Формируем полную дату старта
start_dt = datetime.combine(start_date, start_time)
start_dt = cet_zone.localize(start_dt)

st.divider()

# --- БЛОК 2: ПАРАМЕТРЫ РЕЙСА ---
col1, col2 = st.columns(2)
with col1:
    dist = st.number_input("Осталось ехать (км):", min_value=1, value=1000)
    speed = st.slider("Средняя скорость (км/ч):", 40, 90, 70)
with col2:
    mode = st.radio("Режим:", ["Одиночка (паузы 1ч)", "Экипаж"])
    already_driven = st.number_input("Уже проехал сегодня (часов):", min_value=0.0, max_value=10.0, value=0.0, step=0.5)

ferry = st.checkbox("🚢 Паром (+2 часа)")

# --- МАТЕМАТИКА ---
pure_drive_needed = dist / speed
extra = 2.0 if ferry else 0.0

if "Одиночка" in mode:
    # Сколько осталось до конца первой смены (лимит 9ч)
    drive_left_in_first_shift = max(0.0, 9.0 - already_driven)
    
    if pure_drive_needed <= drive_left_in_first_shift:
        # Успевает доехать за текущую смену
        total_breaks = 1 if pure_drive_needed > 4.5 else 0
        total_rests = 0
    else:
        # Не успевает, нужен отстой
        first_shift_drive = drive_left_in_first_shift
        remaining_drive = pure_drive_needed - first_shift_drive
        
        # Считаем паузы в первой смене
        breaks_in_first = 1 if (already_driven < 4.5 and (already_driven + first_shift_drive) > 4.5) else 0
        
        # Считаем последующие полные смены
        full_shifts = remaining_drive // 9
        remainder_last_shift = remaining_drive % 9
        
        total_breaks = breaks_in_first + (full_shifts * 2) + (1 if remainder_last_shift > 4.5 else 0)
        total_rests = (full_shifts + 1) * 9.0 # +1 это отстой после текущей недобитой смены
        
    total_way = pure_drive_needed + total_breaks + total_rests + extra
else:
    # Экипаж (упрощенно: 18ч едут, 9ч стоят)
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

# Детали для контроля
c1, c2 = st.columns(2)
c1.metric("Чистое руление", f"{pure_drive_needed:.1f} ч")
c2.metric("Общее время в пути", f"{total_way:.1f} ч")

if "Одиночка" in mode:
    st.caption(f"Учтено: {int(total_breaks)} пауз по 1ч и {int(total_way // 9)} ночевок по 9ч.")
