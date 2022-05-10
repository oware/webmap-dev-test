from tethys_sdk.base import TethysAppBase, url_map_maker


class DroughtWatch(TethysAppBase):
    """
    Tethys app class for East Africa Drought Watch.
    """

    name = 'East Africa Drought Watch'
    index = 'drought_watch:home'
    icon = 'drought_watch/images/icon.gif'
    package = 'drought_watch'
    root_url = 'drought-watch'
    color = '#16a085'
    description = 'East Africa Drought Watch'
    tags = ''
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='home',
                url='drought-watch',
                controller='drought_watch.controllers.home'
            ),
            UrlMap(
                name='get_image_collection',
                url='drought-watch/get-image-collection',
                controller='drought_watch.controllers.get_image_collection'
            ),
            UrlMap(
                name='get_time_series_plot',
                url='drought-watch/get-time-series-plot',
                controller='drought_watch.controllers.get_time_series_plot'
            ),
        )

        return url_maps