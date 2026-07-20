from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "app" / "static" / "img" / "campus-quad.jpg"
OUTPUTS = (
    (380, ROOT / "app" / "static" / "img" / "campus-quad-380.webp"),
    (760, ROOT / "app" / "static" / "img" / "campus-quad-760.webp"),
)


def main() -> None:
    with Image.open(SOURCE) as image:
        image = image.convert("RGB")
        for width, output in OUTPUTS:
            height = round(image.height * (width / image.width))
            resized = image.resize((width, height), Image.Resampling.LANCZOS)
            resized.save(output, "WEBP", quality=32, method=6)
            print(f"{output.relative_to(ROOT)} {width}x{height} {output.stat().st_size} bytes")


if __name__ == "__main__":
    main()
