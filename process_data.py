import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "DataCoSupplyChainDataset.csv"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_PATH = PROCESSED_DIR / "supply_chain.db"


def load_raw_data() -> pd.DataFrame:
    """Load the raw DataCo supply chain dataset."""
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Raw dataset not found: {RAW_DATA_PATH}")

    df = pd.read_csv(RAW_DATA_PATH, encoding="latin1")
    return df


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Create a cleaned order-level table for dashboard analysis."""

    orders = df[
        [
            "Order Id",
            "Order Status",
            "Order Country",
            "Order Region",
            "Order State",
            "Market",
            "order date (DateOrders)",
            "shipping date (DateOrders)",
            "Delivery Status",
            "Late_delivery_risk",
            "Days for shipping (real)",
            "Days for shipment (scheduled)",
            "Shipping Mode",
            "Category Name",
            "Product Name",
            "Order Item Quantity",
            "Sales",
            "Order Item Total",
            "Order Profit Per Order",
            "Benefit per order",
        ]
    ].copy()

    orders.columns = [
        "order_id",
        "order_status",
        "order_country",
        "order_region",
        "order_state",
        "market",
        "order_date",
        "shipping_date",
        "delivery_status",
        "late_delivery_risk",
        "actual_shipping_days",
        "scheduled_shipping_days",
        "shipping_mode",
        "category_name",
        "product_name",
        "order_quantity",
        "sales",
        "order_item_total",
        "order_profit",
        "benefit_per_order",
    ]

    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    orders["shipping_date"] = pd.to_datetime(orders["shipping_date"], errors="coerce")

    orders["delay_days"] = (
        orders["actual_shipping_days"] - orders["scheduled_shipping_days"]
    ).clip(lower=0)

    orders["is_late"] = orders["late_delivery_risk"].astype(int)
    orders["is_on_time"] = 1 - orders["is_late"]

    orders["year_month"] = orders["order_date"].dt.to_period("M").astype(str)

    return orders


def create_products_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create a cleaned product table."""

    products = df[
        [
            "Product Card Id",
            "Product Name",
            "Category Name",
            "Department Name",
            "Product Price",
            "Product Status",
        ]
    ].copy()

    products.columns = [
        "product_id",
        "product_name",
        "category_name",
        "department_name",
        "product_price",
        "product_status",
    ]

    products = products.drop_duplicates(subset=["product_id"]).reset_index(drop=True)

    return products


def create_shipments_table(orders: pd.DataFrame) -> pd.DataFrame:
    """Create a shipment-focused table from cleaned order data."""

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


def create_inventory_table(products: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a simple inventory planning table.

    The original DataCo dataset does not include inventory levels.
    Therefore, inventory values are generated from product demand patterns
    for academic dashboard demonstration purposes.
    """

    demand_by_product = (
        orders.groupby("product_name")["order_quantity"]
        .sum()
        .reset_index()
        .rename(columns={"order_quantity": "total_demand"})
    )

    inventory = products.merge(demand_by_product, on="product_name", how="left")
    inventory["total_demand"] = inventory["total_demand"].fillna(0)

    inventory["average_daily_demand"] = (inventory["total_demand"] / 365).clip(lower=1)

    inventory["safety_stock"] = (inventory["average_daily_demand"] * 7).round().astype(int)
    inventory["reorder_point"] = (inventory["average_daily_demand"] * 14).round().astype(int)

    # Create realistic stock levels around reorder point.
    inventory["current_stock"] = (
        inventory["reorder_point"] * 1.4
    ).round().astype(int)

    # Make some products intentionally risky for dashboard demonstration.
    inventory.loc[inventory.index[::5], "current_stock"] = (
        inventory.loc[inventory.index[::5], "reorder_point"] * 0.7
    ).round().astype(int)

    inventory.loc[inventory.index[::7], "current_stock"] = (
        inventory.loc[inventory.index[::7], "reorder_point"] * 1.05
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

    inventory = inventory[
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

    return inventory


def create_demand_table(orders: pd.DataFrame) -> pd.DataFrame:
    """Create monthly demand table by product category."""

    demand = (
        orders.groupby(["year_month", "category_name"])["order_quantity"]
        .sum()
        .reset_index()
        .rename(columns={"order_quantity": "demand_quantity"})
    )

    return demand


def create_risk_table(orders: pd.DataFrame, inventory: pd.DataFrame) -> pd.DataFrame:
    """Create region-level operational risk scores."""

    region_perf = (
        orders.groupby(["market", "order_region"])
        .agg(
            total_orders=("order_id", "count"),
            late_delivery_rate=("is_late", "mean"),
            avg_delay_days=("delay_days", "mean"),
            avg_shipping_days=("actual_shipping_days", "mean"),
            total_sales=("sales", "sum"),
            total_profit=("order_profit", "sum"),
        )
        .reset_index()
    )

    region_perf["late_delivery_risk_score"] = (
        region_perf["late_delivery_rate"] * 100
    ).round(2)

    max_delay = region_perf["avg_delay_days"].max()
    if max_delay == 0:
        region_perf["delay_risk_score"] = 0
    else:
        region_perf["delay_risk_score"] = (
            region_perf["avg_delay_days"] / max_delay * 100
        ).round(2)

    region_perf["profit_risk_score"] = region_perf["total_profit"].apply(
        lambda x: 80 if x < 0 else 20
    )

    region_perf["overall_risk_score"] = (
        0.50 * region_perf["late_delivery_risk_score"]
        + 0.30 * region_perf["delay_risk_score"]
        + 0.20 * region_perf["profit_risk_score"]
    ).round(2)

    def classify_risk(score):
        if score < 30:
            return "Low"
        if score < 60:
            return "Medium"
        return "High"

    region_perf["risk_level"] = region_perf["overall_risk_score"].apply(classify_risk)

    return region_perf


def save_to_csv_and_sqlite(
    orders: pd.DataFrame,
    products: pd.DataFrame,
    shipments: pd.DataFrame,
    inventory: pd.DataFrame,
    demand: pd.DataFrame,
    risk: pd.DataFrame,
) -> None:
    """Save processed tables as CSV files and SQLite database tables."""

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    orders.to_csv(PROCESSED_DIR / "orders_clean.csv", index=False)
    products.to_csv(PROCESSED_DIR / "products_clean.csv", index=False)
    shipments.to_csv(PROCESSED_DIR / "shipments_clean.csv", index=False)
    inventory.to_csv(PROCESSED_DIR / "inventory_generated.csv", index=False)
    demand.to_csv(PROCESSED_DIR / "demand_clean.csv", index=False)
    risk.to_csv(PROCESSED_DIR / "risk_scores.csv", index=False)

    with sqlite3.connect(DB_PATH) as conn:
        orders.to_sql("orders", conn, if_exists="replace", index=False)
        products.to_sql("products", conn, if_exists="replace", index=False)
        shipments.to_sql("shipments", conn, if_exists="replace", index=False)
        inventory.to_sql("inventory", conn, if_exists="replace", index=False)
        demand.to_sql("demand", conn, if_exists="replace", index=False)
        risk.to_sql("risk_scores", conn, if_exists="replace", index=False)


def main() -> None:
    print("Loading raw dataset...")
    raw_df = load_raw_data()
    print(f"Raw dataset loaded: {raw_df.shape[0]} rows, {raw_df.shape[1]} columns")

    print("Creating cleaned tables...")
    orders = clean_orders(raw_df)
    products = create_products_table(raw_df)
    shipments = create_shipments_table(orders)
    inventory = create_inventory_table(products, orders)
    demand = create_demand_table(orders)
    risk = create_risk_table(orders, inventory)

    print("Saving processed data...")
    save_to_csv_and_sqlite(orders, products, shipments, inventory, demand, risk)

    print("Done.")
    print(f"Processed files saved in: {PROCESSED_DIR}")
    print(f"SQLite database saved as: {DB_PATH}")


if __name__ == "__main__":
    main()