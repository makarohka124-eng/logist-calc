import streamlit as st
from datetime import datetime, timedelta
import pytz

# Настройка страницы
st.set_page_config(page_title="Logist Calc", layout="centered", page_icon="🚛")

# Берем время CET (Центральная Европа)
cet_zone = pytz.timezone('Europe/Berlin')
now_cet = datetime.now(cet_zone)

st.title("🚛 Калькулятор Логиста")

# --- БЛОК 1: ВРЕМЯ СТАРТА ---
st.subheader("📅 Время выезда")
use_current = st.checkbox("Считать от текущего времени (сейчас)", value=True)

if use_current:
    # Если галочка стоит, просто фиксируем текущее время
    start_dt = now_cet
    st.info(f"🚀 Старт: **Сегодня, {start_dt.strftime('%H:%M')}** (по CET)")
else:
    # Если галочку сняли, показываем выбор даты и времени
    col1, col2 = st.columns(2)
    with col1:
        sd = st.date_input("Выбери дату", now_cet.date())
    with col2:
        st_time = st.time_input("Выбери время", now_cet.time())
    
    # Собираем всё в одну дату
    start_dt = datetime.combine(sd, st_time)
    start_dt = cet_zone.localize(start_dt)

st.divider()

# --- БЛОК 2: ПАРАМЕТРЫ ---
col_a, col_b = st.columns(2)
with col_a:
    dist = st.number_input("Дистанция (км):", min_value=1, value=1000)
    speed = st.slider("Скорость (км/ч):", 40, 90, 70)
with col_b:
    mode = st.radio("Режим:", ["Одиночка", "Экипаж"])
    already_driven = st.number_input("Уже проехал сегодня (ч):", min_value=0.0, max_value=9.0, value=0.0, step=0.5)

# --- РАСЧЕТ ---
pure_drive = dist / speed

if "Одиночка" in mode:
    # Сколько осталось до конца первой смены
    left_in_shift = max(0.0, 9.0 - already_driven)
    
    if pure_drive <= left_in_shift:
        total_breaks = 1 if (already_driven < 4.5 and (already_driven + pure_drive) > 4.5) else 0
        total_rests = 0
    else:
        rem_drive = pure_drive - left_in_shift
        full_shifts = rem_drive // 9
        rem_last = rem_drive % 9
        
        # Паузы по 1ч (2 на смену)
        total_breaks = (1 if already_driven < 4.5 else 0) + (full_shifts * 2) + (1 if rem_last > 4.5 else 0)
        total_rests = (full_shifts + 1) * 9.0
    
    total_way = pure_drive + total_breaks + total_rests
else:
    # Экипаж
    left_in_shift = max(0.0, 18.0 - already_driven)
    rests = ((pure_drive - left_in_shift) // 18.0) + 1 if pure_drive > left_in_shift else 0
    total_way = pure_drive + (rests * 9.0)

# Финал
arrival = start_dt + timedelta(hours=total_way)

st.divider()
st.success(f"## 🏁 ПРИБЫТИЕ: {arrival.strftime('%A, %H:%M')} (CET)")
st.info(f"📅 Дата: {arrival.strftime('%d.%m.%Y')}")

st.write(f"**Общее время в пути:** {total_way:.1f} ч.")
