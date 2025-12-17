# Streamlit Cloud Deployment Guide

## Prerequisites
1. A Streamlit Cloud account (sign up at https://share.streamlit.io/)
2. Your Google Cloud service account credentials (`credentials.json`)
3. This repository pushed to GitHub

## Step-by-Step Deployment

### 1. Prepare Your Repository
Ensure your latest changes are pushed to GitHub:
```bash
git add -A
git commit -m "Ready for deployment"
git push origin master
```

### 2. Deploy to Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Click "New app"
3. Select your repository: `daregoodness1997/youtube-channels-script`
4. Set the branch to `master`
5. Set main file path to `app.py`
6. Click "Deploy"

### 3. Configure Secrets
⚠️ **IMPORTANT**: Your app won't connect to Google Sheets until you add secrets!

1. In Streamlit Cloud, open your deployed app
2. Click the three-dot menu (⋮) in the top right
3. Select "Settings"
4. Go to the "Secrets" section
5. Copy the contents of your `credentials.json` file
6. Format it as TOML and paste into the secrets editor:

```toml
[gcp_service_account]
type = "service_account"
project_id = "useeducator"
private_key_id = "your-private-key-id-here"
private_key = "-----BEGIN PRIVATE KEY-----\nYour-Full-Private-Key-Here\n-----END PRIVATE KEY-----\n"
client_email = "youtube-data-api@useeducator.iam.gserviceaccount.com"
client_id = "118046692065655758618"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/youtube-data-api%40useeducator.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

7. Click "Save"
8. Your app will automatically reboot with the new secrets

### 4. Verify Deployment
1. Open your deployed app
2. Try extracting a video with Google Sheets enabled
3. Check that data appears in your Google Sheet

## Troubleshooting

### Google Sheets Connection Fails
- **Check**: Did you add the secrets in Streamlit Cloud settings?
- **Check**: Is your Google Sheet shared with `youtube-data-api@useeducator.iam.gserviceaccount.com`?
- **Check**: Does the sheet ID in your custom URL match the actual sheet?
- **Check**: Is the worksheet name correct (default is "Sheet1")?

### Database Not Persisting
- Streamlit Cloud's file system is ephemeral - the SQLite database will reset on each deployment
- For persistent storage, consider using:
  - Google Sheets only (disable local database)
  - Streamlit Cloud's file uploader to backup/restore the database
  - External database service (PostgreSQL, MongoDB, etc.)

### Module Import Errors
- Verify all dependencies are in `requirements.txt`
- Check that Python version matches (see `runtime.txt` if needed)

### API Quota Exceeded
- YouTube API has daily quotas
- Monitor usage at: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas

## Security Notes

✅ **DO:**
- Keep `credentials.json` in `.gitignore`
- Use Streamlit secrets for deployment
- Regularly rotate service account keys
- Monitor service account usage

❌ **DON'T:**
- Commit `credentials.json` to git
- Share your credentials publicly
- Use credentials in client-side code
- Hardcode API keys in source code

## Support
For issues, check:
- Streamlit Docs: https://docs.streamlit.io/
- YouTube API Docs: https://developers.google.com/youtube/v3
- Repository Issues: https://github.com/daregoodness1997/youtube-channels-script/issues
