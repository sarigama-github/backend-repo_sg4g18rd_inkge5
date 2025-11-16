import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TemplateIn(BaseModel):
    title: str
    body: str
    category: Optional[str] = None
    type: Optional[str] = "request"

class RenderRequest(BaseModel):
    template_id: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    data: Dict[str, Any]

@app.get("/")
def read_root():
    return {"message": "Legal Assistant Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# Helper to convert ObjectId
class JSONEncoder:
    @staticmethod
    def encode(doc):
        if isinstance(doc, list):
            return [JSONEncoder.encode(d) for d in doc]
        if isinstance(doc, dict):
            d = {}
            for k, v in doc.items():
                if isinstance(v, ObjectId):
                    d[k] = str(v)
                else:
                    d[k] = v
            return d
        return doc

# CRUD for templates
@app.get("/api/templates")
def list_templates() -> List[Dict[str, Any]]:
    if db is None:
        return []
    docs = get_documents("template")
    return JSONEncoder.encode(docs)

@app.post("/api/templates")
def create_template(payload: TemplateIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    inserted_id = create_document("template", payload.dict())
    doc = db["template"].find_one({"_id": ObjectId(inserted_id)})
    return JSONEncoder.encode(doc)

# Render a document from template and data
@app.post("/api/render")
def render_document(payload: RenderRequest):
    body: Optional[str] = payload.body
    title: Optional[str] = payload.title

    if payload.template_id:
        try:
            t = db["template"].find_one({"_id": ObjectId(payload.template_id)})
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid template_id")
        if not t:
            raise HTTPException(status_code=404, detail="Template not found")
        body = body or t.get("body", "")
        title = title or t.get("title", "")

    if not body:
        raise HTTPException(status_code=400, detail="No template body provided")

    # Simple placeholder rendering: {{ key }}
    rendered = body
    for k, v in payload.data.items():
        rendered = rendered.replace("{{ "+k+" }}", str(v))
        rendered = rendered.replace("{{"+k+"}}", str(v))

    # Save generated doc
    doc_id = create_document("generateddoc", {
        "template_id": payload.template_id,
        "title": title or "Generated Document",
        "rendered": rendered,
        "data": payload.data
    })
    doc = db["generateddoc"].find_one({"_id": ObjectId(doc_id)})
    return JSONEncoder.encode(doc)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
