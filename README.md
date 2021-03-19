# Postmatic

Postmatic is a simple reddit-to-instagram posting bot based upon a cli

## Usage

*Coming soon..*

## Example config

```json
{
    "description": "Bot based upon Postmatic",
    "reddit": {
        "subreddit": "memes",
        "client_id": "fdsfs",
        "client_secret": "sfdfgdgsdfsdgdfgsdfsgsdff"
    },
    "instagram": {
        "username": "fd",
        "password": "fdfg"
    },
    "mins_per_upload": 1440
}
```

## Under-the-hood

Postmatic uses a PRAW-based reddit fetcher and custom selenium for Instagram uploading so use at your own risk! Everything is written in Python and there are currently no plans to change anything major; this program is in maintenance-mode.
