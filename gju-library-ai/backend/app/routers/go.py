from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.deps import get_current_user_id, get_db

router = APIRouter(tags=["click"])


@router.get("/go/{click_id}")
def go(
    click_id: str,
    uid: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text(
            """
            UPDATE click_events
               SET clicked_at = COALESCE(clicked_at, now())
             WHERE id = :id AND user_id = :uid
             RETURNING target_url
            """
        ),
        {"id": click_id, "uid": uid},
    ).first()
    db.commit()
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    return RedirectResponse(url=row.target_url, status_code=302)
