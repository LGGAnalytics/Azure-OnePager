import time
from azure.identity import ClientSecretCredential
from azure.mgmt.datafactory import DataFactoryManagementClient
# import azure.functions as func
import requests
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)



SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
RESOURCE_GROUP  = os.getenv("RESOURCE_GROUP")
FACTORY_NAME    = os.getenv("FACTORY_NAME")
PIPELINE_NAME   = os.getenv("PIPELINE_NAME")

TENANT_ID = os.getenv("BLOB_TENANT_ID")
CLIENT_ID = os.getenv("BLOB_CLIENT_ID")
CLIENT_SECRET = os.getenv("BLOB_CLIENT_SECRET")
FUNCTION_URL = os.getenv("FUNCTION_URL")


def trigger_adf_pipeline(pipeline_name=None, parameters=None):
    """
    Triggers an Azure Data Factory pipeline directly using the Management SDK.

    Args:
        pipeline_name: Name of the pipeline to trigger (defaults to PIPELINE_NAME from .env)
        parameters: Dictionary of parameters to pass to the pipeline (optional)

    Returns:
        run_id: The pipeline run ID for tracking

    Example:
        # Trigger default pipeline
        run_id = trigger_adf_pipeline()

        # Trigger with custom pipeline and parameters
        run_id = trigger_adf_pipeline(
            pipeline_name="my-pipeline",
            parameters={"company_number": "12345678"}
        )
    """
    # Validate required environment variables
    if not all([SUBSCRIPTION_ID, RESOURCE_GROUP, FACTORY_NAME, TENANT_ID, CLIENT_ID, CLIENT_SECRET]):
        raise ValueError(
            "Missing required environment variables. Please ensure the following are set in .env:\n"
            "- AZURE_SUBSCRIPTION_ID\n"
            "- RESOURCE_GROUP\n"
            "- FACTORY_NAME\n"
            "- BLOB_TENANT_ID\n"
            "- BLOB_CLIENT_ID\n"
            "- BLOB_CLIENT_SECRET"
        )

    # Use default pipeline name if not provided
    pipeline_name = pipeline_name or PIPELINE_NAME
    if not pipeline_name:
        raise ValueError("Pipeline name not provided and PIPELINE_NAME not set in .env")

    # Create credentials
    credential = ClientSecretCredential(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

    # Create Data Factory client
    adf_client = DataFactoryManagementClient(credential, SUBSCRIPTION_ID)

    # Trigger the pipeline
    print(f"Triggering pipeline '{pipeline_name}' in Data Factory '{FACTORY_NAME}'...")
    run_response = adf_client.pipelines.create_run(
        resource_group_name=RESOURCE_GROUP,
        factory_name=FACTORY_NAME,
        pipeline_name=pipeline_name,
        parameters=parameters or {}
    )

    run_id = run_response.run_id
    print(f"Pipeline triggered successfully. Run ID: {run_id}")

    return run_id

def check_pipeline_status(run_id, pipeline_name=None):
    """
    Check the status of a running pipeline.

    Args:
        run_id: The pipeline run ID returned from trigger_adf_pipeline()
        pipeline_name: Name of the pipeline (defaults to PIPELINE_NAME from .env)

    Returns:
        Dictionary with status information

    Example:
        run_id = trigger_adf_pipeline()
        time.sleep(10)
        status = check_pipeline_status(run_id)
        print(f"Status: {status['status']}")
    """
    # Validate required environment variables
    if not all([SUBSCRIPTION_ID, RESOURCE_GROUP, FACTORY_NAME, TENANT_ID, CLIENT_ID, CLIENT_SECRET]):
        raise ValueError("Missing required environment variables for Azure authentication")

    pipeline_name = pipeline_name or PIPELINE_NAME
    if not pipeline_name:
        raise ValueError("Pipeline name not provided and PIPELINE_NAME not set in .env")

    # Create credentials
    credential = ClientSecretCredential(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

    # Create Data Factory client
    adf_client = DataFactoryManagementClient(credential, SUBSCRIPTION_ID)

    # Get pipeline run details
    pipeline_run = adf_client.pipeline_runs.get(
        resource_group_name=RESOURCE_GROUP,
        factory_name=FACTORY_NAME,
        run_id=run_id
    )

    return {
        "run_id": pipeline_run.run_id,
        "pipeline_name": pipeline_run.pipeline_name,
        "status": pipeline_run.status,
        "message": pipeline_run.message,
        "run_start": pipeline_run.run_start,
        "run_end": pipeline_run.run_end,
        "duration_ms": pipeline_run.duration_in_ms
    }

def wait_for_pipeline_completion(run_id, pipeline_name=None, timeout_seconds=3600, check_interval=10):
    """
    Wait for a pipeline to complete, checking status periodically.

    Args:
        run_id: The pipeline run ID
        pipeline_name: Name of the pipeline (defaults to PIPELINE_NAME from .env)
        timeout_seconds: Maximum time to wait (default 1 hour)
        check_interval: Seconds between status checks (default 10)

    Returns:
        Final status dictionary

    Raises:
        TimeoutError: If pipeline doesn't complete within timeout

    Example:
        run_id = trigger_adf_pipeline()
        final_status = wait_for_pipeline_completion(run_id)
        if final_status['status'] == 'Succeeded':
            print("Pipeline completed successfully!")
    """
    pipeline_name = pipeline_name or PIPELINE_NAME

    start_time = time.time()

    while True:
        status_info = check_pipeline_status(run_id, pipeline_name)
        current_status = status_info['status']

        print(f"Pipeline status: {current_status}")

        # Terminal states
        if current_status in ['Succeeded', 'Failed', 'Cancelled']:
            return status_info

        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            raise TimeoutError(
                f"Pipeline did not complete within {timeout_seconds} seconds. "
                f"Current status: {current_status}"
            )

        # Wait before next check
        time.sleep(check_interval)
