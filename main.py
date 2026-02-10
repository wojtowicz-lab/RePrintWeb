from dash import Dash
import dash_bootstrap_components as dbc
import os

app = Dash(
    __name__, 
    suppress_callback_exceptions=True, 
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    serve_locally=False,
    include_assets_files=False,
    assets_folder=os.path.join(os.path.dirname(__file__), 'assets'),
    assets_url_path='/assets'
)

