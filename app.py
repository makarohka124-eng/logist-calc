import streamlit as st
from datetime import datetime, timedelta
import pytz
import math

# Настройка страницы
st.set_page_config(page_title="Logist Calc", layout="wide", page_icon="🚛")

# Улучшенные CSS-стили для компактности и четкости
st.markdown("""
<style>
    /* Убираем отступы сверху */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    
    /* Делаем вертикальный разделитель более заметным */
    .stVerticalDivider {
        margin: 0px 30px;
        opacity: 0.5;
    }
    
    /* Стили для подписи */
    .footer {
        position: fixed;
        left: 10px;
        bottom: 10px;
        color: #888;
        font-size: 11px;
        z-index: 100;
    }
</style>
""", unsafe_allow_html=True)

# Время CET
cet_zone = pytz.timezone('Europe/Berlin')
now_cet = datetime.now(cet_zone)

st.title("🚛 Профи-Калькулятор")

# --- ЛИНИЯ 1: ВРЕМЯ ВЫЕЗДА (Уже поправлено в прошлом коде) ---
if 'start_date' not in st.session_state:
    st.session_state.start_date = now_cet.date()
if 'start_time' not in st.session_state:
    st.session_state.start_time = now_cet.time()

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

# --- ЛИНИЯ 2: ПАРАМЕТРЫ РЕЙСА (Основное разделение) ---
# Создаем три колонки. Средняя будет узкой и в ней будет разделитель.
# Коэффициент ширины колонок: Лево (4) | Центр ( узкая 0.2) | Право (3)
main_col1, main_divider, main_col2 = st.columns([4, 0.2, 3])

# ЗОНА 1: ВВОД ДАННЫХ РЕЙСА (ЛЕВАЯ ЧАСТЬ)
with main_col1:
    st.subheader("🏁 Параметры рейса")
    
    # Разделяем левую часть еще на две колонки для компактности
    sub_col1, sub_col2 = st.columns(2)
    with sub_col1:
        dist = st.number_input("КМ:", min_value=1, value=1000, key="dist", help="Дистанция в километрах")
        speed = st.slider("Скорость:", 40, 90, 70, key="speed", help="Средняя скорость движения км/ч")
        
    with sub_col2:
        mode = st.radio("Режим:", ["Одиночка", "Экипаж"], horizontal=True, key="mode", help="Одиночный водитель или парный экипаж")
        
        # Динамический лимит для "Уже проехал"
        max_drive = 9.0 if mode == "Одиночка" else 18.0
        
        if 'already' not in st.session_state:
            st.session_state.already = 0.0
        if st.session_state.already > max_drive:
            st.session_state.already = max_drive
            
        already_driven = st.number_input(f"Уже проехал сегодня (ч):", 
                                         min_value=0.0, 
                                         max_value=max_drive, 
                                         value=st.session_state.already, 
                                         step=0.5, 
                                         key="already_input", 
                                         help="Сколько часов водитель уже отработал сегодня")
        st.session_state.already = already_driven

# ТА САМАЯ РАЗДЕЛИТЕЛЬНАЯ ПОЛОСКА
with main_divider:
    # Идеально вертикально выравниваем разделитель с помощью CSS
    st.markdown("""
        <style>
            .vertical-divider {
                border-left: 2px solid rgba(255,255,255,0.1);
                height: 100%;
                margin: 0px 10px;
            }
        </style>
        <div class="vertical-divider"></div>
        """, unsafe_allow_html=True)

# ЗОНА 2: ДОПОЛНИТЕЛЬНЫЕ ПАРАМЕТРЫ (ПРАВАЯ ЧАСТЬ)
with main_col2:
    st.subheader("➕ Допы & Остановки")
    
    # Разделяем правую часть еще на две колонки
    ext_col1, ext_col2 = st.columns(2)
    with ext_col1:
        ferry_option = st.selectbox("Паром:", ["Нет", "1 час", "2 часа"], key="ferry", help="Время в пути на пароме")
        misc = st.selectbox("Прочее (ч):", [0, 1, 2, 3, 4, 5], key="misc", help="Дополнительное время на пробки, документы и т.д.")
    
    with ext_col2:
        st.write("**Дополнительные часы:**")
        gas = st.checkbox("Заправка (+1ч)", key="gas", help="Плановая заправка")
        trailer = st.checkbox("Перецеп (+1ч)", key="trail", help="Смена прицепа")
        loading = st.checkbox("Загрузка (+2ч)", key="load", help="Время погрузки/выгрузки")

st.divider()

# --- МАТЕМАТИКА (Без изменений) ---
# Суммируем все дополнительные часы
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

# Расчет общего времени в пути для ETA (с учетом пауз одиночки)
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
    # Экипаж (отстои каждые 18ч руля)
    total_way = pure_drive + (rests_count * 9.0) + ferry_time + extra_time

arrival = start_dt + timedelta(hours=total_way)

# --- РАБОЧАЯ СТРОКА ---
# Автоматическое определение 1/2 или 2/2 на основе времени ТЕКУЩЕГО (а не приезда)
check_val = "1/2" if now_cet.hour < 12 else "2/2"
arrival_str = arrival.strftime('%d.%m %H:%M')
dh_val = int(drive_remaining) # Округляем до целого

work_string = f"{check_val} ETA  {arrival_str}CET D/H {dh_val}"

# --- БЛОК РЕЗУЛЬТАТОВ (ETA и СТРОКА ДЛЯ ОТЧЕТА) ---
res_col1, res_col2 = st.columns([1, 1])

with res_col1:
    # Зеленая плашка с полным временем приезда
    st.success(f"🏁 **Приезд: {arrival.strftime('%A, %d.%m.%Y %H:%M')} (CET)**")
    st.caption(f"Итого в пути: {total_way:.1f} ч. | Чистое руление: {pure_drive:.1f} ч. | Доп. время: {extra_time + ferry_time} ч.")

with res_col2:
    # Черное поле с готовой строкой для отчета
    st.subheader("📝 Скопируй строку:")
    st.code(work_string)

# Подпись Yaroslav Makarovskyi в левом нижнем углу
st.markdown('<div class="footer">Создал: Yaroslav Makarovskyi</div>', unsafe_allow_html=True)
