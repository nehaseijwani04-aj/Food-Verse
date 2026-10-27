"""Food Verse AI - Multimodal Food Intelligence Agent (Skill Wallet Capstone 3)
Run: streamlit run app.py
"""
import base64, io, json, re, tempfile
from collections import OrderedDict

import plotly.graph_objects as go
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Food Verse AI", page_icon="🍽️", layout="wide")

# ───────────────────────── Styling ─────────────────────────
st.markdown("""<style>
.hero{background:linear-gradient(120deg,#ff6b35,#f7c548 55%,#2ec4b6);padding:1.4rem 1.8rem;border-radius:18px;color:#fff;margin-bottom:1rem}
.hero h1{margin:0;font-size:2rem}.hero p{margin:.2rem 0 0;opacity:.95}
.badge{display:inline-block;padding:.3rem .8rem;border-radius:999px;font-weight:600;color:#fff;margin:.15rem .25rem .15rem 0}
.card{border:1px solid rgba(128,128,128,.25);border-radius:14px;padding:1rem;margin-bottom:.6rem}
.stTabs [data-baseweb="tab"]{font-weight:600}
</style>
<div class="hero"><h1>🍽️ Food Verse AI</h1><p>Multimodal Food Intelligence Agent · Recognition · Freshness · Hygiene · Recipes · Meal Planning</p></div>
""", unsafe_allow_html=True)

COLORS = {"green": "#2ec4b6", "yellow": "#f4a300", "red": "#e63946", "blue": "#3a86ff", "purple": "#8338ec"}


def badge(text, color="green"):
    st.markdown(f'<span class="badge" style="background:{COLORS.get(color, color)}">{text}</span>', unsafe_allow_html=True)


# ───────────────────────── LLM layer ─────────────────────────
def pil_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode()


def parse_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)


def call_llm(prompt: str, image: Image.Image | None = None) -> dict:
    """Return parsed JSON from Gemini/Groq. Raises on failure (callers fall back to demo)."""
    provider, key = st.session_state.get("provider"), st.session_state.get("api_key")
    sys_msg = "You are FoodVerse AI, an expert food scientist. Respond with ONLY valid minified JSON, no prose."
    if provider == "Gemini":
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel(st.session_state.get("model_name") or "gemini-2.0-flash",
                                      system_instruction=sys_msg,
                                      generation_config={"response_mime_type": "application/json"})
        parts = [prompt] + ([image] if image else [])
        return parse_json(model.generate_content(parts).text)
    if provider == "Groq":
        from groq import Groq
        client = Groq(api_key=key)
        content = [{"type": "text", "text": prompt}]
        if image:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{pil_to_b64(image)}"}})
        model = st.session_state.get("model_name") or "meta-llama/llama-4-scout-17b-16e-instruct"
        r = client.chat.completions.create(model=model, temperature=0.3,
                                           messages=[{"role": "system", "content": sys_msg},
                                                     {"role": "user", "content": content}])
        return parse_json(r.choices[0].message.content)
    raise RuntimeError("No provider configured")


def run_ai(prompt, demo_fn, image=None):
    """Try live AI, otherwise (or on error) use demo data. Returns (data, is_demo)."""
    if st.session_state.get("api_key") and st.session_state.get("provider") in ("Gemini", "Groq"):
        try:
            return call_llm(prompt, image), False
        except Exception as e:  # noqa: BLE001
            st.warning(f"Live AI call failed ({type(e).__name__}: {str(e)[:160]}). Showing demo output instead.")
    return demo_fn(), True


def load_image(file):
    try:
        img = Image.open(file)
        img.load()
        img.thumbnail((1280, 1280))
        return img
    except Exception as e:  # noqa: BLE001
        st.error(f"Could not read image: {e}")
        return None


# ───────────────────────── Demo fallbacks ─────────────────────────
def demo_meal():
    return {"dish_name": "Chicken Biryani with Raita", "cuisine": "Indian (Hyderabadi)",
            "ingredients": ["basmati rice", "chicken", "yogurt", "onion", "ghee", "saffron", "mint", "spices"],
            "portion_size": "Large plate (~350 g)", "calories": 640, "protein_g": 32, "carbs_g": 78,
            "fats_g": 21, "fiber_g": 4, "allergens": ["Dairy (yogurt, ghee)"], "health_score": 62,
            "health_notes": "Good protein; high refined carbs and saturated fat. Add a vegetable side and reduce ghee."}


def demo_fresh():
    return {"item": "Tomato", "category": "vegetable",
            "observations": {"surface_texture": "Slightly soft with minor wrinkling near stem", "discoloration": "Small dull patches",
                             "wrinkling": "Mild", "mold": "None detected"},
            "freshness_stage": "Moderately Fresh", "freshness_pct": 58, "safety_advice": "Consume within 24h",
            "storage_tips": ["Use soft tomatoes in sauces or soups today", "Store ripe tomatoes in a cool spot, stem-side down",
                             "Avoid sealed plastic bags; trapped moisture speeds decay", "Refrigerate only fully ripe fruit"]}


def demo_hygiene():
    return {"checks": {"Chef hat / hairnet": "Compliant", "Gloves": "Violation", "Sanitization state": "Compliant",
                       "Cross-contamination": "Violation", "Clean work surfaces": "Compliant", "Apron / uniform": "Compliant"},
            "violations": [{"item": "Gloves", "severity": "Medium", "detail": "Staff handling food bare-handed near prep counter."},
                           {"item": "Cross-contamination", "severity": "High", "detail": "Raw poultry stored beside fresh vegetables without separation."}],
            "recommendations": ["Use colour-coded boards for raw meat vs produce", "Store raw poultry on lowest shelf, sealed",
                                "Enforce glove change between tasks"]}


def demo_recipes(pantry, diet):
    p = ", ".join(pantry[:4]) or "mixed vegetables"
    mk = lambda n, t, d, s, sub: {"name": n, "time_min": t, "difficulty": d, "calories": 420, "ingredients": pantry[:8],
                                  "steps": s, "substitutions": sub}
    return {"recipes": [
        mk(f"One-Pan {pantry[0].title() if pantry else 'Veggie'} Skillet", 25, "Easy",
           ["Chop all ingredients evenly.", "Heat oil in a pan over medium-high heat.", f"Sauté {p} for 8-10 min.",
            "Season with salt, pepper, and herbs; serve hot."], {"oil": "ghee or butter", "herbs": "any dried herb mix"}),
        mk("Hearty Pantry Soup", 35, "Easy", ["Sauté onions/garlic.", "Add ingredients and 3 cups stock/water.",
                                              "Simmer 20 min.", "Blend half for creaminess."], {"stock": "water + bouillon"}),
        mk("Protein Power Bowl", 20, "Medium", ["Cook a grain base.", "Roast or pan-sear main ingredients.",
                                               "Assemble with a quick lemon-yogurt dressing."], {"yogurt": "tahini or coconut yogurt"})]}


# ───────────────────────── Nutrition math ─────────────────────────
def bmr_tdee(age, gender, weight, height, activity):
    s = {"Male": 5, "Female": -161}.get(gender, -78)
    bmr = 10 * weight + 6.25 * height - 5 * age + s
    mult = {"Sedentary": 1.2, "Lightly active": 1.375, "Moderately active": 1.55, "Very active": 1.725, "Athlete": 1.9}[activity]
    return bmr, bmr * mult


def macro_split(kcal, diet, goal, weight):
    if "Keto" in diet:
        p, f, c = 0.25, 0.70, 0.05
    elif goal == "Muscle Gain":
        p, f, c = 0.30, 0.25, 0.45
    elif goal == "Fat Loss" or "Diabetic-Friendly" in diet:
        p, f, c = 0.30, 0.30, 0.40
    else:
        p, f, c = 0.20, 0.30, 0.50
    return {"Protein": round(kcal * p / 4), "Carbs": round(kcal * c / 4), "Fats": round(kcal * f / 9)}


DEMO_MEALS = {
    "Vegan": [("Overnight oats with chia & berries", ["rolled oats", "chia seeds", "berries", "soy milk"]),
              ("Chickpea quinoa bowl", ["chickpeas", "quinoa", "cucumber", "tahini"]),
              ("Tofu veggie stir-fry", ["tofu", "broccoli", "bell pepper", "brown rice", "soy sauce"]),
              ("Lentil soup", ["red lentils", "carrot", "onion", "cumin"]),
              ("Banana peanut butter smoothie", ["banana", "peanut butter", "soy milk"])],
    "Keto": [("Spinach & cheese omelette", ["eggs", "spinach", "cheddar", "butter"]),
             ("Chicken Caesar (no croutons)", ["chicken breast", "romaine", "parmesan", "olive oil"]),
             ("Salmon with asparagus", ["salmon", "asparagus", "butter", "lemon"]),
             ("Avocado egg boats", ["avocado", "eggs"]), ("Almonds & cheese", ["almonds", "cheddar"])],
    "Diabetic-Friendly": [("Veggie egg scramble + whole-grain toast", ["eggs", "whole-grain bread", "tomato", "spinach"]),
                          ("Grilled chicken & lentil salad", ["chicken breast", "lentils", "mixed greens", "olive oil"]),
                          ("Baked fish, quinoa & greens", ["white fish", "quinoa", "green beans", "lemon"]),
                          ("Greek yogurt with walnuts", ["greek yogurt", "walnuts"]), ("Chana & veggie curry", ["chickpeas", "tomato", "onion", "spices"])],
    "Balanced": [("Poha with peanuts & veggies", ["flattened rice", "peanuts", "onion", "peas"]),
                 ("Paneer wrap with salad", ["paneer", "whole-wheat roti", "cucumber", "yogurt"]),
                 ("Chicken curry with rice & dal", ["chicken", "rice", "toor dal", "tomato", "onion"]),
                 ("Fruit & nuts", ["apple", "almonds"]), ("Veg khichdi", ["rice", "moong dal", "carrot", "ghee"])],
}


def demo_plan(kcal, diets):
    key = next((d for d in ("Vegan", "Keto", "Diabetic-Friendly") if d in diets), "Balanced")
    pool, days = DEMO_MEALS[key], []
    split = [("Breakfast", .25), ("Lunch", .30), ("Dinner", .30), ("Snack", .15)]
    for d in range(7):
        meals = []
        for i, (slot, frac) in enumerate(split):
            name, ing = pool[(i + d) % len(pool)] if slot != "Snack" else pool[-1]
            meals.append({"slot": slot, "meal": name, "kcal": round(kcal * frac), "ingredients": ing})
        days.append({"day": f"Day {d + 1}", "meals": meals})
    return {"days": days}


# ───────────────────────── Sidebar ─────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")
    st.session_state["provider"] = st.selectbox("AI Provider", ["Demo (no key)", "Gemini", "Groq"])
    key = ""
    if st.session_state["provider"] != "Demo (no key)":
        key = st.text_input("API Key", type="password", help="Held only in this session; never stored.")
        st.session_state["model_name"] = st.text_input(
            "Model (optional)", placeholder="gemini-2.0-flash" if st.session_state["provider"] == "Gemini"
            else "meta-llama/llama-4-scout-17b-16e-instruct")
    st.session_state["api_key"] = key
    live = bool(key) and st.session_state["provider"] != "Demo (no key)"
    badge("🟢 Live AI mode" if live else "🟡 Demo mode", "green" if live else "yellow")
    st.caption("Demo mode returns sample results so you can explore every feature without a key.")
    st.divider()
    st.caption("Food Verse AI · Skill Wallet Capstone 3\n\n⚠️ Estimates are informational, not medical advice.")

tabs = st.tabs(["🍛 Nutrition Audit", "🥬 Freshness Check", "🧼 Kitchen Hygiene", "👩‍🍳 Recipe Assistant", "📅 Meal Planner"])

# ───────────────────────── Tab 1 ─────────────────────────
with tabs[0]:
    st.subheader("Food Recognition & Nutrition Audit")
    up = st.file_uploader("Upload a meal photo", type=["jpg", "jpeg", "png", "webp"], key="meal")
    if up and (img := load_image(up)):
        c1, c2 = st.columns([1, 1.3])
        c1.image(img, use_container_width=True)
        if c2.button("Analyze meal", type="primary", key="b1"):
            prompt = ("Identify the dish in the image. Return JSON with keys: dish_name, cuisine, ingredients (list), portion_size, "
                      "calories, protein_g, carbs_g, fats_g, fiber_g (numbers for the visible portion), allergens (list), "
                      "health_score (1-100 integer), health_notes (string).")
            with st.spinner("Analyzing..."):
                try:
                    r, demo = run_ai(prompt, demo_meal, img)
                    st.session_state["meal_res"] = r
                except Exception as e:  # noqa: BLE001
                    st.error(f"Analysis failed: {e}")
    r = st.session_state.get("meal_res")
    if r and up:
        try:
            st.markdown(f"### {r['dish_name']}  ·  {r['cuisine']}")
            st.write(f"**Portion:** {r['portion_size']}  |  **Ingredients:** {', '.join(r['ingredients'])}")
            m = st.columns(5)
            for col, (lbl, k) in zip(m, [("Calories", "calories"), ("Protein g", "protein_g"), ("Carbs g", "carbs_g"),
                                         ("Fats g", "fats_g"), ("Fiber g", "fiber_g")]):
                col.metric(lbl, r.get(k, 0))
            score = int(r.get("health_score", 0))
            col = "green" if score >= 70 else "yellow" if score >= 45 else "red"
            badge(f"Health Score {score}/100", col)
            badge("Balanced" if score >= 70 else "Moderate" if score >= 45 else "Indulgent", col)
            for a in r.get("allergens") or []:
                badge(f"⚠️ {a}", "red")
            if not r.get("allergens"):
                badge("✅ No major allergens detected", "green")
            g1, g2 = st.columns(2)
            pie = go.Figure(go.Pie(labels=["Protein", "Carbs", "Fats"],
                                   values=[r["protein_g"] * 4, r["carbs_g"] * 4, r["fats_g"] * 9], hole=.5,
                                   marker_colors=[COLORS["blue"], COLORS["yellow"], COLORS["red"]]))
            pie.update_layout(title="Calories from macros (kcal)", height=320, margin=dict(t=50, b=10))
            g1.plotly_chart(pie, use_container_width=True)
            gauge = go.Figure(go.Indicator(mode="gauge+number", value=score, title={"text": "Health Score"},
                                           gauge={"axis": {"range": [0, 100]}, "bar": {"color": COLORS[col]}}))
            gauge.update_layout(height=320, margin=dict(t=50, b=10))
            g2.plotly_chart(gauge, use_container_width=True)
            st.info(r.get("health_notes", ""))
        except (KeyError, TypeError, ValueError) as e:
            st.error(f"Unexpected AI response format ({e}). Please retry.")

# ───────────────────────── Tab 2 ─────────────────────────
with tabs[1]:
    st.subheader("Food Freshness & Spoilage Diagnostic")
    up = st.file_uploader("Upload a perishable item (fruit, vegetable, meat, dairy)", type=["jpg", "jpeg", "png", "webp"], key="fresh")
    if up and (img := load_image(up)):
        c1, c2 = st.columns([1, 1.3])
        c1.image(img, use_container_width=True)
        if c2.button("Diagnose freshness", type="primary", key="b2"):
            prompt = ("Assess freshness of the perishable food in the image. Return JSON: item, category, observations "
                      "{surface_texture, discoloration, wrinkling, mold}, freshness_stage (exactly one of 'Fresh','Moderately Fresh','Spoiled'), "
                      "freshness_pct (0-100), safety_advice (exactly one of 'Safe to consume','Consume within 24h','Discard immediately'), "
                      "storage_tips (list of 3-5 strings).")
            with st.spinner("Inspecting..."):
                try:
                    st.session_state["fresh_res"], _ = run_ai(prompt, demo_fresh, img)
                except Exception as e:  # noqa: BLE001
                    st.error(f"Diagnosis failed: {e}")
    r = st.session_state.get("fresh_res")
    if r and up:
        try:
            stage = r["freshness_stage"]
            col = {"Fresh": "green", "Moderately Fresh": "yellow"}.get(stage, "red")
            st.markdown(f"### {r['item']} ({r.get('category', '')})")
            badge(stage, col)
            badge(r["safety_advice"], col)
            st.progress(max(0, min(100, int(r.get("freshness_pct", 0)))) / 100, text=f"Freshness {r.get('freshness_pct')}%")
            o = r.get("observations", {})
            cols = st.columns(4)
            for c, (k, v) in zip(cols, o.items()):
                c.markdown(f'<div class="card"><b>{k.replace("_", " ").title()}</b><br>{v}</div>', unsafe_allow_html=True)
            if stage == "Spoiled":
                st.error("🚫 Discard immediately. Do not taste to test.")
            elif stage == "Moderately Fresh":
                st.warning("⏱️ Use within 24 hours.")
            else:
                st.success("✅ Safe to consume.")
            st.markdown("**Preservation tips**")
            for t in r.get("storage_tips", []):
                st.write(f"• {t}")
        except (KeyError, TypeError) as e:
            st.error(f"Unexpected AI response format ({e}). Please retry.")

# ───────────────────────── Tab 3 ─────────────────────────
with tabs[2]:
    st.subheader("Kitchen Hygiene & Food Safety Compliance")
    up = st.file_uploader("Upload kitchen image or short video", type=["jpg", "jpeg", "png", "webp", "mp4", "mov", "avi"], key="hyg")
    frame = None
    if up:
        if up.type.startswith("video"):
            try:
                import cv2
                with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
                    tmp.write(up.read()); tmp.flush()
                    cap = cv2.VideoCapture(tmp.name)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, int(cap.get(cv2.CAP_PROP_FRAME_COUNT) // 2))
                    ok, fr = cap.read(); cap.release()
                if ok:
                    frame = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
                    st.caption("Analyzing a representative mid-video frame.")
                else:
                    st.error("Could not extract a frame from the video.")
            except ImportError:
                st.error("Video support needs opencv-python-headless. Upload an image instead.")
            except Exception as e:  # noqa: BLE001
                st.error(f"Video error: {e}")
        else:
            frame = load_image(up)
    if frame:
        c1, c2 = st.columns([1, 1.3])
        c1.image(frame, use_container_width=True)
        if c2.button("Run compliance audit", type="primary", key="b3"):
            prompt = ("Audit this commercial kitchen scene. Return JSON: checks (object mapping 'Chef hat / hairnet','Gloves','Sanitization state',"
                      "'Cross-contamination','Clean work surfaces','Apron / uniform' to 'Compliant'|'Violation'|'Not visible'), "
                      "violations (list of {item,severity:'Low'|'Medium'|'High',detail}), recommendations (list). Flag raw poultry near vegetables.")
            with st.spinner("Auditing..."):
                try:
                    st.session_state["hyg_res"], _ = run_ai(prompt, demo_hygiene, frame)
                except Exception as e:  # noqa: BLE001
                    st.error(f"Audit failed: {e}")
    r = st.session_state.get("hyg_res")
    if r and frame:
        try:
            judged = {k: v for k, v in r["checks"].items() if v in ("Compliant", "Violation")}
            score = round(100 * sum(v == "Compliant" for v in judged.values()) / max(1, len(judged)))
            col = "green" if score >= 85 else "yellow" if score >= 60 else "red"
            g = go.Figure(go.Indicator(mode="gauge+number", value=score, number={"suffix": "%"},
                                       title={"text": "Hygiene Compliance"},
                                       gauge={"axis": {"range": [0, 100]}, "bar": {"color": COLORS[col]}}))
            g.update_layout(height=280, margin=dict(t=50, b=10))
            a, b = st.columns([1, 1.2])
            a.plotly_chart(g, use_container_width=True)
            with b:
                for k, v in r["checks"].items():
                    st.write({"Compliant": "✅", "Violation": "❌"}.get(v, "➖") + f" **{k}** — {v}")
            st.markdown("#### Violation log")
            if r.get("violations"):
                st.dataframe(r["violations"], use_container_width=True, hide_index=True)
            else:
                st.success("No violations detected.")
            st.markdown("#### Corrective actions")
            for t in r.get("recommendations", []):
                st.write(f"• {t}")
        except (KeyError, TypeError) as e:
            st.error(f"Unexpected AI response format ({e}). Please retry.")

# ───────────────────────── Tab 4 ─────────────────────────
with tabs[3]:
    st.subheader("Smart Kitchen Recipe Assistant")
    pantry_txt = st.text_area("Your pantry (comma or line separated)", placeholder="rice, eggs, spinach, tomato, paneer, onion")
    c1, c2, c3 = st.columns(3)
    r_diet = c1.selectbox("Diet", ["None", "Vegetarian", "Vegan", "Keto", "Diabetic-Friendly"])
    r_time = c2.slider("Max cook time (min)", 10, 90, 40, 5)
    r_n = c3.slider("Recipes", 1, 3, 3)
    if st.button("Generate recipes", type="primary", key="b4"):
        pantry = [p.strip() for p in re.split(r"[,\n]", pantry_txt) if p.strip()]
        if not pantry:
            st.warning("Add at least one ingredient.")
        else:
            prompt = (f"Pantry: {pantry}. Diet: {r_diet}. Max time: {r_time} min. Create {r_n} creative, nutritious recipes. Return JSON "
                      "{recipes:[{name,time_min,difficulty:'Easy'|'Medium'|'Hard',calories,ingredients,steps,substitutions:{ingredient:substitute}}]}")
            with st.spinner("Cooking up ideas..."):
                try:
                    st.session_state["rec_res"], _ = run_ai(prompt, lambda: demo_recipes(pantry, r_diet), None)
                except Exception as e:  # noqa: BLE001
                    st.error(f"Recipe generation failed: {e}")
    for rec in (st.session_state.get("rec_res") or {}).get("recipes", []):
        try:
            with st.expander(f"🍲 {rec['name']} — ⏱️ {rec['time_min']} min · {rec['difficulty']} · ~{rec.get('calories', '?')} kcal", expanded=True):
                st.write("**Ingredients:** " + ", ".join(rec["ingredients"]))
                for i, s in enumerate(rec["steps"], 1):
                    st.write(f"{i}. {s}")
                if rec.get("substitutions"):
                    st.write("**Substitutions:** " + "; ".join(f"{k} → {v}" for k, v in rec["substitutions"].items()))
        except (KeyError, TypeError, AttributeError):
            st.error("Could not render one recipe (unexpected format).")

# ───────────────────────── Tab 5 ─────────────────────────
with tabs[4]:
    st.subheader("Personalized Meal Planner")
    with st.form("profile"):
        a, b, c = st.columns(3)
        age = a.number_input("Age", 14, 90, 28)
        gender = b.selectbox("Gender", ["Male", "Female", "Other"])
        activity = c.selectbox("Activity level", ["Sedentary", "Lightly active", "Moderately active", "Very active", "Athlete"], 1)
        w = a.number_input("Weight (kg)", 30.0, 250.0, 70.0, 0.5)
        h = b.number_input("Height (cm)", 120.0, 230.0, 170.0, 0.5)
        goal = c.selectbox("Fitness goal", ["Fat Loss", "Muscle Gain", "Maintain"])
        diets = st.multiselect("Dietary constraints", ["Vegan", "Keto", "Diabetic-Friendly", "Vegetarian", "Gluten-Free"])
        allergies = st.text_input("Allergies / dislikes (optional)")
        go_btn = st.form_submit_button("Build my plan", type="primary")
    if go_btn:
        bmr, tdee = bmr_tdee(age, gender, w, h, activity)
        target = round(tdee + {"Fat Loss": -500, "Muscle Gain": 300, "Maintain": 0}[goal])
        target = max(target, 1200 if gender == "Female" else 1500)
        macros = macro_split(target, diets, goal, w)
        prompt = (f"Create a 7-day meal plan at ~{target} kcal/day. Diet: {diets}. Goal: {goal}. Avoid: {allergies or 'none'}. Macros g/day: {macros}. "
                  "Return JSON {days:[{day,meals:[{slot:'Breakfast'|'Lunch'|'Dinner'|'Snack',meal,kcal,ingredients:[names]}]}]}")
        with st.spinner("Planning your week..."):
            try:
                plan, _ = run_ai(prompt, lambda: demo_plan(target, diets), None)
                st.session_state["plan"] = dict(plan=plan, bmr=bmr, tdee=tdee, target=target, macros=macros)
            except Exception as e:  # noqa: BLE001
                st.error(f"Plan generation failed: {e}")
    P = st.session_state.get("plan")
    if P:
        try:
            m = st.columns(4)
            m[0].metric("BMR", f"{P['bmr']:.0f} kcal"); m[1].metric("TDEE", f"{P['tdee']:.0f} kcal")
            m[2].metric("Daily target", f"{P['target']} kcal"); m[3].metric("BMI", f"{w / (h / 100) ** 2:.1f}")
            bar = go.Figure(go.Bar(x=list(P["macros"]), y=list(P["macros"].values()),
                                   marker_color=[COLORS["blue"], COLORS["yellow"], COLORS["red"]]))
            bar.update_layout(title="Daily macro targets (g)", height=280, margin=dict(t=50, b=10))
            st.plotly_chart(bar, use_container_width=True)
            days = P["plan"]["days"]
            dtabs = st.tabs([d["day"] for d in days])
            groc = OrderedDict()
            for t, d in zip(dtabs, days):
                with t:
                    for ml in d["meals"]:
                        st.markdown(f'<div class="card"><b>{ml["slot"]}</b> · {ml["meal"]} <i>(~{ml["kcal"]} kcal)</i><br>'
                                    f'<small>{", ".join(ml["ingredients"])}</small></div>', unsafe_allow_html=True)
                        for ing in ml["ingredients"]:
                            groc[ing.lower()] = groc.get(ing.lower(), 0) + 1
            st.markdown("### 🛒 Grocery shopping list")
            cols = st.columns(3)
            for i, (ing, n) in enumerate(sorted(groc.items())):
                cols[i % 3].checkbox(f"{ing.title()} (used in {n} meals)", key=f"g_{ing}")
            st.download_button("⬇️ Download plan (JSON)", json.dumps({"targets": {"kcal": P["target"], **P["macros"]},
                               "plan": P["plan"], "grocery": sorted(groc)}, indent=2), "foodverse_plan.json", "application/json")
        except (KeyError, TypeError) as e:
            st.error(f"Unexpected plan format ({e}). Please regenerate.")
