import pandas as pd

path = r"C:\IoT-Collector\ML_READY\v2_realistic_full\merged_dataset.csv"

df = pd.read_csv(path, usecols=["timestamp"], low_memory=False)

print("Total rows:", len(df))

parsed = pd.to_datetime(df["timestamp"], errors="coerce")

print("Valid timestamps:", parsed.notna().sum())
print("Invalid timestamps:", parsed.isna().sum())

print("\nExamples of invalid timestamps:")
print(df.loc[parsed.isna(), "timestamp"].head(20))