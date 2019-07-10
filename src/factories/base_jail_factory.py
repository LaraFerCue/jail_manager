import lzma
import tarfile
from pathlib import PosixPath
from tempfile import TemporaryDirectory
from typing import List

from models.distribution import Distribution, Component, Version, Architecture
from models.jail import JailError
from src.utils.zfs import ZFS, ZFSType, ZFSProperty


def extract_tarball_into(jail_path: PosixPath, path_to_tarball: PosixPath):
    with TemporaryDirectory(prefix="jail_factory_") as temp_dir:
        temp_file_path = f"{temp_dir}/{path_to_tarball.name}"
        with lzma.open(path_to_tarball.as_posix(), 'r') as lz_file:
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(lz_file.read())
        with tarfile.open(temp_file_path, mode='r') as tar_file:
            tar_file.extractall(path=jail_path.as_posix())


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

    def base_jail_exists(self, distribution: Distribution):
        base_jail_dataset = self.get_base_jail_data_set(distribution)
        snapshot_name = self.get_snapshot_name(component_list=distribution.components)
        snapshot_data_set = f"{base_jail_dataset}@{snapshot_name}"
        list_of_datasets = self.ZFS_FACTORY.zfs_list(data_set=snapshot_data_set)
        return len(list_of_datasets) > 0

    def get_snapshot_name(self, component_list: List[Component]):
        components = component_list.copy()
        if Component.BASE in components:
            components.remove(Component.BASE)

        components.sort()
        if not components:
            return self.SNAPSHOT_NAME
        component_extension = '_'.join([dist.value for dist in components])
        return f"{self.SNAPSHOT_NAME}_{component_extension}"

    def create_base_jail(self, distribution: Distribution, path_to_tarballs: PosixPath):
        if self.base_jail_exists(distribution=distribution):
            raise JailError(f"The base jail for '{distribution.version}/{distribution.architecture.value}' exists")

        components = self.get_remaining_components(distribution)
        if not components:
            return

        for component in components:
            if not path_to_tarballs.joinpath(f"{component.value}.txz").is_file():
                raise FileNotFoundError(f"Component '{component.value}' not found in {path_to_tarballs}")

        jail_path = self.get_jail_mountpoint(self.get_base_jail_data_set(distribution=distribution))
        if set(components) == set(distribution.components):
            self.create_base_data_set(distribution, jail_path)

        self.extract_components_into_base_jail(components, jail_path, path_to_tarballs,
                                               self.get_base_jail_data_set(distribution=distribution))

    def get_remaining_components(self, distribution: Distribution):
        components = distribution.components.copy()

        data_set = self.get_base_jail_data_set(distribution=distribution)
        component_list = []
        for component in components.copy():
            component_list.append(component)
            snapshot_name = self.get_snapshot_name(component_list)

            if len(self.ZFS_FACTORY.zfs_list(data_set=f"{data_set}@{snapshot_name}")):
                components.remove(component)
            else:
                return components
        return []

    def extract_components_into_base_jail(self, components: List[Component], jail_path: PosixPath,
                                          path_to_tarballs: PosixPath, data_set: str):
        processed_components = []
        for component in components:
            extract_tarball_into(jail_path, path_to_tarballs.joinpath(f"{component.value}.txz"))
            processed_components.append(component)
            if component == Component.BASE:
                snapshot_name = self.SNAPSHOT_NAME
            else:
                snapshot_name = self.get_snapshot_name(component_list=processed_components)
            self.ZFS_FACTORY.zfs_snapshot(
                data_set=data_set,
                snapshot_name=snapshot_name
            )

    def create_base_data_set(self, distribution, jail_path):
        self.ZFS_FACTORY.zfs_create(
            data_set=self.get_base_jail_data_set(distribution=distribution),
            options={"mountpoint": jail_path.as_posix()}
        )

    def get_jail_mountpoint(self, jail_data_set_path: str) -> PosixPath:
        jail_path = self._jail_root_path.joinpath(jail_data_set_path)
        return jail_path

    def destroy_base_jail(self, distribution: Distribution):
        base_jail_dataset = self.get_base_jail_data_set(distribution)
        if self.base_jail_exists(distribution=distribution):
            snapshot_name = self.get_snapshot_name(component_list=distribution.components)
            self.ZFS_FACTORY.zfs_destroy(data_set=f"{base_jail_dataset}@{snapshot_name}")
        if not len(self.list_base_jails()):
            self.ZFS_FACTORY.zfs_destroy(data_set=f"{base_jail_dataset}")

    def get_base_jail_data_set(self, distribution) -> str:
        return f"{self._zfs_root_data_set}/{distribution.version}_{distribution.architecture.value}"

    def get_jail_data_set(self, jail_name: str) -> str:
        return f"{self._zfs_root_data_set}/{jail_name}"

    def get_origin_from_jail(self, jail_name: str) -> Distribution:
        jail_data_set = self.get_jail_data_set(jail_name)

        origin_list = self.ZFS_FACTORY.zfs_get(jail_data_set, properties=['origin'])
        origin = origin_list[jail_data_set]['origin']
        components = []
        for component in origin.split('@')[1].replace(self.SNAPSHOT_NAME, '').split('_'):
            if component:
                components.append(Component(component))
        origin = origin.split('@')[0]
        origin = origin.replace(f"{self._zfs_root_data_set}/", "")

        version = Version.from_string(origin.split('_')[0])
        architecture = Architecture(origin.split('_')[1])
        return Distribution(version=version, architecture=architecture, components=components)

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
