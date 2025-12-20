import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Initialize app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)

# Generate sample fraud data
def generate_fraud_data(n=500):
    np.random.seed(42)
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), periods=n)
    
    df = pd.DataFrame({
        "transaction_id": [f"TX{i:08d}" for i in range(n)],
        "date": dates,
        "amount": np.random.lognormal(mean=4, sigma=1.8, size=n).round(2),
        "merchant": np.random.choice(["AMAZON", "GOOGLE", "APPLE", "NETFLIX", "UBER", "UNKNOWN", "PAYPAL"], n, p=[0.3, 0.2, 0.15, 0.1, 0.1, 0.05, 0.1]),
        "country": np.random.choice(["US", "UK", "DE", "FR", "IN", "BR"], n),
        "user_id": [f"USER{np.random.randint(1000, 9999)}" for _ in range(n)]
    })
    
    fraud_conditions = (
        (df["amount"] > 10000) |
        (df["merchant"] == "UNKNOWN") |
        (df["amount"].between(5000, 10000) & (df["country"].isin(["IN", "BR"])))
    )
    
    df["is_fraud"] = fraud_conditions & (np.random.random(n) > 0.3)
    df["risk_score"] = np.where(
        df["is_fraud"],
        np.random.uniform(0.7, 1.0, n),
        np.random.uniform(0.0, 0.6, n)
    ).round(3)
    
    return df

# Generate data
df = generate_fraud_data(500)

# Calculate metrics
total_amount = df["amount"].sum()
total_transactions = len(df)
fraud_transactions = df["is_fraud"].sum()
fraud_amount = df[df["is_fraud"]]["amount"].sum()
fraud_rate = (fraud_transactions / total_transactions * 100)

# Create charts
daily_fraud = df.groupby(df["date"].dt.date).agg({"transaction_id": "count", "is_fraud": "sum"}).reset_index()
daily_fraud["fraud_rate"] = (daily_fraud["is_fraud"] / daily_fraud["transaction_id"] * 100).round(2)

fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(x=daily_fraud["date"], y=daily_fraud["fraud_rate"], mode="lines+markers",
                              name="Fraud Rate %", line=dict(color="#FF6B6B", width=3), fill='tozeroy'))

fig_dist = go.Figure()
fig_dist.add_trace(go.Histogram(x=df[~df["is_fraud"]]["amount"], name="Legitimate", marker_color="#4ECDC4", opacity=0.7))
fig_dist.add_trace(go.Histogram(x=df[df["is_fraud"]]["amount"], name="Fraudulent", marker_color="#FF6B6B", opacity=0.7))

# App layout
app.layout = dbc.Container([
    dbc.Row([dbc.Col([html.H1("🚨 Fraud Analytics Dashboard", className="text-center my-4", style={"color": "#00ff88"}),
                      html.P("Real-time Fraud Detection & Monitoring", className="text-center text-muted mb-4")])]),
    
    dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([html.H4(f"${total_amount:,.0f}", className="text-center"), html.P("Total Amount", className="text-center")])]), width=2),
        dbc.Col(dbc.Card([dbc.CardBody([html.H4(f"{total_transactions:,}", className="text-center"), html.P("Transactions", className="text-center")])]), width=2),
        dbc.Col(dbc.Card([dbc.CardBody([html.H4(f"{fraud_transactions}", className="text-center text-warning"), html.P("Fraud Cases", className="text-center")])]), width=2),
        dbc.Col(dbc.Card([dbc.CardBody([html.H4(f"${fraud_amount:,.0f}", className="text-center text-danger"), html.P("Fraud Amount", className="text-center")])]), width=2),
        dbc.Col(dbc.Card([dbc.CardBody([html.H4(f"{fraud_rate:.2f}%", className="text-center text-info"), html.P("Fraud Rate", className="text-center")])]), width=2),
        dbc.Col(dbc.Card([dbc.CardBody([html.H4(f"${df['amount'].mean():,.0f}", className="text-center"), html.P("Avg Transaction", className="text-center")])]), width=2),
    ], className="mb-4"),
    
    dbc.Row([dbc.Col(dcc.Graph(figure=fig_trend), width=6), dbc.Col(dcc.Graph(figure=fig_dist), width=6)], className="mb-4"),
    
    dbc.Row([dbc.Col(dbc.Card([
        dbc.CardHeader([html.H4("Recent High-Risk Transactions", className="mb-0")]),
        dbc.CardBody([dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in ["date", "transaction_id", "amount", "merchant", "risk_score", "is_fraud"]],
            data=df.nlargest(10, 'risk_score').to_dict('records'),
            style_table={'overflowX': 'auto'},
            style_cell={'backgroundColor': '#1a1a2e', 'color': 'white'},
            style_header={'backgroundColor': '#0f3460', 'fontWeight': 'bold'}
        )])
    ]), width=12)], className="mb-4")
], fluid=True, style={"backgroundColor": "#0d1117", "minHeight": "100vh", "color": "white"})

server = app.server

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run(host='0.0.0.0', port=port, debug=False)