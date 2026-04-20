import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# --- LOGIN PAGE UI & HEADER (ONLY SHOW IF NOT LOGGED IN) ---
if not st.session_state.get("authentication_status"):
    
   # 1. Apply the narrow CSS ONLY to the login screen
    st.markdown("""
        <style>
        .block-container {
            padding-top: 0 !important;
            padding-bottom: 1rem !important;
            max-width: 650px !important; 
        }
        footer {
            display: none !important;
        }
        
        /* Mobile Viewport Overrides for Login Screen */
        @media screen and (max-width: 768px) {
            /* Shrink the Main Title */
            div[data-testid="stMarkdownContainer"] h1 {
                font-size: 1.6rem !important;
                margin-bottom: 0.5rem !important;
                line-height: 1.2 !important;
            }
            /* Shrink the "Institutional Access Required" Subheading */
            div[data-testid="stMarkdownContainer"] h3 {
                font-size: 1.15rem !important;
                margin-bottom: 0.5rem !important;
            }
            /* Shrink the paragraph text slightly */
            div[data-testid="stMarkdownContainer"] p {
                font-size: 0.9rem !important;
                line-height: 1.4 !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)

# --- AUTH CONFIGURATION ---
# In a real app, store these in a secret config or database. 
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
        # This dynamically pulls your hidden key from the vault
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

# --- LOGIN PAGE HEADER (ONLY SHOW IF NOT LOGGED IN) ---
if not st.session_state.get("authentication_status"):
    st.title("Karachi Fleet Optimizer")
    st.markdown("""
    ### Institutional Access Required
    Welcome to the Karachi Fleet Optimizer ERP. This system is for authorized personnel only. 
    Please use your credentials to securely access your dedicated portal.
    """)
    st.divider()

# --- LOGIN SCREEN ---
authenticator.login()

if st.session_state.get("authentication_status"):
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

elif st.session_state.get("authentication_status") is False:
    st.error('Username/password is incorrect')
elif st.session_state.get("authentication_status") is None:
    st.warning('Please enter your username and password')

if not st.session_state.get("authentication_status"):
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