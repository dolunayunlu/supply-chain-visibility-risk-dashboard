from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

ORDERS_PATH = PROCESSED_DIR / "orders_clean.csv"
INVENTORY_PATH = PROCESSED_DIR / "inventory_generated.csv"
RISK_PATH = PROCESSED_DIR / "risk_scores.csv"


st.set_page_config(
    page_title="Supply Chain Visibility and Risk Dashboard",
    page_icon="📦",
    layout="wide",
)


@st.cache_data
def load_data():
    """Load processed dashboard datasets."""
    orders = pd.read_csv(ORDERS_PATH)
    inventory = pd.read_csv(INVENTORY_PATH)
    risk = pd.read_csv(RISK_PATH)

    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    orders["shipping_date"] = pd.to_datetime(orders["shipping_date"], errors="coerce")

    return orders, inventory, risk


def format_percent(value: float) -> str:
    return f"{value:.1f}%"


def create_filter_options(series: pd.Series):
    values = sorted(series.dropna().unique())
    return ["All"] + values


def apply_filters(orders: pd.DataFrame) -> pd.DataFrame:
    """Apply sidebar filters to the orders dataset."""

    st.sidebar.title("Filters")
    st.sidebar.caption("Use the filters below to narrow the dashboard view.")

    market_options = create_filter_options(orders["market"])
    selected_market = st.sidebar.selectbox("Market", market_options)

    if selected_market != "All":
        orders = orders[orders["market"] == selected_market]

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


def calculate_kpis(orders: pd.DataFrame, inventory: pd.DataFrame, risk: pd.DataFrame):
    """Calculate main dashboard KPIs."""

    total_orders = orders["order_id"].nunique()
    total_sales = orders["sales"].sum()
    total_profit = orders["order_profit"].sum()

    late_delivery_rate = orders["is_late"].mean() * 100
    on_time_delivery_rate = 100 - late_delivery_rate

    avg_shipping_days = orders["actual_shipping_days"].mean()
    avg_delay_days = orders["delay_days"].mean()

    critical_stock_items = inventory[
        inventory["inventory_status"] == "Critical"
    ].shape[0]

    warning_stock_items = inventory[
        inventory["inventory_status"] == "Warning"
    ].shape[0]

    high_risk_regions = risk[risk["risk_level"] == "High"].shape[0]

    return {
        "total_orders": total_orders,
        "total_sales": total_sales,
        "total_profit": total_profit,
        "on_time_delivery_rate": on_time_delivery_rate,
        "late_delivery_rate": late_delivery_rate,
        "avg_shipping_days": avg_shipping_days,
        "avg_delay_days": avg_delay_days,
        "critical_stock_items": critical_stock_items,
        "warning_stock_items": warning_stock_items,
        "high_risk_regions": high_risk_regions,
    }


def show_kpis(kpis: dict):
    """Display executive KPI cards."""

    st.subheader("Executive Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Orders", f"{kpis['total_orders']:,}")
    col2.metric("Total Sales", f"${kpis['total_sales']:,.0f}")
    col3.metric("Total Profit", f"${kpis['total_profit']:,.0f}")
    col4.metric("On-Time Delivery Rate", format_percent(kpis["on_time_delivery_rate"]))

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("Late Delivery Rate", format_percent(kpis["late_delivery_rate"]))
    col6.metric("Avg. Shipping Days", f"{kpis['avg_shipping_days']:.1f}")
    col7.metric("Avg. Delay Days", f"{kpis['avg_delay_days']:.1f}")
    col8.metric("High-Risk Regions", kpis["high_risk_regions"])

    col9, col10 = st.columns(2)

    col9.metric("Critical Stock Items", kpis["critical_stock_items"])
    col10.metric("Warning Stock Items", kpis["warning_stock_items"])


def show_charts(orders: pd.DataFrame, inventory: pd.DataFrame, risk: pd.DataFrame):
    """Display overview dashboard charts."""

    st.divider()

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Monthly Order Volume")

        monthly_orders = (
            orders.groupby("year_month")["order_id"]
            .nunique()
            .reset_index()
            .rename(columns={"order_id": "total_orders"})
            .sort_values("year_month")
        )

        fig = px.line(
            monthly_orders,
            x="year_month",
            y="total_orders",
            markers=True,
            title="Monthly Order Volume",
        )

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Number of Orders",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)

    with right_col:
        st.subheader("Delivery Status Distribution")

        delivery_status = (
            orders["delivery_status"]
            .value_counts()
            .reset_index()
        )

        delivery_status.columns = ["delivery_status", "count"]

        fig = px.bar(
            delivery_status,
            x="delivery_status",
            y="count",
            title="Delivery Status Distribution",
        )

        fig.update_layout(
            xaxis_title="Delivery Status",
            yaxis_title="Number of Orders",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)

    left_col2, right_col2 = st.columns(2)

    with left_col2:
        st.subheader("Average Delay by Shipping Mode")

        delay_by_mode = (
            orders.groupby("shipping_mode")["delay_days"]
            .mean()
            .reset_index()
            .sort_values("delay_days", ascending=False)
        )

        fig = px.bar(
            delay_by_mode,
            x="shipping_mode",
            y="delay_days",
            title="Average Delay by Shipping Mode",
        )

        fig.update_layout(
            xaxis_title="Shipping Mode",
            yaxis_title="Average Delay Days",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)

    with right_col2:
        st.subheader("Order Volume by Market")

        market_orders = (
            orders.groupby("market")["order_id"]
            .nunique()
            .reset_index()
            .rename(columns={"order_id": "total_orders"})
            .sort_values("total_orders", ascending=False)
        )

        fig = px.bar(
            market_orders,
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

    left_col3, right_col3 = st.columns(2)

    with left_col3:
        st.subheader("Inventory Status Summary")

        inventory_status = (
            inventory["inventory_status"]
            .value_counts()
            .reset_index()
        )

        inventory_status.columns = ["inventory_status", "count"]

        fig = px.bar(
            inventory_status,
            x="inventory_status",
            y="count",
            title="Inventory Status Summary",
        )

        fig.update_layout(
            xaxis_title="Inventory Status",
            yaxis_title="Number of Products",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)

    with right_col3:
        st.subheader("Risk Level Distribution")

        risk_status = (
            risk["risk_level"]
            .value_counts()
            .reset_index()
        )

        risk_status.columns = ["risk_level", "count"]

        fig = px.bar(
            risk_status,
            x="risk_level",
            y="count",
            title="Region Risk Level Distribution",
        )

        fig.update_layout(
            xaxis_title="Risk Level",
            yaxis_title="Number of Regions",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)


def show_data_preview(orders: pd.DataFrame):
    """Display a sample of cleaned order data."""

    st.divider()
    st.subheader("Cleaned Order Data Preview")

    preview_columns = [
        "order_id",
        "order_status",
        "market",
        "order_region",
        "order_country",
        "category_name",
        "product_name",
        "shipping_mode",
        "delivery_status",
        "actual_shipping_days",
        "scheduled_shipping_days",
        "delay_days",
        "sales",
        "order_profit",
    ]

    available_columns = [col for col in preview_columns if col in orders.columns]

    st.dataframe(
        orders[available_columns].head(100),
        use_container_width=True,
        hide_index=True,
    )


def main():
    orders, inventory, risk = load_data()

    st.title("Supply Chain Visibility and Risk Dashboard")

    st.markdown(
        """
        This dashboard provides a decision-support view of supply chain operations by monitoring
        order volume, delivery performance, inventory status, and operational risk indicators.
        """
    )

    with st.expander("Dataset and project note", expanded=False):
        st.write(
            """
            This project uses the public DataCo Smart Supply Chain dataset as the main operational dataset.
            The original dataset includes order, product, shipping, delivery, sales, and profit information.
            Inventory-related fields are generated from product demand patterns for academic dashboard demonstration.
            """
        )

    filtered_orders = apply_filters(orders)

    if filtered_orders.empty:
        st.warning("No data available for the selected filters.")
        return

    kpis = calculate_kpis(filtered_orders, inventory, risk)

    show_kpis(kpis)
    show_charts(filtered_orders, inventory, risk)
    show_data_preview(filtered_orders)


if __name__ == "__main__":
    main()