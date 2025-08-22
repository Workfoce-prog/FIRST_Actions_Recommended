#!/usr/bin/env python3
# scripts/weekly_email.py
import os, mimetypes, ssl, smtplib
from email.message import EmailMessage
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

BRAND = {
    "primary": "#0F766E",
    "accent": "#14B8A6",
    "warn": "#F59E0B",
    "danger": "#EF4444",
    "ok": "#22C55E",
}

DATA_PATH = os.environ.get("FIRST_DATA", "data/Food_Insecurity_Input_With_Actions.xlsx")
SHEET = os.environ.get("FIRST_SHEET", "Food Insecurity Inputs")

def build_pdf_with_county_profiles(df_source, out_path="FIRST_report_with_profiles.pdf"):
    with PdfPages(out_path) as pdf:
        # Cover
        fig, ax = plt.subplots(figsize=(8.5, 11)); ax.axis("off")
        ax.text(0.1, 0.8, "FIRST — Food Insecurity Score Tracker", fontsize=22, color=BRAND["primary"], weight="bold")
        ax.text(0.1, 0.74, f"Rows: {len(df_source)}", fontsize=12)
        ax.text(0.1, 0.71, f"Date Range: {pd.to_datetime(df_source['Date']).min().date()} to {pd.to_datetime(df_source['Date']).max().date()}", fontsize=12)
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

        # County pages
        for county in sorted(df_source["geo"].dropna().unique().tolist()):
            sub = df_source[df_source["geo"] == county].copy()
            rows = len(sub)
            avg_risk = sub["Risk_Score"].mean()
            thr_mode = sub["FIRST_Threshold"].mode()
            threshold = thr_mode.iat[0] if not thr_mode.empty else ""
            action_mode = sub["Recommended_Actions"].mode()
            action = action_mode.iat[0] if not action_mode.empty else ""

            fig, ax = plt.subplots(figsize=(8.5, 11)); ax.axis("off")
            ax.text(0.1, 0.93, f"County Profile — {county}", fontsize=18, color=BRAND["primary"], weight="bold")
            ax.text(0.1, 0.90, f"Rows: {rows}    Avg Risk Score: {avg_risk:.3f}    Threshold: {threshold}", fontsize=11)
            ax.text(0.1, 0.86, f"Action: {action}", fontsize=10)

            # Trend
            trend = sub.groupby("Date")["Risk_Score"].mean()
            ax2 = fig.add_axes([0.1, 0.55, 0.8, 0.25])
            ax2.plot(trend.index, trend.values, marker="o", color=BRAND["accent"])
            ax2.set_title("Risk Trend"); ax2.set_xlabel(""); ax2.set_ylabel("Avg Risk")

            # RAG
            rag = sub["FIRST_Threshold"].value_counts().reindex(["Severe","High","Moderate","Low"]).fillna(0)
            ax3 = fig.add_axes([0.1, 0.35, 0.8, 0.15])
            rag.plot(kind="bar", ax=ax3, color=[BRAND["danger"], BRAND["warn"], "#EAB308", "#22C55E"])
            ax3.set_title("RAG Distribution"); ax3.set_xlabel(""); ax3.set_ylabel("Count")

            pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)
    return out_path

def send_email_with_attachments(
    smtp_server, smtp_port, username, password,
    to_address, subject, body_text, attachment_paths
):
    msg = EmailMessage()
    msg["From"] = username
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body_text)

    for path in attachment_paths:
        if not os.path.exists(path):
            continue
        mime_type, _ = mimetypes.guess_type(path)
        maintype, subtype = (mime_type.split("/", 1) if mime_type else ("application","octet-stream"))
        with open(path, "rb") as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(path))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, int(smtp_port), context=context) as server:
        server.login(username, password)
        server.send_message(msg)

def main():
    df = pd.read_excel(DATA_PATH, sheet_name=SHEET)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    pdf_path = build_pdf_with_county_profiles(df, out_path="FIRST_report_with_profiles.pdf")
    # Attachments
    attachments = [pdf_path]
    # Send
    send_email_with_attachments(
        os.environ["SMTP_SERVER"],
        os.environ["SMTP_PORT"],
        os.environ["SMTP_USER"],
        os.environ["SMTP_PASSWORD"],
        os.environ["SMTP_TO"],
        os.environ.get("EMAIL_SUBJECT", "FIRST — Weekly Food Insecurity Summary"),
        os.environ.get("EMAIL_BODY", "Please find attached the latest weekly summary."),
        attachments
    )

if __name__ == "__main__":
    main()
