r"""CrowdStrike Unattended Stale Sensor Environment Detector
REQUIRES: crowdstrike-falconpy v0.9.0+, python-dateutil, tabulate

This example will work for all CrowdStrike regions. In order to produce
results for the US-GOV-1 region, pass the '-g' argument.
"""

import csv
from argparse import ArgumentParser, RawTextHelpFormatter
from datetime import datetime, timedelta, timezone
from dateutil import parser as dparser
from tabulate import tabulate

try:
    from falconpy import Hosts
except ImportError as no_falconpy:
    raise SystemExit(
        "CrowdStrike FalconPy must be installed in order to use this application.\n"
        "Please execute `python3 -m pip install crowdstrike-falconpy` and try again."
    ) from no_falconpy

# API Credentials
client_id = "XXX"
client_secret = "XXX"

def connect_api(key: str, secret: str, base_url: str, child_cid: str = None) -> Hosts:
    """Connect to the API and return an instance of the Hosts Service Class."""
    return Hosts(client_id=key, client_secret=secret, base_url=base_url, member_cid=child_cid)

def get_host_details(id_list: list) -> list:
    """Retrieve a list containing device infomration based upon the ID list provided."""
    returned = falcon.get_device_details(ids=id_list)["body"]["resources"]
    if not returned:
        returned = []
    return returned

def get_hosts(date_filter: str, tag_filter: str) -> list:
    """Retrieve a list of hosts IDs that match the last_seen date filter."""
    filter_string = f"last_seen:<='{date_filter}Z'"
    if tag_filter:
        filter_string = f"{filter_string} + tags:*'*{tag_filter}*'"

    return falcon.query_devices_by_filter_scroll(
        limit=5000,
        filter=filter_string
    )["body"]["resources"]

def calc_stale_date(num_days: int) -> str:
    """Calculate the 'stale' datetime based upon the number of days provided by the user."""
    today = datetime.utcnow()
    return str(today - timedelta(days=num_days)).replace(" ", "T")

def parse_host_detail(detail: dict, found: list):
    """Parse the returned host detail and add it to the stale list."""
    now = datetime.now(timezone.utc)
    then = dparser.parse(detail["last_seen"])
    distance = (now - then).days
    tagname = detail.get("tags", "Not Found")
    newtag = "\n".join(tagname)
    found.append([
        detail.get("hostname", "Unknown"),
        detail.get("device_id", "Unknown"),
        detail.get("local_ip", "Unknown"),
        newtag,
        dparser.parse(detail["last_seen"], ignoretz=True),
        f"{distance} days"
        ])

    return found

def hide_hosts(id_list: list) -> dict:
    """Hide hosts identified as stale."""
    return falcon.perform_action(action_name="hide_host", body={"ids": id_list})

# Connect to the API
falcon = connect_api(client_id, client_secret, "https://api.crowdstrike.com")

# List to hold our identified hosts
stale = []
# For each stale host identified
for host in get_host_details(get_hosts(calc_stale_date(30), "GCP")):
    # Retrieve host detail
    stale = parse_host_detail(host, stale)

# If we produced stale host results
if stale:
    # Display only is the default
    sorted_results = sorted(stale, key=lambda x: (x[4], x[0]))
    fields = ["Hostname", "Device ID", "Local IP", "Tag", "Last Seen", "Stale Period"]
    stale_display = tabulate(
        sorted_results,
        fields
    )
    print(f"\n{stale_display}")
else:
    print("No stale hosts identified for the range specified.")
