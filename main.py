from fastapi import FastAPI, HTTPException, Query, Request
import json
from typing import List, Dict, Any
import os

app = FastAPI(title="Uczelnia API", description="API to retrieve records based on uczelnia parameter")

# Path to the JSON data file
UNI_JSON_FILE_PATH = "uczelnie.json"
TEAM_JSON_FILE_PATH = "osoby.json"
RES_JSON_FILE_PATH = "badania.json"

# Ensure the data file exists
def load_data(data_path) -> List[Dict[str, Any]]:
    try:
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data file not found at {UNI_JSON_FILE_PATH}")
        
        with open(data_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error parsing JSON data file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Badania API. Use /badania endpoint to query research data."}

@app.post("/badania")
async def get_badania(request: Request):
    """
    Retrieve all records from the badania.json file.
    """
    payload = await request.json()

    print("Webhook received:", payload)

    # Test capability
    if isinstance(payload, dict) and "input" in payload and isinstance(payload["input"], str) and payload["input"].startswith("test"):
        return {"output": payload["input"]}

    data = load_data(RES_JSON_FILE_PATH)

    all_keywords = []
    if isinstance(payload, dict):
        # Handle nested structure where keywords are inside 'input' field
        if "input" in payload and isinstance(payload["input"], dict) and "keywords" in payload["input"]:
            keywords_data = payload["input"]["keywords"]
            if isinstance(keywords_data, str):
                keywords_str = keywords_data.lower()
                keywords = [k.strip() for k in keywords_str.replace(';', ',').split(',')]
                all_keywords = [k for k in keywords if k]
            elif isinstance(keywords_data, list):
                all_keywords = [k.lower() for k in keywords_data if isinstance(k, str)]
        # Original handling for direct 'keywords' attribute
        elif "keywords" in payload:
            if isinstance(payload["keywords"], str):
                keywords_str = payload["keywords"].lower()
                keywords = [k.strip() for k in keywords_str.replace(';', ',').split(',')]
                all_keywords = [k for k in keywords if k]
            elif isinstance(payload["keywords"], list):
                all_keywords = [k.lower() for k in payload["keywords"] if isinstance(k, str)]
    # If payload is a list of items
    elif isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict) and "keywords" in item:
                if isinstance(item["keywords"], str):
                    keywords_str = item["keywords"].lower()
                    keywords = [k.strip() for k in keywords_str.replace(';', ',').split(',')]
                    all_keywords.extend([k for k in keywords if k])
                elif isinstance(item["keywords"], list):
                    all_keywords.extend([k.lower() for k in item["keywords"] if isinstance(k, str)])

    print(f"Extracted keywords: {all_keywords}")

    def is_topic(title):
        title_lower = title.lower()
        return any(kw in title_lower for kw in all_keywords)

    matching_entries = [entry for entry in data if is_topic(entry["nazwa"])]

    return matching_entries

@app.post("/uczelnie-zespoly")
async def get_uczelnie(request: Request):
    """
    Retrieve records from the JSON file that match the provided 'uczelnia' parameter.
    If no parameter is provided, returns all records.
    """

    payload = await request.json()

    print("Webhook received:", payload)

    if isinstance(payload, dict) and "input" in payload and isinstance(payload["input"], dict):
        uczelnia = payload["input"].get("uczelnia")
    else:
        uczelnia = payload.get("uczelnia") if "uczelnia" in payload else None

    data_uni = load_data(UNI_JSON_FILE_PATH)
    data_team = load_data(TEAM_JSON_FILE_PATH)
    
    if uczelnia is None:
        return data_uni
    
    # Filter records based on the uczelnia parameter
    filtered_uni_data = [record for record in data_uni if record.get("id") == uczelnia]
    filtered_team_data = [record for record in data_team if record.get("uczelnia") == uczelnia]

    if not filtered_uni_data:
        return {"message": f"No records found for uczelnia: {uczelnia}", "data": []}
    
    return {f'"nazwa_uczelni": {filtered_uni_data}, "zespol":{filtered_team_data}'}
    
@app.get("/uczelnie/list")
def get_uczelnie_list():
    """
    Return a list of all unique uczelnia names in the dataset.
    """
    data = load_data(UNI_JSON_FILE_PATH)
    unique_uczelnie = set(record.get("id") for record in data if "id" in record)
    return {"uczelnie": sorted(list(unique_uczelnie))}
