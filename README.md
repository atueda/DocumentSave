# Dodument Save
This is a python script for saving message in Slack. 

## Prerequisites
Make sure you have python3 installed in your system.
Go to the [python website](https://www.python.org/downloads/) to download and install python3.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Setup

Copy the `example.env` file to `.env` file.

```bash
cp example.env .env
```

Update the `.env` file with your slack token.

```bash
SLACK_ORG_ADMIN_USER_TOKEN=xoxp-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

The slack user token can be found in the [You app's admin page](https://api.slack.com/apps). 

Go to the `OAuth & Permissions` page and copy the `User OAuth Token` under the `OAuth Tokens for Your Workspace` section.

<img src="./slack-user-token.png" alt="slack-user-token image" width="500"/>


## Usage
Run the following command to get the users list whose country attribute is None.

```bash
python3 app.py 
python3 count.py 
```