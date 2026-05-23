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

## Risk Scoring Logic

The supply chain risk module uses rule-based and interpretable risk scoring. The overall risk score is calculated from four main components: late delivery rate, inventory risk, delay risk, and demand volatility risk.

Inventory risk is calculated as a weighted inventory status ratio. Critical inventory items are treated as full-risk items, while warning inventory items are treated as half-risk items:

```text
Inventory Risk = ((Critical Items x 1.0) + (Warning Items x 0.5)) / Total Inventory Items x 100
```

Delay risk is calculated by normalizing the average delay days. In this prototype, an average delay of three days or more is treated as the maximum delay risk:

```text
Delay Risk = min((Average Delay Days / 3) x 100, 100)
```

The overall supply chain risk score is calculated as:

```text
Overall Risk Score =
0.35 x Late Delivery Rate
+ 0.25 x Inventory Risk
+ 0.20 x Delay Risk
+ 0.20 x Demand Volatility Risk
```

Regional and category-level risk tables use related operational indicators such as late delivery rate, delay days, profit risk, and inventory condition. These scores are intended to support decision-making and are not machine-learning-based predictions.

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

```text
supply-chain-visibility-risk-dashboard/
â”‚
â”œâ”€â”€ Overview.py
â”œâ”€â”€ process_data.py
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ run_dashboard.bat
â”œâ”€â”€ README.md
â”‚
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ raw/
â”‚   â”‚   â”œâ”€â”€ DataCoSupplyChainDataset.csv
â”‚   â”‚   â””â”€â”€ DescriptionDataCoSupplyChain.csv
â”‚   â”‚
â”‚   â””â”€â”€ processed/
â”‚       â”œâ”€â”€ orders_clean.csv
â”‚       â”œâ”€â”€ products_clean.csv
â”‚       â”œâ”€â”€ shipments_clean.csv
â”‚       â”œâ”€â”€ inventory_generated.csv
â”‚       â”œâ”€â”€ demand_clean.csv
â”‚       â”œâ”€â”€ risk_scores.csv
â”‚       â””â”€â”€ supply_chain.db
â”‚
â”œâ”€â”€ pages/
â”‚   â”œâ”€â”€ 1_Regional_Performance.py
â”‚   â”œâ”€â”€ 2_Inventory_Control.py
â”‚   â”œâ”€â”€ 3_Shipment_Performance.py
â”‚   â”œâ”€â”€ 4_Supply_Chain_Risk.py
â”‚   â””â”€â”€ 5_Demand_Forecast.py
â”‚
â”œâ”€â”€ utils/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â””â”€â”€ data_adapter.py
â”‚
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ er_diagram.png
â”‚   â”œâ”€â”€ system_architecture.png
â”‚   â”œâ”€â”€ use_case_diagram.png
â”‚   â””â”€â”€ graduation_thesis_report.docx
â”‚
â””â”€â”€ screenshots/
    â”œâ”€â”€ 01_data_source_manager.png
    â”œâ”€â”€ 02_overview_uploaded_dataset.png
    â”œâ”€â”€ 03_regional_performance_uploaded.png
    â”œâ”€â”€ 04_inventory_control_uploaded.png
    â”œâ”€â”€ 05_shipment_performance_uploaded.png
    â”œâ”€â”€ 06_supply_chain_risk_uploaded.png
    â””â”€â”€ 07_demand_forecast_uploaded.png
```

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
