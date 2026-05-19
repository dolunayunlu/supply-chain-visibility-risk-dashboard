from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

INVENTORY_PATH = PROCESSED_DIR / "inventory_generated.csv"
ORDERS_PATH = PROCESSED_DIR / "orders_clean.csv"


st.set_page_config(
    page_title="Inventory Monitoring",
    page_icon="📦",
    layout="wide",
)


@st.cache_data
def load_data():
    """Load inventory and order datasets."""
    inventory = pd.read_csv(INVENTORY_PATH)
    orders = pd.read_csv(ORDERS_PATH)

    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")

    return inventory, orders


def create_filter_options(series: pd.Series):
    values = sorted(series.dropna().unique())
    return ["All"] + values


def add_inventory_metrics(inventory: pd.DataFrame) -> pd.DataFrame:
    """Add calculated inventory risk fields."""

    inventory = inventory.copy()

    inventory["stock_gap"] = inventory["current_stock"] - inventory["reorder_point"]

    inventory["stock_gap_pct"] = (
        inventory["stock_gap"] / inventory["reorder_point"] * 100
    ).round(2)

    def calculate_inventory_risk(row):
        if row["inventory_status"] == "Critical":
            return 100
        if row["inventory_status"] == "Warning":
            return 60
        return 20

    inventory["inventory_risk_score"] = inventory.apply(
        calculate_inventory_risk, axis=1
    )

    return inventory


def apply_filters(inventory: pd.DataFrame) -> pd.DataFrame:
    """Apply sidebar filters."""

    st.sidebar.title("Filters")
    st.sidebar.caption("Filter inventory items by category, status, and product name.")

    category_options = create_filter_options(inventory["category_name"])
    selected_category = st.sidebar.selectbox("Product Category", category_options)

    if selected_category != "All":
        inventory = inventory[inventory["category_name"] == selected_category]

    status_options = create_filter_options(inventory["inventory_status"])
    selected_status = st.sidebar.selectbox("Inventory Status", status_options)

    if selected_status != "All":
        inventory = inventory[inventory["inventory_status"] == selected_status]

    search_text = st.sidebar.text_input("Search Product Name")

    if search_text:
        inventory = inventory[
            inventory["product_name"].str.contains(
                search_text, case=False, na=False
            )
        ]

    return inventory


def show_kpis(inventory: pd.DataFrame):
    """Display inventory KPI cards."""

    total_products = inventory["product_id"].nunique()
    total_stock_units = inventory["current_stock"].sum()

    critical_items = inventory[inventory["inventory_status"] == "Critical"].shape[0]
    warning_items = inventory[inventory["inventory_status"] == "Warning"].shape[0]
    healthy_items = inventory[inventory["inventory_status"] == "Healthy"].shape[0]

    avg_days_of_supply = inventory["days_of_supply"].mean()
    avg_inventory_risk = inventory["inventory_risk_score"].mean()

    st.subheader("Inventory Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Products", f"{total_products:,}")
    col2.metric("Total Stock Units", f"{total_stock_units:,.0f}")
    col3.metric("Critical Items", critical_items)
    col4.metric("Warning Items", warning_items)

    col5, col6, col7 = st.columns(3)

    col5.metric("Healthy Items", healthy_items)
    col6.metric("Avg. Days of Supply", f"{avg_days_of_supply:.1f}")
    col7.metric("Avg. Inventory Risk Score", f"{avg_inventory_risk:.1f}")


def show_charts(inventory: pd.DataFrame):
    """Display inventory monitoring charts."""

    st.divider()

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Inventory Status Summary")

        status_summary = (
            inventory["inventory_status"]
            .value_counts()
            .reset_index()
        )

        status_summary.columns = ["inventory_status", "count"]

        fig = px.bar(
            status_summary,
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

    with right_col:
        st.subheader("Inventory Risk by Category")

        category_risk = (
            inventory.groupby("category_name")
            .agg(
                avg_inventory_risk=("inventory_risk_score", "mean"),
                product_count=("product_id", "nunique"),
            )
            .reset_index()
            .sort_values("avg_inventory_risk", ascending=False)
            .head(15)
        )

        fig = px.bar(
            category_risk,
            x="avg_inventory_risk",
            y="category_name",
            orientation="h",
            title="Top Categories by Average Inventory Risk",
        )

        fig.update_layout(
            xaxis_title="Average Inventory Risk Score",
            yaxis_title="Product Category",
            height=500,
        )

        st.plotly_chart(fig, use_container_width=True)

    left_col2, right_col2 = st.columns(2)

    with left_col2:
        st.subheader("Stock Level vs Reorder Point")

        stock_compare = inventory.sort_values("inventory_risk_score", ascending=False).head(25)

        stock_compare_melted = stock_compare.melt(
            id_vars=["product_name", "inventory_status"],
            value_vars=["current_stock", "reorder_point", "safety_stock"],
            var_name="metric",
            value_name="units",
        )

        fig = px.bar(
            stock_compare_melted,
            x="product_name",
            y="units",
            color="metric",
            barmode="group",
            title="Stock Level, Reorder Point and Safety Stock",
        )

        fig.update_layout(
            xaxis_title="Product",
            yaxis_title="Units",
            height=520,
            xaxis_tickangle=-45,
        )

        st.plotly_chart(fig, use_container_width=True)

    with right_col2:
        st.subheader("Lowest Days of Supply")

        lowest_supply = inventory.sort_values("days_of_supply", ascending=True).head(20)

        fig = px.bar(
            lowest_supply,
            x="days_of_supply",
            y="product_name",
            orientation="h",
            color="inventory_status",
            title="Products with Lowest Days of Supply",
        )

        fig.update_layout(
            xaxis_title="Days of Supply",
            yaxis_title="Product",
            height=520,
        )

        st.plotly_chart(fig, use_container_width=True)

    left_col3, right_col3 = st.columns(2)

    with left_col3:
        st.subheader("Stock Gap by Product")

        stock_gap = inventory.sort_values("stock_gap", ascending=True).head(20)

        fig = px.bar(
            stock_gap,
            x="stock_gap",
            y="product_name",
            orientation="h",
            color="inventory_status",
            title="Products with Lowest Stock Gap",
        )

        fig.update_layout(
            xaxis_title="Current Stock - Reorder Point",
            yaxis_title="Product",
            height=520,
        )

        st.plotly_chart(fig, use_container_width=True)

    with right_col3:
        st.subheader("Inventory Status by Category")

        category_status = (
            inventory.groupby(["category_name", "inventory_status"])
            .size()
            .reset_index(name="count")
        )

        fig = px.bar(
            category_status,
            x="category_name",
            y="count",
            color="inventory_status",
            title="Inventory Status by Category",
        )

        fig.update_layout(
            xaxis_title="Product Category",
            yaxis_title="Number of Products",
            height=520,
            xaxis_tickangle=-45,
        )

        st.plotly_chart(fig, use_container_width=True)


def show_tables(inventory: pd.DataFrame):
    """Display inventory tables."""

    st.divider()

    st.subheader("Critical and Warning Inventory Items")

    risk_table = inventory[
        inventory["inventory_status"].isin(["Critical", "Warning"])
    ].copy()

    risk_table = risk_table.sort_values(
        ["inventory_risk_score", "days_of_supply"],
        ascending=[False, True],
    )

    display_columns = [
        "product_id",
        "product_name",
        "category_name",
        "current_stock",
        "reorder_point",
        "safety_stock",
        "average_daily_demand",
        "days_of_supply",
        "stock_gap",
        "stock_gap_pct",
        "inventory_status",
        "inventory_risk_score",
    ]

    st.dataframe(
        risk_table[display_columns],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Full Inventory Table")

    full_table = inventory.sort_values("inventory_risk_score", ascending=False)

    st.dataframe(
        full_table[display_columns],
        use_container_width=True,
        hide_index=True,
    )


def main():
    inventory, orders = load_data()
    inventory = add_inventory_metrics(inventory)

    st.title("Inventory Monitoring")

    st.markdown(
        """
        This page monitors inventory health across product categories. It identifies
        products with critical stock levels, low days of supply, and high replenishment risk.
        """
    )

    with st.expander("How is inventory status calculated?", expanded=False):
        st.write(
            """
            Inventory status is calculated by comparing current stock with reorder point
            and safety stock.

            - Critical: current stock is below reorder point
            - Warning: current stock is above reorder point but below reorder point + safety stock
            - Healthy: current stock is above reorder point + safety stock

            The original dataset does not include inventory planning fields, so inventory values
            were generated from product demand patterns for academic dashboard demonstration.
            """
        )

    filtered_inventory = apply_filters(inventory)

    if filtered_inventory.empty:
        st.warning("No inventory records available for the selected filters.")
        return

    show_kpis(filtered_inventory)
    show_charts(filtered_inventory)
    show_tables(filtered_inventory)


if __name__ == "__main__":
    main()