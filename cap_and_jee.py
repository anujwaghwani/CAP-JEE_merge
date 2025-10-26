import PyPDF2
import re
import pandas as pd
from tqdm import tqdm

# ---- Step 1: Extract ALL Application IDs and Names from CAP.pdf ----

cap_pdf_path = 'CAP.pdf'  # set your CAP PDF filename
all_ids_names = []

with open(cap_pdf_path, 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    for page in reader.pages:
        text = page.extract_text()
        for line in text.split('\n'):
            match = re.search(r'EN\d{8}', line)
            if match:
                app_id = match.group()
                parts = line.split()
                idx = [i for i, p in enumerate(parts) if p == app_id]
                if idx:
                    i = idx[0]
                    name = ' '.join(parts[i+1:i+5])
                    all_ids_names.append([app_id, name])

print(f"Found {len(all_ids_names)} students in CAP.pdf")

# ---- Step 2: Extract JEE data for ALL Application IDs from JEE.pdf ----

jee_pdf_path = 'JEE.pdf'  # set your JEE PDF filename
jee_records = []
all_id_set = set(row[0] for row in all_ids_names)

with open(jee_pdf_path, "rb") as f:
    reader = PyPDF2.PdfReader(f)
    for page in tqdm(reader.pages, desc="JEE PDF Pages"):
        text = page.extract_text()
        for line in text.split("\n"):
            parts = line.split()
            if len(parts) > 4 and re.match(r"EN\d{8}", parts[1]):
                app_id = parts[1]
                if app_id in all_id_set:
                    merit_no = parts[0]
                    try:
                        jee_pos = parts.index("JEE")
                    except ValueError:
                        continue  # skip lines with no 'JEE'
                    name = " ".join(parts[2:jee_pos])
                    values = [parts[jee_pos + offset] if len(parts) > jee_pos + offset else '' for offset in range(1, 17)]
                    record = [merit_no, app_id, name] + values
                    jee_records.append(record)

columns = [
    "Merit_No", "Application_ID", "JEE_Name",
    "JEE_Main_Percentile", "JEE_Math_Percentile", "JEE_Physics_Percentile", "JEE_Chemistry_Percentile",
    "MHT_CET_PCM_Total", "MHT_CET_Math", "MHT_CET_Physics", "MHT_CET_Chemistry",
    "HSC_PCM_Percent", "HSC_Math_Percent", "HSC_Physics_Percent", "HSC_Total_Percent",
    "SSC_Total_Percent", "SSC_Math_Percent", "SSC_Science_Percent", "SSC_English_Percent"
]
jee_df = pd.DataFrame(jee_records, columns=columns)

# ---- Step 3: Merge with CAP Names ----

cap_df = pd.DataFrame(all_ids_names, columns=['Application_ID', 'CAP_Name'])
merged = pd.merge(cap_df, jee_df, on="Application_ID", how="left")

# ---- Step 4: Sort and Save ----
# (Optional: Sort by JEE Main Percentile if you want)
merged['JEE_Main_Percentile'] = pd.to_numeric(merged['JEE_Main_Percentile'], errors='coerce')
merged = merged.sort_values('JEE_Main_Percentile', ascending=False)

merged.to_csv('ALL_CAP_JEE_Merged.csv', index=False)
print(f"✅ Merged and saved {len(merged)} students as ALL_CAP_JEE_Merged.csv")
print(merged.head())
