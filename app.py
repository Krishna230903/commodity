"""
Part 1: The Data Pipeline (Acquisition & Cleaning)

This script:
1.  Creates an output directory for clean data.
2.  Defines a separate function for each data source.
3.  Loads data (either from a direct URL or a local file).
4.  Cleans and standardizes the data (dates, numbers).
5.  Saves the clean data to a new CSV file in the 'clean_data/' folder.

You must manually download the required files and place them
in a 'data/' folder, then update the file paths in this script.
"""

import pandas as pd
import os
import openpyxl  # Required for pandas to read .xlsx files

# --- Global Settings ---
# This is where your new clean files will be saved.
CLEAN_DATA_DIR = "clean_data"
# This is where you should save your manually downloaded raw files.
RAW_DATA_DIR = "data"


def setup_directories():
    """Creates the 'clean_data' directory if it doesn't exist."""
    if not os.path.exists(CLEAN_DATA_DIR):
        os.makedirs(CLEAN_DATA_DIR)
        print(f"Created directory: {CLEAN_DATA_DIR}")

# --- Data Loading Functions ---

def load_and_clean_wpi():
    """
    Fetches WPI (Wholesale Price Index) data.
    This is a REAL, WORKING EXAMPLE of a direct URL import.
    """
    print("Processing WPI data...")
    # This is a real, live URL from data.gov.in (WPI 2011-12 Series)
    # This shows the "direct import" method.
    url = "https://data.gov.in/files/ogdpv2dms/s3fs-public/Wholesale_Price_Index__WPI___New_Series__2011-12__Monthly_1_0_0.csv"
    
    try:
        df = pd.read_csv(url)
        
        # --- Start Cleaning ---
        # 1. Convert date column to datetime objects
        # The format 'Jan-12' is '%b-%y' (Abbreviated month-short year)
        df['Date'] = pd.to_datetime(df['Month-Year'], format='%b-%y')
        
        # 2. Select only the columns we need for the project
        # (Example: We want Food, Fuel, and Manufactured Products)
        df_clean = df[['Date', 'Food Articles', 'Fuel & Power', 'Manufactured Products']]
        
        # 3. Set the new 'Date' column as the index
        df_clean = df_clean.set_index('Date')
        
        # 4. Save the clean file
        save_path = os.path.join(CLEAN_DATA_DIR, 'clean_wpi_2011_present.csv')
        df_clean.to_csv(save_path)
        print(f"SUCCESS: WPI data saved to {save_path}\n")
        
    except Exception as e:
        print(f"ERROR: Could not download or process WPI data from URL.")
        print(f"{e}\n")

def load_and_clean_forex_reserves():
    """
    Loads and cleans RBI Foreign Exchange Reserves data.
    This is a TEMPLATE for a MANUALLY DOWNLOADED file.
    """
    print("Processing RBI Forex Reserves data...")
    # You must download this file from the RBI website (DBIE portal)
    # and save it in your 'data/' folder.
    local_file_path = os.path.join(RAW_DATA_DIR, "rbi_forex_data.xlsx") 

    try:
        # RBI files often have many header rows. 'skiprows' is your best friend.
        # You MUST open your Excel file and see how many rows to skip.
        df = pd.read_excel(local_file_path, skiprows=5)
        
        # --- Start Cleaning ---
        # This part is a GUESS. You must inspect your file and adapt.
        
        # 1. Rename messy columns
        df = df.rename(columns={
            'Month / Year': 'Date_Str',
            'Total Reserves (USD Million)': 'Forex_USD_Million' 
            # Add other columns you need
        })
        
        # 2. Convert date column
        # The format might be '2023 Apr' (%Y %b)
        df['Date'] = pd.to_datetime(df['Date_Str'], format='%Y %b')
        
        # 3. Clean number column (remove 'NA', '-', etc.)
        df['Forex_USD_Million'] = pd.to_numeric(df['Forex_USD_Million'], errors='coerce')
        
        # 4. Select, index, and save
        df_clean = df[['Date', 'Forex_USD_Million']].set_index('Date')
        
        save_path = os.path.join(CLEAN_DATA_DIR, 'clean_forex_reserves.csv')
        df_clean.to_csv(save_path)
        print(f"SUCCESS: Forex Reserves data saved to {save_path}\n")

    except FileNotFoundError:
        print(f"ERROR: File not found: {local_file_path}")
        print("Please download the RBI Forex data, save it to your 'data/' folder, and update the path.\n")
    except Exception as e:
        print(f"ERROR: Could not process RBI file. Check your 'skiprows' and column names.")
        print(f"{e}\n")

def load_and_clean_gold_prices():
    """
    Loads and cleans historical Gold prices (1947-present).
    This is a TEMPLATE for a MANUALLY DOWNLOADED file.
    """
    print("Processing historical Gold prices...")
    # You will likely find this data on a financial site,
    # copy it to Excel, and save it as a CSV.
    local_file_path = os.path.join(RAW_DATA_DIR, "historical_gold_inr.csv")

    try:
        df = pd.read_csv(local_file_path)
        
        # --- Start Cleaning (Assuming columns 'Year' and 'Price_per_10g_INR') ---
        # 1. Convert date
        df['Date'] = pd.to_datetime(df['Year'], format='%Y')
        
        # 2. Clean numbers
        # Remove '₹' and ',' characters before converting to numeric
        df['Price_per_10g_INR'] = df['Price_per_10g_INR'].astype(str).str.replace('₹', '').str.replace(',', '')
        df['Price_per_10g_INR'] = pd.to_numeric(df['Price_per_10g_INR'], errors='coerce')
        
        # 3. Select, index, and save
        df_clean = df[['Date', 'Price_per_10g_INR']].set_index('Date')
        
        save_path = os.path.join(CLEAN_DATA_DIR, 'clean_gold_prices.csv')
        df_clean.to_csv(save_path)
        print(f"SUCCESS: Gold price data saved to {save_path}\n")

    except FileNotFoundError:
        print(f"ERROR: File not found: {local_file_path}")
        print("Please find historical gold prices, save it as a CSV in 'data/', and update the path.\n")
    except Exception as e:
        print(f"ERROR: Could not process Gold file. Check your column names ('Year', 'Price_per_10g_INR').")
        print(f"{e}\n")

def load_and_clean_mcx_oil():
    """
    Loads and cleans MCX Crude Oil prices.
    This is a TEMPLATE for a MANUALLY DOWNLOADED file from MCX.
    """
    print("Processing MCX Crude Oil data...")
    # You must go to the MCX website, use their chart,
    # and "Download CSV" for the commodity and date range.
    local_file_path = os.path.join(RAW_DATA_DIR, "mcx_crude_oil_daily.csv")

    try:
        # MCX/NCDEX files are often well-formatted
        df = pd.read_csv(local_file_path)
        
        # --- Start Cleaning ---
        # 1. Convert date
        df['Date'] = pd.to_datetime(df['Date'])
        
        # 2. Select, index, and save
        # We keep Open, High, Low, Close for potential candlestick charts
        df_clean = df[['Date', 'Open', 'High', 'Low', 'Close']]
        df_clean = df_clean.set_index('Date')
        
        save_path = os.path.join(CLEAN_DATA_DIR, 'clean_mcx_oil_daily.csv')
        df_clean.to_csv(save_path)
        print(f"SUCCESS: MCX Crude Oil data saved to {save_path}\n")
        
    except FileNotFoundError:
        print(f"ERROR: File not found: {local_file_path}")
        print("Please download daily Crude Oil data from MCX, save it in 'data/', and update the path.\n")
    except Exception as e:
        print(f"ERROR: Could not process MCX file. Check your column names.")
        print(f"{e}\n")

# --- Main Pipeline Runner ---

def main():
    """Runs the entire Part 1 data pipeline."""
    print("--- [Part 1] Starting Data Acquisition & Cleaning Pipeline ---")
    
    # 1. Create the 'clean_data/' directory
    setup_directories()
    
    # 2. Run each processing function
    # We will run them all, and they will print their own success/error messages.
    
    # Example 1: Direct URL download
    load_and_clean_wpi()
    
    # Example 2: Manual Excel download (e.g., from RBI)
    load_and_clean_forex_reserves()
    
    # Example 3: Manual CSV download (e.g., from a financial blog)
    load_and_clean_gold_prices()
    
    # Example 4: Manual CSV download (e.g., from MCX)
    load_and_clean_mcx_oil()
    
    # --- Add more functions for your other data here ---
    # e.g., load_and_clean_msp_data()
    # e.g., load_and_clean_ppac_petrol_prices()
    
    print("--- [Part 1] Pipeline Finished. Check 'clean_data/' folder. ---")


if __name__ == "__main__":
    main()
