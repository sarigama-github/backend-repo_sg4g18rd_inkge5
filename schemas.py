"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class Template(BaseModel):
    """
    Templates for legal documents (requests, indictments, etc.)
    Collection name: "template"
    """
    title: str = Field(..., description="Template title")
    body: str = Field(..., description="Template text with placeholders like {{ case_number }}")
    category: Optional[str] = Field(None, description="Category, e.g., organizations, court, bank")
    type: Optional[str] = Field("request", description="Type: request | indictment | other")

class Generateddoc(BaseModel):
    """
    Rendered documents based on templates
    Collection name: "generateddoc"
    """
    template_id: Optional[str] = Field(None, description="Source template id")
    title: str = Field(..., description="Document title")
    rendered: str = Field(..., description="Rendered plain text content")
    data: Dict[str, Any] = Field(default_factory=dict, description="Data used for rendering")
