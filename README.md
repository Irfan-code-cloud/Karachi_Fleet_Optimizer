# 🚚 Karachi Fleet Optimizer (ERP)

**Live Demo:** [Click here to launch the application](https://karachifleetoptimizer-hqthjtkx8gcl2g9df4k5ne.streamlit.app/)

An enterprise-grade, role-based logistics ERP designed to mathematically optimize delivery routes across the sprawling metropolis of Karachi. Built with Python and Streamlit, it leverages Google OR-Tools and OSRM to minimize total fleet distance, significantly reducing daily fuel consumption and operational costs.

## 🛑 The Problem
Logistics operations in high-density urban environments like Karachi frequently suffer from inefficient routing. Manual dispatching leads to overlapping vehicle paths, backtracking, and failure to meet strict delivery time windows. This results in inflated fuel consumption, excessive vehicle wear-and-tear, unpredicted driver overtime, and ultimately, massive losses in capital.

## 💡 The Solution
The Karachi Fleet Optimizer tackles this by removing human guesswork. It formulates daily dispatching as a **Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)**. The engine ingests daily demand data, respects strict vehicle weight capacities, and mathematically calculates the absolute minimal-distance routes. Coupled with a Role-Based Access Control (RBAC) portal, it provides real-time telemetry, live Proof of Delivery (POD) tracking, and instant ROI analytics for management.

## 🧠 Architecture: Why OSRM?
For the routing engine's distance matrix, **OSRM (Open Source Routing Machine)** was selected over alternative commercial APIs (like Google Maps Distance Matrix) or pure Euclidean/Haversine calculations for several critical reasons:
1. **Real-World Street Networks:** Unlike straight-line Haversine math, OSRM routes along actual drivable roads, accounting for one-way streets, intersections, and road hierarchy.
2. **Cost & Scalability:** Commercial APIs charge heavily per API call. OSRM is open-source and free, allowing the application to scale to hundreds of daily stops without triggering massive cloud billing overhead.
3. **Fault Tolerance:** The system is engineered with a built-in Haversine fallback matrix. If the public OSRM node experiences downtime, the algorithm gracefully degrades to coordinate-based math, ensuring dispatching is never halted.

---

## 🌟 Key Features
* **Algorithmic Routing:** Google OR-Tools engine optimizing for distance, capacity, and time.
* **Role-Based Access Control:** Mathematically hashed (bcrypt) authentication with distinct views for Admins, Managers, and Drivers.
* **Real-Time Cloud Sync:** Firebase Realtime Database integration for live delivery tracking and persistent session states.
* **Interactive Mapping:** Folium-based dynamic maps rendering polyline routes, custom markers, and HTML status tooltips.

## 🛠️ Tech Stack
* **Frontend:** Streamlit, Plotly, Folium
* **Backend:** Python
* **Optimization:** Google OR-Tools, OSRM API, Haversine Distance
* **Database:** Firebase Realtime Database
* **Security:** `streamlit-authenticator`, Streamlit Secrets Management

---

## 💻 Local Development Setup

Want to run this project locally or build upon it? Follow these steps:

### 1. Clone the Repository
    git clone https://github.com/Irfan-code-cloud/Karachi_Fleet_Optimizer.git
    cd Karachi_Fleet_Optimizer

### 2. Install Dependencies
Ensure you have Python 3.9+ installed. Install the required packages:

    pip install -r requirements.txt

### 3. Setup Environment Variables (Secrets)
This project uses Streamlit Secrets and Firebase. You must provide your own credentials.
1. Create a hidden folder and file at the root of the project: `.streamlit/secrets.toml`
2. Add your custom session cookie key and Firebase Service Account credentials:

```toml
cookie_key = "your_custom_random_string_here"

[firebase]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account-email"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "your-cert-url"
universe_domain = "googleapis.com"
```

### 4. Run the Application

    streamlit run app.py

---
Best, Irfan Khattak