import csv
import os

src = "NEOMA_BrainSpine_Reflex_v1.0/1_data/pcam_embodied_reflex_prior_10k.csv"
dst_dir = "data"
dst = "data/pcam_embodied_reflex_sample_100.csv"

os.makedirs(dst_dir, exist_ok=True)

with open(src, "r", encoding="utf-8") as f_in, open(dst, "w", newline="", encoding="utf-8") as f_out:
    reader = csv.reader(f_in)
    writer = csv.writer(f_out)
    for i in range(101):  # 헤더 + 100개 행
        writer.writerow(next(reader))

print("[+] 100-Row Verification Sample Extracted: data/pcam_embodied_reflex_sample_100.csv")
