import streamlit as st
from datetime import datetime, timedelta
import pytz
import math

# Настройка страницы
st.set_page_config(page_title="Logist Calc", layout="wide", page_icon="🚛")

# Компактный интерфейс и стиль для подписи
st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    .footer {
        position: fixed;
        left: 10px;
        bottom: 10px;
        color: grey;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Время CET
cet_zone = pytz.timezone('Europe/Berlin')
now_cet = datetime.now(cet_zone)

st.title("🚛 Профи-Калькулятор")

# --- ИНИЦИАЛИЗАЦИЯ ПАМЯТИ ---
if 'start_date' not in st.session_state:
    st.session_state.start_date = now_cet.date()
if 'start_time' not in st.session_state:
    st.session_state.start_time = now_cet.time()

# --- ЛИНИЯ 1: ВРЕМЯ ВЫЕЗДА ---
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    use_current = st.checkbox("Сейчас", value=True, key="use_curr")
with c2:
    if not use_current:
        st.session_state.start_date = st.date_input("Дата", st.session_state.start_date)
    else:
        st.write("📅 " + now_cet.strftime('%d.%m'))
with c3:
    if not use_current:
        st.session_state.start_time = st.time_input("Время (CET)", st.session_state.start_time)
        start_dt = cet_zone.localize(datetime.combine(st.session_state.start_date, st.session_state.start_time))
    else:
        start_dt = now_cet
        st.write("🕒 " + now_cet.strftime('%H:%M') + " CET")

st.divider()

# --- ЛИНИЯ 2: ПАРАМЕТРЫ РЕЙСА ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    dist = st.number_input("КМ:", min_value=1, value=1000, key="dist")
    speed = st.slider("Скорость:", 40, 90, 70, key="speed")

with col2:
    mode = st.radio("Режим:", ["Одиночка", "Экипаж"], horizontal=True, key="mode")
    
    # Динамический лимит для "Уже проехал"
    max_drive = 9.0 if mode == "Одиночка" else 18.0
    
    # Проверка, чтобы значение не вылетало за границы при смене режима
    if 'already' not in st.session_state:
        st.session_state.already = 0.0
    if st.session_state.already > max_drive:
        st.session_state.already = max_drive
        
    already_driven = st.number_input(f"Уже проехал сегодня (макс {int(max_drive)}ч):", 
                                     min_value=0.0, 
                                     max_value=max_drive, 
                                     value=st.session_state.already, 
                                     step=0.5, 
                                     key="already_input")
    st.session_state.already = already_driven

with col3:
    ferry_option = st.selectbox("Паром:", ["Нет", "1 час", "2 часа"], key="ferry")
    misc = st.selectbox("Прочее (ч):", [0, 1, 2, 3, 4, 5], key="misc")

with col4:
    st.write("Допы:")
    gas = st.checkbox("Заправка (+1ч)", key="gas")
    trailer = st.checkbox("Перецеп (+1ч)", key="trail")
    loading = st.checkbox("Загрузка (+2ч)", key="load")

# --- МАТЕМАТИКА ---
extra_time = (1 if gas else 0) + (1 if trailer else 0) + (2 if loading else 0) + misc
ferry_time = 1 if "1 час" in ferry_option else (2 if "2 часа" in ferry_option else 0)

pure_drive = dist / speed
limit = 9.0 if mode == "Одиночка" else 18.0
current_left = max(0.0, limit - already_driven)

# Расчет D/H (Driving Hours) по твоей логике
if pure_drive <= current_left:
    drive_remaining = current_left - pure_drive
    rests_count = 0
else:
    remaining_after_first = pure_drive - current_left
    rests_count = math.ceil(remaining_after_first / limit)
    drive_in_last_shift = remaining_after_first % limit
    if drive_in_last_shift == 0: drive_in_last_shift = limit
    drive_remaining = limit - drive_in_last_shift

# Расчет общего времени в пути для ETA
if mode == "Одиночка":
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

# --- РАБОЧАЯ СТРОКА ---
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

# Подпись
st.markdown('<div class="footer">Создал: Yaroslav Makarovskyi</div>', unsafe_allow_html=True)

st.caption(f"Итого в пути: {total_way:.1f} ч. | Чистое руление: {pure_drive:.1f} ч.")
