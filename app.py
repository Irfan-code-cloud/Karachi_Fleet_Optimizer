import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# --- AUTH CONFIGURATION ---
hashed_123 = '$2b$12$6pXk0/P.Xn.iB1X.e5v5.uVdYp5f0.m5Gk0.vG5v5.uVdYp5' # Example placeholder

config = {
    'credentials': {
        'usernames': {
            'exec_user': {
                'name': 'Executive Administrator',
                'password': '$2b$12$iMfELIzptWIWsLp9HrRcU.KrU3INj16EC2AR51MdQv1SthMkNjiZa', 
                'role': 'admin'
            },
            'ops_manager': {
                'name': 'Operations Manager',
                'password': '$2b$12$iMfELIzptWIWsLp9HrRcU.KrU3INj16EC2AR51MdQv1SthMkNjiZa', 
                'role': 'manager'
            },
            'driver_01': {
                'name': 'Active Driver 01',
                'password': '$2b$12$iMfELIzptWIWsLp9HrRcU.KrU3INj16EC2AR51MdQv1SthMkNjiZa', 
                'role': 'driver'
            },
            'driver_02': {
                'name': 'Active Driver 02',
                'password': '$2b$12$iMfELIzptWIWsLp9HrRcU.KrU3INj16EC2AR51MdQv1SthMkNjiZa',
                'role': 'driver'
            },
            'driver_03': {
                'name': 'Active Driver 03',
                'password': '$2b$12$iMfELIzptWIWsLp9HrRcU.KrU3INj16EC2AR51MdQv1SthMkNjiZa',
                'role': 'driver'
            },
            'driver_04': {
                'name': 'Active Driver 04',
                'password': '$2b$12$iMfELIzptWIWsLp9HrRcU.KrU3INj16EC2AR51MdQv1SthMkNjiZa',
                'role': 'driver'
            },
            'driver_05': {
                'name': 'Active Driver 05',
                'password': '$2b$12$iMfELIzptWIWsLp9HrRcU.KrU3INj16EC2AR51MdQv1SthMkNjiZa',
                'role': 'driver'
            },
            'driver_06': {
                'name': 'Active Driver 06',
                'password': '$2b$12$iMfELIzptWIWsLp9HrRcU.KrU3INj16EC2AR51MdQv1SthMkNjiZa',
                'role': 'driver'
            }
        }
    },
    'cookie': {
        'expiry_days': 30,
        'key': st.secrets.get("cookie_key", "fallback_local_key_only"), 
        'name': 'kfo_auth_cookie'
    },
    'preauthorized': {
        'emails': []
    }
}

# --- AUTH INITIALIZATION ---
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)
st.session_state["authenticator"] = authenticator

# =====================================================================
# THE MAGIC ERASER CONTAINER (Fixes the ghosting glitch!)
# =====================================================================
login_container = st.empty()

# --- LOGIN PAGE HEADER & UI (ONLY SHOW IF NOT LOGGED IN) ---
if not st.session_state.get("authentication_status"):
    
    # We wrap the ENTIRE login UI and footer inside the eraser container
    with login_container.container():
        st.markdown("""
        <style>
        /* 1. Global Reset & Sidebar Hide */
        [data-testid="collapsedControl"], [data-testid="stSidebar"], [data-testid="stHeader"] { 
            display: none !important; 
        }
        
        /* 2. Desktop Layout (Wide) */
        .block-container { 
            max-width: 1100px !important; 
            padding-top: 5rem !important; 
            padding-bottom: 2rem !important;
        }
        
        /* 3. MOBILE RESPONSIVE OVERRIDES (The Fix) */
        @media screen and (max-width: 768px) {
            .block-container {
                padding-top: 1rem !important;    /* Remove huge top gap */
                padding-bottom: 0rem !important; /* Remove bottom gap */
                max-width: 100% !important;
            }
            
            /* Shrink the massive headline for mobile screens */
            h1 {
                font-size: 2.2rem !important; 
                line-height: 1.2 !important;
                text-align: center !important;
            }
            
            h3 {
                font-size: 1rem !important;
                text-align: center !important;
                margin-bottom: 1.5rem !important;
            }

            /* Reduce padding inside the login card to save screen space */
            [data-testid="stForm"] {
                padding: 1.5rem 1rem !important;
                margin: 0 auto !important;
            }
        }

        /* 4. The Form Card Styling */
        [data-testid="stForm"] {
            border-radius: 12px !important;
            box-shadow: 0px 8px 30px rgba(0, 0, 0, 0.2) !important;
            background-color: var(--secondary-background-color) !important; 
            border: 1px solid rgba(128, 128, 128, 0.3) !important; 
        }
        
        [data-testid="stForm"] h2 { display: none !important; }
            
          /* 6. TRUE FULL-LENGTH MONOCHROME BUTTON */
          /* This targets the wrapper and the button together to force 100% width */
            div.stButton, div.stButton > button {
                width: 100% !important;
                display: block !important;
            }

            div.stButton > button {
                background-color: #1F2937 !important; 
                color: #FFFFFF !important; 
                font-size: 1.1rem !important;
                font-weight: 600 !important;
                padding: 0.75rem !important; 
                border-radius: 8px !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                margin-top: 1.5rem !important;
                transition: all 0.2s ease !important;
            }

            div.stButton > button:hover {
                background-color: #374151 !important;
                border-color: rgba(255, 255, 255, 0.3) !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        left_col, right_col = st.columns([1.2, 1], gap="large", vertical_alignment="center")
        
        with left_col:
            st.markdown("""
                <h1 style='font-size: 3.8rem; line-height: 1.1; margin-bottom: 1rem;'>
                    Optimize your<br>fleet operations.
                </h1>
                <h3 style='font-weight: 400; font-size: 1.3rem; margin-bottom: 2rem; opacity: 0.8;'>
                    Secure Institutional Access for Karachi Fleet Optimizer. Manage routes, track live telemetry, and analyze ROI in real-time.
                </h3>
            """, unsafe_allow_html=True)
            
        with right_col:
            authenticator.login()
        
        # Display the error ONLY inside the login screen
        if st.session_state.get("authentication_status") is False:
            st.error('🚨 Institutional ID or password is incorrect.', icon="🛑")

        # --- DEPLOYMENT FOOTER ---
        st.divider()
        footer_html = """
        <div style="text-align: center; color: gray; font-size: small; padding: 10px;">
            <p>© 2026 FleetLink Solutions (PVT) LTD. All rights reserved.</p>
            <p>
                <a href="https://yourdomain.com/privacy" target="_blank" style="color: gray; text-decoration: none;">Privacy Policy</a> 
                &nbsp; | &nbsp;
                <a href="https://yourdomain.com/terms" target="_blank" style="color: gray; text-decoration: none;">Terms & Conditions</a>
            </p>
            <p style="font-size: x-small;">Unauthorized access is strictly prohibited and subject to legal action under the PECA Act 2016.</p>
        </div>
        """
        st.markdown(footer_html, unsafe_allow_html=True)

        # ==========================================
        # THIS LINE HERE TO FIX THE GHOST GLITCH
        # ==========================================
        st.stop()
        

# =====================================================================
# THE SECURE APP (Only runs if logged in)
# =====================================================================
if st.session_state.get("authentication_status"):
    
    # INSTANTLY VAPORIZE THE LOGIN SCREEN CONTAINER!
    login_container.empty()
    
    # The user is logged in! Grab their details from the session state
    username = st.session_state["username"]
    name = st.session_state["name"]
    
    # --- ROLE BASED NAVIGATION ---
    user_role = config['credentials']['usernames'][username].get('role', 'driver')
    
    # --- SESSION ISOLATION INJECTION ---
    st.session_state["role"] = user_role
    
    # Dynamically assign trucks based on username (e.g., 'driver_04' -> 'Truck 4')
    if user_role == 'driver':
        try:
            # Extract the number from 'driver_XX' and format it as 'Truck X'
            driver_num = int(username.split('_')[1])
            st.session_state["assigned_truck"] = f"Truck {driver_num}"
        except (IndexError, ValueError):
            # Fallback just in case
            st.session_state["assigned_truck"] = "Truck 1"
    else:
        st.session_state["assigned_truck"] = "All" # For managers/admins
    
    # Define Pages
    analytics_page = st.Page("views/Executive_Analytics.py", title="Executive Analytics", icon=":material/show_chart:")
    dashboard_page = st.Page("views/Manager_Dashboard.py", title="Manager Dashboard", icon=":material/dashboard:")
    driver_page = st.Page("views/Driver_App.py", title="Driver Portal", icon=":material/near_me:")
    
    # Restrict Pages based on Role
    if user_role == 'admin':
        pages = [analytics_page, dashboard_page, driver_page]
    elif user_role == 'manager':
        pages = [dashboard_page, driver_page]
    else:
        pages = [driver_page]
    
    # Render Navigation
    pg = st.navigation(pages)
    
    # Add Logout to Sidebar
    st.sidebar.markdown(f"**Logged in as:** {name}")
    authenticator.logout("Logout", "sidebar")
    
    # Run the Page
    pg.run()