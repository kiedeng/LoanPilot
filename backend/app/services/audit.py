import json

from sqlalchemy.orm import Session

from app.models.domain import AuditLog


def write_audit_log(db: Session, actor: str, action: str, detail: dict) -> None:
    db.add(AuditLog(actor=actor, action=action, detail_json=json.dumps(detail, ensure_ascii=False)))
    db.commit()
