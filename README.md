
# FIRST — Food Insecurity Score Tracker (Streamlit Package)

This package includes a ready-to-run Streamlit app and sample data files for demo, testing, and deployment.

## Quickstart

1. Create a new virtual environment (optional, recommended).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```

## What’s Included

- `app.py` — Streamlit UI (upload or use bundled sample data; charts and RAG views).
- `data/`
  - `Food_Insecurity_Input_With_Actions.xlsx` — **complete** sample dataset (all columns filled) with recommended actions.
  - `Food_Insecurity_Input_Final.xlsx` — complete dataset without action columns.
  - `Food_Insecurity_Input_Template_With_Scoring.xlsx` — original template.
- `config/county_overrides_template.json` — example to override actions per county.
- `assets/` — place logos or images here (optional).

## App Features

- RAG summary (counts by FIRST_Threshold).
- Average Risk Score by county (bar chart).
- Trend over time (average Risk_Score by Date).
- County-level table with recommended actions.
- Download filtered data as Excel.

## Notes

- The app expects the main sheet to be **"Food Insecurity Inputs"**.
- Add your own `county_overrides.json` in the `config/` directory to replace the template.


## Included Visualizations (exported as PNGs)
- `assets/trend_average_risk_over_time.png`
- `assets/rag_summary.png`
- `assets/avg_risk_by_county.png`

These are auto-generated from the bundled sample dataset and can be replaced with your own exports.


## Reports & Exports
- **Static PNG exports:** Click **Export Static PNGs** to save filtered charts into `assets/exports/`.
- **PDF report:** Use **Build PDF Report** to generate a multi-page PDF (cover, RAG, county averages, trend, county table). You can rename the output before downloading.

## Branded Color Palette
The app uses a teal-forward palette configured in `.streamlit/config.toml` and applied to charts via a `BRAND` dictionary in `app.py`. Update hex codes as needed.


## County Profiles PDF
Use **Build PDF with County Profiles** to generate a multi-page PDF (one page per county) including metrics, RAG distribution, trend, and actions.

## Email Workflow (attachments)
In the **Email Report** section:
- Enter SMTP settings (or set via `st.secrets`).
- Choose to attach the **County Profiles PDF** and/or **static PNGs**.
- Click **Send Email Now** to email the files.

**Streamlit secrets** example (`.streamlit/secrets.toml`):
```
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT="465"
SMTP_USER="you@example.com"
SMTP_PASSWORD="your_app_password"
SMTP_TO="recipient@example.com"
```


## Per-County CSV Export
Use **Per-County CSV Export** to download individual CSVs or a ZIP of selected counties based on current filters.

## Scheduled Weekly Email
Two options:
1. **In-session scheduler** (APScheduler): Configure under **Scheduled Weekly Email (in-session)**. Emails are sent weekly **while the app is running**.
2. **Always-on GitHub Actions**: Use `.github/workflows/weekly-email.yml`. Add SMTP secrets in your repo settings and adjust the cron as needed.

### Required secrets for GitHub Actions
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_TO`


## S3 Upload & Share Links
Use the **S3 Upload & Share Links** section to upload generated reports/PNGs to Amazon S3 and get **presigned URLs** to share with leadership.

### Configure (prefer Streamlit secrets)
Add to `.streamlit/secrets.toml`:
```
AWS_S3_BUCKET="your-bucket-name"
AWS_REGION="us-east-1"
AWS_S3_PREFIX="first-exports/"
AWS_ACCESS_KEY_ID="AKIA..."
AWS_SECRET_ACCESS_KEY="..."
```
Optionally set an S3 bucket policy or use **presigned URLs** (no public access required).

**Note:** The UI supports `public-read` uploads if you prefer public objects. Otherwise, keep `private` and share presigned links.
