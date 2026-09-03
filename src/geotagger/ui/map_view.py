import html
import json

from PySide6.QtWebEngineWidgets import QWebEngineView

from ..gpx_parser import TrackPoint
from ..preview import PreviewResult


class MapView(QWebEngineView):
    def __init__(self):
        super().__init__()

        self.show_empty_map()

    def show_empty_map(self):
        self.setHtml(
            """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    html, body {
                        width: 100%;
                        height: 100%;
                        margin: 0;
                        background: #1e1e1e;
                        color: #dddddd;
                        font-family: Arial, sans-serif;
                    }

                    .empty {
                        width: 100%;
                        height: 100%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 16px;
                    }
                </style>
            </head>

            <body>
                <div class="empty">
                    Preview photos to display the map.
                </div>
            </body>
            </html>
            """
        )

    def set_results(
        self,
        track_points: list[TrackPoint],
        preview_results: list[PreviewResult],
    ):
        if not track_points:
            self.show_empty_map()
            return

        route = [
            [point.latitude, point.longitude]
            for point in track_points
        ]

        markers = []

        for result in preview_results:
            if (
                not result.matched
                or result.latitude is None
                or result.longitude is None
            ):
                continue

            photo_time = (
                result.photo_time.strftime("%H:%M:%S")
                if result.photo_time
                else "Unknown"
            )

            elevation = (
                f"{result.elevation:.1f} m"
                if result.elevation is not None
                else "Unknown"
            )

            popup = (
                f"<strong>{html.escape(result.source_path.name)}</strong>"
                f"<br><br>"
                f"Time: {photo_time}"
                f"<br>"
                f"Latitude: {result.latitude:.6f}"
                f"<br>"
                f"Longitude: {result.longitude:.6f}"
                f"<br>"
                f"Elevation: {elevation}"
            )

            markers.append(
                {
                    "lat": result.latitude,
                    "lon": result.longitude,
                    "popup": popup,
                }
            )

        route_json = json.dumps(route)
        markers_json = json.dumps(markers)

        page = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">

            <meta
                name="viewport"
                content="width=device-width, initial-scale=1.0"
            >

            <link
                rel="stylesheet"
                href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
            />

            <script
                src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
            </script>

            <style>
                html, body {{
                    height: 100%;
                    width: 100%;
                    margin: 0;
                    padding: 0;
                }}

                #map {{
                    height: 100%;
                    width: 100%;
                }}

                .leaflet-popup-content {{
                    font-family: Arial, sans-serif;
                    min-width: 220px;
                }}
            </style>
        </head>

        <body>
            <div id="map"></div>

            <script>
                const route = {route_json};
                const markers = {markers_json};

                const map = L.map("map");

                L.tileLayer(
                    "https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
                    {{
                        maxZoom: 19,
                        attribution:
                            "&copy; OpenStreetMap contributors"
                    }}
                ).addTo(map);

                const routeLine = L.polyline(
                    route,
                    {{
                        weight: 4,
                        opacity: 0.8
                    }}
                ).addTo(map);

                markers.forEach(marker => {{
                    L.marker(
                        [marker.lat, marker.lon]
                    )
                    .addTo(map)
                    .bindPopup(marker.popup);
                }});

                if (route.length > 0) {{
                    map.fitBounds(
                        routeLine.getBounds(),
                        {{
                            padding: [25, 25]
                        }}
                    );
                }}
            </script>
        </body>
        </html>
        """

        self.setHtml(page)