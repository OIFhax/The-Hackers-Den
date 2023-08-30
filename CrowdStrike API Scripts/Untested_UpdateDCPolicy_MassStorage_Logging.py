# A script that will compare the most current device control policy in the falcon console
# with a csv file of deivces and add the devices in the file to a new device control policy
# with an incrementaly larger version number in the name.  could be automated with some 
# human interaction. This is untested, use with caution. As always, update with your client ID
# secret and path to the new csv file. 
# --OIFhax


import csv
import requests
import json
import logging

# Set up logging
logging.basicConfig(filename='script_log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_access_token(client_id, client_secret):
    """Get the access token using client ID and secret."""
    token_endpoint = "https://api.crowdstrike.com/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(token_endpoint, headers=headers, data=data)
    if response.status_code in [200, 201]:  # Treat both 200 and 201 as successful responses
        token_data = response.json()
        if "access_token" in token_data:
            logging.info("Successfully retrieved the access token.")
            return token_data["access_token"]
        else:
            logging.error("Unexpected response: Access token not found.")
            return None
    else:
        logging.error(f"API returned an error. Status code: {response.status_code}. Response: {response.text}")
        return None

def read_csv_and_extract_combined_ids(filename):
    """Read the CSV file and extract combined IDs."""
    combined_ids = []
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            vid = row[0]  # Get the value from column A for Vendor ID
            pid = row[1]  # Get the value from column B for Product ID, if available
            cid = row[2]  # Get the value from column C for Combined ID, if available
            combined_ids.append((vid, pid, cid))
    return combined_ids

def get_latest_policy_version_and_exceptions(access_token):
    """Fetch the latest policy version and its exceptions."""
    api_endpoint = "https://api.crowdstrike.com/policy/entities/device-control/v1"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(api_endpoint, headers=headers)
    if response.status_code == 200:
        policies = response.json().get("resources", [])
        if policies:
            latest_policy = policies[0]  # Assuming the first policy is the latest
            version = latest_policy["name"].split("_v")[-1]
            exceptions = latest_policy["settings"]["classes"][0]["exceptions"]
            logging.info(f"Successfully fetched the latest policy version: {version} with {len(exceptions)} exceptions.")
            return version, exceptions
        else:
            logging.error("No policies found.")
            return None, []
    else:
        logging.error(f"Failed to fetch policies. Response: {response.text}")
        return None, []

def create_new_policy_and_add_exceptions(access_token, combined_ids, existing_exceptions):
    """Create a new policy and add the exceptions."""
    api_endpoint = "https://api.crowdstrike.com/policy/entities/device-control/v1"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    # Construct the payload for a new policy with the combined IDs and PID/VIDs
    payload = {
        "resources": [
            {
                "name": "DC_Allowlist_v3",
                "description": "Policy to allow specific combined IDs and PID/VIDs",
                "platform_name": "Windows",
                "enabled": False,
                "use_wildcard": False,
                "settings": {
                    "enforcement_mode": "MONITOR_ONLY",
                    "end_user_notification": "SILENT",
                    "classes": [
                        {
                            "id": class_type,
                            "action": "BLOCK_ALL" if class_type == "MASS_STORAGE" else "FULL_ACCESS",
                            "exceptions": [
                                {
                                "class": "MASS_STORAGE",
                                "action": "FULL_ACCESS",
                                "vendor_id_decimal": vid
                                } for vid, pid, cid in combined_ids if len(pid) == 0 and len(cid) == 0 
                            ]+ [
                                {
                                "class": "MASS_STORAGE",
                                "action": "FULL_ACCESS",
                                "vendor_id_decimal": vid,
                                "product_id_decimal": pid
                                } for vid, pid, cid in combined_ids if len(pid) > 0 and len(cid) == 0

                            ]+ [
                                {
                                "class": "MASS_STORAGE",
                                "action": "FULL_ACCESS",
                                "combined_id": cid
                                } for vid, pid, cid in combined_ids if len(cid) > 0
                            ] if class_type == "MASS_STORAGE" else []
                        } for class_type in ["ANY", "AUDIO_VIDEO", "IMAGING", "MASS_STORAGE", "MOBILE", "PRINTER", "WIRELESS"]
                    ],                
                    "

enhanced_file_metadata": True
                }
            }
        ]
    }
    
    logging.info(f"Payload for new policy: {json.dumps(payload, indent=1)}")

    # Send the API request to create a new policy
    response = requests.post(api_endpoint, headers=headers, json=payload)
    
    # Check the response
    if response.status_code == 200:
        logging.info("Successfully created a new policy and added combined IDs and PID/VIDs!")
    else:
        logging.error(f"Failed to create a new policy. Response: {response.text}")

if __name__ == "__main__":
    client_id = "YOUR_CLIENT_ID"
    client_secret = "YOUR_CLIENT_SECRET"
    access_token = get_access_token(client_id, client_secret)
    if access_token:
        latest_version, existing_exceptions = get_latest_policy_version_and_exceptions(access_token)
        combined_ids = read_csv_and_extract_combined_ids("PATH_TO_YOUR_CSV_FILE")
        create_new_policy_and_add_exceptions(access_token, combined_ids, existing_exceptions)

