import datetime as dt
import logging
import geojson
from simplejson.errors import JSONDecodeError
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseNotAllowed
from tethys_sdk.permissions import login_required
from tethys_sdk.gizmos import SelectInput, DatePicker, Button, MapView, MVView, PlotlyView, MVDraw, MVLayer
from .helpers import generate_figure



log = logging.getLogger(f'tethys.apps.{__name__}')



def home(request):
    """
    Controller for the app home page.
    """


    # Build year select control
    year_select = SelectInput(
        name='year',
        display_text='Year',
        options=(
            ('2022', '2022'),

        )
    )

    # Build month select control
    month_select = SelectInput(
        name='month',
        display_text='Month',
        options=(
            ('Jan', '01'),
            ('Feb', '02'),
            ('Mar', '03'),
            ('Apr', '04'),
            ('May', '05'),
            ('Jun', '06'),
            ('Jul', '07'),
            ('Aug', '08'),
            ('Sep', '09'),
            ('Oct', '10'),
            ('Nov', '11'),
            ('Dec', '12'),

        )
    )

    dekad_select = SelectInput(
        name='dekad',
        display_text='Dekad',
        options=(
            ('Dekad 1', '01'),
            ('Dekad 2', '11'),
            ('Dekad 3', '21'),

        )
    )

    # Build Buttons
    load_button = Button(
        name='load_map',
        display_text='Load',
        style='default',
        attributes={'id': 'load_map'}
    )

    map_layers = []

    cdi_layer = MVLayer(
        source='ImageWMS',
        options={
            'url': 'https://droughtwatch.icpac.net/mapserver/mukau/php/gis/mswms.php',
            'params': {'LAYERS': 'cdi_chirps',
                       'MAP': 'mukau',
                       'VERSION': '1.1.1',
                       'SELECTED_YEAR': '2022',
                       'SELECTED_MONTH': '01',
                       'SELECTED_TENDAYS': '01',
                       },
            'serverType': 'mapserver',
        },
        legend_title='Combined Drought Indicator',
    )

    map_layers.append(cdi_layer)

    map_view = MapView(
        height='100%',
        width='100%',
        controls=[
            'ZoomSlider', 'Rotate', 'FullScreen',
            {'ZoomToExtent': {
                'projection': 'EPSG:4326',
                'extent': [29.25, -4.75, 46.25, 5.2]
            }}
        ],
        basemap=[
            'CartoDB',
            {'CartoDB': {'style': 'dark'}},
            'OpenStreetMap',
            'Stamen',
            'ESRI'
        ],
        layers=map_layers,
        view=MVView(
            projection='EPSG:4326',
            center=[37.880859, 0.219726],
            zoom=4,
            maxZoom=18,
            minZoom=2
        ),
        draw=MVDraw(
            controls=['Pan', 'Modify', 'Delete', 'Move', 'Point', 'Polygon', 'Box'],
            initial='Pan',
            output_format='GeoJSON'
        )
    )

    clear_button = Button(
        name='clear_map',
        display_text='Clear',
        style='default',
        attributes={'id': 'clear_map'}
    )

    plot_button = Button(
        name='load_plot',
        display_text='Plot',
        style='default',
        attributes={'id': 'load_plot'}
    )

    context = {

        'year_select': year_select,
        'month_select': month_select,
        'dekad_select': dekad_select,
        'load_button': load_button,
        'clear_button': clear_button,
        'plot_button': plot_button,
        'ee_products': EE_PRODUCTS,
        'map_view': map_view
    }

    return render(request, 'drought_watch/home.html', context)


def get_image_collection(request):
    """
    Controller to handle image collection requests.
    """
    response_data = {'success': False}

    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        log.debug(f'POST: {request.POST}')

        platform = request.POST.get('platform', None)
        #sensor = request.POST.get('sensor', None)
        product = request.POST.get('product', None)
        start_date = request.POST.get('start_date', None)
        end_date = request.POST.get('end_date', None)
        reducer = request.POST.get('reducer', None)

        url = get_image_collection_asset(
            platform=platform,
            #sensor=sensor,
            product=product,
            date_from=start_date,
            date_to=end_date,
            reducer=reducer
        )

        log.debug(f'Image Collection URL: {url}')

        response_data.update({
            'success': True,
            'url': url
        })

    except Exception as e:
        response_data['error'] = f'Error Processing Request: {e}'

    return JsonResponse(response_data)


def get_time_series_plot(request):
    context = {'success': False}

    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        log.debug(f'POST: {request.POST}')

        platform = request.POST.get('platform', None)
        product = request.POST.get('product', None)
        start_date = request.POST.get('start_date', None)
        end_date = request.POST.get('end_date', None)
        reducer = request.POST.get('reducer', None)
        index_name = request.POST.get('index_name', None)
        scale = float(request.POST.get('scale', 250))
        geometry_str = request.POST.get('geometry', None)

        # Derived parameters
        ee_product = EE_PRODUCTS[platform][product]
        display_name = ee_product['display']

        if not index_name:
            index_name = ee_product['index']

        try:
            geometry = geojson.loads(geometry_str)
        except JSONDecodeError:
            raise ValueError('Please draw an area of interest.')

        if index_name is None:
            raise ValueError(f"We're sorry, but plotting {display_name} is not supported at this time. Please select "
                             f"a different product.")

        time_series = get_time_series_from_image_collection(
            platform=platform,
            product=product,
            index_name=index_name,
            scale=scale,
            geometry=geometry,
            date_from=start_date,
            date_to=end_date,
            reducer=reducer
        )

        log.debug(f'Time Series: {time_series}')

        figure = generate_figure(
            figure_title=display_name,
            time_series=time_series
        )

        plot_view = PlotlyView(figure, height='200px', width='100%')

        context.update({
            'success': True,
            'plot_view': plot_view
        })

    except ValueError as e:
        context['error'] = str(e)

    except Exception:
        context['error'] = f'An unexpected error has occurred. Please try again.'
        log.exception('An unexpected error occurred.')

    return render(request, 'drought_watch/plot.html', context)
