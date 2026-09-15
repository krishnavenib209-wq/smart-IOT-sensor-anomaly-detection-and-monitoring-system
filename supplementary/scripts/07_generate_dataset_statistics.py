import pandas as pd
from pathlib import Path

# ============================================================
# PATHS
# ============================================================
DATASET_PATH = r"C:\IoT-Collector\analysis\setD_D2\datasets\merged_dataset_ml_ready.csv"
OUTPUT_DIR = Path(r"C:\IoT-Collector\analysis\setD_D2\final_statistics_v2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Loading ML-ready dataset...")
df = pd.read_csv(DATASET_PATH, low_memory=False)

print("Rows:", len(df))
print("Columns:", len(df.columns))

# ============================================================
# 1) FEATURE STATISTICS
# ============================================================
print("Generating feature statistics...")

numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()

feature_stats = df[numeric_cols].describe().T
feature_stats.index.name = "feature"
feature_stats.to_csv(OUTPUT_DIR / "01_feature_statistics.csv")

print("Saved: 01_feature_statistics.csv")

# ============================================================
# 2) ANOMALY DISTRIBUTION BY TYPE
# ============================================================
print("Generating anomaly type distribution...")

anom_only = df[df["anomaly_flag"] == 1].copy()

anomaly_dist = (
    anom_only["anomaly_type"]
    .value_counts()
    .reset_index()
)
anomaly_dist.columns = ["anomaly_type", "count"]
anomaly_dist["percentage"] = (
    anomaly_dist["count"] / anomaly_dist["count"].sum() * 100
).round(3)

anomaly_dist.to_csv(OUTPUT_DIR / "02_anomaly_type_distribution.csv", index=False)

print("Saved: 02_anomaly_type_distribution.csv")

# ============================================================
# 3) TEMPORAL ANOMALY DISTRIBUTION
#    FIXED for mixed timestamp formats / mixed timezones
# ============================================================
print("Generating temporal anomaly distribution...")

# Force UTC so mixed timezone strings do not break .dt
df["timestamp_parsed"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce",
    utc=True
)

# Keep only rows with valid parsed timestamps for temporal analysis
df_time = df[df["timestamp_parsed"].notna()].copy()

print("Valid timestamps used for temporal analysis:", len(df_time))
print("Invalid timestamps excluded from temporal analysis:", df["timestamp_parsed"].isna().sum())

# Extract date safely
df_time["date"] = df_time["timestamp_parsed"].dt.date

daily_anomalies = (
    df_time[df_time["anomaly_flag"] == 1]
    .groupby("date")
    .size()
    .reset_index(name="anomaly_count")
)

daily_anomalies.to_csv(OUTPUT_DIR / "03_daily_anomalies.csv", index=False)

print("Saved: 03_daily_anomalies.csv")

# ============================================================
# 4) SENSOR AVAILABILITY
# ============================================================
print("Generating sensor availability matrix...")

sensor_cols = [
    col for col in df.columns
    if any(k in col.lower() for k in ["temp", "hum", "pir", "accel", "mq", "gas"])
]

availability = {}
for col in sensor_cols:
    availability[col] = df[col].notna().sum()

availability_df = pd.DataFrame.from_dict(
    availability, orient="index", columns=["available_samples"]
)
availability_df.index.name = "sensor"

availability_df["percentage"] = (
    availability_df["available_samples"] / len(df) * 100
).round(2)

availability_df.to_csv(OUTPUT_DIR / "04_sensor_availability.csv")

print("Saved: 04_sensor_availability.csv")

# ============================================================
# 5) SIMPLE SUMMARY REPORT
# ============================================================
print("Writing summary report...")

with open(OUTPUT_DIR / "05_statistics_summary.txt", "w", encoding="utf-8") as f:
    f.write("DATASET STATISTICS SUMMARY\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Input dataset: {DATASET_PATH}\n")
    f.write(f"Rows: {len(df):,}\n")
    f.write(f"Columns: {len(df.columns)}\n")
    f.write(f"Total anomaly rows: {int((df['anomaly_flag'] == 1).sum()):,}\n")
    f.write(
        f"Global anomaly rate (%): "
        f"{round((df['anomaly_flag'] == 1).sum() / len(df) * 100, 4)}\n"
    )
    f.write(f"Valid timestamps used for temporal analysis: {len(df_time):,}\n")
    f.write(
        f"Invalid timestamps excluded from temporal analysis: "
        f"{int(df['timestamp_parsed'].isna().sum()):,}\n"
    )

print("Saved: 05_statistics_summary.txt")

# ============================================================
# DONE
# ============================================================
print("\nAll dataset statistics generated successfully.")
print("Output folder:", OUTPUT_DIR)