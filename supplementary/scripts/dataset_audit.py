import pandas as pd
import os
from datetime import datetime

# ==============================
# CONFIGURATION
# ==============================

DATASET_PATH = r"C:\IoT-Collector\ML_READY\v2_realistic_full\merged_dataset.csv"

OUTPUT_DIR = r"C:\IoT-Collector\analysis\dataset_audit"
os.makedirs(OUTPUT_DIR, exist_ok=True)

REPORT_FILE = os.path.join(OUTPUT_DIR, "dataset_audit_report.txt")


# ==============================
# LOAD DATASET
# ==============================

print("Loading dataset...")

df = pd.read_csv(DATASET_PATH)

print("Rows:", len(df))
print("Columns:", len(df.columns))


# ==============================
# START REPORT
# ==============================

report = []

report.append("DATASET AUDIT REPORT")
report.append("="*50)
report.append(f"Rows: {len(df)}")
report.append(f"Columns: {len(df.columns)}")
report.append("")


# ==============================
# 1 VERIFY TIMESTAMP EXISTS
# ==============================

if "timestamp" not in df.columns:
    report.append("ERROR: timestamp column missing")
else:
    report.append("OK: timestamp column exists")


# ==============================
# 2 CHECK MALFORMED TIMESTAMPS
# ==============================

print("Checking timestamp format...")

df["timestamp_parsed"] = pd.to_datetime(df["timestamp"], errors="coerce")

malformed = df["timestamp_parsed"].isna().sum()

report.append("")
report.append("Timestamp Validation")
report.append("--------------------")
report.append(f"Malformed timestamps: {malformed}")


# ==============================
# 3 CHECK TIMESTAMP MONOTONICITY
# ==============================

print("Checking timestamp order...")

df_sorted = df.sort_values("timestamp_parsed")

time_diff = df_sorted["timestamp_parsed"].diff()

negative_jumps = (time_diff < pd.Timedelta(0)).sum()

report.append("")
report.append("Timestamp Monotonicity")
report.append("----------------------")
report.append(f"Backward timestamp jumps: {negative_jumps}")


# ==============================
# 4 CHECK MISSING DAYS
# ==============================

print("Checking missing days...")

df["date"] = df["timestamp_parsed"].dt.date

dates = sorted(df["date"].dropna().unique())

missing_days = []

for i in range(len(dates)-1):

    diff = (dates[i+1] - dates[i]).days

    if diff > 1:
        missing_days.append((dates[i], dates[i+1]))

report.append("")
report.append("Missing Days")
report.append("-------------")

if len(missing_days) == 0:
    report.append("No missing days detected")
else:
    for d in missing_days:
        report.append(f"Gap between {d[0]} and {d[1]}")


# ==============================
# 5 SENSOR COLUMN CHECK
# ==============================

expected_columns = [
    "temperature",
    "humidity",
    "motion",
    "accel_x",
    "accel_y",
    "accel_z",
    "gas",
]

report.append("")
report.append("Sensor Column Validation")
report.append("------------------------")

for col in expected_columns:
    if col in df.columns:
        report.append(f"{col}: OK")
    else:
        report.append(f"{col}: MISSING")


# ==============================
# 6 DUPLICATE RECORDS
# ==============================

print("Checking duplicates...")

duplicates = df.duplicated().sum()

report.append("")
report.append("Duplicate Records")
report.append("-----------------")
report.append(f"Duplicate rows: {duplicates}")


# ==============================
# 7 ANOMALY FIELD VALIDATION
# ==============================

print("Checking anomaly labels...")

valid_types = [
    "none",
    "cpu_stress",
    "pir_false_motion",
    "pir_suppressed",
    "adxl_spike",
    "mq_gas_spike",
    "net_jitter",
]

report.append("")
report.append("Anomaly Type Validation")
report.append("-----------------------")

invalid_types = df[~df["anomaly_type"].isin(valid_types)]

report.append(f"Invalid anomaly_type rows: {len(invalid_types)}")

invalid_file = os.path.join(OUTPUT_DIR, "invalid_anomaly_types.csv")
invalid_types.to_csv(invalid_file, index=False)


# ==============================
# 8 LONG STRING ANOMALIES
# ==============================

print("Checking corrupted anomaly strings...")

long_strings = df[df["anomaly_type"].astype(str).str.len() > 40]

report.append("")
report.append("Corrupted Anomaly Labels")
report.append("------------------------")
report.append(f"Very long anomaly strings: {len(long_strings)}")

long_file = os.path.join(OUTPUT_DIR, "corrupted_anomaly_labels.csv")
long_strings.to_csv(long_file, index=False)


# ==============================
# 9 DOUBLE ANOMALY RECORDS
# ==============================

print("Checking multi-anomaly labels...")

multi_anom = df[df["anomaly_type"].astype(str).str.contains(",|/|;| and ")]

report.append("")
report.append("Multiple Anomaly Labels")
report.append("-----------------------")
report.append(f"Rows with multiple anomalies: {len(multi_anom)}")

multi_file = os.path.join(OUTPUT_DIR, "multi_anomaly_rows.csv")
multi_anom.to_csv(multi_file, index=False)


# ==============================
# SAVE REPORT
# ==============================

with open(REPORT_FILE, "w") as f:
    for line in report:
        f.write(line + "\n")

print("Audit complete")

print("Report saved:", REPORT_FILE)