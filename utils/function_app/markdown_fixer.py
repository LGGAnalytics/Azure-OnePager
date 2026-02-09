import logging
import json
import re
import azure.functions as func

def unify_split_markdown_tables(content):
    """(Your regex logic here)"""
    split_pattern = re.compile(
        r'(<table>.*?)</table>\s*'
        r'(<!-- PageNumber=".*?" -->\s*'
        r'<!-- PageBreak -->\s*'
        r'(?:<!-- PageNumber=".*?" -->\s*)?'
        r'<!-- PageHeader=".*?" -->)\s*'
        r'<table>\s*(<tr>.*?</table>)',
        re.DOTALL
    )
    
    def merge_tables(match):
        first_part = match.group(1)
        page_markers = match.group(2)
        second_part = match.group(3)
        return first_part.rstrip() + "\n" + second_part.lstrip() + "\n\n" + page_markers

    return split_pattern.sub(merge_tables, content)

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON", status_code=400)

    values = body.get('values', [])
    results = {}
    results["values"] = []

    for rec in values:
        recordId = rec['recordId']
        # 1. Get the list of page contents from the input
        # The skillset will send: ["# Page 1 content...", "# Page 2 content..."]
        pages_list = rec['data']['pages_content']
        
        # 2. Join them to reconstruct the full document with page markers
        # Note: Depending on DocIntel version, you might need to insert PageBreaks manually
        # if they aren't in the string. Assuming standard Markdown output:
        full_doc = "\n\n".join(pages_list)

        # 3. Run your fix
        cleaned_doc = unify_split_markdown_tables(full_doc)
        page_chunks = cleaned_doc.split("<!-- PageBreak -->")

        # 4. Output: You can return the full text and let AI Search split it later
        results["values"].append({
            "recordId": recordId,
            "data": {
                "cleaned_markdown": page_chunks
            }
        })

    return func.HttpResponse(json.dumps(results), mimetype="application/json")