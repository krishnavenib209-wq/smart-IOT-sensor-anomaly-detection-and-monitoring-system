import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# SETTINGS
# ============================================================

INPUT_CSV = r"C:\IoT-Collector\ML_READY\v2_realistic_full\merged_dataset.csv"
OUTPUT_DIR = Path(r"C:\IoT-Collector\analysis\paperA_audit_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# LOAD DATA
# ============================================================

print("Loading dataset...")
df = pd.read_csv(INPUT_CSV, low_memory=False)

print(f"Rows loaded: {len(df):,}")
print(f"Columns loaded: {len(df.columns)}")

with open(OUTPUT_DIR / "01_columns.txt", "w", encoding="utf-8") as f:
    for c in df.columns:
        f.write(c + "\n")

# ============================================================
# TYPE CLEANUP
# ============================================================

expected_sensor_cols = [
    "temperature_C",
    "humidity",
    "pir_motion",
    "accel_x_m_s2",
    "accel_y_m_s2",
    "accel_z_m_s2",
    "mq_raw",
    "mq_gas_detected",
]

for col in expected_sensor_cols + ["anomaly_flag"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

if "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["date"] = df["timestamp"].dt.date
    df["year_month"] = df["timestamp"].dt.to_period("M").astype(str)

if "anomaly_type" in df.columns:
    df["anomaly_type"] = df["anomaly_type"].replace(0, "unknown")
    df["anomaly_type"] = df["anomaly_type"].fillna("none").astype(str)

if "anomaly_source" in df.columns:
    df["anomaly_source"] = df["anomaly_source"].fillna("none").astype(str)

if "pi_id" in df.columns:
    df["pi_id"] = df["pi_id"].astype(str)

if "anomaly_flag" in df.columns and "anomaly_type" in df.columns:
    df["anomaly_flag_original"] = df["anomaly_flag"].copy()
    df["anomaly_flag_normalized"] = (df["anomaly_type"] != "none").astype(int)

# ============================================================
# BASIC SUMMARY
# ============================================================

summary = {}
summary["rows"] = len(df)
summary["columns"] = len(df.columns)

if "timestamp" in df.columns:
    summary["valid_timestamps"] = int(df["timestamp"].notna().sum())
    summary["invalid_timestamps"] = int(df["timestamp"].isna().sum())
    if df["timestamp"].notna().any():
        summary["start_timestamp"] = str(df["timestamp"].min())
        summary["end_timestamp"] = str(df["timestamp"].max())

if "pi_id" in df.columns:
    summary["num_devices"] = int(df["pi_id"].nunique())

if "anomaly_flag_normalized" in df.columns:
    total_anoms = int(df["anomaly_flag_normalized"].sum())
    summary["total_anomalies_normalized"] = total_anoms
    summary["global_anomaly_rate_percent"] = round(total_anoms / len(df) * 100, 4)

summary_df = pd.DataFrame(list(summary.items()), columns=["metric", "value"])
summary_df.to_csv(OUTPUT_DIR / "02_dataset_summary.csv", index=False)

print("\nBasic summary:")
print(summary_df)

# ============================================================
# DEVICE COUNTS
# ============================================================

if "pi_id" in df.columns:
    device_counts = df["pi_id"].value_counts().rename_axis("pi_id").reset_index(name="rows")
    device_counts.to_csv(OUTPUT_DIR / "03_device_row_counts.csv", index=False)

    plt.figure(figsize=(8, 5))
    plt.bar(device_counts["pi_id"], device_counts["rows"])
    plt.title("Rows per Device")
    plt.xlabel("Device")
    plt.ylabel("Rows")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "03_rows_per_device.png", dpi=300)
    plt.close()

# ============================================================
# ANOMALY COUNTS PER DEVICE
# ============================================================

paper_table = None
if "pi_id" in df.columns and "anomaly_flag_normalized" in df.columns:
    paper_table = (
        df.groupby("pi_id")
        .agg(
            records=("pi_id", "count"),
            anomalies=("anomaly_flag_normalized", "sum")
        )
        .reset_index()
    )
    paper_table["anomalies"] = paper_table["anomalies"].astype(int)
    paper_table["anomaly_rate_percent"] = (
        paper_table["anomalies"] / paper_table["records"] * 100
    ).round(4)

    paper_table.to_csv(OUTPUT_DIR / "04_paperA_dataset_overview_table.csv", index=False)

    plt.figure(figsize=(8, 5))
    plt.bar(paper_table["pi_id"], paper_table["anomalies"])
    plt.title("Anomalies per Device")
    plt.xlabel("Device")
    plt.ylabel("Anomaly Rows")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "04_anomalies_per_device.png", dpi=300)
    plt.close()

# ============================================================
# TIME RANGE PER DEVICE
# ============================================================

if "pi_id" in df.columns and "timestamp" in df.columns:
    time_range = (
        df.groupby("pi_id")
        .agg(
            start_time=("timestamp", "min"),
            end_time=("timestamp", "max"),
            rows=("pi_id", "count")
        )
        .reset_index()
    )
    time_range["duration_days"] = (
        (time_range["end_time"] - time_range["start_time"]).dt.total_seconds() / 86400
    ).round(2)
    time_range.to_csv(OUTPUT_DIR / "05_time_range_per_device.csv", index=False)

# ============================================================
# MISSINGNESS
# ============================================================

missing_stats = []
for col in df.columns:
    miss = int(df[col].isna().sum())
    pct = round(miss / len(df) * 100, 4)
    missing_stats.append([col, miss, pct])

missing_df = pd.DataFrame(missing_stats, columns=["column", "missing_count", "missing_pct"])
missing_df.to_csv(OUTPUT_DIR / "06_missingness_report.csv", index=False)

# ============================================================
# FEATURE STATISTICS
# ============================================================

numeric_cols_present = [c for c in expected_sensor_cols if c in df.columns]
if numeric_cols_present:
    feature_stats = df[numeric_cols_present].describe().T
    feature_stats.index.name = "feature"
    feature_stats.to_csv(OUTPUT_DIR / "07_feature_statistics.csv")

# ============================================================
# SENSOR AVAILABILITY MATRIX
# ============================================================

if "pi_id" in df.columns:
    availability_rows = []
    for pi in sorted(df["pi_id"].dropna().unique()):
        sub = df[df["pi_id"] == pi]
        row = {"pi_id": pi}
        for col in expected_sensor_cols:
            row[col] = int(col in sub.columns and sub[col].notna().sum() > 0)
        availability_rows.append(row)

    availability_df = pd.DataFrame(availability_rows)
    availability_df.to_csv(OUTPUT_DIR / "08_sensor_availability_matrix.csv", index=False)

# ============================================================
# ANOMALY TYPE DISTRIBUTION
# ============================================================

if "anomaly_type" in df.columns and "anomaly_flag_normalized" in df.columns:
    anom_only = df[df["anomaly_flag_normalized"] == 1].copy()
    anom_type = (
        anom_only["anomaly_type"]
        .value_counts()
        .rename_axis("anomaly_type")
        .reset_index(name="count")
    )
    anom_type["percentage"] = (anom_type["count"] / anom_type["count"].sum() * 100).round(4)
    anom_type.to_csv(OUTPUT_DIR / "09_anomaly_type_distribution.csv", index=False)

# ============================================================
# ANOMALY SOURCE DISTRIBUTION
# ============================================================

if "anomaly_source" in df.columns and "anomaly_flag_normalized" in df.columns:
    anom_only = df[df["anomaly_flag_normalized"] == 1].copy()
    anom_source = (
        anom_only["anomaly_source"]
        .value_counts()
        .rename_axis("anomaly_source")
        .reset_index(name="count")
    )
    anom_source["percentage"] = (anom_source["count"] / anom_source["count"].sum() * 100).round(4)
    anom_source.to_csv(OUTPUT_DIR / "10_anomaly_source_distribution.csv", index=False)

# ============================================================
# GLOBAL DAILY ANOMALY TIMELINE
# ============================================================

if "timestamp" in df.columns and "anomaly_flag_normalized" in df.columns:
    anom_only = df[df["anomaly_flag_normalized"] == 1].copy()
    global_daily = anom_only.groupby("date").size().reset_index(name="anomaly_rows")
    global_daily.to_csv(OUTPUT_DIR / "11_global_daily_anomalies.csv", index=False)

    plt.figure(figsize=(12, 5))
    plt.plot(global_daily["date"], global_daily["anomaly_rows"], marker="o")
    plt.title("Global Daily Anomaly Timeline")
    plt.xlabel("Date")
    plt.ylabel("Anomaly Rows")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "11_global_daily_anomaly_timeline.png", dpi=300)
    plt.close()

# ============================================================
# DAILY ANOMALIES PER DEVICE
# ============================================================

if "timestamp" in df.columns and "pi_id" in df.columns and "anomaly_flag_normalized" in df.columns:
    anom_only = df[df["anomaly_flag_normalized"] == 1].copy()
    daily_per_device = (
        anom_only.groupby(["date", "pi_id"])
        .size()
        .reset_index(name="anomaly_rows")
    )
    daily_per_device.to_csv(OUTPUT_DIR / "12_daily_anomalies_per_device.csv", index=False)

    if not daily_per_device.empty:
        pivot = daily_per_device.pivot(index="date", columns="pi_id", values="anomaly_rows").fillna(0)
        plt.figure(figsize=(12, 6))
        for dev in pivot.columns:
            plt.plot(pivot.index, pivot[dev], marker="o", label=dev)
        plt.title("Daily Anomaly Events per Device")
        plt.xlabel("Date")
        plt.ylabel("Anomaly Rows")
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "12_daily_anomaly_events_per_device.png", dpi=300)
        plt.close()

# ============================================================
# DEVICE-ANOMALY TABLE
# ============================================================

if "pi_id" in df.columns and "anomaly_type" in df.columns and "anomaly_flag_normalized" in df.columns:
    anom_only = df[df["anomaly_flag_normalized"] == 1].copy()
    heatmap_table = pd.crosstab(anom_only["pi_id"], anom_only["anomaly_type"])
    heatmap_table.to_csv(OUTPUT_DIR / "13_device_anomaly_heatmap_table.csv")

# ============================================================
# LABEL CHECKS
# ============================================================

issues = []
if "anomaly_flag_original" in df.columns and "anomaly_flag_normalized" in df.columns:
    mismatch = (df["anomaly_flag_original"].fillna(-1) != df["anomaly_flag_normalized"]).sum()
    issues.append(["anomaly_flag_mismatch_original_vs_normalized", int(mismatch)])

if "timestamp" in df.columns:
    issues.append(["invalid_timestamps_after_load", int(df["timestamp"].isna().sum())])

issues_df = pd.DataFrame(issues, columns=["check", "value"])
issues_df.to_csv(OUTPUT_DIR / "14_label_integrity_checks.csv", index=False)

# ============================================================
# HUMAN-READABLE SUMMARY
# ============================================================

with open(OUTPUT_DIR / "15_human_readable_summary.txt", "w", encoding="utf-8") as f:
    f.write("PAPER A DATASET AUDIT SUMMARY\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Input file: {INPUT_CSV}\n")
    f.write(f"Rows: {len(df):,}\n")
    f.write(f"Columns: {len(df.columns)}\n")

    if "timestamp" in df.columns:
        f.write(f"Valid timestamps: {df['timestamp'].notna().sum():,}\n")
        f.write(f"Invalid timestamps: {df['timestamp'].isna().sum():,}\n")
        if df["timestamp"].notna().any():
            f.write(f"Start timestamp: {df['timestamp'].min()}\n")
            f.write(f"End timestamp: {df['timestamp'].max()}\n")

    if "anomaly_flag_normalized" in df.columns:
        total_anoms = int(df["anomaly_flag_normalized"].sum())
        total_pct = round(total_anoms / len(df) * 100, 4)
        f.write(f"Total anomalies: {total_anoms:,}\n")
        f.write(f"Global anomaly rate (%): {total_pct}\n")

    if paper_table is not None:
        f.write("\nPer-device summary:\n")
        for _, row in paper_table.iterrows():
            f.write(
                f"  {row['pi_id']}: records={int(row['records']):,}, "
                f"anomalies={int(row['anomalies']):,}, "
                f"rate={row['anomaly_rate_percent']}%\n"
            )

print("\nAudit complete.")
print(f"Outputs saved to: {OUTPUT_DIR}")