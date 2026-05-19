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
- Total order and sales KPIs
- On-time and late delivery rate calculation
- Average shipping and delay day calculation
- Monthly order volume analysis
- Delivery status distribution
- Average delay by shipping mode
- Inventory status summary
- Cleaned order data preview
- Processed CSV tables
- SQLite database generation

Planned modules:

- Supplier or region performance analysis
- Inventory monitoring page
- Shipment tracking page
- Risk analysis page
- Demand forecasting page

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
├── app.py
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
├── docs/
└── screenshots/