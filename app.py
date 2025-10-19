"""
Complete Project: India's Commodity Price History (All-in-One)

V2.0: Refactored for REAL DATA loading.
      - Removes mock data generation.
      - Prioritizes reading local files from the 'data/' folder.
      - Includes direct URL example for WPI.
      - Requires user to download files and adapt cleaning steps.

This single file contains all three parts of the project:
1.  Part 1: Data Pipeline (Real data loading and cleaning)
2.  Part 2: Analysis Engine (Plotting functions)
3.  Part 3: Interactive App (Streamlit UI)

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
sns.set_style("darkgrid")

# ==============================================================================
# --- PART 1: DATA PIPELINE (HELPER FUNCTIONS) ---
# ==============================================================================

def setup_directories():
    """Creates 'clean_data' and 'data' directories if they don't exist."""
    for dir_path in [CLEAN_DATA_DIR, RAW_DATA_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")

@st.cache_data # Cache the results of data loading and cleaning
def load_and_clean_data(clean_file, source_info):
    """
    Main data loading function.
    Tries to load clean CSV. If not found, attempts to load and clean
    raw data based on source_info.

    Args:
        clean_file (str): Name for the cleaned CSV output file.
        source_info (dict): Information about the raw data source.
            Expected keys:
            - 'type': 'local_excel', 'local_csv', 'url_csv', 'url_excel', 'multi_local_csv'
            - 'path'/'url': File path or URL (list for multi_local_csv).
            - 'skiprows': (Optional) Number of rows to skip. Default 0.
            - 'sheet_name': (Optional) For Excel files. Default 0 (first sheet).
            - 'date_col': Name of the date column in the raw data.
            - 'value_cols': List of value column names in the raw data.
            - 'new_names': List of new names for the value columns.
            - 'date_format': (Optional) String format for pd.to_datetime.
    Returns:
        pd.DataFrame or None: Cleaned DataFrame or None if loading fails.
    """
    clean_file_path = os.path.join(CLEAN_DATA_DIR, clean_file)

    if os.path.exists(clean_file_path):
        try:
            print(f"Loading cached data: {clean_file}")
            df = pd.read_csv(clean_file_path, parse_dates=True, index_col='Date')
            if df.empty:
                print(f"WARNING: Clean file {clean_file} is empty. Re-processing...")
                os.remove(clean_file_path)
                # Re-run after removing empty file
                st.rerun() # Use Streamlit's rerun mechanism
            return df
        except EmptyDataError:
            print(f"ERROR: {clean_file} is empty. Deleting and re-processing...")
            os.remove(clean_file_path)
            st.rerun() # Use Streamlit's rerun mechanism
        except Exception as e:
             print(f"Error reading cached file {clean_file}: {e}. Re-processing...")
             try:
                 os.remove(clean_file_path)
             except OSError:
                 pass
             st.rerun()


    # --- If clean file doesn't exist or was invalid, process raw data ---
    print(f"Processing raw data for: {clean_file}")
    df_raw = None
    source_type = source_info.get('type')
    path_or_url = source_info.get('path') or source_info.get('url')
    skiprows = source_info.get('skiprows', 0)
    sheet_name = source_info.get('sheet_name', 0)

    try:
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
        # Add 'multi_local_csv' or other types if needed later
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

        # --- Basic Cleaning ---
        # Rename columns
        rename_dict = {source_info['date_col']: 'Date_Str'}
        for old, new in zip(source_info['value_cols'], source_info['new_names']):
            rename_dict[old] = new
        df_raw = df_raw.rename(columns=rename_dict)

        # Convert date
        date_format = source_info.get('date_format')
        df_raw['Date'] = pd.to_datetime(df_raw['Date_Str'], format=date_format, errors='coerce')
        df_raw.dropna(subset=['Date'], inplace=True) # Drop rows where date conversion failed

        # Select columns and convert values to numeric
        final_cols = ['Date'] + source_info['new_names']
        df_clean = df_raw[final_cols].copy() # Use copy to avoid SettingWithCopyWarning
        for col in source_info['new_names']:
            # Attempt to clean common non-numeric chars before converting
            if df_clean[col].dtype == 'object': # Only clean if it's string-like
                 df_clean[col] = df_clean[col].astype(str).str.replace(r'[₹,NA\-]', '', regex=True)
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

        df_clean = df_clean.set_index('Date').dropna() # Drop rows with any NaN values

        if df_clean.empty:
            print(f"ERROR: No valid data found after cleaning raw source for {clean_file}")
            st.error(f"Failed to process data for {clean_file}. No valid data found. Check raw file and cleaning parameters.")
            return None

        df_clean.to_csv(clean_file_path)
        print(f"Clean data saved to {clean_file_path}")
        return df_clean

    except FileNotFoundError as e:
        print(f"ERROR: Raw file not found: {e}")
        st.error(f"Data file not found: {os.path.basename(str(e))}. Please download it to the '{RAW_DATA_DIR}/' folder.")
        return None
    except EmptyDataError:
        print(f"ERROR: Raw file for {clean_file} is empty.")
        st.error(f"Raw data file for {clean_file} is empty.")
        return None
    except KeyError as e:
         print(f"ERROR: Column not found during cleaning for {clean_file}: {e}. Check 'date_col' or 'value_cols'.")
         st.error(f"Column '{e}' not found in the raw data for {clean_file}. Please check the file structure and update the script.")
         return None
    except Exception as e:
        print(f"ERROR: Failed to load/clean data for {clean_file}: {e}")
        st.error(f"An unexpected error occurred while processing data for {clean_file}: {e}")
        return None

# --- Specific Data Getters ---
# You MUST adapt the 'source_info' dictionaries below based on your actual files!

def get_wpi_data():
    # Example using direct URL - Check if this URL is still valid
    source_info = {
        'type': 'url_csv',
        'url': "https://data.gov.in/files/ogdpv2dms/s3fs-public/Wholesale_Price_Index__WPI___New_Series__2011-12__Monthly_1_0_0.csv",
        'date_col': 'Month-Year',
        'value_cols': ['Food Articles', 'Fuel & Power', 'Manufactured Products', 'Vegetables'], # Added Vegetables
        'new_names': ['WPI_Food', 'WPI_Fuel', 'WPI_Manuf', 'WPI_Vegetables'],
        'date_format': '%b-%y'
    }
    return load_and_clean_data('clean_wpi_2011_present.csv', source_info)

def get_forex_reserves():
    # Example for local Excel file from RBI
    source_info = {
        'type': 'local_excel',
        'path': 'RBI_Forex_Reserves_Historical.xlsx', # UPDATE FILENAME
        'skiprows': 5, # UPDATE SKIPROWS
        'sheet_name': 'Monthly Data', # UPDATE SHEET NAME
        'date_col': 'Month / Year', # UPDATE DATE COL NAME
        'value_cols': ['Total Reserves (USD Million)'], # UPDATE VALUE COL NAME
        'new_names': ['Forex_USD_Million'],
        'date_format': '%Y %b' # UPDATE DATE FORMAT
    }
    return load_and_clean_data('clean_forex_reserves.csv', source_info)

def get_historical_gold_prices():
    # Example for local CSV (e.g., copied from a website)
    source_info = {
        'type': 'local_csv',
        'path': 'Gold_INR_1947_Present.csv', # UPDATE FILENAME
        'date_col': 'Year', # UPDATE DATE COL NAME
        'value_cols': ['Price_per_10g_INR'], # UPDATE VALUE COL NAME
        'new_names': ['Price_per_10g_INR'],
        'date_format': '%Y' # UPDATE DATE FORMAT
    }
    return load_and_clean_data('clean_gold_prices.csv', source_info)

def get_mcx_copper():
     # Example for local CSV downloaded from MCX/financial site
    source_info = {
        'type': 'local_csv',
        'path': 'MCX_Copper_Futures_Daily.csv', # UPDATE FILENAME
        'date_col': 'Date', # UPDATE DATE COL NAME
        'value_cols': ['Close'], # UPDATE VALUE COL NAME (usually 'Close')
        'new_names': ['Price_per_kg_INR'], # Name it appropriately
        # Date format often standard like YYYY-MM-DD, pandas might detect automatically
    }
    return load_and_clean_data('clean_mcx_copper.csv', source_info)

@st.cache_data
def get_oil_petrol_inr_data():
    """
    Loads and merges Brent(USD), USD/INR, and Petrol(INR) data.
    Requires three separate local files. Bypasses the main helper.
    """
    clean_file_path = os.path.join(CLEAN_DATA_DIR, 'clean_oil_petrol_inr.csv')
    # --- UPDATE THESE FILENAMES ---
    raw_oil_path = os.path.join(RAW_DATA_DIR, 'global_brent_usd_daily.csv')
    raw_inr_path = os.path.join(RAW_DATA_DIR, 'rbi_usd_inr_daily.csv')
    raw_petrol_path = os.path.join(RAW_DATA_DIR, 'ppac_petrol_delhi_daily.csv')

    if os.path.exists(clean_file_path):
        try:
            print("Loading cached Oil/Petrol/INR data...")
            df = pd.read_csv(clean_file_path, parse_dates=True, index_col='Date')
            if df.empty : raise EmptyDataError
            return df
        except (EmptyDataError, Exception) as e:
            print(f"Error reading or empty cached Oil/Petrol/INR file: {e}. Re-processing...")
            if os.path.exists(clean_file_path): os.remove(clean_file_path)
            # Continue to raw processing logic
    # --- If cache miss or error, process raw ---
    try:
        print(f"Processing raw files: Oil, INR, Petrol")
        # --- Load Brent Oil Data (USD) ---
        # UPDATE skiprows, date_col, value_cols based on your file
        df_oil = pd.read_csv(raw_oil_path, skiprows=0)
        df_oil = df_oil.rename(columns={'Date': 'Date_Str', 'Price': 'Brent_USD'}) # ADAPT
        df_oil['Date'] = pd.to_datetime(df_oil['Date_Str'], errors='coerce') # ADAPT format if needed
        df_oil = df_oil[['Date', 'Brent_USD']].dropna(subset=['Date'])
        df_oil['Brent_USD'] = pd.to_numeric(df_oil['Brent_USD'], errors='coerce')

        # --- Load INR Data (USD to INR rate) ---
        # UPDATE skiprows, date_col, value_cols based on your file
        df_inr = pd.read_csv(raw_inr_path, skiprows=0)
        df_inr = df_inr.rename(columns={'Date': 'Date_Str', 'Value': 'USD_INR'}) # ADAPT
        df_inr['Date'] = pd.to_datetime(df_inr['Date_Str'], errors='coerce') # ADAPT format if needed
        df_inr = df_inr[['Date', 'USD_INR']].dropna(subset=['Date'])
        df_inr['USD_INR'] = pd.to_numeric(df_inr['USD_INR'], errors='coerce')

        # --- Load Petrol Data (INR per Litre) ---
        # UPDATE skiprows, date_col, value_cols based on your file
        df_petrol = pd.read_csv(raw_petrol_path, skiprows=0)
        df_petrol = df_petrol.rename(columns={'Date': 'Date_Str', 'Delhi_Price': 'Petrol_Delhi'}) # ADAPT
        df_petrol['Date'] = pd.to_datetime(df_petrol['Date_Str'], errors='coerce') # ADAPT format if needed
        df_petrol = df_petrol[['Date', 'Petrol_Delhi']].dropna(subset=['Date'])
        df_petrol['Petrol_Delhi'] = pd.to_numeric(df_petrol['Petrol_Delhi'], errors='coerce')

        # --- Merge Data ---
        df_merged = pd.merge(df_oil, df_inr, on='Date', how='inner')
        df_merged = pd.merge(df_merged, df_petrol, on='Date', how='inner')

        # --- Calculate Brent in INR ---
        df_merged['Brent_in_INR'] = df_merged['Brent_USD'] * df_merged['USD_INR']

        # --- Final Clean and Save ---
        df_clean = df_merged.set_index('Date').dropna()

        if df_clean.empty:
            st.error("Merging Oil/Petrol/INR failed - no overlapping dates or data invalid.")
            return None

        df_clean.to_csv(clean_file_path)
        print(f"Clean Oil/Petrol/INR data saved to {clean_file_path}")
        return df_clean

    except FileNotFoundError as e:
        st.error(f"Raw data file not found for Oil/Petrol/INR analysis: {e}. Please download all required files to '{RAW_DATA_DIR}/'.")
        return None
    except EmptyDataError as e:
        st.error(f"Raw file is empty: {getattr(e, 'filename', 'Unknown')}. Cannot proceed.")
        return None
    except KeyError as e:
        st.error(f"Column '{e}' not found in one of the Oil/Petrol/INR files. Please check file structures and update column names in the script.")
        return None
    except Exception as e:
        st.error(f"Failed to process Oil/Petrol/INR data: {e}")
        return None


# ==============================================================================
# --- PART 2: ANALYSIS & VISUALIZATION FUNCTIONS ---
# ==============================================================================

@st.cache_data
def plot_1991_bop_crisis():
    # ... (Plotting code remains the same as v1.3) ...
    print("Generating 1991 BoP Crisis plot...")
    df = get_forex_reserves()

    if df is None or 'Forex_USD_Million' not in df.columns:
        return create_error_fig("Forex data not found or column mismatch.")

    if not pd.api.types.is_datetime64_any_dtype(df.index):
        df.index = pd.to_datetime(df.index, errors='coerce')
        df = df.dropna(subset=[df.index.name])

    df_crisis = df.loc['1988-01-01':'1993-01-01']
    if df_crisis.empty:
        return create_error_fig("No Forex data available for 1988-1993.")

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.lineplot(x=df_crisis.index, y=df_crisis['Forex_USD_Million'], ax=ax, color='red', linewidth=2.5)

    crisis_point = pd.to_datetime('1990-08-01')
    low_point = pd.to_datetime('1991-06-01')
    crisis_point_num = mdates.date2num(crisis_point)
    low_point_num = mdates.date2num(low_point)

    ax.axvline(crisis_point_num, color='black', linestyle='--', label='1990 Gulf War (Oil Spike)')
    ax.axvline(low_point_num, color='gold', linestyle='--', label='1991 India Pledges Gold')

    ax.set_title("The 1991 Balance of Payments Crisis", fontsize=18)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Foreign Exchange Reserves (in Million USD)", fontsize=12)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter('${x:,.0f}M'))
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
    plt.tight_layout()
    return fig


@st.cache_data
def plot_2008_financial_crisis():
    # ... (Plotting code remains the same as v1.3) ...
    print("Generating 2008 Gold vs. Copper plot...")
    df_gold = get_historical_gold_prices()
    df_copper = get_mcx_copper()

    if df_gold is None or 'Price_per_10g_INR' not in df_gold.columns:
        return create_error_fig("Gold data not found or column mismatch.")
    if df_copper is None or 'Price_per_kg_INR' not in df_copper.columns:
        return create_error_fig("Copper data not found or column mismatch.")

    if not pd.api.types.is_datetime64_any_dtype(df_gold.index):
        df_gold.index = pd.to_datetime(df_gold.index, errors='coerce').dropna()
    if not pd.api.types.is_datetime64_any_dtype(df_copper.index):
        df_copper.index = pd.to_datetime(df_copper.index, errors='coerce').dropna()

    start_date = '2007-01-01'
    end_date = '2011-01-01'
    common_index = df_gold.index.intersection(df_copper.index)
    common_index = common_index[(common_index >= start_date) & (common_index <= end_date)]

    if common_index.empty:
        return create_error_fig("No overlapping Gold/Copper data for 2007-2011.")

    df_gold_plot = df_gold.loc[common_index]
    df_copper_plot = df_copper.loc[common_index]

    fig, ax1 = plt.subplots(figsize=(12, 7))

    crisis_point = pd.to_datetime('2008-09-15')
    crisis_point_num = mdates.date2num(crisis_point)
    ax1.axvline(crisis_point_num, color='red', linestyle='--', label='2008 Financial Crisis')

    sns.lineplot(data=df_gold_plot, x=df_gold_plot.index, y='Price_per_10g_INR', ax=ax1, color='gold', label='Gold (Safe Haven)', marker='.')
    ax1.set_xlabel("Date", fontsize=12)
    ax1.set_ylabel("Gold Price (₹ per 10g)", fontsize=12, color='gold')
    ax1.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))

    ax2 = ax1.twinx()
    sns.lineplot(data=df_copper_plot, x=df_copper_plot.index, y='Price_per_kg_INR', ax=ax2, color='brown', label='Copper (Industrial)', marker='.')
    ax2.set_ylabel("Copper Price (₹ per kg)", fontsize=12, color='brown')
    ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))

    fig.suptitle("2008 Crisis: Gold (Safe Haven) vs. Copper (Industrial)", fontsize=18)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', bbox_to_anchor=(0.1, 0.9))

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.setp(ax1.get_xticklabels(), rotation=30, ha='right')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig


@st.cache_data
def plot_2016_demonetisation_shock():
    print("Generating 2016 Demonetisation plot...")
    # Use the general WPI loader for vegetables
    df_wpi = get_wpi_data() # Ensure get_wpi_data loads 'WPI_Vegetables'
    df_gold = get_historical_gold_prices()

    if df_wpi is None or 'WPI_Vegetables' not in df_wpi.columns:
         # Try loading specifically if the general one failed or lacked the column
         df_agri = load_and_clean_data(
             'clean_agri_wpi.csv',
             {'type': 'local_csv', 'path': 'wpi_vegetables.csv', # UPDATE FILENAME
              'date_col': 'Month-Year', 'value_cols': ['Vegetables'], # ADAPT
              'new_names': ['WPI_Vegetables'], 'date_format': '%b-%y'}, # ADAPT
             None # No mock func here, rely on main function error handling
         )
         if df_agri is None: return create_error_fig("Agri WPI data not found or column mismatch.")
    else:
        df_agri = df_wpi[['WPI_Vegetables']].copy() # Extract from general WPI df


    if df_gold is None or 'Price_per_10g_INR' not in df_gold.columns:
        return create_error_fig("Gold data not found or column mismatch.")

    # Ensure indices are datetime
    if not pd.api.types.is_datetime64_any_dtype(df_agri.index):
        df_agri.index = pd.to_datetime(df_agri.index, errors='coerce').dropna()
    if not pd.api.types.is_datetime64_any_dtype(df_gold.index):
        df_gold.index = pd.to_datetime(df_gold.index, errors='coerce').dropna()

    # Define plot range
    start_date_agri = '2016-08-01'
    end_date_agri = '2017-02-01'
    start_date_gold = '2016-10-01' # Gold data might start later
    end_date_gold = '2017-01-01'

    df_agri_plot = df_agri.loc[start_date_agri:end_date_agri]
    df_gold_plot = df_gold.loc[start_date_gold:end_date_gold]

    # Use intersection of available dates within the range
    common_index = df_agri_plot.index.intersection(df_gold_plot.index)

    # For plotting lines over full range, reindex before plotting
    plot_index = pd.date_range(min(start_date_agri, start_date_gold), max(end_date_agri, end_date_gold), freq='MS')
    df_agri_plot = df_agri_plot.reindex(plot_index) # Let NaNs appear where data is missing
    df_gold_plot = df_gold_plot.reindex(plot_index)

    if df_agri_plot.empty and df_gold_plot.empty: # Check if BOTH are empty over the range
         return create_error_fig("No Agri/Gold data for 2016-2017 plot range.")


    fig, ax1 = plt.subplots(figsize=(12, 7))

    crisis_point = pd.to_datetime('2016-11-08')
    crisis_point_num = mdates.date2num(crisis_point)
    ax1.axvline(crisis_point_num, color='red', linestyle='--', label='Demonetisation (Nov 8)')

    # Axis 1: Agri WPI - plot only where data is not NaN
    sns.lineplot(data=df_agri_plot.dropna(), x=df_agri_plot.dropna().index, y='WPI_Vegetables', ax=ax1, color='green', label='Agri WPI (Cash Market)', marker='o')
    ax1.set_xlabel("Date", fontsize=12)
    ax1.set_ylabel("Vegetable WPI (Index)", fontsize=12, color='green')

    # Axis 2: Gold - plot only where data is not NaN
    ax2 = ax1.twinx()
    sns.lineplot(data=df_gold_plot.dropna(), x=df_gold_plot.dropna().index, y='Price_per_10g_INR', ax=ax2, color='gold', label='Gold Price (Store of Value)', marker='s')
    ax2.set_ylabel("Gold Price (₹ per 10g)", fontsize=12, color='gold')
    ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))


    fig.suptitle("2016 Demonetisation: Agri (Liquidity Crash) vs. Gold (Panic Spike)", fontsize=16)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', bbox_to_anchor=(0.1, 0.9))

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.setp(ax1.get_xticklabels(), rotation=30, ha='right')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig


@st.cache_data
def plot_2022_oil_shock():
    # ... (Plotting code remains the same as v1.3) ...
    print("Generating 2022 Oil Shock plot...")
    df = get_oil_petrol_inr_data()

    required_cols = ['Brent_in_INR', 'Petrol_Delhi']
    if df is None or not all(col in df.columns for col in required_cols):
        return create_error_fig("Oil/Petrol data not found or column mismatch (needs 'Brent_in_INR', 'Petrol_Delhi').")

    if not pd.api.types.is_datetime64_any_dtype(df.index):
        df.index = pd.to_datetime(df.index, errors='coerce')
        df = df.dropna(subset=[df.index.name])

    df_crisis = df.loc['2021-12-01':'2022-07-01'].copy()
    if df_crisis.empty:
        return create_error_fig("No Oil/Petrol data available for 2021-12 to 2022-07.")

    window_size = 20 # More appropriate for potentially daily data
    df_crisis['Brent_in_INR'] = pd.to_numeric(df_crisis['Brent_in_INR'], errors='coerce')
    df_crisis['Petrol_Delhi'] = pd.to_numeric(df_crisis['Petrol_Delhi'], errors='coerce')
    df_crisis.dropna(subset=['Brent_in_INR', 'Petrol_Delhi'], inplace=True)

    correlation_calculated = False
    if len(df_crisis) >= window_size:
         # Use min_periods=window_size to avoid partial calculations at start
         df_crisis['Correlation'] = df_crisis['Brent_in_INR'].rolling(window_size, min_periods=window_size).corr(df_crisis['Petrol_Delhi'])
         fig, (ax1, ax3) = plt.subplots(nrows=2, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
         correlation_calculated = True
    else:
         print(f"Warning: Not enough data points ({len(df_crisis)}) for rolling correlation window ({window_size}). Skipping correlation plot.")
         fig, ax1 = plt.subplots(figsize=(12, 7))


    crisis_point = pd.to_datetime('2022-02-24')
    crisis_point_num = mdates.date2num(crisis_point)
    ax1.axvline(crisis_point_num, color='red', linestyle='--', label='Russia-Ukraine War')

    sns.lineplot(data=df_crisis, x=df_crisis.index, y='Brent_in_INR', ax=ax1, color='green', label='Brent Crude (in ₹)', marker='.')
    ax1.set_ylabel("Crude Price (₹ per Barrel)", fontsize=12, color='green')
    ax1.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))

    ax2 = ax1.twinx()
    sns.lineplot(data=df_crisis, x=df_crisis.index, y='Petrol_Delhi', ax=ax2, color='purple', label='Retail Petrol, Delhi (in ₹)', marker='.')
    ax2.set_ylabel("Petrol Price (₹ per Litre)", fontsize=12, color='purple')
    ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))

    fig.suptitle("2022 Oil Shock: Global Price vs. Retail Price", fontsize=18)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', bbox_to_anchor=(0.1, 0.9))

    if correlation_calculated:
        sns.lineplot(data=df_crisis, x=df_crisis.index, y='Correlation', ax=ax3, color='black', label=f'{window_size}-period Rolling Correlation')
        ax3.set_ylabel("Correlation Coefficient")
        ax3.set_ylim(-1.1, 1.1)
        ax3.axhline(1, color='grey', linestyle=':')
        ax3.axhline(0, color='grey', linestyle=':')
        ax3.axhline(-1, color='grey', linestyle=':')
        ax3.legend()
        ax3.set_xlabel("Date", fontsize=12)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
    else:
        ax1.set_xlabel("Date", fontsize=12)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig


def create_error_fig(message):
    """Returns a matplotlib figure with an error message."""
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.text(0.5, 0.5, f"Data Error: {message}\n\nPlease check the required files in the '{RAW_DATA_DIR}/' folder\nand the cleaning parameters in the script.",
            horizontalalignment='center', verticalalignment='center',
            fontsize=16, color='red', wrap=True)
    return fig

# ==============================================================================
# --- PART 3: INTERACTIVE APP (STREAMLIT UI) ---
# ==============================================================================

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="India's Economic Eras: A Commodity Analysis",
    page_icon="🇮🇳",
    layout="wide"
)

# --- 2. Main Title ---
st.title("From Control to Crisis: India's Commodity Story (1947-Present)")
st.markdown("""
This project analyzes how the impact of global and domestic crises on Indian commodity
prices has fundamentally changed, splitting India's modern history into two distinct eras.
**Note:** This app attempts to load real data files you provide in the 'data/' folder. If files are missing or formats are incorrect, it will display error messages or potentially cached mock data.
""")

# --- Run Setup ---
setup_directories() # Ensure directories exist before data loading attempt

# --- 3. Main Page Navigation (Using Tabs) ---
# ... (UI Code remains the same as v1.3) ...
tab1, tab2, tab3 = st.tabs([
    "Global Crises: The 'Controlled' Era (1947-1991)",
    "Global Crises: The 'Market' Era (1991-Present)",
    "Domestic Shocks: Policy & Liquidity"
])

# --- TAB 1: CONTROLLED ERA ---
with tab1:
    st.header("The 'Controlled' Era (1947-1991)")
    st.markdown("...") # Description

    st.subheader("Case Study: The 1991 Balance of Payments (BoP) Crisis")
    st.write("...") # Analysis text

    with st.spinner("Generating 1991 Crisis plot..."):
        fig1 = plot_1991_bop_crisis()
        if isinstance(fig1, plt.Figure):
             st.pyplot(fig1)
        else:
             st.error("Could not generate 1991 BoP plot.")


# --- TAB 2: MARKET ERA ---
with tab2:
    st.header("The 'Market' Era (1991-Present)")
    st.markdown("...") # Description

    st.subheader("Case Study: The 2008 Global Financial Crisis")
    st.write("...") # Analysis text

    with st.spinner("Generating 2008 Crisis plot..."):
        fig2 = plot_2008_financial_crisis()
        if isinstance(fig2, plt.Figure):
             st.pyplot(fig2)
        else:
             st.error("Could not generate 2008 Crisis plot.")


    st.divider()

    st.subheader("Case Study: The 2022 Russia-Ukraine War")
    st.write("...") # Analysis text

    with st.spinner("Generating 2022 Oil Shock plot..."):
        fig4 = plot_2022_oil_shock()
        if isinstance(fig4, plt.Figure):
            st.pyplot(fig4)
        else:
            st.error("Could not generate 2022 Oil Shock plot.")

# --- TAB 3: DOMESTIC SHOCKS ---
with tab3:
    st.header("Domestic Shocks: Policy & Liquidity")
    st.markdown("...") # Description

    st.subheader("Case Study: The 2016 Demonetisation")
    st.write("...") # Analysis text

    with st.spinner("Generating 2016 Demonetisation plot..."):
        fig3 = plot_2016_demonetisation_shock()
        if isinstance(fig3, plt.Figure):
             st.pyplot(fig3)
        else:
             st.error("Could not generate 2016 Demonetisation plot.")


# --- Sidebar "About" Section ---
st.sidebar.title("About")
st.sidebar.info(
    "This is a project demonstrating the impact of global and domestic crises "
    "on Indian commodity prices from 1947 to the present day. "
    "Built by KD with assistance from Friday."
)

# --- Optional: Show Raw Data Sample in Sidebar ---
# ... (Sidebar data display code remains the same) ...
if st.sidebar.checkbox("Show Sample Data (Attempt Load)"):
    st.sidebar.write("Attempting to load data for display...")
    try:
        st.sidebar.subheader("Forex Reserves")
        df_forex = get_forex_reserves()
        if df_forex is not None:
            st.sidebar.dataframe(df_forex.head(3))
        else:
            st.sidebar.warning("Forex data unavailable.")
    except Exception as e:
        st.sidebar.error(f"Error loading Forex sample: {e}")

    # Add similar try-except blocks for Gold and Agri WPI if needed
    try:
        st.sidebar.subheader("Gold Prices")
        df_gold = get_historical_gold_prices()
        if df_gold is not None:
            st.sidebar.dataframe(df_gold.head(3))
        else:
            st.sidebar.warning("Gold data unavailable.")
    except Exception as e:
        st.sidebar.error(f"Error loading Gold sample: {e}")

    try:
        st.sidebar.subheader("WPI Data (includes Agri)")
        df_wpi = get_wpi_data() # Using the WPI function which loads vegetables
        if df_wpi is not None and 'WPI_Vegetables' in df_wpi.columns:
            st.sidebar.dataframe(df_wpi[['WPI_Vegetables']].head(3))
        elif df_wpi is not None:
             st.sidebar.warning("WPI data loaded, but 'WPI_Vegetables' column missing.")
        else:
            st.sidebar.warning("WPI data unavailable.")
    except Exception as e:
        st.sidebar.error(f"Error loading WPI sample: {e}")
