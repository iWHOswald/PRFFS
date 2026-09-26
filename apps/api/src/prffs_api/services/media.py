from pathlib import Path
import re

MEDIA_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".pdf"}


def infer_media_metadata(path: Path, root: Path) -> dict:
    rel = path.relative_to(root)
    text = str(rel)
    year_match = re.search(r"(20\d{2})", text)
    week_match = re.search(r"week[_-]?(\d+)|wk[_-]?(\d+)", text, flags=re.IGNORECASE)
    category = None
    lower = path.name.lower()
    for candidate in ["side", "points", "draft", "plus", "minus", "qb", "rb", "wr", "te", "dst"]:
        if candidate in lower:
            category = candidate
            break

    week = None
    if week_match:
        week = int(next(group for group in week_match.groups() if group))

    return {
        "path": str(rel),
        "title": path.stem.replace("_", " ").replace("-", " "),
        "media_type": path.suffix.lower().lstrip("."),
        "year": int(year_match.group(1)) if year_match else None,
        "week": week,
        "category": category,
    }


def discover_media(root: Path) -> list[dict]:
    ignored = {".git", ".idea", "node_modules", "archive", "apps"}
    assets: list[dict] = []
    for path in root.rglob("*"):
        if any(part in ignored for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS:
            assets.append(infer_media_metadata(path, root))
    return assets
