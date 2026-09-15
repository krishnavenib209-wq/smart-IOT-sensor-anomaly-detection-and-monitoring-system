import pandas as pd
from pathlib import Path

INPUT = r"C:\IoT-Collector\ML_READY\v2_realistic_full\merged_dataset.csv"
OUTDIR = Path(r"C:\IoT-Collector\analysis\paperA_audit_outputs")

print("Loading dataset...")
df = pd.read_csv(INPUT, low_memory=False)

print("Cleaning timestamps...")

ts = df["timestamp"].astype(str)

# remove duplicated leading year patterns like 2022025-
ts = ts.str.replace(r"^20\d{2}(20\d{2}-)", r"\1", regex=True)

# remove trailing 'T' if incomplete
ts = ts.str.replace(r"T$", "", regex=True)

# parse with timezone support
parsed = pd.to_datetime(ts, errors="coerce", utc=True)

df["timestamp_clean"] = parsed

print("Valid timestamps:", parsed.notna().sum())
print("Invalid timestamps:", parsed.isna().sum())

df["date"] = parsed.dt.date

# recompute time range per device
table = (
    df.groupby("pi_id")
      .agg(
        start_time=("timestamp_clean","min"),
        end_time=("timestamp_clean","max"),
        rows=("pi_id","count")
      )
      .reset_index()
)

table["duration_days"] = (
    (table["end_time"] - table["start_time"])
    .dt.total_seconds() / 86400
).round(2)

print("\nCorrected duration table:")
print(table)

table.to_csv(OUTDIR / "05_time_range_per_device_FIXED.csv", index=False)

print("\nSaved corrected table.")