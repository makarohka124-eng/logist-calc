import streamlit as st
from datetime import datetime, timedelta
import pytz
import math

# Настройка страницы
st.set_page_config(page_title="Logist Calc Pro", layout="wide", page_icon="🚛")

# Стили
st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    .footer {position: fixed; left: 10px; bottom: 10px; color: grey; font-size: 11px;}
    .stCheckbox {margin-bottom: -10px;}
</style>
""", unsafe_allow_html=True)

# Время CET
cet_zone = pytz.timezone('Europe/Berlin')
now_cet = datetime.now(cet_zone)

st.title("🚛 Профи-Калькулятор + Fix Time")

# --- ИНИЦИАЛИЗАЦИЯ ПАМЯТИ ---
if 'start_date' not in st.session_state:
    st.session_state.start_date = now_cet.date()
if 'start_time' not in st.session_state:
    st.session_state.start_time = now_cet.time()

# --- ЛИНИЯ 1: ВРЕМЯ ВЫЕЗДА ---
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    use_current = st.checkbox("Выезд: Сейчас", value=True, key="use_curr")
with c2:
    if not use_current:
        st.session_state.start_date = st.date_input("Дата выезда", st.session_state.start_date)
    else:
        st.write("📅 " + now_cet.strftime('%d.%m'))
with c3:
    if not use_current:
        st.session_state.start_time = st.time_input("Время выезда (CET)", st.session_state.start_time)
        start_dt = cet_zone.localize(datetime.combine(st.session_state.start_date, st.session_state.start_time))
    else:
        start_dt = now_cet
        st.write("🕒 " + now_cet.strftime('%H:%M') + " CET")

st.divider()

# --- ОСНОВНОЙ БЛОК ---
main_col1, main_divider, main_col2 = st.columns([4, 0.1, 3])

with main_col1:
    st.subheader("🏁 Параметры рейса")
    sc1, sc2 = st.columns(2)
    with sc1:
        dist = st.number_input("КМ:", min_value=1, value=1000, key="dist")
        speed = st.slider("Скорость:", 40, 90, 70, key="speed")
    with sc2:
        mode = st.radio("Режим:", ["Одиночка", "Экипаж"], horizontal=True, key="mode")
        max_drive = 9.0 if mode == "Одиночка" else 18.0
        already_driven = st.number_input(f"Уже проехал сегодня (ч):", 0.0, max_drive, 0.0, 0.5, key="already")

with main_divider:
    st.markdown('<div style="border-left: 1px solid grey; height: 350px; margin-left: 20px;"></div>', unsafe_allow_html=True)

with main_col2:
    st.subheader("⏱️ Срок и Запреты")
    
    # СЕКЦИЯ FIX TIME
    use_fix = st.checkbox("📍 Установить время выгрузки (FIX)", value=False)
    if use_fix:
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            fix_date = st.date_input("Дата FIX", now_cet.date() + timedelta(days=1))
        with fcol2:
            fix_time = st.time_input("Время FIX (CET)", datetime.strptime("08:00", "%H:%M").time())
        fix_dt = cet_zone.localize(datetime.combine(fix_date, fix_time))
    
    st.write("**Транзит (TrafficBan):**")
    ignore_bans = st.checkbox("✅ Еду ПОД ЗАПРЕТ", value=False)
    countries = st.multiselect("Страны:", ["Германия (DE)", "Австрия (AT)", "Франция (FR)", "Италия (IT)", "Швейцария (CH)"])
    
    st.write("**Допы:**")
    ec1, ec2 = st.columns(2)
    with ec1:
        gas = st.checkbox("Заправка (+1ч)")
        trailer = st.checkbox("Перецеп (+1ч)")
        loading = st.checkbox("Загрузка (+2ч)")
    with ec2:
        ferry_option = st.selectbox("Паром:", ["Нет", "1 час", "2 часа"])
        misc = st.selectbox("Белеберда (ч):", [0, 1, 2, 3, 4, 5])

# --- МАТЕМАТИКА ---
extra_time = (1 if gas else 0) + (1 if trailer else 0) + (2 if loading else 0) + misc
ferry_time = 1 if "1 час" in ferry_option else (2 if "2 часа" in ferry_option else 0)
pure_drive = dist / speed
limit = 9.0 if mode == "Одиночка" else 18.0
current_left = max(0.0, limit - already_driven)

# Базовое время (вождение + отстои 9ч + паузы одиночки 45 мин)
if mode == "Одиночка":
    if pure_drive <= current_left:
        total_way = pure_drive + (1 if (already_driven < 4.5 and (already_driven + pure_drive) > 4.5) else 0)
        drive_remaining = current_left - pure_drive
    else:
        rem = pure_drive - current_left
        shifts = math.ceil(rem / 9)
        total_way = pure_drive + (shifts * 9) + (1 if already_driven < 4.5 else 0) + (shifts * 2)
        drive_remaining = 9 - (rem % 9) if rem % 9 != 0 else 9
else:
    shifts = math.ceil((pure_drive - current_left) / 18) if pure_drive > current_left else 0
    total_way = pure_drive + (shifts * 9)
    drive_remaining = current_left - pure_drive if shifts == 0 else 18 - ((pure_drive - current_left) % 18)

total_way += extra_time + ferry_time

# Корректировка по странам
if not ignore_bans and countries:
    check_time = start_dt
    added_hours = 0
    remaining_way = total_way
    while remaining_way > 0:
        is_banned = False
        weekday = check_time.weekday()
        hour = check_time.hour
        for c in countries:
            if "DE" in c and weekday == 6 and 0 <= hour < 22: is_banned = True
            if "AT" in c and ((weekday == 5 and hour >= 15) or (weekday == 6 and hour < 22)): is_banned = True
            if "FR" in c and ((weekday == 5 and hour >= 22) or (weekday == 6 and hour < 22)): is_banned = True
            if "IT" in c and weekday == 6 and 9 <= hour < 22: is_banned = True
            if "CH" in c and (weekday == 6 or (hour >= 22 or hour < 5)): is_banned = True
        if is_banned:
            added_hours += 1
            check_time += timedelta(hours=1)
        else:
            remaining_way -= 1
            check_time += timedelta(hours=1)
    total_way += added_hours

final_arrival = start_dt + timedelta(hours=total_way)

# --- ВЫВОД РЕЗУЛЬТАТОВ ---
st.divider()
res_c1, res_c2 = st.columns(2)

with res_c1:
    # Проверка на опоздание
    if use_fix:
        diff = fix_dt - final_arrival
        diff_hours = diff.total_seconds() / 3600
        if diff_hours >= 0:
            st.success(f"✅ **Приезд: {final_arrival.strftime('%A, %d.%m %H:%M')}**")
            st.info(f"Успеваем! Запас по времени: **{abs(int(diff_hours))} ч. {int((diff_hours % 1) * 60)} мин.**")
        else:
            st.error(f"🚨 **Приезд: {final_arrival.strftime('%A, %d.%m %H:%M')}**")
            st.warning(f"ОПОЗДАНИЕ на **{abs(int(diff_hours))} ч. {int((abs(diff_hours) % 1) * 60)} мин.**")
    else:
        st.success(f"🏁 **Приезд: {final_arrival.strftime('%A, %d.%m %H:%M')}**")

with res_col2:
    check_val = "1/2" if now_cet.hour < 12 else "2/2"
    work_string = f"{check_val} ETA  {final_arrival.strftime('%d.%m %H:%M')}CET D/H {int(drive_remaining)}"
    st.subheader("📝 Строка для отчета:")
    st.code(work_string)

st.markdown(f'<div class="footer">Создал: Yaroslav Makarovskyi</div>', unsafe_allow_html=True)
