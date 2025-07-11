from darts import TimeSeries
from darts.models import Theta
from darts.utils.timeseries_generation import datetime_attribute_timeseries
from darts.utils.missing_values import fill_missing_values
import plotly.graph_objects as go


class Forecast:

    def render_figure(self, symbol: str = None, data=None, periods=None):
        # m = Prophet()
        # m.fit(data)
        # future = m.make_future_dataframe(periods=periods)
        # forecast = m.predict(future)
        #
        # forecast_fig = plot_plotly(m, forecast, uncertainty=True, plot_cap=True, trend=False, changepoints=True)

        # Initialisation et entraînement d’un modèle de base
        model = Theta()  # ou ExponentialSmoothing() / LinearRegressionModel()
        model.fit(data)

        # Génération de la prévision (comme `make_future_dataframe(periods=...)`)
        forecast = model.predict(n=periods)

        df_series = data.pd_dataframe()
        df_forecast = forecast.pd_dataframe()

        # ➤ Construction de la figure Plotly
        fig = go.Figure()

        # Historique
        fig.add_trace(go.Scatter(
            x=df_series.index,
            y=df_series['y'],
            mode='lines',
            name='Historique'
        ))

        # Prévision
        fig.add_trace(go.Scatter(
            x=df_forecast.index,
            y=df_forecast['y'],
            mode='lines',
            name='Prévision',
            line=dict(dash='dash')
        ))

        fig.update_layout(
            title='Prévision avec Darts',
            xaxis_title='Date',
            yaxis_title='Valeur',
            template='plotly_white'
        )
        return fig