import pandas as pd
import random
import os


subjects = [
    "Mathematics", "English", "Biology", "Chemistry", "Physics", 
    "Economics", "Civic Education", "Computer Science", "Agricultural Science", "History",
    "Social studies", "Cultural Arts", "Physical Health Education", "CRS", "IRK", "Digital science",
    "Basic Education", "Basic science",  "Yoruba language", "Igbo Langauge", "Hausa language", "French Language"
]
qualifications = ["NCE", "B.Ed", "B.Sc (Ed)", "M.Ed", "PhD"]
genders = ["Male", "Female"]

teachers = []
for i in range(1, 501):  # 500 teachers
    teacher = {
        "teacher_id": f"TCH{i:04}",
        "teacher_name": f"Teacher_{i}",
        "gender": random.choice(genders),
        "age": random.randint(24, 60),
        "qualification": random.choice(qualifications),
        "years_experience": random.randint(1, 35),
        "subject_specialization": random.choice(subjects),
        "school_id": f"SCH{random.randint(1, 100):03}",
        "training_attended_2020_2024": random.randint(0, 8),
        "teacher_rating": round(random.uniform(2.0, 5.0), 2),
        "teacher_satisfaction": random.choice(["High", "Moderate", "Low"]),
    }
    teachers.append(teacher)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Define the c output path
output_dir = os.path.join(BASE_DIR, "data", "raw")
output_path = os.path.join(output_dir, "teachers.csv")

#  Save CSV
df_teachers = pd.DataFrame(teachers)
df_teachers.to_csv(output_path, index=False)

print(f"teachers.csv generated successfully at: {os.path.abspath(output_path)}")
print(df_teachers.head())


