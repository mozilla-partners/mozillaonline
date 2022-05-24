#!/usr/bin/env python

import os
import taskcluster

from taskcluster import download
from taskcluster.exceptions import TaskclusterRestFailure

EXTENSIONS = ["cehomepage", "china-newtab", "cpmanager"]
XPINSTALL = "application/x-xpinstall"

def download_artifact(**kwargs):
    target_file = kwargs.pop("targetFile")
    with open(target_file, "wb") as f:
        download.downloadArtifactToFile(file=f, **kwargs)

def xpi_artifact(queue, taskId):
    result = queue.listLatestArtifacts(taskId)
    xpi_artifacts = [
        artifact for artifact in result.get("artifacts", []) if (
            artifact.get("contentType") == XPINSTALL and
            artifact.get("name", "").endswith(".xpi")
        )
    ]
    assert len(xpi_artifacts) == 1
    return xpi_artifacts[0].get("name")

def task_for_index(index, indexPath):
    try:
        return index.findTask(indexPath).get("taskId")
    except TaskclusterRestFailure as tcrf:
        if tcrf.status_code == 404:
            return ""
        raise tcrf

def main():
    config = taskcluster.optionsFromEnvironment()
    index = taskcluster.Index(config)
    queue = taskcluster.Queue(config)

    for extension in EXTENSIONS:
        indexPath = f"xpi.v2.xpi-manifest.{extension}.release-signing.latest"
        target_file = f"templates/extensions/{extension}.xpi"
        taskId = task_for_index(index, indexPath)
        if not taskId:
            print(f"No task found for index {indexPath}")
            continue

        xpi_artifact_name = xpi_artifact(queue, taskId)
        download_artifact(
            name=xpi_artifact_name,
            queueService=queue,
            targetFile=target_file,
            taskId=taskId
        )
        print(f"{xpi_artifact_name} from {taskId} saved to {target_file}")

if __name__ == "__main__":
    if not os.getenv("CI"):
        from dotenv import load_dotenv
        load_dotenv()

    main()
