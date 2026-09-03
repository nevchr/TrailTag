# GPX Photo Geotagger

A desktop application that automatically adds GPS coordinates to photos by matching their EXIF capture timestamps against a GPX track.

## Current Features

- Load timestamped GPX tracks
- Load folders of JPEG photos
- Read EXIF `DateTimeOriginal`
- Convert camera timestamps between time zones
- Adjustable camera time offset
- Interpolate photo locations between surrounding GPX points
- Maximum GPX-gap safety threshold
- Preview all matches before modifying files
- Interactive map preview using OpenStreetMap
- Display:
  - latitude
  - longitude
  - elevation
  - capture time
  - adjusted time
  - match status
- Create geotagged copies without modifying source photos
- Write GPS latitude, longitude, and altitude to JPEG EXIF metadata
- Batch process entire photo folders

## How It Works

1. Select a GPX track.
2. Select a folder containing photos.
3. Choose the camera's timezone.
4. Adjust the camera time offset if necessary.
5. Preview calculated photo locations.
6. Review the results in the table or map.
7. Choose an output folder.
8. Create geotagged copies.

Photo locations are calculated by finding the GPX points immediately before and after each photo timestamp and interpolating the position between them.

## Tech Stack

- Python
- PySide6 / Qt
- gpxpy
- Pillow
- piexif
- Leaflet
- OpenStreetMap

## Project Structure

```text
src/geotagger/
├── main.py
├── gpx_parser.py
├── matcher.py
├── preview.py
├── processor.py
├── photo_metadata.py
├── exif_writer.py
├── geo_utils.py
├── time_utils.py
└── ui/
    ├── main_window.py
    ├── preview_table.py
    └── map_view.py