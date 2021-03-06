import os
import shutil
from pathlib import PosixPath
from tempfile import TemporaryDirectory, mkdtemp
from urllib.error import URLError

import pytest

from jmanager.models.distribution import Architecture, Version, VersionType, Component
from jmanager.utils.fetch import HTTPFetcher
from test.globals import TEST_DISTRIBUTION

TEMPORARY_RELEASE_FTP_DIR = "releases/amd64/12.0-RELEASE"
TEMPORARY_SNAPSHOT_FTP_DIR = "snapshots/amd64/12.0-STABLE"


class MockingFetcher(HTTPFetcher):
    FTP_BASE_DIRECTORY = PosixPath()

    def __init__(self):
        self.tmp_dir = mkdtemp()
        self.SERVER_URL = f"file://{self.tmp_dir}"

    def __enter__(self):
        for folder in [TEMPORARY_RELEASE_FTP_DIR, TEMPORARY_SNAPSHOT_FTP_DIR]:
            temporary_folder = f"{self.tmp_dir}/{folder}"
            os.makedirs(temporary_folder)

            with open(f"{temporary_folder}/base.txz", "w") as base_file:
                base_file.write("base.txz")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)


class TestFetchUtils:
    class ErrorToBeRaised(BaseException):
        pass

    def test_fetch_base_tarball(self):
        with MockingFetcher() as http_fetcher:
            with TemporaryDirectory() as temp_dir:
                temp_dir_path = PosixPath(temp_dir)
                http_fetcher.fetch_tarballs_into(
                    version=TEST_DISTRIBUTION.version,
                    architecture=TEST_DISTRIBUTION.architecture,
                    components=TEST_DISTRIBUTION.components,
                    temp_dir=temp_dir_path)
                assert temp_dir_path.joinpath('base.txz').is_file()

    def test_fetch_tarballs_invalid_version(self):
        distribution_version = Version(major=10, minor=6, version_type=VersionType.RELEASE)

        with MockingFetcher() as http_fetcher:
            with pytest.raises(URLError, match=r'\[Errno 2\] No such file or directory: '):
                http_fetcher.fetch_tarballs_into(
                    version=distribution_version,
                    architecture=Architecture.AMD64,
                    components=[Component.BASE],
                    temp_dir=PosixPath('/tmp'))

    def test_fetch_tarballs_from_snapshots(self):
        distribution_version = Version(major=12, minor=0, version_type=VersionType.STABLE)

        with MockingFetcher() as http_fetcher:
            with TemporaryDirectory() as temp_dir:
                temp_dir_path = PosixPath(temp_dir)
                http_fetcher.fetch_tarballs_into(
                    version=distribution_version,
                    architecture=Architecture.AMD64,
                    components=[Component.BASE],
                    temp_dir=temp_dir_path)
                assert temp_dir_path.joinpath('base.txz').is_file()

    def test_fetch_with_callback_function(self):
        def callback_function(text_to_show: str, received_bytes: int, total_bytes: int, time_elapsed: float):
            assert isinstance(text_to_show, str)
            assert isinstance(received_bytes, int)
            assert isinstance(total_bytes, int)
            assert isinstance(time_elapsed, float)
            raise TestFetchUtils.ErrorToBeRaised(f"test message")

        distribution_version = Version(major=12, minor=0, version_type=VersionType.STABLE)

        with pytest.raises(TestFetchUtils.ErrorToBeRaised):
            with MockingFetcher() as http_fetcher:
                http_fetcher.fetch_tarballs_into(
                    version=distribution_version,
                    architecture=Architecture.AMD64,
                    components=[Component.BASE],
                    temp_dir=PosixPath('/tmp'),
                    callback=callback_function)
