import streamlit as st
import pandas as pd
import plotly.express as px
import firebase_admin
from firebase_admin import credentials, db

# Setup Page
st.set_page_config(page_title="Executive Analytics", layout="wide", page_icon=":material/show_chart:")

# --- UI LAYOUT & MOBILE RESPONSIVENESS FIXES ---
st.markdown("""
    <style>
    /* 1. Desktop: Pull the entire app upward & push metric down */
    .block-container {
        padding-top: 0 !important; 
    }
    div[data-testid="stMarkdownContainer"] h1,
    div[data-testid="stMarkdownContainer"] h2 {
        margin-bottom: 2rem !important;
    }
    
    /* 2. Mobile: Scale down typography for screens under 768px */
    @media screen and (max-width: 768px) {
       /* Shrink Main Title */
        div[data-testid="stMarkdownContainer"] h1,
        div[data-testid="stMarkdownContainer"] h2 {
            font-size: 1.25rem !important;
            margin-bottom: 0.5rem !important; 
            line-height: 1.2 !important;
        }
        
        /* Shrink Chart Subheadings */
        div[data-testid="stMarkdownContainer"] h3 {
            font-size: 1.15rem !important;
        }
        
        /* Shrink KPI Numbers */
        div[data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
        }
        
        /* Shrink KPI Labels */
        div[data-testid="stMetricLabel"] > div {
            font-size: 0.8rem !important;
        }
        
        /* Shrink Chart Captions */
        div[data-testid="stCaptionContainer"] {
            font-size: 0.75rem !important;
            line-height: 1.2 !important;
        }
        
        /* Add breathing room to the edges of the phone screen */
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 0 !important; /* Leaves room for mobile menu */
        }
    }
    </style>
""", unsafe_allow_html=True)
st.title(":material/show_chart: Executive Analytics & ROI")

# --- FIREBASE SETUP ---
if not firebase_admin._apps:
    # 1. CLOUD DEPLOYMENT: Read from Streamlit Secrets
    if "firebase" in st.secrets:
        cert_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(cert_dict)
    # 2. LOCAL DEVELOPMENT: Read from the JSON file
    else:
        cred = credentials.Certificate('firebase_credentials.json')
        
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://karachi-fleet-db-default-rtdb.firebaseio.com/'
    })

# Fetch the ledger data
ledger_data = db.reference('/ledger').get()

if not ledger_data:
    st.info("No historical data available yet. Please save a daily report from the Manager Dashboard.")
else:
    # Build dataframe properly structured from Firebase push UUID keys 
    df = pd.DataFrame.from_dict(ledger_data, orient='index')
    
    # Clean & Sort Timeline Data
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date')
        
        # --- Sidebar Layout ---
        st.sidebar.markdown("### :material/calendar_month: Filter by Date Range")
        time_filter = st.sidebar.selectbox(
            "Select Range",
            ["All Time", "Today", "Last 7 Days", "Last 30 Days"],
            label_visibility="collapsed"
        )
        
        # --- Process Time Logic ---
        now = pd.Timestamp.now().normalize()
        if time_filter == "Today":
            df = df[df['date'] == now]
        elif time_filter == "Last 7 Days":
            df = df[df['date'] >= now - pd.Timedelta(days=7)]
        elif time_filter == "Last 30 Days":
            df = df[df['date'] >= now - pd.Timedelta(days=30)]
            
        csv_data = df.to_csv(index=False).encode('utf-8')
        
        st.sidebar.divider() # Only keep ONE divider to separate filters from admin tools
        
        with st.sidebar.expander(":material/build: Advanced Admin Tools"):
            st.warning("This action is permanent and will wipe all historical records.")
            confirm_text = st.text_input("Type 'PURGE' to enable the reset button", "")
            if st.button(":material/warning: Permanently Wipe Ledger", type="primary", disabled=(confirm_text != "PURGE")):
                db.reference('/ledger').delete()
                st.success("Ledger has been completely reset.")
                st.rerun()

        # Setting date as the index allows native Streamlit charts to automatically parse identical timelines accurately
        df.set_index('date', inplace=True)

    # Output Visualizations
    lifetime_savings = df['estimated_savings_PKR'].sum() if 'estimated_savings_PKR' in df.columns else 0.0
    total_fuel = df['fuel_consumed_L'].sum() if 'fuel_consumed_L' in df.columns else 0.0
    
    # --- TOP LEVEL KPIs ---
    # Using gap="large" ensures vertical alignment with the charts below
    kpi_col1, kpi_col2 = st.columns(2, gap="large")
    
    with kpi_col1:
        # Wraps the metric in a sleek, equal-width bordered card
        with st.container(border=True):
            st.metric(
                label=":material/emoji_events: Lifetime Savings Generated", 
                value=f"Rs. {lifetime_savings:,.2f}"
            )
            
    with kpi_col2:
        with st.container(border=True):
            st.metric(
                label=":material/local_gas_station: Total Fuel Consumed", 
                value=f"{total_fuel:,.2f} Litres"
            )
    st.divider()
    
    # --- PREMIUM PLOTLY CHARTS ---
    # Prepare data for plotting (resetting index and formatting date)
    df_plot = df.reset_index()
    if 'date' in df_plot.columns:
        df_plot['clean_date'] = df_plot['date'].dt.strftime('%b %d, %I:%M %p')
    else:
        df_plot['clean_date'] = "N/A"

    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("### Cumulative Savings Trend (PKR)")
        # Inject Stakeholder Context
        st.caption("Tracks the total estimated cost savings generated by the routing algorithm. An upward trend indicates compounding financial ROI.")
        # Emerald Green Area Chart for Money/Savings
        fig_savings = px.area(
            df_plot, 
            x='clean_date', 
            y='estimated_savings_PKR' if 'estimated_savings_PKR' in df_plot.columns else None,
            color_discrete_sequence=['#10B981'] 
        )
        fig_savings.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title=None,
            yaxis_title=None,
            # Added type='category' to space data evenly
            xaxis=dict(showgrid=False, fixedrange=True, type='category'),
            yaxis=dict(showgrid=True, gridcolor='#E5E7EB', fixedrange=True),
            hovermode="x unified"
        )
        # Make the fill semi-transparent so it looks modern, not like a solid brick
        if 'estimated_savings_PKR' in df_plot.columns:
            fig_savings.update_traces(
                fillcolor='rgba(16, 185, 129, 0.2)', 
                line=dict(width=4, color='#10B981')
            )
            
        st.plotly_chart(fig_savings, use_container_width=True, config={'displayModeBar': False})

    with col2:
        st.markdown("### Daily Fuel Consumption (Litres)")
        # Inject Stakeholder Context
        st.caption("Monitors the total fuel burned across the active fleet. Consistent or dropping levels indicate optimal route compliance and efficiency.")
        # Sleek Blue Bar Chart for Fuel/Operations
        fig_fuel = px.bar(
            df_plot, 
            x='clean_date', 
            y='fuel_consumed_L' if 'fuel_consumed_L' in df_plot.columns else None,
            color_discrete_sequence=['#3B82F6'] 
        )
        fig_fuel.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title=None,
            yaxis_title=None,
            # Added type='category' to fix skinny bars
            xaxis=dict(showgrid=False, fixedrange=True, type='category'),
            yaxis=dict(showgrid=True, gridcolor='#E5E7EB', fixedrange=True),
            hovermode="x unified"
        )
        st.plotly_chart(fig_fuel, use_container_width=True, config={'displayModeBar': False})
            
    st.divider()
    # --- Responsive Table Header & Export Button ---
    # col1 takes up 70% width (for the title), col2 takes 30% (for the button)
    header_col1, header_col2 = st.columns([7, 3], vertical_alignment="bottom")
    
    with header_col1:
        st.markdown("### Access Raw Ledger Data")
        
    with header_col2:
        # use_container_width=True is the secret to mobile responsiveness. 
        # It fills the 30% column on desktop, and spans 100% width when stacked on mobile.
        st.download_button(
            label=":material/download: Export Data to CSV",
            data=csv_data, 
            file_name="fleet_ledger_export.csv",
            mime="text/csv",
            use_container_width=True
        )
    st.dataframe(df.reset_index())

st.write("")
st.write("")
# --- REMOVE DEAD SPACE AT BOTTOM ---
st.markdown("""
    <style>
    /* Nuke the default Streamlit bottom padding */
    .block-container {
        padding-bottom: 0rem !important;
    }
    /* Completely remove the native Streamlit footer */
    footer {
        display: none !important;
    }
    /* Optional: tighten up the padding below the custom footer */
    div[data-testid="stVerticalBlock"] > div:last-child {
        padding-bottom: 1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

st.divider() # Native full-width line

st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <div style="text-align: center; padding-bottom: 20px;">
        <div style="font-size: 1.5rem; margin-bottom: 15px;">
            <a href="https://github.com/Irfan-code-cloud" target="_blank" style="color: #333333; margin: 0 15px; text-decoration: none; transition: opacity 0.3s;" onmouseover="this.style.opacity='0.7'" onmouseout="this.style.opacity='1'">
                <i class="fab fa-github"></i>
            </a>
            <a href="https://www.linkedin.com/in/irfan-khattak-00b847251" target="_blank" style="color: #0077B5; margin: 0 15px; text-decoration: none; transition: opacity 0.3s;" onmouseover="this.style.opacity='0.7'" onmouseout="this.style.opacity='1'">
                <i class="fab fa-linkedin"></i>
            </a>
            <a href="mailto:ifnkhattak@outlook.com" style="color: #D14836; margin: 0 15px; text-decoration: none; transition: opacity 0.3s;" onmouseover="this.style.opacity='0.7'" onmouseout="this.style.opacity='1'">
                <i class="fas fa-envelope"></i>
            </a>
        </div>
        <p style="font-size: 14px; color: #6B7280; margin-top: 12px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            Engineered by <b>Irfan Khattak</b> &nbsp;|&nbsp; &copy; 2026 All Rights Reserved
        </p>
    </div>
""", unsafe_allow_html=True)
