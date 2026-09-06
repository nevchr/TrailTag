"""Create TrailTag's deterministic Windows and application icons."""

from pathlib import Path

from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGING_DIRECTORY = PROJECT_ROOT / "packaging"
PNG_PATH = PACKAGING_DIRECTORY / "trailtag.png"
ICON_PATH = PACKAGING_DIRECTORY / "trailtag.ico"


def main() -> None:
    PACKAGING_DIRECTORY.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (36, 36, 988, 988),
        radius=220,
        fill="#176b4d",
    )

    # A map pin with a camera at its centre keeps the icon recognizable at
    # both Windows shortcut size and in the title bar.
    draw.ellipse((250, 130, 774, 654), fill="#ffffff")
    draw.polygon(
        [(330, 505), (512, 892), (694, 505)],
        fill="#ffffff",
    )
    draw.ellipse((340, 220, 684, 564), fill="#176b4d")
    draw.rounded_rectangle(
        (394, 320, 630, 478),
        radius=28,
        fill="#ffffff",
    )
    draw.polygon(
        [(438, 320), (466, 278), (558, 278), (586, 320)],
        fill="#ffffff",
    )
    draw.ellipse((464, 338, 560, 434), fill="#176b4d")
    draw.ellipse((488, 362, 536, 410), fill="#9bd4b9")

    image.save(PNG_PATH, "PNG", optimize=True)
    image.save(
        ICON_PATH,
        "ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
               (128, 128), (256, 256)],
    )


if __name__ == "__main__":
    main()
