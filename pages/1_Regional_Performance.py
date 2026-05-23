from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_adapter import get_active_dashboard_data


BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

ORDERS_PATH = PROCESSED_DIR / "orders_clean.csv"
RISK_PATH = PROCESSED_DIR / "risk_scores.csv"


st.set_page_config(
    page_title="Region & Market Performance",
    page_icon="🌍",
    layout="wide",
)


def load_data():
    """Load active dashboard data."""
    dashboard_data = get_active_dashboard_data()

    orders = dashboard_data["orders"]
    risk = dashboard_data["risk"]
    inventory = dashboard_data["inventory"]

    return orders, risk, inventory


def create_filter_options(series: pd.Series):
    values = sorted(series.dropna().unique())
    return ["All"] + values


def apply_filters(orders: pd.DataFrame) -> pd.DataFrame:
    """Apply sidebar filters."""

    st.sidebar.title("Filters")
    st.sidebar.caption("Filter regional and market performance.")

    market_options = create_filter_options(orders["market"])
    selected_market = st.sidebar.selectbox("Market", market_options)

    if selected_market != "All":
        orders = orders[orders["market"] == selected_market]

    region_options = create_filter_options(orders["order_region"])
    selected_region = st.sidebar.selectbox("Order Region", region_options)

    if selected_region != "All":
        orders = orders[orders["order_region"] == selected_region]

    category_options = create_filter_options(orders["category_name"])
    selected_category = st.sidebar.selectbox("Product Category", category_options)

    if selected_category != "All":
        orders = orders[orders["category_name"] == selected_category]

    shipping_mode_options = create_filter_options(orders["shipping_mode"])
    selected_shipping_mode = st.sidebar.selectbox("Shipping Mode", shipping_mode_options)

    if selected_shipping_mode != "All":
        orders = orders[orders["shipping_mode"] == selected_shipping_mode]

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

    return orders


def calculate_region_performance(
    orders: pd.DataFrame,
    inventory: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate region-level performance metrics."""

    region_perf = (
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

    region_perf["late_delivery_rate_pct"] = (
        region_perf["late_delivery_rate"] * 100
    ).round(2)

    region_perf["profit_margin_pct"] = (
        region_perf["total_profit"] / region_perf["total_sales"] * 100
    ).round(2)

    max_delay = region_perf["avg_delay_days"].max()

    if max_delay == 0 or pd.isna(max_delay):
        region_perf["delay_risk_score"] = 0
    else:
        region_perf["delay_risk_score"] = (
            region_perf["avg_delay_days"] / max_delay * 100
        ).round(2)

    region_perf["late_delivery_risk_score"] = region_perf["late_delivery_rate_pct"]

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

    region_perf["inventory_risk_score"] = round(inventory_risk_score, 2)

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

    region_perf = region_perf.merge(
        demand_volatility[
            ["market", "order_region", "demand_volatility_risk_score"]
        ],
        on=["market", "order_region"],
        how="left",
    )

    region_perf["demand_volatility_risk_score"] = (
        region_perf["demand_volatility_risk_score"].fillna(0)
    )

    region_perf["performance_risk_score"] = (
        0.35 * region_perf["late_delivery_risk_score"]
        + 0.25 * region_perf["inventory_risk_score"]
        + 0.20 * region_perf["delay_risk_score"]
        + 0.20 * region_perf["demand_volatility_risk_score"]
    ).round(2)

    def classify_risk(score):
        if score < 40:
            return "Low"
        if score < 70:
            return "Medium"
        return "High"

    region_perf["risk_level"] = region_perf["performance_risk_score"].apply(
        classify_risk
    )

    return region_perf.sort_values("performance_risk_score", ascending=False)


def calculate_market_performance(orders: pd.DataFrame) -> pd.DataFrame:
    """Calculate market-level performance metrics."""

    market_perf = (
        orders.groupby("market")
        .agg(
            total_orders=("order_id", "nunique"),
            total_sales=("sales", "sum"),
            total_profit=("order_profit", "sum"),
            late_delivery_rate=("is_late", "mean"),
            avg_delay_days=("delay_days", "mean"),
        )
        .reset_index()
    )

    market_perf["late_delivery_rate_pct"] = (
        market_perf["late_delivery_rate"] * 100
    ).round(2)

    return market_perf.sort_values("total_orders", ascending=False)


def calculate_shipping_mode_performance(orders: pd.DataFrame) -> pd.DataFrame:
    """Calculate shipping-mode performance metrics."""

    shipping_perf = (
        orders.groupby("shipping_mode")
        .agg(
            total_orders=("order_id", "nunique"),
            late_delivery_rate=("is_late", "mean"),
            avg_delay_days=("delay_days", "mean"),
            avg_shipping_days=("actual_shipping_days", "mean"),
            total_sales=("sales", "sum"),
        )
        .reset_index()
    )

    shipping_perf["late_delivery_rate_pct"] = (
        shipping_perf["late_delivery_rate"] * 100
    ).round(2)

    return shipping_perf.sort_values("late_delivery_rate_pct", ascending=False)


def show_kpis(orders: pd.DataFrame, region_perf: pd.DataFrame):
    """Display top KPI cards."""

    total_markets = orders["market"].nunique()
    total_regions = orders["order_region"].nunique()
    total_countries = orders["order_country"].nunique()

    avg_late_delivery_rate = orders["is_late"].mean() * 100
    avg_delay_days = orders["delay_days"].mean()

    high_risk_regions = region_perf[region_perf["risk_level"] == "High"].shape[0]
    worst_region = region_perf.iloc[0]["order_region"] if not region_perf.empty else "-"

    st.subheader("Regional Performance Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Markets", total_markets)
    col2.metric("Regions", total_regions)
    col3.metric("Countries", total_countries)
    col4.metric("High-Risk Regions", high_risk_regions)

    col5, col6, col7 = st.columns(3)

    col5.metric("Late Delivery Rate", f"{avg_late_delivery_rate:.1f}%")
    col6.metric("Average Delay Days", f"{avg_delay_days:.1f}")
    col7.metric("Highest Risk Region", worst_region)


def show_charts(
    orders: pd.DataFrame,
    region_perf: pd.DataFrame,
    market_perf: pd.DataFrame,
    shipping_perf: pd.DataFrame,
):
    """Display regional and market performance charts."""

    st.divider()

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Order Volume by Market")

        fig = px.bar(
            market_perf,
            x="market",
            y="total_orders",
            title="Order Volume by Market",
        )

        fig.update_layout(
            xaxis_title="Market",
            yaxis_title="Number of Orders",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)

    with right_col:
        st.subheader("Late Delivery Rate by Market")

        fig = px.bar(
            market_perf.sort_values("late_delivery_rate_pct", ascending=False),
            x="market",
            y="late_delivery_rate_pct",
            title="Late Delivery Rate by Market",
        )

        fig.update_layout(
            xaxis_title="Market",
            yaxis_title="Late Delivery Rate (%)",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)

    left_col2, right_col2 = st.columns(2)

    with left_col2:
        st.subheader("Top 15 Regions by Risk Score")

        top_risk_regions = region_perf.head(15)

        fig = px.bar(
            top_risk_regions,
            x="performance_risk_score",
            y="order_region",
            orientation="h",
            color="risk_level",
            title="Top 15 Regions by Performance Risk Score",
        )

        fig.update_layout(
            xaxis_title="Risk Score",
            yaxis_title="Region",
            height=500,
        )

        st.plotly_chart(fig, use_container_width=True)

    with right_col2:
        st.subheader("Average Delay by Region")

        top_delay_regions = region_perf.sort_values(
            "avg_delay_days", ascending=False
        ).head(15)

        fig = px.bar(
            top_delay_regions,
            x="avg_delay_days",
            y="order_region",
            orientation="h",
            title="Top 15 Regions by Average Delay Days",
        )

        fig.update_layout(
            xaxis_title="Average Delay Days",
            yaxis_title="Region",
            height=500,
        )

        st.plotly_chart(fig, use_container_width=True)

    left_col3, right_col3 = st.columns(2)

    with left_col3:
        st.subheader("Sales and Profit by Market")

        market_financials = market_perf.melt(
            id_vars="market",
            value_vars=["total_sales", "total_profit"],
            var_name="metric",
            value_name="amount",
        )

        fig = px.bar(
            market_financials,
            x="market",
            y="amount",
            color="metric",
            barmode="group",
            title="Sales and Profit by Market",
        )

        fig.update_layout(
            xaxis_title="Market",
            yaxis_title="Amount",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)

    with right_col3:
        st.subheader("Shipping Mode Performance")

        fig = px.bar(
            shipping_perf,
            x="shipping_mode",
            y="late_delivery_rate_pct",
            title="Late Delivery Rate by Shipping Mode",
        )

        fig.update_layout(
            xaxis_title="Shipping Mode",
            yaxis_title="Late Delivery Rate (%)",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)


def show_tables(region_perf: pd.DataFrame, shipping_perf: pd.DataFrame):
    """Display performance tables."""

    st.divider()

    st.subheader("High-Risk Region Table")

    high_risk_table = region_perf[
        [
            "market",
            "order_region",
            "total_orders",
            "total_sales",
            "total_profit",
            "late_delivery_rate_pct",
            "avg_delay_days",
            "inventory_risk_score",
            "delay_risk_score",
            "demand_volatility_risk_score",
            "performance_risk_score",
            "risk_level",
        ]
    ].copy()

    high_risk_table = high_risk_table.sort_values(
        "performance_risk_score", ascending=False
    )

    st.dataframe(
        high_risk_table.head(30),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Shipping Mode Performance Table")

    shipping_table = shipping_perf[
        [
            "shipping_mode",
            "total_orders",
            "late_delivery_rate_pct",
            "avg_delay_days",
            "avg_shipping_days",
            "total_sales",
        ]
    ].copy()

    st.dataframe(
        shipping_table,
        use_container_width=True,
        hide_index=True,
    )


def main():
    orders, risk, inventory = load_data()

    st.title("Region & Market Performance")

    st.markdown(
        """
        This page analyzes supply chain performance across markets, regions, countries,
        and shipping modes. It helps identify areas with high late delivery rates,
        shipment delays, and operational risk.
        """
    )

    with st.expander("How is the regional risk score calculated?", expanded=False):
        st.write(
            """
            The regional performance risk score is calculated using late delivery risk,
            inventory risk, delay risk, and demand volatility risk. A higher score means
            that the region has weaker operational performance.

            Risk Score = 35% Delivery Risk + 25% Inventory Risk + 20% Delay Risk + 20% Demand Volatility Risk
            """
        )

    filtered_orders = apply_filters(orders)

    if filtered_orders.empty:
        st.warning("No data available for the selected filters.")
        return

    region_perf = calculate_region_performance(filtered_orders, inventory)
    market_perf = calculate_market_performance(filtered_orders)
    shipping_perf = calculate_shipping_mode_performance(filtered_orders)

    show_kpis(filtered_orders, region_perf)
    show_charts(filtered_orders, region_perf, market_perf, shipping_perf)
    show_tables(region_perf, shipping_perf)


if __name__ == "__main__":
    main()