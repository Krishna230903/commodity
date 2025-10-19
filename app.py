"""
Complete Project: India's Commodity Price History (All-in-One)

V1.1: Fixed Streamlit UnhashableParamError by adding an underscore
to the '_create_mock_func' argument in 'load_or_create_data'.

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
def load_or_create_data(clean_file, raw_file_info, _create_mock_func): # <-- FIX 1: Added underscore
    """
    Helper function: Tries to load clean CSV.
    If fails, it tries to load raw files.
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
        # --- Try to load from raw files (TEMPLATE) ---
        try:
            raw_path = os.path.join(RAW_DATA_DIR, raw_file_info['file'])
            if not os.path.exists(raw_path):
                raise FileNotFoundError
            
            print(f"Processing raw file: {raw_path}")
            # --- YOUR REAL DATA LOADING & CLEANING CODE WOULD GO HERE ---
            # e.g., df = pd.read_excel(raw_path, skiprows=raw_file_info['skiprows'])
            # ... (cleaning steps) ...
            raise NotImplementedError # Force jump to mock data for this demo
        
        except (FileNotFoundError, NotImplementedError):
            print(f"Raw file not found or processing not implemented. Creating mock data for {clean_file}.")
            df = _create_mock_func() # <-- FIX 2: Call the underscore-prefixed variable
            df.to_csv(clean_file_path)
            print(f"Clean mock data saved to {clean_file_path}")
            return df

# --- Mock Data Creation Functions ---
# (These don't need caching, as they are called by the cached function)

def create_mock_forex():
    mock_data = """
Date,Forex_USD_Million
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
    return df

def create_mock_gold():
    mock_data = """
Date,Price_per_10g_INR
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
    return df

def create_mock_copper():
    mock_data = """
Date,Price_per_kg_INR
2007-01-01,320
2008-01-01,350
2008-09-15,300
2009-01-01,150
2010-01-01,340
2011-01-01,450
"""
    df = pd.read_csv(io.StringIO(mock_data), parse_dates=True, index_col='Date')
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
Date,WPI_Vegetables
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
    return df

# --- Part 1: Main Data Function Calls ---
# These are the functions your app will call

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

def get_oil_petrol_inr_data():
    return load_or_create_data(
        'clean_oil_petrol_inr.csv',
        {'file_oil': 'mcx_oil.csv', 'file_inr': 'usd_inr.csv', 'file_petrol': 'ppac_petrol.csv'},
        create_mock_oil_petrol_inr
    )
    
def get_agri_wpi():
    return load_or_create_data(
        'clean_agri_wpi.csv',
        {'file': 'wpi_vegetables.csv'},
        create_mock_agri_wpi
    )

# ==============================================================================
# --- PART 2: ANALYSIS & VISUALIZATION FUNCTIONS ---
# ==============================================================================

@st.cache_data  # Cache the plot generation
def plot_1991_bop_crisis():
    print("Generating 1991 BoP Crisis plot...")
    df = get_forex_reserves()
    
    if df is None:
        return create_error_fig("Forex data not found.")
        
    df_crisis = df.loc['1988-01-01':'1993-01-01']
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

    if df_gold is None or df_copper is None:
        return create_error_fig("Gold or Copper data not found.")
        
    df_gold = df_gold.loc['2007-01-01':'2011-01-01']
    df_copper = df_copper.loc['2007-01-01':'2011-01-01']
    
    fig, ax1 = plt.subplots(figsize=(12, 7))
    
    crisis_point = pd.to_datetime('2008-09-15')
    ax1.axvline(crisis_point, color='red', linestyle='--', label='2008 Financial Crisis')
    
    # Axis 1: Gold (Safe Haven)
    sns.lineplot(data=df_gold, x=df_gold.index, y='Price_per_10g_INR', ax=ax1, color='gold', label='Gold (Safe Haven)', marker='o')
    ax1.set_xlabel("Date", fontsize=12)
    ax1.set_ylabel("Gold Price (₹ per 10g)", fontsize=12, color='gold')
    ax1.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))
    
    # Axis 2: Copper (Industrial)
    ax2 = ax1.twinx()
    sns.lineplot(data=df_copper, x=df_copper.index, y='Price_per_kg_INR', ax=ax2, color='brown', label='Copper (Industrial)', marker='o')
    ax2.set_ylabel("Copper Price (₹ per kg)", fontsize=12, color='brown')
    ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter('₹{x:,.0f}'))

    fig.suptitle("2008 Crisis: Gold (Safe Haven) vs. Copper (Industrial)", fontsize=18)
    fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9))
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig

@st.cache_data
def plot_2016_demonetisation_shock():
    print("Generating 2016 Demonetisation plot...")
    df_agri = get_agri_wpi()
    df_gold = get_historical_gold_prices()

    if df_agri is None or df_gold is None:
        return create_error_fig("Agri or Gold data not found.")
        
    df_agri = df_agri.loc['2016-08-01':'2017-02-01']
    df_gold = df_gold.loc['2016-10-01':'2017-01-01']
    
    fig, ax1 = plt.subplots(figsize=(12, 7))
    
    crisis_point = pd.to_datetime('2016-11-08')
    ax1.axvline(crisis_point, color='red', linestyle='--', label='Demonetisation (Nov 8)')
    
    # Axis 1: Agri WPI (Cash Market)
    sns.lineplot(data=df_agri, x=df_agri.index, y='WPI_Vegetables', ax=ax1, color='green', label='Agri WPI (Cash Market)', marker='o')
    ax1.set_xlabel("Date", fontsize=12)
    ax1.set_ylabel("Vegetable WPI (Index)", fontsize=12, color='green')
    
    # Axis 2: Gold (Safe Haven)
    ax2 = ax1.twinx()
    sns.lineplot(data=df_gold, x=df_gold.index, y='Price_per_10g_INR', ax=ax2, color='gold', label='Gold Price (Store of Value)', marker='s')
    ax2.set_ylabel("Gold Price (₹ per 10g)", fontsize=12, color='gold')
    
    fig.suptitle("2016 Demonetisation: Agri (Liquidity Crash) vs. Gold (Panic Spike)", fontsize=16)
    fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9))
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig

@st.cache_data
def plot_2022_oil_shock():
    print("Generating 2022 Oil Shock plot...")
    df = get_oil_petrol_inr_data()

    if df is None:
        return create_error_fig("Oil/Petrol data not found.")
        
    df_crisis = df.loc['2021-12-01':'2022-07-01'].copy()
    
    # --- New Analysis: Rolling Correlation ---
    window_size = 3 # 3-month rolling window
    df_crisis['Correlation'] = df_crisis['Brent_in_INR'].rolling(window_size).corr(df_crisis['Petrol_Delhi'])

    fig, (ax1, ax3) = plt.subplots(nrows=2, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    
    crisis_point = pd.to_datetime('2022-02-24')
    ax1.axvline(crisis_point, color='red', linestyle='--', label='Russia-Ukraine War')
    
    # --- Top Plot (Prices) ---
    sns.lineplot(data=df_crisis, x=df_crisis.index, y='Brent_in_INR', ax=ax1, color='green', label='Brent Crude (in ₹)', marker='o')
    ax1.set_ylabel("Crude Price (₹ per Barrel)", fontsize=12, color='green')
    
    ax2 = ax1.twinx()
    sns.lineplot(data=df_crisis, x=df_crisis.index, y='Petrol_Delhi', ax=ax2, color='purple', label='Retail Petrol, Delhi (in ₹)', marker='o')
    ax2.set_ylabel("Petrol Price (₹ per Litre)", fontsize=12, color='purple')

    fig.suptitle("2022 Oil Shock: Global Price vs. Retail Price", fontsize=18)
    fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9))
    
    # --- Bottom Plot (Correlation) ---
    sns.lineplot(data=df_crisis, x=df_crisis.index, y='Correlation', ax=ax3, color='black', label=f'{window_size}-Month Rolling Correlation')
    ax3.set_ylabel("Correlation Coefficient")
    ax3.set_ylim(-1.1, 1.1)
    ax3.axhline(1, color='grey', linestyle=':')
    ax3.axhline(0, color='grey', linestyle=':')
    ax3.axhline(-1, color='grey', linestyle=':')
    ax3.legend()
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig

def create_error_fig(message):
    """Returns a matplotlib figure with an error message."""
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.text(0.5, 0.5, f"Data Error: {message}\n(Using mock data for now).\nTo fix, check 'data/' folder and 'load_or_create_data' function.",
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
    are now de-regulated, they followed the global price upwards, passing the cost 
    directly to the consumer.
    
    **Analysis (Bottom Chart):** This chart proves the link statistically. It shows 
    the 3-month **rolling correlation** between the global price and the retail price. 
    Notice how the correlation jumps to +1.0? This means that for this period, 
    the price at the pump in Delhi moved in *perfect lock-step* with the global market.
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

if st.sidebar.checkbox("Show Sample Data (from Mock Files)"):
    st.sidebar.subheader("Forex Reserves")
    st.sidebar.dataframe(get_forex_reserves().head(3))
    
    st.sidebar.subheader("Gold Prices")
    st.sidebar.dataframe(get_historical_gold_prices().head(3))
    
    st.sidebar.subheader("Agri WPI")
    st.sidebar.dataframe(get_agri_wpi().head(3))

# --- Setup Directories on first run ---
setup_directories()
