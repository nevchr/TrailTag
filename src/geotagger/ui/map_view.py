import html
import json

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

from ..gpx_parser import TrackPoint
from ..image_preview import create_photo_preview_data_uri
from ..preview import PreviewResult
from .theme import map_stylesheet


class PhotoBridge(QObject):
    photo_selected = Signal(int)

    @Slot(int)
    def selectPhoto(self, photo_index: int) -> None:
        self.photo_selected.emit(photo_index)


class MapView(QWebEngineView):
    photo_selected = Signal(int)

    def __init__(self):
        super().__init__()

        self.preview_results: list[PreviewResult] = []
        self.popup_cache: dict[int, str] = {}
        self.pending_photo_index: int | None = None
        self.page_ready = False
        self.theme_mode = QApplication.instance().property("trailtagTheme") or "light"

        # A channel sends clicks without navigating away from the map. Rejected
        # custom-URL navigations can emit loadFinished(False) and disable previews.
        self.photo_bridge = PhotoBridge(self)
        self.photo_bridge.photo_selected.connect(self._map_photo_selected)
        self.web_channel = QWebChannel(self.page())
        self.web_channel.registerObject("photos", self.photo_bridge)
        self.page().setWebChannel(self.web_channel)
        self.loadFinished.connect(self._map_loaded)
        self.show_empty_map()

    def set_theme(self, mode: str) -> None:
        self.theme_mode = mode
        self._apply_map_theme()

    def _set_themed_html(self, page: str) -> None:
        style = f'<style id="trailtag-theme">{map_stylesheet(self.theme_mode)}</style>'
        self.setHtml(page.replace("</head>", style + "</head>"))

    def _apply_map_theme(self) -> None:
        css = json.dumps(map_stylesheet(self.theme_mode))
        self.page().runJavaScript(f"""
            (() => {{
                if (!document.head) return;
                let style = document.getElementById('trailtag-theme');
                if (!style) {{
                    style = document.createElement('style');
                    style.id = 'trailtag-theme';
                    document.head.appendChild(style);
                }}
                style.textContent = {css};
            }})();
        """)

    def show_empty_map(self, message: str = "Preview photos to display the map."):
        self.preview_results = []
        self.popup_cache = {}
        self.pending_photo_index = None
        self.page_ready = False
        escaped_message = html.escape(message)
        page = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    html, body {
                        width: 100%;
                        height: 100%;
                        margin: 0;
                        background: #f7faf8;
                        color: #687970;
                        font-family: Arial, sans-serif;
                    }

                    .empty {
                        width: 100%;
                        height: 100%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 15px;
                    }
                </style>
            </head>

            <body>
                <div class="empty">
                    __EMPTY_MESSAGE__
                </div>
            </body>
            </html>
            """
        self._set_themed_html(page.replace("__EMPTY_MESSAGE__", escaped_message))

    def set_results(
        self,
        track_points: list[TrackPoint],
        preview_results: list[PreviewResult],
    ):
        if not track_points:
            self.show_empty_map()
            return

        self.preview_results = list(preview_results)
        self.popup_cache = {}
        self.pending_photo_index = None
        self.page_ready = False

        route = [
            [point.latitude, point.longitude]
            for point in track_points
        ]

        markers = []
        for index, result in enumerate(preview_results):
            if (
                not result.matched
                or result.latitude is None
                or result.longitude is None
            ):
                continue

            markers.append(
                {
                    "id": index,
                    "lat": result.latitude,
                    "lon": result.longitude,
                    "popup": self._popup_html(result, loading=True),
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
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <style>
                html, body {{
                    height: 100%;
                    width: 100%;
                    margin: 0;
                    padding: 0;
                    color-scheme: light;
                    background: #f7faf8;
                    color: #18352b;
                }}

                #map {{
                    height: 100%;
                    width: 100%;
                }}

                #map-status {{
                    position: absolute;
                    top: 14px;
                    left: 60px;
                    right: 14px;
                    z-index: 1000;
                    padding: 12px;
                    border-radius: 8px;
                    background: #fff3d6;
                    color: #805500;
                    font: 14px Arial, sans-serif;
                }}

                .leaflet-popup-content {{
                    color: #18352b;
                    font-family: Arial, sans-serif;
                    width: 300px !important;
                    margin: 14px;
                }}

                .photo-preview {{
                    display: block;
                    width: 100%;
                    max-height: 220px;
                    margin-bottom: 10px;
                    border-radius: 6px;
                    object-fit: contain;
                    background: #eeeeee;
                }}

                .photo-name {{
                    display: block;
                    margin-bottom: 8px;
                    overflow-wrap: anywhere;
                }}

                .photo-details {{
                    line-height: 1.45;
                }}

                .preview-unavailable, .preview-loading {{
                    display: flex;
                    min-height: 90px;
                    margin-bottom: 10px;
                    align-items: center;
                    justify-content: center;
                    border-radius: 6px;
                    background: #eeeeee;
                    color: #666666;
                }}
            </style>
        </head>

        <body>
            <div id="map"></div>
            <div id="map-status" role="status">Loading map…</div>

            <script>
                const mapStatus = document.getElementById("map-status");
                if (!window.L) {{
                    mapStatus.textContent = "The map could not load. Check your internet connection, then reopen this trip or preview again. Your saved trip details are still available.";
                }} else {{
                mapStatus.hidden = true;
                const route = {route_json};
                const markers = {markers_json};
                const map = L.map("map");
                const photoMarkers = {{}};
                const previewTimers = {{}};
                let photoBridge = null;
                let queuedPhoto = null;
                function requestPhoto(photoId) {{
                    queuedPhoto = photoId;
                    clearTimeout(previewTimers[photoId]);
                    previewTimers[photoId] = setTimeout(() => {{
                        const popup = photoMarkers[photoId]?.getPopup();
                        const content = popup?.getContent();
                        if (typeof content === "string" && content.includes("preview-loading")) {{
                            photoMarkers[photoId].setPopupContent(content.replace(
                                "Loading photo preview…",
                                "Preview could not load. Click the photo again to retry."
                            ));
                        }}
                    }}, 8000);
                    if (photoBridge) {{
                        queuedPhoto = null;
                        photoBridge.selectPhoto(photoId);
                    }}
                }}
                if (window.qt?.webChannelTransport && window.QWebChannel) {{
                    new QWebChannel(qt.webChannelTransport, channel => {{
                        photoBridge = channel.objects.photos;
                        if (queuedPhoto !== null) requestPhoto(queuedPhoto);
                    }});
                }}

                L.tileLayer(
                    "https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
                    {{
                        maxZoom: 19,
                        attribution: "&copy; OpenStreetMap contributors"
                    }}
                ).on("tileerror", () => {{
                    mapStatus.textContent = "Map tiles are unavailable. Your route and photo locations are still shown.";
                    mapStatus.hidden = false;
                }}).on("tileload", () => {{
                    mapStatus.hidden = true;
                }}).addTo(map);

                const routeLine = L.polyline(
                    route,
                    {{
                        color: "#21825f",
                        weight: 4,
                        opacity: 0.85
                    }}
                ).addTo(map);

                markers.forEach(markerData => {{
                    const marker = L.marker(
                        [markerData.lat, markerData.lon]
                    )
                    .addTo(map)
                    .bindPopup(
                        markerData.popup,
                        {{ minWidth: 300, maxWidth: 340 }}
                    );

                    marker.on("click", () => {{
                        requestPhoto(markerData.id);
                    }});
                    photoMarkers[markerData.id] = marker;
                }});

                window.setPhotoPopup = (photoId, popup) => {{
                    const marker = photoMarkers[photoId];
                    if (!marker) return;
                    clearTimeout(previewTimers[photoId]);
                    marker.setPopupContent(popup);
                    marker.openPopup();
                }};

                window.focusPhoto = photoId => {{
                    const marker = photoMarkers[photoId];
                    if (!marker) return;
                    map.setView(
                        marker.getLatLng(),
                        Math.max(map.getZoom(), 15),
                        {{ animate: true }}
                    );
                    marker.openPopup();
                }};

                if (route.length > 0) {{
                    map.fitBounds(
                        routeLine.getBounds(),
                        {{ padding: [25, 25] }}
                    );
                }}
                }}
            </script>
        </body>
        </html>
        """

        self._set_themed_html(page)

    def focus_photo(self, photo_index: int) -> None:
        if not 0 <= photo_index < len(self.preview_results):
            return
        self.pending_photo_index = photo_index
        if self.page_ready:
            self._apply_photo_popup(photo_index)
            self.page().runJavaScript(f"window.focusPhoto?.({photo_index});")
            self.pending_photo_index = None

    def _map_loaded(self, successful: bool) -> None:
        self.page_ready = successful
        if successful:
            self._apply_map_theme()
        if successful and self.pending_photo_index is not None:
            photo_index = self.pending_photo_index
            self._apply_photo_popup(photo_index)
            self.page().runJavaScript(f"window.focusPhoto?.({photo_index});")
            self.pending_photo_index = None

    def _map_photo_selected(self, photo_index: int) -> None:
        if not 0 <= photo_index < len(self.preview_results):
            return
        if self.page_ready:
            self._apply_photo_popup(photo_index)
        else:
            self.pending_photo_index = photo_index
        self.photo_selected.emit(photo_index)

    def _apply_photo_popup(self, photo_index: int) -> None:
        if not self.page_ready:
            return

        popup = self.popup_cache.get(photo_index)
        if popup is None:
            result = self.preview_results[photo_index]
            preview_data_uri = create_photo_preview_data_uri(result.source_path)
            popup = self._popup_html(
                result,
                preview_data_uri=preview_data_uri,
            )
            self.popup_cache[photo_index] = popup

        self.page().runJavaScript(
            f"window.setPhotoPopup?.({photo_index}, {json.dumps(popup)});"
        )

    @staticmethod
    def _popup_html(
        result: PreviewResult,
        *,
        preview_data_uri: str | None = None,
        loading: bool = False,
    ) -> str:
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
        latitude = (
            f"{result.latitude:.6f}"
            if result.latitude is not None
            else "Unknown"
        )
        longitude = (
            f"{result.longitude:.6f}"
            if result.longitude is not None
            else "Unknown"
        )
        escaped_name = html.escape(result.source_path.name)

        if loading:
            image_preview = (
                '<div class="preview-loading">Loading photo preview…</div>'
            )
        elif preview_data_uri is not None:
            image_preview = (
                '<img class="photo-preview" '
                f'src="{preview_data_uri}" '
                f'alt="Preview of {escaped_name}">'
            )
        else:
            image_preview = (
                '<div class="preview-unavailable">'
                "Photo preview unavailable"
                "</div>"
            )

        return (
            '<div class="photo-popup">'
            f"{image_preview}"
            f'<strong class="photo-name">{escaped_name}</strong>'
            '<div class="photo-details">'
            f"Time: {photo_time}<br>"
            f"Latitude: {latitude}<br>"
            f"Longitude: {longitude}<br>"
            f"Elevation: {elevation}"
            "</div>"
            "</div>"
        )
