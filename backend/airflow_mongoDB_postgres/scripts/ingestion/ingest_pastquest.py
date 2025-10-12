import random
import pandas as pd
import os



exam_types = ["WAEC", "NECO"]
subjects = ["Mathematics", "English", "Biology", "Chemistry", "Physics", "Economics"]
years = list(range(2020, 2025))
sections = ["Objective", "Theory", "Practical"]
difficulties = ["Easy", "Moderate", "Hard"]

topics = {
    "Mathematics": ["Algebra", "Geometry", "Statistics", "Trigonometry"],
    "English": ["Grammar", "Comprehension", "Literature", "Vocabulary"],
    "Biology": ["Cell Biology", "Genetics", "Ecology", "Human Anatomy"],
    "Chemistry": ["Organic", "Inorganic", "Physical", "Acid-Base Reactions"],
    "Physics": ["Mechanics", "Electricity", "Optics", "Heat"],
    "Economics": ["Microeconomics", "Macroeconomics", "Development", "Demand & Supply"]
}

def generate_objective(subject, topic):
    templates = {
        "Mathematics": ("Find x if 3x + 2 = 11", {"A": "2", "B": "3", "C": "4", "D": "5"}, "B", "3x + 2 = 11 → x = 3"),
        "English": ("Choose the correct word: He ____ to school.", {"A": "go", "B": "goes", "C": "gone", "D": "going"}, "B", "‘He’ takes singular verb ‘goes’."),
        "Biology": ("Which organ pumps blood in the body?", {"A": "Liver", "B": "Heart", "C": "Brain", "D": "Lung"}, "B", "The heart pumps blood."),
        "Chemistry": ("What is the pH of a neutral solution?", {"A": "7", "B": "0", "C": "14", "D": "1"}, "A", "Neutral solutions have pH 7."),
        "Physics": ("What is the unit of force?", {"A": "Joule", "B": "Watt", "C": "Newton", "D": "Pascal"}, "C", "The SI unit of force is the Newton."),
        "Economics": ("What is opportunity cost?", {"A": "Best alternative forgone", "B": "Money spent", "C": "Total cost", "D": "Production cost"}, "A", "It’s the next best alternative forgone.")
    }
    return templates[subject]

def generate_theory(subject, topic):
    examples = {
        "Mathematics": ("Solve for x in 2x² + 5x - 3 = 0.", "x = 0.5 or x = -3", "Use quadratic formula: (-b ± √b² - 4ac)/2a"),
        "English": ("Write an essay on 'The Importance of Honesty in Society.'", "Essay should have intro, body, conclusion (250 words)", "Focus on moral and civic examples."),
        "Biology": ("Explain photosynthesis and list two factors affecting it.", "Photosynthesis: 6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂", "Light and chlorophyll are essential factors."),
        "Chemistry": ("Describe the laboratory preparation of oxygen gas.", "Heat potassium chlorate in presence of MnO₂ catalyst.", "Apparatus: test tube, delivery tube, gas jar."),
        "Physics": ("State and explain Ohm’s Law.", "V = IR (Voltage = Current × Resistance)", "Current through conductor is directly proportional to voltage."),
        "Economics": ("Discuss four functions of money.", "Medium of exchange, store of value, unit of account, standard of deferred payment", "Each must be clearly explained.")
    }
    return examples[subject]

def generate_practical(subject, topic):
    tasks = {
        "Biology": ("Observe the given leaf under a microscope and draw its structure.", "Diagram labeled with stomata, veins, epidermis.", "Award marks for accuracy and labeling."),
        "Chemistry": ("Titrate NaOH against HCl using phenolphthalein indicator.", "Record burette readings and calculate molarity.", "Award marks for correct readings and calculations."),
        "Physics": ("Set up a circuit with a resistor and measure current using an ammeter.", "Plot I–V graph and determine resistance.", "Award marks for accuracy and graph plotting.")
    }
    return tasks.get(subject, ("No practical for this subject", "", ""))

records = []

for year in years:
    for exam in exam_types:
        for subject in subjects:
            for section in sections:
                topic = random.choice(topics[subject])
                difficulty = random.choice(difficulties)
                if section == "Objective":
                    for q_num in range(1, 11):
                        q_text, options, ans, explain = generate_objective(subject, topic)
                        records.append({
                            "exam_type": exam,
                            "year": year,
                            "subject": subject,
                            "section": section,
                            "topic": topic,
                            "question_number": q_num,
                            "question_text": q_text,
                            "option_A": options["A"],
                            "option_B": options["B"],
                            "option_C": options["C"],
                            "option_D": options["D"],
                            "correct_answer": ans,
                            "theory_answer_guide": "",
                            "marks_allocated": 1,
                            "difficulty_level": difficulty,
                            "explanation": explain
                        })
                elif section == "Theory":
                    for q_num in range(1, 6):
                        q_text, guide, exp = generate_theory(subject, topic)
                        records.append({
                            "exam_type": exam,
                            "year": year,
                            "subject": subject,
                            "section": section,
                            "topic": topic,
                            "question_number": q_num,
                            "question_text": q_text,
                            "option_A": "",
                            "option_B": "",
                            "option_C": "",
                            "option_D": "",
                            "correct_answer": "",
                            "theory_answer_guide": guide,
                            "marks_allocated": random.randint(10, 20),
                            "difficulty_level": difficulty,
                            "explanation": exp
                        })
                elif section == "Practical" and subject in ["Biology", "Chemistry", "Physics"]:
                    for q_num in range(1, 4):
                        q_text, guide, exp = generate_practical(subject, topic)
                        records.append({
                            "exam_type": exam,
                            "year": year,
                            "subject": subject,
                            "section": section,
                            "topic": topic,
                            "question_number": q_num,
                            "question_text": q_text,
                            "option_A": "",
                            "option_B": "",
                            "option_C": "",
                            "option_D": "",
                            "correct_answer": "",
                            "theory_answer_guide": guide,
                            "marks_allocated": random.randint(15, 25),
                            "difficulty_level": difficulty,
                            "explanation": exp
                        })


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Define the c output path
output_dir = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "pastquest.csv")

#  Save CSV
df_pastquest = pd.DataFrame(records)
df_pastquest.to_csv(output_path, index=False)

print(f"pastquest.csv generated successfully at: {os.path.abspath(output_path)}")
print(df_pastquest.head())

