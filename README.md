# Supply Chain Visibility and Risk Assessment Platform

This project is an interactive supply chain visibility and risk assessment platform. It allows users to work with the default DataCo supply chain dataset or upload their own supply chain dataset through a column mapping and standardization module.

After a dataset is uploaded and mapped to the standard schema, the dashboard modules are dynamically generated based on the active dataset. The system provides operational KPIs, regional performance analysis, inventory control indicators, shipment performance analysis, supply chain risk scoring, and demand forecasting.

## Project Objective

The main objective of this project is to develop a reusable decision-support platform for supply chain visibility and operational risk assessment.

The system is designed to answer the following questions:

- How can raw supply chain datasets be transformed into dashboard-ready analytical tables?
- How can users upload a new supply chain dataset and map it to a standard schema?
- What are the key delivery, shipment, inventory, regional, and demand-related risks?
- Which markets, regions, shipment modes, or product categories create higher operational risk?
- How can supply chain managers monitor performance and risk indicators from a single interface?

The default DataCo dataset is used as a demonstration dataset. However, the system is not limited to this dataset. Users can upload their own CSV or Excel supply chain dataset, map its columns, and generate dashboard modules based on the uploaded data.

## Dataset

This project uses the public **DataCo Smart Supply Chain Dataset** from Kaggle as the main operational data source.

The raw dataset includes order, product, customer, shipping, delivery, sales, and profit-related information.

Since the original dataset does not include complete inventory planning fields, additional inventory-related indicators such as current stock, reorder point, safety stock, days of supply, and inventory status were generated from product demand patterns for academic demonstration purposes.

## Dataset Upload and Standardization

The platform includes a Data Source Manager that allows users to upload a new supply chain dataset in CSV or Excel format.

The uploaded dataset is mapped to the following standard schema:

- order_id
- order_date
- product_name
- category_name
- order_quantity
- shipping_date
- scheduled_delivery_date
- delivery_status
- actual_shipping_days
- scheduled_shipping_days
- shipping_mode
- market
- order_region
- order_country
- sales
- order_profit

Required fields must be mapped by the user. Optional fields improve the quality of the generated dashboard and risk analysis. If some optional fields are missing, the system fills them with default values or derives indicators where possible.

After mapping, the system converts the uploaded dataset into dashboard-ready analytical tables. These tables are then used across all dashboard modules.

## Main Features

The current version includes:

- Default DataCo supply chain dataset support
- User-uploaded CSV/XLSX dataset support
- Column mapping to a standard supply chain schema
- Automatic data standardization
- Dynamic dashboard generation based on the active dataset
- Executive overview dashboard
- Regional performance analysis
- Inventory control dashboard
- Shipment performance dashboard
- Supply chain risk analysis dashboard
- Demand forecasting dashboard
- Total order, sales, quantity, and profit KPIs
- On-time and late delivery rate calculation
- Average shipping and delay day calculation
- Monthly order volume analysis
- Delivery status distribution
- Shipping mode performance analysis
- Inventory status classification
- Critical and warning stock detection
- Region-level risk scoring
- Category-level risk scoring
- Overall supply chain risk score
- 3-month moving average demand forecast
- Linear regression demand forecast
- MAE and MAPE forecast evaluation
- Processed CSV tables
- SQLite database generation

## Future Improvements

- Add automatic column detection using more advanced matching logic
- Add support for multiple saved uploaded datasets
- Add database persistence for uploaded datasets
- Add exportable PDF risk reports
- Add more advanced forecasting models
- Add real-time ERP/API integration
- Add user authentication for production use
- Improve risk scoring with machine learning models
- Deploy the dashboard as a web application

## Limitations

- The default DataCo dataset is a public historical dataset and does not represent a specific company's current operations.
- The quality of dashboard outputs depends on the completeness and structure of the uploaded dataset.
- Uploaded datasets must be mapped manually to the standard schema.
- Some indicators are generated when the uploaded dataset does not contain complete inventory or risk-related fields.
- Inventory planning fields such as reorder point, safety stock, and days of supply are generated for dashboard demonstration purposes.
- The current version does not include real-time ERP or API integration.
- Risk scores are rule-based and interpretable, not machine-learning-based predictions.
- Forecasting uses simple models such as moving average and linear regression.

## Technologies Used

- Python
- Streamlit
- pandas
- numpy
- Plotly
- SQLite
- scikit-learn

## How to Run the Project

### Quick Start for Windows

The easiest way to run the project on Windows is to double-click:

```text
run_dashboard.bat
```

This script automatically:

- creates the virtual environment if it does not exist,
- installs the required Python packages,
- processes the default dataset if needed,
- starts the Streamlit dashboard.

After the dashboard opens, users can either use the default DataCo dataset or upload a new supply chain dataset from the **Data Source Manager** on the Overview page.

---

### Manual Setup

If you prefer to run the project manually, follow the steps below.

### 1. Clone the repository

```bash
git clone https://github.com/dolunayunlu/supply-chain-visibility-risk-dashboard.git
```

### 2. Go to the project folder

```bash
cd supply-chain-visibility-risk-dashboard
```

### 3. Create and activate a virtual environment

```bash
python -m venv venv
```

For Windows PowerShell:

```bash
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run:

```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the virtual environment again:

```bash
.\venv\Scripts\Activate.ps1
```

### 4. Install required packages

```bash
pip install -r requirements.txt
```

### 5. Process the default dataset

```bash
python process_data.py
```

This step creates the cleaned CSV files and SQLite database used by the default dashboard.

### 6. Run the dashboard platform

```bash
streamlit run Overview.py
```

### 7. Use the default dataset or upload a new dataset

When the dashboard opens, the system uses the default DataCo supply chain dataset.

To analyze a new company dataset:

1. Open the **Data Source Manager** on the Overview page.
2. Upload a CSV or Excel supply chain dataset.
3. Map the uploaded dataset columns to the standard schema.
4. Click **Use This Dataset Across Dashboard**.
5. The dashboard pages will update based on the uploaded dataset.

The uploaded dataset is used during the active Streamlit session. Users can return to the default DataCo dataset from the Data Source Manager.

## Project Structure

supply-chain-visibility-risk-dashboard/
│
├── Overview.py
├── process_data.py
├── requirements.txt
├── README.md
│
├── data/
│   ├── raw/
│   │   ├── DataCoSupplyChainDataset.csv
│   │   └── DescriptionDataCoSupplyChain.csv
│   │
│   └── processed/
│       ├── orders_clean.csv
│       ├── products_clean.csv
│       ├── shipments_clean.csv
│       ├── inventory_generated.csv
│       ├── demand_clean.csv
│       ├── risk_scores.csv
│       └── supply_chain.db
│
├── pages/
│   ├── 1_Regional_Performance.py
│   ├── 2_Inventory_Control.py
│   ├── 3_Shipment_Performance.py
│   ├── 4_Supply_Chain_Risk.py
│   └── 5_Demand_Forecast.py
│
├── utils/
│   ├── __init__.py
│   └── data_adapter.py
│
├── docs/
└── screenshots/

## Current Status

The main platform modules are completed.

Completed modules:

- Data Source Manager
- Dataset upload and column mapping
- Dataset standardization
- Overview
- Regional Performance
- Inventory Control
- Shipment Performance
- Supply Chain Risk
- Demand Forecast

The project currently provides a working multi-page Streamlit platform. Users can either use the default DataCo dataset or upload a new company supply chain dataset. The uploaded dataset is standardized and used dynamically across dashboard pages.

## Dashboard Screenshots

The dashboard includes the following pages:

- Overview
- Regional Performance
- Inventory Control
- Shipment Performance
- Supply Chain Risk
- Demand Forecast

Screenshots are available in the `screenshots/` folder.

## Project Diagrams

The project documentation includes:

- ER Diagram
- System Architecture Diagram
- Use Case Diagram

These diagrams are available in the `docs/` folder.