import pandas as pd
from pathlib import Path

# ============================================================
# Paths
# ============================================================
INPUT_DATASET = r"C:\IoT-Collector\analysis\setD_D2\datasets\merged_dataset_timestamp_repaired_v2.csv"
OUTPUT_DATASET = r"C:\IoT-Collector\analysis\setD_D2\datasets\merged_dataset_ml_ready.csv"
OUTPUT_REPORT = r"C:\IoT-Collector\analysis\setD_D2\datasets\merged_dataset_ml_ready_report.txt"

# ============================================================
# Load
# ============================================================
print("Loading dataset...")
df = pd.read_csv(INPUT_DATASET, low_memory=False)

print("Initial rows:", len(df))
print("Initial columns:", len(df.columns))

# Keep original row count for report
initial_rows = len(df)

# ============================================================
# 1) Remove exact duplicate rows
# ============================================================
print("Removing exact duplicate rows...")
before_dups = len(df)
df = df.drop_duplicates()
after_dups = len(df)
removed_dups = before_dups - after_dups

print("Rows after duplicate removal:", after_dups)
print("Duplicate rows removed:", removed_dups)

# ============================================================
# 2) Normalize anomaly labels
#    - Keep raw columns untouched in spirit, but standardize values
#    - Do NOT destroy multi-label information silently
# ============================================================
print("Normalizing anomaly labels...")

def normalize_text(x):
    if pd.isna(x):
        return "none"
    x = str(x).strip()
    if x == "":
        return "none"
    return x

df["anomaly_type"] = df["anomaly_type"].apply(normalize_text)
df["anomaly_source"] = df["anomaly_source"].apply(normalize_text)

# Normalize common variants
type_map = {
    "0": "none",
    "normal": "none",
    "nan": "none",
    "off": "none",
    "one": "none",   # keep if this was a known typo in early files
}

source_map = {
    "0": "none",
    "normal": "none",
    "nan": "none",
}

df["anomaly_type"] = (
    df["anomaly_type"]
    .astype(str)
    .str.strip()
    .str.lower()
    .replace(type_map)
)

df["anomaly_source"] = (
    df["anomaly_source"]
    .astype(str)
    .str.strip()
    .str.lower()
    .replace(source_map)
)

# Truncate obviously corrupted anomaly strings by mapping them to 'corrupted'
# but only if they are absurdly long
df.loc[df["anomaly_type"].str.len() > 60, "anomaly_type"] = "corrupted"
df.loc[df["anomaly_source"].str.len() > 60, "anomaly_source"] = "corrupted"

# Keep multi-label entries as they are for now, but standardize separators a bit
df["anomaly_type"] = (
    df["anomaly_type"]
    .str.replace(r"\s*;\s*", ";", regex=True)
    .str.replace(r"\s*,\s*", ",", regex=True)
    .str.replace(r"\s*\+\s*", "+", regex=True)
)

# ============================================================
# 3) Rebuild anomaly_flag consistently
#    Rule:
#    - anomaly_type == 'none'  -> anomaly_flag = 0
#    - everything else         -> anomaly_flag = 1
# ============================================================
print("Rebuilding anomaly_flag consistently...")

if "anomaly_flag" in df.columns:
    df["anomaly_flag_original"] = df["anomaly_flag"]

df["anomaly_flag"] = (df["anomaly_type"] != "none").astype(int)

# ============================================================
# 4) Timestamp handling
#    IMPORTANT:
#    Do NOT reparsedrop everything again.
#    The input dataset is already timestamp-repaired.
#    We only verify and sort safely.
# ============================================================
print("Checking timestamp column without destructive dropping...")

# Preserve original timestamp text
df["timestamp"] = df["timestamp"].astype(str).str.strip()

# Try parsing for sorting/report only
parsed_ts = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)

valid_ts = int(parsed_ts.notna().sum())
invalid_ts = int(parsed_ts.isna().sum())

print("Valid timestamps for sorting/report:", valid_ts)
print("Invalid timestamps remaining:", invalid_ts)

# Create helper sort column but DO NOT drop rows
df["_timestamp_sort"] = parsed_ts

# Sort valid timestamps first, invalid timestamps last
df = df.sort_values(by="_timestamp_sort", na_position="last")

# Remove helper column
df = df.drop(columns=["_timestamp_sort"])

# ============================================================
# 5) Save ML-ready dataset
# ============================================================
Path(OUTPUT_DATASET).parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT_DATASET, index=False)

final_rows = len(df)

print("\nML-ready dataset saved:")
print(OUTPUT_DATASET)
print("Final rows:", final_rows)

# ============================================================
# 6) Save report
# ============================================================
multi_label_rows = int(
    df["anomaly_type"].astype(str).str.contains(r"[;,+]| and ", regex=True, na=False).sum()
)

corrupted_type_rows = int((df["anomaly_type"] == "corrupted").sum())
corrupted_source_rows = int((df["anomaly_source"] == "corrupted").sum())

with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
    f.write("ML-READY DATASET BUILD REPORT\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Input dataset: {INPUT_DATASET}\n")
    f.write(f"Output dataset: {OUTPUT_DATASET}\n\n")
    f.write(f"Initial rows: {initial_rows:,}\n")
    f.write(f"Rows after duplicate removal: {after_dups:,}\n")
    f.write(f"Duplicate rows removed: {removed_dups:,}\n")
    f.write(f"Final rows saved: {final_rows:,}\n\n")
    f.write("Timestamp status:\n")
    f.write(f"  Valid timestamps: {valid_ts:,}\n")
    f.write(f"  Invalid timestamps remaining: {invalid_ts:,}\n\n")
    f.write("Label normalization summary:\n")
    f.write(f"  Multi-label anomaly rows retained: {multi_label_rows:,}\n")
    f.write(f"  Corrupted anomaly_type rows mapped to 'corrupted': {corrupted_type_rows:,}\n")
    f.write(f"  Corrupted anomaly_source rows mapped to 'corrupted': {corrupted_source_rows:,}\n\n")
    f.write("Per-device summary:\n")

    if "pi_id" in df.columns:
        summary = (
            df.groupby("pi_id")
            .agg(
                rows=("pi_id", "count"),
                anomalies=("anomaly_flag", "sum")
            )
            .reset_index()
        )
        summary["anomalies"] = summary["anomalies"].astype(int)
        summary["anomaly_rate_percent"] = (summary["anomalies"] / summary["rows"] * 100).round(4)

        for _, row in summary.iterrows():
            f.write(
                f"  {row['pi_id']}: rows={int(row['rows']):,}, "
                f"anomalies={int(row['anomalies']):,}, "
                f"rate={row['anomaly_rate_percent']}%\n"
            )

print("Report saved:")
print(OUTPUT_REPORT)