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


def available_output_path(output_folder: Path, filename: str) -> Path:
    """Return a path that will not replace an existing output file."""

    candidate = output_folder / filename
    if not candidate.exists():
        return candidate

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    copy_number = 1
    while True:
        candidate = output_folder / f"{stem} ({copy_number}){suffix}"
        if not candidate.exists():
            return candidate
        copy_number += 1


def process_preview_results(
    preview_results: list[PreviewResult],
    output_folder: Path,
) -> list[ProcessResult]:
    """
    Create geotagged copies using previously calculated
    preview results.
    """

    validate_output_folder(preview_results, output_folder)
    return [
        process_preview_result(preview, output_folder)
        for preview in preview_results
    ]


def validate_output_folder(
    preview_results: list[PreviewResult],
    output_folder: Path,
) -> None:
    resolved_output_folder = output_folder.resolve()
    source_folders = {
        preview.source_path.resolve().parent
        for preview in preview_results
    }
    if resolved_output_folder in source_folders:
        raise ValueError(
            "The output folder must be different from the "
            "source photo folder."
        )


def process_preview_result(
    preview: PreviewResult,
    output_folder: Path,
) -> ProcessResult:
    if (
        not preview.matched
        or preview.latitude is None
        or preview.longitude is None
    ):
        return ProcessResult(
            photo_name=preview.source_path.name,
            success=False,
            status=f"Skipped: {preview.status}",
        )

    output_path = available_output_path(
        output_folder,
        preview.source_path.name,
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
        return ProcessResult(
            photo_name=preview.source_path.name,
            success=False,
            status=f"Write failed: {error}",
        )

    renamed = output_path.name != preview.source_path.name
    return ProcessResult(
        photo_name=preview.source_path.name,
        success=True,
        status=(
            f"Geotagged as {output_path.name}"
            if renamed
            else "Geotagged"
        ),
        output_path=output_path,
    )
