#!/usr/bin/python

import json
from os import environ
from functools import partial

from tc_api import create_tasks


def build_image_task(image):
    return {
        "provisionerId": "aws-provisioner-v1",
        "workerType": "github-worker",
        "requires": "all-completed",
        "priority": "lowest",
        "payload": {
            "maxRunTime": 3600,
            "features": {
                "dind": True
            },
            "env": {
                "IMAGE": image,
                "DOCKER_API_VERSION": "1.18",
                "GITHUB_HEAD_REPO_URL": environ["GITHUB_HEAD_REPO_URL"],
                "GITHUB_HEAD_SHA": environ["GITHUB_HEAD_SHA"],
            },
            "image": "tomprince/rust-ci-base:tc-test",
            "artifacts": {
                "public/image.tar": {
                    "expires": {"relative-datestamp": "1 day"},
                    "path": "/root/image.tar",
                    "type": "file"
                }
            },
            "command": [
                "/bin/bash",
                "--login",
                "-c",
                'git clone "$GITHUB_HEAD_REPO_URL" repo && '
                'cd repo && git config advice.detachedHead false && '
                'git checkout "$GITHUB_HEAD_SHA" && '
                './run-tc.sh'
            ]
        }
    }


def run_image_task(image, labels):
    return {
        "provisionerId": "aws-provisioner-v1",
        "workerType": "github-worker",
        "depedencies": [labels[(image, 'build')]],
        "requires": "all-completed",
        "priority": "lowest",
        "payload": {
            "maxRunTime": 3600,
            "image": {
                "type": "task-image",
                "taskId": labels[(image, 'build')],
                "path": "public/image.tar",
            },
            "env": {
                "DOCKER_API_VERSION": "1.18",
                "GITHUB_HEAD_REPO_URL": environ["GITHUB_HEAD_REPO_URL"],
                "GITHUB_HEAD_SHA": environ["GITHUB_HEAD_SHA"],
            },
            "command": [
                "/bin/bash",
                "--login",
                "-c",
                'git clone "$GITHUB_HEAD_REPO_URL" repo && '
                'cd repo && git config advice.detachedHead false && '
                'git checkout "$GITHUB_HEAD_SHA" && '
                'src/ci/run.sh'
            ]
        }
    }


tasks = {}
for image in ['x86_64-gnu-llvm-3.7', 'asmjs']:
    tasks.update({
        (image, 'build'): build_image_task(image),
        (image, 'run'): partial(run_image_task, image),
    })
create_tasks(tasks)
with open("task-graph.json") as f:
    json.dump(tasks, f)
