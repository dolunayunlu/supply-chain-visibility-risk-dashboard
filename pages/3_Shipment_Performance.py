from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

SHIPMENTS_PATH = PROCESSED_DIR / "shipments_clean.csv"
ORDERS_PATH = PROCESSED_DIR / "orders_clean.csv"


st.set_page_config(
    page_title="Shipment Tracking",
    page_icon="🚚",
    layout="wide",
)


@st.cache_data
def load_data():
    """Load shipment and order datasets."""
    shipments = pd.read_csv(SHIPMENTS_PATH)
    orders = pd.read_csv(ORDERS_PATH)

    shipments["shipping_date"] = pd.to_datetime(
        shipments["shipping_date"], errors="coerce"
    )
    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")

    shipments["year_month"] = shipments["shipping_date"].dt.to_period("M").astype(str)

    return shipments, orders


def create_filter_options(series: pd.Series):
    values = sorted(series.dropna().unique())
    return ["All"] + values


def apply_filters(shipments: pd.DataFrame) -> pd.DataFrame:
    """Apply sidebar filters."""

    st.sidebar.title("Filters")
    st.sidebar.caption("Filter shipment performance by market, region, country, and shipping mode.")

    market_options = create_filter_options(shipments["market"])
    selected_market = st.sidebar.selectbox("Market", market_options)

    if selected_market != "All":
        shipments = shipments[shipments["market"] == selected_market]

    region_options = create_filter_options(shipments["order_region"])
    selected_region = st.sidebar.selectbox("Order Region", region_options)

    if selected_region != "All":
        shipments = shipments[shipments["order_region"] == selected_region]

    country_options = create_filter_options(shipments["order_country"])
    selected_country = st.sidebar.selectbox("Order Country", country_options)

    if selected_country != "All":
        shipments = shipments[shipments["order_country"] == selected_country]

    shipping_mode_options = create_filter_options(shipments["shipping_mode"])
    selected_shipping_mode = st.sidebar.selectbox("Shipping Mode", shipping_mode_options)

    if selected_shipping_mode != "All":
        shipments = shipments[shipments["shipping_mode"] == selected_shipping_mode]

    delivery_status_options = create_filter_options(shipments["delivery_status"])
    selected_delivery_status = st.sidebar.selectbox("Delivery Status", delivery_status_options)

    if selected_delivery_status != "All":
        shipments = shipments[shipments["delivery_status"] == selected_delivery_status]

    min_date = shipments["shipping_date"].min()
    max_date = shipments["shipping_date"].max()

    if pd.notna(min_date) and pd.notna(max_date):
        selected_date_range = st.sidebar.date_input(
            "Shipping Date Range",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date(),
        )

        if len(selected_date_range) == 2:
            start_date, end_date = selected_date_range
            shipments = shipments[
                (shipments["shipping_date"].dt.date >= start_date)
                & (shipments["shipping_date"].dt.date <= end_date)
            ]

    return shipments


def calculate_shipping_mode_performance(shipments: pd.DataFrame) -> pd.DataFrame:
    """Calculate performance by shipping mode."""

    perf = (
        shipments.groupby("shipping_mode")
        .agg(
            total_shipments=("shipment_id", "nunique"),
            delayed_shipments=("is_late", "sum"),
            late_delivery_rate=("is_late", "mean"),
            avg_actual_shipping_days=("actual_shipping_days", "mean"),
            avg_scheduled_shipping_days=("scheduled_shipping_days", "mean"),
            avg_delay_days=("delay_days", "mean"),
        )
        .reset_index()
    )

    perf["late_delivery_rate_pct"] = (perf["late_delivery_rate"] * 100).round(2)

    return perf.sort_values("late_delivery_rate_pct", ascending=False)


def calculate_region_performance(shipments: pd.DataFrame) -> pd.DataFrame:
    """Calculate shipment performance by region."""

    region_perf = (
        shipments.groupby(["market", "order_region"])
        .agg(
            total_shipments=("shipment_id", "nunique"),
            delayed_shipments=("is_late", "sum"),
            late_delivery_rate=("is_late", "mean"),
            avg_actual_shipping_days=("actual_shipping_days", "mean"),
            avg_scheduled_shipping_days=("scheduled_shipping_days", "mean"),
            avg_delay_days=("delay_days", "mean"),
        )
        .reset_index()
    )

    region_perf["late_delivery_rate_pct"] = (
        region_perf["late_delivery_rate"] * 100
    ).round(2)

    return region_perf.sort_values("late_delivery_rate_pct", ascending=False)


def show_kpis(shipments: pd.DataFrame, shipping_mode_perf: pd.DataFrame):
    """Display shipment KPI cards."""

    total_shipments = shipments["shipment_id"].nunique()
    delayed_shipments = int(shipments["is_late"].sum())
    late_delivery_rate = shipments["is_late"].mean() * 100

    avg_actual_shipping_days = shipments["actual_shipping_days"].mean()
    avg_scheduled_shipping_days = shipments["scheduled_shipping_days"].mean()
    avg_delay_days = shipments["delay_days"].mean()

    if not shipping_mode_perf.empty:
        worst_shipping_mode = shipping_mode_perf.iloc[0]["shipping_mode"]
    else:
        worst_shipping_mode = "-"

    st.subheader("Shipment Performance Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Shipments", f"{total_shipments:,}")
    col2.metric("Delayed Shipments", f"{delayed_shipments:,}")
    col3.metric("Late Delivery Rate", f"{late_delivery_rate:.1f}%")
    col4.metric("Worst Shipping Mode", worst_shipping_mode)

    col5, col6, col7 = st.columns(3)

    col5.metric("Avg. Actual Shipping Days", f"{avg_actual_shipping_days:.1f}")
    col6.metric("Avg. Scheduled Shipping Days", f"{avg_scheduled_shipping_days:.1f}")
    col7.metric("Avg. Delay Days", f"{avg_delay_days:.1f}")


def show_charts(
    shipments: pd.DataFrame,
    shipping_mode_perf: pd.DataFrame,
    region_perf: pd.DataFrame,
):
    """Display shipment tracking charts."""

    st.divider()

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Delivery Status Distribution")

        delivery_status = (
            shipments["delivery_status"]
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
            yaxis_title="Number of Shipments",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)

    with right_col:
        st.subheader("Late Delivery Rate by Shipping Mode")

        fig = px.bar(
            shipping_mode_perf,
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

    left_col2, right_col2 = st.columns(2)

    with left_col2:
        st.subheader("Average Delay by Shipping Mode")

        delay_mode = shipping_mode_perf.sort_values("avg_delay_days", ascending=False)

        fig = px.bar(
            delay_mode,
            x="shipping_mode",
            y="avg_delay_days",
            title="Average Delay Days by Shipping Mode",
        )

        fig.update_layout(
            xaxis_title="Shipping Mode",
            yaxis_title="Average Delay Days",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)

    with right_col2:
        st.subheader("Actual vs Scheduled Shipping Days")

        mode_compare = shipping_mode_perf.melt(
            id_vars="shipping_mode",
            value_vars=["avg_actual_shipping_days", "avg_scheduled_shipping_days"],
            var_name="metric",
            value_name="days",
        )

        fig = px.bar(
            mode_compare,
            x="shipping_mode",
            y="days",
            color="metric",
            barmode="group",
            title="Actual vs Scheduled Shipping Days",
        )

        fig.update_layout(
            xaxis_title="Shipping Mode",
            yaxis_title="Average Days",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)

    left_col3, right_col3 = st.columns(2)

    with left_col3:
        st.subheader("Monthly Late Delivery Trend")

        monthly_late = (
            shipments.groupby("year_month")
            .agg(
                total_shipments=("shipment_id", "nunique"),
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
            title="Monthly Late Delivery Rate",
        )

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Late Delivery Rate (%)",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)

    with right_col3:
        st.subheader("Top Regions by Late Delivery Rate")

        top_regions = region_perf.head(15)

        fig = px.bar(
            top_regions,
            x="late_delivery_rate_pct",
            y="order_region",
            orientation="h",
            color="market",
            title="Top 15 Regions by Late Delivery Rate",
        )

        fig.update_layout(
            xaxis_title="Late Delivery Rate (%)",
            yaxis_title="Region",
            height=500,
        )

        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Market and Shipping Mode Risk Heatmap")

    heatmap_data = (
        shipments.groupby(["market", "shipping_mode"])["is_late"]
        .mean()
        .reset_index()
    )

    heatmap_data["late_delivery_rate_pct"] = heatmap_data["is_late"] * 100

    pivot = heatmap_data.pivot(
        index="market",
        columns="shipping_mode",
        values="late_delivery_rate_pct",
    )

    fig = px.imshow(
        pivot,
        text_auto=".1f",
        aspect="auto",
        title="Late Delivery Rate (%) by Market and Shipping Mode",
    )

    fig.update_layout(
        xaxis_title="Shipping Mode",
        yaxis_title="Market",
        height=500,
    )

    st.plotly_chart(fig, use_container_width=True)


def show_tables(
    shipments: pd.DataFrame,
    shipping_mode_perf: pd.DataFrame,
    region_perf: pd.DataFrame,
):
    """Display shipment performance tables."""

    st.divider()

    st.subheader("Shipping Mode Performance Table")

    shipping_table = shipping_mode_perf[
        [
            "shipping_mode",
            "total_shipments",
            "delayed_shipments",
            "late_delivery_rate_pct",
            "avg_actual_shipping_days",
            "avg_scheduled_shipping_days",
            "avg_delay_days",
        ]
    ].copy()

    st.dataframe(
        shipping_table,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("High-Risk Shipment Regions")

    region_table = region_perf[
        [
            "market",
            "order_region",
            "total_shipments",
            "delayed_shipments",
            "late_delivery_rate_pct",
            "avg_actual_shipping_days",
            "avg_scheduled_shipping_days",
            "avg_delay_days",
        ]
    ].copy()

    st.dataframe(
        region_table.head(30),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Shipment Data Preview")

    preview_columns = [
        "shipment_id",
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

    available_columns = [col for col in preview_columns if col in shipments.columns]

    st.dataframe(
        shipments[available_columns].head(100),
        use_container_width=True,
        hide_index=True,
    )


def main():
    shipments, orders = load_data()

    st.title("Shipment Tracking")

    st.markdown(
        """
        This page analyzes shipment performance, delivery status, late delivery risk,
        shipping mode efficiency, and regional delay patterns.
        """
    )

    with st.expander("How is shipment delay calculated?", expanded=False):
        st.write(
            """
            Shipment delay is calculated by comparing actual shipping days with scheduled shipping days.

            Delay Days = Actual Shipping Days - Scheduled Shipping Days

            If the result is below zero, it is treated as zero. Late delivery rate is calculated
            using the late delivery risk field from the processed dataset.
            """
        )

    filtered_shipments = apply_filters(shipments)

    if filtered_shipments.empty:
        st.warning("No shipment records available for the selected filters.")
        return

    shipping_mode_perf = calculate_shipping_mode_performance(filtered_shipments)
    region_perf = calculate_region_performance(filtered_shipments)

    show_kpis(filtered_shipments, shipping_mode_perf)
    show_charts(filtered_shipments, shipping_mode_perf, region_perf)
    show_tables(filtered_shipments, shipping_mode_perf, region_perf)


if __name__ == "__main__":
    main()