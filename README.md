# 🎫 Smart Support Desk

An intelligent internal support tool for SaaS companies, featuring a
**FastAPI backend**, **Streamlit frontend**, and an **AI-powered CRM
Assistant**.\
This system handles ticket management, customer support, and automates
CRM tasks using LLMs (LangChain + Groq/Gemini) with two-way HubSpot
synchronization.

------------------------------------------------------------------------

## 🚀 Features

### 🌟 Core Functionality

-   **Role-Based Access Control (RBAC):** Distinct dashboards and
    permissions for Admins, Agents, Service Persons, and Customers.
-   **Ticket Management:** Complete lifecycle management (Open → In
    Progress → Close) with priority levels (Low, Medium, High).
-   **HubSpot Integration:**
    -   **Two-Way Sync:** Automatically syncs customers and tickets
        between the local database and HubSpot CRM.
    -   **HubSpot Actions:** Create, update, and delete contacts/tickets
        directly from the app.

------------------------------------------------------------------------

## 🤖 AI CRM Assistant

-   **Natural Language Actions:** Chat with the AI to fetch tickets,
    find customer details, or create new tickets without navigating
    menus.
-   **Intelligent Routing:** The AI determines whether to query the
    database, call the HubSpot API, or perform an action based on user
    intent.
-   **Analytics:** Ask questions like *"How many high priority tickets
    are open?"* to get instant visual analytics.

------------------------------------------------------------------------

## 📊 Dashboards

-   **Admin/Agent Dashboard:** Overview of total tickets, status
    distribution (charts), and service person workload.
-   **Service Person Dashboard:** Focused view of assigned tickets only.
-   **Customer Dashboard:** Portal for customers to view their ticket
    history, status, and chat with support agents.

------------------------------------------------------------------------

## 🛠️ Tech Stack

### Backend

-   **Framework:** FastAPI
-   **Language:** Python 3.10
-   **Database:**
    -   MySQL: Primary relational data (Customers, Employees, Tickets).
    -   MongoDB: Chat logs and AI session history.
    -   Redis: Session management and JWT token caching.
-   **AI/LLM:** LangChain, Google Gemini, Groq (Qwen/Moonshot).
-   **Authentication:** OAuth2 with JWT (JSON Web Tokens).

### Frontend

-   **Framework:** Streamlit
-   **Visualization:** Plotly (for analytics charts).
-   **Styling:** Custom CSS injection for a modern UI.

------------------------------------------------------------------------

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

``` bash
git clone https://github.com/dharmikmodi-turabit/Smart_Support_Desk
cd smart_support_desk
```

------------------------------------------------------------------------

### 2️⃣ Environment Configuration

Create a `.env` file in the root directory:

``` ini
# Database Config
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=root
DB_NAME=smart_support_desk
MONGO_URI=mongodb://localhost:27017/ai_crm_chat_db
REDIS_HOST=localhost

# Security
SECRET_KEY=YOUR_SUPER_SECRET_KEY
ALGORITHM=HS256

# API Keys
HUBSPOT_TOKEN=your_hubspot_access_token
GEMINI_API_KEY=your_google_gemini_key
GROK_API_KEY=your_groq_api_key
```

------------------------------------------------------------------------

### 3️⃣ Database Initialization

1.  Log in to your MySQL server.
2.  Run the SQL script located at: ```backend/database/sql_queries.sql```

This will create the required tables and triggers.

------------------------------------------------------------------------

### 4️⃣ Local Installation (Without Docker)

**Prerequisites:**\
Python 3.10+, MySQL, Redis, MongoDB installed locally.

#### Create a virtual environment

``` bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install dependencies

``` bash
pip install -r requirements.txt
```

#### Run the Backend

``` bash
uvicorn backend.main:app --reload --port 8000
```

#### Run the Frontend

``` bash
streamlit run frontend/app.py --server.port 8501
```

------------------------------------------------------------------------

## 📖 Usage Guide

### 🔗 Access Points

-   **Frontend UI:** http://localhost:8501\
-   **Backend API Docs:** http://localhost:8000/docs (Swagger UI)

------------------------------------------------------------------------

### 🔐 Default Credentials

-   **Admin:** admin@gmail.com / admin123\
-   **Agent:** agent1@gmail.com / agent123\
-   **Service Person:** service1@gmail.com / service123\
-   **Customer:** rahul@gmail.com (Login via OTP/Email simulation)

------------------------------------------------------------------------

## 📂 Project Structure

    Smart_Support_Desk/
    ├── backend/
    │   ├── AI/                 # AI Chatbot logic & Tools (LangChain)
    │   ├── Authentication/     # JWT Auth & Redis dependencies
    │   ├── Hubspot/            # HubSpot API integration logic
    │   ├── database/           # DB connection & SQL schema
    │   ├── routes/             # API Endpoints (Customer, Employee, Ticket)
    │   └── main.py             # FastAPI entry point
    ├── frontend/
    │   ├── views/              # UI Pages (Dashboard, Ticket, Chat, etc.)
    │   ├── utils/              # API helpers & Auth handling
    │   └── app.py              # Streamlit entry point
    ├── requirements.txt        # Python dependencies
    └── README.md               # Project documentation

------------------------------------------------------------------------

## ✨ Summary

Smart Support Desk combines AI-powered automation, CRM synchronization,
and modern full-stack architecture to streamline internal support
operations for SaaS companies.
