from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.deps import get_current_user_id, get_db

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackIn(BaseModel):
    scope: Literal["answer", "click"]
    query_id: Optional[int] = None
    click_id: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=-1, le=1)
    comment: Optional[str] = Field(default=None, max_length=2000)


@router.post("")
def feedback(
    payload: FeedbackIn,
    uid: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if payload.scope == "answer" and payload.query_id is None:
        raise HTTPException(400, "query_id required for answer scope")
    if payload.scope == "click" and payload.click_id is None:
        raise HTTPException(400, "click_id required for click scope")
    db.execute(
        text(
            """
            INSERT INTO feedback_events
              (user_id, scope, query_id, click_id, rating, comment)
            VALUES (:uid, :scope, :qid, :cid, :rating, :comment)
            """
        ),
        {
            "uid": uid,
            "scope": payload.scope,
            "qid": payload.query_id,
            "cid": payload.click_id,
            "rating": payload.rating,
            "comment": payload.comment,
        },
    )
    db.commit()
    return {"ok": True}
