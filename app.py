import streamlit as st
from datetime import datetime, timedelta
import pytz

# Настройка страницы
st.set_page_config(page_title="Logist Express 9h", layout="centered", page_icon="🚛")

# Работа с временем CET (Центральная Европа)
cet_zone = pytz.timezone('Europe/Berlin')
now_cet = datetime.now(cet_zone)

st.title("🚀 Экспресс-Калькулятор")
st.write(f"### 🕒 Сейчас в Европе (CET): **{now_cet.strftime('%H:%M')}**")
st.caption(f"Сегодня: {now_cet.strftime('%A, %d.%m.%Y')}")

st.divider()

# Блок ввода данных
dist = st.number_input("Дистанция до точки (км):", min_value=1, value=1000, step=10)
speed = st.slider("Средняя скорость (км/ч):", 40, 90, 70)
ferry = st.checkbox("🚢 Паром (+2 часа к пути)")

# --- ЛОГИКА РАСЧЕТА (ОДИНОЧКА) ---
pure_drive_hours = dist / speed

# Считаем полные смены по 9 часов вождения
full_shifts = pure_drive_hours // 9
remainder_drive = pure_drive_hours % 9

# Твоя логика пауз: 2 паузы по 1 часу на каждую смену (9ч вождения)
total_breaks = full_shifts * 2 
if remainder_drive > 4.5:
    total_breaks += 1  # Доп. пауза 1ч, если остаток руления больше 4.5ч

# Отстой всегда 9 часов после каждой полной смены
total_rests = full_shifts * 9.0

# Дополнительное время (паром и т.д.)
extra_time = 2.0 if ferry else 0.0

# Итоговое время в пути
total_way_time = pure_drive_hours + total_breaks + total_rests + extra_time

# Расчет даты и времени прибытия
arrival_date = now_cet + timedelta(hours=total_way_time)

# --- ВЫВОД РЕЗУЛЬТАТОВ ---
st.divider()
st.success(f"## 🏁 ПРИБЫТИЕ: {arrival_date.strftime('%A, %H:%M')}")
st.info(f"📅 **Дата:** {arrival_date.strftime('%d %B %Y')}")

col1, col2, col3 = st.columns(3)
col1.metric("Всего в пути", f"{total_way_time:.1f} ч")
col2.metric("Паузы (по 1ч)", int(total_breaks))
col3.metric("Отстои (9ч)", int(full_shifts))

st.warning("⚠️ График: 9ч руля -> две паузы по 1ч -> 9ч отстой.")