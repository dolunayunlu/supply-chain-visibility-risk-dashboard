# Supply Chain Visibility and Risk Dashboard

This project is a decision support dashboard for monitoring supplier performance, inventory status, shipment delays, demand trends, and operational risk in a supply chain network.

The dashboard is developed as a graduation project prototype and focuses on supply chain visibility, delivery performance, inventory monitoring, and risk analysis.

## Project Objective

The main objective of this project is to create an interactive dashboard that helps users monitor key supply chain performance indicators from a single interface.

The system aims to answer the following questions:

- How many orders are processed in the supply chain?
- What is the on-time delivery rate?
- Which shipping modes have higher delay levels?
- Which product categories have delivery or inventory risks?
- Which regions have higher operational risk?
- How can supply chain data be transformed into useful decision-support indicators?

## Dataset

This project uses the public **DataCo Smart Supply Chain Dataset** from Kaggle as the main operational data source.

The raw dataset includes order, product, customer, shipping, delivery, sales, and profit-related information.

Since the original dataset does not include complete inventory planning fields, additional inventory-related indicators such as current stock, reorder point, safety stock, days of supply, and inventory status were generated from product demand patterns for academic demonstration purposes.

## Main Features

The current version includes:

- Executive overview dashboard
- Regional performance analysis
- Inventory control dashboard
- Shipment performance dashboard
- Supply chain risk analysis dashboard
- Demand forecasting dashboard
- Total order, sales, and profit KPIs
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

- Improve dashboard visual design
- Add more advanced forecasting models
- Add export buttons for reports
- Add automated data refresh pipeline
- Add real-time ERP/API integration
- Add user authentication for production use
- Improve risk scoring with machine learning models
- Add deployment instructions

## Technologies Used

- Python
- Streamlit
- pandas
- numpy
- Plotly
- SQLite
- scikit-learn

## Project Structure

```text
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
├── docs/
└── screenshots/

## Current Status

The main dashboard modules are completed.

Completed modules:

- Overview
- Regional Performance
- Inventory Control
- Shipment Performance
- Supply Chain Risk
- Demand Forecast

The project currently provides a working multi-page Streamlit dashboard using cleaned supply chain data, generated inventory indicators, risk scoring logic, and basic demand forecasting models.

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