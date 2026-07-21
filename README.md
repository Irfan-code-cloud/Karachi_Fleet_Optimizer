# 🚚 Karachi Fleet Optimizer: AI-Powered Logistics ERP

**Live Demo:** [Click here to launch the application](https://karachi-fleet-optimizer-521715121219.us-central1.run.app)

**Demo Access:** `Username: exec_user` | `Password: Fleet@admin2026`

> ⚠️ **Platform Notice:** To optimize cloud resources, this application pauses after periods of inactivity. **Please allow roughly 15 seconds for the engine to cold-boot and wake up upon your first visit.**

An enterprise-grade, role-based logistics ERP engineered to mathematically optimize delivery routes and financially audit operations across the sprawling, high-density metropolis of Karachi. Built with Python and deployed on Google Cloud Run, it leverages Google OR-Tools for routing and Google Vertex AI for real-time financial telemetry, significantly reducing daily fuel consumption and operational overhead.

## 🛑 The Urban Logistics Problem
Logistics operations in chaotic urban environments frequently suffer from severe routing inefficiencies. Manual dispatching leads to overlapping vehicle paths, backtracking, and a failure to meet strict delivery time windows. This results in inflated fuel consumption, excessive vehicle wear-and-tear, unpredicted driver overtime, and ultimately, massive bleeds in capital.

## 💡 The Mathematical & AI Solution
The Karachi Fleet Optimizer removes human guesswork through a dual-engine approach:
1. **Mathematical Optimization:** Formulates daily dispatching as a **Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)**. The engine ingests daily demand data, respects strict vehicle weight capacities, and calculates the absolute minimal-distance routes.
2. **AI Financial Auditing:** Acts as a digital CFO. It translates operational telemetry into financial insights, calculating exact fuel costs and estimated capital savings in real-time.

Coupled with a Role-Based Access Control (RBAC) portal, it provides real-time tracking, live Proof of Delivery (POD) updates, and instant ROI analytics for executive management.

## 🤖 AI Route Efficiency Audit (Powered by Google Vertex AI)
To move beyond simple distance calculation, this platform integrates **Google Vertex AI** to conduct automated, natural-language operational audits. 

By feeding the mathematical output of the OR-Tools engine into an advanced Large Language Model, the system generates a daily executive summary. The AI evaluates the optimized fuel costs against baseline metrics, predicts potential overtime expenditures based on Karachi's traffic patterns, and delivers actionable financial insights directly to the manager's dashboard. This bridges the gap between raw data and executive decision-making.

## 🧠 Architecture: Why OSRM?
For the routing engine's distance matrix, **OSRM (Open Source Routing Machine)** was selected over alternative commercial APIs for critical reasons:
1. **Real-World Street Networks:** Unlike straight-line Haversine math, OSRM routes along actual drivable roads, accounting for one-way streets, intersections, and road hierarchy.
2. **Cost & Scalability:** Commercial APIs charge heavily per call. OSRM allows the application to scale to hundreds of daily stops without triggering massive cloud billing overhead.
3. **Fault Tolerance:** The system features a built-in Haversine fallback matrix. If the public OSRM node experiences downtime, the algorithm gracefully degrades to coordinate-based math, ensuring dispatching never halts.

## 🌟 Key Features
* **AI Financial Auditing:** Vertex AI-driven insights analyzing route ROI and operational telemetry.
* **Algorithmic Routing:** Google OR-Tools engine optimizing for distance, vehicle capacity, and time windows.
* **Role-Based Access Control:** Mathematically hashed (bcrypt) authentication with distinct views for Executives, Managers, and Drivers.
* **Real-Time Cloud Sync:** Firebase Realtime Database integration for live delivery tracking and persistent session states.
* **Interactive Mapping:** Folium-based dynamic maps rendering polyline routes, custom markers, and HTML status tooltips.

## 📊 Data Schema: Bring Your Own Fleet
To make this platform adaptable for any logistics department, the optimization engine is built to ingest a standardized, lightweight dataset. If your company can export these basic data points from your current CRM, Shopify, or order management system, you can plug them directly into the Karachi Fleet Optimizer to immediately start reducing fuel costs.

**Raw CSV Data**
<img width="805" height="461" alt="Lat_and_Lan_raw_data" src="https://github.com/user-attachments/assets/8bf9368a-b940-49d7-a804-ad04e65d33b9" />

The application parses a standard tabular dataset (CSV/Excel) representing the daily delivery manifest. Here is the required schema:

* `Stop_ID` & `Location_Name`: Unique identifiers for the main distribution hub (Depot) and each customer drop-off location.
* `Latitude` & `Longitude`: Exact GPS coordinates. These are fed directly into the OSRM engine to calculate real-world street distances and traffic directions, rather than simple straight-line math.
* `Demand_KG`: The physical weight (or volume) of the delivery. The algorithm uses this to mathematically ensure no assigned truck ever exceeds its maximum payload capacity.
* `Service_Time_Mins`: The estimated time required for the driver to park, unload the cargo, and collect the Proof of Delivery (POD). This prevents the engine from generating physically impossible schedules.
* `Open_Time` & `Close_Time`: The strict time windows (e.g., 09:00 to 17:00) during which the customer can accept the delivery. The OR-Tools engine acts on these constraints to avoid early arrivals or missed deliveries.

## 📖 Platform User Guide (Role-Based Workflows)

This application is compartmentalized into three distinct portals to ensure data security and operational focus. Use the demo credentials provided at the top of this document to explore the system.

### 1. Manager Dashboard (Dispatch & Operations)
The nerve center for daily logistics. Managers use this portal to transform raw demand into actionable dispatch orders.
* **Route Generation:** Ingest daily delivery nodes and vehicle capacity limits. The system triggers OR-Tools and OSRM to mathematically calculate the most efficient path.
* **Live Fleet Tracking:** Monitor the active geographic visualization of all assigned trucks on an interactive map.
* **AI Route Efficiency Audit:** Trigger the Vertex AI agent to analyze the generated routes, instantly calculating estimated fuel costs and highlighting total capital saved versus unoptimized routing.

<img width="1366" height="2687" alt="manager_dashboard" src="https://github.com/user-attachments/assets/0f1c8659-80d2-4f92-b9ca-6bf9993a98d0" />

---

### 2. Driver Portal (Field Execution)
Designed for mobile responsiveness, this portal provides drivers with exact, distraction-free execution steps while on the road.
* **Route Briefing:** Drivers select their assigned vehicle and receive their mathematically optimized sequence of stops.
* **Real-Time AI Traffic Intel:** At any stop, drivers can trigger a Vertex AI localized prompt that pulls current Karachi standard time to generate hyper-specific warnings about current bottlenecks and safety hazards for that exact neighborhood.
* **Proof of Delivery (POD):** Drivers mark stops as completed, which instantly updates the global Firebase database, removing the stop from the Manager's pending map.

<img width="1366" height="2163" alt="driver_portal" src="https://github.com/user-attachments/assets/d55fdcb8-a1ad-45f6-b7b4-7bd4c1856d3d" />

---

### 3. Executive Analytics (High-Level ROI)
A high-level, read-only dashboard designed for upper management and stakeholders.
* **Financial Overview:** View top-down metrics on total system efficiency, historical fuel consumption, and capital actively recovered by the optimization engine.
* **Operational Telemetry:** Analyze overall fleet utilization and performance bottlenecks without getting bogged down in individual node or street-level data.

<img width="1366" height="1634" alt="executive_analytics" src="https://github.com/user-attachments/assets/b7c5c684-322d-4450-a10d-fc46139eb6e2" />

## 🛠️ Enterprise Tech Stack
* **Cloud Infrastructure:** Google Cloud Run (Serverless Docker Container), Google Secret Manager
* **AI & Optimization:** Google Vertex AI, Google OR-Tools, OSRM API
* **Backend / Database:** Python, Firebase Realtime Database
* **Frontend:** Streamlit, Plotly, Folium
* **Security:** `streamlit-authenticator`

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

GCP_SERVICE_ACCOUNT_JSON = '''
{
  "type": "service_account",
  "project_id": "your-gcp-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account-email",
  "client_id": "your-client-id",
  "auth_uri": "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)",
  "token_uri": "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)",
  "auth_provider_x509_cert_url": "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)",
  "client_x509_cert_url": "your-cert-url",
  "universe_domain": "googleapis.com"
}
'''

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
*Engineered by Irfan Khattak | Developed for AI Seekho 2026*
