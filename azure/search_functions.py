import os, time
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexerClient
from dotenv import load_dotenv, find_dotenv
# Or: from azure.identity import DefaultAzureCredential  # if using Entra ID
load_dotenv(find_dotenv(), override=True)

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")        # e.g. https://<svc>.search.windows.net
INDEXER_NAME    = os.getenv("AZURE_SEARCH_INDEXER")
ADMIN_KEY       = os.getenv("AZURE_SEARCH_API_KEY")        # or use DefaultAzureCredential()

def run_indexer():

    client = SearchIndexerClient(SEARCH_ENDPOINT, AzureKeyCredential(ADMIN_KEY))

    # 1) Run the indexer
    client.run_indexer(INDEXER_NAME)  # on-demand run

    # 2) Poll status (optional)
    while True:
        st = client.get_indexer_status(INDEXER_NAME)
        print("service:", st.status, "| lastResult:", getattr(st.last_result, "status", None))
        if getattr(st.last_result, "status", None) in ("success", "transientFailure", "persistentFailure"):
            break
        time.sleep(10)
