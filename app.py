import json
import math
from collections import Counter
from pathlib import Path
from urllib.parse import quote_plus, urlencode
from urllib.request import Request, urlopen

import pandas as pd
import pydeck as pdk
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="معالم الأردن", page_icon="🏛️", layout="wide")


# ---------- التصميم ----------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
:root { --navy:#1B2340; --sand:#E7CBA0; --cream:#FAF1DE; --clay:#D98E5F; --clay-dark:#A9532A; }
h1, h2, h3, h4, h5, p, li, label, .stMarkdown, .stCaption, [data-testid="stMetricValue"],
[data-testid="stExpander"] summary p, .stButton button p, [data-testid="stLinkButton"] p {
  font-family: 'Tajawal', 'Cairo', sans-serif;
}
.stMarkdown, .stCaption, label, [data-testid="stExpander"] summary { direction: rtl; text-align: right; }
.block-container { padding-top: 1.6rem; max-width: 1100px; }
[data-testid="stToolbar"], #MainMenu, footer { display: none !important; }
[data-testid="stSidebar"] { background: var(--cream); }
h2 { color: var(--navy); font-weight: 800; border-right: 6px solid var(--clay);
     padding-right: 12px; margin-top: .4rem; }
[data-testid="stExpander"] { border: 1px solid var(--sand); border-radius: 14px; background: #fff;
     box-shadow: 0 2px 8px rgba(27,35,64,.06); margin-bottom: 8px; }
[data-testid="stLinkButton"] a, [data-testid^="stBaseLinkButton"], .stButton > button {
  border-radius: 999px; border: 1.5px solid var(--clay); color: var(--navy); font-weight: 700; }
[data-testid="stLinkButton"] a:hover, .stButton > button:hover { background: var(--cream); border-color: var(--clay-dark); }
[data-testid="stMetric"] { background: var(--cream); border-radius: 14px; padding: 10px 14px; }
.hero { display: flex; align-items: center; gap: 22px; direction: rtl; margin-bottom: 18px;
        background: linear-gradient(135deg, #1B2340 0%, #2B3862 100%);
        border-radius: 20px; padding: 22px 28px; }
.hero svg { flex: none; width: 110px; height: 110px; }
.hero h1 { color: var(--cream) !important; font-size: 2.5rem; font-weight: 800; margin: 0; padding: 0; }
.hero p { color: var(--cream) !important; margin: 6px 0 12px; opacity: .92; }
.hero .chips span { display: inline-block; background: rgba(250,241,222,.14); color: var(--cream);
        border-radius: 999px; padding: 4px 14px; margin: 0 0 6px 8px; font-size: .85rem; }
@media (max-width: 640px) {
  .hero { flex-direction: column; text-align: center; padding: 18px; }
  .hero svg { width: 84px; height: 84px; }
  .hero h1 { font-size: 1.9rem; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

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
    {"name": "المدرج الروماني", "city": "عمّان", "type": "أثري",
     "lat": 31.9515, "lon": 35.9395,
     "desc": "مدرج روماني من القرن الثاني الميلادي في قلب وسط البلد."},
    {"name": "قلعة الكرك", "city": "الكرك", "type": "أثري",
     "lat": 31.1803, "lon": 35.7016,
     "desc": "قلعة صليبية ضخمة بأنفاق وقاعات مقنطرة تطل على المدينة."},
    {"name": "قلعة الشوبك", "city": "معان", "type": "أثري",
     "lat": 30.5322, "lon": 35.5604,
     "desc": "قلعة صليبية على قمة جبل وسط بساتين المشمش."},
    {"name": "محمية ضانا", "city": "الطفيلة", "type": "طبيعي",
     "lat": 30.6830, "lon": 35.6110,
     "desc": "أكبر محمية طبيعية في الأردن، مناسبة للمشي والتخييم."},
    {"name": "وادي الموجب", "city": "مادبا", "type": "طبيعي",
     "lat": 31.4437, "lon": 35.5753,
     "desc": "وادي ومحمية بمسارات مائية ومغامرات الأنهار والشلالات."},
    {"name": "موقع المغطس", "city": "البلقاء", "type": "ديني",
     "lat": 31.8372, "lon": 35.5503,
     "desc": "الموقع الذي يُعتقد أن السيد المسيح تعمّد فيه على نهر الأردن."},
    {"name": "مادبا (خريطة الفسيفساء)", "city": "مادبا", "type": "ديني",
     "lat": 31.7165, "lon": 35.7939,
     "desc": "مدينة الفسيفساء، وفيها كنيسة القديس جورج وخريطة الأرض المقدسة."},
    {"name": "البتراء الصغيرة", "city": "معان", "type": "أثري",
     "lat": 30.3836, "lon": 35.4617,
     "desc": "موقع نبطي هادئ قرب البتراء بنقوش ومنازل منحوتة."},
    {"name": "قصر عمرة", "city": "الزرقاء", "type": "أثري",
     "lat": 31.8023, "lon": 36.5859,
     "desc": "قصر أموي في الصحراء بلوحات جدارية مدرجة على قائمة اليونسكو."},
    {"name": "طبقة فحل (بيلا)", "city": "إربد", "type": "أثري",
     "lat": 32.4486, "lon": 35.6192,
     "desc": "موقع أثري قديم في الأغوار الشمالية يعود لآلاف السنين."},
    {"name": "قصر الحرانة", "city": "عمّان", "type": "أثري", "lat": 31.7508, "lon": 36.4506,
     "desc": "قصر أموي صحراوي بطابقين وغرف مقنطرة، من أشهر القصور الصحراوية."},
    {"name": "قصر الأزرق", "city": "الزرقاء", "type": "أثري", "lat": 31.8806, "lon": 36.8290,
     "desc": "قلعة بازلتية سكنها لورانس العرب خلال الثورة العربية الكبرى."},
    {"name": "قصر المشتى", "city": "عمّان", "type": "أثري", "lat": 31.7270, "lon": 36.0490,
     "desc": "قصر أموي مزخرف بالحجر، قرب مطار الملكة علياء."},
    {"name": "قصر الحلابات وحمام الصرح", "city": "الزرقاء", "type": "أثري", "lat": 31.9960, "lon": 36.3480,
     "desc": "قصر وحمّام أمويان في الصحراء الشرقية."},
    {"name": "أم الجمال", "city": "المفرق", "type": "أثري", "lat": 32.3306, "lon": 36.3611,
     "desc": "مدينة بازلتية سوداء قديمة بمبانيها وكنائسها وأبراجها."},
    {"name": "قصر العبد (عراق الأمير)", "city": "عمّان", "type": "أثري", "lat": 31.9066, "lon": 35.7447,
     "desc": "قصر هلنستي ضخم من القرن الثاني قبل الميلاد."},
    {"name": "حسبان", "city": "عمّان", "type": "أثري", "lat": 31.8023, "lon": 35.8067,
     "desc": "تل أثري قديم ذُكر في التوراة باسم حشبون."},
    {"name": "مكاور", "city": "مادبا", "type": "أثري", "lat": 31.5726, "lon": 35.6359,
     "desc": "قلعة هيرودس على تلة عالية تطل على البحر الميت."},
    {"name": "ذيبان", "city": "مادبا", "type": "أثري", "lat": 31.5014, "lon": 35.7792,
     "desc": "ديبون القديمة، وفيها وُجدت مسلة ميشع الشهيرة."},
    {"name": "أم الرصاص", "city": "مادبا", "type": "أثري", "lat": 31.5047, "lon": 35.9199,
     "desc": "موقع على قائمة اليونسكو بفسيفساء بيزنطية وبرج غريب."},
    {"name": "دير عين عبطا (كهف لوط)", "city": "الكرك", "type": "ديني", "lat": 31.2770, "lon": 35.5330,
     "desc": "دير بيزنطي قديم قرب غور الصافي مرتبط بقصة النبي لوط."},
    {"name": "قلعة الطفيلة", "city": "الطفيلة", "type": "أثري", "lat": 30.8372, "lon": 35.6039,
     "desc": "قلعة صليبية صغيرة في وسط المدينة القديمة."},
    {"name": "خربة التنور", "city": "الطفيلة", "type": "أثري", "lat": 30.9422, "lon": 35.6103,
     "desc": "معبد نبطي على قمة جبل بنقوش حجرية جميلة."},
    {"name": "فينان", "city": "الطفيلة", "type": "أثري", "lat": 30.6167, "lon": 35.4833,
     "desc": "من أقدم مواقع تعدين النحاس في العالم."},
    {"name": "بصيرا", "city": "الطفيلة", "type": "أثري", "lat": 30.7220, "lon": 35.6050,
     "desc": "عاصمة الأدوميين القديمة على قمة جبل مطل على الوادي."},
    {"name": "البيضا", "city": "معان", "type": "أثري", "lat": 30.3886, "lon": 35.4442,
     "desc": "قرية من العصر الحجري الحديث من أقدم القرى المعروفة في العالم."},
    {"name": "الدير (البتراء)", "city": "معان", "type": "أثري", "lat": 30.3380, "lon": 35.4330,
     "desc": "من أكبر المعالم المنحوتة في البتراء، يُصعد إليها بنحو 800 درجة."},
    {"name": "الخزنة (البتراء)", "city": "معان", "type": "أثري", "lat": 30.3216, "lon": 35.4513,
     "desc": "الواجهة الأشهر في البتراء، تظهر في نهاية السيق."},
    {"name": "المقابر الملكية (البتراء)", "city": "معان", "type": "أثري", "lat": 30.3236, "lon": 35.4488,
     "desc": "واجهات قبور نبطية ضخمة منحوتة في الجبل."},
    {"name": "المكان العالي للقرابين", "city": "معان", "type": "أثري", "lat": 30.3281, "lon": 35.4411,
     "desc": "مذبح نبطي على قمة جبل مطل على وادي البتراء."},
    {"name": "قصر البنت (البتراء)", "city": "معان", "type": "أثري", "lat": 30.3283, "lon": 35.4463,
     "desc": "من المباني القليلة القائمة بنفسها في البتراء، معبد نبطي."},
    {"name": "السيق", "city": "معان", "type": "طبيعي", "lat": 30.3248, "lon": 35.4635,
     "desc": "الممر الصخري الضيق الذي يؤدي إلى الخزنة في البتراء."},
    {"name": "جبل هارون", "city": "معان", "type": "ديني", "lat": 30.3180, "lon": 35.3950,
     "desc": "جبل قرب البتراء فيه مقام يُنسب للنبي هارون."},
    {"name": "أذرح", "city": "معان", "type": "أثري", "lat": 30.4880, "lon": 35.5570,
     "desc": "حصن روماني قديم وموقع تاريخي مهم في الجنوب."},
    {"name": "الحميمة", "city": "العقبة", "type": "أثري", "lat": 29.7833, "lon": 35.3500,
     "desc": "موقع نبطي وروماني وعباسي، منه خرجت الدعوة العباسية."},
    {"name": "قلعة العقبة", "city": "العقبة", "type": "أثري", "lat": 29.5217, "lon": 35.0000,
     "desc": "قلعة مملوكية على شاطئ العقبة بجانب البحر."},
    {"name": "أيلة (العقبة الإسلامية)", "city": "العقبة", "type": "أثري", "lat": 29.5252, "lon": 35.0074,
     "desc": "من أقدم المدن الإسلامية، تعود للقرن السابع الميلادي."},
    {"name": "تل الخليفي", "city": "العقبة", "type": "أثري", "lat": 29.5500, "lon": 35.0167,
     "desc": "موقع أثري قديم قرب ميناء العقبة من العصر الحديدي."},
    {"name": "معبد وادي رم النبطي", "city": "العقبة", "type": "أثري", "lat": 29.5800, "lon": 35.4200,
     "desc": "بقايا معبد نبطي في قلب وادي رم."},
    {"name": "تل دير علا", "city": "البلقاء", "type": "أثري", "lat": 32.2175, "lon": 35.6200,
     "desc": "تل في الأغوار وُجدت فيه نصوص قديمة مهمة."},
    {"name": "عين غزال", "city": "عمّان", "type": "أثري", "lat": 31.9780, "lon": 35.9700,
     "desc": "موقع من العصر الحجري الحديث اشتهر بتماثيل الجص."},
    {"name": "نمفاوم عمّان", "city": "عمّان", "type": "أثري", "lat": 31.9526, "lon": 35.9382,
     "desc": "نافورة عامة رومانية قديمة في وسط البلد."},
    {"name": "السلط القديمة", "city": "البلقاء", "type": "تراثي", "lat": 32.0392, "lon": 35.7272,
     "desc": "مدينة عثمانية بمبانٍ صفراء مدرجة على قائمة اليونسكو."},
    {"name": "أبيلا", "city": "إربد", "type": "أثري", "lat": 32.6644, "lon": 35.7600,
     "desc": "مدينة من المدن العشر (الديكابوليس) بكنائس ومدافن قديمة."},
    {"name": "بيت راس", "city": "إربد", "type": "أثري", "lat": 32.5560, "lon": 35.8420,
     "desc": "كابيتولياس، إحدى مدن الديكابوليس الرومانية."},
    {"name": "قوس هادريان (جرش)", "city": "جرش", "type": "أثري", "lat": 32.2722, "lon": 35.8991,
     "desc": "قوس نصر روماني على مدخل المدينة القديمة."},
    {"name": "معبد أرتميس (جرش)", "city": "جرش", "type": "أثري", "lat": 32.2767, "lon": 35.8922,
     "desc": "معبد روماني بأعمدة ضخمة من أجمل مباني جرش."},
    {"name": "معبد هرقل (جبل القلعة)", "city": "عمّان", "type": "أثري", "lat": 31.9546, "lon": 35.9343,
     "desc": "معبد روماني بأعمدة عملاقة فوق قلعة عمّان."},
    {"name": "القصر الأموي (جبل القلعة)", "city": "عمّان", "type": "أثري", "lat": 31.9548, "lon": 35.9355,
     "desc": "مجمع قصور أموي بقبة بارزة داخل القلعة."},
    {"name": "خربة المخيط", "city": "مادبا", "type": "أثري", "lat": 31.7569, "lon": 35.7361,
     "desc": "بقايا مدينة نبو القديمة بكنائس وفسيفساء بيزنطية."},
    {"name": "وادي موسى (البلدة)", "city": "معان", "type": "تراثي", "lat": 30.3222, "lon": 35.4800,
     "desc": "البلدة المجاورة للبتراء، ومنها تبدأ زيارة المدينة الوردية."},
    {"name": "عين موسى", "city": "معان", "type": "ديني", "lat": 30.3207, "lon": 35.4780,
     "desc": "نبع يُنسب في الموروث إلى النبي موسى، ومنه سُمّيت المدينة."},
    {"name": "محمية غابات عجلون", "city": "عجلون", "type": "طبيعي", "lat": 32.3550, "lon": 35.7900,
     "desc": "محمية بغابات السنديان فيها مسارات مشي ومخيمات."},
    {"name": "محمية الأزرق للأراضي الرطبة", "city": "الزرقاء", "type": "طبيعي", "lat": 31.8350, "lon": 36.8270,
     "desc": "واحة رطبة في الصحراء الشرقية، ملتقى لهجرة الطيور."},
    {"name": "حمامات ماعين", "city": "مادبا", "type": "طبيعي", "lat": 31.5930, "lon": 35.6120,
     "desc": "ينابيع ماء حار وشلالات في وادي ماعين قرب البحر الميت."},
    {"name": "وادي شعيب", "city": "البلقاء", "type": "طبيعي", "lat": 32.0200, "lon": 35.7100,
     "desc": "وادٍ أخضر قرب السلط ويُنسب إليه مقام النبي شعيب."},
    {"name": "متنزه ديبين الوطني", "city": "جرش", "type": "طبيعي", "lat": 32.2800, "lon": 35.7900,
     "desc": "غابة صنوبر طبيعية قرب جرش مناسبة للتنزه والمشي."},
    {"name": "الحديقة البحرية في العقبة", "city": "العقبة", "type": "طبيعي", "lat": 29.4350, "lon": 34.9700,
     "desc": "شعاب مرجانية ومواقع غوص على ساحل خليج العقبة."},
    {"name": "مطل البحر الميت (بانوراما)", "city": "مادبا", "type": "طبيعي", "lat": 31.7370, "lon": 35.5720,
     "desc": "موقع إطلالة واسعة على البحر الميت ووادي الأردن."},
    {"name": "المتحف الأردني", "city": "عمّان", "type": "ثقافي", "lat": 31.9569, "lon": 35.9394,
     "desc": "متحف يعرض تاريخ الأردن من العصور القديمة حتى اليوم."},
    {"name": "متحف الفولكلور الأردني", "city": "عمّان", "type": "ثقافي", "lat": 31.9510, "lon": 35.9388,
     "desc": "يعرض الأزياء والتراث الشعبي الأردني بجانب المدرج الروماني."},
    {"name": "شارع الرينبو", "city": "عمّان", "type": "سياحي", "lat": 31.9515, "lon": 35.9235,
     "desc": "شارع شهير في جبل عمّان بمقاهيه ومطاعمه وإطلالته."},
    {"name": "الجامع الحسيني", "city": "عمّان", "type": "ديني", "lat": 31.9529, "lon": 35.9378,
     "desc": "مسجد تاريخي في وسط البلد بعمّان."},
    {"name": "مسجد الملك عبدالله الأول", "city": "عمّان", "type": "ديني", "lat": 31.9680, "lon": 35.9072,
     "desc": "مسجد بقبة زرقاء كبيرة، من أبرز معالم عمّان."},
    {"name": "متحف السيارات الملكي", "city": "عمّان", "type": "ثقافي", "lat": 32.0030, "lon": 35.8830,
     "desc": "يعرض سيارات ومقتنيات ملكية من تاريخ الأردن."},
    {"name": "محطة سكة حديد الحجاز (عمّان)", "city": "عمّان", "type": "تراثي", "lat": 31.9100, "lon": 35.9440,
     "desc": "محطة تاريخية على خط الحجاز بقطاراتها القديمة."},
    {"name": "محطة سكة حديد الحجاز (معان)", "city": "معان", "type": "تراثي", "lat": 30.1951, "lon": 35.7360,
     "desc": "محطة تاريخية على خط سكة حديد الحجاز."},
    {"name": "كنيسة الرسل (مادبا)", "city": "مادبا", "type": "ديني", "lat": 31.7153, "lon": 35.7930,
     "desc": "كنيسة بيزنطية في مادبا بفسيفساء مميزة."},
    {"name": "المزار الجنوبي (مقامات الصحابة)", "city": "الكرك", "type": "ديني", "lat": 31.0700, "lon": 35.7000,
     "desc": "مقامات صحابة استشهدوا في معركة مؤتة."},
    {"name": "سارية الثورة العربية الكبرى", "city": "العقبة", "type": "سياحي", "lat": 29.5200, "lon": 35.0060,
     "desc": "سارية علم ضخمة على شاطئ العقبة تخلّد الثورة العربية الكبرى."},
    {"name": "متحف آثار العقبة", "city": "العقبة", "type": "ثقافي", "lat": 29.5217, "lon": 35.0040,
     "desc": "متحف قرب شاطئ العقبة يعرض آثار المنطقة."},
    {"name": "قرية ضانا التراثية", "city": "الطفيلة", "type": "تراثي", "lat": 30.6806, "lon": 35.6100,
     "desc": "قرية حجرية قديمة على حافة وادي ضانا."},
    {"name": "تل صافوط", "city": "البلقاء", "type": "أثري", "lat": 32.0750, "lon": 35.8350,
     "desc": "موقع أثري قديم قرب عين الباشا شمال غرب عمّان."},
    {"name": "جلول", "city": "عمّان", "type": "أثري", "lat": 31.7167, "lon": 35.8500,
     "desc": "تل أثري في هضبة مادبا."},
    {"name": "العراعير", "city": "مادبا", "type": "أثري", "lat": 31.4717, "lon": 35.8219,
     "desc": "موقع قديم يُعتقد أنه عروعر المذكورة في التوراة."},
    {"name": "البصة (كنيسة الكهف)", "city": "عمّان", "type": "أثري", "lat": 31.9330, "lon": 35.7830,
     "desc": "كنيسة كهف رومانية بيزنطية قرب عراق الأمير."},
    {"name": "الفحيص", "city": "البلقاء", "type": "تراثي", "lat": 32.0000, "lon": 35.7700,
     "desc": "بلدة قرب عمّان بيوتها حجرية وتشتهر بمهرجانها."},
]

df = pd.DataFrame(LANDMARKS)


def street_view_url(lat, lon):
    """رابط يفتح جولة Street View (360°) عند الإحداثيات."""
    return f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}"


def maps_search_url(name, city):
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(
        f"{name} {city} الأردن"
    )


@st.cache_data(ttl=86400, show_spinner=False)
def wiki_photo(name):
    """يجيب صورة المعلم من ويكيبيديا العربية، ويرجع None لو ما لقى."""
    try:
        params = urlencode({
            "action": "query", "format": "json", "generator": "search",
            "gsrsearch": f"{name} الأردن", "gsrlimit": 1,
            "prop": "pageimages|info", "piprop": "thumbnail",
            "pithumbsize": 800, "inprop": "url",
        })
        req = Request(
            "https://ar.wikipedia.org/w/api.php?" + params,
            headers={"User-Agent": "JordanLandmarksApp/1.0"},
        )
        with urlopen(req, timeout=6) as resp:
            data = json.load(resp)
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None
        page = next(iter(pages.values()))
        thumb = page.get("thumbnail", {}).get("source")
        if not thumb:
            return None
        return {"image": thumb, "page": page.get("fullurl"), "title": page.get("title")}
    except Exception:
        return None

# ---------- الواجهة ----------
HERO = (
    '<div class="hero">'
    '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="قوس حجري وشمس">'
    '<path d="M 20 100 V 50 A 40 40 0 0 1 100 50 V 100 Z" fill="#D98E5F"/>'
    '<path d="M 36 100 V 55 A 24 24 0 0 1 84 55 V 100 Z" fill="#0F1428"/>'
    '<circle cx="60" cy="62" r="11" fill="#F6E3B4"/>'
    '<path d="M 36 90 L 60 80 L 84 90 V 100 H 36 Z" fill="#8F4F31"/>'
    '<rect x="10" y="100" width="100" height="5" rx="2.5" fill="#F0C98F"/>'
    '</svg>'
    '<div><h1>معالم الأردن</h1>'
    '<p>دليلك لأجمل الأماكن الأثرية والطبيعية والتراثية في المملكة</p>'
    '<div class="chips">'
    f'<span>🏛️ {len(LANDMARKS)} معلم</span>'
    f'<span>📍 {df["city"].nunique()} مدينة</span>'
    '<span>🧭 مخطط رحلات</span><span>🏎️ لعبة قيادة</span>'
    '</div></div></div>'
)
st.markdown(HERO, unsafe_allow_html=True)

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
            st.link_button("جولة 360° (Street View) 🌐",
                           street_view_url(row["lat"], row["lon"]))
            st.link_button("افتح في خرائط Google 🗺️",
                           maps_search_url(row["name"], row["city"]))

with col_map:
    if filtered.empty:
        st.info("ما في نتائج مطابقة.")
    else:
        st.map(filtered[["lat", "lon"]], zoom=6)


# ---------- مخطط الرحلة ----------
def distance_km(a, b):
    """المسافة التقريبية بخط مستقيم بين نقطتين (كم)."""
    r = 6371
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dphi = p2 - p1
    dlon = math.radians(b["lon"] - a["lon"])
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def order_route(start, others):
    """نبدأ من نقطة البداية وكل مرة نروح لأقرب مكان باقي."""
    route = [start]
    remaining = others[:]
    while remaining:
        nxt = min(remaining, key=lambda s: distance_km(route[-1], s))
        remaining.remove(nxt)
        route.append(nxt)
    return route


st.divider()
st.header("🧭 خطّط رحلتك")
st.caption("اختر الأماكن اللي تبي تزورها، وبنرتبها لك بمسار مناسب")

names = st.multiselect(
    "اختر من 2 إلى 8 أماكن", df["name"].tolist(), max_selections=8, key="trip"
)

if len(names) < 2:
    st.info("اختر مكانين على الأقل عشان نرسم لك المسار.")
else:
    start_name = st.selectbox("نقطة البداية", names)
    chosen = [s for s in LANDMARKS if s["name"] in names]
    start = next(s for s in chosen if s["name"] == start_name)
    others = [s for s in chosen if s["name"] != start_name]
    route = order_route(start, others)

    legs = [distance_km(route[i], route[i + 1]) for i in range(len(route) - 1)]
    total = sum(legs)
    road_km = total * 1.3  # تقدير تقريبي للمسافة بالسيارة
    hours = road_km / 60

    st.subheader("ترتيب الزيارة")
    for i, stop in enumerate(route):
        line = f"**{i + 1}. {stop['name']}** ({stop['city']})"
        if i > 0:
            line += f"  ·  حوالي {legs[i - 1]:.0f} كم من المحطة السابقة"
        st.markdown(line)

    c1, c2 = st.columns(2)
    c1.metric("المسافة بخط مستقيم", f"{total:.0f} كم")
    c2.metric("تقدير بالسيارة", f"{road_km:.0f} كم · {hours:.1f} ساعة")
    st.caption("الأرقام تقريبية. المسافة الفعلية والوقت يعتمدون على الطرق والزحمة.")

    # الخريطة
    stops_df = pd.DataFrame(route)
    path_df = pd.DataFrame({"path": [[[s["lon"], s["lat"]] for s in route]]})
    span = max(stops_df["lat"].max() - stops_df["lat"].min(),
               stops_df["lon"].max() - stops_df["lon"].min())
    zoom = 9 if span < 0.3 else 8 if span < 0.8 else 7 if span < 1.5 else 6
    st.pydeck_chart(
        pdk.Deck(
            layers=[
                pdk.Layer("PathLayer", path_df, get_path="path",
                          get_width=60, width_min_pixels=3,
                          get_color=[217, 142, 95]),
                pdk.Layer("ScatterplotLayer", stops_df,
                          get_position="[lon, lat]", get_radius=2500,
                          radius_min_pixels=7, get_fill_color=[27, 35, 64]),
            ],
            initial_view_state=pdk.ViewState(
                latitude=float(stops_df["lat"].mean()),
                longitude=float(stops_df["lon"].mean()),
                zoom=zoom,
            ),
        )
    )

    # فتح المسار في خرائط Google
    gmaps_url = "https://www.google.com/maps/dir/" + "/".join(
        f"{s['lat']},{s['lon']}" for s in route
    )
    st.link_button("افتح المسار في خرائط Google 🗺️", gmaps_url)


# ---------- جولة بالصور ----------
st.divider()
st.header("📸 جولة بالصور")
st.caption("اختر مدينة وتجوّل بين معالمها معلماً بعد معلم")

tour_city = st.selectbox("اختر المدينة", sorted(df["city"].unique()), key="tour_city")
tour_stops = [s for s in LANDMARKS if s["city"] == tour_city]

if st.session_state.get("tour_city_prev") != tour_city:
    st.session_state["tour_i"] = 0
    st.session_state["tour_city_prev"] = tour_city
tour_i = max(0, min(st.session_state.get("tour_i", 0), len(tour_stops) - 1))

c_prev, c_count, c_next = st.columns([1, 1, 1])
if c_prev.button("◀ السابق", disabled=tour_i == 0, key="tour_prev"):
    st.session_state["tour_i"] = tour_i - 1
    st.rerun()
if c_next.button("التالي ▶", disabled=tour_i >= len(tour_stops) - 1, key="tour_next"):
    st.session_state["tour_i"] = tour_i + 1
    st.rerun()
c_count.markdown(f"**{tour_i + 1} / {len(tour_stops)}**")

stop = tour_stops[tour_i]
st.subheader(stop["name"])
photo = wiki_photo(stop["name"])
if photo:
    st.image(photo["image"])
    st.caption(f"الصورة من ويكيبيديا: [{photo['title']}]({photo['page']})")
else:
    st.info("ما لقينا صورة لهذا المعلم، جرّب جولة Street View.")
st.write(stop["desc"])
st.link_button("جولة 360° (Street View) 🌐", street_view_url(stop["lat"], stop["lon"]))
st.link_button("افتح في خرائط Google 🗺️", maps_search_url(stop["name"], stop["city"]))


# ---------- لعبة القيادة ----------
st.divider()
st.header("🏎️ لعبة القيادة بين المعالم الأثرية")
st.caption("سوق السيارة وزر المعالم الأثرية لتجمعها وتقرأ معلوماتها. "
           "بالأسهم أو WASD على الكمبيوتر، أو بأزرار الشاشة على الجوال.")

arch_all = [s for s in LANDMARKS if s["type"] == "أثري"]
counts = Counter(s["city"] for s in arch_all)
regions = ["الأردن كله"] + sorted(c for c, n in counts.items() if n >= 2)
region = st.selectbox("اختر المنطقة", regions, key="game_region")
arch = arch_all if region == "الأردن كله" else [s for s in arch_all if s["city"] == region]

mode = st.radio("نسخة اللعبة", ["ثلاثية الأبعاد 🧊", "ثنائية الأبعاد 🗺️"],
                horizontal=True, key="game_mode")
game_file = "game3d.html" if mode.startswith("ثلاثية") else "game.html"
game_html = (Path(__file__).parent / game_file).read_text(encoding="utf-8")
game_html = game_html.replace("__LANDMARKS__", json.dumps(arch, ensure_ascii=False))
components.html(game_html, height=580)
