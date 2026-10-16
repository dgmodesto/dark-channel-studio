from fastapi import APIRouter
from pydantic import BaseModel

from dcs_niche_templates import list_templates

router = APIRouter()


class TemplateSummary(BaseModel):
    id: str
    version: int
    name: str
    content_language: str


@router.get("/templates")
async def templates() -> list[TemplateSummary]:
    return [
        TemplateSummary(
            id=t.id, version=t.version, name=t.name, content_language=t.content_language
        )
        for t in list_templates()
    ]
