# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Extracted from
# https://dxr.mozilla.org/mozilla-central/source/taskcluster/taskgraph

from __future__ import absolute_import, print_function, unicode_literals

import requests
import requests.adapters
import json
import os


# From https://github.com/taskcluster/slugid.py
def slugid():
    """
    Returns a randomly generated uuid v4 compliant slug which conforms to a set
    of "nice" properties, at the cost of some entropy. Currently this means one
    extra fixed bit (the first bit of the uuid is set to 0) which guarantees
    the slug will begin with [A-Za-f]. For example such slugs don't require
    special handling when used as command line parameters (whereas non-nice
    slugs may start with `-` which can confuse command line tools).

    Potentially other "nice" properties may be added in future to further
    restrict the range of potential uuids that may be generated.
    """
    import uuid
    import base64
    rawBytes = uuid.uuid4().bytes
    # Ensure slug starts with [A-Za-f]
    rawBytes = chr(ord(rawBytes[0]) & 0x7f) + rawBytes[1:]
    return base64.urlsafe_b64encode(rawBytes)[:-2]  # Drop '==' padding

from tc_time import (
    current_json_time,
    json_time_from_now
)


def create_tasks(tasks):
    session = requests.Session()

    decision_task_id = os.environ.get('TASK_ID')

    # when running as an actual decision task, we use the decision task's
    # taskId as the taskGroupId.  The process that created the decision task
    # helpfully placed it in this same taskGroup.  If there is no $TASK_ID,
    # fall back to a slugid
    task_group_id = decision_task_id or slugid()
    scheduler_id = 'taskcluster-github'

    resolved_tasks = {}
    task_ids = {}
    for label, task_def in tasks:
        task_id = slugid()
        task_ids[label] = task_id

        if callable(task_def):
            task_def = task_def(task_ids)
        # if this task has no dependencies, make it depend on this decision
        # task so that it does not start immediately; and so that if this loop
        # fails halfway through, none of the already-created tasks run.
        if decision_task_id and not task_def.get('dependencies'):
            task_def['dependencies'] = [decision_task_id]

        task_def['taskGroupId'] = task_group_id
        task_def['schedulerId'] = scheduler_id

        resolved_tasks[task_id] = task_def
        create_task(session, task_id, label, task_def)

    return resolved_tasks


def create_task(session, task_id, label, task_def):
    # create the task using 'http://taskcluster/queue', which is proxied to the
    # queue service with credentials appropriate to this job.

    # Resolve timestamps
    now = current_json_time(datetime_format=True)
    task_def = resolve_timestamps(now, task_def)

    res = session.put('http://taskcluster/queue/v1/task/{}'.format(task_id),
                      data=json.dumps(task_def))
    if res.status_code != 200:
        try:
            print(res.json()['message'])
        except:
            print(res.text)
        res.raise_for_status()


def resolve_timestamps(now, task_def):
    def recurse(val):
        if isinstance(val, list):
            return [recurse(v) for v in val]
        elif isinstance(val, dict):
            if val.keys() == ['relative-datestamp']:
                return json_time_from_now(val['relative-datestamp'], now)
            else:
                return {k: recurse(v) for k, v in val.iteritems()}
        else:
            return val
    return recurse(task_def)
