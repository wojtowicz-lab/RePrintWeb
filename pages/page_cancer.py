from utils.utils import data
from utils.figpanel import create_empty_figure_with_text, create_main_dashboard
from utils.uploader import parse_contents, load_signatures
from dash import dcc, html
from main import app
import numpy as np
from sigconfide.utils.utils import is_wholenumber
from dash import Input, Output, State
import dash_bootstrap_components as dbc
from pages.nav import navbar
import pandas as pd
import dash


organs = [
    "Breast", "Ovary", "Kidney", "Colorectal", "Bone_SoftTissue",
    "Lung", "Uterus", "CNS", "Prostate", "Bladder", "Skin",
    "Stomach", "NET", "Pancreas", "Biliary", "Liver", "Lymphoid",
    "Myeloid", "Oral_Oropharyngeal", "Esophagus", "Head_neck"
]
data = {
    f'{organ}_Signature.csv': pd.read_csv(f'data/signatures_organ/latest/{organ}_Signature.csv', sep=',').columns[1:].to_list() for organ in organs
}
#@todo change version for signatures latest/version_1/version_2
# Application layout
page2_layout = html.Div([
    navbar,
    dbc.Container([
    html.Div([
        dcc.Upload(
            id='upload-data-cancer',
            children=html.Div(['Drag and Drop Mutational Profiles (csv, tsv, vcf) format (required)']),
            style={
                'width': '300px',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            },
            multiple=False
        ),
        dcc.Store(id='session-cancer', storage_type='session', data=None),
        dcc.Dropdown(
            id='patient-dropdown-cancer',
            options=[],
            value='',
            placeholder='Please upload your catalogs to chose the patient'
        ),
        dcc.Dropdown(
            id='dropdown-cancer',
            options=[
                {'label': f'{organ}_Signature.csv', 'value': f'{organ}_Signature.csv'} for organ in organs
            ],
            disabled=False,
            value='Biliary_Signature.csv'
        ),
        dcc.Dropdown(
            id='signatures-dropdown-cancer',
            options=[{'label': k, 'value': k} for k in data.keys()],
            multi=True,
            value=[k for k in data['Biliary_Signature.csv']],
        ),
        html.Div(id='upload-message-cancer',
                 style={
                     'width': '50%',
                     'height': '60px',
                     'lineHeight': '60px',
                     'borderWidth': '1px',
                     'borderStyle': 'line',
                     'borderRadius': '5px',
                     'textAlign': 'center',
                     'margin': '10px'
                 },
        ),
    ], style={'padding': '10px'}),
    html.Div([
        dbc.InputGroup(
            [
                dbc.InputGroupText("Bootstrap replicates:"),
                dbc.Input(id='input-R-cancer', type='number', value=100),
            ],
            className="mb-3",
        ),
        dbc.Tooltip("The number of bootstrap replicates used for significance testing.", target="input-R", placement='top'),

        dbc.InputGroup(
            [
                dbc.InputGroupText("Mutation count:"),
                dbc.Input(id='input-mutation-count-cancer', type='number', value=1000),
            ],
            className="mb-3",
        ),
        dbc.Tooltip("The observed mutation profile vector for a patient/sample. "
                    "If m is a vector of counts, then mutation.count equals the summation of all the counts. "
                    "If m is probabilities, then mutation.count has to be specified.", target="input-mutation-count", placement='top'),

        dbc.InputGroup(
            [
                dbc.InputGroupText("P-value:"),
                dbc.Input(id='input-p-value-cancer', type='number', value=0.02, step=0.01),
            ],
            className="mb-3",
        ),
        dbc.Tooltip("The p-value threshold below which a signature is considered significant.", target="input-p-value", placement='top'),

        dbc.InputGroup(
            [
                dbc.InputGroupText("Threshold:"),
                dbc.Input(id='input-threshold-cancer', type='number', value=0.01, step=0.01),
            ],
            className="mb-3",
        ),
        dbc.Tooltip("The threshold used to determine if a signature's exposure is significant in the bootstrap samples.", target="input-threshold", placement='top'),
    ], style={'display': 'flex', 'justifyContent': 'center', 'padding': '10px'}),
    html.Button('Run model',
                id='clear-button-cancer',
                className='btn btn-primary'),
    dcc.Loading(
        id="loading-1",
        type="default",
        children=[
            dcc.Graph(id='bar-plot-bootstrap-cancer'),
            dcc.Graph(id='bar-plot-modelselection-cancer')
        ],
    ),
    ])
])

@app.callback(
    [Output('session-cancer', 'data')],
    [Input('upload-data-cancer', 'contents')],
    [State('upload-data-cancer', 'filename')]
)
def update_output_2(contents, filename):
    if contents is not None:
        df = parse_contents(contents, filename)
        patient = df.columns.to_list()[0]
        return [{'data': df.to_dict('records'), 'filename': filename, 'patient': patient}]
    else:
        return dash.no_update

@app.callback(
    [Output('signatures-dropdown-cancer', 'options'),
     Output('signatures-dropdown-cancer', 'value')],
    [Input('dropdown-cancer', 'value')]
)
def set_options(selected_category):
    return [{'label': f"{i}", 'value': i} for i in data[selected_category]], [i for i in data[selected_category]]


@app.callback(
    [Output('bar-plot-bootstrap-cancer', 'figure'),
     Output('bar-plot-modelselection-cancer', 'figure'),
     Output('input-mutation-count-cancer', 'value')],
    [Input('session-cancer', 'data'),
     Input('clear-button-cancer', 'n_clicks'),
     Input('patient-dropdown-cancer', 'value')
    ],
    [
     State('dropdown-cancer', 'value'),
     State('signatures-dropdown-cancer', 'value'),
     State('input-R-cancer', 'value'),
     State('input-mutation-count-cancer', 'value'),
     State('input-p-value-cancer', 'value'),
     State('input-threshold-cancer', 'value'),
     ]
)
def update_output(contents, button, patient, dropdown_value, signatures_new, R, mutation_count, p_value, threshold):
    if contents is not None and patient != '':
        df = pd.DataFrame(contents['data'])
        data, patients = df.to_numpy(), df.columns.to_numpy()
        column_index = np.where(patients == patient)[0]

        patient_column = data[:, column_index].squeeze()
        if all(is_wholenumber(val) for val in patient_column):
            mutation_count = patient_column.sum()

        signatures, names = load_signatures(dropdown_value, organ=True)

        return create_main_dashboard(names, signatures_new, signatures, patient_column, patient, R, mutation_count, threshold, p_value)

    else:
        return create_empty_figure_with_text("Please upload catalogs to view the plot."), create_empty_figure_with_text("Please upload catalogs to view the plot."), 0

@app.callback(
    Output('upload-message-cancer', 'children'),
    Output('patient-dropdown-cancer', 'options'),
    Output('patient-dropdown-cancer', 'value'),
    [Input('session-cancer', 'data')]
)
def update_message(contents):
    if contents is not None:
        df = pd.DataFrame(contents['data'])
        patients = df.columns.to_list()
        return html.Div(f'File {contents["filename"]} has been uploaded.'), [{'label': patient, 'value': patient} for patient in patients], contents['patient']
    return '', [{'label': 'None', 'value': 'None'}], None