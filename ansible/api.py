from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible import context
from ansible.module_utils.common.collections import ImmutableDict
import shutil
import ansible.constants as C
import json
import logging


class MyCallbackResult(CallbackBase):
    def __init__(self):
        self.success = {}
        self.failed = {}
        self.unreachable = {}

    def v2_runner_on_ok(self, result, **kwargs):
        hostname = result._host.get_name()
        self.success[hostname] = result

    def v2_runner_on_failed(self, result, **kwargs):
        hostname = result._host.get_name()
        self.failed[hostname] = result

    def v2_runner_on_unreachable(self, result, **kwargs):
        hostname = result._host.get_name()
        self.unreachable[hostname] = result


ANSIBLE_INVENTORY_DEFAULT_PATH = "~/.ansible/hosts"


class BaseRunner(object):
    def __init__(self):
        context.CLIARGS = ImmutableDict(
            connection="paramiko_ssh",
            remote_user="root",
            private_key_file="~/.ssh/id_rsa",
            timeout=3,
            forks=20,
            syntax=None,
            listhosts=None,
            listtags=None,
            listtasks=None
        )

        self.loader = DataLoader()
        self.inventory = InventoryManager(loader=self.loader, sources=[ANSIBLE_INVENTORY_DEFAULT_PATH])
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)


class ADHocRunner(BaseRunner):
    def __init__(self):
        super().__init__()

    def _json_result(self):
        result = {}
        result["success"] = {}
        result["failed"] = {}
        result["unreachable"] = {}

        for host, value in self.my_callback.success.items():
            result["success"][host] = value._result

        for host, value in self.my_callback.failed.items():
            result["failed"][host] = value._result

        for host, value in self.my_callback.unreachable.items():
            result["unreachable"][host] = value._result

        return result

    def run(self, hosts, tasks):
        _play = dict(
            name="Ansible ADHoc Task",
            hosts=hosts,
            gather_facts="no",
            tasks=tasks
        )

        self.my_callback = MyCallbackResult()
        tmq = TaskQueueManager(
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=self.loader,
            passwords=dict(),
            stdout_callback=self.my_callback
        )
        play = Play.load(_play, variable_manager=self.variable_manager, loader=self.loader)
        try:
            tmq.run(play)
        except Exception as e:
            logging.error(str(e))
        finally:
            tmq.cleanup()

        shutil.rmtree(C.DEFAULT_LOCAL_TMP)
        return self._json_result()


class PlayBookRunner(BaseRunner):
    def __init__(self):
        super().__init__()

    def run(self, playbook):
        pb = PlaybookExecutor(
            playbooks=playbook,
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=self.loader,
            passwords=dict()
        )
        result = None
        try:
            result = pb.run()
        except Exception as e:
            print(e)
        return result
