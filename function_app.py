import azure.functions as func
import logging
from engines.profile_pdf import profile_creator, markdown_table_to_docx
from azure.blob_functions import get_company_name, upload_blob

app = func.FunctionApp(http_auth_level=func.AuthLevel.ADMIN)

@app.route(route="pdfprofile")
def pdfprofile(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        body = req.get_json()
    except ValueError:
        body = {}

    company_number = (
        (body.get("company_number") if isinstance(body, dict) else None)
        or (body.get("id") if isinstance(body, dict) else None)
        or (body.get("IDS") if isinstance(body, dict) else None)
        or req.params.get("company_number")
        or req.params.get("id")
        or req.params.get("IDS")
    )

    if company_number:
        agent = profile_creator(company_number)

        company_name = get_company_name(company_number)
        creator = profile_creator(company_name)
        agent._generate_section()
        agent._check_sections()
        all = agent._unite_sections()

        try:
            # Generate document and get BytesIO buffer
            doc_buffer = markdown_table_to_docx(
                all,
                logo_path="logo_teneo.png"
            )
            print(f"✓ Generated {creator.company_name}.docx")
        except Exception as e:
            print(f"Error generating: {e}")
        
        try:
            # Upload to blob storage with metadata
            upload_blob(
                CONTAINER="companieshousesinglefile",
                BLOB_NAME=f"{creator.company_name}_PROFILE.docx",
                file=doc_buffer,
                company_name=creator.company_name,
                company_number=company_number,
                doc_type="profile"
            )
            print(f"✓ Uploaded {creator.company_name}.docx to blob storage")
        except Exception as e:
            print(f"Error uploading document: {e}")

        return func.HttpResponse(f"Hello, {company_name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )