from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_adapter import get_active_dashboard_data

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

ORDERS_PATH = PROCESSED_DIR / "orders_clean.csv"
SHIPMENTS_PATH = PROCESSED_DIR / "shipments_clean.csv"
INVENTORY_PATH = PROCESSED_DIR / "inventory_generated.csv"
DEMAND_PATH = PROCESSED_DIR / "demand_clean.csv"
RISK_PATH = PROCESSED_DIR / "risk_scores.csv"


st.set_page_config(
    page_title="Risk Analysis",
    page_icon="⚠️",
    layout="wide",
)


def load_data():
    """Load active dashboard data."""
    dashboard_data = get_active_dashboard_data()

    orders = dashboard_data["orders"]
    shipments = dashboard_data["shipments"]
    inventory = dashboard_data["inventory"]
    demand = dashboard_data["demand"]
    risk_scores = dashboard_data["risk"]

    return orders, shipments, inventory, demand, risk_scores


def create_filter_options(series: pd.Series):
    values = sorted(series.dropna().unique())
    return ["All"] + values


def apply_filters(
    orders: pd.DataFrame,
    shipments: pd.DataFrame,
    inventory: pd.DataFrame,
    demand: pd.DataFrame,
):
    """Apply sidebar filters across datasets where possible."""

    st.sidebar.title("Filters")
    st.sidebar.caption("Filter risk indicators by market, region, category, and shipping mode.")

    selected_market = st.sidebar.selectbox(
        "Market",
        create_filter_options(orders["market"]),
    )

    if selected_market != "All":
        orders = orders[orders["market"] == selected_market]
        shipments = shipments[shipments["market"] == selected_market]

    selected_region = st.sidebar.selectbox(
        "Order Region",
        create_filter_options(orders["order_region"]),
    )

    if selected_region != "All":
        orders = orders[orders["order_region"] == selected_region]
        shipments = shipments[shipments["order_region"] == selected_region]

    selected_category = st.sidebar.selectbox(
        "Product Category",
        create_filter_options(orders["category_name"]),
    )

    if selected_category != "All":
        orders = orders[orders["category_name"] == selected_category]
        inventory = inventory[inventory["category_name"] == selected_category]
        demand = demand[demand["category_name"] == selected_category]

    selected_shipping_mode = st.sidebar.selectbox(
        "Shipping Mode",
        create_filter_options(orders["shipping_mode"]),
    )

    if selected_shipping_mode != "All":
        orders = orders[orders["shipping_mode"] == selected_shipping_mode]
        shipments = shipments[shipments["shipping_mode"] == selected_shipping_mode]

    min_date = orders["order_date"].min()
    max_date = orders["order_date"].max()

    if pd.notna(min_date) and pd.notna(max_date):
        selected_date_range = st.sidebar.date_input(
            "Order Date Range",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date(),
        )

        if len(selected_date_range) == 2:
            start_date, end_date = selected_date_range
            orders = orders[
                (orders["order_date"].dt.date >= start_date)
                & (orders["order_date"].dt.date <= end_date)
            ]

    return orders, shipments, inventory, demand


def classify_risk(score: float) -> str:
    """Classify numeric risk score."""

    if score < 40:
        return "Low"
    if score < 70:
        return "Medium"
    return "High"


def calculate_inventory_risk(inventory: pd.DataFrame) -> float:
    """Calculate inventory risk from inventory status distribution."""

    if inventory.empty:
        return 0.0

    total_items = len(inventory)
    critical_items = inventory[inventory["inventory_status"] == "Critical"].shape[0]
    warning_items = inventory[inventory["inventory_status"] == "Warning"].shape[0]

    inventory_risk = ((critical_items * 1.0 + warning_items * 0.5) / total_items) * 100

    return round(float(inventory_risk), 2)


def calculate_demand_volatility_risk(demand: pd.DataFrame) -> float:
    """Calculate demand volatility risk using coefficient of variation."""

    if demand.empty:
        return 0.0

    monthly_demand = (
        demand.groupby("year_month")["demand_quantity"]
        .sum()
        .reset_index()
        .sort_values("year_month")
    )

    mean_demand = monthly_demand["demand_quantity"].mean()
    std_demand = monthly_demand["demand_quantity"].std()

    if mean_demand == 0 or pd.isna(mean_demand) or pd.isna(std_demand):
        return 0.0

    coefficient_of_variation = std_demand / mean_demand

    demand_risk = min(coefficient_of_variation * 100, 100)

    return round(float(demand_risk), 2)

def scope_supporting_tables_by_orders(
    filtered_orders: pd.DataFrame,
    shipments: pd.DataFrame,
    inventory: pd.DataFrame,
):
    """Scope shipments, inventory, and demand according to filtered orders."""

    visible_order_ids = filtered_orders["order_id"].dropna().astype(str).unique()
    visible_products = filtered_orders["product_name"].dropna().unique()
    visible_categories = filtered_orders["category_name"].dropna().unique()

    scoped_shipments = shipments.copy()

    if "order_id" in scoped_shipments.columns:
        scoped_shipments["order_id"] = scoped_shipments["order_id"].astype(str)
        scoped_shipments = scoped_shipments[
            scoped_shipments["order_id"].isin(visible_order_ids)
        ]

    scoped_inventory = inventory.copy()

    if "product_name" in scoped_inventory.columns:
        scoped_inventory = scoped_inventory[
            scoped_inventory["product_name"].isin(visible_products)
        ]

    if "category_name" in scoped_inventory.columns:
        scoped_inventory = scoped_inventory[
            scoped_inventory["category_name"].isin(visible_categories)
        ]

    scoped_demand = (
        filtered_orders.groupby(["year_month", "category_name"])["order_quantity"]
        .sum()
        .reset_index()
        .rename(columns={"order_quantity": "demand_quantity"})
    )

    return scoped_shipments, scoped_inventory, scoped_demand

def calculate_risk_summary(
    orders: pd.DataFrame,
    shipments: pd.DataFrame,
    inventory: pd.DataFrame,
    demand: pd.DataFrame,
) -> dict:
    """Calculate overall supply chain risk indicators."""

    if orders.empty or shipments.empty:
        return {
            "delivery_risk": 0.0,
            "delay_risk": 0.0,
            "inventory_risk": calculate_inventory_risk(inventory),
            "demand_volatility_risk": calculate_demand_volatility_risk(demand),
            "overall_risk_score": 0.0,
            "risk_level": "Low",
        }

    delivery_risk = orders["is_late"].mean() * 100

    avg_delay_days = orders["delay_days"].mean()

    # Normalization assumption:
    # average delay of 3 days or more is treated as maximum delay risk.
    delay_risk = min((avg_delay_days / 3) * 100, 100)

    inventory_risk = calculate_inventory_risk(inventory)
    demand_volatility_risk = calculate_demand_volatility_risk(demand)

    overall_risk_score = (
        0.35 * delivery_risk
        + 0.25 * inventory_risk
        + 0.20 * delay_risk
        + 0.20 * demand_volatility_risk
    )

    overall_risk_score = round(float(overall_risk_score), 2)

    return {
        "delivery_risk": round(float(delivery_risk), 2),
        "delay_risk": round(float(delay_risk), 2),
        "inventory_risk": round(float(inventory_risk), 2),
        "demand_volatility_risk": round(float(demand_volatility_risk), 2),
        "overall_risk_score": overall_risk_score,
        "risk_level": classify_risk(overall_risk_score),
    }


def calculate_region_risk(orders: pd.DataFrame, inventory: pd.DataFrame) -> pd.DataFrame:
    """Calculate region-level risk from filtered order data."""

    if orders.empty:
        return pd.DataFrame()

    region_risk = (
        orders.groupby(["market", "order_region"])
        .agg(
            total_orders=("order_id", "nunique"),
            total_sales=("sales", "sum"),
            total_profit=("order_profit", "sum"),
            late_delivery_rate=("is_late", "mean"),
            avg_delay_days=("delay_days", "mean"),
            avg_shipping_days=("actual_shipping_days", "mean"),
        )
        .reset_index()
    )

    region_risk["late_delivery_risk_score"] = (
        region_risk["late_delivery_rate"] * 100
    ).round(2)

    max_delay = region_risk["avg_delay_days"].max()

    if max_delay == 0 or pd.isna(max_delay):
        region_risk["delay_risk_score"] = 0
    else:
        region_risk["delay_risk_score"] = (
            region_risk["avg_delay_days"] / max_delay * 100
        ).round(2)

    status_counts = inventory["inventory_status"].value_counts()
    total_inventory_items = len(inventory)

    if total_inventory_items == 0:
        inventory_risk_score = 0
    else:
        inventory_risk_score = (
            (
                status_counts.get("Critical", 0) * 1.0
                + status_counts.get("Warning", 0) * 0.5
            )
            / total_inventory_items
            * 100
        )

    region_risk["inventory_risk_score"] = round(inventory_risk_score, 2)

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
        demand_volatility["std"]
        / demand_volatility["mean"].replace(0, pd.NA)
        * 100
    ).fillna(0).clip(upper=100).round(2)

    region_risk = region_risk.merge(
        demand_volatility[
            ["market", "order_region", "demand_volatility_risk_score"]
        ],
        on=["market", "order_region"],
        how="left",
    )

    region_risk["demand_volatility_risk_score"] = (
        region_risk["demand_volatility_risk_score"].fillna(0)
    )

    region_risk["overall_region_risk_score"] = (
        0.35 * region_risk["late_delivery_risk_score"]
        + 0.25 * region_risk["inventory_risk_score"]
        + 0.20 * region_risk["delay_risk_score"]
        + 0.20 * region_risk["demand_volatility_risk_score"]
    ).round(2)

    region_risk["risk_level"] = region_risk["overall_region_risk_score"].apply(
        classify_risk
    )

    return region_risk.sort_values("overall_region_risk_score", ascending=False)


def calculate_category_risk(orders: pd.DataFrame, inventory: pd.DataFrame) -> pd.DataFrame:
    """Calculate category-level risk using delivery and inventory indicators."""

    if orders.empty:
        return pd.DataFrame()

    category_delivery = (
        orders.groupby("category_name")
        .agg(
            total_orders=("order_id", "nunique"),
            late_delivery_rate=("is_late", "mean"),
            avg_delay_days=("delay_days", "mean"),
            total_sales=("sales", "sum"),
            total_profit=("order_profit", "sum"),
        )
        .reset_index()
    )

    category_delivery["delivery_risk_score"] = (
        category_delivery["late_delivery_rate"] * 100
    ).round(2)

    inventory_status_map = {
        "Critical": 100,
        "Warning": 60,
        "Healthy": 20,
    }

    inventory_copy = inventory.copy()
    inventory_copy["inventory_risk_score"] = inventory_copy["inventory_status"].map(
        inventory_status_map
    ).fillna(20)

    category_inventory = (
        inventory_copy.groupby("category_name")
        .agg(
            avg_inventory_risk=("inventory_risk_score", "mean"),
            product_count=("product_id", "nunique"),
        )
        .reset_index()
    )

    category_risk = category_delivery.merge(
        category_inventory,
        on="category_name",
        how="left",
    )

    category_risk["avg_inventory_risk"] = category_risk["avg_inventory_risk"].fillna(0)

    max_delay = category_risk["avg_delay_days"].max()

    if max_delay == 0 or pd.isna(max_delay):
        category_risk["delay_risk_score"] = 0
    else:
        category_risk["delay_risk_score"] = (
            category_risk["avg_delay_days"] / max_delay * 100
        ).round(2)

    category_risk["overall_category_risk_score"] = (
        0.45 * category_risk["delivery_risk_score"]
        + 0.35 * category_risk["avg_inventory_risk"]
        + 0.20 * category_risk["delay_risk_score"]
    ).round(2)

    category_risk["risk_level"] = category_risk["overall_category_risk_score"].apply(
        classify_risk
    )

    return category_risk.sort_values("overall_category_risk_score", ascending=False)


def show_kpis(risk_summary: dict):
    """Display top risk KPI cards."""

    st.subheader("Overall Risk Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Overall Risk Score", f"{risk_summary['overall_risk_score']:.1f}")
    col2.metric("Risk Level", risk_summary["risk_level"])
    col3.metric("Delivery Risk", f"{risk_summary['delivery_risk']:.1f}")
    col4.metric("Delay Risk", f"{risk_summary['delay_risk']:.1f}")

    col5, col6 = st.columns(2)

    col5.metric("Inventory Risk", f"{risk_summary['inventory_risk']:.1f}")
    col6.metric("Demand Volatility Risk", f"{risk_summary['demand_volatility_risk']:.1f}")


def show_risk_gauge(risk_summary: dict):
    """Display overall risk gauge and risk breakdown."""

    st.divider()

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Overall Supply Chain Risk Score")

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=risk_summary["overall_risk_score"],
                title={"text": "Overall Risk Score"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "steps": [
                        {"range": [0, 40], "color": "lightgreen"},
                        {"range": [40, 70], "color": "khaki"},
                        {"range": [70, 100], "color": "salmon"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": risk_summary["overall_risk_score"],
                    },
                },
            )
        )

        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    with right_col:
        st.subheader("Risk Breakdown")

        breakdown = pd.DataFrame(
            {
                "risk_type": [
                    "Delivery Risk",
                    "Inventory Risk",
                    "Delay Risk",
                    "Demand Volatility Risk",
                ],
                "score": [
                    risk_summary["delivery_risk"],
                    risk_summary["inventory_risk"],
                    risk_summary["delay_risk"],
                    risk_summary["demand_volatility_risk"],
                ],
            }
        )

        fig = px.bar(
            breakdown,
            x="risk_type",
            y="score",
            title="Risk Breakdown by Component",
        )

        fig.update_layout(
            xaxis_title="Risk Component",
            yaxis_title="Risk Score",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)


def show_charts(
    orders: pd.DataFrame,
    inventory: pd.DataFrame,
    demand: pd.DataFrame,
    region_risk: pd.DataFrame,
    category_risk: pd.DataFrame,
):
    """Display risk analysis charts."""

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Top 15 High-Risk Regions")

        top_regions = region_risk.head(15)

        fig = px.bar(
            top_regions,
            x="overall_region_risk_score",
            y="order_region",
            orientation="h",
            color="risk_level",
            title="Top 15 Regions by Risk Score",
        )

        fig.update_layout(
            xaxis_title="Risk Score",
            yaxis_title="Region",
            height=520,
        )

        st.plotly_chart(fig, use_container_width=True)

    with right_col:
        st.subheader("Top 15 High-Risk Product Categories")

        top_categories = category_risk.head(15)

        fig = px.bar(
            top_categories,
            x="overall_category_risk_score",
            y="category_name",
            orientation="h",
            color="risk_level",
            title="Top 15 Categories by Risk Score",
        )

        fig.update_layout(
            xaxis_title="Risk Score",
            yaxis_title="Product Category",
            height=520,
        )

        st.plotly_chart(fig, use_container_width=True)

    left_col2, right_col2 = st.columns(2)

    with left_col2:
        st.subheader("Monthly Late Delivery Risk Trend")

        monthly_late = (
            orders.groupby("year_month")
            .agg(
                total_orders=("order_id", "nunique"),
                late_delivery_rate=("is_late", "mean"),
            )
            .reset_index()
            .sort_values("year_month")
        )

        monthly_late["late_delivery_rate_pct"] = (
            monthly_late["late_delivery_rate"] * 100
        ).round(2)

        fig = px.line(
            monthly_late,
            x="year_month",
            y="late_delivery_rate_pct",
            markers=True,
            title="Monthly Late Delivery Risk Trend",
        )

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Late Delivery Risk (%)",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)

    with right_col2:
        st.subheader("Demand Volatility by Category")

        demand_volatility = (
            demand.groupby("category_name")
            .agg(
                avg_demand=("demand_quantity", "mean"),
                std_demand=("demand_quantity", "std"),
            )
            .reset_index()
        )

        demand_volatility["volatility_score"] = (
            demand_volatility["std_demand"] / demand_volatility["avg_demand"] * 100
        ).fillna(0)

        demand_volatility = demand_volatility.sort_values(
            "volatility_score", ascending=False
        ).head(15)

        fig = px.bar(
            demand_volatility,
            x="volatility_score",
            y="category_name",
            orientation="h",
            title="Top Categories by Demand Volatility",
        )

        fig.update_layout(
            xaxis_title="Volatility Score",
            yaxis_title="Product Category",
            height=520,
        )

        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Regional Risk Heatmap")

    heatmap_source = region_risk.copy()

    if not heatmap_source.empty:
        pivot = heatmap_source.pivot_table(
            index="market",
            columns="order_region",
            values="overall_region_risk_score",
            aggfunc="mean",
        )

        fig = px.imshow(
            pivot,
            text_auto=".1f",
            aspect="auto",
            title="Average Risk Score by Market and Region",
        )

        fig.update_layout(
            xaxis_title="Region",
            yaxis_title="Market",
            height=600,
        )

        st.plotly_chart(fig, use_container_width=True)


def show_tables(region_risk: pd.DataFrame, category_risk: pd.DataFrame, inventory: pd.DataFrame):
    """Display risk tables."""

    st.divider()

    st.subheader("Region Risk Table")

    region_columns = [
        "market",
        "order_region",
        "total_orders",
        "late_delivery_rate",
        "avg_delay_days",
        "late_delivery_risk_score",
        "delay_risk_score",
        "inventory_risk_score",
        "demand_volatility_risk_score",
        "overall_region_risk_score",
        "risk_level",
    ]

    region_columns = [col for col in region_columns if col in region_risk.columns]

    st.dataframe(
        region_risk[region_columns].head(50),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Category Risk Table")

    category_columns = [
        "category_name",
        "total_orders",
        "total_sales",
        "total_profit",
        "delivery_risk_score",
        "avg_inventory_risk",
        "delay_risk_score",
        "overall_category_risk_score",
        "risk_level",
    ]

    st.dataframe(
        category_risk[category_columns].head(50),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Critical Inventory Risk Table")

    critical_inventory = inventory[
        inventory["inventory_status"].isin(["Critical", "Warning"])
    ].copy()

    critical_inventory = critical_inventory.sort_values(
        ["inventory_status", "days_of_supply"],
        ascending=[True, True],
    )

    inventory_columns = [
        "product_id",
        "product_name",
        "category_name",
        "current_stock",
        "reorder_point",
        "safety_stock",
        "days_of_supply",
        "inventory_status",
    ]

    st.dataframe(
        critical_inventory[inventory_columns],
        use_container_width=True,
        hide_index=True,
    )


def main():
    orders, shipments, inventory, demand, risk_scores = load_data()

    st.title("Supply Chain Risk Analysis")

    st.markdown(
        """
        This page calculates and visualizes operational supply chain risk by combining
        delivery risk, delay risk, inventory risk, and demand volatility risk.
        """
    )

    with st.expander("How is the overall risk score calculated?", expanded=False):
        st.write(
            """
            The overall supply chain risk score is calculated using four components:

            - Delivery Risk: percentage of late deliveries
            - Delay Risk: normalized average delay days
            - Inventory Risk: share of critical and warning inventory items
            - Demand Volatility Risk: demand variation over time

            Overall Risk Score =
            35% Delivery Risk + 25% Inventory Risk + 20% Delay Risk + 20% Demand Volatility Risk
            """
        )

    filtered_orders, filtered_shipments, filtered_inventory, filtered_demand = apply_filters(
        orders, shipments, inventory, demand
    )

    if filtered_orders.empty:
        st.warning("No order records available for the selected filters.")
        return

    filtered_shipments, filtered_inventory, filtered_demand = scope_supporting_tables_by_orders(
        filtered_orders=filtered_orders,
        shipments=filtered_shipments,
        inventory=filtered_inventory,
    )

    risk_summary = calculate_risk_summary(
        filtered_orders,
        filtered_shipments,
        filtered_inventory,
        filtered_demand,
    )

    region_risk = calculate_region_risk(filtered_orders, filtered_inventory)
    category_risk = calculate_category_risk(filtered_orders, filtered_inventory)

    if region_risk.empty or category_risk.empty:
        st.warning("Not enough data available to calculate risk indicators.")
        return

    show_kpis(risk_summary)
    show_risk_gauge(risk_summary)
    show_charts(
        filtered_orders,
        filtered_inventory,
        filtered_demand,
        region_risk,
        category_risk,
    )
    show_tables(region_risk, category_risk, filtered_inventory)


if __name__ == "__main__":
    main()