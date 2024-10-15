import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Define the scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Add the path to your service account key file
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)




# Authorize and open the spreadsheet
client = gspread.authorize(creds)

# List all spreadsheets to check for correct title

spreadsheets = client.openall()
for sheet in spreadsheets:
    print(sheet.title)


spreadsheet = client.open("Air-Quality")
sheet = spreadsheet.sheet1  # Access the first sheet

# Store data in the sheet
data = ["John Doe", "john.doe@example.com", 30]
sheet.append_row(data)

# Retrieve all data from the sheet
all_data = sheet.get_all_records()
print(all_data)

# Retrieve specific row/column
row_data = sheet.row_values(2)
print(f"Row 2 data: {row_data}")

col_data = sheet.col_values(2)
print(f"Column 2 data: {col_data}")
