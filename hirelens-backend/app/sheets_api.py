import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# SCOPES for reading Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]

SPREADSHEET_ID = "1HU7DC4wYhO_NsUUJiHe_qVBUBdXi1CJEO_kr29tY_lU"  # Replace with your actual Sheet ID
RANGE_NAME = "Sheet1!A1:E4"           # Adjust the range as needed

def get_static_sheet_data():
    """Fetches data from the hardcoded Google Sheet."""
    creds = None
    TOKEN_PATH = "app/google-drive-api-information/token.json"

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    else:
        print("Token file not found. Please authenticate again.")
        return {"error": "Authentication token not found. Please re-authenticate."}, 401

    try:
        # Build the Sheets API service
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API with the hardcoded ID and range
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()

        values = result.get("values", [])

        if not values:
            return {"message": "No data found."}, 404

        return {"data": values}, 200

    except HttpError as error:
        return {"error": f"An error occurred: {error}"}, 500
