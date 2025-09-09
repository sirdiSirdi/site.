import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, dash_table
import pandas as pd
import sqlite3
import datetime
import os

# --- Database Configuration ---
DB_FILE = 'pilot_training_portal.db'

# --- Form Definitions & Questions ---
FORM_CONFIG = {
    "EBT Modules Forms": {
        "table_name": "EbtModules",
        "questions": {
            "ModuleNumber": {"label": "EBT Module Number", "type": "number", "options": None},
            "Competency": {"label": "Key Competency Assessed", "type": "dropdown",
                           "options": ["Communication", "Leadership", "Situational Awareness"]},
            "PerformanceScore": {"label": "Performance Score (1-5)", "type": "number", "options": None},
        }
    },
    "Additional FSTD Forms": {
        "table_name": "AdditionalFstd",
        "questions": {
            "DeviceID": {"label": "Simulator Device ID", "type": "text", "options": None},
            "Maneuver": {"label": "Maneuver Practiced", "type": "dropdown",
                         "options": ["Engine Failure on Takeoff", "Go-Around", "Crosswind Landing"]},
            "Outcome": {"label": "Maneuver Outcome", "type": "dropdown",
                        "options": ["Successful", "Unstable Approach", "Requires Follow-up"]},
        }
    },
    "Bespoke Additional FSTD Forms": {
        "table_name": "BespokeFstd",
        "questions": {
            "ScenarioName": {"label": "Bespoke Scenario Name", "type": "text", "options": None},
            "TrainingObjective": {"label": "Primary Training Objective", "type": "textarea", "options": None},
            "PilotFeedback": {"label": "Pilot Subjective Feedback", "type": "textarea", "options": None},
        }
    },
    "Out of Phase Assessment Forms": {
        "table_name": "OutOfPhaseAssessment",
        "questions": {
            "AssessmentReason": {"label": "Reason for Assessment", "type": "dropdown",
                                 "options": ["Post-Incident", "Performance Decline", "Return to Work"]},
            "AssessorName": {"label": "Assessor Name", "type": "text", "options": None},
            "FinalRecommendation": {"label": "Final Recommendation", "type": "textarea", "options": None},
        }
    },
    "Line Event Forms": {
        "table_name": "LineEvents",
        "questions": {
            "FlightNumber": {"label": "Flight Number", "type": "text", "options": None},
            "DepartureAirport": {"label": "Departure Airport (IATA)", "type": "text", "options": None},
            "EventObserved": {"label": "Observed Event Description", "type": "textarea", "options": None}
        }
    },
    "EBT-I AOC Forms": {
        "table_name": "EbtiAoc",
        "questions": {
            "AocReference": {"label": "AOC Reference Number", "type": "text", "options": None},
            "IsConfirmed": {"label": "EBT Manager Acknowledged", "type": "dropdown", "options": ["Yes", "No"]},
            "ConfirmationDate": {"label": "Date of Acknowledgement", "type": "date", "options": None},
        }
    },
    "Technical Ground Training Forms": {
        "table_name": "GroundTraining",
        "questions": {
            "CourseTitle": {"label": "Course Title", "type": "text", "options": None},
            "AssessmentScore": {"label": "Assessment Score (%)", "type": "number", "options": None},
            "InstructorFeedback": {"label": "Instructor Feedback", "type": "textarea", "options": None},
        }
    },
    "Appendix 10 Forms": {
        "table_name": "Appendix10",
        "questions": {
            "FlightHours": {"label": "Total Flight Hours", "type": "number", "options": None},
            "AircraftType": {"label": "Aircraft Type", "type": "text", "options": None},
            "EndorsementSought": {"label": "Endorsement Sought", "type": "text", "options": None},
        }
    },
    "Command Upgrade Forms": {
        "table_name": "CommandUpgrade",
        "questions": {
            "YearsAsFirstOfficer": {"label": "Years as First Officer", "type": "number", "options": None},
            "CheckCaptain": {"label": "Check Captain Name", "type": "text", "options": None},
            "UpgradeReadiness": {"label": "Upgrade Readiness Assessment", "type": "dropdown",
                                 "options": ["Ready", "Not Ready", "Requires More Training"]},
        }
    }
}


def init_db():
    """
    Initializes the database and creates tables if they don't exist.
    This version DOES NOT delete the database on restart.
    """
    with sqlite3.connect(DB_FILE) as cnxn:
        cursor = cnxn.cursor()
        print(f"Connecting to database: {DB_FILE}")
        for form_name, config in FORM_CONFIG.items():
            table_name = config['table_name']
            columns = [
                "ID INTEGER PRIMARY KEY AUTOINCREMENT",
                "SubmissionDate TEXT",
                "TrainerName TEXT",
                "TrainingDate TEXT"
            ]
            for col_name, col_attrs in config['questions'].items():
                sql_type = "TEXT"
                if col_attrs['type'] == 'number':
                    sql_type = "REAL"
                columns.append(f"{col_name} {sql_type}")

            create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)});"
            cursor.execute(create_table_sql)
        cnxn.commit()
        print("Database initialization complete. Tables are ready.")


def generate_form_layout(form_name):
    """Generates a dynamic form layout based on FORM_CONFIG."""
    form_slug = form_name.replace(' ', '-')
    config = FORM_CONFIG[form_name]

    form_elements = [
        dbc.Row([
            dbc.Label("Name of Pilot Trainer", width=4),
            dbc.Col(dbc.Input(type="text", id=f'trainer-name-{form_slug}'), width=8),
        ], className="mb-3"),
        dbc.Row([
            dbc.Label("Training Date", width=4),
            dbc.Col(dcc.DatePickerSingle(id=f'training-date-{form_slug}', date=datetime.date.today()), width=8),
        ], className="mb-3"),
    ]

    for question_id, attrs in config['questions'].items():
        input_component = None
        input_id = f'{question_id}-{form_slug}'
        if attrs['type'] == 'text':
            input_component = dbc.Input(type="text", id=input_id)
        elif attrs['type'] == 'number':
            input_component = dbc.Input(type="number", id=input_id)
        elif attrs['type'] == 'textarea':
            input_component = dbc.Textarea(id=input_id, placeholder="Enter details...")
        elif attrs['type'] == 'dropdown':
            input_component = dcc.Dropdown(id=input_id, options=attrs['options'])
        elif attrs['type'] == 'date':
            input_component = dcc.DatePickerSingle(id=input_id, date=datetime.date.today())

        form_elements.append(
            dbc.Row([
                dbc.Label(attrs['label'], width=4),
                dbc.Col(input_component, width=8),
            ], className="mb-3")
        )

    return html.Div([
        html.H2(f"{form_name}"),
        html.Hr(),
        dbc.Alert(id=f'alert-{form_slug}', is_open=False, duration=4000, className="mt-3"),
        dbc.Form(form_elements),
        dbc.Button("Submit", id=f'submit-button-{form_slug}', color="primary"),
    ])


# --- App Initialization ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# --- App Layout ---
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dbc.NavbarSimple(
        children=[
            dbc.DropdownMenu(
                children=[dbc.DropdownMenuItem(name, href=f"/form/{name.replace(' ', '-')}") for name in
                          FORM_CONFIG.keys()],
                nav=True,
                in_navbar=True,
                label="Form Folders",
            ),
            dbc.NavLink("Database View", href="/admin"),  # CHANGED
        ],
        brand="Pilot Training Portal",
        brand_href="/",
        color="dark",
        dark=True,
    ),
    dbc.Container(id='page-content', className='mt-4')
])


# --- Page Routing Callback ---
@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if pathname.startswith('/form/'):
        form_slug = pathname.split('/')[-1]
        form_name = form_slug.replace('-', ' ')
        if form_name in FORM_CONFIG:
            return generate_form_layout(form_name)
        return html.H1("404: Form Not Found", className="text-danger")

    elif pathname == '/admin':
        return html.Div([
            html.H2("Database View"),  # CHANGED
            html.P("Select a form to view its submissions:"),
            dcc.Dropdown(
                id='admin-form-selector',
                options=[{'label': name, 'value': config['table_name']} for name, config in FORM_CONFIG.items()],
                placeholder="Select a form type...",
                className="mb-4"
            ),
            html.Div(id='admin-table-container')
        ])

    return html.Div([
        html.H1("Welcome to the Pilot Training Portal"),
        html.P("Select a form from the 'Form Folders' dropdown to begin."),
    ], className="text-center mt-5")


# --- Admin Table Callback ---
@app.callback(
    Output('admin-table-container', 'children'),
    Input('admin-form-selector', 'value')
)
def display_admin_table(table_name):
    if not table_name:
        return dbc.Alert("Please select a form type to see the data.", color="info")
    try:
        with sqlite3.connect(DB_FILE) as cnxn:
            df = pd.read_sql(f"SELECT * FROM {table_name} ORDER BY ID DESC", cnxn)
        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns],
            page_size=20,
            style_table={'overflowX': 'auto'},
            filter_action="native",
            sort_action="native",
        )
    except Exception as e:
        return dbc.Alert(f"Error loading data for table '{table_name}': {e}", color="danger")


# --- Function to Create Form Callbacks Dynamically ---
def create_form_callback(form_name, config):
    form_slug = form_name.replace(' ', '-')
    table_name = config['table_name']
    question_ids = list(config['questions'].keys())

    state_inputs = [
                       State(f'trainer-name-{form_slug}', 'value'),
                       State(f'training-date-{form_slug}', 'date')
                   ] + [State(f'{q_id}-{form_slug}', 'value') for q_id in question_ids]

    @callback(
        Output(f'alert-{form_slug}', 'is_open'),
        Output(f'alert-{form_slug}', 'children'),
        Output(f'alert-{form_slug}', 'color'),
        Input(f'submit-button-{form_slug}', 'n_clicks'),
        state_inputs,
        prevent_initial_call=True
    )
    def submit_form(n_clicks, *args):
        if not n_clicks:
            return False, "", "light"

        if any(val is None or val == '' for val in args):
            return True, "Please fill out all required fields.", "warning"

        try:
            with sqlite3.connect(DB_FILE) as cnxn:
                cursor = cnxn.cursor()
                trainer_name, training_date, *dynamic_values = args
                columns = ['SubmissionDate', 'TrainerName', 'TrainingDate'] + question_ids
                values = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), trainer_name,
                          training_date] + dynamic_values
                placeholders = ', '.join(['?'] * len(columns))
                sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders});"
                cursor.execute(sql, tuple(values))
                cnxn.commit()
            return True, "Form submitted successfully!", "success"
        except sqlite3.Error as ex:
            return True, f"Database error: {ex}", "danger"


# --- Loop to register a callback for each form ---
for name, conf in FORM_CONFIG.items():
    create_form_callback(name, conf)

# --- Run Application ---
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
