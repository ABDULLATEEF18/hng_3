 
 HELLO WELCOME TO COUNTRiES API.
 # 🌍 Country Currency & Exchange API

A RESTful API that fetches country data from the [REST Countries API](https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies) and exchange rates from the [Open Exchange Rates API](https://open.er-api.com/v6/latest/USD).  
It stores the data in a PostgreSQL database and provides endpoints for querying and refreshing country information.

---

## 🚀 Features
- Fetch and store country details with currency and exchange rate data  
- Compute estimated GDP based on population and exchange rate  
- Auto-refresh database with up-to-date info  
- Retrieve country details or all countries  
- PostgreSQL connection pooling for performance  

---

## 🛠️ Tech Stack
- **Python 3.10+**
- **Flask** – REST API framework  
- **PostgreSQL** – Database  
- **psycopg2** – PostgreSQL adapter  
- **requests** – API data fetching  

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/country-exchange-api.git
cd country-exchange-api


CREATE VIRTUAL ENVIRONMENTS

python -m venv .venv
source .venv/bin/activate  # for macOS/Linux
.venv\Scripts\activate     # for Windows

INSTALL DEPENDENCIES
     pip install -r requirements.txt

SET ENVIRONMENT VARIABLES
DB_HOST=your-db-host
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME=your-db-name
DB_PORT=your-db-port
DATABASE_URL=postgresql://user:password@host:port/dbname?sslmode=require

RUN THE APP
flask run
