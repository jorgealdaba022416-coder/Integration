import os
import boto3
from storage_interface import StorageAdapter
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

class S3Adapter(StorageAdapter):
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        # Picks up AWS credentials automatically from environment or ~/.aws/credentials
        self.s3_client = boto3.client('s3')

    def upload(self, file_path: str, destination_name: str) -> str:
        self.s3_client.upload_file(file_path, self.bucket_name, destination_name)
        return f"s3://{self.bucket_name}/{destination_name}"

    def list_files(self) -> list:
        response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
        return [obj['Key'] for obj in response.get('Contents', [])]


class GoogleDriveAdapter(StorageAdapter):
    def __init__(self, token_path: str = "token.json"):
        # Assumes OAuth token generated after initial auth flow
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path)
            self.service = build('drive', 'v3', credentials=creds)
        else:
            self.service = None

    def upload(self, file_path: str, destination_name: str) -> str:
        if not self.service:
            return "Google Drive credentials not configured."
        
        file_metadata = {'name': destination_name}
        media = MediaFileUpload(file_path, resumable=True)
        file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return f"gdrive://{file.get('id')}"

    def list_files(self) -> list:
        if not self.service:
            return []
        results = self.service.files().list(pageSize=10, fields="files(id, name)").execute()
        return [f['name'] for f in results.get('files', [])]
