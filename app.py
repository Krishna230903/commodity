"""
Complete Project: India's Commodity Price History (All-in-One)

V3.1: Fixed TypeError in data loading calls by removing the
      third argument (the obsolete mock function) when calling
      load_and_clean_data from the get_... functions.

This single file contains all three parts of the project:
1.  Part 1: Data Pipeline (Real data loading and cleaning)
2.  Part 2: Analysis Engine (Plotting functions)
3.  Part 3: Interactive App (Streamlit web user interface)

To run:
1.  **DOWNLOAD** required data files into a 'data/' subfolder.
2.  **UPDATE** file paths and cleaning steps in Part 1 functions.
3.  Install requirements: pip install streamlit pandas matplotlib seaborn openpyxl requests
4.  Run from terminal: streamlit run app.py
"""

# ==============================================================================
# --- IMPORTS ---
# ==============================================================================
import streamlit as st
import pandas as pd
from pandas.errors import EmptyDataError
import os
import io
import openpyxl # Required by pandas for .xlsx
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import seaborn as sns
import requests # For potential API/direct URL downloads

# ==============================================================================
# --- GLOBAL SETTINGS ---
# ==============================================================================
CLEAN_DATA_DIR = "clean_data"
RAW_DATA_DIR = "data"
sns.set_style("whitegrid")

# ==============================================================================
# --- PART 1: DATA PIPELINE (HELPER FUNCTIONS) ---
# ==============================================================================

def setup_directories():
    """Creates 'clean_data' and 'data' directories if they don't exist."""
    for dir_path in [CLEAN_DATA_DIR, RAW_DATA_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            # print(f"Created directory: {dir_path}")

@st.cache_data # Cache the results of data loading and cleaning
def load_and_clean_data(clean_file, source_info):
    """
    Main data loading function.
    Tries to load clean CSV. If not found, attempts to load and clean
    raw data based on source_info.
    """
    clean_file_path = os.path.join(CLEAN_DATA_DIR, clean_file)

    if os.path.exists(clean_file_path):
        try:
            # print(f"Loading cached data: {clean_file}")
            df = pd.read_csv(clean_file_path, parse_dates=True, index_col='Date')
            if df.empty:
                print(f"WARNING: Clean file {clean_file} is empty. Re-processing...")
                os.remove(clean_file_path)
                st.rerun()
            return df
        except (EmptyDataError, Exception) as e:
             print(f"Error reading cached file {clean_file}: {e}. Re-processing...")
             if os.path.exists(clean_file_path): os.remove(clean_file_path)
             st.rerun()

    # --- If clean file doesn't exist or was invalid, process raw data ---
    print(f"Processing raw data for: {clean_file}")
    df_raw = None
    source_type = source_info.get('type')
    path_or_url = source_info.get('path') or source_info.get('url')
    skiprows = source_info.get('skiprows', 0)
    sheet_name = source_info.get('sheet_name', 0)

    try:
        # --- File Loading based on type ---
        if source_type == 'local_excel':
            full_path = os.path.join(RAW_DATA_DIR, path_or_url)
            if not os.path.exists(full_path): raise FileNotFoundError(full_path)
            df_raw = pd.read_excel(full_path, skiprows=skiprows, sheet_name=sheet_name)
        elif source_type == 'local_csv':
            full_path = os.path.join(RAW_DATA_DIR, path_or_url)
            if not os.path.exists(full_path): raise FileNotFoundError(full_path)
            df_raw = pd.read_csv(full_path, skiprows=skiprows)
        elif source_type == 'url_csv':
            df_raw = pd.read_csv(path_or_url, skiprows=skiprows)
        elif source_type == 'url_excel':
             df_raw = pd.read_excel(path_or_url, skiprows=skiprows, sheet_name=sheet_name)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

        # --- Basic Cleaning (Requires User Adaptation) ---
        # Ensure essential keys exist
        if 'date_col' not in source_info or 'value_cols' not in source_info or 'new_names' not in source_info:
             raise KeyError("source_info dictionary missing required keys ('date_col', 'value_cols', 'new_names')")
        if len(source_info['value_cols']) != len(source_info['new_names']):
             raise ValueError("Length mismatch between 'value_cols' and 'new_names'")

        rename_dict = {source_info['date_col']: 'Date_Str'}
        for old, new in zip(source_info['value_cols'], source_info['new_names']):
            rename_dict[old] = new

        # Check if all columns to be renamed actually exist
        missing_cols = [col for col in rename_dict if col not in df_raw.columns]
        if missing_cols:
            raise KeyError(f"Columns to rename not found in raw data: {missing_cols}")

        df_raw = df_raw.rename(columns=rename_dict)

        date_format = source_info.get('date_format')
        # Ensure Date_Str column exists before converting
        if 'Date_Str' not in df_raw.columns:
            raise KeyError(f"Date column '{source_info['date_col']}' not found or not renamed correctly.")

        df_raw['Date'] = pd.to_datetime(df_raw['Date_Str'], format=date_format, errors='coerce')
        df_raw.dropna(subset=['Date'], inplace=True)

        final_cols = ['Date'] + source_info['new_names']
        # Check if all final columns exist after potential drops/renames
        missing_final = [col for col in final_cols if col not in df_raw.columns]
        if missing_final:
             raise KeyError(f"Expected final columns missing after processing: {missing_final}")


        df_clean = df_raw[final_cols].copy()
        for col in source_info['new_names']:
            if df_clean[col].dtype == 'object':
                 df_clean[col] = df_clean[col].astype(str).str.replace(r'[₹,NA\-]', '', regex=True).str.strip()
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

        df_clean = df_clean.set_index('Date').dropna()

        if df_clean.empty:
            st.error(f"Failed to process data for {clean_file}. No valid data found after cleaning. Check raw file and cleaning parameters.")
            return None

        df_clean.to_csv(clean_file_path)
        print(f"Clean data saved to {clean_file_path}")
        return df_clean

    except FileNotFoundError as e:
        st.error(f"Data file not found: {os.path.basename(str(e))}. Please download it to the '{RAW_DATA_DIR}/' folder.")
        return None
    except EmptyDataError:
        st.error(f"Raw data file for {clean_file} is empty.")
        return None
    except KeyError as e:
         st.error(f"Column '{e}' not found while processing {clean_file}. Check file structure/script parameters.")
         return None
    except Exception as e:
        st.error(f"An unexpected error occurred processing {clean_file}: {e}")
        return None

# --- Specific Data Getters ---
# ADAPT source_info DICTIONARIES BELOW BASED ON YOUR ACTUAL FILES!

def get_wpi_data():
    source_info = {
        'type': 'url_csv', # Assumes this URL is stable
        'url': "https://data.gov.in/files/ogdpv2dms/s3fs-public/Wholesale_Price_Index__WPI___New_Series__2011-12__Monthly_1_0_0.csv",
        'date_col': 'Month-Year',
        'value_cols': ['Food Articles', 'Fuel & Power', 'Manufactured Products', 'Vegetables'],
        'new_names': ['WPI_Food', 'WPI_Fuel', 'WPI_Manuf', 'WPI_Vegetables'],
        'date_format': '%b-%y'
    }
    # **FIX:** Call with only 2 arguments
    return load_and_clean_data('clean_wpi_2011_present.csv', source_info)

def get_forex_reserves():
    source_info = {
        'type': 'local_excel',
        'path': 'RBI_Forex_Reserves_Historical.xlsx', # UPDATE FILENAME
        'skiprows': 5, # UPDATE SKIPROWS
        'sheet_name': 0, # UPDATE (use 0 for first sheet if name unknown)
        'date_col': 'Month / Year', # UPDATE DATE COL NAME
        'value_cols': ['Total Reserves (USD Million)'], # UPDATE VALUE COL NAME
        'new_names': ['Forex_USD_Million'],
        'date_format': '%Y %b' # UPDATE DATE FORMAT
    }
    # **FIX:** Call with only 2 arguments
    return load_and_clean_data('clean_forex_reserves.csv', source_info)

def get_historical_gold_prices():
    source_info = {
        'type': 'local_csv',
        'path': 'Gold_INR_1947_Present.csv', # UPDATE FILENAME
        'date_col': 'Year', # UPDATE DATE COL NAME
        'value_cols': ['Price_per_10g_INR'], # UPDATE VALUE COL NAME
        'new_names': ['Price_per_10g_INR'],
        'date_format': '%Y' # UPDATE DATE FORMAT
    }
    # **FIX:** Call with only 2 arguments
    return load_and_clean_data('clean_gold_prices.csv', source_info)

def get_mcx_copper():
     source_info = {
        'type': 'local_csv',
        'path': 'MCX_Copper_Futures_Daily.csv', # UPDATE FILENAME
        'date_col': 'Date', # UPDATE DATE COL NAME
        'value_cols': ['Close'], # UPDATE VALUE COL NAME (usually 'Close')
        'new_names': ['Price_per_kg_INR'], # Name it appropriately
        # date_format usually auto-detected for YYYY-MM-DD
    }
     # **FIX:** Call with only 2 arguments
     return load_and_clean_data('clean_mcx_copper.csv', source_info)

@st.cache_data
def get_oil_petrol_inr_data():
    """Loads and merges Brent(USD), USD/INR, and Petrol(INR) data."""
    # (This function was already correct as it bypassed the helper)
    clean_file_path = os.path.join(CLEAN_DATA_DIR, 'clean_oil_petrol_inr.csv')
    raw_oil_path = os.path.join(RAW_DATA_DIR, 'global_brent_usd_daily.csv') # UPDATE
    raw_inr_path = os.path.join(RAW_DATA_DIR, 'rbi_usd_inr_daily.csv')      # UPDATE
    raw_petrol_path = os.path.join(RAW_DATA_DIR, 'ppac_petrol_delhi_daily.csv') # UPDATE

    if os.path.exists(clean_file_path):
        try:
            df = pd.read_csv(clean_file_path, parse_dates=True, index_col='Date')
            if df.empty : raise EmptyDataError
            return df
        except (EmptyDataError, Exception) as e:
            print(f"Error reading or empty cached Oil/Petrol/INR file: {e}. Re-processing...")
            if os.path.exists(clean_file_path): os.remove(clean_file_path)
    try:
        print(f"Processing raw files: Oil, INR, Petrol")
        # --- Load Brent Oil Data (USD) --- ADAPT
        df_oil = pd.read_csv(raw_oil_path, skiprows=0)
        df_oil = df_oil.rename(columns={'Date': 'Date_Str', 'Price': 'Brent_USD'})
        df_oil['Date'] = pd.to_datetime(df_oil['Date_Str'], errors='coerce')
        df_oil = df_oil[['Date', 'Brent_USD']].dropna(subset=['Date'])
        df_oil['Brent_USD'] = pd.to_numeric(df_oil['Brent_USD'], errors='coerce')

        # --- Load INR Data (USD to INR rate) --- ADAPT
        df_inr = pd.read_csv(raw_inr_path, skiprows=0)
        df_inr = df_inr.rename(columns={'Date': 'Date_Str', 'Value': 'USD_INR'})
        df_inr['Date'] = pd.to_datetime(df_inr['Date_Str'], errors='coerce')
        df_inr = df_inr[['Date', 'USD_INR']].dropna(subset=['Date'])
        df_inr['USD_INR'] = pd.to_numeric(df_inr['USD_INR'], errors='coerce')

        # --- Load Petrol Data (INR per Litre) --- ADAPT
        df_petrol = pd.read_csv(raw_petrol_path, skiprows=0)
        df_petrol = df_petrol.rename(columns={'Date': 'Date_Str', 'Delhi_Price': 'Petrol_Delhi'})
        df_petrol['Date'] = pd.to_datetime(df_petrol['Date_Str'], errors='coerce')
        df_petrol = df_petrol[['Date', 'Petrol_Delhi']].dropna(subset=['Date'])
        df_petrol['Petrol_Delhi'] = pd.to_numeric(df_petrol['Petrol_Delhi'], errors='coerce')

        # --- Merge Data ---
        df_merged = pd.merge(df_oil, df_inr, on='Date', how='inner')
        df_merged = pd.merge(df_merged, df_petrol, on='Date', how='inner')
        df_merged['Brent_in_INR'] = df_merged['Brent_USD'] * df_merged['USD_INR']
        df_clean = df_merged.set_index('Date').dropna()

        if df_clean.empty:
            st.error("Merging Oil/Petrol/INR failed - no overlapping dates or data invalid.")
            return None

        df_clean.to_csv(clean_file_path)
        print(f"Clean Oil/Petrol/INR data saved to {clean_file_path}")
        return df_clean

    except FileNotFoundError as e:
        st.error(f"Raw data file not found for Oil/Petrol/INR: {e}. Download files to '{RAW_DATA_DIR}/'.")
        return None
    except (EmptyDataError, KeyError, Exception) as e:
        st.error(f"Failed to process Oil/Petrol/INR data: {e}. Check file structures/names.")
        return None


# ==============================================================================
# --- PART 2: ANALYSIS & VISUALIZATION FUNCTIONS ---
# ==============================================================================
# (Plotting functions remain the same as v3.0)
def create_error_fig(message):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.text(0.5, 0.5, f"⚠️ Data Error:\n{message}\n\nPlease ensure the required data file(s) are in the\n'{RAW_DATA_DIR}/' folder and the script parameters match the file structure.",
            horizontalalignment='center', verticalalignment='center',
            fontsize=12, color='red', wrap=True)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values(): spine.set_visible(False)
    return fig

@st.cache_data
def plot_1965_food_crisis(): # Placeholder
    return create_error_fig("Plotting for 1965 Food Crisis not yet implemented.")

@st.cache_data
def plot_1973_oil_shock(): # Placeholder
    return create_error_fig("Plotting for 1973/79 Oil Shocks not yet implemented.")

@st.cache_data
def plot_1991_bop_crisis():
    # print("Generating 1991 BoP Crisis plot...")
    df = get_forex_reserves()
    if df is None or 'Forex_USD_Million' not in df.columns: return create_error_fig("Forex data for 1991.")
    if not pd.api.types.is_datetime64_any_dtype(df.index): df.index = pd.to_datetime(df.index, errors='coerce'); df = df.dropna(subset=[df.index.name])
    df_crisis = df.loc['1988-01-01':'1993-01-01']
    if df_crisis.empty: return create_error_fig("No Forex data for 1988-1993.")
    fig, ax = plt.subplots(figsize=(12, 6)); sns.lineplot(x=df_crisis.index, y=df_crisis['Forex_USD_Million'], ax=ax, color='red', linewidth=2)
    crisis_point = pd.to_datetime('1990-08-01'); low_point = pd.to_datetime('1991-06-01')
    crisis_point_num = mdates.date2num(crisis_point); low_point_num = mdates.date2num(low_point)
    ax.axvline(crisis_point_num, color='grey', linestyle='--', lw=1, label='Aug 1990: Gulf War'); ax.axvline(low_point_num, color='gold', linestyle='--', lw=1, label='Jun 1991: Gold Pledged')
    ax.set_title("1991 Balance of Payments Crisis", fontsize=16); ax.set_ylabel("Forex Reserves (USD Million)")
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter('${x:,.0f}M')); ax.legend(); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.setp(ax.get_xticklabels(), rotation=30, ha='right'); plt.tight_layout(); return fig

@st.cache_data
def plot_2008_financial_crisis():
    # print("Generating 2008 Gold vs. Copper plot...")
    df_gold = get_historical_gold_prices(); df_copper = get_mcx_copper()
    if df_gold is None or df_copper is None: return create_error_fig("Gold/Copper data for 2008.")
    if not pd.api.types.is_datetime64_any_dtype(df_gold.index): df_gold.index = pd.to_datetime(df_gold.index, errors='coerce').dropna()
    if not pd.api.types.is_datetime64_any_dtype(df_copper.index): df_copper.index = pd.to_datetime(df_copper.index, errors='coerce').dropna()
    start_date='2007-01-01'; end_date='2011-01-01'; common_index = df_gold.index.intersection(df_copper.index); common_index = common_index[(common_index >= start_date) & (common_index <= end_date)]
    if common_index.empty: return create_error_fig("No overlapping Gold/Copper data for 2007-2011.")
    df_gold_plot = df_gold.loc[common_index]; df_copper_plot = df_copper.loc[common_index]
    fig, ax1 = plt.subplots(figsize=(12, 6)); crisis_point = pd.to_datetime('2008-09-15'); crisis_point_num = mdates.date2num(crisis_point); ax1.axvline(crisis_point_num, color='red', linestyle='--', lw=1, label='Sep 2008: Lehman Collapse')
    sns.lineplot(data=df_gold_plot, x=df_gold_plot.index, y='Price_per_10g_INR', ax=ax1, color='gold', label='Gold (₹/10g)', marker='.', markersize=2, lw=1.5); ax1.set_ylabel("Gold Price", color='gold'); ax1.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))
    ax2 = ax1.twinx(); sns.lineplot(data=df_copper_plot, x=df_copper_plot.index, y='Price_per_kg_INR', ax=ax2, color='brown', label='Copper (₹/kg)', marker='.', markersize=2, lw=1.5); ax2.set_ylabel("Copper Price", color='brown'); ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))
    fig.suptitle("2008 Crisis: Flight to Safety (Gold) vs. Industrial Slowdown (Copper)", fontsize=16); lines1, labels1 = ax1.get_legend_handles_labels(); lines2, labels2 = ax2.get_legend_handles_labels(); ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left'); ax1.set_xlabel("Date")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m')); plt.setp(ax1.get_xticklabels(), rotation=30, ha='right'); plt.tight_layout(rect=[0, 0.03, 1, 0.95]); return fig

@st.cache_data
def plot_2016_demonetisation_shock():
    # print("Generating 2016 Demonetisation plot...")
    df_wpi = get_wpi_data() # Use the general WPI function
    df_gold = get_historical_gold_prices()
    if df_wpi is None or 'WPI_Vegetables' not in df_wpi.columns: return create_error_fig("WPI Vegetable data for 2016.")
    if df_gold is None: return create_error_fig("Gold data for 2016.")
    if not pd.api.types.is_datetime64_any_dtype(df_wpi.index): df_wpi.index = pd.to_datetime(df_wpi.index, errors='coerce').dropna()
    if not pd.api.types.is_datetime64_any_dtype(df_gold.index): df_gold.index = pd.to_datetime(df_gold.index, errors='coerce').dropna()
    start_agri='2016-08-01'; end_agri='2017-02-01'; start_gold='2016-10-01'; end_gold='2017-01-01'
    df_agri_plot = df_wpi.loc[start_agri:end_agri, ['WPI_Vegetables']]; df_gold_plot = df_gold.loc[start_gold:end_gold, ['Price_per_10g_INR']]
    if df_agri_plot.empty or df_gold_plot.empty: return create_error_fig("No Agri/Gold data for 2016-17.")
    fig, ax1 = plt.subplots(figsize=(12, 6)); crisis_point = pd.to_datetime('2016-11-08'); crisis_point_num = mdates.date2num(crisis_point); ax1.axvline(crisis_point_num, color='red', linestyle='--', lw=1, label='Nov 8: Demonetisation')
    sns.lineplot(data=df_agri_plot.dropna(), x=df_agri_plot.dropna().index, y='WPI_Vegetables', ax=ax1, color='green', label='Agri WPI (Index)', marker='o', markersize=4, lw=1.5); ax1.set_ylabel("Vegetable WPI", color='green')
    ax2 = ax1.twinx(); sns.lineplot(data=df_gold_plot.dropna(), x=df_gold_plot.dropna().index, y='Price_per_10g_INR', ax=ax2, color='gold', label='Gold Price (₹/10g)', marker='s', markersize=4, lw=1.5); ax2.set_ylabel("Gold Price", color='gold'); ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))
    fig.suptitle("2016 Demonetisation: Liquidity Crash (Agri) vs. Panic Spike (Gold)", fontsize=16); lines1, labels1 = ax1.get_legend_handles_labels(); lines2, labels2 = ax2.get_legend_handles_labels(); ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left'); ax1.set_xlabel("Date")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m')); plt.setp(ax1.get_xticklabels(), rotation=30, ha='right'); plt.tight_layout(rect=[0, 0.03, 1, 0.95]); return fig

@st.cache_data
def plot_2020_covid_oil_crash(): # Placeholder
    return create_error_fig("Plotting for 2020 COVID Oil Crash not yet implemented.")

@st.cache_data
def plot_2022_oil_shock():
    # print("Generating 2022 Oil Shock plot...")
    df = get_oil_petrol_inr_data()
    required_cols = ['Brent_in_INR', 'Petrol_Delhi']
    if df is None or not all(col in df.columns for col in required_cols): return create_error_fig("Oil/Petrol data for 2022.")
    if not pd.api.types.is_datetime64_any_dtype(df.index): df.index = pd.to_datetime(df.index, errors='coerce'); df = df.dropna(subset=[df.index.name])
    df_crisis = df.loc['2021-11-01':'2022-08-01'].copy()
    if df_crisis.empty: return create_error_fig("No Oil/Petrol data for 2021-11 to 2022-08.")
    window_size = 20; df_crisis['Brent_in_INR'] = pd.to_numeric(df_crisis['Brent_in_INR'], errors='coerce'); df_crisis['Petrol_Delhi'] = pd.to_numeric(df_crisis['Petrol_Delhi'], errors='coerce'); df_crisis.dropna(subset=['Brent_in_INR', 'Petrol_Delhi'], inplace=True)
    correlation_calculated = False
    if len(df_crisis) >= window_size:
         df_crisis['Correlation'] = df_crisis['Brent_in_INR'].rolling(window_size, min_periods=window_size).corr(df_crisis['Petrol_Delhi'])
         fig, (ax1, ax3) = plt.subplots(nrows=2, figsize=(12, 9), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
         correlation_calculated = True
    else: fig, ax1 = plt.subplots(figsize=(12, 6))
    crisis_point = pd.to_datetime('2022-02-24'); crisis_point_num = mdates.date2num(crisis_point)
    ax1.axvline(crisis_point_num, color='red', linestyle='--', lw=1, label='Feb 2022: Ukraine War')
    sns.lineplot(data=df_crisis, x=df_crisis.index, y='Brent_in_INR', ax=ax1, color='green', label='Brent Crude (₹/Barrel)', marker='.', markersize=2, lw=1.5); ax1.set_ylabel("Crude Price", color='green'); ax1.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))
    ax2 = ax1.twinx(); sns.lineplot(data=df_crisis, x=df_crisis.index, y='Petrol_Delhi', ax=ax2, color='purple', label='Retail Petrol (₹/Litre)', marker='.', markersize=2, lw=1.5); ax2.set_ylabel("Petrol Price", color='purple'); ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))
    fig.suptitle("2022 Oil Shock: Global vs. Retail Price Pass-Through", fontsize=16); lines1, labels1 = ax1.get_legend_handles_labels(); lines2, labels2 = ax2.get_legend_handles_labels(); ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    if correlation_calculated:
        sns.lineplot(data=df_crisis, x=df_crisis.index, y='Correlation', ax=ax3, color='black', label=f'{window_size}-period Rolling Correlation'); ax3.set_ylabel("Correlation"); ax3.set_ylim(-1.1, 1.1)
        ax3.axhline(1, color='grey', linestyle=':', lw=0.5); ax3.axhline(0, color='grey', linestyle=':', lw=0.5); ax3.axhline(-1, color='grey', linestyle=':', lw=0.5); ax3.legend(loc='lower left'); ax3.set_xlabel("Date")
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d')); plt.setp(ax3.get_xticklabels(), rotation=30, ha='right')
    else:
        ax1.set_xlabel("Date"); ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d')); plt.setp(ax1.get_xticklabels(), rotation=30, ha='right')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95]); return fig


# ==============================================================================
# --- PART 3: INTERACTIVE APP (STREAMLIT UI) ---
# ==============================================================================

# --- Page Config ---
st.set_page_config(page_title="India's Commodity Story", page_icon="🇮🇳", layout="wide")

# --- Title & Abstract ---
st.title("🇮🇳 From Control to Crisis: India's Commodity Story (1947-Present)")
st.markdown("""
_An analysis by KD, assisted by Friday._

This interactive application explores how the impact of global and domestic crises on **Indian commodity prices** has fundamentally changed over time. We examine two distinct eras:

1.  **The 'Controlled' Era (1947-1991):** Government-set prices meant crises often led to **national-level shortages, rationing, and foreign exchange emergencies**, forcing major policy shifts like the Green Revolution or the 1991 liberalization.
2.  **The 'Market' Era (1991-Present):** Post-liberalization, prices became increasingly linked to global markets. Crises now trigger more immediate **price volatility impacting consumers and businesses directly**, with government policy acting as a reaction or buffer.

Use the tabs below to explore key case studies from each era.
""")
st.markdown("---")

# --- Run Setup ---
setup_directories() # Ensure directories exist before data loading attempt

# --- Main Tabs ---
tab_controlled, tab_market, tab_domestic, tab_conclusion = st.tabs([
    "📉 Controlled Era (1947-1991)",
    "📈 Market Era (1991-Present)",
    "🏠 Domestic Shocks",
    "สรุป Conclusion"
])

# --- TAB 1: CONTROLLED ERA ---
with tab_controlled:
    st.header("Global Crises: The 'Controlled' Era (1947-1991)")
    st.info("Prices fixed by government; crises hit national finances & supply.")

    # --- 1965 Food Crisis ---
    st.subheader("🌾 Case Study: 1965-66 Drought & War (Food Crisis)")
    with st.expander("Click to read analysis"): st.write("...") # Analysis
    with st.spinner("Generating 1965 Food Crisis plot..."):
        fig_65 = plot_1965_food_crisis() # Placeholder
        if isinstance(fig_65, plt.Figure): st.pyplot(fig_65); st.caption("...") # Sources
        else: st.warning("Plotting for 1965 Food Crisis is not yet implemented.")
    st.divider()

    # --- 1973/79 Oil Shocks ---
    st.subheader("⛽ Case Study: 1973 & 1979 Oil Shocks (Energy & Forex Crisis)")
    with st.expander("Click to read analysis"): st.write("...") # Analysis
    with st.spinner("Generating 1973/79 Oil Shocks plot..."):
        fig_73 = plot_1973_oil_shock() # Placeholder
        if isinstance(fig_73, plt.Figure): st.pyplot(fig_73); st.caption("...") # Sources
        else: st.warning("Plotting for 1973/79 Oil Shocks is not yet implemented.")
    st.divider()

    # --- 1991 BoP Crisis ---
    st.subheader("📉 Case Study: 1990-91 Gulf War (The Final BoP Crisis)")
    with st.expander("Click to read analysis"): st.write("...") # Analysis
    with st.spinner("Generating 1991 BoP Crisis plot..."):
        fig_91 = plot_1991_bop_crisis()
        if isinstance(fig_91, plt.Figure): st.pyplot(fig_91); st.caption("Data Source: Reserve Bank of India (RBI)")
        else: st.error("Could not generate 1991 BoP plot. Check data availability.")

# --- TAB 2: MARKET ERA ---
with tab_market:
    st.header("Global Crises: The 'Market' Era (1991-Present)")
    st.info("Prices increasingly market-linked; crises cause direct volatility.")

    # --- 2008 Financial Crisis ---
    st.subheader("🏦 Case Study: 2008 Global Financial Crisis")
    with st.expander("Click to read analysis"): st.write("...") # Analysis
    with st.spinner("Generating 2008 Crisis plot..."):
        fig_08 = plot_2008_financial_crisis()
        if isinstance(fig_08, plt.Figure): st.pyplot(fig_08); st.caption("Data Sources: MCX/Market (Copper), RBI/Market (Gold)")
        else: st.error("Could not generate 2008 Crisis plot. Check data availability.")
    st.divider()

    # --- 2020 COVID Oil Crash ---
    st.subheader("🛢️ Case Study: 2020 COVID-19 Pandemic (Oil Demand Collapse)")
    with st.expander("Click to read analysis"): st.write("...") # Analysis
    with st.spinner("Generating 2020 COVID Oil Crash plot..."):
        fig_20 = plot_2020_covid_oil_crash() # Placeholder
        if isinstance(fig_20, plt.Figure): st.pyplot(fig_20); st.caption("...") # Sources
        else: st.warning("Plotting for 2020 COVID Oil Crash is not yet implemented.")
    st.divider()

    # --- 2022 Ukraine War ---
    st.subheader("🌍 Case Study: 2022 Russia-Ukraine War (Energy & Food Shock)")
    with st.expander("Click to read analysis"): st.write("...") # Analysis
    with st.spinner("Generating 2022 Oil Shock plot..."):
        fig_22 = plot_2022_oil_shock()
        if isinstance(fig_22, plt.Figure): st.pyplot(fig_22); st.caption("Data Sources: EIA/Market (Brent), RBI (INR), PPAC (Petrol)")
        else: st.error("Could not generate 2022 Oil Shock plot. Check data availability.")

# --- TAB 3: DOMESTIC SHOCKS ---
with tab_domestic:
    st.header("Domestic Shocks: Policy & Liquidity")
    st.info("Impact of internal policy decisions on commodity markets.")

    # --- 2016 Demonetisation ---
    st.subheader("💸 Case Study: 2016 Demonetisation")
    with st.expander("Click to read analysis"): st.write("...") # Analysis
    with st.spinner("Generating 2016 Demonetisation plot..."):
        fig_16 = plot_2016_demonetisation_shock()
        if isinstance(fig_16, plt.Figure): st.pyplot(fig_16); st.caption("Data Sources: Office of Economic Adviser (WPI), RBI/Market (Gold)")
        else: st.error("Could not generate 2016 Demonetisation plot. Check data availability.")

# --- TAB 4: CONCLUSION ---
with tab_conclusion:
    st.header("สรุป Conclusion: Two Eras of Impact")
    st.markdown("""
    This analysis demonstrates a clear shift in how India experiences commodity price shocks:

    * **Pre-1991 (Controlled Era):** Global crises primarily manifested as **macroeconomic instability** (forex drains, deficits) and **physical supply risks** (shortages), met with major **structural policy responses** (Green Revolution, MSP, eventual Liberalization). The direct price impact on consumers was often delayed or muted by government controls (APM).

    * **Post-1991 (Market Era):** Global and domestic crises now translate much more directly into **market price volatility** (spikes and crashes) visible on exchanges and at the retail level. Government policy still plays a role (taxes, export bans, subsidies), but often acts as a **reactive buffer or mediator** rather than the primary price setter. Market integration brings efficiency but also direct exposure to global shocks.

    Understanding this evolution is crucial for predicting the impact of future crises and for designing effective policy responses in today's interconnected Indian economy. 🇮🇳
    """)
    st.success("Project structure complete. Implement remaining plots and refine data loading for full functionality.")

# --- Sidebar "About" Section ---
st.sidebar.title("About")
st.sidebar.info(...) # About text remains same

# --- Optional: Show Raw Data Sample in Sidebar ---
# (Sidebar data display code remains the same as v3.0)
if st.sidebar.checkbox("Show Sample Loaded Data"):
    st.sidebar.markdown("*(Displaying first 3 rows of currently loaded data)*")
    data_functions = {
        "Forex Reserves": get_forex_reserves,
        "Gold Prices": get_historical_gold_prices,
        "Copper Prices": get_mcx_copper,
        "Oil/Petrol/INR": get_oil_petrol_inr_data,
        "WPI Data": get_wpi_data # Includes Veg WPI if available
    }
    for name, func in data_functions.items():
        try:
            st.sidebar.subheader(name)
            df_sample = func()
            if df_sample is not None:
                st.sidebar.dataframe(df_sample.head(3))
            else:
                st.sidebar.warning(f"{name} data unavailable.")
        except Exception as e:
            st.sidebar.error(f"Error loading {name} sample: {e}")
