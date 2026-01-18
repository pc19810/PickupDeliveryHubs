import pandas as pd
import numpy as np
import logging
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from .config import Config

class HubVisualizer:
    """Create interactive visualization of logistics hub network."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.app = None
        self.pickup_df = None
        self.delivery_df = None
        self.state_centroid_df = None
        self.combined = None
        self.colorscale = {
            'Pickup': [(0, '#e6f7ff'), (0.5, '#69c0ff'), (1, '#0050b3')],
            'Delivery': [(0, '#fff2e8'), (0.5, '#ff9c6e'), (1, '#d4380d')]
        }
    
    def load_data(self):
        """Load all required data files."""
        self.logger.info("Loading visualization data...")
        
        # Load hub coverage data
        pickup_file = self.config.PROCESSED_DATA_DIR / self.config.PICKUP_HUB_COVERAGE_FILE
        delivery_file = self.config.PROCESSED_DATA_DIR / self.config.DELIVERY_HUB_COVERAGE_FILE
        
        if not pickup_file.exists() or not delivery_file.exists():
            raise FileNotFoundError(
                "Hub coverage files not found. Run hub creation first."
            )
        
        self.pickup_df = pd.read_csv(pickup_file)
        self.delivery_df = pd.read_csv(delivery_file)
        
        # Load state centroids
        state_file = self.config.REFERENCE_DATA_DIR / self.config.US_STATES_FILE
        if state_file.exists():
            self.state_centroid_df = pd.read_csv(state_file)
            self.state_centroid_df.columns = self.state_centroid_df.columns.str.strip().str.lower()
            self.state_centroid_df = self.state_centroid_df[['state', 'latitude', 'longitude']]
        else:
            self.logger.warning(f"State centroids file not found: {state_file}")
            self.state_centroid_df = pd.DataFrame(columns=['state', 'latitude', 'longitude'])
        
        self.logger.info("Data loaded successfully")
    
    def prepare_summary_data(self):
        """Prepare summary data for hub visualization."""
        
        def prepare_summary(df, count_col, hub_label):
            summary = df.groupby(['hub_state', 'hub_city']).agg({
                count_col: 'sum',
                'city': 'count',
                'latitude': 'first',
                'longitude': 'first'
            }).reset_index().rename(columns={'city': 'city_count'})
            
            city_lists = df.groupby(['hub_state', 'hub_city'])['city'].apply(
                lambda x: sorted(set(x))
            ).reset_index()
            
            summary = summary.merge(city_lists, on=['hub_state', 'hub_city'])
            summary['type'] = hub_label
            summary.rename(
                columns={count_col: 'total_count', 'latitude': 'lat', 'longitude': 'lon'}, 
                inplace=True
            )
            
            return summary
        
        pickup_summary = prepare_summary(self.pickup_df, 'pickup_count', 'Pickup')
        delivery_summary = prepare_summary(self.delivery_df, 'delivery_count', 'Delivery')
        
        self.combined = pd.concat([pickup_summary, delivery_summary], ignore_index=True)
        self.combined['size_scaled'] = (
            (np.log1p(self.combined['total_count']) ** 1.5) /
            (np.log1p(self.combined['total_count'].max()) ** 1.5) * 50
        )
    
    def create_app(self):
        """Create and configure the Dash application."""
        self.app = dash.Dash(__name__, suppress_callback_exceptions=True)
        self.app.title = "Logistics Hub Network"
        
        self.app.layout = self._create_layout()
        self.app.index_string = self._get_custom_css()
        self._register_callbacks()
    
    def _create_layout(self):
        """Create the app layout."""
        return html.Div([
            # Header
            html.Div([
                html.H1("Logistics Hub Network", className="header-title"),
                html.P(
                    "Pickup and delivery hubs across the United States", 
                    className="header-description"
                )
            ], className="header"),
            
            # Main content
            html.Div([
                # Control panel
                html.Div([
                    html.H3("Controls", className="control-title"),
                    
                    html.Div([
                        html.Label("Display Mode:"),
                        dcc.RadioItems(
                            id='display-mode',
                            options=[
                                {'label': 'Hubs', 'value': 'hubs'},
                                {'label': 'Cities', 'value': 'cities'},
                                {'label': 'Auto', 'value': 'auto'}
                            ],
                            value='auto',
                            className="radio-group"
                        )
                    ], className="control-group"),
                    
                    html.Div([
                        html.Label("Show:"),
                        dcc.Checklist(
                            id='hub-type-filter',
                            options=[
                                {'label': 'Pickup Hubs', 'value': 'pickup'},
                                {'label': 'Delivery Hubs', 'value': 'delivery'}
                            ],
                            value=['pickup', 'delivery'],
                            className="checkbox-group"
                        )
                    ], className="control-group"),
                    
                    html.Div(id="hub-details", className="hub-details")
                ], className="control-panel"),
                
                # Map
                html.Div([
                    dcc.Graph(
                        id='hub-map',
                        config={
                            'displayModeBar': True,
                            'scrollZoom': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['select2d', 'lasso2d']
                        },
                        style={'height': 'calc(100vh - 80px)'}
                    )
                ], className="map-container")
            ], className="main-content"),
            
            # Hidden state divs
            html.Div(id='current-zoom-level', style={'display': 'none'}, children='1'),
            html.Div(id='map-center-lat', style={'display': 'none'}, children='37.0902'),
            html.Div(id='map-center-lon', style={'display': 'none'}, children='-95.7129'),
            html.Div(id='selected-hub-info', style={'display': 'none'})
        ], className="app-container")
    
    def _get_custom_css(self):
        """Return custom CSS for the app."""
        return '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Roboto', sans-serif;
            }
            
            body {
                background-color: #f8f9fa;
                color: #343a40;
            }
            
            .app-container {
                display: flex;
                flex-direction: column;
                width: 100%;
                min-height: 100vh;
            }
            
            .header {
                background: linear-gradient(135deg, #2c3e50, #4ca1af);
                color: white;
                padding: 20px 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .header-title {
                font-weight: 500;
                font-size: 28px;
                margin-bottom: 8px;
            }
            
            .header-description {
                font-weight: 300;
                opacity: 0.9;
            }
            
            .main-content {
                display: flex;
                flex: 1;
                position: relative;
            }
            
            .control-panel {
                width: 280px;
                background: white;
                padding: 20px;
                border-right: 1px solid #e9ecef;
                box-shadow: 2px 0 10px rgba(0,0,0,0.05);
                z-index: 10;
                display: flex;
                flex-direction: column;
            }
            
            .control-title {
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 1px solid #e9ecef;
                font-weight: 500;
                font-size: 18px;
            }
            
            .control-group {
                margin-bottom: 25px;
            }
            
            .control-group label {
                display: block;
                margin-bottom: 10px;
                font-weight: 500;
                color: #495057;
            }
            
            .radio-group, .checkbox-group {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            .map-container {
                flex: 1;
                height: calc(100vh - 80px);
                position: relative;
            }
            
            .hub-details {
                margin-top: auto;
                padding-top: 20px;
                border-top: 1px solid #e9ecef;
            }
            
            .hub-details h4 {
                font-size: 16px;
                margin-bottom: 10px;
                font-weight: 500;
            }
            
            .hub-details ul {
                list-style-type: none;
                max-height: 200px;
                overflow-y: auto;
                margin-left: 0;
                padding-left: 0;
            }
            
            .hub-details li {
                padding: 4px 0;
                border-bottom: 1px dashed #e9ecef;
            }
        </style>
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
    
    def _register_callbacks(self):
        """Register all Dash callbacks."""
        
        @self.app.callback(
            Output('hub-map', 'figure'),
            [Input('display-mode', 'value'),
             Input('hub-type-filter', 'value'),
             Input('current-zoom-level', 'children'),
             Input('map-center-lat', 'children'),
             Input('map-center-lon', 'children')]
        )
        def update_map(display_mode, hub_types, zoom_level, center_lat, center_lon):
            return self._create_map_figure(
                display_mode, hub_types, 
                float(zoom_level), float(center_lat), float(center_lon)
            )
        
        @self.app.callback(
            [Output('current-zoom-level', 'children'),
             Output('map-center-lat', 'children'),
             Output('map-center-lon', 'children')],
            [Input('hub-map', 'relayoutData')],
            [State('current-zoom-level', 'children'),
             State('map-center-lat', 'children'),
             State('map-center-lon', 'children')]
        )
        def store_map_state(relayout_data, current_zoom, current_lat, current_lon):
            if not relayout_data:
                return current_zoom, current_lat, current_lon
            
            zoom_level = float(current_zoom)
            center_lat = float(current_lat)
            center_lon = float(current_lon)
            
            if 'geo.projection.scale' in relayout_data:
                zoom_level = relayout_data['geo.projection.scale']
            
            if 'geo.center.lat' in relayout_data:
                center_lat = relayout_data['geo.center.lat']
            
            if 'geo.center.lon' in relayout_data:
                center_lon = relayout_data['geo.center.lon']
            
            return str(zoom_level), str(center_lat), str(center_lon)
        
        @self.app.callback(
            Output('hub-details', 'children'),
            [Input('hub-map', 'clickData')],
            [State('display-mode', 'value')]
        )
        def display_hub_details(click_data, display_mode):
            return self._create_hub_details(click_data, display_mode)
    
    def _create_map_figure(self, display_mode, hub_types, zoom_level, center_lat, center_lon):
        """Create the map figure based on current settings."""
        ZOOM_THRESHOLD = 4
        show_cities = (display_mode == 'cities' or 
                      (display_mode == 'auto' and zoom_level > ZOOM_THRESHOLD))
        
        traces = []
        
        # Add hub or city traces based on selection
        if not show_cities:
            if 'pickup' in hub_types:
                traces.append(self._create_hub_trace(self.combined, 'Pickup'))
            if 'delivery' in hub_types:
                traces.append(self._create_hub_trace(self.combined, 'Delivery'))
        else:
            if 'pickup' in hub_types:
                traces.append(self._create_city_trace(self.pickup_df, 'pickup_count', 'Pickup'))
            if 'delivery' in hub_types:
                traces.append(self._create_city_trace(self.delivery_df, 'delivery_count', 'Delivery'))
        
        # Add state labels
        if len(self.state_centroid_df) > 0:
            traces.append(go.Scattergeo(
                lon=self.state_centroid_df['longitude'],
                lat=self.state_centroid_df['latitude'],
                text=self.state_centroid_df['state'],
                mode='text',
                textfont=dict(color='rgba(50,50,50,0.7)', size=10),
                hoverinfo='skip',
                showlegend=False
            ))
        
        fig = go.Figure(data=traces)
        
        title = f"Logistics Network: {'City' if show_cities else 'Hub'}-Level View"
        if hub_types:
            title += f" ({' & '.join([t.capitalize() for t in hub_types])})"
        
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=20, color="#333"),
                x=0.02,
                y=0.97,
                xanchor='left',
                yanchor='top'
            ),
            geo=dict(
                scope='usa',
                projection=dict(type='albers usa', scale=zoom_level),
                center=dict(lat=center_lat, lon=center_lon),
                showland=True,
                landcolor='rgb(250, 250, 250)',
                showocean=True,
                oceancolor='rgb(230, 245, 255)',
                showlakes=True,
                lakecolor='rgb(220, 240, 255)',
                countrycolor='rgb(204, 204, 204)',
                subunitcolor='rgb(230, 230, 230)',
            ),
            height=800,
            margin=dict(l=0, r=0, t=50, b=0),
            legend=dict(
                x=0.02,
                y=0.02,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='rgba(0, 0, 0, 0.1)',
                borderwidth=1,
                orientation='h'
            ),
            dragmode='zoom',
        )
        
        return fig
    
    def _create_hub_trace(self, data, hub_type):
        """Create a trace for hubs."""
        subset = data[data['type'] == hub_type]
        
        return go.Scattergeo(
            lon=subset['lon'],
            lat=subset['lat'],
            text=subset.apply(
                lambda r: f"{hub_type} Hub: {r['hub_city']}, {r['hub_state']}<br>"
                         f"Total: {int(r['total_count'])}<br>"
                         f"Cities: {r['city_count']}", 
                axis=1
            ),
            customdata=subset[['hub_city', 'hub_state', 'total_count', 'city_count']].to_dict('records'),
            marker=dict(
                size=subset['size_scaled'],
                color=subset['city_count'],
                colorscale=self.colorscale[hub_type],
                opacity=0.85,
                line=dict(width=1, color='white'),
                colorbar=dict(
                    title=f"{hub_type}<br>Cities",
                    x=0.90 if hub_type == 'Pickup' else 0.98,
                    thickness=15,
                    len=0.6
                )
            ),
            mode='markers',
            name=f'{hub_type} Hubs',
            hovertemplate='%{text}',
        )
    
    def _create_city_trace(self, data, count_col, label):
        """Create a trace for cities."""
        return go.Scattergeo(
            lon=data['longitude'],
            lat=data['latitude'],
            text=data.apply(
                lambda r: f"{r['city']}, {r['state']}<br>{label} Count: {r[count_col]}", 
                axis=1
            ),
            marker=dict(
                size=np.log1p(data[count_col]) * 2 + 3,
                color=self.colorscale[label][1][1],
                opacity=0.7,
                line=dict(width=0.5, color='white')
            ),
            mode='markers',
            name=f'{label} Cities',
            hovertemplate='%{text}',
        )
    
    def _create_hub_details(self, click_data, display_mode):
        """Create hub details panel content."""
        if not click_data or not click_data.get('points', []):
            return html.Div([
                html.H4("Hub Information"),
                html.P("Click on a hub to see details about its coverage.")
            ])
        
        if display_mode == 'cities':
            return html.Div([
                html.H4("City Information"),
                html.P(click_data['points'][0].get('text', 'No information available'))
            ])
        
        point = click_data['points'][0]
        customdata = point.get('customdata')
        
        if not customdata:
            return html.Div([
                html.H4("No Data Available"),
                html.P("The selected point doesn't have associated data.")
            ])
        
        hub_city = customdata.get('hub_city', 'Unknown')
        hub_state = customdata.get('hub_state', 'Unknown')
        total_count = customdata.get('total_count', 0)
        city_count = customdata.get('city_count', 0)
        hub_type = 'Pickup' if point['curveNumber'] == 0 else 'Delivery'
        
        df = self.pickup_df if hub_type == 'Pickup' else self.delivery_df
        cities_df = df[(df['hub_city'] == hub_city) & (df['hub_state'] == hub_state)]
        cities_list = sorted(cities_df['city'].unique())
        
        return html.Div([
            html.H4(f"{hub_type} Hub: {hub_city}, {hub_state}"),
            html.P([html.Strong("Total Volume: "), f"{int(total_count):,}"]),
            html.P([html.Strong("Cities Served: "), f"{city_count}"]),
            html.H4("Cities Served:"),
            html.Ul([html.Li(city) for city in cities_list])
        ])
    
    def run(self):
        """Run the Dash application."""
        self.logger.info(
            f"Starting visualization server at http://{self.config.DASH_HOST}:{self.config.DASH_PORT}"
        )
        self.app.run(
            debug=self.config.DASH_DEBUG,
            host=self.config.DASH_HOST,
            port=self.config.DASH_PORT
        )
