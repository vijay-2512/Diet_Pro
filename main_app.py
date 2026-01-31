import flet as ft
from src.diet_logic import SimpleINDBDiet
from src.chatbot import get_smart_response

# ---------------- BOT MESSAGE ----------------
def bot_msg(text):
    return ft.Container(
        content=ft.Text(text, size=16, color=ft.Colors.BLACK),
        padding=10,
        bgcolor=ft.Colors.BLUE_50,
        border_radius=10,
        width=350
    )

# ---------------- MAIN ----------------
def main(page: ft.Page):
    page.title = "Diet Pro"
    page.icon = "assets/icon.png"
    page.padding = 12
    page.safe_area = True
    page.scroll = ft.ScrollMode.AUTO
    page.resize_to_avoid_bottom_inset = True

    planner = SimpleINDBDiet()
    plan_count = 0
    chat_input = ft.TextField(label="Type your message", expand=True)

    # ---------------- INPUT FIELDS ----------------
    age_field = ft.TextField(label="👤 Age")
    weight_field = ft.TextField(label="⚖️ Weight (kg)")
    height_field = ft.TextField(label="📏 Height (cm)")
    neck_field = ft.TextField(label="👔 Neck (cm)")
    waist_field = ft.TextField(label="📐 Waist (cm)")

    gender_dropdown = ft.Dropdown(
        label="⚥ Gender",
        options=[ft.dropdown.Option("Male"), ft.dropdown.Option("Female")],
    )

    activity_dropdown = ft.Dropdown(
        label="🏃 Activity",
        options=[ft.dropdown.Option(x) for x in [
            "Sedentary(No activity)",
            "Light(Walk)",
            "Moderate(Walk+Light Exercises)",
            "Active(Gym)",
            "Very Active(Gym + Sports)"
        ]]
    )

    goal_dropdown = ft.Dropdown(
        label="🎯 Goal",
        options=[ft.dropdown.Option(x) for x in ["Weight loss", "Weight Gain", "Maintenance"]]
    )

    pref_dropdown = ft.Dropdown(
        label="🍽️ Preference",
        options=[ft.dropdown.Option(x) for x in ["Veg", "Egg", "Non-Veg", "Veg+Egg", "Egg+Non-Veg", "Veg+Egg+Non-Veg"]]
    )

    allergy_dropdown = ft.Dropdown(
        label="⚠️ Allergies",
        options=[ft.dropdown.Option(x) for x in ["Egg", "Gluten", "Milk", "Peanuts", "None"]]
    )

    result_text = ft.Text("👆 Fill all fields & click Calculate", size=15)

    # ---------------- FUNCTIONS ----------------
    def reset_fields():
        for f in [age_field, weight_field, height_field, neck_field, waist_field]:
            f.value = ""
        for d in [gender_dropdown, activity_dropdown, goal_dropdown, pref_dropdown, allergy_dropdown]:
            d.value = None
        result_text.value = "✅ Ready for next person"
        page.update()

    def calculate(e):
        try:
            age = float(age_field.value or 25)
            weight = float(weight_field.value or 70)
            height = float(height_field.value or 170)
            neck = float(neck_field.value or 35)
            waist = float(waist_field.value or 80)
            gender = (gender_dropdown.value or "Male").lower()

            bmi, status = planner.calculate_bmi(weight, height)
            body_fat, method = planner.navy_body_fat(gender, height, neck, waist)

            result_text.value = f"""
🎯 HEALTH SUMMARY

👤 {int(age)} yrs | {gender.upper()}
📏 {height} cm | ⚖️ {weight} kg
📊 BMI: {bmi} ({status})
💪 Body Fat: {body_fat}% ({method})

🏃 {activity_dropdown.value}
🎯 {goal_dropdown.value}
🍽️ {pref_dropdown.value}
⚠️ {allergy_dropdown.value}
"""
            page.update()
        except:
            result_text.value = "❌ Invalid inputs"
            page.update()

    def generate_plan(e):
        nonlocal plan_count
        plan_count += 1
        try:
            age = float(age_field.value or 25)
            weight = float(weight_field.value or 70)
            height = float(height_field.value or 170)
            neck = float(neck_field.value or 35)
            waist = float(waist_field.value or 80)

            gender = gender_dropdown.value or "Male"
            activity = activity_dropdown.value or "Moderate(Walk+Light Exercises)"
            goal = goal_dropdown.value or "Weight loss"
            pref = pref_dropdown.value or "Nonveg"
            allergy = allergy_dropdown.value or "None"

            bmi, status = planner.calculate_bmi(weight, height)
            body_fat, _ = planner.navy_body_fat(gender, height, neck, waist)

            plan = planner.plan(
                age, gender, weight, height,
                (bmi, status), body_fat,
                neck, waist, activity, goal, pref, allergy
            )

            meals = ""
            for m, d in plan["meals"].items():
                icon = "🥬" if d["type"] == "Veg" else "🍗"
                meals += f"{m.upper()}: {icon} {d['food']} ({d['total_kcal']} kcal)\n"

            result_text.value = f"""
🍽️ DIET PLAN #{plan_count}

🔥 Target Calories: {plan['target_calories']}kcal

{meals}
⚡ Total Calories: {plan['total_calories']}kcal
💪 Protein: {plan['total_prot']} g
🍞 Carbs: {plan['total_carb']} g
🧈 Fat: {plan['total_fat']} g
"""
            page.update()
        except Exception as ex:
            result_text.value = f"❌ Failed: {ex}"
            page.update()

    # ---------------- CHATBOT ----------------
    chat_display = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def send_chat(e):
        user_msg = chat_input.value
        if not user_msg.strip():
            return
        chat_input.value = ""

        # Show user message
        chat_display.controls.append(
            ft.Container(
                content=ft.Text(f"You: {user_msg}", size=16, color=ft.Colors.BLACK),
                padding=10,
                bgcolor=ft.Colors.GREY_200,
                border_radius=10,
                width=350
            )
        )

        # Get bot response
        bot_reply = get_smart_response(user_msg)

        # Show bot message
        chat_display.controls.append(
            ft.Row([bot_msg(bot_reply),]))
        page.update()

    # ---------------- TABS ----------------
    diet_tab = ft.Column(
        [
            ft.Text("🎯 INDB Diet Planner", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([age_field, gender_dropdown], wrap=True),
            ft.Row([weight_field, height_field], wrap=True),
            ft.Row([neck_field, waist_field], wrap=True),
            ft.Row([activity_dropdown, goal_dropdown], wrap=True),
            ft.Row([pref_dropdown, allergy_dropdown], wrap=True),
            ft.Row([
                ft.Button("📊 Calculate", on_click=calculate),
                ft.Button("🍽️ Generate", on_click=generate_plan),
                ft.Button("➡️ Next", on_click=lambda e: reset_fields())
            ], wrap=True),
            ft.Divider(),
            result_text,
        ],
        visible=True
    )

    chat_tab = ft.Column(
        [
            ft.Text("🤖 Smart Chatbot", size=22, weight=ft.FontWeight.BOLD),
            chat_display,
            ft.Row(
                [chat_input, ft.Button("🚀", on_click=send_chat)],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        ],
        expand=True,
        visible=False
    )

    # ---------------- TAB SWITCH ----------------
    def show_diet(e):
        diet_tab.visible = True
        chat_tab.visible = False
        page.update()

    def show_chat(e):
        diet_tab.visible = False
        chat_tab.visible = True
        page.update()

    # ---------------- PAGE LAYOUT ----------------
    page.add(
        ft.Column(
            [
                ft.Row([
                    ft.Button("🍽️ Diet Planner", on_click=show_diet),
                    ft.Button("💬 Chatbot", on_click=show_chat)
                ]),
                diet_tab,
                chat_tab
            ]
        )
    )

