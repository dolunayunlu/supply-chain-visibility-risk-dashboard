import io

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Dataset Upload Manager",
    page_icon="📤",
    layout="wide",
)


STANDARD_FIELDS = {
    "order_id": {
        "required": True,
        "description": "Unique order identifier",
        "keywords": ["order id", "order_id", "order", "id"],
    },
    "order_date": {
        "required": True,
        "description": "Order creation date",
        "keywords": ["order date", "order_date", "dateorders", "date"],
    },
    "product_name": {
        "required": True,
        "description": "Product name",
        "keywords": ["product name", "product_name", "product"],
    },
    "category_name": {
        "required": True,
        "description": "Product category",
        "keywords": ["category name", "category_name", "category"],
    },
    "order_quantity": {
        "required": True,
        "description": "Ordered quantity",
        "keywords": ["quantity", "qty", "order item quantity", "order_quantity"],
    },
    "shipping_date": {
        "required": False,
        "description": "Shipment or delivery date",
        "keywords": ["shipping date", "ship date", "delivery date", "shipping_date"],
    },
    "delivery_status": {
        "required": False,
        "description": "Delivery status",
        "keywords": ["delivery status", "status", "late", "on time"],
    },
    "actual_shipping_days": {
        "required": False,
        "description": "Actual shipping duration in days",
        "keywords": ["days for shipping", "actual shipping", "real", "actual_shipping_days"],
    },
    "scheduled_shipping_days": {
        "required": False,
        "description": "Scheduled shipping duration in days",
        "keywords": ["scheduled", "shipment scheduled", "scheduled_shipping_days"],
    },
    "shipping_mode": {
        "required": False,
        "description": "Shipping mode or carrier type",
        "keywords": ["shipping mode", "ship mode", "carrier", "shipping_mode"],
    },
    "market": {
        "required": False,
        "description": "Market or business region",
        "keywords": ["market"],
    },
    "order_region": {
        "required": False,
        "description": "Order region",
        "keywords": ["region", "order region", "order_region"],
    },
    "order_country": {
        "required": False,
        "description": "Order country",
        "keywords": ["country", "order country", "order_country"],
    },
    "sales": {
        "required": False,
        "description": "Sales amount",
        "keywords": ["sales", "revenue", "amount"],
    },
    "order_profit": {
        "required": False,
        "description": "Profit amount",
        "keywords": ["profit", "benefit", "margin"],
    },
}


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
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

    raise ValueError("Unsupported file type. Please upload a CSV or XLSX file.")


def suggest_column(field_name: str, columns: list[str]) -> str | None:
    """Suggest a matching source column for a standard field."""

    field_info = STANDARD_FIELDS[field_name]
    keywords = field_info["keywords"]

    normalized_columns = {col: col.lower().replace("_", " ").replace("-", " ") for col in columns}

    # Exact-ish keyword match first
    for keyword in keywords:
        keyword = keyword.lower()
        for original_col, normalized_col in normalized_columns.items():
            if keyword == normalized_col:
                return original_col

    # Partial match second
    for keyword in keywords:
        keyword = keyword.lower()
        for original_col, normalized_col in normalized_columns.items():
            if keyword in normalized_col:
                return original_col

    return None


def build_mapping_ui(df: pd.DataFrame) -> dict:
    """Build column mapping selectors."""

    st.subheader("Column Mapping")

    st.write(
        """
        Map the columns in your uploaded dataset to the standard supply chain schema.
        Required fields must be selected. Optional fields can be left as `Not available`.
        """
    )

    columns = list(df.columns)
    options = ["Not available"] + columns

    mapping = {}

    required_fields = [field for field, info in STANDARD_FIELDS.items() if info["required"]]
    optional_fields = [field for field, info in STANDARD_FIELDS.items() if not info["required"]]

    st.markdown("### Required Fields")

    for field in required_fields:
        suggested = suggest_column(field, columns)
        default_index = options.index(suggested) if suggested in options else 0

        mapping[field] = st.selectbox(
            label=f"{field} — {STANDARD_FIELDS[field]['description']}",
            options=options,
            index=default_index,
            key=f"mapping_required_{field}",
        )

    with st.expander("Optional Fields", expanded=False):
        for field in optional_fields:
            suggested = suggest_column(field, columns)
            default_index = options.index(suggested) if suggested in options else 0

            mapping[field] = st.selectbox(
                label=f"{field} — {STANDARD_FIELDS[field]['description']}",
                options=options,
                index=default_index,
                key=f"mapping_optional_{field}",
            )

    return mapping


def validate_mapping(mapping: dict) -> list[str]:
    """Validate required field mappings."""

    errors = []

    for field, info in STANDARD_FIELDS.items():
        if info["required"] and mapping.get(field) == "Not available":
            errors.append(f"Required field missing: {field}")

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


def safe_numeric(series: pd.Series, default_value: float = 0) -> pd.Series:
    """Convert a series to numeric safely."""

    return pd.to_numeric(series, errors="coerce").fillna(default_value)


def standardize_dataset(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Convert uploaded data into the standard analytical schema."""

    standardized = pd.DataFrame()

    # Required fields
    standardized["order_id"] = df[mapping["order_id"]].astype(str)
    standardized["order_date"] = pd.to_datetime(df[mapping["order_date"]], errors="coerce")
    standardized["product_name"] = df[mapping["product_name"]].astype(str)
    standardized["category_name"] = df[mapping["category_name"]].astype(str)
    standardized["order_quantity"] = safe_numeric(df[mapping["order_quantity"]], default_value=0)

    # Optional text fields
    optional_text_defaults = {
        "delivery_status": "Unknown",
        "shipping_mode": "Unknown",
        "market": "Unknown",
        "order_region": "Unknown",
        "order_country": "Unknown",
    }

    for field, default in optional_text_defaults.items():
        if mapping.get(field) != "Not available":
            standardized[field] = df[mapping[field]].astype(str)
        else:
            standardized[field] = default

    # Optional date field
    if mapping.get("shipping_date") != "Not available":
        standardized["shipping_date"] = pd.to_datetime(
            df[mapping["shipping_date"]],
            errors="coerce",
        )
    else:
        standardized["shipping_date"] = pd.NaT

    # Optional numeric fields
    if mapping.get("actual_shipping_days") != "Not available":
        standardized["actual_shipping_days"] = safe_numeric(
            df[mapping["actual_shipping_days"]],
            default_value=np.nan,
        )
    else:
        standardized["actual_shipping_days"] = np.nan

    if mapping.get("scheduled_shipping_days") != "Not available":
        standardized["scheduled_shipping_days"] = safe_numeric(
            df[mapping["scheduled_shipping_days"]],
            default_value=np.nan,
        )
    else:
        standardized["scheduled_shipping_days"] = np.nan

    if mapping.get("sales") != "Not available":
        standardized["sales"] = safe_numeric(df[mapping["sales"]], default_value=0)
    else:
        standardized["sales"] = 0

    if mapping.get("order_profit") != "Not available":
        standardized["order_profit"] = safe_numeric(df[mapping["order_profit"]], default_value=0)
    else:
        standardized["order_profit"] = 0

    # Derive actual shipping days from dates if not mapped
    missing_actual_days = standardized["actual_shipping_days"].isna()

    if standardized["shipping_date"].notna().any():
        calculated_days = (
            standardized["shipping_date"] - standardized["order_date"]
        ).dt.days

        standardized.loc[missing_actual_days, "actual_shipping_days"] = calculated_days

    standardized["actual_shipping_days"] = standardized["actual_shipping_days"].fillna(0)

    # If scheduled days are missing, use actual days as baseline
    standardized["scheduled_shipping_days"] = standardized["scheduled_shipping_days"].fillna(
        standardized["actual_shipping_days"]
    )

    standardized["delay_days"] = (
        standardized["actual_shipping_days"] - standardized["scheduled_shipping_days"]
    ).clip(lower=0)

    # Derive late flag
    status_lower = standardized["delivery_status"].astype(str).str.lower()

    status_based_late = status_lower.str.contains("late|delayed|delay", regex=True)

    delay_based_late = standardized["delay_days"] > 0

    standardized["is_late"] = (status_based_late | delay_based_late).astype(int)

    standardized["is_on_time"] = 1 - standardized["is_late"]

    standardized["year_month"] = standardized["order_date"].dt.to_period("M").astype(str)

    # Clean invalid dates
    standardized = standardized.dropna(subset=["order_date"])

    return standardized


def calculate_uploaded_kpis(data: pd.DataFrame) -> dict:
    """Calculate basic KPIs from standardized uploaded dataset."""

    total_orders = data["order_id"].nunique()
    total_quantity = data["order_quantity"].sum()
    total_sales = data["sales"].sum()
    total_profit = data["order_profit"].sum()
    late_delivery_rate = data["is_late"].mean() * 100 if len(data) else 0
    avg_delay_days = data["delay_days"].mean() if len(data) else 0
    categories = data["category_name"].nunique()
    markets = data["market"].nunique()

    return {
        "total_orders": total_orders,
        "total_quantity": total_quantity,
        "total_sales": total_sales,
        "total_profit": total_profit,
        "late_delivery_rate": late_delivery_rate,
        "avg_delay_days": avg_delay_days,
        "categories": categories,
        "markets": markets,
    }


def show_uploaded_kpis(kpis: dict) -> None:
    """Display KPI cards."""

    st.subheader("Generated KPIs")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Orders", f"{kpis['total_orders']:,}")
    col2.metric("Total Quantity", f"{kpis['total_quantity']:,.0f}")
    col3.metric("Total Sales", f"${kpis['total_sales']:,.0f}")
    col4.metric("Total Profit", f"${kpis['total_profit']:,.0f}")

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("Late Delivery Rate", f"{kpis['late_delivery_rate']:.1f}%")
    col6.metric("Avg. Delay Days", f"{kpis['avg_delay_days']:.1f}")
    col7.metric("Categories", kpis["categories"])
    col8.metric("Markets", kpis["markets"])


def show_uploaded_charts(data: pd.DataFrame) -> None:
    """Display basic charts for uploaded data."""

    st.divider()
    st.subheader("Generated Dashboard Preview")

    left_col, right_col = st.columns(2)

    with left_col:
        monthly_orders = (
            data.groupby("year_month")["order_id"]
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
        category_quantity = (
            data.groupby("category_name")["order_quantity"]
            .sum()
            .reset_index()
            .sort_values("order_quantity", ascending=False)
            .head(15)
        )

        fig = px.bar(
            category_quantity,
            x="order_quantity",
            y="category_name",
            orientation="h",
            title="Top Categories by Order Quantity",
        )

        fig.update_layout(
            xaxis_title="Order Quantity",
            yaxis_title="Category",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)

    left_col2, right_col2 = st.columns(2)

    with left_col2:
        delivery_status = (
            data["delivery_status"]
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
            yaxis_title="Number of Records",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)

    with right_col2:
        shipping_delay = (
            data.groupby("shipping_mode")["delay_days"]
            .mean()
            .reset_index()
            .sort_values("delay_days", ascending=False)
        )

        fig = px.bar(
            shipping_delay,
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


def create_download_csv(data: pd.DataFrame) -> bytes:
    """Create downloadable CSV bytes."""

    return data.to_csv(index=False).encode("utf-8")


def main():
    st.title("Dataset Upload Manager")

    st.markdown(
        """
        This module allows users to upload a new supply chain dataset, map its columns
        to a standard schema, validate the required fields, and generate basic supply
        chain KPIs and charts.
        """
    )

    with st.expander("What does this module do?", expanded=False):
        st.write(
            """
            The main dashboard uses the default DataCo dataset. This upload module extends
            the project by allowing new CSV or Excel datasets to be adapted into a standard
            supply chain analysis format. It does not replace the default dashboard data,
            but it demonstrates how the system can process new datasets through column mapping.
            """
        )

    uploaded_file = st.file_uploader(
        "Upload a supply chain dataset",
        type=["csv", "xlsx"],
    )

    if uploaded_file is None:
        st.info("Upload a CSV or Excel file to start.")
        return

    try:
        raw_df = read_uploaded_file(uploaded_file)
    except Exception as error:
        st.error(f"Could not read uploaded file: {error}")
        return

    st.subheader("Uploaded Data Preview")

    st.write(f"Rows: {raw_df.shape[0]:,} | Columns: {raw_df.shape[1]:,}")
    st.dataframe(raw_df.head(20), use_container_width=True)

    mapping = build_mapping_ui(raw_df)

    errors = validate_mapping(mapping)

    if errors:
        st.error("Please fix the following mapping issues:")
        for error in errors:
            st.write(f"- {error}")
        return

    if st.button("Process Dataset", type="primary"):
        try:
            standardized = standardize_dataset(raw_df, mapping)
        except Exception as error:
            st.error(f"Dataset processing failed: {error}")
            return

        if standardized.empty:
            st.error("Processed dataset is empty. Please check the date and required field mappings.")
            return

        st.success("Dataset processed successfully.")

        st.subheader("Standardized Data Preview")
        st.dataframe(standardized.head(50), use_container_width=True)

        kpis = calculate_uploaded_kpis(standardized)

        show_uploaded_kpis(kpis)
        show_uploaded_charts(standardized)

        csv_bytes = create_download_csv(standardized)

        st.download_button(
            label="Download Standardized CSV",
            data=csv_bytes,
            file_name="standardized_supply_chain_dataset.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()