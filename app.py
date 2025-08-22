
import io
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="FIRST — Food Insecurity Score Tracker", layout="wide")

st.title("FIRST — Food Insecurity Score Tracker")
st.caption("Demo app with RAG dashboard, actions mapping, and export tools")

# --- Robust base_dir and sample path resolution ---
from pathlib import Path as _Path
_base_dir = _Path(__file__).parent

def _resolve_sample_path():
    # Allow env override
    env_path = os.environ.get("FIRST_SAMPLE_PATH", "").strip()
    candidates = []
    if env_path:
        candidates.append(_base_dir / env_path if not _Path(env_path).is_absolute() else _Path(env_path))
    # Preferred bundled paths
    candidates += [
        _base_dir / "data" / "Food_Insecurity_Input_With_Actions.xlsx",
        _base_dir / "data" / "Food_Insecurity_Input_Final.xlsx",
        _base_dir / "Food_Insecurity_Input_With_Actions.xlsx",
        _base_dir / "Food_Insecurity_Input_Final.xlsx",
    ]
    for c in candidates:
        try:
            if c.exists():
                return c
        except Exception:
            pass
    return None

def _generate_minimal_sample(save_to):
    import pandas as pd, numpy as np
    cols = [
        "geo","Date","Household_Zip","School_ID","Race_Ethnicity","Gender",
        "Percentage of Households below 150% Poverty line",
        "Number Household_Children_Eligible_SNAP","Number Household_Children_Eligible_WIC",
        "Percentage of Household_Children_Reciving_SNAP","Percentage Household_Children_Reciving_WIC",
        "FRL_Status","Attendance","Unemployment_Rate","Eviction_Rate","Food_Shelf_Visits","Shutoffs",
        "FRL_Norm","Attendance_Norm","Unemp_Norm","Evict_Norm","Food_Norm","Shutoff_Norm",
        "BenefitUptake","OutreachIntensity","Communitypartner coverage",
        "Drought Severity Index","Location Adjustment Index_Rural_Urban",
        "Risk_Score","FIRST_Threshold","Meaning/Flag",
        "Recommended_Actions","Short_Term_Actions","Medium_Term_Actions","Long_Term_Actions"
    ]
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    dfm = pd.DataFrame({
        "geo": ["Hennepin County"]*5 + ["Ramsey County"]*5,
        "Date": dates,
        "Household_Zip": [55411, 55412, 55430, 55106, 55107, 55104, 55105, 55114, 55117, 55119],
        "School_ID": [f"S{i}" for i in range(1,11)],
        "Race_Ethnicity": np.random.choice(["White","Black","Hispanic","Asian"], size=10),
        "Gender": np.random.choice(["Male","Female"], size=10),
        "Percentage of Households below 150% Poverty line": np.random.randint(10,60,size=10),
        "Number Household_Children_Eligible_SNAP": np.random.randint(2000,30000,size=10),
        "Number Household_Children_Eligible_WIC": np.random.randint(500,5000,size=10),
        "Percentage of Household_Children_Reciving_SNAP": np.random.randint(30,95,size=10),
        "Percentage Household_Children_Reciving_WIC": np.random.randint(20,90,size=10),
        "FRL_Status": np.random.choice(["Free","Reduced","Paid"], size=10),
        "Attendance": np.round(np.random.uniform(70,100,size=10),1),
        "Unemployment_Rate": np.round(np.random.uniform(2,15,size=10),1),
        "Eviction_Rate": np.round(np.random.uniform(0,10,size=10),2),
        "Food_Shelf_Visits": np.random.randint(50,2000,size=10),
        "Shutoffs": np.random.randint(0,200,size=10),
    })
    # Norms and scores
    for c in ["FRL_Norm","Attendance_Norm","Unemp_Norm","Evict_Norm","Food_Norm","Shutoff_Norm"]:
        dfm[c] = np.round(np.random.uniform(0,1,size=10),3)
    dfm["Risk_Score"] = dfm[["FRL_Norm","Attendance_Norm","Unemp_Norm","Evict_Norm","Food_Norm","Shutoff_Norm"]].mean(axis=1).round(3)
    def band(x):
        return "Severe" if x>=0.75 else ("High" if x>=0.5 else ("Moderate" if x>=0.25 else "Low"))
    dfm["FIRST_Threshold"] = dfm["Risk_Score"].apply(band)
    meaning_map = {"Severe":"Crisis-level instability or hardship","High":"Structural challenges likely","Moderate":"Warning signs present","Low":"Stability / low risk"}
    dfm["Meaning/Flag"] = dfm["FIRST_Threshold"].map(meaning_map)
    action_map = {
        "Severe": "Immediate intervention: expand SNAP/EBT outreach, emergency food support, housing & utility relief",
        "High": "Strengthen safety nets: partner with schools, community orgs, increase program uptake",
        "Moderate": "Monitor closely: targeted outreach, boost enrollment in WIC/SNAP, preventive supports",
        "Low": "Maintain stability: continue community engagement, periodic monitoring"
    }
    dfm["Recommended_Actions"] = dfm["FIRST_Threshold"].map(action_map)
    dfm["Short_Term_Actions"] = dfm["FIRST_Threshold"].map({
        "Severe":"Deploy emergency food, rental, and utility assistance immediately",
        "High":"Expand outreach for SNAP/WIC enrollment within 3 months",
        "Moderate":"Identify at-risk groups and conduct targeted outreach",
        "Low":"Keep monitoring monthly and maintain existing supports"
    })
    dfm["Medium_Term_Actions"] = dfm["FIRST_Threshold"].map({
        "Severe":"Scale up cross-agency coordination, increase food shelf capacity",
        "High":"Partner with schools and health providers for support programs",
        "Moderate":"Pilot community workshops on nutrition and budgeting",
        "Low":"Sustain partnerships and prepare quarterly reports"
    })
    dfm["Long_Term_Actions"] = dfm["FIRST_Threshold"].map({
        "Severe":"Invest in housing stability, employment programs, and structural reforms",
        "High":"Strengthen resilience through community partnerships and workforce pathways",
        "Moderate":"Develop monitoring systems and preventive strategies",
        "Low":"Maintain resilience planning and evaluate bi-annually"
    })
    save_to.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(str(save_to), engine="openpyxl") as writer:
        dfm.to_excel(writer, index=False, sheet_name="Food Insecurity Inputs")
    return save_to


# --- Sidebar controls ---
st.sidebar.header("Data Source")
uploaded = st.sidebar.file_uploader("Upload Excel (sheet: 'Food Insecurity Inputs')", type=["xlsx"])

use_sample = st.sidebar.checkbox("Use bundled sample dataset", value=True)
sample_path = _resolve_sample_path()

# County overrides
st.sidebar.header("Overrides")
use_overrides = st.sidebar.checkbox("Apply county overrides (if found)", value=True)
overrides_path = st.sidebar.text_input("Overrides JSON path", "config/county_overrides_template.json")

# --- Load Data ---
@st.cache_data
def load_excel(path_or_buffer):
    df = pd.read_excel(path_or_buffer, sheet_name="Food Insecurity Inputs")
    # Ensure Date is datetime
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df

df = None

if uploaded is not None:
    df = load_excel(uploaded)
elif use_sample:
    try:
        if sample_path is None or not Path(sample_path).exists():
            # Attempt to generate a minimal sample so app never breaks
            gen_path = _base_dir / "data" / "Food_Insecurity_Input_With_Actions.xlsx"
            sample_path = _generate_minimal_sample(gen_path)
        df = load_excel(sample_path)
    except Exception as e:
        st.error(f"Could not load sample file: {e}")


if df is None:
    st.warning("Upload a dataset or enable 'Use bundled sample dataset' to proceed.")
    st.stop()

# --- Optional: apply county overrides ---
if use_overrides and overrides_path:
    try:
        with open(overrides_path, "r") as f:
            overrides = json.load(f)
        for county, mapping in overrides.items():
            mask = df["geo"].astype(str).str.lower() == str(county).lower()
            for col, val in mapping.items():
                if col in df.columns:
                    df.loc[mask, col] = val
                else:
                    # Create the column if not exists
                    df.loc[mask, col] = val
    except Exception as e:
        st.info(f"No valid overrides applied ({e}).")

# --- Filters ---
st.sidebar.header("Filters")
counties = sorted(df["geo"].dropna().unique().tolist())
county_sel = st.sidebar.multiselect("County", counties, default=counties)
min_date = pd.to_datetime(df["Date"]).min()
max_date = pd.to_datetime(df["Date"]).max()
date_range = st.sidebar.date_input("Date range", [min_date, max_date])

mask = df["geo"].isin(county_sel)
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    mask &= (df["Date"] >= start) & (df["Date"] <= end)

df_f = df.loc[mask].copy()

# --- KPI cards ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Rows", len(df_f))
col2.metric("Mean Risk Score", f"{df_f['Risk_Score'].mean():.3f}")
col3.metric("Severe/High", int((df_f["FIRST_Threshold"].isin(["Severe", "High"])).sum()))
col4.metric("Low/Moderate", int((df_f["FIRST_Threshold"].isin(["Low", "Moderate"])).sum()))

# --- RAG Summary ---
st.subheader("RAG Summary")
rag_counts = df_f["FIRST_Threshold"].value_counts().reindex(["Severe","High","Moderate","Low"]).fillna(0)

fig1, ax1 = plt.subplots(figsize=(5,4))
rag_counts.plot(kind="bar", ax=ax1)
ax1.set_xlabel("FIRST Threshold")
ax1.set_ylabel("Number of Records")
ax1.set_title("Counts by Risk Level")
st.pyplot(fig1)

# --- Average Risk by County ---
st.subheader("Average Risk Score by County")
county_risk = df_f.groupby("geo")["Risk_Score"].mean().sort_values(ascending=False)
fig2, ax2 = plt.subplots(figsize=(7,4))
county_risk.plot(kind="barh", ax=ax2)
ax2.invert_yaxis()
ax2.set_xlabel("Average Risk Score")
ax2.set_ylabel("County")
st.pyplot(fig2)

# --- Trend over time ---
st.subheader("Trend of Average Risk Over Time")
date_risk = df_f.groupby("Date")["Risk_Score"].mean()
fig3, ax3 = plt.subplots(figsize=(8,4))
ax3.plot(date_risk.index, date_risk.values, marker="o")
ax3.set_xlabel("Date")
ax3.set_ylabel("Average Risk Score")
st.pyplot(fig3)

# --- County-level Actions Table ---
st.subheader("County-Level Actions")
summary = (
    df_f.groupby("geo")
    .agg(
        Avg_Risk_Score=("Risk_Score","mean"),
        Threshold=("FIRST_Threshold", lambda x: x.mode().iat[0] if not x.mode().empty else ""),
        Action=("Recommended_Actions", lambda x: x.mode().iat[0] if not x.mode().empty else ""),
        Short_Term=("Short_Term_Actions", lambda x: x.mode().iat[0] if not x.mode().empty else ""),
        Medium_Term=("Medium_Term_Actions", lambda x: x.mode().iat[0] if not x.mode().empty else ""),
        Long_Term=("Long_Term_Actions", lambda x: x.mode().iat[0] if not x.mode().empty else ""),
    )
    .reset_index()
    .sort_values("Avg_Risk_Score", ascending=False)
)
st.dataframe(summary, use_container_width=True)

# --- Download filtered data ---
st.subheader("Download")
def to_excel_bytes(df_out: pd.DataFrame) -> bytes:
    import io
    from pandas import ExcelWriter
    with io.BytesIO() as buffer:
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_out.to_excel(writer, index=False, sheet_name="Food Insecurity Inputs")
        return buffer.getvalue()

st.download_button(
    "Download filtered dataset (Excel)",
    data=to_excel_bytes(df_f),
    file_name=f"FIRST_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


st.markdown("""
<hr/>
<div style="font-size: 0.9rem;">
<strong>FIRST &mdash; Food Insecurity Score Tracker</strong> &bull; StratDesign Solutions<br/>
Need a custom build, data integrations, or county-specific overrides? <a href="mailto:info@stratdesignsolutions.com">Contact us</a>.
</div>
""", unsafe_allow_html=True)



# --- Static Visuals (optional, from assets) ---
with st.expander("Static Visuals (exported PNGs)"):
    import pathlib
    asset_files = {
        "Trend of Average Risk Score Over Time": "assets/trend_average_risk_over_time.png",
        "Food Insecurity Risk Levels (RAG Summary)": "assets/rag_summary.png",
        "Average Risk Score by County": "assets/avg_risk_by_county.png",
    }
    for title, path in asset_files.items():
        p = pathlib.Path(path)
        if p.exists():
            st.markdown(f"**{title}**")
            st.image(str(p), use_column_width=True)



# --- Branded color palette ---
BRAND = {
    "primary": "#0F766E",  # teal
    "accent": "#14B8A6",   # teal-400
    "warn": "#F59E0B",     # amber-500
    "danger": "#EF4444",   # red-500
    "ok": "#22C55E",       # green-500
    "bg2": "#F1F5F9"
}



# --- PDF Report Export (using matplotlib.backends.backend_pdf) ---
from matplotlib.backends.backend_pdf import PdfPages

def build_pdf_report(df_source, out_path="FIRST_report.pdf", title="FIRST — Food Insecurity Report"):
    import matplotlib.pyplot as plt
    import pandas as pd
    from textwrap import fill

    with PdfPages(out_path) as pdf:
        # Cover page
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis("off")
        cover_text = f"{title}\n\nRows: {len(df_source)}\nDate Range: {pd.to_datetime(df_source['Date']).min().date()} to {pd.to_datetime(df_source['Date']).max().date()}"
        ax.text(0.1, 0.8, "FIRST — Food Insecurity Score Tracker", fontsize=22, color=BRAND["primary"], weight="bold")
        ax.text(0.1, 0.72, cover_text, fontsize=12)
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

        # RAG Summary
        rag_counts = df_source["FIRST_Threshold"].value_counts().reindex(["Severe","High","Moderate","Low"]).fillna(0)
        fig, ax = plt.subplots(figsize=(8.5, 5))
        rag_counts.plot(kind="bar", ax=ax, color=[BRAND["danger"], BRAND["warn"], "#EAB308", BRAND["ok"]])
        ax.set_title("Food Insecurity Risk Levels (RAG Summary)")
        ax.set_xlabel("Risk Level")
        ax.set_ylabel("Records")
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

        # Avg Risk by County
        county_risk = df_source.groupby("geo")["Risk_Score"].mean().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(8.5, max(3, 0.4*len(county_risk)+2)))
        county_risk.plot(kind="barh", ax=ax, color=BRAND["primary"])
        ax.invert_yaxis()
        ax.set_title("Average Risk Score by County")
        ax.set_xlabel("Average Risk Score")
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

        # Trend over time
        date_risk = df_source.groupby("Date")["Risk_Score"].mean()
        fig, ax = plt.subplots(figsize=(8.5, 4))
        ax.plot(date_risk.index, date_risk.values, marker="o", color=BRAND["accent"])
        ax.set_title("Trend of Average Risk Score Over Time")
        ax.set_xlabel("Date"); ax.set_ylabel("Average Risk Score")
        fig.autofmt_xdate()
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

        # County-level actions table (first 20 rows)
        summary = (
            df_source.groupby("geo")
            .agg(
                Avg_Risk_Score=("Risk_Score","mean"),
                Threshold=("FIRST_Threshold", lambda x: x.mode().iat[0] if not x.mode().empty else ""),
                Action=("Recommended_Actions", lambda x: x.mode().iat[0] if not x.mode().empty else "")
            )
            .reset_index()
            .sort_values("Avg_Risk_Score", ascending=False)
        )
        fig, ax = plt.subplots(figsize=(8.5, min(11, 1 + 0.4*len(summary))))
        ax.axis("off")
        ax.set_title("County-Level Summary", loc="left")
        table = ax.table(cellText=summary.values[:20],
                         colLabels=summary.columns,
                         loc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.2)
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    return out_path



# --- County Filtered Static Exports (PNG) ---
def export_static_pngs(df_source, out_dir="assets/exports"):
    import os, matplotlib.pyplot as plt
    os.makedirs(out_dir, exist_ok=True)

    # 1) Trend over time
    date_risk = df_source.groupby("Date")["Risk_Score"].mean().reset_index()
    fig, ax = plt.subplots(figsize=(10,5))
    ax.plot(date_risk["Date"], date_risk["Risk_Score"], marker="o", color=BRAND["accent"])
    ax.set_title("Trend of Average Risk Score Over Time")
    ax.set_xlabel("Date"); ax.set_ylabel("Average Risk Score")
    fig.autofmt_xdate(); fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "trend_average_risk_over_time.png"), dpi=160); plt.close(fig)

    # 2) RAG summary
    rag_counts = df_source["FIRST_Threshold"].value_counts()
    fig, ax = plt.subplots(figsize=(7,5))
    rag_counts.plot(kind="bar", ax=ax, color=[BRAND["danger"], BRAND["warn"], "#EAB308", BRAND["ok"]])
    ax.set_title("Food Insecurity Risk Levels (RAG Summary)")
    ax.set_xlabel("Risk Level"); ax.set_ylabel("Number of Records")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "rag_summary.png"), dpi=160); plt.close(fig)

    # 3) Average Risk by County
    county_risk = df_source.groupby("geo")["Risk_Score"].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8,5))
    county_risk.plot(kind="barh", ax=ax, color=BRAND["primary"])
    ax.set_title("Average Risk Score by County")
    ax.set_xlabel("Average Risk Score"); ax.set_ylabel("County")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "avg_risk_by_county.png"), dpi=160); plt.close(fig)

# UI elements to export based on the currently filtered dataframe
st.subheader("Reports & Exports")
colA, colB, colC = st.columns(3)
with colA:
    if st.button("Export Static PNGs (using current filters)"):
        export_static_pngs(df_f, out_dir="assets/exports")
        st.success("Static PNGs exported to assets/exports")
with colB:
    pdf_name = st.text_input("PDF filename", "FIRST_report.pdf")
with colC:
    if st.button("Build PDF Report (using current filters)"):
        path = build_pdf_report(df_f, out_path=pdf_name)
        with open(pdf_name, "rb") as f:
            st.download_button("Download PDF Report", f, file_name=pdf_name, mime="application/pdf")



# --- Extended PDF with County Profile pages ---
def build_pdf_with_county_profiles(df_source, out_path="FIRST_report_with_profiles.pdf", title="FIRST — Food Insecurity Report (with County Profiles)"):
    import matplotlib.pyplot as plt
    import pandas as pd
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages(out_path) as pdf:
        # Cover page
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis("off")
        cover_text = f"{title}\n\nRows: {len(df_source)}\nDate Range: {pd.to_datetime(df_source['Date']).min().date()} to {pd.to_datetime(df_source['Date']).max().date()}"
        ax.text(0.1, 0.8, "FIRST — Food Insecurity Score Tracker", fontsize=22, color=BRAND.get("primary", "#0F766E"), weight="bold")
        ax.text(0.1, 0.72, cover_text, fontsize=12)
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

        # Global RAG Summary
        rag_counts = df_source["FIRST_Threshold"].value_counts().reindex(["Severe","High","Moderate","Low"]).fillna(0)
        fig, ax = plt.subplots(figsize=(8.5, 5))
        rag_counts.plot(kind="bar", ax=ax, color=[BRAND["danger"], BRAND["warn"], "#EAB308", BRAND["ok"]])
        ax.set_title("Food Insecurity Risk Levels (RAG Summary)")
        ax.set_xlabel("Risk Level"); ax.set_ylabel("Records")
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

        # Global Avg Risk by County
        county_risk = df_source.groupby("geo")["Risk_Score"].mean().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(8.5, max(3, 0.4*len(county_risk)+2)))
        county_risk.plot(kind="barh", ax=ax, color=BRAND["primary"])
        ax.invert_yaxis()
        ax.set_title("Average Risk Score by County")
        ax.set_xlabel("Average Risk Score")
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

        # Global Trend
        date_risk = df_source.groupby("Date")["Risk_Score"].mean()
        fig, ax = plt.subplots(figsize=(8.5, 4))
        ax.plot(date_risk.index, date_risk.values, marker="o", color=BRAND["accent"])
        ax.set_title("Trend of Average Risk Score Over Time")
        ax.set_xlabel("Date"); ax.set_ylabel("Average Risk Score")
        fig.autofmt_xdate()
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

        # County Profiles (one page per county)
        for county in sorted(df_source["geo"].dropna().unique().tolist()):
            sub = df_source[df_source["geo"] == county].copy()
            # Metrics
            rows = len(sub)
            avg_risk = sub["Risk_Score"].mean()
            thr_mode = sub["FIRST_Threshold"].mode()
            threshold = thr_mode.iat[0] if not thr_mode.empty else ""
            action_mode = sub["Recommended_Actions"].mode()
            action = action_mode.iat[0] if not action_mode.empty else ""
            severe_count = (sub["FIRST_Threshold"] == "Severe").sum()
            high_count = (sub["FIRST_Threshold"] == "High").sum()
            moderate_count = (sub["FIRST_Threshold"] == "Moderate").sum()
            low_count = (sub["FIRST_Threshold"] == "Low").sum()

            # Page layout
            fig, ax = plt.subplots(figsize=(8.5, 11))
            ax.axis("off")
            y = 0.95
            ax.text(0.1, y, f"County Profile — {county}", fontsize=18, color=BRAND["primary"], weight="bold"); y -= 0.05
            ax.text(0.1, y, f"Rows: {rows}    Avg Risk Score: {avg_risk:.3f}    Threshold: {threshold}", fontsize=11); y -= 0.03
            ax.text(0.1, y, f"RAG: Severe={severe_count}  High={high_count}  Moderate={moderate_count}  Low={low_count}", fontsize=11); y -= 0.05

            # Mini charts (RAG and Trend)
            # RAG counts
            rag = sub["FIRST_Threshold"].value_counts().reindex(["Severe","High","Moderate","Low"]).fillna(0)
            ax_inset1 = fig.add_axes([0.1, 0.6, 0.35, 0.25])
            rag.plot(kind="bar", ax=ax_inset1, color=[BRAND["danger"], BRAND["warn"], "#EAB308", BRAND["ok"]])
            ax_inset1.set_title("RAG Distribution"); ax_inset1.set_xlabel(""); ax_inset1.set_ylabel("Count")

            # Trend
            trend = sub.groupby("Date")["Risk_Score"].mean()
            ax_inset2 = fig.add_axes([0.55, 0.6, 0.35, 0.25])
            ax_inset2.plot(trend.index, trend.values, marker="o", color=BRAND["accent"])
            ax_inset2.set_title("Risk Trend"); ax_inset2.set_xlabel(""); ax_inset2.set_ylabel("Avg Risk")

            # Actions box
            ax_actions = fig.add_axes([0.1, 0.3, 0.8, 0.2])
            ax_actions.axis("off")
            ax_actions.text(0, 1, "Recommended Actions", fontsize=12, weight="bold", color=BRAND["primary"])
            ax_actions.text(0, 0.7, f"- {action}", fontsize=10)
            # If separate action columns exist, show them
            for label, col in [("Short-term", "Short_Term_Actions"), ("Medium-term", "Medium_Term_Actions"), ("Long-term", "Long_Term_Actions")]:
                if col in sub.columns:
                    modev = sub[col].mode()
                    if not modev.empty:
                        ax_actions.text(0, 0.7 - 0.12*(["Short-term","Medium-term","Long-term"].index(label)+1), f"- {label}: {modev.iat[0]}", fontsize=10)

            # Key fields table (first 10 rows)
            show_cols = [c for c in ["Date","School_ID","Household_Zip","Attendance","Unemployment_Rate","Eviction_Rate","Food_Shelf_Visits","Shutoffs","Risk_Score","FIRST_Threshold"] if c in sub.columns]
            tab = sub[show_cols].head(10).copy()
            ax_table = fig.add_axes([0.1, 0.05, 0.8, 0.2])
            ax_table.axis("off")
            table = ax_table.table(cellText=tab.values, colLabels=tab.columns, loc="center")
            table.auto_set_font_size(False); table.set_fontsize(7); table.scale(1, 1.1)

            pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    return out_path



# --- Email Workflow: send PDF/PNGs via SMTP ---
import smtplib, ssl, mimetypes, os
from email.message import EmailMessage

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

# --- UI: Email section ---
with st.expander("Email Report (attach current PDF/PNGs)"):
    st.markdown("**Use Streamlit secrets for production** (e.g., `st.secrets['SMTP_USER']`).")
    # Try to pull defaults from secrets
    def get_secret(key, default=""):
        try:
            return st.secrets.get(key, default)
        except Exception:
            return default

    smtp_server = st.text_input("SMTP Server", value=get_secret("SMTP_SERVER", "smtp.gmail.com"))
    smtp_port = st.text_input("SMTP Port", value=str(get_secret("SMTP_PORT", "465")))
    smtp_user = st.text_input("SMTP Username", value=get_secret("SMTP_USER", ""), help="From email address / login")
    smtp_pass = st.text_input("SMTP Password", value=get_secret("SMTP_PASSWORD", ""), type="password")

    to_addr = st.text_input("To", value=get_secret("SMTP_TO", ""))
    subject = st.text_input("Subject", "FIRST — Food Insecurity Report")
    body = st.text_area("Email body", "Attached are the current FIRST report and visuals.")

    # Attachment selection
    default_pdf = "FIRST_report_with_profiles.pdf"
    attach_pdf = st.checkbox("Attach PDF report with county profiles", value=True)
    attach_pngs = st.checkbox("Attach static PNGs (from assets/exports)", value=True)

    if st.button("Send Email Now"):
        attachments = []
        if attach_pdf and os.path.exists(default_pdf):
            attachments.append(default_pdf)
        if attach_pngs:
            for fn in ["trend_average_risk_over_time.png","rag_summary.png","avg_risk_by_county.png"]:
                p = os.path.join("assets","exports", fn)
                if os.path.exists(p):
                    attachments.append(p)
        if not attachments:
            st.warning("No attachments found. Build the PDF and export PNGs first.")
        else:
            try:
                send_email_with_attachments(
                    smtp_server, smtp_port, smtp_user, smtp_pass,
                    to_addr, subject, body, attachments
                )
                st.success(f"Email sent to {to_addr} with {len(attachments)} attachment(s).")
            except Exception as e:
                st.error(f"Failed to send email: {e}")



# --- Build County Profiles PDF ---
st.subheader("County Profiles Report")
colP1, colP2 = st.columns([1,2])
with colP1:
    if st.button("Build PDF with County Profiles (using current filters)"):
        path = build_pdf_with_county_profiles(df_f, out_path="FIRST_report_with_profiles.pdf")
        with open(path, "rb") as f:
            st.download_button("Download County Profiles PDF", f, file_name="FIRST_report_with_profiles.pdf", mime="application/pdf")
with colP2:
    st.markdown("Creates a **multi-page PDF** with one page per county including metrics, mini RAG chart, mini trend, and actions.")



# --- Per-County CSV Export ---
st.subheader("Per-County CSV Export")
export_counties = st.multiselect("Select counties to export as CSV", counties, default=county_sel)
colE1, colE2 = st.columns(2)

def _county_csv_bytes(df_src, county_name):
    dfc = df_src[df_src["geo"] == county_name].copy()
    return dfc.to_csv(index=False).encode("utf-8")

with colE1:
    if st.button("Show CSV Download Buttons (per county)"):
        if not export_counties:
            st.warning("Select one or more counties first.")
        else:
            for c in export_counties:
                st.download_button(
                    label=f"Download {c}.csv",
                    data=_county_csv_bytes(df_f, c),
                    file_name=f"{c.replace(' ','_')}.csv",
                    mime="text/csv"
                )

with colE2:
    if st.button("Export Selected Counties as ZIP"):
        if not export_counties:
            st.warning("Select one or more counties first.")
        else:
            import zipfile, io
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                for c in export_counties:
                    z.writestr(f"{c.replace(' ','_')}.csv", df_f[df_f["geo"]==c].to_csv(index=False))
            st.download_button(
                "Download counties_export.zip",
                data=buf.getvalue(),
                file_name="counties_export.zip",
                mime="application/zip"
            )



# --- Scheduled Weekly Email (in-session) ---
from apscheduler.schedulers.background import BackgroundScheduler
import datetime as _dt

if "weekly_email_cfg" not in st.session_state:
    st.session_state["weekly_email_cfg"] = {}
if "scheduler" not in st.session_state:
    st.session_state["scheduler"] = None

with st.expander("Scheduled Weekly Email (in-session)"):
    st.markdown("Configure a weekly email summary **while this app is running**. For always-on scheduling, see the GitHub Actions workflow in the README.")
    # Settings
    days_map = {"Mon": "mon", "Tue":"tue", "Wed":"wed", "Thu":"thu", "Fri":"fri", "Sat":"sat", "Sun":"sun"}
    dow = st.selectbox("Day of week", list(days_map.keys()), index=0)
    send_time = st.time_input("Send time (server time)", value=_dt.time(9,0))
    # Reuse email settings from Email Report section if present, else blank
    smtp_server = st.text_input("SMTP Server (for scheduler)", value=st.session_state.get("smtp_server", st.secrets.get("SMTP_SERVER", "smtp.gmail.com")))
    smtp_port = st.text_input("SMTP Port (for scheduler)", value=str(st.session_state.get("smtp_port", st.secrets.get("SMTP_PORT", "465"))))
    smtp_user = st.text_input("SMTP Username (for scheduler)", value=st.session_state.get("smtp_user", st.secrets.get("SMTP_USER", "")))
    smtp_pass = st.text_input("SMTP Password (for scheduler)", value=st.session_state.get("smtp_pass", st.secrets.get("SMTP_PASSWORD", "")), type="password")
    to_addr = st.text_input("To (for scheduler)", value=st.session_state.get("to_addr", st.secrets.get("SMTP_TO", "")))
    subject = st.text_input("Subject (for scheduler)", value="FIRST — Weekly Food Insecurity Summary")
    body = st.text_area("Email body (for scheduler)", value="Attached are the weekly FIRST report and visuals.")
    include_profiles_pdf = st.checkbox("Attach County Profiles PDF", value=True)
    include_pngs = st.checkbox("Attach static PNGs", value=True)

    def weekly_email_job():
        # Build report/PNGs using current filtered df_f
        if include_profiles_pdf:
            build_pdf_with_county_profiles(df_f, out_path="FIRST_report_with_profiles.pdf")
        if include_pngs:
            export_static_pngs(df_f, out_dir="assets/exports")
        attachments = []
        if include_profiles_pdf and os.path.exists("FIRST_report_with_profiles.pdf"):
            attachments.append("FIRST_report_with_profiles.pdf")
        if include_pngs:
            for fn in ["trend_average_risk_over_time.png","rag_summary.png","avg_risk_by_county.png"]:
                p = os.path.join("assets","exports", fn)
                if os.path.exists(p):
                    attachments.append(p)
        if not attachments:
            return
        try:
            send_email_with_attachments(
                smtp_server, smtp_port, smtp_user, smtp_pass,
                to_addr, subject, body, attachments
            )
        except Exception as e:
            # Log to Streamlit console
            print(f"[Scheduler] Email send failed: {e}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Start Weekly Scheduler"):
            if st.session_state["scheduler"] is None:
                st.session_state["scheduler"] = BackgroundScheduler()
                st.session_state["scheduler"].start()
            # Store settings
            st.session_state["weekly_email_cfg"] = {
                "dow": days_map[dow],
                "hour": send_time.hour,
                "minute": send_time.minute,
                "smtp_server": smtp_server,
                "smtp_port": smtp_port,
                "smtp_user": smtp_user,
                "smtp_pass": smtp_pass,
                "to_addr": to_addr,
                "subject": subject,
                "body": body,
                "attach_pdf": include_profiles_pdf,
                "attach_pngs": include_pngs
            }
            # Schedule job
            try:
                st.session_state["scheduler"].add_job(
                    weekly_email_job,
                    "cron",
                    day_of_week=days_map[dow],
                    hour=send_time.hour,
                    minute=send_time.minute,
                    id="weekly_email_job",
                    replace_existing=True
                )
                st.success(f"Scheduled weekly email for {dow} at {send_time.strftime('%H:%M')} (server time).")
            except Exception as e:
                st.error(f"Failed to schedule: {e}")

    with c2:
        if st.button("Stop Scheduler"):
            if st.session_state["scheduler"]:
                try:
                    st.session_state["scheduler"].remove_job("weekly_email_job")
                except Exception:
                    pass
                st.session_state["scheduler"].shutdown(wait=False)
                st.session_state["scheduler"] = None
                st.info("Scheduler stopped.")
            else:
                st.info("No scheduler running.")



# --- S3 Upload & Share Links ---
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError, ClientError

def _get_secret(key, default=""):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default

def get_s3_client(region_name=None, aws_access_key_id=None, aws_secret_access_key=None):
    kwargs = {}
    if region_name: kwargs["region_name"] = region_name
    if aws_access_key_id and aws_secret_access_key:
        kwargs["aws_access_key_id"] = aws_access_key_id
        kwargs["aws_secret_access_key"] = aws_secret_access_key
    return boto3.client("s3", **kwargs)

def s3_upload(file_path, bucket, key, region=None, acl="private"):
    s3 = get_s3_client(region_name=region)
    s3.upload_file(file_path, bucket, key, ExtraArgs={"ACL": acl})

def s3_presigned_url(bucket, key, expires_in=3600, region=None):
    s3 = get_s3_client(region_name=region)
    try:
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=int(expires_in)
        )
    except Exception as e:
        return None

def _list_available_exports():
    paths = []
    # County profiles PDF (if built)
    if os.path.exists("FIRST_report_with_profiles.pdf"):
        paths.append("FIRST_report_with_profiles.pdf")
    # Static PNGs (if exported)
    for fn in ["trend_average_risk_over_time.png", "rag_summary.png", "avg_risk_by_county.png"]:
        p = os.path.join("assets", "exports", fn)
        if os.path.exists(p):
            paths.append(p)
    # Counties ZIP (if created)
    pzip = os.path.join("assets", "exports", "counties_export.zip")
    if os.path.exists(pzip):
        paths.append(pzip)
    return paths

with st.expander("S3 Upload & Share Links"):
    st.markdown("Configure AWS settings via **secrets** in production. You can also enter them below for local testing.")
    bucket = st.text_input("S3 Bucket", value=_get_secret("AWS_S3_BUCKET", ""))
    region = st.text_input("AWS Region", value=_get_secret("AWS_REGION", "us-east-1"))
    prefix = st.text_input("Key Prefix (folder path in bucket)", value=_get_secret("AWS_S3_PREFIX", "first-exports/"))
    expires_hours = st.slider("Presigned URL Expiry (hours)", min_value=1, max_value=168, value=72)  # up to 7 days
    acl_public = st.checkbox("Make objects public-read (optional; presigned URLs work without public access)", value=False)

    # Credentials (prefer secrets)
    access_key = st.text_input("AWS Access Key ID", value=_get_secret("AWS_ACCESS_KEY_ID", ""), help="Use Streamlit secrets in production")
    secret_key = st.text_input("AWS Secret Access Key", value=_get_secret("AWS_SECRET_ACCESS_KEY", ""), type="password")

    available = _list_available_exports()
    st.write("Available exports found:", available if available else "None yet — build the PDF/PNGs first.")

    files_to_upload = st.multiselect("Select files to upload", available, default=available)

    if st.button("Upload & Create Links"):
        if not bucket or not files_to_upload:
            st.warning("Please provide a bucket and choose at least one file.")
        else:
            links = []
            for path in files_to_upload:
                key = f"{prefix.rstrip('/')}/{os.path.basename(path)}"
                try:
                    # Create a client with explicit creds if provided
                    s3 = get_s3_client(region_name=region, aws_access_key_id=access_key or None, aws_secret_access_key=secret_key or None)
                    extra = {"ACL": "public-read"} if acl_public else {}
                    s3.upload_file(path, bucket, key, ExtraArgs=extra if extra else None)
                    url = s3_presigned_url(bucket, key, expires_in=expires_hours*3600, region=region)
                    links.append({"file": path, "s3_key": key, "presigned_url": url})
                except (NoCredentialsError, ClientError, BotoCoreError) as e:
                    st.error(f"Upload failed for {path}: {e}")
            if links:
                st.success(f"Uploaded {len(links)} file(s) to s3://{bucket}/{prefix}")
                st.dataframe(pd.DataFrame(links))
                # Also provide a JSON download of links
                import io
                buf = io.StringIO()
                json.dump(links, buf)
                st.download_button("Download links.json", data=buf.getvalue(), file_name="s3_links.json", mime="application/json")

