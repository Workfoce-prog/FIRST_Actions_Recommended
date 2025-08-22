
#!/usr/bin/env python3
import os, mimetypes, ssl, boto3, pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

BRAND = {"primary":"#0F766E","accent":"#14B8A6","warn":"#F59E0B","danger":"#EF4444","ok":"#22C55E"}

DATA_PATH = os.environ.get("FIRST_DATA", "data/Food_Insecurity_Input_With_Actions.xlsx")
SHEET = os.environ.get("FIRST_SHEET", "Food Insecurity Inputs")

def build_pdf(df, out_path="FIRST_report_with_profiles.pdf"):
    with PdfPages(out_path) as pdf:
        fig, ax = plt.subplots(figsize=(8.5, 11)); ax.axis("off")
        ax.text(0.1, 0.8, "FIRST — Food Insecurity Score Tracker", fontsize=22, color=BRAND["primary"], weight="bold")
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)
    return out_path

def upload_to_s3(file_path, bucket, key, region="us-east-1"):
    s3 = boto3.client("s3", region_name=region)
    s3.upload_file(file_path, bucket, key)
    return f"s3://{bucket}/{key}"

def main():
    df = pd.read_excel(DATA_PATH, sheet_name=SHEET)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    pdf_path = build_pdf(df, out_path="FIRST_report_with_profiles.pdf")
    bucket = os.environ["AWS_S3_BUCKET"]
    prefix = os.environ.get("AWS_S3_PREFIX", "first-exports/").rstrip("/") + "/"
    region = os.environ.get("AWS_REGION", "us-east-1")
    key = prefix + os.path.basename(pdf_path)
    s3_uri = upload_to_s3(pdf_path, bucket, key, region=region)
    print("Uploaded:", s3_uri)

if __name__ == "__main__":
    main()
