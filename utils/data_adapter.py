from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

ORDERS_PATH = PROCESSED_DIR / "orders_clean.csv"
PRODUCTS_PATH = PROCESSED_DIR / "products_clean.csv"
SHIPMENTS_PATH = PROCESSED_DIR / "shipments_clean.csv"
INVENTORY_PATH = PROCESSED_DIR / "inventory_generated.csv"
DEMAND_PATH = PROCESSED_DIR / "demand_clean.csv"
RISK_PATH = PROCESSED_DIR / "risk_scores.csv"


STANDARD_FIELDS = {
    "order_id": {
        "required": True,
        "description": "Unique order identifier",
        "keywords": ["order id", "order_id", "order", "purchase order", "po"],
    },
    "order_date": {
        "required": True,
        "description": "Order creation date",
        "keywords": ["order date", "order_date", "po created", "created", "dateorders", "date"],
    },
    "product_name": {
        "required": True,
        "description": "Product or SKU name",
        "keywords": ["product name", "product_name", "sku", "item", "material", "product"],
    },
    "category_name": {
        "required": True,
        "description": "Product category or group",
        "keywords": ["category", "category name", "product group", "department"],
    },
    "order_quantity": {
        "required": True,
        "description": "Ordered quantity",
        "keywords": ["quantity", "qty", "order item quantity", "ordered"],
    },
    "shipping_date": {
        "required": False,
        "description": "Shipping, dispatch, or delivery date",
        "keywords": ["shipping date", "ship date", "delivery date", "dispatch"],
    },
    "scheduled_delivery_date": {
    "required": False,
    "description": "Scheduled or promised delivery date",
    "keywords": [
        "scheduled delivery date",
        "promised delivery date",
        "planned delivery date",
        "scheduled date",
        "expected delivery date",],
    },
    "delivery_status": {
        "required": False,
        "description": "Delivery status",
        "keywords": ["delivery status", "status", "delivery situation", "late"],
    },
    "actual_shipping_days": {
        "required": False,
        "description": "Actual shipping / transit days",
        "keywords": ["actual shipping", "real transit", "days for shipping", "real"],
    },
    "scheduled_shipping_days": {
        "required": False,
        "description": "Scheduled / promised shipping days",
        "keywords": ["scheduled", "promised", "planned", "shipment scheduled"],
    },
    "shipping_mode": {
        "required": False,
        "description": "Shipping mode, transport type, or carrier",
        "keywords": ["shipping mode", "transport", "carrier", "ship mode"],
    },
    "market": {
        "required": False,
        "description": "Market or business area",
        "keywords": ["market", "business market"],
    },
    "order_region": {
        "required": False,
        "description": "Sales or order region",
        "keywords": ["region", "sales region", "order region"],
    },
    "order_country": {
        "required": False,
        "description": "Destination or order country",
        "keywords": ["country", "destination country", "order country"],
    },
    "sales": {
        "required": False,
        "description": "Sales, revenue, or order amount",
        "keywords": ["sales", "revenue", "net revenue", "amount"],
    },
    "order_profit": {
        "required": False,
        "description": "Profit, margin, or benefit",
        "keywords": ["profit", "margin", "gross margin", "benefit"],
    },
}


@st.cache_data
def load_default_dashboard_data():
    """Load default processed DataCo dashboard data."""
    orders = pd.read_csv(ORDERS_PATH)
    products = pd.read_csv(PRODUCTS_PATH)
    shipments = pd.read_csv(SHIPMENTS_PATH)
    inventory = pd.read_csv(INVENTORY_PATH)
    demand = pd.read_csv(DEMAND_PATH)
    risk = pd.read_csv(RISK_PATH)

    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    orders["shipping_date"] = pd.to_datetime(orders["shipping_date"], errors="coerce")
    shipments["shipping_date"] = pd.to_datetime(shipments["shipping_date"], errors="coerce")

    return {
        "orders": orders,
        "products": products,
        "shipments": shipments,
        "inventory": inventory,
        "demand": demand,
        "risk": risk,
        "source_name": "Default DataCo Dataset",
        "is_uploaded": False,
    }


def get_active_dashboard_data():
    """Return uploaded dashboard data if available; otherwise return default data."""
    if "custom_dashboard_data" in st.session_state:
        return st.session_state["custom_dashboard_data"]

    return load_default_dashboard_data()


def clear_uploaded_dataset():
    """Return dashboard to default dataset."""
    if "custom_dashboard_data" in st.session_state:
        del st.session_state["custom_dashboard_data"]


def read_uploaded_file(uploaded_file):
    """Read uploaded CSV or Excel file."""
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        try:
            return pd.read_csv(uploaded_file)
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding="latin1")

    if file_name.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)

    raise ValueError("Unsupported file type. Please upload CSV or XLSX.")


def suggest_column(field_name, columns):
    """Suggest a source column for a standard field."""
    keywords = STANDARD_FIELDS[field_name]["keywords"]

    normalized_columns = {
        col: col.lower().replace("_", " ").replace("-", " ").strip()
        for col in columns
    }

    for keyword in keywords:
        keyword = keyword.lower()
        for original, normalized in normalized_columns.items():
            if keyword == normalized:
                return original

    for keyword in keywords:
        keyword = keyword.lower()
        for original, normalized in normalized_columns.items():
            if keyword in normalized:
                return original

    return None


def build_mapping_ui(df):
    """Build column mapping UI."""
    st.subheader("Column Mapping")

    st.write(
        "Map the uploaded dataset columns to the standard supply chain schema. "
        "Required fields must be mapped. Optional fields improve dashboard quality."
    )

    columns = list(df.columns)
    options = ["Not available"] + columns
    mapping = {}

    required_fields = [
        field for field, info in STANDARD_FIELDS.items() if info["required"]
    ]

    optional_fields = [
        field for field, info in STANDARD_FIELDS.items() if not info["required"]
    ]

    st.markdown("#### Required Fields")

    for field in required_fields:
        suggested = suggest_column(field, columns)
        default_index = options.index(suggested) if suggested in options else 0

        mapping[field] = st.selectbox(
            f"{field} — {STANDARD_FIELDS[field]['description']}",
            options=options,
            index=default_index,
            key=f"global_required_{field}",
        )

    with st.expander("Optional Fields", expanded=False):
        for field in optional_fields:
            suggested = suggest_column(field, columns)
            default_index = options.index(suggested) if suggested in options else 0

            mapping[field] = st.selectbox(
                f"{field} — {STANDARD_FIELDS[field]['description']}",
                options=options,
                index=default_index,
                key=f"global_optional_{field}",
            )

    return mapping


def validate_mapping(mapping):
    """Validate required fields and duplicate mappings."""
    errors = []

    for field, info in STANDARD_FIELDS.items():
        if info["required"] and mapping.get(field) == "Not available":
            errors.append(f"Missing required field: {field}")

    mapped_columns = [
        source_col
        for source_col in mapping.values()
        if source_col != "Not available"
    ]

    duplicate_columns = {
        col for col in mapped_columns if mapped_columns.count(col) > 1
    }

    if duplicate_columns:
        errors.append(
            "The same source column was mapped to multiple fields: "
            + ", ".join(sorted(duplicate_columns))
        )

    return errors


def safe_numeric(series, default_value=0):
    """Convert a series to numeric safely."""
    return pd.to_numeric(series, errors="coerce").fillna(default_value)


def standardize_uploaded_orders(raw_df, mapping):
    """Convert uploaded dataset into the order schema used by dashboard pages."""
    orders = pd.DataFrame()

    orders["order_id"] = raw_df[mapping["order_id"]].astype(str)
    orders["order_status"] = "Unknown"
    orders["order_date"] = pd.to_datetime(raw_df[mapping["order_date"]], errors="coerce")
    orders["product_name"] = raw_df[mapping["product_name"]].astype(str)
    orders["category_name"] = raw_df[mapping["category_name"]].astype(str)
    orders["order_quantity"] = safe_numeric(raw_df[mapping["order_quantity"]], 0)

    text_defaults = {
        "delivery_status": "Unknown",
        "shipping_mode": "Unknown",
        "market": "Unknown",
        "order_region": "Unknown",
        "order_country": "Unknown",
    }

    for field, default in text_defaults.items():
        if mapping.get(field) != "Not available":
            orders[field] = raw_df[mapping[field]].astype(str)
        else:
            orders[field] = default

    orders["order_state"] = "Unknown"

    if mapping.get("shipping_date") != "Not available":
        orders["shipping_date"] = pd.to_datetime(
            raw_df[mapping["shipping_date"]],
            errors="coerce",
        )
    else:
        orders["shipping_date"] = pd.NaT

    if mapping.get("scheduled_delivery_date") != "Not available":
        orders["scheduled_delivery_date"] = pd.to_datetime(
            raw_df[mapping["scheduled_delivery_date"]],
            errors="coerce",
        )
    else:
        orders["scheduled_delivery_date"] = pd.NaT

    if mapping.get("actual_shipping_days") != "Not available":
        orders["actual_shipping_days"] = safe_numeric(
            raw_df[mapping["actual_shipping_days"]],
            np.nan,
        )
    else:
        orders["actual_shipping_days"] = np.nan

    if mapping.get("scheduled_shipping_days") != "Not available":
        orders["scheduled_shipping_days"] = safe_numeric(
            raw_df[mapping["scheduled_shipping_days"]],
            np.nan,
        )
    else:
        orders["scheduled_shipping_days"] = np.nan

    missing_actual_days = orders["actual_shipping_days"].isna()

    if orders["shipping_date"].notna().any():
        calculated_actual_days = (
            orders["shipping_date"] - orders["order_date"]
        ).dt.days

        orders.loc[missing_actual_days, "actual_shipping_days"] = calculated_actual_days

    missing_scheduled_days = orders["scheduled_shipping_days"].isna()

    if orders["scheduled_delivery_date"].notna().any():
        calculated_scheduled_days = (
            orders["scheduled_delivery_date"] - orders["order_date"]
        ).dt.days

        orders.loc[missing_scheduled_days, "scheduled_shipping_days"] = calculated_scheduled_days

    orders["actual_shipping_days"] = orders["actual_shipping_days"].fillna(0)

    orders["scheduled_shipping_days"] = orders["scheduled_shipping_days"].fillna(
        orders["actual_shipping_days"]
    )

    date_based_delay = (
        orders["shipping_date"] - orders["scheduled_delivery_date"]
    ).dt.days

    numeric_based_delay = (
        orders["actual_shipping_days"] - orders["scheduled_shipping_days"]
    )

    orders["delay_days"] = numeric_based_delay

    has_date_based_delay = date_based_delay.notna()

    orders.loc[has_date_based_delay, "delay_days"] = date_based_delay.loc[
        has_date_based_delay
    ]

    orders["delay_days"] = orders["delay_days"].fillna(0).clip(lower=0)

    status_lower = orders["delivery_status"].astype(str).str.lower()
    status_late = status_lower.str.contains("late|delay|delayed", regex=True)
    delay_late = orders["delay_days"] > 0

    orders["is_late"] = (status_late | delay_late).astype(int)
    orders["is_on_time"] = 1 - orders["is_late"]
    orders["late_delivery_risk"] = orders["is_late"]

    if mapping.get("sales") != "Not available":
        orders["sales"] = safe_numeric(raw_df[mapping["sales"]], 0)
    else:
        orders["sales"] = 0

    if mapping.get("order_profit") != "Not available":
        orders["order_profit"] = safe_numeric(raw_df[mapping["order_profit"]], 0)
    else:
        orders["order_profit"] = 0

    orders["order_item_total"] = orders["sales"]
    orders["benefit_per_order"] = orders["order_profit"]

    orders = orders.dropna(subset=["order_date"])
    orders["year_month"] = orders["order_date"].dt.to_period("M").astype(str)

    return orders


def create_products_table(orders):
    """Create product table from uploaded orders."""
    products = (
        orders[["product_name", "category_name"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    products.insert(0, "product_id", range(1, len(products) + 1))
    products["department_name"] = products["category_name"]

    quantity_sum = max(orders["order_quantity"].sum(), 1)
    avg_price = orders["sales"].sum() / quantity_sum

    products["product_price"] = avg_price
    products["product_status"] = 0

    return products


def create_shipments_table(orders):
    """Create shipment table from uploaded orders."""
    shipments = orders[
        [
            "order_id",
            "market",
            "order_region",
            "order_country",
            "shipping_mode",
            "delivery_status",
            "actual_shipping_days",
            "scheduled_shipping_days",
            "delay_days",
            "is_late",
            "shipping_date",
        ]
    ].copy()

    shipments = shipments.reset_index(drop=True)
    shipments.insert(0, "shipment_id", range(1, len(shipments) + 1))

    return shipments


def create_inventory_table(products, orders):
    """Generate inventory table from demand patterns."""
    demand_by_product = (
        orders.groupby("product_name")["order_quantity"]
        .sum()
        .reset_index()
        .rename(columns={"order_quantity": "total_demand"})
    )

    inventory = products.merge(demand_by_product, on="product_name", how="left")
    inventory["total_demand"] = inventory["total_demand"].fillna(0)

    active_days = max((orders["order_date"].max() - orders["order_date"].min()).days, 30)

    inventory["average_daily_demand"] = (
        inventory["total_demand"] / active_days
    ).clip(lower=1)

    inventory["safety_stock"] = (
        inventory["average_daily_demand"] * 7
    ).round().astype(int)

    inventory["reorder_point"] = (
        inventory["average_daily_demand"] * 14
    ).round().astype(int)

    np.random.seed(42)
    inventory["current_stock"] = (
    inventory["reorder_point"] * np.random.uniform(0.6, 1.8, size=len(inventory))
    ).round().astype(int)


    inventory["days_of_supply"] = (
        inventory["current_stock"] / inventory["average_daily_demand"]
    ).round(1)

    def classify_inventory(row):
        if row["current_stock"] < row["reorder_point"]:
            return "Critical"
        if row["current_stock"] < row["reorder_point"] + row["safety_stock"]:
            return "Warning"
        return "Healthy"

    inventory["inventory_status"] = inventory.apply(classify_inventory, axis=1)

    return inventory[
        [
            "product_id",
            "product_name",
            "category_name",
            "current_stock",
            "reorder_point",
            "safety_stock",
            "average_daily_demand",
            "days_of_supply",
            "inventory_status",
        ]
    ]


def create_demand_table(orders):
    """Create monthly demand by category."""
    return (
        orders.groupby(["year_month", "category_name"])["order_quantity"]
        .sum()
        .reset_index()
        .rename(columns={"order_quantity": "demand_quantity"})
    )


def classify_risk(score):
    if score < 40:
        return "Low"
    elif score < 70:
        return "Medium"
    else:
        return "High"


def create_risk_table(orders, inventory):
    """Create region-level risk score table."""
    risk = (
        orders.groupby(["market", "order_region"])
        .agg(
            total_orders=("order_id", "nunique"),
            late_delivery_rate=("is_late", "mean"),
            avg_delay_days=("delay_days", "mean"),
            avg_shipping_days=("actual_shipping_days", "mean"),
            total_sales=("sales", "sum"),
            total_profit=("order_profit", "sum"),
        )
        .reset_index()
    )

    risk["late_delivery_risk_score"] = (
        risk["late_delivery_rate"] * 100
    ).round(2)

    max_delay = risk["avg_delay_days"].max()

    if max_delay == 0 or pd.isna(max_delay):
        risk["delay_risk_score"] = 0
    else:
        risk["delay_risk_score"] = (
            risk["avg_delay_days"] / max_delay * 100
        ).round(2)

    inventory_risk_map = {
        "Critical": 100,
        "Warning": 60,
        "Healthy": 20,
    }

    inventory_risk_score = (
        inventory["inventory_status"]
        .map(inventory_risk_map)
        .fillna(60)
        .mean()
    )

    risk["inventory_risk_score"] = round(inventory_risk_score, 2)

    monthly_demand = (
        orders.groupby(["market", "order_region", "year_month"])["order_quantity"]
        .sum()
        .reset_index()
    )

    demand_volatility = (
        monthly_demand.groupby(["market", "order_region"])["order_quantity"]
        .agg(["mean", "std"])
        .reset_index()
    )

    demand_volatility["std"] = demand_volatility["std"].fillna(0)
    demand_volatility["demand_volatility_risk_score"] = (
        demand_volatility["std"] / demand_volatility["mean"].replace(0, pd.NA) * 100
    ).fillna(0).clip(upper=100).round(2)

    risk = risk.merge(
        demand_volatility[
            ["market", "order_region", "demand_volatility_risk_score"]
        ],
        on=["market", "order_region"],
        how="left",
    )

    risk["demand_volatility_risk_score"] = (
        risk["demand_volatility_risk_score"].fillna(0)
    )

    risk["profit_risk_score"] = risk["total_profit"].apply(
        lambda value: 80 if value < 0 else 20
    )

    risk["overall_risk_score"] = (
        0.35 * risk["late_delivery_risk_score"]
        + 0.25 * risk["inventory_risk_score"]
        + 0.20 * risk["delay_risk_score"]
        + 0.20 * risk["demand_volatility_risk_score"]
    ).round(2)

    risk["risk_level"] = risk["overall_risk_score"].apply(classify_risk)

    return risk


def build_dashboard_tables_from_uploaded_data(raw_df, mapping, source_name):
    """Build all dashboard tables from uploaded data."""
    orders = standardize_uploaded_orders(raw_df, mapping)

    if orders.empty:
        raise ValueError("No valid rows after standardization. Check order date mapping.")

    products = create_products_table(orders)
    shipments = create_shipments_table(orders)
    inventory = create_inventory_table(products, orders)
    demand = create_demand_table(orders)
    risk = create_risk_table(orders, inventory)

    return {
        "orders": orders,
        "products": products,
        "shipments": shipments,
        "inventory": inventory,
        "demand": demand,
        "risk": risk,
        "source_name": source_name,
        "is_uploaded": True,
    }


def render_data_source_manager():
    """Render global data source manager on Overview page."""
    dashboard_data = get_active_dashboard_data()
    active_source = dashboard_data["source_name"]

    with st.expander("Data Source Manager", expanded=False):
        st.write(f"**Active dataset:** {active_source}")

        if dashboard_data["is_uploaded"]:
            st.info("All dashboard pages are currently using the uploaded dataset.")

            if st.button("Return to Default DataCo Dataset"):
                clear_uploaded_dataset()
                st.success("Returned to default dataset.")
                st.rerun()
        else:
            st.caption("The dashboard is currently using the default DataCo dataset.")

        uploaded_file = st.file_uploader(
            "Upload a company supply chain dataset",
            type=["csv", "xlsx"],
            key="global_company_dataset_upload",
        )

        if uploaded_file is None:
            return

        try:
            raw_df = read_uploaded_file(uploaded_file)
        except Exception as error:
            st.error(f"Could not read uploaded file: {error}")
            return

        st.write(f"Rows: {raw_df.shape[0]:,} | Columns: {raw_df.shape[1]:,}")
        st.dataframe(raw_df.head(10), use_container_width=True)

        mapping = build_mapping_ui(raw_df)
        errors = validate_mapping(mapping)

        if errors:
            st.error("Fix mapping errors before using this dataset:")
            for error in errors:
                st.write(f"- {error}")
            return

        if st.button("Use This Dataset Across Dashboard", type="primary"):
            try:
                custom_data = build_dashboard_tables_from_uploaded_data(
                    raw_df=raw_df,
                    mapping=mapping,
                    source_name=uploaded_file.name,
                )
            except Exception as error:
                st.error(f"Dataset could not be processed: {error}")
                return

            st.session_state["custom_dashboard_data"] = custom_data
            st.success(
                "Dataset activated. All dashboard pages will now use the uploaded dataset."
            )
            st.rerun()