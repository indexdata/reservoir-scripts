#!/usr/bin/env python3

"""
Determine relevant matchers from the list of touched files.

NOTE: Please use 'black' to re-format code.
"""

import argparse
import json
import logging
import os
from pathlib import Path
import re
import sys

SCRIPT_VERSION = "1.3.2"

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
        files_list = os.environ["FILES_LIST"]
    except KeyError:
        LOGGER.error("Missing env: FILES_LIST")
        options_okay = False
    if not options_okay:
        sys.exit(2)
    return files_list


def collate_assertions_test_records(input_fn):
    """
    Reads a JSON assertions file and collates the records filenames.
    """
    assertion_records = []
    with open(input_fn, mode="r", encoding="utf-8") as json_fh:
        try:
            content = json.load(json_fh)
        except json.decoder.JSONDecodeError as err:
            msg = f"Trouble loading assertions file: {err.lineno} {err.msg}"
            LOGGER.error(msg)
            raise
    for record_fn in content.keys():
        assertion_records.append(record_fn)
    return assertion_records


def gather_matchers_test_records():
    """
    Inspects each assertions file
    and composes list of record files for each matcher.
    """
    assertion_re = r"assertions-([^\.]+)\.json$"
    matchers_records = {}
    dir_test = Path("test")
    files_assertions = list(dir_test.glob("assertions*.json"))
    for input_fn in files_assertions:
        match = re.search(assertion_re, input_fn.name)
        if match:
            assertion = match.group(1)
            # Handle some special files.
            if assertion == "deepdish-goldrush2024":
                assertion = "deepdish"
            try:
                matchers_records[assertion]
            except KeyError:
                matchers_records[assertion] = set([])
            assertion_records = collate_assertions_test_records(input_fn)
            for record_fn in assertion_records:
                matchers_records[assertion].add(f"js/{record_fn}")
    return matchers_records


def detect_matcher_for_record(matchers_records, record_fn):
    """
    Detect matchers that utilise this record file.
    """
    matchers = []
    for matcher in matchers_records.keys():
        if record_fn in matchers_records[matcher]:
            matchers.append(matcher)
    return matchers


def main():
    """
    Determine relevant matchers from the list of touched files.

    Returns:
        Space-delimited string of matcher names.
    """
    files_list = get_options()
    LOGGER.debug("files_list=%s", files_list)
    matcher_src_re = r"^js/matchers/([^/]+)/.+\.mjs$"
    test_src_re = r"^js/test/([^.]+)\.mjs$"
    test_assertion_re = r"js/test/assertions-([^\.]+)\.json$"
    matcher_name_re = r"^[a-zA-Z][0-9a-zA-Z-]+[0-9a-zA-Z]$"
    matcher_errors = False
    matchers_records = gather_matchers_test_records()
    # pprint.pprint(matchers_records)
    matchers = set()
    for input_fn in files_list.split():
        match = re.search(matcher_src_re, input_fn)
        if match:
            matchers.add(match.group(1))
        match = re.search(test_src_re, input_fn)
        if match:
            matchers.add(match.group(1))
        match = re.search(test_assertion_re, input_fn)
        if match:
            matchers.add(match.group(1))
        # Handle some special files:
        if input_fn == "js/test/assertions-deepdish-goldrush2024.json":
            matchers.add("deepdish")
            matchers.discard("deepdish-goldrush2024")
        if input_fn == "js/matchers/goldrush/goldrush.mjs":
            matchers.add("goldrush2021")
            matchers.discard("goldrush")
        # Detect changed related assertions records.
        for matcher in detect_matcher_for_record(matchers_records, input_fn):
            matchers.add(matcher)
    for matcher in matchers:
        if len(matcher) < 3:
            msg = (
                f"matcher '{matcher}': "
                "The matcher name length must be longer than 2 characters"
            )
            LOGGER.error(msg)
            matcher_errors = True
        else:
            match = re.search(matcher_name_re, matcher)
            if not match:
                msg = (
                    f"matcher '{matcher}': "
                    "The matcher names are restricted to alpha-numeric "
                    "or hyphen characters, and must begin with an alpha character, "
                    "and must not end with hyphen."
                )
                LOGGER.error(msg)
                matcher_errors = True
        if matcher in ["goldrush2021"]:
            continue
        dir_matcher = Path(f"matchers/{matcher}")
        if not dir_matcher.exists():
            LOGGER.error("The matcher '%s' does not exist.", matcher)
            matcher_errors = True
    if matcher_errors:
        sys.exit(1)
    LOGGER.info("Determined %s matchers.", len(matchers))
    print(" ".join(matchers))


if __name__ == "__main__":
    sys.exit(main())
