from pathlib import PosixPath
from time import time
from typing import Callable, List
from urllib.request import urlopen

from jmanager.models.distribution import Architecture, Version, VersionType, Component


class HTTPFetcher:
    SERVER_URL = "https://ftp.FreeBSD.org"
    FTP_BASE_DIRECTORY = PosixPath('pub/FreeBSD')
    BLOCK_SIZE = 8192

    def fetch_file(self, url: str, destination: PosixPath, callback: Callable[[str, int, int, float], None] = None):
        fetcher = urlopen(url)
        file_size = int(fetcher.headers["content-length"])

        received_bytes = 0
        msg = f"{destination.name} "
        total_time_elapsed = 0.0
        speed = 0.0
        with open(destination.as_posix(), 'wb') as destination_file:
            while True:
                start_time = time()
                buffer = fetcher.read(self.BLOCK_SIZE)
                if not buffer:
                    break

                if total_time_elapsed <= 5.0:
                    speed = len(buffer) / (time() - start_time)
                    total_time_elapsed += (time() - start_time)
                else:
                    total_time_elapsed = 0.0

                received_bytes += len(buffer)
                if callback is not None:
                    callback(msg, received_bytes, file_size, speed)
                destination_file.write(buffer)

    def fetch_tarballs_into(self, version: Version, architecture: Architecture,
                            components: List[Component], temp_dir: PosixPath,
                            callback: Callable[[str, int, int, float], None] = None):
        directory = self.get_directory_path(architecture, version)
        base_url = f"{self.SERVER_URL}/{directory.as_posix()}"

        for component in components.copy():
            temp_file = temp_dir.joinpath(f"{component.value}.txz")
            self.fetch_file(url=f"{base_url}/{component.value}.txz", destination=temp_file, callback=callback)

    def get_directory_path(self, architecture: Architecture, version: Version) -> PosixPath:
        if version.version_type == VersionType.RELEASE:
            directory = self.FTP_BASE_DIRECTORY.joinpath('releases')
        else:
            directory = self.FTP_BASE_DIRECTORY.joinpath('snapshots')
        directory = directory.joinpath(architecture.value, str(version))
        return directory
