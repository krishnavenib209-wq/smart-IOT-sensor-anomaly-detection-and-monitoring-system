import pandas as pd
from pathlib import Path

# =========================
# Paths
# =========================
INPUT_FILE = Path(r"C:\IoT-Collector\analysis\setD_D2\datasets\merged_dataset_ml_ready.csv")

OUT_DIR = Path(r"C:\IoT-Collector\publication_dataset\data\clients_full")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_FILE = OUT_DIR / "clients_full_summary.csv"

# =========================
# Load dataset
# =========================
print("Loading curated merged dataset...")
df = pd.read_csv(INPUT_FILE, low_memory=False)

print(f"Rows loaded: {len(df):,}")
print(f"Columns loaded: {len(df.columns):,}")

# =========================
# Detect device column
# =========================
possible_device_cols = ["pi_id", "device", "device_id", "client_id"]
device_col = None

for col in possible_device_cols:
    if col in df.columns:
        device_col = col
        break

if device_col is None:
    raise ValueError(
        f"No device column found. Expected one of: {possible_device_cols}. "
        f"Available columns: {list(df.columns)}"
    )

print(f"Using device column: {device_col}")

# =========================
# Detect anomaly column
# =========================
possible_label_cols = ["anomaly_flag", "label", "target", "is_anomaly"]
label_col = None

for col in possible_label_cols:
    if col in df.columns:
        label_col = col
        break

if label_col is None:
    raise ValueError(
        f"No anomaly/label column found. Expected one of: {possible_label_cols}. "
        f"Available columns: {list(df.columns)}"
    )

print(f"Using anomaly column: {label_col}")

# =========================
# Standardize device names
# =========================
df[device_col] = df[device_col].astype(str).str.lower().str.strip()

expected_devices = ["pi4", "pi5", "pi6", "pi7"]

summary_rows = []

# =========================
# Save full client partitions
# =========================
print("\nBuilding full device-level client partitions...")

for dev in expected_devices:
    client_df = df[df[device_col] == dev].copy()

    if client_df.empty:
        print(f"WARNING: No rows found for {dev}")
        continue

    out_file = OUT_DIR / f"{dev}_client_full.csv"
    client_df.to_csv(out_file, index=False)

    rows = len(client_df)
    anomalies = int(client_df[label_col].fillna(0).astype(int).sum())
    anomaly_rate = (anomalies / rows) * 100 if rows > 0 else 0

    summary_rows.append({
        "client": dev,
        "rows": rows,
        "anomalies": anomalies,
        "anomaly_rate_percent": round(anomaly_rate, 4),
        "file": str(out_file)
    })

    print(
        f"Saved {dev}: rows={rows:,}, "
        f"anomalies={anomalies:,}, "
        f"rate={anomaly_rate:.4f}%"
    )

# =========================
# Save summary
# =========================
summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv(SUMMARY_FILE, index=False)

print("\nDone.")
print(f"Clients saved to: {OUT_DIR}")
print(f"Summary saved to: {SUMMARY_FILE}")

print("\nSummary:")
print(summary_df)