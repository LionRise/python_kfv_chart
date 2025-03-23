import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import requests
import io

API_URL = "https://dashboards.kfv.at/api/udm_verkehrstote/csv"

# Bundesland-ID to name map
state_map = {
    1: "Burgenland",
    2: "Kärnten",
    3: "Niederösterreich",
    4: "Oberösterreich",
    5: "Salzburg",
    6: "Steiermark",
    7: "Tirol",
    8: "Vorarlberg",
    9: "Wien",
}

# Month map
month_map = {
    1: "Januar",
    2: "Februar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember"
}

# Weekday map
weekday_map = {
    1: "Montag",
    2: "Dienstag",
    3: "Mittwoch",
    4: "Donnerstag",
    5: "Freitag",
    6: "Samstag",
    7: "Sonntag",
}

# Data fetching
response = requests.get(API_URL)
data = pd.read_csv(io.StringIO(response.text))

# Adapt datatypes
data["Getötete"] = pd.to_numeric(data["Getötete"], errors="coerce")
data["Berichtsjahr"] = data["Berichtsjahr"].astype(str)
data["Bundesland_ID"] = pd.to_numeric(data["Bundesland_ID"], errors="coerce")
data["Monat_ID"] = pd.to_numeric(data["Monat_ID"], errors="coerce")
data["Wochentag_ID"] = pd.to_numeric(data["Wochentag_ID"], errors="coerce")
data["Geschlecht_ID"] = pd.to_numeric(data["Geschlecht_ID"], errors="coerce")

# Map the data to their commonly used names
data["Bundesland"] = data["Bundesland_ID"].map(state_map)
data["Wochentag"] = data["Wochentag_ID"].map(weekday_map)
data["Monat"] = data["Monat_ID"].map(month_map)
data["Geschlecht"] = data["Geschlecht_ID"].map({1: "Männlich", 2: "Weiblich"})

# Dash-App initialization
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Getötete im Straßenverkehr in Österreich", style={"textAlign": "center"}),
    html.P("nach Bundesland und Berichtsjahr", style={"textAlign": "center", "fontSize": "18px"}),

    html.Div([
        html.Div([
            dcc.Dropdown(
                id="bundesland-filter",
                options=[{"label": bl, "value": bl} for bl in data["Bundesland"].dropna().unique()],
                multi=True,
                placeholder="Wählen Sie ein Bundesland...",
                value=[]
            )
        ], style={"width": "19%", "display": "inline-block", "padding": "0 0.5%"}),

        html.Div([
            dcc.Dropdown(
                id="jahr-filter",
                options=[{"label": yr, "value": yr} for yr in data["Berichtsjahr"].dropna().unique()],
                multi=True,
                placeholder="Jahr wählen...",
                value=[]
            )
        ], style={"width": "19%", "display": "inline-block", "padding": "0 0.5%"}),

        html.Div([
            dcc.Dropdown(
                id="monat-filter",
                options=[{"label": m, "value": m} for m in data["Monat"].dropna().unique()],
                multi=True,
                placeholder="Monat wählen...",
                value=[]
            )
        ], style={"width": "19%", "display": "inline-block", "padding": "0 0.5%"}),

        html.Div([
            dcc.Dropdown(
                id="wochentag-filter",
                options=[{"label": wt, "value": wt} for wt in data["Wochentag"].dropna().unique()],
                multi=True,
                placeholder="Wochentag wählen...",
                value=[]
            )
        ], style={"width": "19%", "display": "inline-block", "padding": "0 0.5%"}),

        html.Div([
            dcc.Dropdown(
                id="geschlecht-filter",
                options=[{"label": g, "value": g} for g in data["Geschlecht"].dropna().unique()],
                multi=True,
                placeholder="Geschlecht wählen...",
                value=[]
            )
        ], style={"width": "19%", "display": "inline-block", "padding": "0 0.5%"}),
    ], style={"width": "100%", "textAlign": "center", "marginBottom": "10px"}),

    html.Div(
        html.Button("Alle Filter zurücksetzen", id="reset-filters", n_clicks=0, style={"margin": "10px auto", "display": "block"}),
    ),

    dcc.Graph(id="verkehrs-tote-chart"),

    html.Footer(
        "Quelle: Statistik der Straßenverkehrsunfälle mit Personenschaden, Statistik Austria",
        style={"textAlign": "center", "padding": "1em", "fontSize": "14px", "color": "#666"},
    ),
])

@app.callback(
    [
        Output("verkehrs-tote-chart", "figure"),
        Output("bundesland-filter", "value"),
        Output("jahr-filter", "value"),
        Output("monat-filter", "value"),
        Output("wochentag-filter", "value"),
        Output("geschlecht-filter", "value"),
    ],
    [
        Input("bundesland-filter", "value"),
        Input("jahr-filter", "value"),
        Input("monat-filter", "value"),
        Input("wochentag-filter", "value"),
        Input("geschlecht-filter", "value"),
        Input("reset-filters", "n_clicks"),
    ]
)

# Updating the chart after filters have been selected
def update_chart(bundeslaender, jahre, monate, wochentage, geschlechter, reset_clicks):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    if triggered_id == 'reset-filters':
        return dash.no_update, [], [], [], [], []

    df = data.copy()
    if bundeslaender:
        df = df[df["Bundesland"].isin(bundeslaender)]
    if jahre:
        df = df[df["Berichtsjahr"].isin(jahre)]
    if monate:
        df = df[df["Monat"].isin(monate)]
    if wochentage:
        df = df[df["Wochentag"].isin(wochentage)]
    if geschlechter:
        df = df[df["Geschlecht"].isin(geschlechter)]

    grouped = df.groupby(["Berichtsjahr", "Bundesland"], as_index=False)["Getötete"].sum()

    fig = px.area(
        grouped,
        x="Berichtsjahr",
        y="Getötete",
        color="Bundesland",
        line_group="Bundesland",
        markers=True,
        title="Verkehrstote nach Bundesland",
    )

    fig.update_layout(
        plot_bgcolor="white",
        xaxis=dict(title="Berichtsjahr", showgrid=False, tickmode="linear"),
        yaxis=dict(title="Getötete", gridcolor="#eee"),
        legend_title_text="Bundesland",
        margin=dict(t=60, b=40, l=40, r=40),
        title_x=0.5,
    )

    return fig, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

# main
if __name__ == "__main__":
    app.run(debug=False)