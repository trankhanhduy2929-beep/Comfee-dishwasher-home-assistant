"""Build the Comfee dishwasher custom-component archive."""

from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parent
COMPONENT = ROOT / "custom_components" / "comfee_dishwasher"
OUTPUT = ROOT / "dist" / "comfee_dishwasher.zip"
CHECKSUM = ROOT / "dist" / "comfee_dishwasher.zip.sha256"
ARCHIVE_TIMESTAMP = (2020, 1, 1, 0, 0, 0)


def main() -> None:
    """Create a clean Home Assistant custom-component archive."""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(COMPONENT.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            archive_name = path.relative_to(COMPONENT)
            info = ZipInfo(archive_name.as_posix(), ARCHIVE_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    digest = sha256(OUTPUT.read_bytes()).hexdigest()
    CHECKSUM.write_text(f"{digest}  {OUTPUT.name}\n", encoding="ascii")
    OUTPUT.chmod(0o644)
    CHECKSUM.chmod(0o644)
    print(f"{OUTPUT}\n{CHECKSUM}")


if __name__ == "__main__":
    main()
