import os
import io
import json
import tempfile
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from typing import Optional

logger = logging.getLogger(__name__)

# Scopes required for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.file']
# Path for the service account key file
SERVICE_ACCOUNT_FILE = 'service-account-key.json'
# Optional: Specify a folder ID in Google Drive where reports should be uploaded
DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", None)  # Set this in your .env file


class GoogleDriveService:
    def __init__(self):
        self.creds = self._get_credentials()
        if self.creds:
            try:
                self.service = build('drive', 'v3', credentials=self.creds)
                logger.info("Google Drive service initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to build Google Drive service: {e}", exc_info=True)
                self.service = None
        else:
            self.service = None
            logger.error("Failed to obtain Google Drive credentials.")

    def _get_credentials(self):
        """Gets credentials from the service account key file or environment variable."""
        try:
            # First try to get credentials from environment variable
            service_account_key = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")
            if service_account_key:
                try:
                    # Create a temporary file with the service account key json content
                    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
                        tmp.write(service_account_key)
                        tmp_file_path = tmp.name
                    
                    credentials = service_account.Credentials.from_service_account_file(
                        tmp_file_path, scopes=SCOPES)
                    
                    # Remove the temporary file
                    os.unlink(tmp_file_path)
                    
                    logger.info("Successfully loaded service account credentials from environment variable")
                    return credentials
                except Exception as env_error:
                    logger.error(f"Error loading service account credentials from environment: {env_error}", exc_info=True)
                    # Fall back to file-based credentials
            
            # Fall back to file-based credentials
            if not os.path.exists(SERVICE_ACCOUNT_FILE):
                logger.error(f"Service account key file not found: {SERVICE_ACCOUNT_FILE}")
                logger.error("Please download your service account key file from Google Cloud Console and save it as "
                            f"'{SERVICE_ACCOUNT_FILE}' in the backend directory or set GOOGLE_SERVICE_ACCOUNT_KEY environment variable.")
                return None
                
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
                
            logger.info("Successfully loaded service account credentials from file")
            return credentials
                
        except Exception as e:
            logger.error(f"Error loading service account credentials: {e}", exc_info=True)
            return None

    def upload_file(self, file_buffer: io.BytesIO, filename: str, mime_type: str = 'application/pdf') -> Optional[str]:
        """
        Uploads a file buffer to Google Drive and returns the shareable link.
        
        Args:
            file_buffer: BytesIO buffer containing the file data
            filename: Name to give the file in Google Drive
            mime_type: MIME type of the file (default: 'application/pdf')
            
        Returns:
            Optional[str]: Web view link to the uploaded file, or None if upload fails
        """
        if not self.service:
            logger.error("Google Drive service not available for upload.")
            return None
        if not file_buffer or file_buffer.getbuffer().nbytes == 0:
             logger.error(f"File buffer for {filename} is empty, cannot upload.")
             return None

        try:
            # Reset buffer position
            file_buffer.seek(0)

            file_metadata = {
                'name': filename,
                'mimeType': mime_type
            }
            
            # Add parent folder if specified
            use_root_dir = True
            if DRIVE_FOLDER_ID:
                try:
                    # Check if folder exists before trying to use it
                    folder = self.service.files().get(fileId=DRIVE_FOLDER_ID, fields="id,name").execute()
                    if folder and folder.get('id'):
                        file_metadata['parents'] = [DRIVE_FOLDER_ID]
                        use_root_dir = False
                        logger.info(f"Uploading '{filename}' to Drive folder: {folder.get('name', DRIVE_FOLDER_ID)}")
                except HttpError as folder_error:
                    logger.warning(f"Specified folder ID {DRIVE_FOLDER_ID} not found or not accessible: {folder_error}. Falling back to root directory.")
            
            if use_root_dir:
                logger.info(f"Uploading '{filename}' to Drive root directory.")

            media = MediaIoBaseUpload(file_buffer, mimetype=mime_type, resumable=True)

            logger.info(f"Starting Google Drive upload for: {filename} (MIME type: {mime_type})")
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink' # Request necessary fields
            ).execute()

            file_id = file.get('id')
            web_view_link = file.get('webViewLink') # Link to view in browser

            if not file_id:
                 logger.error("Google Drive upload failed, no file ID returned.")
                 return None

            logger.info(f"File '{filename}' uploaded successfully. File ID: {file_id}")

            # Make the file publicly readable via link
            try:
                permission = {'type': 'anyone', 'role': 'reader'}
                self.service.permissions().create(
                    fileId=file_id,
                    body=permission,
                    fields='id' # Only need ID back
                ).execute()
                logger.info(f"Permissions set to 'anyone with the link can view' for file ID: {file_id}")
            except HttpError as error:
                logger.error(f"Failed to set permissions for file ID {file_id}: {error}", exc_info=True)
                # Return the link anyway, but log the permission error
                # User might need to manually share if this fails

            logger.info(f"File shareable link: {web_view_link}")
            return web_view_link

        except HttpError as error:
            logger.error(f"An HTTP error occurred during Google Drive upload: {error}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during Google Drive upload: {e}", exc_info=True)
            return None

    # Maintain backward compatibility by keeping upload_pdf as a wrapper
    def upload_pdf(self, pdf_buffer: io.BytesIO, filename: str) -> Optional[str]:
        """Uploads a PDF buffer to Google Drive (wrapper for upload_file)."""
        return self.upload_file(pdf_buffer, filename, mime_type='application/pdf')

# You can create a singleton instance if needed
# google_drive_service = GoogleDriveService() 