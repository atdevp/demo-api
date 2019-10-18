from api import ADHocRunner
from api import PlayBookRunner
import json


def run_adhoc():
    runner = ADHocRunner()
    hosts = [
        "1.1.1.1",
        "1.1.1.2"
    ]

    tasks = [
        dict(action=dict(module="shell", args="uptime"), register="res"),
        dict(action=dict(module="debug", args=dict(msg="{{res.stdout}}")))
    ]

    #result = runner.run(hosts, tasks)
    result = runner.run("t1", tasks)
    print(json.dumps(result))


def run_playbook():
    runner = PlayBookRunner()
    play_book = ["/Users/ad/workspace/demo-api/ansible/main.yml"]
    result = runner.run(play_book)
    print(result)


def main():
    run_adhoc()
    # run_playbook()


main()
