#!/usr/bin/python

import json
from os import environ
from functools import partial

from tc_api import create_tasks


def metadata(name, description):
    return {
        "name": name,
        "description": description,
        "owner": environ["GITHUB_HEAD_USER_EMAIL"],
        "source": environ["GITHUB_HEAD_REPO_URL"],
    }


def build_image_task(image):
    return {
        "provisionerId": "aws-provisioner-v1",
        "workerType": "github-worker",
        "requires": "all-completed",
        "priority": "lowest",
        "created": {"relative-datestamp": "0 day"},
        "deadline": {"relative-datestamp": "1 day"},
        "metadata": metadata("build/{}".format(image),
                             "Build docker image for {}".format(image)),
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
                    "path": "/repo/image.tar",
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
        "dependencies": [labels["/".join([image, 'build'])]],
        "requires": "all-completed",
        "priority": "lowest",
        "created": {"relative-datestamp": "0 day"},
        "deadline": {"relative-datestamp": "1 day"},
        "metadata": metadata("run/{}".format(image),
                             "Run docker image for {}".format(image)),
        "payload": {
            "maxRunTime": 3600,
            "image": {
                "type": "task-image",
                "taskId": labels["/".join([image, 'build'])],
                "path": "public/image.tar",
            },
            "env": {
                "DOCKER_API_VERSION": "1.18",
                "GITHUB_HEAD_REPO_URL": environ["GITHUB_HEAD_REPO_URL"],
                "GITHUB_HEAD_SHA": environ["GITHUB_HEAD_SHA"],
                "SRC": "/repo",
            },
            "command": [
                "/bin/bash",
                "--login",
                "-c",
                'git clone "$GITHUB_HEAD_REPO_URL" "$SRC" && '
                'cd "$SRC" && git config advice.detachedHead false && '
                'git checkout "$GITHUB_HEAD_SHA" && '
                'mkdir "$HOME/rustsrc" && '
                'src/ci/init_repo.sh . "$HOME/rustsrc" && '
                'mkdir $SRC/build && cd $SRC/build &&'
                '$SRC/src/ci/run.sh'
            ]
        }
    }


tasks = []
for image in ['x86_64-gnu-llvm-3.7', 'asmjs']:
    tasks.extend([
        ("/".join([image, 'build']), build_image_task(image)),
        ("/".join([image, 'run']), partial(run_image_task, image)),
    ])

resolved_tasks = create_tasks(tasks)

with open("task-graph.json", "w") as f:
    json.dump(resolved_tasks, f)
