from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

ORDERS_PATH = PROCESSED_DIR / "orders_clean.csv"
SHIPMENTS_PATH = PROCESSED_DIR / "shipments_clean.csv"
INVENTORY_PATH = PROCESSED_DIR / "inventory_generated.csv"
RISK_PATH = PROCESSED_DIR / "risk_scores.csv"


st.set_page_config(
    page_title="Supply Chain Visibility and Risk Dashboard",
    page_icon="📦",
    layout="wide",
)


@st.cache_data
def load_data():
    orders = pd.read_csv(ORDERS_PATH)
    shipments = pd.read_csv(SHIPMENTS_PATH)
    inventory = pd.read_csv(INVENTORY_PATH)
    risk = pd.read_csv(RISK_PATH)

    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    orders["shipping_date"] = pd.to_datetime(orders["shipping_date"], errors="coerce")

    return orders, shipments, inventory, risk


def format_percent(value):
    return f"{value:.1f}%"


def main():
    st.title("Supply Chain Visibility and Risk Dashboard")

    st.write(
        """
        This dashboard monitors delivery performance, inventory status, shipment delays,
        and operational risk using a cleaned public supply chain dataset.
        """
    )

    orders, shipments, inventory, risk = load_data()

    # Sidebar filters
    st.sidebar.header("Filters")

    selected_market = st.sidebar.multiselect(
        "Market",
        options=sorted(orders["market"].dropna().unique()),
        default=sorted(orders["market"].dropna().unique()),
    )

    selected_category = st.sidebar.multiselect(
        "Product Category",
        options=sorted(orders["category_name"].dropna().unique()),
        default=sorted(orders["category_name"].dropna().unique()),
    )

    filtered_orders = orders[
        (orders["market"].isin(selected_market))
        & (orders["category_name"].isin(selected_category))
    ]

    if filtered_orders.empty:
        st.warning("No data available for the selected filters.")
        return

    # KPI calculations
    total_orders = filtered_orders["order_id"].nunique()
    total_sales = filtered_orders["sales"].sum()
    avg_shipping_days = filtered_orders["actual_shipping_days"].mean()
    late_delivery_rate = filtered_orders["is_late"].mean() * 100
    on_time_delivery_rate = 100 - late_delivery_rate
    avg_delay_days = filtered_orders["delay_days"].mean()

    critical_stock_items = inventory[
        inventory["inventory_status"] == "Critical"
    ].shape[0]

    high_risk_regions = risk[risk["risk_level"] == "High"].shape[0]

    st.subheader("Executive Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Orders", f"{total_orders:,}")
    col2.metric("Total Sales", f"${total_sales:,.0f}")
    col3.metric("On-Time Delivery Rate", format_percent(on_time_delivery_rate))
    col4.metric("Late Delivery Rate", format_percent(late_delivery_rate))

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("Avg. Shipping Days", f"{avg_shipping_days:.1f}")
    col6.metric("Avg. Delay Days", f"{avg_delay_days:.1f}")
    col7.metric("Critical Stock Items", critical_stock_items)
    col8.metric("High-Risk Regions", high_risk_regions)

    st.divider()

    # Charts
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Monthly Order Volume")

        monthly_orders = (
            filtered_orders.groupby("year_month")["order_id"]
            .nunique()
            .reset_index()
            .rename(columns={"order_id": "total_orders"})
        )

        fig_monthly = px.line(
            monthly_orders,
            x="year_month",
            y="total_orders",
            markers=True,
            title="Monthly Order Volume",
        )

        fig_monthly.update_layout(
            xaxis_title="Month",
            yaxis_title="Number of Orders",
        )

        st.plotly_chart(fig_monthly, use_container_width=True)

    with right_col:
        st.subheader("Delivery Status Distribution")

        delivery_status = (
            filtered_orders["delivery_status"]
            .value_counts()
            .reset_index()
        )

        delivery_status.columns = ["delivery_status", "count"]

        fig_delivery = px.bar(
            delivery_status,
            x="delivery_status",
            y="count",
            title="Delivery Status Distribution",
        )

        fig_delivery.update_layout(
            xaxis_title="Delivery Status",
            yaxis_title="Number of Orders",
        )

        st.plotly_chart(fig_delivery, use_container_width=True)

    left_col2, right_col2 = st.columns(2)

    with left_col2:
        st.subheader("Average Delay by Shipping Mode")

        delay_by_mode = (
            filtered_orders.groupby("shipping_mode")["delay_days"]
            .mean()
            .reset_index()
            .sort_values("delay_days", ascending=False)
        )

        fig_delay_mode = px.bar(
            delay_by_mode,
            x="shipping_mode",
            y="delay_days",
            title="Average Delay by Shipping Mode",
        )

        fig_delay_mode.update_layout(
            xaxis_title="Shipping Mode",
            yaxis_title="Average Delay Days",
        )

        st.plotly_chart(fig_delay_mode, use_container_width=True)

    with right_col2:
        st.subheader("Inventory Status Summary")

        inventory_status = (
            inventory["inventory_status"]
            .value_counts()
            .reset_index()
        )

        inventory_status.columns = ["inventory_status", "count"]

        fig_inventory = px.bar(
            inventory_status,
            x="inventory_status",
            y="count",
            title="Inventory Status Summary",
        )

        fig_inventory.update_layout(
            xaxis_title="Inventory Status",
            yaxis_title="Number of Products",
        )

        st.plotly_chart(fig_inventory, use_container_width=True)

    st.divider()

    st.subheader("Sample Cleaned Order Data")
    st.dataframe(filtered_orders.head(50), use_container_width=True)


if __name__ == "__main__":
    main()