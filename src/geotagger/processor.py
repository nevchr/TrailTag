from dataclasses import dataclass
from pathlib import Path

from .exif_writer import write_photo_gps
from .preview import PreviewResult


@dataclass
class ProcessResult:
    photo_name: str
    success: bool
    status: str
    output_path: Path | None = None


def process_preview_results(
    preview_results: list[PreviewResult],
    output_folder: Path,
) -> list[ProcessResult]:
    """
    Create geotagged copies using previously calculated
    preview results.
    """

    results: list[ProcessResult] = []

    for preview in preview_results:

        if (
            not preview.matched
            or preview.latitude is None
            or preview.longitude is None
        ):
            results.append(
                ProcessResult(
                    photo_name=preview.source_path.name,
                    success=False,
                    status=f"Skipped: {preview.status}",
                )
            )

            continue

        output_path = (
            output_folder
            / preview.source_path.name
        )

        try:
            write_photo_gps(
                source_path=preview.source_path,
                output_path=output_path,
                latitude=preview.latitude,
                longitude=preview.longitude,
                elevation=preview.elevation,
            )

        except Exception as error:
            results.append(
                ProcessResult(
                    photo_name=preview.source_path.name,
                    success=False,
                    status=f"Write failed: {error}",
                )
            )

            continue

        results.append(
            ProcessResult(
                photo_name=preview.source_path.name,
                success=True,
                status="Geotagged",
                output_path=output_path,
            )
        )

    return results