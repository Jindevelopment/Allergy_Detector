import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXCEL_DIR = ROOT / "data" / "excel"
CSV_DIR   = ROOT / "data" / "csv"

NAME_MAP = {
    "알레르겐_목록": "allergen_list.csv",
    "증상_가중치": "symptom_weights.csv",
    "위험도_규칙": "risk_rules.csv",
    "사용자_정보": "users_seed.csv",
    "사용자_보고": "user_reports_seed.csv"
}

def convert_all():
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    excel_files = list(EXCEL_DIR.glob("*.xlsx")) + list(EXCEL_DIR.glob("*.xls"))
    if not excel_files:
        print(f"[WARN] 엑셀 파일이 없습니다: {EXCEL_DIR}")
        sys.exit(0)

    for xf in excel_files:
        stem = xf.stem
        out_name = NAME_MAP.get(stem, f"{stem}.csv")
        out_path = CSV_DIR / out_name

        df = pd.read_excel(xf, engine="openpyxl")

        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str).str.strip()

        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"[OK] {xf.name} -> {out_path.name}")

if __name__ == "__main__":
    convert_all()
