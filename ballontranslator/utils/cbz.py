"""Import comic ZIP pages into a persistent, editable folder project."""

import hashlib
import json
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from natsort import natsorted
from PIL import Image

from .io_utils import IMG_EXT


def import_cbz(archive_path: str) -> str:
    """Return a persistent project directory, preserving an earlier import.

    >>> callable(import_cbz)
    True
    """
    source = Path(archive_path).resolve(strict=True)
    hasher = hashlib.sha256()
    with source.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(chunk)
    digest = hasher.hexdigest()
    destination = source.with_name(f'{source.stem}.ballons-{digest[:12]}')
    marker_name = '.cbz-source.json'
    if destination.exists():
        marker = destination / marker_name
        if destination.is_symlink() or not marker.is_file():
            raise ValueError('CBZ project destination already exists without import metadata.')
        metadata = json.loads(marker.read_text(encoding='utf8'))
        if metadata.get('sha256') != digest:
            raise ValueError('CBZ project metadata does not match the archive.')
        return str(destination)

    with zipfile.ZipFile(source) as archive:
        images = []
        for member in archive.infolist():
            name = PurePosixPath(member.filename.replace('\\', '/'))
            if name.suffix.lower() not in IMG_EXT or member.is_dir():
                continue
            if (name.is_absolute() or '..' in name.parts or ':' in str(name)
                    or stat.S_ISLNK(member.external_attr >> 16)):
                raise ValueError('Unsafe image path in CBZ archive.')
            if '__MACOSX' in name.parts or name.name.startswith('._'):
                continue
            images.append(member)
        if not images:
            raise ValueError('CBZ archive contains no supported images.')
        if len(images) > 10000 or sum(m.file_size for m in images) > 4 * 1024**3:
            raise ValueError('CBZ archive exceeds the import size limit.')
        images = natsorted(images, key=lambda member: member.filename)
        # Only this newly-created staging folder is cleaned up on failure.
        staging = Path(tempfile.mkdtemp(prefix='.cbz-import-', dir=source.parent))
        try:
            pages = []
            for index, member in enumerate(images, 1):
                if member.file_size > 256 * 1024**2:
                    raise ValueError('CBZ page exceeds the import size limit.')
                basename = PurePosixPath(member.filename.replace('\\', '/')).name
                page = staging / f'{index:05d}-{basename}'
                with archive.open(member) as incoming, page.open('xb') as output:
                    shutil.copyfileobj(incoming, output)
                with Image.open(page) as image:
                    image.verify()
                pages.append(page.name)
            (staging / marker_name).write_text(json.dumps({
                'sha256': digest, 'source': str(source), 'pages': pages,
            }, ensure_ascii=False), encoding='utf8')
            staging.rename(destination)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    return str(destination)
