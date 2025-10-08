from io import BytesIO
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient
from dotenv import load_dotenv, find_dotenv
import os 
load_dotenv(find_dotenv(), override=True)


# === CONFIG ===
ACCOUNT_URL   = os.getenv("BLOB_ACCOUNT_URL")
AZURE_STORAGE_CONNECTION_STRING=os.getenv("BLOB_AZURE_STORAGE_CONNECTION_STRING")
# BLOB_NAME     = "companieslist/CompaniesHouseList.xlsx"   # e.g., "reports/myfile.xlsx"



def get_file_blob(CONTAINER, BLOB_NAME):
    # === AUTH + CLIENT ===
    # cred = DefaultAzureCredential()  # Works locally (Azure CLI login), in VM/MSI, GitHub OIDC, etc.
    # blob = BlobClient(account_url=ACCOUNT_URL, container_name=CONTAINER,
    #                 blob_name=BLOB_NAME, credential=cred)

    blob = BlobClient.from_connection_string(conn_str=AZURE_STORAGE_CONNECTION_STRING,
                                         container_name=CONTAINER,
                                         blob_name=BLOB_NAME)


    data = blob.download_blob().readall()

    return data

def companyHouseListAdd(CONTAINER = 'companieslist', BLOB_NAME = 'CompaniesHouseList.xlsx', CompanyNumber = None):

    df = get_file_blob(CONTAINER, BLOB_NAME)

    excel_bytes = get_file_blob(CONTAINER, BLOB_NAME)

    df = pd.read_excel(BytesIO(excel_bytes), sheet_name="IDs")

    # 2) Append at the end (assumes single column)
    col = df.columns[0]
    df = pd.concat([df, pd.DataFrame({col: [CompanyNumber]})], ignore_index=True)

    # 3) Write back to Excel in-memory
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        df.to_excel(xw, index=False, sheet_name="IDs")
    buf.seek(0)

    # 4) Overwrite the blob
    blob = BlobClient.from_connection_string(conn_str=AZURE_STORAGE_CONNECTION_STRING,
                                         container_name=CONTAINER,
                                         blob_name=BLOB_NAME)
    blob.upload_blob(buf, overwrite=True)

def upload_blob(CONTAINER, BLOB_NAME, file, company):
    blob = BlobClient.from_connection_string(conn_str=AZURE_STORAGE_CONNECTION_STRING,
                                        container_name=CONTAINER,
                                        blob_name=BLOB_NAME)
        
    pass

def get_companies(CONTAINER = 'companieslist', BLOB_NAME = 'CompaniesHouseList.xlsx'):


    excel_bytes = get_file_blob(CONTAINER = 'companieslist', BLOB_NAME = 'CompaniesHouseList.xlsx')
    df = pd.read_excel(BytesIO(excel_bytes), sheet_name="IDs")
    names = df['NAMES'].copy()
    clean = (names.astype(str)
                .str.replace(r'_+', ' ', regex=True)  # "_" -> " "
                .str.replace(r'\s+', ' ', regex=True) # collapse double spaces
                .str.strip())

    name_map = dict(zip(names.tolist(), clean.tolist()))
    clean_in_order = [name_map[orig] for orig in names] 




    return name_map, clean_in_order