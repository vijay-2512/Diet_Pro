import pandas as pd
import numpy as np
import math
import random

class SimpleINDBDiet:
    def __init__(self):
        np.random.seed(42)
        foods = []
        indian_foods = ["Chicken Curry", "Egg Bhurji", "Fish Fry", "Paneer Tikka",
                        "Dal Makhani", "Rice", "Roti", "Idli Sambhar", "Dosa",
                        "Apple", "Boiled Egg", "Yogurt", "Chicken Biryani", 
                        "Mutton Korma", "Prawn Masala"]

        for i in range(1014):
            food = random.choice(indian_foods) + f" #{i}"
            foods.append({
                'code': i+1,
                'name': food,
                'kcal': np.random.randint(80, 450),
                'prot': np.random.uniform(3, 25),
                'carb': np.random.uniform(10, 70),
                'fat': np.random.uniform(2, 20),
                'fiber': np.random.uniform(0, 8),
                'category': 'Non-Veg' if any(x in food.lower() for x in ['chicken','egg','fish','biryani','mutton','prawn']) else 'Veg',
                'allergens': random.choice(['None', 'milk', 'egg', 'gluten'])
            })
        self.df = pd.DataFrame(foods)
        print(f"✅ Loaded {len(self.df)} INDB foods")

    def calculate_bmi(self, weight, height):
        bmi = weight / ((height / 100) ** 2)
        status = "Normal" if 18.5<=bmi<25 else "Underweight" if bmi<18.5 else "Overweight" if bmi<30 else "Obese"
        return round(bmi, 1), status

    def navy_body_fat(self, gender, height_cm, neck_cm, waist_cm):
        h_in = height_cm * 0.393701
        n_in = neck_cm * 0.393701
        w_in = waist_cm * 0.393701
        if gender == "male":
            body_fat = 86.010*math.log10(w_in-n_in) - 70.041*math.log10(h_in) + 36.76
        else:
            body_fat = 163.205*math.log10(w_in*1.1-n_in) - 97.684*math.log10(h_in) - 78.387
        return round(max(5, min(50, body_fat)), 1), "US Navy"

    def bmr(self, age, gender, weight, height, activity, goal):
        if gender == "m":
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)

        mult = {
            "Sedentary(No activity)": 1.2,
            "Light(Walk)": 1.375,
            "Moderate(Walk+Light Excersises)": 1.55,
            "Active(Light workout GYM)": 1.725,
            "Very active(Workout GYM + Sports)": 1.9
        }
        tdee = bmr * mult.get(activity, 1.55)

        if goal == "Weight loss":
            calories = max(1200, int(tdee * 0.75))
            if calories > 2000: calories = 1900
        elif goal == "Weight Gain":
            calories = min(3500, int(tdee * 1.25))
            if calories < 2500: calories = 2600
        else:
            calories = int(tdee)
            calories = max(2000, min(2500, calories))
        return calories

    def plan(self, age, gender, weight, height, bmi_status, body_fat,
        neck, waist, activity, goal, preference, allergy):

        calories = self.bmr(age, gender, weight, height, activity, goal)
        df = self.df.copy()

        if allergy and allergy != "None":
            df = df[df["allergens"].str.lower() != allergy.lower()]

        pref_map = {"Veg": 1,"Egg": 2,"Non-Veg": 3,"Veg+Egg": 4,"Egg+Non-Veg": 5,"Veg+Egg+Non-Veg": 6}

        preference_num = pref_map.get(preference, 6)

        if preference_num == 1:  # Veg only
            df = df[df["category"] == "Veg"]

        elif preference_num == 2:  # Egg only
            df = df[df["name"].str.contains("egg", case=False, na=False)]

        elif preference_num == 3:  # Non-Veg (no egg)
            df = df[
                (df["category"] == "Non-Veg") &
                (~df["name"].str.contains("egg", case=False, na=False))
            ]

        elif preference_num == 4:  # Veg + Egg
            df = df[
                (df["category"] == "Veg") |
                (df["name"].str.contains("egg", case=False, na=False))
            ]

        elif preference_num == 5:  # Egg + Non-Veg
            df = df[
                (df["name"].str.contains("egg", case=False, na=False)) |
                (
                    (df["category"] == "Non-Veg") &
                    (~df["name"].str.contains("egg", case=False, na=False))
                )
            ]

        elif preference_num == 6:  # Everything
            df = df

    
        if len(df) == 0:
            df = self.df

        targets = {
            "breakfast": calories * 0.22,
            "lunch": calories * 0.28,
            "snack": calories * 0.12,
            "dinner": calories * 0.38
        }

    # 🎯 GOAL-BASED MACRO CONSTRAINTS
        if goal == "Weight loss":
            min_fat = weight * 0.6
            max_fat = weight * 0.7
            min_protein = weight * 1.0

        elif goal == "Maintenance":
            min_fat = weight * 0.8
            max_fat = weight * 0.9
            min_protein = 0

        else:  # Weight Gain
            min_fat = 0
            max_fat = float("inf")
            min_protein = 0

    # 🔁 Retry loop to satisfy constraints
        for _ in range(60):
            meals = {}
            total_prot = total_carb = total_fat = total_cal = 0

            for meal, target in targets.items():
                available = df.sample(n=min(30, len(df)))
                available["cal_diff"] = abs(available["kcal"] - target)
                best_food = available.loc[available["cal_diff"].idxmin()]

                portion = max(100, min(400, int(target * 100 / best_food["kcal"])))

                kcal = int(best_food["kcal"] * portion / 100)
                prot = best_food["prot"] * portion / 100
                carb = best_food["carb"] * portion / 100
                fat = best_food["fat"] * portion / 100

                meals[meal] = {
                    "food": str(best_food["name"])[:25],
                    "type": best_food["category"],
                    "portion_g": portion,
                    "total_kcal": kcal,
                    "prot_g": round(prot, 1),
                    "carb_g": round(carb, 1),
                    "fat_g": round(fat, 1)
                }

                total_cal += kcal
                total_prot += prot
                total_carb += carb
                total_fat += fat

        # ✅ ACCEPT PLAN ONLY IF CONSTRAINTS ARE MET
            if (
                min_fat <= total_fat <= max_fat
                and total_prot >= min_protein
            ):
                break

        return {
            "meals": meals,
            "target_calories": calories,
            "total_calories": int(total_cal),
            "total_prot": round(total_prot, 1),
            "total_carb": round(total_carb, 1),
            "total_fat": round(total_fat, 1),
            "protein_target": f">= {round(min_protein,1)} g" if min_protein > 0 else None,
            "fat_range": f"{round(min_fat,1)}–{round(max_fat,1)} g",
            "bmi": bmi_status[0],
            "bmi_status": bmi_status[1],
            "body_fat": body_fat
        }
