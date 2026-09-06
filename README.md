# TrailTag

TrailTag is a desktop application that adds GPS coordinates to photos by
matching their EXIF capture timestamps against a GPX track.

Source photos are never modified. TrailTag previews every match first and
creates geotagged copies in a separate output folder.

## Current Features

- Load timestamped GPX tracks
- Load folders of JPEG photos
- Read EXIF `DateTimeOriginal`
- Convert camera timestamps between time zones
- Apply an adjustable camera time offset
- Interpolate locations between surrounding GPX points
- Reject interpolation across an unsafe GPX time gap
- Preview matches in a table and on an OpenStreetMap map
- Click a map marker to see a thumbnail of its matched photo
- Save a route as a named trip and reopen it after restarting TrailTag
- Review each saved trip's map, distance, duration, locations, and photo totals
- Rename or delete saved trips, reopen them for editing, and reconnect moved photos
- Review elevation gain, average speed, and an elevation profile for each trip
- Browse a saved trip's photos beside its map and elevation profile
- Select a gallery photo or map marker to highlight the same route location
- Display latitude, longitude, elevation, times, and match status
- Create geotagged JPEG copies without modifying source photos
- Keep earlier output copies safe by choosing a numbered filename when needed
- Write GPS latitude, longitude, and altitude to EXIF metadata
- Batch-process a photo folder
- Keep the window responsive with background processing and live progress
- Cancel safely between photos and continue past individual photo failures
- Remember the last folders, timezone, GPX gap, and window size
- Install from a standard Windows installer with a Start menu shortcut
- Switch between light and dark mode from the Appearance menu; your choice is remembered

## Latest checkpoint: 0.2.0

- Fixed map photo previews getting stuck on the loading message.
- Added coordinated light/dark colors for tables, galleries, menus, map popups,
  and elevation charts, with contrast checks for text/background pairs.
- Assigned the TrailTag icon explicitly to the app window and Start menu shortcut,
  and added a shared Windows taskbar identity. The EXE includes multi-size icons
  for File Explorer. Installer files themselves use Windows' standard installer icon.

After building the installer, close TrailTag and run `dist\TrailTag-Setup-0.2.0-x64.msi`, then
open TrailTag from Start. Saved trips and original photos are retained. If an
older pinned shortcut still shows a generic icon, unpin it and pin the updated
TrailTag Start menu entry again.

Earlier local test installers were labeled 1.0.x. Windows considers 0.2.0 an
older version, so uninstall a 1.0.x test build before installing 0.2.0. Uninstalling
preserves saved trips and original photos. Existing installer files are not
renamed or rebuilt by a source-code commit.

## How It Works

1. Select a GPX track.
2. Select a folder containing JPEG photos.
3. Choose the camera's timezone and any required clock offset.
4. Preview the calculated photo locations.
5. Review the results in the table or map.
6. Save the route as a named trip if you want to revisit it later.
7. Choose a separate output folder.
8. Create the geotagged copies.

TrailTag finds the GPX points immediately before and after each photo's
adjusted timestamp, then interpolates the position between those points.

Saved trips are stored locally in your Windows app-data folder. TrailTag keeps
a snapshot of the route and match details so the trip map and statistics remain
available after the app closes. Photo thumbnails remain linked to the original
photo files, so a thumbnail may become unavailable if its source photo is moved
or deleted. Use **Reconnect photos** in Saved trips after moving a photo folder.
Deleting a saved trip removes only TrailTag's saved record; it never deletes the
original GPX track or photos.

## Run TrailTag

Create and activate a Python 3.12 virtual environment, then install the
dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start the desktop application from the project folder:

```powershell
python -m src.geotagger.main
```

## Run the Tests

```powershell
python -m pytest
```

The tests use generated GPX and JPEG files. Personal photos and local test
data are not read or uploaded.

## Tech Stack

- Python
- PySide6 / Qt
- gpxpy
- Pillow
- piexif
- Leaflet
- OpenStreetMap
- pytest

## Project Structure

```text
src/geotagger/
|-- main.py
|-- gpx_parser.py
|-- matcher.py
|-- preview.py
|-- processor.py
|-- photo_metadata.py
|-- exif_writer.py
|-- geo_utils.py
|-- time_utils.py
|-- trip_store.py
|-- workers.py
`-- ui/
    |-- elevation_profile.py
    |-- main_window.py
    |-- photo_gallery.py
    |-- preview_table.py
    |-- map_view.py
    `-- saved_trips_view.py

tests/
|-- test_gpx_and_time.py
|-- test_main_window.py
|-- test_matcher.py
|-- test_photo_workflow.py
`-- test_trip_store.py
```

## Build the Windows Application

Install the build dependency:

```powershell
python -m pip install -r requirements-build.txt
```

Then run the repeatable build script:

```powershell
.\scripts\build_windows.ps1
```

The script runs the tests first, builds the application in a temporary staging
folder, verifies that its window starts correctly, and creates
`dist\TrailTag-windows-x64.zip`. The ZIP contains the complete application;
extract it before opening `TrailTag.exe`.

To build both the portable ZIP and the Windows installer, run:

```powershell
.\scripts\build_installer.ps1
```

This produces `dist\TrailTag-Setup-0.2.0-x64.msi`. The installer adds TrailTag
to the Windows Start menu and to the Installed apps list. By default it
installs for the current Windows account. Running the same installer again
offers repair and uninstall options. Installing or
uninstalling the app does not delete saved trips because those are kept
separately in the current user's Windows app-data folder.

The installer build downloads a checksum-pinned copy of WiX 5.0.2 into the
ignored `build` folder the first time it is needed. It does not install WiX as
a permanent developer tool.

Both downloads include third-party software notices and a separate SHA-256
checksum file. The checksum can be used to verify that a downloaded package
has not changed.

Installer verification is available with `scripts\test_installer.ps1`.
It installs, starts, repairs, and uninstalls a temporary TrailTag installation,
checking that saved trips stay unchanged. It refuses to run if TrailTag is
already installed so it cannot replace an existing installation.

The local release artifacts are not digitally signed. Windows may show an
unknown-publisher warning until a trusted code-signing certificate is added
for a public release.

The map requires an internet connection because it loads Leaflet and
OpenStreetMap map tiles at runtime. Photo matching and EXIF writing remain
local.
