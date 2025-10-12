import pandas as pd
import random
import os

# Generate school profiles across different states in Nigeria
states = ["Lagos", "Kano", "Ogun", "Abuja", "Enugu", "Kaduna", "Rivers", "Oyo", "Borno", "Delta", "Abia", "Kogi", "Ekiti"]
ownership_types = ["Public", "Private"]
school_types = ["Primary", "Junior Secondary", "Senior Secondary", "Technical college"]

schools = []
for i in range(1, 1001):  # 1000 schools
    school = {
        "school_id": f"SCH{i:03}",
        "school_name": f"{random.choice(states)} Model School {i}",
        "state": random.choice(states),
        "lga": f"LGA-{random.randint(1, 20)}",
        "ownership": random.choice(ownership_types),
        "school_type": random.choice(school_types),
        "total_teachers": random.randint(10, 80),
        "total_students": random.randint(200, 2500),
        "student_teacher_ratio": round(random.uniform(15, 60), 2),
        "facilities_score": round(random.uniform(30, 100), 2),
        "digital_learning_access": random.choice(["High", "Moderate", "Low"]),
        "performance_band": random.choice(["High", "Average", "Low"])
    }
    schools.append(school)
    
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Define the c output path
output_dir = os.path.join(BASE_DIR, "data", "raw")
output_path = os.path.join(output_dir, "schools.csv")

#  Save CSV
df_schools = pd.DataFrame(schools)
df_schools.to_csv(output_path, index=False)

print(f"schools.csv generated successfully at: {os.path.abspath(output_path)}")
print(df_schools.head())


