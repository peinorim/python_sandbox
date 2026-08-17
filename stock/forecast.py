from datetime import timedelta

import numpy as np
import pandas as pd
import plotly.graph_objs as go
from prophet import Prophet

# --- Palette moderne ---
_COLORS = {
    "bg": "#0e1117",
    "paper": "#161b22",
    "grid": "rgba(255,255,255,0.2)",
    "text": "#c9d1d9",
    "muted": "#8b949e",
    "accent": "#58a6ff",
    "actual": "#FAFAFA",
    "forecast": "#f0883e",
    "uncertainty": "rgba(240,136,62,0.3)",
    "changepoint": "rgba(255,75,75,0.45)",
    "btn_active": "#58a6ff",
    "btn_bg": "#21262d",
}


def _plot_plotly(
    m: Prophet,
    fcst: pd.DataFrame,
    uncertainty: bool = True,
    plot_cap: bool = True,
    trend: bool = False,
    changepoints: bool = False,
    changepoints_threshold: float = 0.01,
    xlabel: str = 'ds',
    ylabel: str = 'y',
    figsize: tuple = (900, 600),
) -> go.Figure:
    """Réimplémentation locale de prophet.plot.plot_plotly.

    La version fournie par le package prophet (>=1.4.0) contient des
    `assert m.history` / `assert m.changepoints` qui déclenchent
    `ValueError: The truth value of a DataFrame is ambiguous` dès que
    `m.history` contient plus d'une ligne (pandas >= 2). Cette version
    corrige ces vérifications en utilisant `is not None` / `len(...) > 0`.
    """
    prediction_color = '#0072B2'
    error_color = 'rgba(0, 114, 178, 0.2)'
    actual_color = 'black'
    cap_color = 'black'
    trend_color = '#B23B00'
    line_width = 2
    marker_size = 4

    data = []
    # Add actual
    assert m.history is not None
    data.append(go.Scatter(
        name='Actual',
        x=m.history['ds'],
        y=m.history['y'],
        marker=dict(color=actual_color, size=marker_size),
        mode='markers'
    ))
    # Add lower bound
    if uncertainty and m.uncertainty_samples:
        data.append(go.Scatter(
            x=fcst['ds'],
            y=fcst['yhat_lower'],
            mode='lines',
            line=dict(width=0),
            hoverinfo='skip'
        ))
    # Add prediction
    data.append(go.Scatter(
        name='Predicted',
        x=fcst['ds'],
        y=fcst['yhat'],
        mode='lines',
        line=dict(color=prediction_color, width=line_width),
        fillcolor=error_color,
        fill='tonexty' if uncertainty and m.uncertainty_samples else 'none'
    ))
    # Add upper bound
    if uncertainty and m.uncertainty_samples:
        data.append(go.Scatter(
            x=fcst['ds'],
            y=fcst['yhat_upper'],
            mode='lines',
            line=dict(width=0),
            fillcolor=error_color,
            fill='tonexty',
            hoverinfo='skip'
        ))
    # Add caps
    if 'cap' in fcst and plot_cap:
        data.append(go.Scatter(
            name='Cap',
            x=fcst['ds'],
            y=fcst['cap'],
            mode='lines',
            line=dict(color=cap_color, dash='dash', width=line_width),
        ))
    if m.logistic_floor and 'floor' in fcst and plot_cap:
        data.append(go.Scatter(
            name='Floor',
            x=fcst['ds'],
            y=fcst['floor'],
            mode='lines',
            line=dict(color=cap_color, dash='dash', width=line_width),
        ))
    # Add trend
    if trend:
        data.append(go.Scatter(
            name='Trend',
            x=fcst['ds'],
            y=fcst['trend'],
            mode='lines',
            line=dict(color=trend_color, width=line_width),
        ))
    # Add changepoints
    assert m.changepoints is not None
    if changepoints and len(m.changepoints) > 0:
        signif_changepoints = m.changepoints[
            np.abs(np.nanmean(m.params['delta'], axis=0)) >= changepoints_threshold
        ]
        data.append(go.Scatter(
            x=signif_changepoints,
            y=fcst.loc[fcst['ds'].isin(signif_changepoints), 'trend'],
            marker=dict(size=50, symbol='line-ns-open', color=trend_color,
                        line=dict(width=line_width)),
            mode='markers',
            hoverinfo='skip'
        ))

    layout = dict(
        showlegend=False,
        width=figsize[0],
        height=figsize[1],
        yaxis=dict(title=ylabel),
        xaxis=dict(
            title=xlabel,
            type='date',
            rangeselector=dict(
                buttons=list([
                    dict(count=7, label='1w', step='day', stepmode='backward'),
                    dict(count=1, label='1m', step='month', stepmode='backward'),
                    dict(count=6, label='6m', step='month', stepmode='backward'),
                    dict(count=1, label='1y', step='year', stepmode='backward'),
                    dict(step='all')
                ])
            ),
            rangeslider=dict(visible=True),
        ),
    )
    return go.Figure(data=data, layout=layout)


class Forecast:

    def __init__(self):
        self.m = Prophet()

    def get_future_data(self, data: dict = None, periods: int = None):
        self.m.fit(data)
        future = self.m.make_future_dataframe(periods=periods)
        return self.m.predict(future)

    def render_figure(self, symbol: str = None, info: dict = None, data=None, periods=None):

        forecast = self.get_future_data(data=data, periods=periods)
        forecast_fig = _plot_plotly(self.m, forecast, uncertainty=True, plot_cap=True, changepoints=True)

        # ── Titre ────────────────────────────────────────────
        title_text = (
            f"{info.get('shortName', '').strip()} ({symbol})  ·  "
            f"200 MA : {round(float(info.get('twoHundredDayAverage', 'N/A')), 2)}"
        ).upper() if info else symbol.upper()

        # ── Restyle des traces existantes ────────────────────
        # Prophet plot_plotly génère les traces dans cet ordre :
        #   0: "Actual"    — markers (points réels)
        #   1: (sans nom)  — yhat_lower, line width=0
        #   2: "Predicted" — yhat, line + fill='tonexty'
        #   3: (sans nom)  — yhat_upper, line width=0, fill='tonexty'
        #   4: "Trend"     — trend line
        #   5: (sans nom)  — changepoints markers
        for trace in forecast_fig.data:
            name = (trace.name or "").lower()

            if name == "actual":
                trace.marker = dict(
                    color=_COLORS["actual"],
                    size=5,
                    opacity=0.9,
                    line=dict(width=0),
                )
                trace.name = "Réel"
            elif name == "predicted":
                trace.line = dict(color=_COLORS["forecast"], width=2.5)
                trace.fillcolor = _COLORS["uncertainty"]
                trace.name = "Prévision"
            elif not name:
                # Traces sans nom : bandes d'incertitude ou changepoints
                fill = getattr(trace, "fill", None) or ""
                mode = getattr(trace, "mode", "") or ""
                if fill or mode == "lines":
                    # Bandes d'incertitude (upper/lower)
                    if fill:
                        trace.fillcolor = _COLORS["uncertainty"]
                    trace.line = dict(width=0, color="rgba(0,0,0,0)")
                    trace.showlegend = False
                elif mode == "markers":
                    # Changepoints
                    trace.marker.color = _COLORS["changepoint"]
                    trace.marker.line.color = _COLORS["changepoint"]
                    trace.name = "Changepoint"
                    trace.showlegend = True

        # ── Range par défaut : 1 an ──────────────────────────
        last_date = forecast["ds"].max()
        one_year_ago = last_date - timedelta(days=365)
        default_range = [one_year_ago.strftime("%Y-%m-%d"), last_date.strftime("%Y-%m-%d")]

        # ── Layout moderne (dark theme) ──────────────────────
        forecast_fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=_COLORS["paper"],
            plot_bgcolor=_COLORS["bg"],
            width=None,  # responsive
            font=dict(family="Inter, Segoe UI, sans-serif", size=13, color=_COLORS["text"]),
            title=dict(
                text=title_text,
                font=dict(size=18, color=_COLORS["text"]),
                x=0.5,
                xanchor="center",
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=11, color=_COLORS["muted"]),
                bgcolor="rgba(0,0,0,0)",
            ),
            margin=dict(l=50, r=30, t=80, b=50),
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor=_COLORS["paper"],
                font_size=12,
                font_color=_COLORS["text"],
                bordercolor=_COLORS["grid"],
            ),
            xaxis=dict(
                title="",
                range=default_range,
                tickformat="%d %b %Y",
                tickfont=dict(size=11, color=_COLORS["muted"]),
                gridcolor=_COLORS["grid"],
                zeroline=False,
                showline=False,
                rangeselector=dict(
                    bgcolor=_COLORS["btn_bg"],
                    activecolor=_COLORS["btn_active"],
                    font=dict(size=11, color=_COLORS["text"]),
                    buttons=[
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1A", step="year", stepmode="backward"),
                        dict(step="all", label="Tout"),
                    ],
                ),
                rangeslider=dict(visible=True, bgcolor=_COLORS["paper"], thickness=0.1),
                type="date",
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=_COLORS["grid"],
                zeroline=False,
                showline=False,
                tickfont=dict(size=11, color=_COLORS["muted"]),
                title="",
            ),
        )

        return forecast_fig