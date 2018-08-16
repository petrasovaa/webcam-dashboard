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
from datetime import timedelta as td
import urllib

csvdata = pd.read_csv('export.csv', parse_dates=['isodate'])
csvdata.set_index('isodate', drop=False, inplace=True)
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
cameras = [os.path.basename(img) for img in glob.glob(cameras_dir + '*.JPG')]
static_image_route = '/static/'
plot_config = {'displaylogo': False,
               'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'autoScale2d',
                                          'toggleSpikelines', 'hoverClosestCartesian']}


app.layout = \
    html.Div([
        html.H3('Health Matters Dashboard'),
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div([html.Label('Park:'),
                                      dcc.Dropdown(id='park-dropdown',
                                                   options=sorted([{'label': park_names[park],
                                                                    'value': park} for park in parks]))
                                      ], className="six columns"),

                            html.Div([html.Label('Camera:'),
                                      dcc.Dropdown(id='camera-dropdown',
                                                   options=sorted([{'label': camera,
                                                                    'value': camera} for camera in parks]))
                                      ], className="three columns"),
                        ], className="row"),
                        html.Div([
                            html.Div([html.Label('Days:'),
                                      dcc.DatePickerRange(id='date-picker-range',
                                                          min_date_allowed=initial_date,
                                                          max_date_allowed=dt.now(),
                                                          start_date=initial_date,
                                                          end_date=dt.now()),
                                      ], className="five columns"),
                            html.Div([html.Label('Days of week:'),
                                      dcc.Checklist(id='weekdays_checkbox',
                                                    options=[{'label': 'Mon', 'value': 1}, {'label': 'Tue', 'value': 2},
                                                             {'label': 'Wed', 'value': 3}, {'label': 'Thu', 'value': 4},
                                                             {'label': 'Fri', 'value': 5}, {'label': 'Sat', 'value': 6},
                                                             {'label': 'Sun', 'value': 7}],
                                                    values=list(range(1, 8)),
                                                    labelStyle={'display': 'inline-block', 'padding-right': '10px'},
                                                    style={'padding-top': '10px', 'padding-bottom': '10px'})
                                      ], className="seven columns"),
                        ], className="row", style={'padding-top': '25px'}),
                        html.Div([
                            html.Div([html.Label('Hours:'),
                                      dcc.RangeSlider(id="hour-filter",
                                                      min=6, max=22, step=1,
                                                      marks={h: '{}:00 '.format(h) for h in range(6, 23)},
                                                      value=[6, 22])
                                      ], className="twelve columns", style={'padding-right': '5px', 'padding-left': '10px', 'padding-bottom': '30px'})
                        ], className="row", style={'padding-top': '25px'}),
                        html.Div([
                            html.Div([html.A('Download filtered data as CSV', id='download-link',
                                             download="rawdata.csv",  href="",  target="_blank")],
                                     className="twelve columns", style={'padding-top': '25px'}),
                        ], className="row"),
                    ], className="eight columns"),
                    html.Div([html.Img(id='camera-image', style={'width': '100%', 'max-width': '500px'})], className="four columns"),
                    ], className="row", style={'padding-right': '10px', 'padding-left': '10px', 'padding-top': '30px'})
                ], className="row", style={'padding-bottom': '5px', 'padding-left': '20px'}),
        ], style={'background-color': 'WhiteSmoke'}),
        html.Div([
            html.Div([dcc.Graph(id='x-time-series', config=plot_config)], className="row",
                     style={'padding-top': '20px', 'padding-bottom': '20px', 'padding-left': '5px'}),
            html.Div([
                html.Div([dcc.Graph(id='plot-aggreg-day', config=plot_config)],  className="six columns", style={'padding-left': '5px'}),
                html.Div([dcc.Graph(id='plot-aggreg-hour', config=plot_config)],  className="six columns", style={'padding-left': '5px'})
                 ], className="row", style={'padding-bottom': '20px', 'padding-left': '5px'}),
            html.Div([
                html.Div([dcc.Graph(id='plot-aggreg-day-avg', config=plot_config)],  className="six columns", style={'padding-left': '5px'}),
                html.Div([dcc.Graph(id='plot-aggreg-hour-avg', config=plot_config)],  className="six columns", style={'padding-left': '5px'})
                 ], className="row", style={'padding-bottom': '20px', 'padding-left': '5px'}),
            ])
        ])


app.config['supress_callback_exceptions'] = True


def create_time_series(dff, shapes, annotations, axis_type='Linear', title='Counts'):
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
            'annotations': annotations,
            'yaxis': {'type': 'linear' if axis_type == 'Linear' else 'log'},
            'xaxis': {'showgrid': False, 'ticks': 'outside'},
            'shapes': shapes
        }
    }


def highlight_intervals(df):
    ranges = []
    isodates = [row['isodate'] for index, row in df.iterrows()]
    if not isodates:
        return [], []
    last = isodates[0]
    for i in range(len(isodates) - 1):
        if isodates[i + 1] - isodates[i] > td(days=1):
            ranges.append((last, isodates[i]))
            last = isodates[i + 1]
    ranges.append((last, isodates[i + 1]))
    shapes = []
    annotations = []
    for each in ranges:
        shapes.append({'type': 'rect', 'xref': 'x', 'yref': 'paper', 'y0': 0, 'y1': 1,
                       'fillcolor': '#FF0000', 'opacity': 0.1, 'line': {'width': 0},
                       'x0': each[0], 'x1': each[1]})
        if (each[1] - each[0]) >= td(days=1):
            annotations.append({'x': each[0] + (each[1] - each[0]) / 2, 'y': 0.5, 'xanchor': 'center', 'yanchor': 'center',
                                'xref': 'x', 'yref': 'paper', 'showarrow': False,
                                'align': 'left', 'bgcolor': 'rgba(255, 255, 255, 0.5)',
                                'text': 'No images'})
    return shapes, annotations


def create_aggr_weekday(df, method):
    title = ''
    if method == 'count':
        title = "Number of visitors by day of week"
    elif method == 'avg':
        title = "Average number of visitors by day of week"
    return {
        'data': [go.Bar(
            x=df['weekday'],
            y=df['count']
        )],
        'layout': {
            'title': title,
            'height': 225,
            'margin': {'l': 30, 'b': 30, 'r': 20, 't': 50},
            'yaxis': {'type': 'linear'},
            'xaxis': {'showgrid': False, 'tickvals': range(1, 8), 'ticks': 'outside',
                      'ticktext': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                      }
        }
    }


def create_aggr_hour(df, method):
    title = ''
    if method == 'count':
        title = "Number of visitors by hour"
    elif method == 'avg':
        title = "Average number of visitors by hour"
    return {
        'data': [go.Bar(
            x=df['hour'],
            y=df['count'],
            marker=dict(color='rgb(249,127,46)')
        )],
        'layout': {
            'title': title,
            'height': 225,
            'margin': {'l': 30, 'b': 30, 'r': 20, 't': 50},
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
    df = df.loc[start_date:end_date]
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
    df = df.loc[start_date:end_date]
    df = df[df['weekday'].isin(weekdays)]
    df = df[(df['hour'] >= hour[0]) & (df['hour'] < hour[1])]
    df = df.groupby(pd.Grouper(key='hour')).sum().reset_index()
    return create_aggr_hour(df, method='count')


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
    df = df.loc[start_date:end_date]
    df = df[df['weekday'].isin(weekdays)]
    df = df[(df['hour'] >= hour[0]) & (df['hour'] < hour[1])]
    df = df.groupby(pd.Grouper(key='weekday')).sum().reset_index()
    return create_aggr_weekday(df, method='count')


@app.callback(
    dash.dependencies.Output('plot-aggreg-hour-avg', 'figure'),
    [dash.dependencies.Input('weekdays_checkbox', 'values'),
     dash.dependencies.Input('hour-filter', 'value'),
     dash.dependencies.Input('date-picker-range', 'start_date'),
     dash.dependencies.Input('date-picker-range', 'end_date'),
     dash.dependencies.Input('park-dropdown', 'value'),
     dash.dependencies.Input('camera-dropdown', 'value')])
def update_aggr_hour_avg(weekdays, hour, start_date, end_date, park, camera):
    df = csvdata[(csvdata['park'] == park) & (csvdata['camera'] == camera)]
    highlight_intervals(df)
    df = df.loc[start_date:end_date]
    df = df[df['weekday'].isin(weekdays)]
    df = df[(df['hour'] >= hour[0]) & (df['hour'] < hour[1])]
    df = df.resample('1h').sum()
    df = df[df['year'] != 0]  # filter no data values, count is always 0, no NaN
    df = df.groupby(df.index.hour)['count'].mean().reset_index()
    df['hour'] = df['isodate']
    df = df[df['count'].notnull()]
    return create_aggr_hour(df, method='avg')


# all filter callback to redraw overview figure
@app.callback(
    dash.dependencies.Output('plot-aggreg-day-avg', 'figure'),
    [dash.dependencies.Input('weekdays_checkbox', 'values'),
     dash.dependencies.Input('hour-filter', 'value'),
     dash.dependencies.Input('date-picker-range', 'start_date'),
     dash.dependencies.Input('date-picker-range', 'end_date'),
     dash.dependencies.Input('park-dropdown', 'value'),
     dash.dependencies.Input('camera-dropdown', 'value')])
def update_aggr_weekday_avg(weekdays, hour, start_date, end_date, park, camera):
    df = csvdata[(csvdata['park'] == park) & (csvdata['camera'] == camera)]
    df = df.loc[start_date:end_date]
    df = df[df['weekday'].isin(weekdays)]
    df = df[(df['hour'] >= hour[0]) & (df['hour'] < hour[1])]
    df = df.resample('1d').sum()
    df = df[df['year'] != 0]  # filter no data values, count is always 0, no NaN
    df = df.groupby(df.index.dayofweek)['count'].mean().reset_index()
    df['weekday'] = df['isodate'] + 1
    return create_aggr_weekday(df, method='avg')



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

    dff = df.loc[start_date:end_date]
    dff = dff[dff['weekday'].isin(weekdays)]
    dff = dff[(dff['hour'] >= hour[0]) & (dff['hour'] < hour[1])]
    dff = dff.groupby(pd.Grouper(key='isodate', freq='D')).sum().reset_index()
    dff = dff[dff['year'] != 0]  # filter no data values, count is always 0, no NaN

    # separately compute 'no image' time gaps, without filtering
    df = df.groupby(pd.Grouper(key='isodate', freq='D')).sum().reset_index()
    shapes, annotations = highlight_intervals(df[df['year'] == 0])

    return create_time_series(dff, shapes, annotations)


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
    return os.path.join(static_image_route, 'default_image.JPG')


@app.server.route('{}<image_path>.JPG'.format(static_image_route))
def serve_image(image_path):
    image_name = '{}.JPG'.format(image_path)
    if image_name not in cameras:
        raise Exception('"{}" is excluded from the allowed static files'.format(image_path))
    return flask.send_from_directory(cameras_dir, image_name)


if __name__ == '__main__':
    app.run_server(debug=True)
