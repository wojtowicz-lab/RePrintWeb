from dash import dcc, html
from dash.dependencies import Input, Output
from main import *
from pages.page1 import page1_layout
from pages.page2 import page2_layout
from pages.page4 import page4_layout

server = app.server

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
])
# Favicon i title
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>DNA Repair Footprint Uncovers Contribution of DNA Repair Mechanism to Mutational Signatures</title>
        {%favicon%}
        {%css%}
        <link rel="icon" type="image/png" href="/assets/favicon.png">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return page1_layout
    elif pathname == '/page1':
        return page2_layout
    elif pathname == '/page3':
        return page4_layout

# Callback to set the active state
@app.callback(
    [Output("nav-home", "active"),
     Output("nav-page1", "active"),
     Output("nav-page4", "active")
    ],
    [Input("url", "pathname")]
)
def set_active_nav(pathname):
    # Check the current pathname and return True for the matching NavLink
    if pathname == "/":
        return True, False, False
    elif pathname == "/page1":
        return False, True, False
    elif pathname == "/page3":
        return False, False, True

    return False, False, False


if __name__ == '__main__':
    app.run(debug=True, port=8080)
