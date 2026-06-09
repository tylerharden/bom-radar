import ftplib
import re
from pathlib import Path

FTP_HOST = "ftp.bom.gov.au"
FTP_DIR = "/anon/gen/radar"

_FRAME_RE = re.compile(r"^({station})\.T\.(\d{{12}})\.png$")


def list_frames(station: str, n: int = 12) -> list[str]:
    """Return the latest n radar frame filenames for a station from BOM FTP."""
    pattern = re.compile(rf"^{re.escape(station)}\.T\.\d{{12}}\.png$")
    with ftplib.FTP(FTP_HOST) as ftp:
        ftp.login()
        ftp.cwd(FTP_DIR)
        files = ftp.nlst()
    return sorted(f for f in files if pattern.match(f))[-n:]


def download_frames(station: str, cache_dir: Path, n: int = 12) -> list[Path]:
    """Download the latest n frames for a station, skipping already-cached files."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    frames = list_frames(station, n)
    downloaded: list[Path] = []

    with ftplib.FTP(FTP_HOST) as ftp:
        ftp.login()
        ftp.cwd(FTP_DIR)
        for filename in frames:
            dest = cache_dir / filename
            if not dest.exists():
                with open(dest, "wb") as f:
                    ftp.retrbinary(f"RETR {filename}", f.write)
            downloaded.append(dest)

    return downloaded
