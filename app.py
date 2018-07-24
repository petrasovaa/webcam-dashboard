#!/usr/bin/env python

import os
import glob
import dash
import flask
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime as dt
import urllib

csvdata = pd.read_csv('export.csv', parse_dates=['isodate'])
server = flask.Flask(__name__)
app = dash.Dash(__name__, sharing=True, server=server, csrf_protect=False)

app.title = "Health Matters"
app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

parks = csvdata['park'].unique()
initial_date = dt(2017, 6, 1)
park_names = {'Br': 'Braswell Park',
              'Cl': 'Clark Park',
              'Ga': 'Garysburg Community Park',
              'Ri': 'River FallsPark',
              'Ve': 'Veterans Memorial Park',
              'Wo': 'Woodland Park',
              'Pl': 'Tarboro Parking Lot Project',
              '4H': '4-H Rural Life Center'
             }

cameras_dir = './resources/'
cameras = [os.path.basename(img) for img in glob.glob(cameras_dir + '*.jpg')]
static_image_route = '/static/'



app.layout = \
    html.Div([
        html.H2('Health Matters Dashboard'),
        html.Div([
            html.Div([
                html.Div([html.Label('Park:'),
                          dcc.Dropdown(id='park-dropdown',
                                       options=sorted([{'label': park_names[park],
                                                        'value': park} for park in parks]))
                          ], className="three columns"),
                html.Div([html.Label('Camera:'),
                          dcc.Dropdown(id='camera-dropdown',
                                       options=sorted([{'label': camera,
                                                        'value': camera} for camera in parks]))
                          ], className="two columns"),
                html.Div([html.Label('Days:'),
                          dcc.DatePickerRange(id='date-picker-range',
                                              min_date_allowed=initial_date,
                                              max_date_allowed=dt.now(),
                                              start_date=initial_date,
                                              end_date=dt.now()),
                          ], className="three columns"),
                html.Div([html.Label('Days of week:'),
                          dcc.Checklist(id='weekdays_checkbox',
                                        options=[{'label': 'Mon', 'value': 1}, {'label': 'Tue', 'value': 2},
                                                 {'label': 'Wed', 'value': 3}, {'label': 'Thu', 'value': 4},
                                                 {'label': 'Fri', 'value': 5}, {'label': 'Sat', 'value': 6},
                                                 {'label': 'Sun', 'value': 7}],
                                        values=list(range(1, 8)),
                                        labelStyle={'display': 'inline-block', 'padding-right': '10px'},
                                        style={'padding-top': '10px', 'padding-bottom': '10px'})
                          ], className="four columns"),
                ], className="row", style={'padding-bottom': '20px', 'padding-left': '20px'}),
            html.Div([
                html.Div([html.Label('Hours:'),
                          dcc.RangeSlider(id="hour-filter",
                                          min=6, max=22, step=1,
                                          marks={h: '{}:00 '.format(h) for h in range(6, 23)},
                                          value=[6, 22])
                          ], className="ten columns", style={'padding-right': '5px', 'padding-left': '20px', 'padding-bottom': '30px'}),
                html.Div([html.A('Download filtered data as CSV', id='download-link', download="rawdata.csv",  href="",  target="_blank")],
                         className="two columns",
                         style={'padding-top': '20px'}),
                ], className="row"),
            html.Div([
                html.Div([html.Img(id='camera-image', style={'width': '100%'})
                          ], className="four columns", style={'padding-right': '5px', 'padding-left': '20px', 'padding-bottom': '30px'}),
                ], className="row"),
        ], style={'background-color': 'WhiteSmoke'}),
        html.Div([
            html.Div([dcc.Graph(id='x-time-series')], className="row",
                     style={'padding-top': '20px', 'padding-bottom': '20px', 'padding-left': '5px'}),
            html.Div([
                html.Div([dcc.Graph(id='plot-aggreg-day')],  className="six columns", style={'padding-left': '5px'}),
                html.Div([dcc.Graph(id='plot-aggreg-hour')],  className="six columns", style={'padding-left': '5px'})
                 ], className="row", style={'padding-bottom': '20px', 'padding-left': '5px'}),
            ])
        ])


app.config['supress_callback_exceptions'] = True


def create_time_series(dff, axis_type='Linear', title='Counts'):
    return {
        'data': [go.Bar(
            x=dff['isodate'],
            y=dff['count'],
            marker=dict(color='rgb(150,150,150)')
        )],
        'layout': {
            'title': "Number of visitors per day",
            'height': 225,
            'margin': {'l': 30, 'b': 40, 'r': 20, 't': 50},
            'annotations': [{
                'x': 0, 'y': 0.85, 'xanchor': 'left', 'yanchor': 'bottom',
                'xref': 'paper', 'yref': 'paper', 'showarrow': False,
                'align': 'left', 'bgcolor': 'rgba(255, 255, 255, 0.5)',
                'text': title
            }],
            'yaxis': {'type': 'linear' if axis_type == 'Linear' else 'log'},
            'xaxis': {'showgrid': False, 'ticks': 'outside'}
        }
    }


def create_aggr_weekday(df):
    return {
        'data': [go.Bar(
            x=df['weekday'],
            y=df['count']
        )],
        'layout': {
            'title': "Number of visitors by day of week",
            'height': 225,
            'margin': {'l': 30, 'b': 30, 'r': 20, 't': 50},
            'annotations': [{
                'x': 0, 'y': 0.85, 'xanchor': 'left', 'yanchor': 'bottom',
                'xref': 'paper', 'yref': 'paper', 'showarrow': False,
                'align': 'left', 'bgcolor': 'rgba(255, 255, 255, 0.5)',
                'text': 'Counts'
            }],
            'yaxis': {'type': 'linear'},
            'xaxis': {'showgrid': False, 'tickvals': range(1, 8), 'ticks': 'outside',
                      'ticktext': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                      }
        }
    }


def create_aggr_hour(df):
    return {
        'data': [go.Bar(
            x=df['hour'],
            y=df['count'],
            marker=dict(color='rgb(249,127,46)')
        )],
        'layout': {
            'title': "Number of visitors by hour",
            'height': 225,
            'margin': {'l': 30, 'b': 30, 'r': 20, 't': 50},
            'annotations': [{
                'x': 0, 'y': 0.85, 'xanchor': 'left', 'yanchor': 'bottom',
                'xref': 'paper', 'yref': 'paper', 'showarrow': False,
                'align': 'left', 'bgcolor': 'rgba(255, 255, 255, 0.5)',
                'text': 'Counts'
            }],
            'yaxis': {'type': 'linear'},
            'xaxis': {'showgrid': False, 'tickvals': [i - 0.5 for i in range(6, 24)], 'ticks': 'outside',
                      'ticktext': ['{}:00'.format(i) for i in range(6, 24)]
                      }
        }
    }


@app.callback(
    dash.dependencies.Output('download-link', 'href'),
    [dash.dependencies.Input('weekdays_checkbox', 'values'),
     dash.dependencies.Input('hour-filter', 'value'),
     dash.dependencies.Input('date-picker-range', 'start_date'),
     dash.dependencies.Input('date-picker-range', 'end_date'),
     dash.dependencies.Input('park-dropdown', 'value'),
     dash.dependencies.Input('camera-dropdown', 'value')])
def update_download_link(weekdays, hour, start_date, end_date, park, camera):
    df = csvdata[(csvdata['park'] == park) & (csvdata['camera'] == camera)]
    df = df[(df['isodate'] > start_date) & (df['isodate'] < end_date)]
    df = df[df['weekday'].isin(weekdays)]
    df = df[(df['hour'] >= hour[0]) & (df['hour'] < hour[1])]
    csv_string = df.to_csv(index=False, encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.quote(csv_string)
    return csv_string


# all filter callback to redraw overview figure
@app.callback(
    dash.dependencies.Output('plot-aggreg-hour', 'figure'),
    [dash.dependencies.Input('weekdays_checkbox', 'values'),
     dash.dependencies.Input('hour-filter', 'value'),
     dash.dependencies.Input('date-picker-range', 'start_date'),
     dash.dependencies.Input('date-picker-range', 'end_date'),
     dash.dependencies.Input('park-dropdown', 'value'),
     dash.dependencies.Input('camera-dropdown', 'value')])
def update_aggr_hour(weekdays, hour, start_date, end_date, park, camera):
    df = csvdata[(csvdata['park'] == park) & (csvdata['camera'] == camera)]
    df = df[(df['isodate'] > start_date) & (df['isodate'] < end_date)]
    df = df[df['weekday'].isin(weekdays)]
    df = df[(df['hour'] >= hour[0]) & (df['hour'] < hour[1])]
    df = df.groupby(pd.Grouper(key='hour')).sum().reset_index()
    return create_aggr_hour(df)


# all filter callback to redraw overview figure
@app.callback(
    dash.dependencies.Output('plot-aggreg-day', 'figure'),
    [dash.dependencies.Input('weekdays_checkbox', 'values'),
     dash.dependencies.Input('hour-filter', 'value'),
     dash.dependencies.Input('date-picker-range', 'start_date'),
     dash.dependencies.Input('date-picker-range', 'end_date'),
     dash.dependencies.Input('park-dropdown', 'value'),
     dash.dependencies.Input('camera-dropdown', 'value')])
def update_aggr_weekday(weekdays, hour, start_date, end_date, park, camera):
    df = csvdata[(csvdata['park'] == park) & (csvdata['camera'] == camera)]
    df = df[(df['isodate'] > start_date) & (df['isodate'] < end_date)]
    df = df[df['weekday'].isin(weekdays)]
    df = df[(df['hour'] >= hour[0]) & (df['hour'] < hour[1])]
    df = df.groupby(pd.Grouper(key='weekday')).sum().reset_index()
    return create_aggr_weekday(df)


# all filter callback to redraw overview figure
@app.callback(
    dash.dependencies.Output('x-time-series', 'figure'),
    [dash.dependencies.Input('weekdays_checkbox', 'values'),
     dash.dependencies.Input('hour-filter', 'value'),
     dash.dependencies.Input('date-picker-range', 'start_date'),
     dash.dependencies.Input('date-picker-range', 'end_date'),
     dash.dependencies.Input('park-dropdown', 'value'),
     dash.dependencies.Input('camera-dropdown', 'value')])
def update_overview(weekdays, hour, start_date, end_date, park, camera):
    df = csvdata[(csvdata['park'] == park) & (csvdata['camera'] == camera)]
    df = df[(df['isodate'] > start_date) & (df['isodate'] < end_date)]
    df = df[df['weekday'].isin(weekdays)]
    df = df[(df['hour'] >= hour[0]) & (df['hour'] < hour[1])]
    df = df.groupby(pd.Grouper(key='isodate', freq='D')).sum().reset_index()
    return create_time_series(df)


# set start date based on the camera
@app.callback(
    dash.dependencies.Output('date-picker-range', 'start_date'),
    [dash.dependencies.Input('park-dropdown', 'value'),
     dash.dependencies.Input('camera-dropdown', 'value')])
def set_date_start(park, camera):
    if park and camera:
        df = csvdata[(csvdata['park'] == park) & (csvdata['camera'] == camera)]
        return df['isodate'].min().to_pydatetime()
    return initial_date


# set end date based on the camera
@app.callback(
    dash.dependencies.Output('date-picker-range', 'end_date'),
    [dash.dependencies.Input('park-dropdown', 'value'),
     dash.dependencies.Input('camera-dropdown', 'value')])
def set_date_end(park, camera):
    if park and camera:
        df = csvdata[(csvdata['park'] == park) & (csvdata['camera'] == camera)]
        return df['isodate'].max().to_pydatetime()
    return initial_date


@app.callback(
    dash.dependencies.Output('camera-dropdown', 'options'),
    [dash.dependencies.Input('park-dropdown', 'value')])
def set_camera_options(selected_park):
    return sorted([{'label': i, 'value': i} for i in csvdata[csvdata['park'] == selected_park]['camera'].unique()])


@app.callback(
    dash.dependencies.Output('camera-dropdown', 'value'),
    [dash.dependencies.Input('camera-dropdown', 'options')])
def set_cameras_value(available_options):
    if available_options:
        return available_options[0]['value']
    return None


@app.callback(
    dash.dependencies.Output('camera-image', 'src'),
    [dash.dependencies.Input('park-dropdown', 'value'),
     dash.dependencies.Input('camera-dropdown', 'value')])
def update_image_src(parkv, camerav):
    for each in cameras:
        name = each.split('.')[0]
        try:
            county, city, park, camera = name.split('_')
            if park == parkv and camera == camerav:
                return os.path.join(static_image_route, each)
        except ValueError:
            pass
    return os.path.join(static_image_route, 'default_image.jpg')


@app.server.route('{}<image_path>.jpg'.format(static_image_route))
def serve_image(image_path):
    image_name = '{}.jpg'.format(image_path)
    if image_name not in cameras:
        raise Exception('"{}" is excluded from the allowed static files'.format(image_path))
    return flask.send_from_directory(cameras_dir, image_name)


if __name__ == '__main__':
    app.run_server(debug=True)
