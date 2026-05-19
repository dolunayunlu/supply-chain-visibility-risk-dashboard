import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Company Risk Report Generator",
    page_icon="🏢",
    layout="wide",
)


STANDARD_FIELDS = {
    "order_id": {
        "required": True,
        "description": "Unique order identifier",
        "keywords": ["order id", "order_id", "order", "purchase order", "po"],
    },
    "order_date": {
        "required": True,
        "description": "Order creation date",
        "keywords": ["order date", "order_date", "created", "dateorders", "date"],
    },
    "product_name": {
        "required": True,
        "description": "Product or SKU name",
        "keywords": ["product name", "product_name", "sku", "item", "material"],
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


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    """Read CSV or Excel files."""
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
    """Suggest column mappings using simple keyword matching."""
    keywords = STANDARD_FIELDS[field_name]["keywords"]

    normalized_columns = {
        column: column.lower().replace("_", " ").replace("-", " ").strip()
        for column in columns
    }

    for keyword in keywords:
        keyword = keyword.lower()
        for original_column, normalized_column in normalized_columns.items():
            if keyword == normalized_column:
                return original_column

    for keyword in keywords:
        keyword = keyword.lower()
        for original_column, normalized_column in normalized_columns.items():
            if keyword in normalized_column:
                return original_column

    return None


def create_mapping_ui(df: pd.DataFrame) -> dict:
    """Create column mapping UI."""
    st.subheader("1. Column Mapping")

    st.write(
        "Map your company dataset columns to the standard supply chain schema. "
        "Required fields must be selected. Optional fields improve the risk report."
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
        suggestion = suggest_column(field, columns)
        default_index = options.index(suggestion) if suggestion in options else 0

        mapping[field] = st.selectbox(
            f"{field} — {STANDARD_FIELDS[field]['description']}",
            options=options,
            index=default_index,
            key=f"required_{field}",
        )

    with st.expander("Optional Fields", expanded=False):
        for field in optional_fields:
            suggestion = suggest_column(field, columns)
            default_index = options.index(suggestion) if suggestion in options else 0

            mapping[field] = st.selectbox(
                f"{field} — {STANDARD_FIELDS[field]['description']}",
                options=options,
                index=default_index,
                key=f"optional_{field}",
            )

    return mapping


def validate_mapping(mapping: dict) -> list[str]:
    """Validate required mappings and duplicate mappings."""
    errors = []

    for field, info in STANDARD_FIELDS.items():
        if info["required"] and mapping.get(field) == "Not available":
            errors.append(f"Missing required field: {field}")

    mapped_columns = [
        source_column
        for source_column in mapping.values()
        if source_column != "Not available"
    ]

    duplicate_columns = {
        column
        for column in mapped_columns
        if mapped_columns.count(column) > 1
    }

    if duplicate_columns:
        errors.append(
            "The same source column was mapped to multiple standard fields: "
            + ", ".join(sorted(duplicate_columns))
        )

    return errors


def safe_numeric(series: pd.Series, default_value: float = 0) -> pd.Series:
    """Safely convert a column to numeric values."""
    return pd.to_numeric(series, errors="coerce").fillna(default_value)


def calculate_data_quality_risk(raw_df: pd.DataFrame, mapping: dict) -> tuple[float, float]:
    """Calculate missing value risk and optional field completeness."""
    mapped_columns = [
        source_column
        for source_column in mapping.values()
        if source_column != "Not available"
    ]

    if not mapped_columns:
        missing_value_risk = 100.0
    else:
        missing_value_risk = raw_df[mapped_columns].isna().mean().mean() * 100

    optional_fields = [
        field for field, info in STANDARD_FIELDS.items() if not info["required"]
    ]

    missing_optional_fields = [
        field
        for field in optional_fields
        if mapping.get(field) == "Not available"
    ]

    optional_completeness = (
        1 - (len(missing_optional_fields) / len(optional_fields))
    ) * 100

    data_quality_risk = min(missing_value_risk + (100 - optional_completeness) * 0.35, 100)

    return round(float(data_quality_risk), 2), round(float(optional_completeness), 2)


def standardize_dataset(raw_df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Convert uploaded data into a standard supply chain table."""
    data = pd.DataFrame()

    data["order_id"] = raw_df[mapping["order_id"]].astype(str)
    data["order_date"] = pd.to_datetime(raw_df[mapping["order_date"]], errors="coerce")
    data["product_name"] = raw_df[mapping["product_name"]].astype(str)
    data["category_name"] = raw_df[mapping["category_name"]].astype(str)
    data["order_quantity"] = safe_numeric(raw_df[mapping["order_quantity"]], 0)

    text_defaults = {
        "delivery_status": "Unknown",
        "shipping_mode": "Unknown",
        "market": "Unknown",
        "order_region": "Unknown",
        "order_country": "Unknown",
    }

    for field, default_value in text_defaults.items():
        if mapping.get(field) != "Not available":
            data[field] = raw_df[mapping[field]].astype(str)
        else:
            data[field] = default_value

    if mapping.get("shipping_date") != "Not available":
        data["shipping_date"] = pd.to_datetime(
            raw_df[mapping["shipping_date"]],
            errors="coerce",
        )
    else:
        data["shipping_date"] = pd.NaT

    if mapping.get("actual_shipping_days") != "Not available":
        data["actual_shipping_days"] = safe_numeric(
            raw_df[mapping["actual_shipping_days"]],
            np.nan,
        )
    else:
        data["actual_shipping_days"] = np.nan

    if mapping.get("scheduled_shipping_days") != "Not available":
        data["scheduled_shipping_days"] = safe_numeric(
            raw_df[mapping["scheduled_shipping_days"]],
            np.nan,
        )
    else:
        data["scheduled_shipping_days"] = np.nan

    if mapping.get("sales") != "Not available":
        data["sales"] = safe_numeric(raw_df[mapping["sales"]], 0)
    else:
        data["sales"] = 0

    if mapping.get("order_profit") != "Not available":
        data["order_profit"] = safe_numeric(raw_df[mapping["order_profit"]], 0)
    else:
        data["order_profit"] = 0

    missing_actual_days = data["actual_shipping_days"].isna()

    if data["shipping_date"].notna().any():
        calculated_days = (data["shipping_date"] - data["order_date"]).dt.days
        data.loc[missing_actual_days, "actual_shipping_days"] = calculated_days

    data["actual_shipping_days"] = data["actual_shipping_days"].fillna(0)

    data["scheduled_shipping_days"] = data["scheduled_shipping_days"].fillna(
        data["actual_shipping_days"]
    )

    data["delay_days"] = (
        data["actual_shipping_days"] - data["scheduled_shipping_days"]
    ).clip(lower=0)

    status_lower = data["delivery_status"].astype(str).str.lower()
    status_late = status_lower.str.contains("late|delay|delayed", regex=True)
    delay_late = data["delay_days"] > 0

    data["is_late"] = (status_late | delay_late).astype(int)

    data = data.dropna(subset=["order_date"])
    data["year_month"] = data["order_date"].dt.to_period("M").astype(str)

    return data


def calculate_demand_volatility(data: pd.DataFrame) -> float:
    """Calculate demand volatility risk from monthly quantity."""
    if data.empty:
        return 0.0

    monthly_demand = (
        data.groupby("year_month")["order_quantity"]
        .sum()
        .reset_index()
        .sort_values("year_month")
    )

    mean_demand = monthly_demand["order_quantity"].mean()
    std_demand = monthly_demand["order_quantity"].std()

    if mean_demand == 0 or pd.isna(mean_demand) or pd.isna(std_demand):
        return 0.0

    return round(float(min((std_demand / mean_demand) * 100, 100)), 2)


def calculate_risk_scores(
    data: pd.DataFrame,
    data_quality_risk: float,
) -> dict:
    """Calculate overall risk scores for the uploaded company dataset."""
    if data.empty:
        return {
            "delivery_risk": 0,
            "delay_risk": 0,
            "financial_risk": 0,
            "demand_volatility_risk": 0,
            "data_quality_risk": data_quality_risk,
            "overall_risk": data_quality_risk,
            "risk_level": "High",
        }

    delivery_risk = data["is_late"].mean() * 100

    avg_delay_days = data["delay_days"].mean()
    delay_risk = min((avg_delay_days / 5) * 100, 100)

    if "order_profit" in data.columns and data["order_profit"].abs().sum() > 0:
        financial_risk = (data["order_profit"] < 0).mean() * 100
    else:
        financial_risk = 0

    demand_volatility_risk = calculate_demand_volatility(data)

    overall_risk = (
        0.30 * delivery_risk
        + 0.20 * delay_risk
        + 0.20 * financial_risk
        + 0.20 * demand_volatility_risk
        + 0.10 * data_quality_risk
    )

    if overall_risk < 30:
        risk_level = "Low"
    elif overall_risk < 60:
        risk_level = "Medium"
    else:
        risk_level = "High"

    return {
        "delivery_risk": round(float(delivery_risk), 2),
        "delay_risk": round(float(delay_risk), 2),
        "financial_risk": round(float(financial_risk), 2),
        "demand_volatility_risk": round(float(demand_volatility_risk), 2),
        "data_quality_risk": round(float(data_quality_risk), 2),
        "overall_risk": round(float(overall_risk), 2),
        "risk_level": risk_level,
    }


def calculate_region_risk(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate regional risk ranking."""
    region_risk = (
        data.groupby(["market", "order_region"])
        .agg(
            total_orders=("order_id", "nunique"),
            total_quantity=("order_quantity", "sum"),
            late_delivery_rate=("is_late", "mean"),
            avg_delay_days=("delay_days", "mean"),
            total_sales=("sales", "sum"),
            total_profit=("order_profit", "sum"),
        )
        .reset_index()
    )

    region_risk["delivery_risk"] = region_risk["late_delivery_rate"] * 100

    max_delay = region_risk["avg_delay_days"].max()

    if max_delay == 0 or pd.isna(max_delay):
        region_risk["delay_risk"] = 0
    else:
        region_risk["delay_risk"] = region_risk["avg_delay_days"] / max_delay * 100

    region_risk["financial_risk"] = region_risk["total_profit"].apply(
        lambda value: 80 if value < 0 else 20
    )

    region_risk["region_risk_score"] = (
        0.50 * region_risk["delivery_risk"]
        + 0.30 * region_risk["delay_risk"]
        + 0.20 * region_risk["financial_risk"]
    ).round(2)

    return region_risk.sort_values("region_risk_score", ascending=False)


def calculate_category_risk(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate category risk ranking."""
    category_risk = (
        data.groupby("category_name")
        .agg(
            total_orders=("order_id", "nunique"),
            total_quantity=("order_quantity", "sum"),
            late_delivery_rate=("is_late", "mean"),
            avg_delay_days=("delay_days", "mean"),
            total_sales=("sales", "sum"),
            total_profit=("order_profit", "sum"),
        )
        .reset_index()
    )

    category_risk["delivery_risk"] = category_risk["late_delivery_rate"] * 100

    max_delay = category_risk["avg_delay_days"].max()

    if max_delay == 0 or pd.isna(max_delay):
        category_risk["delay_risk"] = 0
    else:
        category_risk["delay_risk"] = category_risk["avg_delay_days"] / max_delay * 100

    category_risk["financial_risk"] = category_risk["total_profit"].apply(
        lambda value: 80 if value < 0 else 20
    )

    category_risk["category_risk_score"] = (
        0.50 * category_risk["delivery_risk"]
        + 0.30 * category_risk["delay_risk"]
        + 0.20 * category_risk["financial_risk"]
    ).round(2)

    return category_risk.sort_values("category_risk_score", ascending=False)


def apply_dashboard_filters(data: pd.DataFrame) -> pd.DataFrame:
    """Apply interactive filters after processing."""
    st.sidebar.header("Dashboard Filters")

    filtered = data.copy()

    market_options = ["All"] + sorted(filtered["market"].dropna().unique())
    selected_market = st.sidebar.selectbox("Market", market_options)

    if selected_market != "All":
        filtered = filtered[filtered["market"] == selected_market]

    category_options = ["All"] + sorted(filtered["category_name"].dropna().unique())
    selected_category = st.sidebar.selectbox("Category", category_options)

    if selected_category != "All":
        filtered = filtered[filtered["category_name"] == selected_category]

    mode_options = ["All"] + sorted(filtered["shipping_mode"].dropna().unique())
    selected_mode = st.sidebar.selectbox("Shipping Mode", mode_options)

    if selected_mode != "All":
        filtered = filtered[filtered["shipping_mode"] == selected_mode]

    min_date = filtered["order_date"].min()
    max_date = filtered["order_date"].max()

    if pd.notna(min_date) and pd.notna(max_date):
        selected_range = st.sidebar.date_input(
            "Order Date Range",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date(),
        )

        if len(selected_range) == 2:
            start_date, end_date = selected_range
            filtered = filtered[
                (filtered["order_date"].dt.date >= start_date)
                & (filtered["order_date"].dt.date <= end_date)
            ]

    return filtered


def show_kpi_cards(data: pd.DataFrame, risk_scores: dict) -> None:
    """Show KPI cards."""
    total_orders = data["order_id"].nunique()
    total_quantity = data["order_quantity"].sum()
    total_sales = data["sales"].sum()
    total_profit = data["order_profit"].sum()
    avg_delay = data["delay_days"].mean()
    late_rate = data["is_late"].mean() * 100

    st.subheader("Executive KPI Summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Orders", f"{total_orders:,}")
    col2.metric("Total Quantity", f"{total_quantity:,.0f}")
    col3.metric("Total Sales", f"${total_sales:,.0f}")
    col4.metric("Total Profit", f"${total_profit:,.0f}")

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("Late Delivery Rate", f"{late_rate:.1f}%")
    col6.metric("Avg. Delay Days", f"{avg_delay:.1f}")
    col7.metric("Overall Risk Score", f"{risk_scores['overall_risk']:.1f}")
    col8.metric("Risk Level", risk_scores["risk_level"])


def show_risk_breakdown(risk_scores: dict) -> None:
    """Show risk score breakdown."""
    st.subheader("Risk Score Breakdown")

    risk_df = pd.DataFrame(
        [
            {"risk_component": "Delivery Risk", "score": risk_scores["delivery_risk"]},
            {"risk_component": "Delay Risk", "score": risk_scores["delay_risk"]},
            {"risk_component": "Financial Risk", "score": risk_scores["financial_risk"]},
            {
                "risk_component": "Demand Volatility Risk",
                "score": risk_scores["demand_volatility_risk"],
            },
            {
                "risk_component": "Data Quality Risk",
                "score": risk_scores["data_quality_risk"],
            },
        ]
    )

    fig = px.bar(
        risk_df,
        x="risk_component",
        y="score",
        title="Risk Components",
    )

    fig.update_layout(
        xaxis_title="Risk Component",
        yaxis_title="Score",
        height=420,
    )

    st.plotly_chart(fig, use_container_width=True)


def show_dashboard_charts(data: pd.DataFrame) -> None:
    """Show dynamic dashboard charts."""
    st.divider()
    st.subheader("Generated Dashboard")

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
            title="Top Categories by Quantity",
        )

        fig.update_layout(
            xaxis_title="Quantity",
            yaxis_title="Category",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)

    left_col2, right_col2 = st.columns(2)

    with left_col2:
        delivery_status = data["delivery_status"].value_counts().reset_index()
        delivery_status.columns = ["delivery_status", "count"]

        fig = px.bar(
            delivery_status,
            x="delivery_status",
            y="count",
            title="Delivery Status Distribution",
        )

        fig.update_layout(
            xaxis_title="Delivery Status",
            yaxis_title="Records",
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


def generate_recommendations(risk_scores: dict, region_risk: pd.DataFrame, category_risk: pd.DataFrame) -> list[str]:
    """Generate basic management recommendations."""
    recommendations = []

    if risk_scores["delivery_risk"] >= 50:
        recommendations.append(
            "Review root causes of late deliveries and prioritize high-delay shipment modes."
        )

    if risk_scores["delay_risk"] >= 50:
        recommendations.append(
            "Investigate transport planning assumptions because average delay is above the acceptable range."
        )

    if risk_scores["financial_risk"] >= 30:
        recommendations.append(
            "Analyze categories or regions with negative profit records and review pricing or cost structure."
        )

    if risk_scores["demand_volatility_risk"] >= 40:
        recommendations.append(
            "Improve demand planning for volatile categories and consider higher safety stock for unstable demand patterns."
        )

    if risk_scores["data_quality_risk"] >= 30:
        recommendations.append(
            "Improve dataset completeness by adding missing optional fields such as shipment mode, region, sales, and profit."
        )

    if not region_risk.empty:
        top_region = region_risk.iloc[0]
        recommendations.append(
            f"Prioritize regional review for {top_region['order_region']} "
            f"because it has the highest regional risk score."
        )

    if not category_risk.empty:
        top_category = category_risk.iloc[0]
        recommendations.append(
            f"Monitor {top_category['category_name']} category closely because it has the highest category risk score."
        )

    if not recommendations:
        recommendations.append(
            "No major risk concentration detected. Continue monitoring KPIs regularly."
        )

    return recommendations


def generate_report_text(
    file_name: str,
    data: pd.DataFrame,
    risk_scores: dict,
    region_risk: pd.DataFrame,
    category_risk: pd.DataFrame,
    recommendations: list[str],
) -> str:
    """Generate downloadable text report."""
    total_orders = data["order_id"].nunique()
    total_quantity = data["order_quantity"].sum()
    total_sales = data["sales"].sum()
    total_profit = data["order_profit"].sum()

    top_region = region_risk.iloc[0]["order_region"] if not region_risk.empty else "N/A"
    top_category = category_risk.iloc[0]["category_name"] if not category_risk.empty else "N/A"

    lines = [
        "SUPPLY CHAIN RISK REPORT",
        "=" * 32,
        "",
        f"Dataset: {file_name}",
        f"Total Orders: {total_orders:,}",
        f"Total Quantity: {total_quantity:,.0f}",
        f"Total Sales: ${total_sales:,.2f}",
        f"Total Profit: ${total_profit:,.2f}",
        "",
        "RISK SUMMARY",
        "-" * 32,
        f"Overall Risk Score: {risk_scores['overall_risk']:.2f} / 100",
        f"Risk Level: {risk_scores['risk_level']}",
        f"Delivery Risk: {risk_scores['delivery_risk']:.2f}",
        f"Delay Risk: {risk_scores['delay_risk']:.2f}",
        f"Financial Risk: {risk_scores['financial_risk']:.2f}",
        f"Demand Volatility Risk: {risk_scores['demand_volatility_risk']:.2f}",
        f"Data Quality Risk: {risk_scores['data_quality_risk']:.2f}",
        "",
        "MAIN FINDINGS",
        "-" * 32,
        f"Highest Risk Region: {top_region}",
        f"Highest Risk Category: {top_category}",
        "",
        "RECOMMENDED ACTIONS",
        "-" * 32,
    ]

    for index, recommendation in enumerate(recommendations, start=1):
        lines.append(f"{index}. {recommendation}")

    return "\n".join(lines)


def show_risk_report(
    file_name: str,
    data: pd.DataFrame,
    risk_scores: dict,
    region_risk: pd.DataFrame,
    category_risk: pd.DataFrame,
) -> None:
    """Show executive risk report."""
    st.divider()
    st.subheader("Executive Risk Report")

    recommendations = generate_recommendations(risk_scores, region_risk, category_risk)

    if risk_scores["risk_level"] == "High":
        st.error(f"Overall Risk Level: {risk_scores['risk_level']}")
    elif risk_scores["risk_level"] == "Medium":
        st.warning(f"Overall Risk Level: {risk_scores['risk_level']}")
    else:
        st.success(f"Overall Risk Level: {risk_scores['risk_level']}")

    st.markdown("#### Main Findings")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Top Regional Risks**")
        st.dataframe(
            region_risk[
                [
                    "market",
                    "order_region",
                    "total_orders",
                    "late_delivery_rate",
                    "avg_delay_days",
                    "region_risk_score",
                ]
            ].head(10),
            use_container_width=True,
            hide_index=True,
        )

    with col2:
        st.write("**Top Category Risks**")
        st.dataframe(
            category_risk[
                [
                    "category_name",
                    "total_orders",
                    "total_quantity",
                    "late_delivery_rate",
                    "avg_delay_days",
                    "category_risk_score",
                ]
            ].head(10),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("#### Recommended Actions")

    for recommendation in recommendations:
        st.write(f"- {recommendation}")

    report_text = generate_report_text(
        file_name=file_name,
        data=data,
        risk_scores=risk_scores,
        region_risk=region_risk,
        category_risk=category_risk,
        recommendations=recommendations,
    )

    st.download_button(
        label="Download Risk Report",
        data=report_text.encode("utf-8"),
        file_name="supply_chain_risk_report.txt",
        mime="text/plain",
    )

    st.download_button(
        label="Download Standardized Dataset",
        data=data.to_csv(index=False).encode("utf-8"),
        file_name="standardized_supply_chain_dataset.csv",
        mime="text/csv",
    )


def main():
    st.title("Company Risk Report Generator")

    st.markdown(
        """
        Upload a company supply chain dataset, map its columns to a standard schema,
        and generate an interactive dashboard with operational risk analysis.
        """
    )

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel dataset",
        type=["csv", "xlsx"],
    )

    if uploaded_file is None:
        st.info("Upload a CSV or Excel file to generate a company-specific dashboard and risk report.")
        return

    try:
        raw_df = read_uploaded_file(uploaded_file)
    except Exception as error:
        st.error(f"Could not read uploaded file: {error}")
        return

    st.subheader("Uploaded Dataset Preview")
    st.write(f"Rows: {raw_df.shape[0]:,} | Columns: {raw_df.shape[1]:,}")
    st.dataframe(raw_df.head(20), use_container_width=True)

    mapping = create_mapping_ui(raw_df)
    mapping_errors = validate_mapping(mapping)

    if mapping_errors:
        st.error("Please fix the following mapping issues:")
        for error in mapping_errors:
            st.write(f"- {error}")
        return

    if "processed_company_dataset" not in st.session_state:
        st.session_state["processed_company_dataset"] = None

    if st.button("Generate Dashboard and Risk Report", type="primary"):
        try:
            data_quality_risk, optional_completeness = calculate_data_quality_risk(
                raw_df,
                mapping,
            )

            standardized_data = standardize_dataset(raw_df, mapping)

            if standardized_data.empty:
                st.error("The standardized dataset is empty. Check date and required field mappings.")
                return

            st.session_state["processed_company_dataset"] = {
                "file_name": uploaded_file.name,
                "data": standardized_data,
                "data_quality_risk": data_quality_risk,
                "optional_completeness": optional_completeness,
            }

            st.success("Dashboard and risk report generated successfully.")

        except Exception as error:
            st.error(f"Processing failed: {error}")
            return

    processed = st.session_state.get("processed_company_dataset")

    if processed is None:
        return

    file_name = processed["file_name"]
    data = processed["data"]
    data_quality_risk = processed["data_quality_risk"]
    optional_completeness = processed["optional_completeness"]

    st.divider()
    st.subheader("Active Company Dataset")

    st.write(f"**Dataset:** {file_name}")
    st.write(f"**Standardized Rows:** {data.shape[0]:,}")
    st.write(f"**Optional Field Completeness:** {optional_completeness:.1f}%")

    filtered_data = apply_dashboard_filters(data)

    if filtered_data.empty:
        st.warning("No data available for selected filters.")
        return

    risk_scores = calculate_risk_scores(filtered_data, data_quality_risk)
    region_risk = calculate_region_risk(filtered_data)
    category_risk = calculate_category_risk(filtered_data)

    show_kpi_cards(filtered_data, risk_scores)
    show_risk_breakdown(risk_scores)
    show_dashboard_charts(filtered_data)
    show_risk_report(file_name, filtered_data, risk_scores, region_risk, category_risk)


if __name__ == "__main__":
    main()