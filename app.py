import streamlit as st
from datetime import datetime, timedelta
import pytz

# Настройка страницы
st.set_page_config(page_title="Logist Pro Calc", layout="centered", page_icon="🚛")

# Работа с временем CET
cet_zone = pytz.timezone('Europe/Berlin')
now_cet = datetime.now(cet_zone)

st.title("🚛 Калькулятор Логиста")
st.write(f"### 🕒 Сейчас в Европе (CET): **{now_cet.strftime('%H:%M')}**")

st.divider()

# Ввод данных
dist = st.number_input("Дистанция (км):", min_value=1, value=1000, step=10)
speed = st.slider("Средняя скорость (км/ч):", 40, 90, 70)

# ВЫБОР РЕЖИМА (то, что мы возвращаем)
mode = st.radio("Кто за рулем?", ["Одиночка (паузы по 1ч)", "Экипаж (Двойка)"])

ferry = st.checkbox("🚢 Паром (+2 часа)")

# --- МАТЕМАТИКА ---
pure_drive = dist / speed
extra = 2.0 if ferry else 0.0

if "Одиночка" in mode:
    # Твоя жесткая схема: 2 паузы по 1ч на смену 9ч
    full_shifts = pure_drive // 9
    remainder = pure_drive % 9
    
    total_breaks = full_shifts * 2 
    if remainder > 4.5:
        total_breaks += 1
        
    total_rests = full_shifts * 9.0 # Всегда 9ч отдых
    total_way = pure_drive + total_breaks + total_rests + extra
    details = f"Пауз по 1ч: {int(total_breaks)}, Отстоев по 9ч: {int(full_shifts)}"
else:
    # Экипаж: 18ч рулят, 9ч стоят
    rests_count = (pure_drive - 0.01) // 18.0
    total_way = pure_drive + (rests_count * 9.0) + extra
    details = f"Суточных отстоев экипажа (9ч): {int(rests_count)}"

# Прибытие
arrival = now_cet + timedelta(hours=total_way)

st.divider()
st.success(f"## 🏁 ПРИБЫТИЕ: {arrival.strftime('%A, %H:%M')} (CET)")
st.info(f"📅 Дата: {arrival.strftime('%d.%m.%Y')}")

# Детали
st.write(f"**Всего в пути:** {total_way:.1f} ч.")
st.caption(f"ℹ️ {details}")
