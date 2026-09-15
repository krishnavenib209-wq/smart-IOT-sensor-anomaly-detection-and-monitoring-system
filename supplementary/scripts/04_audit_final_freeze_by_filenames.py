from pathlib import Path
import pandas as pd

BASE = Path(r"C:\IoT-Collector\FINAL_FREEZE\dataset_canonical_v2")
OUTDIR = Path(r"C:\IoT-Collector\analysis\paperA_audit_outputs")
OUTDIR.mkdir(parents=True, exist_ok=True)

pi_dirs = ["pi4", "pi5", "pi6", "pi7"]

rows = []

for pi in pi_dirs:
    folder = BASE / pi
    files = sorted(folder.glob("*.csv"))

    if not files:
        rows.append({
            "pi_id": pi,
            "num_files": 0,
            "first_file": None,
            "last_file": None,
            "duration_days_by_filename": None
        })
        continue

    # extract dates from filenames like 2026-01-30.csv
    dates = []
    for f in files:
        try:
            d = pd.to_datetime(f.stem, format="%Y-%m-%d", errors="coerce")
            if pd.notna(d):
                dates.append(d)
        except Exception:
            pass

    if dates:
        first_date = min(dates)
        last_date = max(dates)
        duration_days = (last_date - first_date).days + 1
    else:
        first_date = None
        last_date = None
        duration_days = None

    rows.append({
        "pi_id": pi,
        "num_files": len(files),
        "first_file": first_date.date() if first_date is not None else None,
        "last_file": last_date.date() if last_date is not None else None,
        "duration_days_by_filename": duration_days
    })

result = pd.DataFrame(rows)
print("\nFINAL FREEZE coverage by filenames:")
print(result)

result.to_csv(OUTDIR / "17_final_freeze_file_coverage.csv", index=False)
print("\nSaved:", OUTDIR / "17_final_freeze_file_coverage.csv")