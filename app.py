"""
Complete Project: India's Commodity Price History (All-in-One)

V1.2: Fixed KeyError: 'file' by handling the multi-file case
      in get_oil_petrol_inr_data directly, bypassing the helper.

This single file contains all three parts of the project:
1.  Part 1: Data Pipeline (Data loading and cleaning functions)
2.  Part 2: Analysis Engine (Plotting functions for case studies)
3.  Part 3: Interactive App (Streamlit web user interface)

To run:
1. Save this file as 'app.py'
2. Install requirements: pip install streamlit pandas matplotlib seaborn openpyxl
3. Run from terminal: streamlit run app.py
"""

# ==============================================================================
# --- IMPORTS ---
# ==============================================================================
import streamlit as st
import pandas as pd
from pandas.errors import EmptyDataError
import os
import io
import openpyxl  # Required for pandas to read .xlsx
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ==============================================================================
# --- GLOBAL SETTINGS ---
# ==============================================================================
CLEAN_DATA_DIR = "clean_data"
RAW_DATA_DIR = "data"
sns.set_style("darkgrid")  # Set plot style globally

# ==============================================================================
# --- PART 1: DATA PIPELINE (HELPER FUNCTIONS) ---
# ==============================================================================

def setup_directories():
    """Creates 'clean_data' and 'data' directories if they don't exist."""
    for dir_path in [CLEAN_DATA_DIR, RAW_DATA_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")

@st.cache_data  # Use Streamlit's cache for data loading
def load_or_create_data(clean_file, raw_file_info, _create_mock_func):
    """
    Helper function: Tries to load clean CSV.
    If fails, it tries to load ONE raw file specified by raw_file_info['file'].
    If that fails, it creates mock data.
    """
    clean_file_path = os.path.join(CLEAN_DATA_DIR, clean_file)

    if os.path.exists(clean_file_path):
        try:
            print(f"Loading cached data: {clean_file}")
            df = pd.read_csv(clean_file_path, parse_dates=True, index_col='Date')
            if df.empty:
                print(f"WARNING: Clean file {clean_file} is empty. Re-processing...")
                os.remove(clean_file_path)
                return load_or_create_data(clean_file, raw_file_info, _create_mock_func)
            return df
        except EmptyDataError:
            print(f"ERROR: {clean_file} is empty. Deleting and re-processing...")
            os.remove(clean_file_path)
            return load_or_create_data(clean_file, raw_file_info, _create_mock_func)
    else:
        # --- Try to load from the single raw file (TEMPLATE) ---
        try:
            # Check if 'file' key exists, otherwise skip to mock
            if 'file' not in raw_file_info:
                 raise FileNotFoundError("Raw file info doesn't contain 'file' key")
                 
            raw_path = os.path.join(RAW_DATA_DIR, raw_file_info['file'])
            if not os.path.exists(raw_path):
                raise FileNotFoundError(f"File not found: {raw_path}")

            print(f"Processing raw file: {raw_path}")
            # --- YOUR REAL DATA LOADING & CLEANING CODE FOR SINGLE FILES ---
            # Determine file type and load accordingly
            skiprows = raw_file_info.get('skiprows', 0) # Use get for optional keys
            if raw_path.endswith('.csv'):
                 df_raw = pd.read_csv(raw_path, skiprows=skiprows)
            elif raw_path.endswith('.xlsx'):
                 df_raw = pd.read_excel(raw_path, skiprows=skiprows)
            else:
                 raise ValueError("Unsupported raw file type")

            # --- Apply cleaning specific to the file type ---
            # This part still needs customization based on the actual file structure
            # Example (you MUST adapt this based on your actual raw files):
            if 'rbi_forex' in raw_file_info['file']:
                 df_raw = df_raw.rename(columns={'Month / Year': 'Date_Str', 'Total Reserves (USD Million)': 'Value'})
                 df_raw['Date'] = pd.to_datetime(df_raw['Date_Str'], format='%Y %b')
                 df_raw['Value'] = pd.to_numeric(df_raw['Value'], errors='coerce')
            elif 'historical_gold' in raw_file_info['file']:
                 df_raw = df_raw.rename(columns={'Year': 'Date_Str', 'Price_per_10g_INR': 'Value'})
                 df_raw['Date'] = pd.to_datetime(df_raw['Date_Str'], format='%Y')
                 df_raw['Value'] = df_raw['Value'].astype(str).str.replace('₹', '').str.replace(',', '')
                 df_raw['Value'] = pd.to_numeric(df_raw['Value'], errors='coerce')
            elif 'mcx_copper' in raw_file_info['file']:
                 df_raw = df_raw.rename(columns={'Date': 'Date_Str', 'Close': 'Value'})
                 df_raw['Date'] = pd.to_datetime(df_raw['Date_Str'])
                 df_raw['Value'] = pd.to_numeric(df_raw['Value'], errors='coerce')
            elif 'wpi_vegetables' in raw_file_info['file']:
                 df_raw = df_raw.rename(columns={'Month-Year': 'Date_Str', 'Vegetables': 'Value'}) # Assuming 'Vegetables' column
                 df_raw['Date'] = pd.to_datetime(df_raw['Date_Str'], format='%b-%y')
                 df_raw['Value'] = pd.to_numeric(df_raw['Value'], errors='coerce')
            else:
                 print(f"Warning: No specific cleaning logic for {raw_file_info['file']}")
                 # Add generic cleaning if needed, or raise error
                 return None # Or handle appropriately

            df_clean = df_raw[['Date', 'Value']].set_index('Date').dropna()

            if df_clean.empty:
                print(f"ERROR: No data found after cleaning raw file: {raw_path}")
                return None

            df_clean.to_csv(clean_file_path)
            print(f"Clean data saved to {clean_file_path}")
            return df_clean

        except (FileNotFoundError, NotImplementedError, KeyError, ValueError) as e:
            print(f"Raw file processing failed for {clean_file}: {e}. Creating mock data.")
            df = _create_mock_func() # Fallback to mock data
            if df is not None:
                df.to_csv(clean_file_path)
                print(f"Clean mock data saved to {clean_file_path}")
            return df
        except Exception as e:
            print(f"An unexpected error occurred processing {raw_file_info.get('file', 'unknown')}: {e}. Creating mock data.")
            df = _create_mock_func() # Fallback to mock data
            if df is not None:
                df.to_csv(clean_file_path)
                print(f"Clean mock data saved to {clean_file_path}")
            return df


# --- Mock Data Creation Functions ---
def create_mock_forex():
    mock_data = """
Date,Value
1988-01-01,5400
1989-01-01,4500
1990-01-01,4000
1990-08-01,2800
1991-01-01,2100
1991-06-01,1100
1991-12-01,3500
1993-01-01,6000
"""
    df = pd.read_csv(io.StringIO(mock_data), parse_dates=True, index_col='Date')
    # Rename 'Value' back to the expected column name for plotting
    df = df.rename(columns={'Value': 'Forex_USD_Million'})
    return df

def create_mock_gold():
    mock_data = """
Date,Value
2007-01-01,10800
2008-01-01,12500
2008-09-15,14500
2009-01-01,15000
2010-01-01,18500
2016-01-01,26000
2016-11-08,30500
2016-11-09,31800
2017-01-01,29000
"""
    df = pd.read_csv(io.StringIO(mock_data), parse_dates=True, index_col='Date')
    df = df.rename(columns={'Value': 'Price_per_10g_INR'})
    return df

def create_mock_copper():
    mock_data = """
Date,Value
2007-01-01,320
2008-01-01,350
2008-09-15,300
2009-01-01,150
2010-01-01,340
2011-01-01,450
"""
    df = pd.read_csv(io.StringIO(mock_data), parse_dates=True, index_col='Date')
    df = df.rename(columns={'Value': 'Price_per_kg_INR'})
    return df

def create_mock_oil_petrol_inr():
    mock_data = """
Date,Brent_USD,USD_INR,Petrol_Delhi
2021-12-01,74.8,75.0,95.4
2022-01-01,86.5,74.5,95.4
2022-02-01,97.1,75.0,95.4
2022-02-24,105.0,75.5,95.4
2022-03-01,117.2,76.0,95.4
2022-03-22,120.0,76.2,96.2
2022-04-01,105.0,76.2,105.4
2022-05-01,113.0,77.0,105.4
2022-06-01,122.7,78.0,105.4
2022-07-01,107.0,79.5,105.4
"""
    df = pd.read_csv(io.StringIO(mock_data), parse_dates=True)
    df['Brent_in_INR'] = df['Brent_USD'] * df['USD_INR']
    df = df.set_index('Date')
    return df

def create_mock_agri_wpi():
    mock_data = """
Date,Value
2016-08-01,120
2016-09-01,115
2016-10-01,110
2016-11-01,100
2016-11-08,98
2016-12-01,80
2017-01-01,75
2017-02-01,78
"""
    df = pd.read_csv(io.StringIO(mock_data), parse_dates=True, index_col='Date')
    df = df.rename(columns={'Value': 'WPI_Vegetables'})
    return df

# --- Part 1: Main Data Function Calls ---
def get_forex_reserves():
    return load_or_create_data(
        'clean_forex_reserves.csv',
        {'file': 'rbi_forex_data.xlsx', 'skiprows': 5},
        create_mock_forex
    )

def get_historical_gold_prices():
    return load_or_create_data(
        'clean_gold_prices.csv',
        {'file': 'historical_gold_inr.csv'},
        create_mock_gold
    )
    
def get_mcx_copper():
    return load_or_create_data(
        'clean_mcx_copper.csv',
        {'file': 'mcx_copper_daily.csv'},
        create_mock_copper
    )

@st.cache_data # Cache this specific function
def get_oil_petrol_inr_data():
    """
    Part 1 function for 2022 Crisis.
    Loads and cleans MCX Crude Oil, USD/INR, and Petrol data.
    Handles multiple raw files directly. Bypasses the helper.
    """
    clean_file_path = os.path.join(CLEAN_DATA_DIR, 'clean_oil_petrol_inr.csv')
    raw_oil_path = os.path.join(RAW_DATA_DIR, 'mcx_oil.csv') # Assumed MCX oil in INR
    raw_inr_path = os.path.join(RAW_DATA_DIR, 'usd_inr_daily.csv') # For context
    raw_petrol_path = os.path.join(RAW_DATA_DIR, 'ppac_petrol_delhi.csv') # Assumed PPAC format

    if os.path.exists(clean_file_path):
        try:
            print("Loading cached Oil/Petrol/INR data...")
            df = pd.read_csv(clean_file_path, parse_dates=True, index_col='Date')
            if df.empty:
                print("WARNING: Clean Oil/Petrol/INR file is empty. Re-processing...")
                os.remove(clean_file_path)
                return get_oil_petrol_inr_data()
            return df
        except EmptyDataError:
            print("ERROR: 'clean_oil_petrol_inr.csv' is empty. Deleting and re-processing...")
            os.remove(clean_file_path)
            return get_oil_petrol_inr_data()
    else:
        # --- Load and process the raw files ---
        try:
            print(f"Processing raw files: {raw_oil_path}, {raw_inr_path}, {raw_petrol_path}")
            
            # 1. Load Oil Data (e.g., MCX Crude Futures in INR)
            df_oil = pd.read_csv(raw_oil_path) # You need to adapt column names
            df_oil['Date'] = pd.to_datetime(df_oil['Date']) # Adapt date column name/format
            df_oil = df_oil.rename(columns={'Close': 'Crude_INR'}) # Adapt Close column name
            df_oil = df_oil[['Date', 'Crude_INR']]

            # 2. Load INR Data (e.g., from RBI)
            df_inr = pd.read_csv(raw_inr_path) # Adapt column names
            df_inr['Date'] = pd.to_datetime(df_inr['Date']) # Adapt date column name/format
            df_inr = df_inr.rename(columns={'Value': 'USD_INR'}) # Adapt Value column name
            df_inr = df_inr[['Date', 'USD_INR']]

            # 3. Load Petrol Data (e.g., from PPAC)
            df_petrol = pd.read_csv(raw_petrol_path) # Adapt column names
            df_petrol['Date'] = pd.to_datetime(df_petrol['Date']) # Adapt date column name/format
            df_petrol = df_petrol.rename(columns={'Delhi_Price': 'Petrol_Delhi'}) # Adapt Price column name
            df_petrol = df_petrol[['Date', 'Petrol_Delhi']]
            
            # 4. Merge them all on the date
            df_merged = pd.merge(df_oil, df_inr, on='Date', how='inner')
            df_merged = pd.merge(df_merged, df_petrol, on='Date', how='inner')
            
            # --- Optional: If your MCX oil is in INR but represents USD barrel price ---
            # --- you might need to calculate Brent_in_INR differently ---
            # --- For this example, we assume MCX data is not directly Brent ---
            # --- We will use the mock function's logic for Brent_in_INR calculation ---
            # --- If you get real Brent USD data, merge it and calculate here ---
            # --- For now, just pass through Crude_INR from MCX ---
            df_merged['Brent_in_INR'] = df_merged['Crude_INR'] # Placeholder - Adapt if needed!

            # 5. Set index and save
            df_clean = df_merged.set_index('Date').dropna()
            
            if df_clean.empty:
                print("ERROR: No matching dates found between Oil, INR, and Petrol files. Check your files.")
                return None

            df_clean.to_csv(clean_file_path)
            print(f"Clean Oil/Petrol/INR data saved to {clean_file_path}")
            return df_clean

        except FileNotFoundError as e:
            print(f"SKIPPING: Raw file not found. Make sure ALL files exist:")
            print(f"1: {raw_oil_path}")
            print(f"2: {raw_inr_path}")
            print(f"3: {raw_petrol_path}\n")
            print("Falling back to mock data for Oil/Petrol/INR.")
            df_mock = create_mock_oil_petrol_inr() # Fallback to mock
            if df_mock is not None:
                df_mock.to_csv(clean_file_path)
                print(f"Clean mock data saved to {clean_file_path}")
            return df_mock
        except EmptyDataError as e:
            print(f"ERROR: A raw file is empty: {e.filename}. Falling back to mock data.")
            df_mock = create_mock_oil_petrol_inr() # Fallback to mock
            if df_mock is not None:
                df_mock.to_csv(clean_file_path)
                print(f"Clean mock data saved to {clean_file_path}")
            return df_mock
        except Exception as e:
            print(f"ERROR: Could not process Oil/INR/Petrol files. Check column names/formats.")
            print(f"{e}\nFalling back to mock data.")
            df_mock = create_mock_oil_petrol_inr() # Fallback to mock
            if df_mock is not None:
                df_mock.to_csv(clean_file_path)
                print(f"Clean mock data saved to {clean_file_path}")
            return df_mock


def get_agri_wpi():
    return load_or_create_data(
        'clean_agri_wpi.csv',
        {'file': 'wpi_vegetables.csv'}, # Assuming WPI file has 'Vegetables' column
        create_mock_agri_wpi
    )

# ==============================================================================
# --- PART 2: ANALYSIS & VISUALIZATION FUNCTIONS ---
# ==============================================================================

@st.cache_data  # Cache the plot generation
def plot_1991_bop_crisis():
    print("Generating 1991 BoP Crisis plot...")
    df = get_forex_reserves()

    if df is None or 'Forex_USD_Million' not in df.columns:
        return create_error_fig("Forex data not found or column mismatch.")

    df_crisis = df.loc['1988-01-01':'1993-01-01']
    if df_crisis.empty:
        return create_error_fig("No Forex data available for 1988-1993.")

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.lineplot(x=df_crisis.index, y=df_crisis['Forex_USD_Million'], ax=ax, color='red', linewidth=2.5)

    crisis_point = pd.to_datetime('1990-08-01')
    low_point = pd.to_datetime('1991-06-01')
    ax.axvline(crisis_point, color='black', linestyle='--', label='1990 Gulf War (Oil Spike)')
    ax.axvline(low_point, color='gold', linestyle='--', label='1991 India Pledges Gold')

    ax.set_title("The 1991 Balance of Payments Crisis", fontsize=18)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Foreign Exchange Reserves (in Million USD)", fontsize=12)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter('${x:,.0f}M'))
    ax.legend()
    plt.tight_layout()
    return fig

@st.cache_data
def plot_2008_financial_crisis():
    print("Generating 2008 Gold vs. Copper plot...")
    df_gold = get_historical_gold_prices()
    df_copper = get_mcx_copper()

    if df_gold is None or 'Price_per_10g_INR' not in df_gold.columns:
        return create_error_fig("Gold data not found or column mismatch.")
    if df_copper is None or 'Price_per_kg_INR' not in df_copper.columns:
        return create_error_fig("Copper data not found or column mismatch.")

    # Align data to common date range before plotting
    start_date = '2007-01-01'
    end_date = '2011-01-01'
    idx = pd.date_range(start_date, end_date) # Create a full index
    
    # Reindex and forward-fill to align data for plotting, handle potential missing dates
    df_gold = df_gold.reindex(idx, method='ffill').loc[start_date:end_date]
    df_copper = df_copper.reindex(idx, method='ffill').loc[start_date:end_date]
    
    if df_gold.empty or df_copper.empty:
         return create_error_fig("No Gold/Copper data for 2007-2011.")


    fig, ax1 = plt.subplots(figsize=(12, 7))

    crisis_point = pd.to_datetime('2008-09-15')
    ax1.axvline(crisis_point, color='red', linestyle='--', label='2008 Financial Crisis')

    # Axis 1: Gold (Safe Haven)
    sns.lineplot(data=df_gold, x=df_gold.index, y='Price_per_10g_INR', ax=ax1, color='gold', label='Gold (Safe Haven)', marker='.') # Use '.' for potentially daily data
    ax1.set_xlabel("Date", fontsize=12)
    ax1.set_ylabel("Gold Price (₹ per 10g)", fontsize=12, color='gold')
    ax1.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))

    # Axis 2: Copper (Industrial)
    ax2 = ax1.twinx()
    sns.lineplot(data=df_copper, x=df_copper.index, y='Price_per_kg_INR', ax=ax2, color='brown', label='Copper (Industrial)', marker='.') # Use '.'
    ax2.set_ylabel("Copper Price (₹ per kg)", fontsize=12, color='brown')
    ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))

    fig.suptitle("2008 Crisis: Gold (Safe Haven) vs. Copper (Industrial)", fontsize=18)
    # Combine legends manually for twin axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', bbox_to_anchor=(0.1, 0.9))

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig

@st.cache_data
def plot_2016_demonetisation_shock():
    print("Generating 2016 Demonetisation plot...")
    df_agri = get_agri_wpi()
    df_gold = get_historical_gold_prices()

    if df_agri is None or 'WPI_Vegetables' not in df_agri.columns:
        return create_error_fig("Agri WPI data not found or column mismatch.")
    if df_gold is None or 'Price_per_10g_INR' not in df_gold.columns:
        return create_error_fig("Gold data not found or column mismatch.")

    df_agri = df_agri.loc['2016-08-01':'2017-02-01']
    df_gold = df_gold.loc['2016-10-01':'2017-01-01'] # Adjust gold range slightly for plotting

    if df_agri.empty or df_gold.empty:
         return create_error_fig("No Agri/Gold data for 2016-2017.")

    fig, ax1 = plt.subplots(figsize=(12, 7))

    crisis_point = pd.to_datetime('2016-11-08')
    ax1.axvline(crisis_point, color='red', linestyle='--', label='Demonetisation (Nov 8)')

    # Axis 1: Agri WPI (Cash Market)
    sns.lineplot(data=df_agri, x=df_agri.index, y='WPI_Vegetables', ax=ax1, color='green', label='Agri WPI (Cash Market)', marker='o')
    ax1.set_xlabel("Date", fontsize=12)
    ax1.set_ylabel("Vegetable WPI (Index)", fontsize=12, color='green')

    # Axis 2: Gold (Store of Value) - Use df_gold which has the correct column name
    ax2 = ax1.twinx()
    sns.lineplot(data=df_gold, x=df_gold.index, y='Price_per_10g_INR', ax=ax2, color='gold', label='Gold Price (Store of Value)', marker='s')
    ax2.set_ylabel("Gold Price (₹ per 10g)", fontsize=12, color='gold')
    ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))


    fig.suptitle("2016 Demonetisation: Agri (Liquidity Crash) vs. Gold (Panic Spike)", fontsize=16)
    # Combine legends manually
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', bbox_to_anchor=(0.1, 0.9))

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig

@st.cache_data
def plot_2022_oil_shock():
    print("Generating 2022 Oil Shock plot...")
    df = get_oil_petrol_inr_data()

    # Check if essential columns exist after loading
    required_cols = ['Brent_in_INR', 'Petrol_Delhi']
    if df is None or not all(col in df.columns for col in required_cols):
        return create_error_fig("Oil/Petrol data not found or column mismatch (needs 'Brent_in_INR', 'Petrol_Delhi').")

    df_crisis = df.loc['2021-12-01':'2022-07-01'].copy()
    if df_crisis.empty:
        return create_error_fig("No Oil/Petrol data available for 2021-12 to 2022-07.")


    # --- Analysis: Rolling Correlation ---
    window_size = 3 # 3-month rolling window (adjust if data is daily)
    # Ensure columns are numeric before calculating correlation
    df_crisis['Brent_in_INR'] = pd.to_numeric(df_crisis['Brent_in_INR'], errors='coerce')
    df_crisis['Petrol_Delhi'] = pd.to_numeric(df_crisis['Petrol_Delhi'], errors='coerce')
    df_crisis.dropna(subset=['Brent_in_INR', 'Petrol_Delhi'], inplace=True) # Drop rows where conversion failed

    if len(df_crisis) < window_size:
         print(f"Warning: Not enough data points ({len(df_crisis)}) for rolling correlation window ({window_size}). Skipping correlation plot.")
         # Plot only the top chart if correlation can't be calculated
         fig, ax1 = plt.subplots(figsize=(12, 7))
         correlation_calculated = False
    else:
         df_crisis['Correlation'] = df_crisis['Brent_in_INR'].rolling(window_size).corr(df_crisis['Petrol_Delhi'])
         fig, (ax1, ax3) = plt.subplots(nrows=2, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
         correlation_calculated = True

    crisis_point = pd.to_datetime('2022-02-24')
    ax1.axvline(crisis_point, color='red', linestyle='--', label='Russia-Ukraine War')

    # --- Top Plot (Prices) ---
    sns.lineplot(data=df_crisis, x=df_crisis.index, y='Brent_in_INR', ax=ax1, color='green', label='Brent Crude (in ₹)', marker='.')
    ax1.set_ylabel("Crude Price (₹ per Barrel)", fontsize=12, color='green')
    ax1.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))


    ax2 = ax1.twinx()
    sns.lineplot(data=df_crisis, x=df_crisis.index, y='Petrol_Delhi', ax=ax2, color='purple', label='Retail Petrol, Delhi (in ₹)', marker='.')
    ax2.set_ylabel("Petrol Price (₹ per Litre)", fontsize=12, color='purple')
    ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))


    fig.suptitle("2022 Oil Shock: Global Price vs. Retail Price", fontsize=18)
    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', bbox_to_anchor=(0.1, 0.9))


    # --- Bottom Plot (Correlation) ---
    if correlation_calculated:
        sns.lineplot(data=df_crisis, x=df_crisis.index, y='Correlation', ax=ax3, color='black', label=f'{window_size}-period Rolling Correlation')
        ax3.set_ylabel("Correlation Coefficient")
        ax3.set_ylim(-1.1, 1.1)
        ax3.axhline(1, color='grey', linestyle=':')
        ax3.axhline(0, color='grey', linestyle=':')
        ax3.axhline(-1, color='grey', linestyle=':')
        ax3.legend()
        ax3.set_xlabel("Date", fontsize=12) # Add x-label to bottom plot

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig

def create_error_fig(message):
    """Returns a matplotlib figure with an error message."""
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.text(0.5, 0.5, f"Data Error: {message}\n(Using mock data for now).\nTo fix, check 'data/' folder and function calls.",
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
""")

# --- Run Setup ---
setup_directories()

# --- 3. Main Page Navigation (Using Tabs) ---
tab1, tab2, tab3 = st.tabs([
    "Global Crises: The 'Controlled' Era (1947-1991)",
    "Global Crises: The 'Market' Era (1991-Present)",
    "Domestic Shocks: Policy & Liquidity"
])

# --- TAB 1: CONTROLLED ERA ---
with tab1:
    st.header("The 'Controlled' Era (1947-1991)")
    st.markdown("""
    During this period, the government, not the market, set prices. A global crisis
    didn't cause an immediate price spike for consumers. Instead, it created a
    **national-level emergency** that drained government funds and forced massive policy changes.
    """)

    st.subheader("Case Study: The 1991 Balance of Payments (BoP) Crisis")
    st.write("""
    **Background:** The 1990 Gulf War caused global oil prices to skyrocket. India,
    still under the "controlled" system, had to buy this expensive oil but sell it
    cheaply, draining its entire foreign exchange (Forex) reserve.

    **Analysis:** The chart below shows India's Forex reserves. You can see a steady
    decline after the Gulf War (Aug 1990) which accelerates into a freefall. At its
    lowest point in June 1991, India had only enough money for ~3 weeks of imports
    and was forced to physically pledge its gold to the IMF. This single event was
    the trigger for the 1991 Economic Liberalization.
    """)

    with st.spinner("Generating 1991 Crisis plot..."):
        fig1 = plot_1991_bop_crisis()
        st.pyplot(fig1)

# --- TAB 2: MARKET ERA ---
with tab2:
    st.header("The 'Market' Era (1991-Present)")
    st.markdown("""
    After the 1991 reforms, India liberalized its economy. Now, global crises
    **bypass the government** and hit the Indian market—and the consumer—directly
    and instantly. Policy is now a *reaction* to these shocks.
    """)

    st.subheader("Case Study: The 2008 Global Financial Crisis")
    st.write("""
    **Background:** The 2008 crisis was a "demand shock" and a "confidence shock."
    Investors feared a global recession (crashing industrial demand) and fled to safety.

    **Analysis:** This chart shows two stories. **Copper (Brown Line)**, an industrial
    metal, crashed as investors predicted less construction and manufacturing.
    At the same time, **Gold (Gold Line)**, a "safe-haven" asset, spiked as
    panicked investors sought a secure store of value. This demonstrates India's
    full integration into global market sentiment.
    """)

    with st.spinner("Generating 2008 Crisis plot..."):
        fig2 = plot_2008_financial_crisis()
        st.pyplot(fig2)

    st.divider()

    st.subheader("Case Study: The 2022 Russia-Ukraine War")
    st.write("""
    **Background:** The 2022 war created a massive energy and food supply shock.
    This was the ultimate test of India's "Market Era."

    **Analysis (Top Chart):** This chart shows the **dual shock**. The global price
    of crude oil (in ₹, Green Line) spiked. Because retail petrol prices (Purple Line)
    are now largely de-regulated, they followed the global price upwards, passing the cost
    directly to the consumer.

    **Analysis (Bottom Chart):** This chart proves the link statistically. It shows
    the 3-period **rolling correlation** between the crude price (in ₹) and the retail petrol price.
    Notice how the correlation approaches +1.0 during the peak? This means that for this period,
    the price at the pump in Delhi moved in *strong lock-step* with the global market pressures.
    """)

    with st.spinner("Generating 2022 Oil Shock plot..."):
        fig4 = plot_2022_oil_shock()
        st.pyplot(fig4)

# --- TAB 3: DOMESTIC SHOCKS ---
with tab3:
    st.header("Domestic Shocks: Policy & Liquidity")
    st.markdown("""
    Not all shocks come from overseas. Sometimes, domestic policy decisions
    can have an immediate and powerful impact on commodity prices.
    """)

    st.subheader("Case Study: The 2016 Demonetisation")
    st.write("""
    **Background:** On Nov 8, 2016, the government invalidated 86% of the
    nation's currency overnight. This created a severe **liquidity crisis**—a
    sudden removal of cash from the economy.

    **Analysis:** This chart shows two opposite effects. The **Agri WPI (Green Line)**,
    which represents cash-based markets like vegetable mandis, *crashed*.
    Farmers had to sell produce at a loss because no one had the cash to buy.
    Simultaneously, the **Gold Price (Gold Line)** saw an immediate, short-lived
    *spike* as people with unaccounted cash rushed to convert it into gold,
    a physical store of value.
    """)

    with st.spinner("Generating 2016 Demonetisation plot..."):
        fig3 = plot_2016_demonetisation_shock()
        st.pyplot(fig3)

# --- Sidebar "About" Section ---
st.sidebar.title("About")
st.sidebar.info(
    "This is a project demonstrating the impact of global and domestic crises "
    "on Indian commodity prices from 1947 to the present day. "
    "Built by KD with assistance from Friday."
)

# --- Optional: Show Raw Data Sample in Sidebar ---
if st.sidebar.checkbox("Show Sample Data (from Mock Files)"):
    try:
        st.sidebar.subheader("Forex Reserves")
        df_forex = get_forex_reserves()
        if df_forex is not None:
            st.sidebar.dataframe(df_forex.head(3))
        else:
            st.sidebar.warning("Forex data unavailable.")
    except Exception as e:
        st.sidebar.error(f"Error loading Forex sample: {e}")

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
        st.sidebar.subheader("Agri WPI")
        df_agri = get_agri_wpi()
        if df_agri is not None:
            st.sidebar.dataframe(df_agri.head(3))
        else:
            st.sidebar.warning("Agri WPI data unavailable.")
    except Exception as e:
        st.sidebar.error(f"Error loading Agri WPI sample: {e}")

# --- Setup Directories on first run (call at the end) ---
# setup_directories() # Moved setup call earlier before data loading starts
