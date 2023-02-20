# Jellyfin Scripts

## Delete watched media

This script deletes watched media from Jellyfin. 

The media must meet the following criteria before it's deleted:
- It is not marked as a Favorite.
- A week has passed since the media was marked as watched.

### Setup

1. Make a copy of `env.example` named `.env`.
   ```bash
   cp env.example .env
   ```
1. In `.env`, enter values for each of the environment variables and save the file.

### Run the scipt

This deletes media from your server. Run this script at your own risk:
1. Run the script:
   ```bash
   python jellyfin/delete_watched.py
   ```

## Quirks

For some reason, an API key is not sufficient for deleting items. You need an access key. To retrieve the access key, you need an API key, admin username, and password. The script automatically retrieves one unless you've added an `JELLY_ACCESS_TOKEN` environment variable.

Retrieving an access token may result in new access tokens being assigned. I've found that when using the Swiftfin app on an AppleTV device, this causes my logged-in user to revieve `401` errors. I have to delete and recreate the user on Swiftfin to get around this. This does not affect the user on the Jellyfin server; all user data, such as favorites and last played dates persist. But it's annoying. To get around this disruption, I assign the `JELLY_ACCESS_TOKEN` environment variable so the scipt doesn't send the `POST` call to retrieve the access token every time it runs. 

If you want to fetch your `JELLY_ACCESS_TOKEN`, you can insert a `print(auth_token['AccessToken'])` above `return(auth_token['AccessToken'])` in the script. Remember to remove this when you have the token, cos you don't really want it being printed to the console every time.