import os
import shutil
import pandas as pd

# ==== CONFIGURATION ====
csv_path = r"E:\BIS\Bismarvel\BISDB\SP\MasterTable_SPs.csv"
source_folder = r"E:\BIS\Bismarvel\BISDB\SP"
destination_folder = r"E:\BIS\Bismarvel\BISDB\SP\PendingSPs"
verification_folder = r"E:\BIS\Bismarvel\BISDB\SP\ReadCompletedSPs"

# create destination if not exists
os.makedirs(destination_folder, exist_ok=True)

# ==== READ CSV ====
df = pd.read_csv(csv_path)

# ==== FILTER ROWS ====
filtered = df[df["SizeKB"] > 0.0]

# ==== PROCESS FILES ====
for name in filtered["Name"]:
    try:
        source_file = os.path.join(source_folder, name + ".sql")
        dest_file = os.path.join(destination_folder, name + ".sql")

        #File should not be copied if it already exists in the verification folder, which means it has been processed.
        if os.path.isfile(source_file) and not os.path.isfile(os.path.join(verification_folder, name + ".sql")):
            shutil.copy2(source_file, dest_file)
            print(f"Copied: {name}")
        else:
            print(f"Not found or already processed: {name}")
    except Exception as e:
        print(f"ERROR processing {name}: {e}")
        continue

print("Done.")