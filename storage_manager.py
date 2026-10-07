from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore
import uvicorn
import os

app = FastAPI(title="Smart Storage & Calendar Portal")

# Build absolute paths for files in the project folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_KEY_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")
INDEX_PATH = os.path.join(BASE_DIR, "index.html")

# Initialize Firebase Admin SDK safely
if os.path.exists(SERVICE_KEY_PATH):
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_KEY_PATH)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Successfully connected to Firebase!")
else:
    db = None
    print("Warning: serviceAccountKey.json not found in project directory.")

DOC_EXTENSIONS = {'.docx', '.pdf', '.xlsx', '.csv', '.txt', '.pptx'}

class EventSchema(BaseModel):
    title: str
    category: str
    date: str
    time: str
    description: str = ""
    author: str = "Anonymous"

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    if os.path.exists(INDEX_PATH):
        return FileResponse(INDEX_PATH)
    return HTMLResponse(content="<h1>index.html not found!</h1>", status_code=404)

# Firebase Firestore Endpoints for Shared Calendar
@app.get("/api/events")
async def get_events():
    if not db:
        return []
    events_ref = db.collection("events").stream()
    events = []
    for doc in events_ref:
        data = doc.to_dict()
        data["id"] = doc.id
        events.append(data)
    return events

@app.post("/api/events")
async def create_event(event: EventSchema):
    if not db:
        raise HTTPException(status_code=500, detail="Firebase not configured.")
    update_time, doc_ref = db.collection("events").add(event.dict())
    return {"id": doc_ref.id, "status": "Event saved to Firestore!"}

@app.delete("/api/events/{event_id}")
async def delete_event(event_id: str):
    if not db:
        raise HTTPException(status_code=500, detail="Firebase not configured.")
    db.collection("events").document(event_id).delete()
    return {"status": "Deleted successfully"}

# File Upload Endpoint
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    target_destination = "Google Drive (Document Storage)" if ext in DOC_EXTENSIONS else "AWS S3 (Blob/Media Storage)"
    icon = "📄" if ext in DOC_EXTENSIONS else "📦"

    return {
        "filename": file.filename,
        "size_bytes": file.size,
        "content_type": file.content_type,
        "routed_to": target_destination,
        "icon": icon,
        "status": "Success"
    }

if __name__ == "__main__":
    uvicorn.run("storage_manager:app", host="127.0.0.1", port=8000, reload=True)