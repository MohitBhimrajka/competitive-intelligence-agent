# Google Drive Service Account Setup

This application uses a Google Drive service account to upload PDF reports and generate shareable links. Follow these steps to set up the service account:

## 1. Create a Google Cloud Project

If you don't already have one:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use an existing one)

## 2. Enable the Google Drive API

1. In your project, go to "APIs & Services" > "Library"
2. Search for "Google Drive API" and enable it

## 3. Create a Service Account

1. Go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Give it a name like "competitive-intelligence-drive"
4. Click "Create and Continue"
5. Skip the "Grant this service account access to project" step by clicking "Continue"
6. Skip the "Grant users access to this service account" step by clicking "Done"

## 4. Create and Download the Key

1. Click on the service account you just created
2. Go to the "Keys" tab
3. Click "Add Key" > "Create new key"
4. Choose "JSON" and click "Create"
5. A key file will be downloaded to your computer

## 5. Configure the Application

1. Rename the downloaded key file to `service-account-key.json`
2. Move the file to the `backend` directory of this project
3. Add this file to your `.gitignore` to prevent accidentally committing it

## 6. (Optional) Set Up a Shared Folder

If you want to store files in a specific Google Drive folder:

1. Create a folder in Google Drive
2. Share this folder with the service account's email address (found in the service account details or in the key file as `client_email`)
3. Set the permission to "Editor"
4. Get the folder ID from the URL when you're inside that folder (it's the long alphanumeric string after `/folders/` in the URL)
5. Add this folder ID to your `.env` file:
   ```
   GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
   ```

## Security Notes

- Keep your service account key secure - it's like a password
- Don't commit the key file to version control
- The service account has limited permissions by default
- Files created by the service account will be owned by the service account

## Troubleshooting

- If uploads fail, check the application logs for specific error messages
- Verify that the Drive API is enabled in your Google Cloud project
- Make sure the service account key file is correctly placed in the backend directory
- Ensure the service account has proper permissions if using a shared folder 