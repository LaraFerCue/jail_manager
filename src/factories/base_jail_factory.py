import lzma
import shutil
import tarfile
from os import chflags
from pathlib import PosixPath
from stat import SF_IMMUTABLE
from tempfile import TemporaryDirectory
from typing import List, Callable

from models.distribution import Distribution, Component, Version, Architecture
from models.jail import JailError
from src.factories.data_set_factory import DataSetFactory
from src.utils.file_utils import extract_tarball_into, remove_immutable_path


class BaseJailFactory:
    ZFS_FACTORY = ZFS()
    SNAPSHOT_NAME = "jmanager_base_jail"

    def __init__(self, jail_root_path: PosixPath, zfs_root_data_set: str):
        self._jail_root_path = jail_root_path
        self._zfs_root_data_set = zfs_root_data_set

        if jail_root_path.exists() and not jail_root_path.is_dir():
            raise PermissionError("The jail root path exists and it is not a directory")
        elif not jail_root_path.exists():
            jail_root_path.mkdir(parents=True)

    def get_jail_mountpoint(self, jail_data_set_path: str) -> PosixPath:
        jail_path = self._jail_root_path.joinpath(jail_data_set_path)
        return jail_path

    def get_base_jail_data_set(self, distribution) -> str:
        return f"{self._zfs_root_data_set}/{distribution.version}_{distribution.architecture.value}"

    def get_jail_data_set(self, jail_name: str) -> str:
        return f"{self._zfs_root_data_set}/{jail_name}"

    def get_snapshot_name(self, component_list: List[Component]):
        components = component_list.copy()
        if Component.BASE in components:
            components.remove(Component.BASE)

        components.sort()
        if not components:
            return self.SNAPSHOT_NAME
        component_extension = '_'.join([dist.value for dist in components])
        return f"{self.SNAPSHOT_NAME}_{component_extension}"

    def base_data_set_exists(self, data_set: str, snapshot: str = ""):
        if snapshot:
            return len(self.ZFS_FACTORY.zfs_list(data_set=f"{data_set}@{snapshot}"))
        return len(self.ZFS_FACTORY.zfs_list(data_set=data_set))

    def base_jail_exists(self, distribution: Distribution):
        base_jail_dataset = self.get_base_jail_data_set(distribution)
        snapshot_name = self.get_snapshot_name(component_list=distribution.components)
        snapshot_data_set = f"{base_jail_dataset}@{snapshot_name}"
        list_of_datasets = self.ZFS_FACTORY.zfs_list(data_set=snapshot_data_set)
        return len(list_of_datasets) > 0

    def create_base_jail(self, distribution: Distribution, path_to_tarballs: PosixPath,
                         callback: Callable[[str, int, int], None] = None):
        if self.base_jail_exists(distribution):
            raise JailError(f"The base jail for '{distribution.version}/{distribution.architecture.value}' exists")

        for component in distribution.components:
            if not path_to_tarballs.joinpath(f"{component.value}.txz").is_file():
                raise FileNotFoundError(f"Component '{component.value}' not found in {path_to_tarballs}")

        jail_path = self.get_jail_mountpoint(f"{distribution.version}_{distribution.architecture.value}")
        if not self.base_data_set_exists(data_set=self.get_base_jail_data_set(distribution)):
            self.create_base_data_set(distribution, jail_path)
        else:
            remove_immutable_path(jail_path)

        self.extract_components_into_base_jail(components=distribution.components,
                                               jail_path=jail_path,
                                               path_to_tarballs=path_to_tarballs,
                                               data_set=self.get_base_jail_data_set(distribution=distribution),
                                               callback=callback)

    def extract_components_into_base_jail(self, components: List[Component], jail_path: PosixPath,
                                          path_to_tarballs: PosixPath, data_set: str,
                                          callback: Callable[[str, int, int], None]):
        processed_components = []
        for component in components:
            extract_tarball_into(
                jail_path=jail_path,
                path_to_tarball=path_to_tarballs.joinpath(f"{component.value}.txz"),
                callback=callback
            )
            processed_components.append(component)
            if component == Component.BASE:
                snapshot_name = self.SNAPSHOT_NAME
            else:
                snapshot_name = self.get_snapshot_name(component_list=processed_components)

            if not self.base_data_set_exists(data_set=data_set, snapshot=snapshot_name):
                self.ZFS_FACTORY.zfs_snapshot(
                    data_set=data_set,
                    snapshot_name=snapshot_name
                )

    def create_base_data_set(self, distribution, jail_path):
        self.ZFS_FACTORY.zfs_create(
            data_set=self.get_base_jail_data_set(distribution=distribution),
            options={"mountpoint": jail_path.as_posix(),
                     "dedup": "sha512",
                     "atime": "off"}
        )

    def destroy_base_jail(self, distribution: Distribution):
        base_jail_dataset = self.get_base_jail_data_set(distribution)
        if self.base_jail_exists(distribution=distribution):
            snapshot_name = self.get_snapshot_name(component_list=distribution.components)
            self.ZFS_FACTORY.zfs_destroy(data_set=f"{base_jail_dataset}@{snapshot_name}")
        if not len(self.list_base_jails()):
            self.ZFS_FACTORY.zfs_destroy(data_set=f"{base_jail_dataset}")

    def list_base_jails(self) -> List[Distribution]:
        list_of_snapshots = self.ZFS_FACTORY.zfs_list(self._zfs_root_data_set, depth=-1,
                                                      properties=[ZFSProperty.NAME],
                                                      types=[ZFSType.SNAPSHOT])
        distribution_list = []
        for snapshot in list_of_snapshots:
            snapshot_name = snapshot[ZFSProperty.NAME].split('@')[1].replace(f"{self.SNAPSHOT_NAME}", '')
            data_set = snapshot[ZFSProperty.NAME].split('@')[0].replace(f"{self._zfs_root_data_set}/", '')

            components = []
            for component in snapshot_name.split('_'):
                if component:
                    components.append(Component(component))
            version = Version.from_string(data_set.split('_')[0])
            architecture = Architecture(data_set.split('_')[1])
            distribution_list.append(Distribution(version=version, architecture=architecture,
                                                  components=components))
        return distribution_list
