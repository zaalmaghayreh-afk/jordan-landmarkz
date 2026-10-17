import pandas as pd
import streamlit as st

st.set_page_config(page_title="معالم الأردن", page_icon="🏛️", layout="wide")

# ---------- البيانات (لاحقاً ننقلها لملف JSON أو قاعدة بيانات) ----------
LANDMARKS = [
    {"name": "البتراء", "city": "معان", "type": "أثري",
     "lat": 30.3285, "lon": 35.4444,
     "desc": "المدينة الوردية المنحوتة في الصخر، من عجائب الدنيا السبع الجديدة."},
    {"name": "وادي رم", "city": "العقبة", "type": "طبيعي",
     "lat": 29.5764, "lon": 35.4195,
     "desc": "صحراء ساحرة بجبال رملية وتجارب تخييم وسفاري."},
    {"name": "جرش", "city": "جرش", "type": "أثري",
     "lat": 32.2747, "lon": 35.8961,
     "desc": "من أفضل المدن الرومانية المحفوظة في العالم."},
    {"name": "قلعة عجلون", "city": "عجلون", "type": "أثري",
     "lat": 32.3256, "lon": 35.7279,
     "desc": "قلعة إسلامية من القرن الثاني عشر تطل على غور الأردن."},
    {"name": "البحر الميت", "city": "البلقاء", "type": "طبيعي",
     "lat": 31.5590, "lon": 35.4732,
     "desc": "أخفض نقطة على سطح الأرض، ومياهه شديدة الملوحة."},
    {"name": "أم قيس", "city": "إربد", "type": "أثري",
     "lat": 32.6537, "lon": 35.6817,
     "desc": "مدينة جدارا القديمة بإطلالة على بحيرة طبريا والجولان."},
    {"name": "جبل نيبو", "city": "مادبا", "type": "ديني",
     "lat": 31.7686, "lon": 35.7255,
     "desc": "المكان الذي يُعتقد أن النبي موسى رأى منه الأرض الموعودة."},
    {"name": "قلعة عمّان (جبل القلعة)", "city": "عمّان", "type": "أثري",
     "lat": 31.9547, "lon": 35.9348,
     "desc": "تضم معبد هرقل والقصر الأموي وإطلالة على وسط البلد."},
]

df = pd.DataFrame(LANDMARKS)

# ---------- الواجهة ----------
st.title("🏛️ معالم الأردن")
st.caption("تعرّف على أجمل الأماكن الأثرية والطبيعية في الأردن")

# الفلاتر في الشريط الجانبي
with st.sidebar:
    st.header("بحث وتصفية")
    query = st.text_input("ابحث بالاسم")
    cities = st.multiselect("المدينة", sorted(df["city"].unique()))
    types = st.multiselect("النوع", sorted(df["type"].unique()))

filtered = df
if query:
    filtered = filtered[filtered["name"].str.contains(query, case=False)]
if cities:
    filtered = filtered[filtered["city"].isin(cities)]
if types:
    filtered = filtered[filtered["type"].isin(types)]

st.write(f"عدد النتائج: **{len(filtered)}**")

col_list, col_map = st.columns([1, 1])

with col_list:
    for _, row in filtered.iterrows():
        with st.expander(f"{row['name']}  ·  {row['city']}"):
            st.write(row["desc"])
            st.write(f"**النوع:** {row['type']}")

with col_map:
    if filtered.empty:
        st.info("ما في نتائج مطابقة.")
    else:
        st.map(filtered[["lat", "lon"]], zoom=6)
