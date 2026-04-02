import streamlit as st
import pandas as pd
import plotly.express as px

# CONFIG
st.set_page_config(
    page_title="Air Quality Monitoring - Guanyuan City",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime')
    return df

# FILTER DATA
def filter_data(df, months, hour_start, hour_end):
    return df[
        (df['month'].isin(months)) &
        (df['hour'].between(hour_start, hour_end))
    ]

# KPI METRICS
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
        title='PM2.5 Concentration Over Time',
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

    insights.append(f"Rata-rata PM2.5: {metrics['avg']:.2f}")
    insights.append(f"Polusi tertinggi: {metrics['max']:.2f}")

    # Korelasi angin
    wind_corr = df['WSPM'].corr(df['PM2.5'])
    if wind_corr < -0.1:
        insights.append("Kecepatan angin menurunkan tingkat polusi udara")

    # Pola waktu
    morning = df[df['hour'].between(6, 11)]['PM2.5'].mean()
    night = df[df['hour'].between(18, 23)]['PM2.5'].mean()

    if night > morning:
        insights.append("Polusi lebih tinggi pada malam hari")

    # Kategori kualitas udara
    if metrics['avg'] <= 15:
        insights.append("Kualitas udara: BAIK")
    elif metrics['avg'] <= 35:
        insights.append("Kualitas udara: SEDANG")
    else:
        insights.append("Kualitas udara: TIDAK SEHAT")

    return insights

# SIDEBAR
def render_sidebar(df):
    st.sidebar.title("Filter")

    months = st.sidebar.multiselect(
        "Pilih Bulan",
        sorted(df['month'].unique()),
        default=sorted(df['month'].unique())
    )

    hour_range = st.sidebar.slider("Pilih Jam", 0, 23, (0, 23))

    return months, hour_range

# KPI UI
def render_kpi(metrics):
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Avg PM2.5", f"{metrics['avg']:.1f}")
    col2.metric("Max PM2.5", f"{metrics['max']:.1f}")
    col3.metric("Min PM2.5", f"{metrics['min']:.1f}")
    col4.metric("Total Data", metrics['count'])


def main():
    st.title("🌫️ Air Quality Monitoring – Guanyuan City")
    st.caption("Dashboard interaktif untuk analisis PM2.5 dan faktor cuaca")

    df = load_data('data_guanyuan.csv')

    months, hour_range = render_sidebar(df)

    if not months:
        st.warning("Pilih minimal satu bulan")
        st.stop()

    df_filtered = filter_data(df, months, hour_range[0], hour_range[1])

    metrics = calculate_kpi_metrics(df_filtered)
    render_kpi(metrics)

    st.markdown("---")

    # Trend
    st.subheader("PM2.5 Concentration Over Time")
    st.plotly_chart(create_trend_chart(df_filtered), use_container_width=True)

    # Hourly
    st.subheader("Hourly Pattern")
    st.plotly_chart(create_hourly_chart(df_filtered), use_container_width=True)

    # Weather
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

    # Heatmap
    st.subheader("Correlation Analysis")
    st.plotly_chart(create_heatmap(df_filtered), use_container_width=True)

    # Insight
    st.markdown("---")
    st.subheader("Insights")

    insights = generate_insights(metrics, df_filtered)

    for i in insights:
        st.success(f"• {i}")


if __name__ == "__main__":
    main()