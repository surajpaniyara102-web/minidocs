import os, io, html
from datetime import datetime
from fastapi import FastAPI, Depends, Header, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import mammoth, markdown

DB_URL = os.getenv("DB_URL", "sqlite:///./app.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)


class Doc(Base):
    __tablename__ = "docs"
    id = Column(Integer, primary_key=True)
    title = Column(String, default="Untitled")
    content = Column(Text, default="")
    owner_id = Column(Integer, ForeignKey("users.id"))
    updated_at = Column(DateTime, default=datetime.utcnow)


class Share(Base):
    __tablename__ = "shares"
    id = Column(Integer, primary_key=True)
    doc_id = Column(Integer, ForeignKey("docs.id"))
    user_id = Column(Integer, ForeignKey("users.id"))


Base.metadata.create_all(engine)


def seed():
    db = SessionLocal()
    for name in ["alice", "bob", "carol"]:
        if not db.query(User).filter_by(username=name).first():
            db.add(User(username=name))
    db.commit()
    db.close()


seed()

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_user(x_username: str = Header(None), db=Depends(get_db)):
    u = db.query(User).filter_by(username=x_username or "").first()
    if not u:
        raise HTTPException(401, "Login required")
    return u


def get_doc(db, doc_id, user):
    d = db.get(Doc, doc_id)
    if not d:
        raise HTTPException(404, "Document not found")
    is_owner = d.owner_id == user.id
    shared = db.query(Share).filter_by(doc_id=doc_id, user_id=user.id).first()
    if not (is_owner or shared):
        raise HTTPException(403, "No access")
    return d, is_owner


def doc_out(d, db, user, full=False):
    owner = db.get(User, d.owner_id)
    out = {
        "id": d.id,
        "title": d.title,
        "owner": owner.username,
        "is_owner": d.owner_id == user.id,
        "updated_at": d.updated_at.isoformat(),
    }
    if full:
        out["content"] = d.content
    return out


class DocIn(BaseModel):
    title: str | None = None
    content: str | None = None


class ShareIn(BaseModel):
    username: str


class LoginIn(BaseModel):
    username: str


@app.post("/api/login")
def login(body: LoginIn, db=Depends(get_db)):
    u = db.query(User).filter_by(username=body.username.strip().lower()).first()
    if not u:
        raise HTTPException(404, "Unknown user (try alice, bob, carol)")
    return {"username": u.username}


@app.get("/api/docs")
def list_docs(db=Depends(get_db), user=Depends(current_user)):
    owned = db.query(Doc).filter_by(owner_id=user.id).order_by(Doc.updated_at.desc()).all()
    ids = [s.doc_id for s in db.query(Share).filter_by(user_id=user.id)]
    shared = (
        db.query(Doc).filter(Doc.id.in_(ids)).order_by(Doc.updated_at.desc()).all()
        if ids
        else []
    )
    return {
        "owned": [doc_out(d, db, user) for d in owned],
        "shared": [doc_out(d, db, user) for d in shared],
    }


@app.post("/api/docs")
def create_doc(body: DocIn, db=Depends(get_db), user=Depends(current_user)):
    d = Doc(
        title=(body.title or "Untitled").strip()[:200],
        content=body.content or "",
        owner_id=user.id,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return doc_out(d, db, user, full=True)


@app.get("/api/docs/{doc_id}")
def read_doc(doc_id: int, db=Depends(get_db), user=Depends(current_user)):
    d, _ = get_doc(db, doc_id, user)
    return doc_out(d, db, user, full=True)


@app.put("/api/docs/{doc_id}")
def update_doc(doc_id: int, body: DocIn, db=Depends(get_db), user=Depends(current_user)):
    d, is_owner = get_doc(db, doc_id, user)
    if body.title is not None:
        if not body.title.strip():
            raise HTTPException(400, "Title cannot be empty")
        d.title = body.title.strip()[:200]
    if body.content is not None:
        d.content = body.content
    d.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "updated_at": d.updated_at.isoformat()}


@app.post("/api/docs/{doc_id}/share")
def share_doc(doc_id: int, body: ShareIn, db=Depends(get_db), user=Depends(current_user)):
    d, is_owner = get_doc(db, doc_id, user)
    if not is_owner:
        raise HTTPException(403, "Only owner can share")
    target = db.query(User).filter_by(username=body.username.strip().lower()).first()
    if not target:
        raise HTTPException(404, "User not found")
    if target.id == user.id:
        raise HTTPException(400, "You already own this")
    if not db.query(Share).filter_by(doc_id=d.id, user_id=target.id).first():
        db.add(Share(doc_id=d.id, user_id=target.id))
        db.commit()
    return {"ok": True}


MAX_SIZE = 2 * 1024 * 1024


@app.post("/api/upload")
async def upload(file: UploadFile = File(...), db=Depends(get_db), user=Depends(current_user)):
    name = file.filename or "upload"
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ("txt", "md", "docx"):
        raise HTTPException(400, "Only .txt, .md, .docx supported")
    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(400, "File too large (max 2MB)")
    try:
        if ext == "docx":
            content = mammoth.convert_to_html(io.BytesIO(data)).value
        elif ext == "md":
            content = markdown.markdown(data.decode("utf-8", errors="replace"))
        else:
            text = data.decode("utf-8", errors="replace")
            content = "".join(
                f"<p>{html.escape(l)}</p>" for l in text.splitlines() if l.strip()
            )
    except Exception:
        raise HTTPException(400, "Could not read this file")
    d = Doc(title=name.rsplit(".", 1)[0][:200], content=content, owner_id=user.id)
    db.add(d)
    db.commit()
    db.refresh(d)
    return doc_out(d, db, user, full=True)


dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(dist):
    app.mount("/", StaticFiles(directory=dist, html=True), name="static")