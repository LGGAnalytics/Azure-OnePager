import azure.functions as func
import logging
import json
import re

app = func.FunctionApp()

@app.route(route="fix_tables", auth_level=func.AuthLevel.FUNCTION)
def fix_tables(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing request to fix split markdown tables.')

    try:
        from utils.function_app.markdown_fixer import markdown_fixer
    except ImportError as e:
        logging.error(f"Failed to import markdown_fixer: {e}")
        return func.HttpResponse("Internal Server Error: Missing dependencies", status_code=500)
    
    try:
        results = markdown_fixer.main(req)
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)

    return func.HttpResponse(json.dumps(results), mimetype="application/json")