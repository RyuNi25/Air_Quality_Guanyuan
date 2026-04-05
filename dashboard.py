import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Air Quality Monitoring - Guanyuan City",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime')
    return df

def filter_data(df, date_range, hour_start, hour_end):
    start_date, end_date = date_range
    return df[
        (df['datetime'].dt.date >= start_date) &
        (df['datetime'].dt.date <= end_date) &
        (df['hour'].between(hour_start, hour_end))
    ]

def calculate_kpi_metrics(df):
    return {
        "avg": df['PM2.5'].mean(),
        "max": df['PM2.5'].max(),
        "min": df['PM2.5'].min(),
        "count": len(df)
    }

def create_trend_chart(df):
    fig = px.line(
        df,
        x='datetime',
        y='PM2.5',
        title='PM2.5 Trend Over Time',
        render_mode='svg'
    )
    fig.update_layout(hovermode='x unified')
    return fig

def create_hourly_chart(df):
    hourly = df.groupby('hour')['PM2.5'].mean().reset_index()
    fig = px.line(
        hourly,
        x='hour',
        y='PM2.5',
        markers=True,
        title='Hourly PM2.5 Pattern',
        render_mode='svg'
    )
    return fig

def create_monthly_chart(df):
    monthly = df.groupby('month')['PM2.5'].mean().reset_index()
    fig = px.line(
        monthly,
        x='month',
        y='PM2.5',
        markers=True,
        title='Monthly PM2.5 Pattern',
        render_mode='svg'
    )
    return fig

def create_weather_chart(df, col, label):
    grouped = df.groupby(col)['PM2.5'].mean().reset_index()
    fig = px.line(
        grouped,
        x=col,
        y='PM2.5',
        title=f'PM2.5 vs {label}',
        render_mode='svg'
    )
    return fig

def create_heatmap(df):
    corr = df[['PM2.5','TEMP','PRES','DEWP','RAIN','WSPM']].corr()
    fig = px.imshow(
        corr,
        text_auto='.2f',
        color_continuous_scale='RdBu_r',
        title='Correlation Matrix'
    )
    return fig

def generate_insights(metrics, df):
    insights = []

    insights.append(f"Rata-rata PM2.5: {metrics['avg']:.2f} µg/m³")
    insights.append(f"PM2.5 maksimum: {metrics['max']:.2f} µg/m³")

    wind_corr = df['WSPM'].corr(df['PM2.5'])
    if wind_corr < -0.1:
        insights.append("Kecepatan angin berpengaruh negatif terhadap PM2.5 dan membantu menurunkan konsentrasi polutan")

    dewp_corr = df['DEWP'].corr(df['PM2.5'])
    if dewp_corr > 0.1:
        insights.append("Kelembaban memiliki hubungan positif dengan PM2.5")

    monthly_peak = df.groupby('month')['PM2.5'].mean().idxmax()
    monthly_low = df.groupby('month')['PM2.5'].mean().idxmin()
    insights.append(f"PM2.5 tertinggi terjadi pada bulan {monthly_peak} dan terendah pada bulan {monthly_low}")

    night = df[df['hour'].between(18, 23)]['PM2.5'].mean()
    day = df[df['hour'].between(12, 16)]['PM2.5'].mean()
    if night > day:
        insights.append("PM2.5 cenderung lebih tinggi pada malam hari dibandingkan siang hari")

    if metrics['avg'] <= 15:
        insights.append("Kualitas udara rata-rata: BAIK")
    elif metrics['avg'] <= 35:
        insights.append("Kualitas udara rata-rata: SEDANG")
    else:
        insights.append("Kualitas udara rata-rata: TIDAK SEHAT")

    return insights

def render_sidebar(df):
    st.sidebar.title("Filter")

    min_date = df['datetime'].min().date()
    max_date = df['datetime'].max().date()

    quick_option = st.sidebar.selectbox(
        "Quick Filter",
        ["Custom Range", "Last 30 Days", "Last 90 Days", "Last 1 Year"]
    )

    if quick_option == "Last 30 Days":
        date_range = [max_date - pd.Timedelta(days=30), max_date]
    elif quick_option == "Last 90 Days":
        date_range = [max_date - pd.Timedelta(days=90), max_date]
    elif quick_option == "Last 1 Year":
        date_range = [max_date - pd.Timedelta(days=365), max_date]
    else:
        date_range = st.sidebar.date_input(
            "Pilih Rentang Tanggal",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )

    hour_range = st.sidebar.slider("Pilih Jam", 0, 23, (0, 23))

    return date_range, hour_range

def render_kpi(metrics):
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Avg PM2.5", f"{metrics['avg']:.1f}")
    col2.metric("Max PM2.5", f"{metrics['max']:.1f}")
    col3.metric("Min PM2.5", f"{metrics['min']:.1f}")
    col4.metric("Total Data", metrics['count'])

def main():
    st.title("🌫️ Air Quality Monitoring – Guanyuan City")
    st.caption("Analisis konsentrasi PM2.5 dan pengaruh faktor cuaca periode 2013–2017")

    df = load_data('data_guanyuan.csv')

    date_range, hour_range = render_sidebar(df)

    if len(date_range) != 2:
        st.warning("Pilih rentang tanggal yang valid")
        st.stop()

    df_filtered = filter_data(df, date_range, hour_range[0], hour_range[1])

    metrics = calculate_kpi_metrics(df_filtered)
    render_kpi(metrics)

    st.markdown("---")

    st.subheader("PM2.5 Trend Over Time")
    st.plotly_chart(create_trend_chart(df_filtered), use_container_width=True)

    st.subheader("Monthly Pattern")
    st.plotly_chart(create_monthly_chart(df_filtered), use_container_width=True)

    st.subheader("Hourly Pattern")
    st.plotly_chart(create_hourly_chart(df_filtered), use_container_width=True)

    st.subheader("Weather Impact")

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(
            create_weather_chart(df_filtered, 'WSPM', 'Wind Speed'),
            use_container_width=True
        )

    with col2:
        st.plotly_chart(
            create_weather_chart(df_filtered, 'TEMP', 'Temperature'),
            use_container_width=True
        )

    st.subheader("Correlation Analysis")
    st.plotly_chart(create_heatmap(df_filtered), use_container_width=True)

    st.markdown("---")
    st.subheader("Insights")

    insights = generate_insights(metrics, df_filtered)

    for i in insights:
        st.success(f"• {i}")

if __name__ == "__main__":
    main()
