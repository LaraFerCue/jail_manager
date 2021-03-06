import filecmp
import os
from pathlib import PosixPath
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory

import pytest

from jmanager.models.jail import Jail
from jmanager.utils.ansible import Ansible
from test.globals import TMP_PATH, RESOURCES_PATH

TEST_RESOURCES_PLAYBOOK = RESOURCES_PATH.joinpath('playbook')


class MockingAnsible(Ansible):
    ANSIBLE_PLAYBOOK_CMD = "sh scripts/ansible-playbook.sh"
    ANSIBLE_CMD = 'sh scripts/ansible.sh'


def configure_ansible_template(temp_folder_path: str, filename: str):
    with open(RESOURCES_PATH.joinpath('ansible.cfg').as_posix(), 'r') as template:
        with open(f"{temp_folder_path}/{filename}", 'w') as temp_file:
            temp_file.write(template.read().replace('%temp%', temp_folder_path))


class TestProvision:
    def test_write_playbook(self):
        configuration = [{
            'block1': {'name': 'hello'}
        }]
        with TemporaryDirectory() as temp_dir:
            playbook_path = PosixPath(temp_dir).joinpath('test')
            MockingAnsible().write_ansible_playbook(playbook_path,
                                                    configuration)
            assert filecmp.cmp(playbook_path.as_posix(), TEST_RESOURCES_PLAYBOOK.as_posix())

    def test_run_playbook(self):
        os.makedirs(TMP_PATH.as_posix(), exist_ok=True)
        open(TMP_PATH.joinpath(MockingAnsible.ANSIBLE_INVENTORY_NAME), 'w').close()
        MockingAnsible().run_provision(
            path_to_playbook_file=TEST_RESOURCES_PLAYBOOK,
            config_folder=TMP_PATH
        )

        with pytest.raises(CalledProcessError):
            MockingAnsible().run_provision(
                path_to_playbook_file=TEST_RESOURCES_PLAYBOOK.joinpath('none'),
                config_folder=TMP_PATH
            )

    def test_create_ansible_configuration(self):
        with TemporaryDirectory() as temp_dir:
            MockingAnsible().write_ansible_configuration(PosixPath(temp_dir))
            configure_ansible_template(temp_dir, 'config')
            assert filecmp.cmp(f"{temp_dir}/ansible.cfg", f"{temp_dir}/config", shallow=False)

    def test_write_inventory_file(self):
        with TemporaryDirectory() as config_dir:
            config_dir_path = PosixPath(config_dir)
            MockingAnsible().write_inventory([Jail('test1'), Jail('test2')], config_dir_path)
            assert filecmp.cmp(config_dir_path.joinpath('ansible_inventory').as_posix(),
                               RESOURCES_PATH.joinpath('ansible_inventory').as_posix())

    def test_run_provision_cmd(self):
        cmd = 'echo true'

        with TemporaryDirectory() as ansible_dir:
            ansible_dir_path = PosixPath(ansible_dir)
            open(ansible_dir_path.joinpath('ansible_inventory').as_posix(), 'w').close()
            open(ansible_dir_path.joinpath('ansible.cfg').as_posix(), 'w').close()
            MockingAnsible().run_provision_cmd(cmd, 'test', config_folder=ansible_dir_path)
