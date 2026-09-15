from pathlib import Path
import pandas as pd

FREEZE = Path(r"C:\IoT-Collector\FINAL_FREEZE\dataset_canonical_v2")
MERGED = Path(r"C:\IoT-Collector\ML_READY\v2_realistic_full\merged_dataset.csv")

pi_dirs = ["pi4", "pi5", "pi6", "pi7"]

print("\nCounting rows directly from FINAL_FREEZE files...\n")

freeze_counts = {}
total_freeze = 0

for pi in pi_dirs:
    folder = FREEZE / pi
    count = 0

    for f in sorted(folder.glob("*.csv")):
        # subtract header row
        rows = sum(1 for _ in open(f, "r", encoding="utf8")) - 1
        count += rows

    freeze_counts[pi] = count
    total_freeze += count

print("Rows per device from FINAL_FREEZE:")
for k,v in freeze_counts.items():
    print(f"{k}: {v:,}")

print("\nTotal rows from FINAL_FREEZE:", f"{total_freeze:,}")

print("\nReading merged dataset row count...")
merged_rows = sum(1 for _ in open(MERGED, "r", encoding="utf8")) - 1

print("Rows in merged_dataset:", f"{merged_rows:,}")

print("\nDifference (merged - freeze):", merged_rows - total_freeze)

if merged_rows == total_freeze:
    print("\n✔ MERGED DATASET IS COMPLETE")
else:
    print("\n⚠ MERGED DATASET DOES NOT MATCH SOURCE FILES")