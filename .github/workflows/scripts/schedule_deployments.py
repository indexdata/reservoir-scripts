#!/usr/bin/env python3

"""
Generate and commit Kubernetes custom resource for a pool at the GitOps repository.
Append the schedule JSONL to schedule-deployments.jsonl file.

NOTE: Please use 'black' to re-format code.
"""

# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "jinja2",
# ]
# [tool.uv]
# exclude-newer = "7 days"
# ///

import argparse
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import pprint  # pylint: disable=unused-import
import re
import sys

from jinja2 import Environment, FileSystemLoader

SCRIPT_VERSION = "1.7.0"

LOGLEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}
PROG_NAME = Path(sys.argv[0]).name
PROG_PATH = Path(__file__).absolute().parent
PROG_DESC = __import__("__main__").__doc__
LOG_FORMAT = "%(levelname)s: %(message)s"
LOGGER = logging.getLogger(PROG_NAME)


def get_options():
    """
    Gets the input options.
    Verifies configuration.
    """
    options_okay = True
    parser = argparse.ArgumentParser(description=PROG_DESC)
    parser.add_argument(
        "-l",
        "--loglevel",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level. (Default: %(default)s)",
    )
    args = parser.parse_args()
    logging.basicConfig(format=LOG_FORMAT)
    if args.loglevel:
        loglevel = LOGLEVELS.get(args.loglevel.lower(), logging.NOTSET)
        LOGGER.setLevel(loglevel)
    LOGGER.info("Using script version: %s", SCRIPT_VERSION)
    try:
        action = os.environ["ACTION"]
    except KeyError:
        LOGGER.error("Missing env: ACTION")
        options_okay = False
    try:
        schedule = os.environ["SCHEDULE"]
    except KeyError:
        LOGGER.error("Missing env: SCHEDULE")
        options_okay = False
    try:
        branch = os.environ["BRANCH_NAME"]
    except KeyError:
        LOGGER.error("Missing env: BRANCH_NAME")
        options_okay = False
    try:
        dir_output = os.environ["DIR_OUTPUT"]
    except KeyError:
        LOGGER.error("Missing env: DIR_OUTPUT")
        options_okay = False
    try:
        job_id = os.environ["JOB_ID"]
    except KeyError:
        LOGGER.error("Missing env: JOB_ID")
        options_okay = False
    templates_pn = PROG_PATH.joinpath("templates")
    if not templates_pn.exists():
        LOGGER.error("The jinja templates '%s' not found.", templates_pn)
        options_okay = False
    dir_namespace = "minitex-matchers"
    dir_storage = PROG_PATH.parent.parent.parent.joinpath(dir_output, dir_namespace)
    if not dir_storage.exists():
        LOGGER.error("The namespace directory '%s' not found.", dir_namespace)
        options_okay = False
    if not options_okay:
        sys.exit(2)
    return int(job_id), branch, action, schedule, templates_pn, dir_storage


def load_matchers_summary():
    """
    Loads the summary of all matchers.
    """
    input_fn = "matchers-summary.json"
    input_pn = PROG_PATH.parent.parent.parent.joinpath(input_fn)
    # LOGGER.debug("%s", input_pn)
    with open(input_pn, mode="r", encoding="utf-8") as json_fh:
        try:
            summary = json.load(json_fh)
        except json.decoder.JSONDecodeError as err:
            msg = f"Trouble loading '{input_fn}' JSON file: {err.lineno} {err.msg}"
            LOGGER.critical(msg)
            sys.exit(1)
    return summary


def get_matcher_script(matchers_summary, matcher):
    """
    Get the script pathname and type for this matcher.
    """
    script_fn = None
    script_type = None
    input_fn = "matchers-summary.json"
    if not any(dictionary.get("name") == matcher for dictionary in matchers_summary):
        msg = f"Matcher '{matcher}' not found in '{input_fn}' file."
        LOGGER.critical(msg)
        sys.exit(1)
    else:
        matcher_details = [d for d in matchers_summary if d["name"] == matcher]
        try:
            matcher_details[0]["script"]
        except KeyError:
            msg = (
                "The 'script' property is not found for "
                f"matcher '{matcher}' in '{input_fn}' file."
            )
            LOGGER.critical(msg)
            sys.exit(1)
        script_fn = matcher_details[0]["script"]
        script_pn = PROG_PATH.parent.parent.parent.joinpath(script_fn)
        if not script_pn.exists():
            msg = (
                f"The script '{script_fn}' declared for "
                f"matcher '{matcher}' in '{input_fn}' file "
                "does not exist."
            )
            LOGGER.critical(msg)
            sys.exit(1)
        try:
            matcher_details[0]["type"]
        except KeyError:
            msg = (
                "The 'type' property is not found for "
                f"matcher '{matcher}' in '{input_fn}' file."
            )
            LOGGER.critical(msg)
            sys.exit(1)
        else:
            script_type = matcher_details[0]["type"]
    return script_fn, script_type


def slugify(branch):
    """
    Translate branch name into a string suitable for pool ID.
    """
    slug = branch.lower().strip()
    slug = re.sub(r"\W+", "-", slug)  # Replace non-word characters
    slug = slug.replace("_", "-")
    slug = re.sub(r"[-]+", "-", slug)
    slug = slug.strip("-")
    # Ensure first character is alpha
    match = re.search(r"^([0-9])", slug)
    if match:
        slug = f"a{slug}"
    return slug


def assemble_pool_details(schedule, branch, matchers_summary):
    """
    Assembles the details of this pool.
    """
    # LOGGER.debug("schedule=%s", schedule)
    deployments = schedule.split(",")
    matchers = []
    pool_matchers = []
    pool_details = {"matchers": []}
    for deployment in deployments:
        matcher_packet = {}
        matcher, sha = deployment.split(":")
        matcher_packet["name"] = matcher
        matcher_packet["sha"] = sha
        matcher_fn, matcher_type = get_matcher_script(matchers_summary, matcher)
        matcher_packet["script"] = matcher_fn
        matcher_packet["type"] = matcher_type
        id_matcher = f"{matcher}-{sha[0:7]}"
        matcher_packet["id"] = id_matcher
        matchers.append(id_matcher)
        pool_matchers.append(f"{id_matcher}-matcher::matchkey")
        pool_details["matchers"].append(matcher_packet)
    id_pool = slugify(branch)
    # id_pool = "-".join(matchers)
    pool_details["id_pool"] = id_pool
    pool_details["pool_matcher"] = ", ".join(pool_matchers)
    return id_pool, pool_details


def generate_cr(templates_pn, pool_details, dir_storage):
    """
    Generates and stores the custom resource YAML.
    """
    # pprint.pprint(pool_details)
    dir_pools = dir_storage.joinpath("pools")
    os.makedirs(dir_pools, exist_ok=True)
    pool_pn = dir_pools.joinpath(f"{pool_details['id_pool']}.yaml")
    env_jinja = Environment(loader=FileSystemLoader(templates_pn))
    template_cr = env_jinja.get_template("cr.yaml.jinja")
    content_cr = template_cr.render(
        id_pool=pool_details["id_pool"],
        pool_matcher=pool_details["pool_matcher"],
        matchers=pool_details["matchers"],
    )
    with open(pool_pn, mode="w", encoding="utf-8") as output_fh:
        output_fh.write(content_cr)
        output_fh.write("\n")


def append_schedule(job_id, branch, action, id_pool, dir_storage):
    """
    Composes the JSONL and appends to file.
    """
    dir_log = dir_storage.joinpath("log")
    os.makedirs(dir_log, exist_ok=True)
    schedule_pn = dir_log.joinpath("schedule-deployments.jsonl")
    json_packet = {}
    json_packet["id"] = job_id
    json_packet["scheduleDate"] = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )
    json_packet["action"] = action
    json_packet["initialized"] = False
    json_packet["poolId"] = id_pool
    json_packet["branch"] = branch
    with open(schedule_pn, mode="a", encoding="utf-8") as output_fh:
        output_fh.write(json.dumps(json_packet, sort_keys=False, indent=None))
        output_fh.write("\n")


def main():
    """
    Generate and commit Kubernetes custom resource for a pool at the GitOps repository.
    Append the schedule JSONL to schedule-deployments.jsonl file.
    """
    job_id, branch, action, schedule, templates_pn, dir_storage = get_options()
    matchers_summary = load_matchers_summary()
    id_pool, pool_details = assemble_pool_details(schedule, branch, matchers_summary)
    generate_cr(templates_pn, pool_details, dir_storage)
    append_schedule(job_id, branch, action, id_pool, dir_storage)


if __name__ == "__main__":
    sys.exit(main())
