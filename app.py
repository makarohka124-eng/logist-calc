import streamlit as st
from datetime import datetime, timedelta
import pytz
import math

# Настройка страницы (широкий экран и компактные отступы)
st.set_page_config(page_title="Logist Calc", layout="wide", page_icon="🚛")

# Убираем лишние отступы сверху через CSS
st.markdown("""<style>.block-container {padding-top: 1rem; padding-bottom: 0rem;}</style>""", unsafe_allow_html=True)

# Время CET
cet_zone = pytz.timezone('Europe/Berlin')
now_cet = datetime.now(cet_zone)

st.title("🚛 Профи-Калькулятор")

# --- ЛИНИЯ 1: ВРЕМЯ ВЫЕЗДА ---
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    use_current = st.checkbox("Сейчас", value=True)
with c2:
    if not use_current:
        sd = st.date_input("Дата", now_cet.date())
    else:
        st.write("📅 " + now_cet.strftime('%d.%m'))
with c3:
    if not use_current:
        st_time = st.time_input("Время (CET)", now_cet.time())
        start_dt = cet_zone.localize(datetime.combine(sd, st_time))
    else:
        start_dt = now_cet
        st.write("🕒 " + now_cet.strftime('%H:%M') + " CET")

st.divider()

# --- ЛИНИЯ 2: ПАРАМЕТРЫ И ДОПЫ ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    dist = st.number_input("КМ:", min_value=1, value=1000)
    speed = st.slider("Скорость:", 40, 90, 70)

with col2:
    mode = st.radio("Режим:", ["Одиночка", "Экипаж"], horizontal=True)
    already_driven = st.number_input("Уже проехал (ч):", 0.0, 18.0, 0.0, 0.5)

with col3:
    ferry_option = st.selectbox("Паром:", ["Нет", "1 час", "2 часа"])
    misc = st.selectbox("Прочее (ч):", [0, 1, 2, 3, 4, 5])

with col4:
    st.write("Допы:")
    gas = st.checkbox("Заправка (+1ч)")
    trailer = st.checkbox("Перецеп (+1ч)")

# --- МАТЕМАТИКА ---
extra_time = (1 if gas else 0) + (1 if trailer else 0) + misc
ferry_time = 1 if "1 час" in ferry_option else (2 if "2 часа" in ferry_option else 0)
pure_drive = dist / speed
limit = 9.0 if "Одиночка" in mode else 18.0
current_left = max(0.0, limit - already_driven)

if pure_drive <= current_left:
    drive_remaining = current_left - pure_drive
    rests_count = 0
else:
    remaining_after_first = pure_drive - current_left
    rests_count = math.ceil(remaining_after_first / limit)
    drive_in_last_shift = remaining_after_first % limit
    if drive_in_last_shift == 0: drive_in_last_shift = limit
    drive_remaining = limit - drive_in_last_shift

if "Одиночка" in mode:
    if pure_drive <= current_left:
        total_breaks = 1 if (already_driven < 4.5 and (already_driven + pure_drive) > 4.5) else 0
        total_rests = 0
    else:
        full_shifts_after = (pure_drive - current_left) // 9
        rem_last = (pure_drive - current_left) % 9
        total_breaks = (1 if already_driven < 4.5 else 0) + (full_shifts_after * 2) + (1 if rem_last > 4.5 else 0)
        total_rests = (full_shifts_after + 1) * 9.0
    total_way = pure_drive + total_breaks + total_rests + ferry_time + extra_time
else:
    total_way = pure_drive + (rests_count * 9.0) + ferry_time + extra_time

arrival = start_dt + timedelta(hours=total_way)

# --- ФИНАЛЬНАЯ СТРОКА ---
check_val = "1/2" if now_cet.hour < 12 else "2/2"
arrival_str = arrival.strftime('%d.%m %H:%M')
dh_val = int(drive_remaining)
work_string = f"{check_val} ETA  {arrival_str}CET D/H {dh_val}"

st.divider()

res_col1, res_col2 = st.columns([1, 1])
with res_col1:
    st.success(f"🏁 **Приезд: {arrival.strftime('%A, %H:%M')}**")
with res_col2:
    st.code(work_string)

st.caption(f"Итого в пути: {total_way:.1f} ч. | Чистое руление: {pure_drive:.1f} ч.")
