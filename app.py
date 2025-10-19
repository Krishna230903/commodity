"""
PROJECT ENGINE (Combines Part 1 and Part 2)

Part 1: The Data Pipeline
- Functions to load, clean, and cache data.
- Data is either loaded from a raw file/URL or from a pre-cleaned file.
- All functions return a clean pandas DataFrame.

Part 2: The Analysis Engine
- Functions to generate specific plots for our case studies.
- Each plot function calls the necessary data functions from Part 1.
- Each plot function returns a 'matplotlib.figure.Figure' object,
  ready for Part 3 (Streamlit).

MOCK DATA is used in this file so it can run immediately
without any manual downloads. You can replace the 'else'
blocks in the Part 1 functions with your real file-loading code.
"""

import pandas as pd
import os
import io  # Used for reading string-based mock data
import openpyxl  # Required for pandas
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# --- Global Settings ---
CLEAN_DATA_DIR = "clean_data"
RAW_DATA_DIR = "data"


def setup_directories():
    """Creates 'clean_data' and 'data' directories if they don't exist."""
    if not os.path.exists(CLEAN_DATA_DIR):
        os.makedirs(CLEAN_DATA_DIR)
        print(f"Created directory: {CLEAN_DATA_DIR}")
    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR)
        print(f"Created directory: {RAW_DATA_DIR}")


# ==============================================================================
# --- PART 1: DATA PIPELINE FUNCTIONS ---
# ==============================================================================

def get_forex_reserves():
    """
    Part 1 function for 1991 Crisis.
    Loads and cleans RBI Foreign Exchange Reserves data.
    Tries to load 'clean_forex_reserves.csv' first.
    If not found, it generates and saves mock data.
    """
    clean_file_path = os.path.join(CLEAN_DATA_DIR, 'clean_forex_reserves.csv')

    if os.path.exists(clean_file_path):
        # If clean file exists, load it (fast path)
        print("Loading cached Forex data...")
        df = pd.read_csv(clean_file_path, parse_dates=True, index_col='Date')
        return df
    else:
        # --- Create Mock Data (Replace this block with your real file loading) ---
        print("Creating mock Forex data...")
        mock_data_csv = """
Date_Str,Forex_USD_Million
1988-01-01,5400
1988-07-01,5100
1989-01-01,4500
1989-07-01,4200
1990-01-01,4000
1990-07-01,3500
1990-08-01,2800
1991-01-01,2100
1991-06-01,1100
1991-07-01,1200
1991-12-01,3500
1992-07-01,5000
1993-01-01,6000
"""
        df = pd.read_csv(io.StringIO(mock_data_csv))
        df['Date'] = pd.to_datetime(df['Date_Str'])
        df = df[['Date', 'Forex_USD_Million']].set_index('Date')
        # --- End Mock Data Block ---

        # Save the clean data for next time
        df.to_csv(clean_file_path)
        print(f"Clean Forex data saved to {clean_file_path}")
        return df


def get_historical_gold_prices():
    """
    Part 1 function for 2008 Crisis.
    Loads and cleans historical Gold prices.
    Tries to load 'clean_gold_prices.csv' first.
    If not found, it generates and saves mock data.
    """
    clean_file_path = os.path.join(CLEAN_DATA_DIR, 'clean_gold_prices.csv')

    if os.path.exists(clean_file_path):
        print("Loading cached Gold data...")
        df = pd.read_csv(clean_file_path, parse_dates=True, index_col='Date')
        return df
    else:
        # --- Create Mock Data (Replace with your real file) ---
        print("Creating mock Gold data...")
        mock_data_csv = """
Year,Price_per_10g_INR
2005,7000
2006,8500
2007,10800
2008,12500
2009,14500
2010,18500
2011,26400
"""
        df = pd.read_csv(io.StringIO(mock_data_csv))
        df['Date'] = pd.to_datetime(df['Year'], format='%Y')
        df['Price_per_10g_INR'] = pd.to_numeric(df['Price_per_10g_INR'])
        df = df[['Date', 'Price_per_10g_INR']].set_index('Date')
        # --- End Mock Data Block ---
        
        df.to_csv(clean_file_path)
        print(f"Clean Gold data saved to {clean_file_path}")
        return df

def get_mcx_oil_and_inr():
    """
    Part 1 function for 2022 Crisis.
    Loads and cleans MCX Crude Oil and USD/INR data.
    Generates mock data for this combined case.
    """
    clean_file_path = os.path.join(CLEAN_DATA_DIR, 'clean_oil_and_inr.csv')
    
    if os.path.exists(clean_file_path):
        print("Loading cached Oil & INR data...")
        df = pd.read_csv(clean_file_path, parse_dates=True, index_col='Date')
        return df
    else:
        # --- Create Mock Data (Replace with your real files) ---
        print("Creating mock Oil & INR data...")
        mock_data_csv = """
Date,Brent_USD,USD_INR
2021-12-01,74.8
2022-01-01,86.5,74.5
2022-02-01,97.1,75.0
2022-03-01,117.2,76.0
2022-04-01,105.0,76.2
2022-05-01,113.0,77.0
2022-06-01,122.7,78.0
2022-07-01,107.0,79.5
"""
        df = pd.read_csv(io.StringIO(mock_data_csv))
        df['Date'] = pd.to_datetime(df['Date'])
        
        # --- This is the key analysis step ---
        df['Brent_in_INR'] = df['Brent_USD'] * df['USD_INR']
        
        df = df.set_index('Date')
        # --- End Mock Data Block ---
        
        df.to_csv(clean_file_path)
        print(f"Clean Oil & INR data saved to {clean_file_path}")
        return df


# ==============================================================================
# --- PART 2: ANALYSIS & VISUALIZATION FUNCTIONS ---
# ==============================================================================

def plot_1991_bop_crisis():
    """
    Part 2 function.
    Generates the chart for the 1991 Balance of Payments Crisis.
    Calls get_forex_reserves() to get its data.
    """
    print("Generating 1991 BoP Crisis plot...")
    
    # 1. Get Data
    df = get_forex_reserves()
    # Filter for the crisis period
    df_crisis = df.loc['1988-01-01':'1993-01-01']

    # 2. Create Plot
    sns.set_style("darkgrid")
    fig, ax = plt.subplots(figsize=(12, 7))
    
    sns.lineplot(
        x=df_crisis.index,
        y=df_crisis['Forex_USD_Million'],
        ax=ax,
        color='red',
        linewidth=2.5
    )

    # 3. Add Annotations (The Story)
    crisis_point = pd.to_datetime('1990-08-01') # Iraq invades Kuwait (Oil spike)
    low_point = pd.to_datetime('1991-06-01')    # India pledges gold
    
    ax.axvline(crisis_point, color='black', linestyle='--', label='1990 Gulf War (Oil Spike)')
    ax.axvline(low_point, color='gold', linestyle='--', label='1991 India Pledges Gold')
    
    ax.annotate(
        "Gulf War Begins\nOil Prices Spike",
        xy=(crisis_point, df_crisis.loc[crisis_point]['Forex_USD_Million']),
        xytext=(crisis_point + pd.DateOffset(months=6), 4000),
        arrowprops=dict(facecolor='black', shrink=0.05),
        ha='center'
    )
    
    # 4. Professional Styling
    ax.set_title("The 1991 Balance of Payments Crisis", fontsize=18)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Foreign Exchange Reserves (in Million USD)", fontsize=12)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter('${x:,.0f}M'))
    ax.legend()
    
    plt.tight_layout()
    return fig


def plot_2008_financial_crisis_gold():
    """
    Part 2 function.
    Generates the "flight to safety" chart for Gold in 2008.
    Calls get_historical_gold_prices() to get its data.
    """
    print("Generating 2008 Gold 'Flight to Safety' plot...")

    # 1. Get Data
    df = get_historical_gold_prices()
    df_crisis = df.loc['2005-01-01':'2011-01-01']

    # 2. Create Plot
    sns.set_style("darkgrid")
    fig, ax = plt.subplots(figsize=(12, 7))

    sns.lineplot(
        x=df_crisis.index,
        y=df_crisis['Price_per_10g_INR'],
        ax=ax,
        color='gold',
        linewidth=2.5,
        marker='o'
    )
    
    # 3. Add Annotations
    crisis_point = pd.to_datetime('2008-09-15') # Lehman Brothers collapse
    
    ax.axvline(crisis_point, color='red', linestyle='--', label='2008 Financial Crisis')
    
    ax.annotate(
        "Lehman Brothers Collapse\nInvestors 'Flight to Safety'",
        xy=(crisis_point, df_crisis.loc['2008-01-01']['Price_per_10g_INR']),
        xytext=(crisis_point - pd.DateOffset(years=1), 16000),
        arrowprops=dict(facecolor='black', shrink=0.05),
        ha='center'
    )

    # 4. Professional Styling
    ax.set_title("Gold Price (INR) During 2008 Financial Crisis", fontsize=18)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Price per 10g (in ₹)", fontsize=12)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))
    ax.legend()
    
    plt.tight_layout()
    return fig


def plot_2022_oil_shock():
    """
    Part 2 function.
    Generates the chart for the 2022 Russia-Ukraine War.
    Shows Brent (USD) vs. Brent (INR).
    """
    print("Generating 2022 Oil Shock plot...")
    
    # 1. Get Data
    df = get_mcx_oil_and_inr()
    df_crisis = df.loc['2021-12-01':'2022-07-01']

    # 2. Create Plot (two y-axes)
    sns.set_style("darkgrid")
    fig, ax1 = plt.subplots(figsize=(12, 7))
    
    # Axis 1: Brent in USD
    sns.lineplot(data=df_crisis, x=df_crisis.index, y='Brent_USD',
                 ax=ax1, color='blue', label='Brent Crude (USD)', marker='o')
    ax1.set_xlabel("Date", fontsize=12)
    ax1.set_ylabel("Price per Barrel (in $)", fontsize=12, color='blue')
    ax1.yaxis.set_major_formatter(mticker.StrMethodFormatter('${x:,.0f}'))
    
    # Axis 2: Brent in INR
    ax2 = ax1.twinx()
    sns.lineplot(data=df_crisis, x=df_crisis.index, y='Brent_in_INR',
                 ax=ax2, color='green', label='Brent Crude (INR)', marker='o')
    ax2.set_ylabel("Price per Barrel (in ₹)", fontsize=12, color='green')
    ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))

    # 3. Add Annotations
    crisis_point = pd.to_datetime('2022-02-24') # Russia-Ukraine War
    ax1.axvline(crisis_point, color='red', linestyle='--', label='Russia-Ukraine War')
    
    # 4. Professional Styling
    fig.suptitle("Impact of 2022 War on Oil Price (USD vs. INR)", fontsize=18)
    fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9))
    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust for suptitle
    
    return fig


# ==============================================================================
# --- MAIN EXECUTION BLOCK (FOR TESTING) ---
# ==============================================================================

if __name__ == "__main__":
    """
    This block runs ONLY when you execute this file directly.
    It will first run the Part 1 pipeline to create the clean files.
    Then, it will test each Part 2 plot function and show you the chart.
    """
    print("--- [Part 1 & 2] Running Project Engine as a Test ---")
    
    # 1. Setup
    setup_directories()

    # 2. Test Plot 1
    print("\n--- Testing Plot 1: 1991 BoP Crisis ---")
    fig1 = plot_1991_bop_crisis()
    print("Plot 1 generated. Showing now...")
    plt.show() # This will display the first plot

    # 3. Test Plot 2
    print("\n--- Testing Plot 2: 2008 Gold Crisis ---")
    fig2 = plot_2008_financial_crisis_gold()
    print("Plot 2 generated. Showing now...")
    plt.show() # This will display the second plot

    # 4. Test Plot 3
    print("\n--- Testing Plot 3: 2022 Oil Shock ---")
    fig3 = plot_2022_oil_shock()
    print("Plot 3 generated. Showing now...")
    plt.show() # This will display the third plot

    print("\n--- [Part 1 & 2] All tests complete. ---")
