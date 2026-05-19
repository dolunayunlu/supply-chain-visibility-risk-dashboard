from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

from utils.data_adapter import get_active_dashboard_data


BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

DEMAND_PATH = PROCESSED_DIR / "demand_clean.csv"
ORDERS_PATH = PROCESSED_DIR / "orders_clean.csv"


st.set_page_config(
    page_title="Demand Forecasting",
    page_icon="📈",
    layout="wide",
)


def load_data():
    """Load active dashboard data."""
    dashboard_data = get_active_dashboard_data()

    demand = dashboard_data["demand"].copy()
    orders = dashboard_data["orders"]

    demand["month_date"] = pd.to_datetime(
        demand["year_month"] + "-01",
        errors="coerce",
    )

    return demand, orders


def create_filter_options(series: pd.Series):
    values = sorted(series.dropna().unique())
    return ["All"] + values


def prepare_category_demand(demand: pd.DataFrame, selected_category: str) -> pd.DataFrame:
    """Prepare monthly demand data for the selected category or all categories."""

    if selected_category != "All":
        filtered = demand[demand["category_name"] == selected_category].copy()
    else:
        filtered = demand.copy()

    monthly = (
        filtered.groupby(["year_month", "month_date"])["demand_quantity"]
        .sum()
        .reset_index()
        .sort_values("month_date")
    )

    monthly["time_index"] = np.arange(len(monthly))

    return monthly


def add_moving_average_forecast(monthly: pd.DataFrame, window: int = 3) -> pd.DataFrame:
    """Add 3-month moving average forecast."""

    monthly = monthly.copy()

    monthly["moving_average_forecast"] = (
        monthly["demand_quantity"]
        .shift(1)
        .rolling(window=window)
        .mean()
    )

    return monthly


def calculate_mape(actual: pd.Series, predicted: pd.Series) -> float:
    """Calculate Mean Absolute Percentage Error safely."""

    actual = actual.replace(0, np.nan)
    mape = (np.abs((actual - predicted) / actual)).mean() * 100

    if pd.isna(mape):
        return 0.0

    return float(mape)


def train_linear_regression_forecast(monthly: pd.DataFrame):
    """Train a simple linear regression model on monthly demand."""

    model_data = monthly.dropna(subset=["demand_quantity"]).copy()

    if len(model_data) < 6:
        return None, monthly, pd.DataFrame(), {}

    X = model_data[["time_index"]]
    y = model_data["demand_quantity"]

    model = LinearRegression()
    model.fit(X, y)

    monthly = monthly.copy()
    monthly["linear_regression_forecast"] = model.predict(monthly[["time_index"]])

    evaluation_data = monthly.dropna(
        subset=["moving_average_forecast", "linear_regression_forecast"]
    ).copy()

    if evaluation_data.empty:
        metrics = {
            "ma_mae": 0.0,
            "ma_mape": 0.0,
            "lr_mae": 0.0,
            "lr_mape": 0.0,
        }
    else:
        ma_mae = mean_absolute_error(
            evaluation_data["demand_quantity"],
            evaluation_data["moving_average_forecast"],
        )

        lr_mae = mean_absolute_error(
            evaluation_data["demand_quantity"],
            evaluation_data["linear_regression_forecast"],
        )

        ma_mape = calculate_mape(
            evaluation_data["demand_quantity"],
            evaluation_data["moving_average_forecast"],
        )

        lr_mape = calculate_mape(
            evaluation_data["demand_quantity"],
            evaluation_data["linear_regression_forecast"],
        )

        metrics = {
            "ma_mae": float(ma_mae),
            "ma_mape": float(ma_mape),
            "lr_mae": float(lr_mae),
            "lr_mape": float(lr_mape),
        }

    last_index = int(monthly["time_index"].max())
    last_month = monthly["month_date"].max()

    future_rows = []

    for step in range(1, 7):
        future_index = last_index + step
        future_month = last_month + pd.DateOffset(months=step)

        prediction = model.predict(pd.DataFrame({"time_index": [future_index]}))[0]

        future_rows.append(
            {
                "year_month": future_month.strftime("%Y-%m"),
                "month_date": future_month,
                "time_index": future_index,
                "forecasted_demand": max(round(float(prediction), 0), 0),
            }
        )

    future_forecast = pd.DataFrame(future_rows)

    return model, monthly, future_forecast, metrics


def calculate_demand_volatility(demand: pd.DataFrame) -> pd.DataFrame:
    """Calculate demand volatility by category."""

    volatility = (
        demand.groupby("category_name")
        .agg(
            avg_monthly_demand=("demand_quantity", "mean"),
            std_monthly_demand=("demand_quantity", "std"),
            total_demand=("demand_quantity", "sum"),
        )
        .reset_index()
    )

    volatility["volatility_score"] = (
        volatility["std_monthly_demand"] / volatility["avg_monthly_demand"] * 100
    ).fillna(0)

    volatility = volatility.sort_values("volatility_score", ascending=False)

    return volatility


def show_kpis(monthly: pd.DataFrame, future_forecast: pd.DataFrame, metrics: dict):
    """Display demand forecasting KPI cards."""

    total_demand = monthly["demand_quantity"].sum()
    avg_monthly_demand = monthly["demand_quantity"].mean()
    max_monthly_demand = monthly["demand_quantity"].max()
    min_monthly_demand = monthly["demand_quantity"].min()

    if not future_forecast.empty:
        next_month_forecast = future_forecast.iloc[0]["forecasted_demand"]
        six_month_forecast_total = future_forecast["forecasted_demand"].sum()
    else:
        next_month_forecast = 0
        six_month_forecast_total = 0

    st.subheader("Demand Forecasting Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Historical Demand", f"{total_demand:,.0f}")
    col2.metric("Avg. Monthly Demand", f"{avg_monthly_demand:,.0f}")
    col3.metric("Max Monthly Demand", f"{max_monthly_demand:,.0f}")
    col4.metric("Min Monthly Demand", f"{min_monthly_demand:,.0f}")

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("Next Month Forecast", f"{next_month_forecast:,.0f}")
    col6.metric("Next 6 Months Forecast", f"{six_month_forecast_total:,.0f}")
    col7.metric("Moving Avg. MAPE", f"{metrics.get('ma_mape', 0):.1f}%")
    col8.metric("Linear Reg. MAPE", f"{metrics.get('lr_mape', 0):.1f}%")


def show_forecast_charts(monthly: pd.DataFrame, future_forecast: pd.DataFrame):
    """Display demand forecasting charts."""

    st.divider()

    st.subheader("Actual Demand vs Forecast")

    chart_data = monthly[
        [
            "year_month",
            "month_date",
            "demand_quantity",
            "moving_average_forecast",
            "linear_regression_forecast",
        ]
    ].copy()

    chart_data = chart_data.melt(
        id_vars=["year_month", "month_date"],
        value_vars=[
            "demand_quantity",
            "moving_average_forecast",
            "linear_regression_forecast",
        ],
        var_name="metric",
        value_name="quantity",
    )

    fig = px.line(
        chart_data,
        x="month_date",
        y="quantity",
        color="metric",
        markers=True,
        title="Actual Demand vs Forecast",
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Demand Quantity",
        height=520,
    )

    st.plotly_chart(fig, use_container_width=True)

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Historical Monthly Demand")

        fig = px.bar(
            monthly,
            x="month_date",
            y="demand_quantity",
            title="Historical Monthly Demand",
        )

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Demand Quantity",
            height=420,
        )

        st.plotly_chart(fig, use_container_width=True)

    with right_col:
        st.subheader("Next 6 Months Forecast")

        if future_forecast.empty:
            st.warning("Not enough data to generate future forecast.")
        else:
            fig = px.bar(
                future_forecast,
                x="year_month",
                y="forecasted_demand",
                title="Next 6 Months Forecast",
            )

            fig.update_layout(
                xaxis_title="Forecast Month",
                yaxis_title="Forecasted Demand",
                height=420,
            )

            st.plotly_chart(fig, use_container_width=True)


def show_error_metrics(metrics: dict):
    """Display forecast model evaluation table."""

    st.subheader("Forecast Model Evaluation")

    metrics_table = pd.DataFrame(
        [
            {
                "model": "3-Month Moving Average",
                "MAE": round(metrics.get("ma_mae", 0), 2),
                "MAPE (%)": round(metrics.get("ma_mape", 0), 2),
            },
            {
                "model": "Linear Regression",
                "MAE": round(metrics.get("lr_mae", 0), 2),
                "MAPE (%)": round(metrics.get("lr_mape", 0), 2),
            },
        ]
    )

    st.dataframe(
        metrics_table,
        use_container_width=True,
        hide_index=True,
    )


def show_volatility_analysis(demand: pd.DataFrame):
    """Display category demand volatility analysis."""

    st.divider()

    st.subheader("Demand Volatility by Category")

    volatility = calculate_demand_volatility(demand)

    left_col, right_col = st.columns(2)

    with left_col:
        top_volatility = volatility.head(15)

        fig = px.bar(
            top_volatility,
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

    with right_col:
        top_demand = volatility.sort_values("total_demand", ascending=False).head(15)

        fig = px.bar(
            top_demand,
            x="total_demand",
            y="category_name",
            orientation="h",
            title="Top Categories by Total Demand",
        )

        fig.update_layout(
            xaxis_title="Total Demand",
            yaxis_title="Product Category",
            height=520,
        )

        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Demand Volatility Table")

    volatility_table = volatility[
        [
            "category_name",
            "total_demand",
            "avg_monthly_demand",
            "std_monthly_demand",
            "volatility_score",
        ]
    ].copy()

    volatility_table["avg_monthly_demand"] = volatility_table[
        "avg_monthly_demand"
    ].round(2)

    volatility_table["std_monthly_demand"] = volatility_table[
        "std_monthly_demand"
    ].round(2)

    volatility_table["volatility_score"] = volatility_table[
        "volatility_score"
    ].round(2)

    st.dataframe(
        volatility_table,
        use_container_width=True,
        hide_index=True,
    )


def show_forecast_tables(monthly: pd.DataFrame, future_forecast: pd.DataFrame):
    """Display historical and forecast tables."""

    st.divider()

    st.subheader("Next 6 Months Forecast Table")

    if future_forecast.empty:
        st.warning("Future forecast could not be generated due to insufficient data.")
    else:
        st.dataframe(
            future_forecast[["year_month", "forecasted_demand"]],
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Historical Demand and Forecast Table")

    historical_table = monthly[
        [
            "year_month",
            "demand_quantity",
            "moving_average_forecast",
            "linear_regression_forecast",
        ]
    ].copy()

    historical_table["moving_average_forecast"] = historical_table[
        "moving_average_forecast"
    ].round(2)

    historical_table["linear_regression_forecast"] = historical_table[
        "linear_regression_forecast"
    ].round(2)

    st.dataframe(
        historical_table,
        use_container_width=True,
        hide_index=True,
    )


def main():
    demand, orders = load_data()

    st.title("Demand Forecasting")

    st.markdown(
        """
        This page analyzes historical demand trends and creates simple forecasting models.
        The purpose is to support supply chain planning by estimating future demand patterns.
        """
    )

    with st.expander("How is demand forecasting calculated?", expanded=False):
        st.write(
            """
            Two simple forecasting approaches are used:

            - 3-Month Moving Average: uses the average demand of the previous three months
            - Linear Regression: models demand trend over time using a numeric time index

            The forecasting module is designed as a decision-support prototype, not as a final
            production-level demand planning model.
            """
        )

    st.sidebar.title("Filters")

    category_options = create_filter_options(demand["category_name"])
    selected_category = st.sidebar.selectbox("Product Category", category_options)

    monthly = prepare_category_demand(demand, selected_category)

    if monthly.empty or len(monthly) < 6:
        st.warning("Not enough monthly demand data available for forecasting.")
        return

    monthly = add_moving_average_forecast(monthly, window=3)
    model, monthly, future_forecast, metrics = train_linear_regression_forecast(monthly)

    show_kpis(monthly, future_forecast, metrics)
    show_forecast_charts(monthly, future_forecast)
    show_error_metrics(metrics)
    show_volatility_analysis(demand)
    show_forecast_tables(monthly, future_forecast)


if __name__ == "__main__":
    main()