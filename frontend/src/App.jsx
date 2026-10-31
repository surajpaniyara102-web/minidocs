import { useState, useEffect, useRef } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import "./App.css";

async function api(path, user, opts = {}) {
  const headers = { "X-Username": user || "" };
  if (opts.body && !(opts.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const r = await fetch("/api" + path, { ...opts, headers });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || "Something went wrong");
  return data;
}

function Login({ onLogin }) {
  const [name, setName] = useState("");
  const [err, setErr] = useState("");
  const go = async (n) => {
    try {
      const u = await api("/login", "", {
        method: "POST",
        body: JSON.stringify({ username: n }),
      });
      onLogin(u.username);
    } catch (e) {
      setErr(e.message);
    }
  };
  return (
    <div className="card">
      <h2>Login</h2>
      <p>Demo users (no password):</p>
      {["alice", "bob", "carol"].map((n) => (
        <button key={n} onClick={() => go(n)}>{n}</button>
      ))}
      <div>
        <input placeholder="username" value={name} onChange={(e) => setName(e.target.value)} />
        <button onClick={() => go(name)}>Login</button>
      </div>
      {err && <p className="err">{err}</p>}
    </div>
  );
}

function Dashboard({ user, open }) {
  const [docs, setDocs] = useState({ owned: [], shared: [] });
  const [err, setErr] = useState("");
  const load = () => api("/docs", user).then(setDocs).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);

  const create = async () => {
    const d = await api("/docs", user, {
      method: "POST",
      body: JSON.stringify({ title: "Untitled" }),
    });
    open(d.id);
  };

  const upload = async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    const fd = new FormData();
    fd.append("file", f);
    try {
      const d = await api("/upload", user, { method: "POST", body: fd });
      open(d.id);
    } catch (e2) {
      setErr(e2.message);
    }
  };

  const List = ({ items }) =>
    items.length === 0 ? (
      <p className="muted">Nothing here yet</p>
    ) : (
      items.map((d) => (
        <div key={d.id} className="row" onClick={() => open(d.id)}>
          <b>{d.title}</b>
          <span className="muted">
            {d.is_owner ? "Owned by you" : `Shared by ${d.owner}`} ·{" "}
            {new Date(d.updated_at + "Z").toLocaleString()}
          </span>
        </div>
      ))
    );

  return (
    <div>
      <div className="bar">
        <button onClick={create}>+ New document</button>
        <label className="btn">
          Upload (.txt .md .docx)
          <input type="file" accept=".txt,.md,.docx" hidden onChange={upload} />
        </label>
      </div>
      {err && <p className="err">{err}</p>}
      <h3>My documents</h3>
      <List items={docs.owned} />
      <h3>Shared with me</h3>
      <List items={docs.shared} />
    </div>
  );
}

function Editor({ user, id, back }) {
  const [doc, setDoc] = useState(null);
  const [title, setTitle] = useState("");
  const [status, setStatus] = useState("Saved");
  const [err, setErr] = useState("");
  const [shareTo, setShareTo] = useState("");
  const [msg, setMsg] = useState("");
  const timer = useRef(null);

  const editor = useEditor({
    extensions: [StarterKit, Underline],
    content: "",
    onUpdate: ({ editor }) => {
      setStatus("Saving...");
      clearTimeout(timer.current);
      timer.current = setTimeout(async () => {
        try {
          await api(`/docs/${id}`, user, {
            method: "PUT",
            body: JSON.stringify({ content: editor.getHTML() }),
          });
          setStatus("Saved");
        } catch (e) {
          setStatus("Save failed");
          setErr(e.message);
        }
      }, 800);
    },
  });

  useEffect(() => {
    if (!editor) return;
    api(`/docs/${id}`, user)
      .then((d) => {
        setDoc(d);
        setTitle(d.title);
        editor.commands.setContent(d.content, false);
      })
      .catch((e) => setErr(e.message));
  }, [id, editor]);

  const saveTitle = async () => {
    try {
      await api(`/docs/${id}`, user, {
        method: "PUT",
        body: JSON.stringify({ title }),
      });
      setErr("");
    } catch (e) {
      setErr(e.message);
    }
  };

  const share = async () => {
    try {
      await api(`/docs/${id}/share`, user, {
        method: "POST",
        body: JSON.stringify({ username: shareTo }),
      });
      setMsg(`Shared with ${shareTo}`);
      setShareTo("");
    } catch (e) {
      setMsg(e.message);
    }
  };

  if (err && !doc)
    return (
      <div>
        <button onClick={back}>← Back</button>
        <p className="err">{err}</p>
      </div>
    );
  if (!doc) return <p>Loading...</p>;

  const Btn = ({ label, on, active }) => (
    <button
      className={active ? "active" : ""}
      onMouseDown={(e) => { e.preventDefault(); on(); }}
    >
      {label}
    </button>
  );
  const c = () => editor.chain().focus();

  return (
    <div>
      <button onClick={back}>← Back</button>
      <input
        className="title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        onBlur={saveTitle}
      />
      <span className="muted">
        {" "}{status} · {doc.is_owner ? "You own this" : `Shared by ${doc.owner}`}
      </span>
      {err && <p className="err">{err}</p>}
      {editor && (
        <div className="toolbar">
          <Btn label="B" on={() => c().toggleBold().run()} active={editor.isActive("bold")} />
          <Btn label="I" on={() => c().toggleItalic().run()} active={editor.isActive("italic")} />
          <Btn label="U" on={() => c().toggleUnderline().run()} active={editor.isActive("underline")} />
          <Btn label="H1" on={() => c().toggleHeading({ level: 1 }).run()} active={editor.isActive("heading", { level: 1 })} />
          <Btn label="H2" on={() => c().toggleHeading({ level: 2 }).run()} active={editor.isActive("heading", { level: 2 })} />
          <Btn label="• List" on={() => c().toggleBulletList().run()} active={editor.isActive("bulletList")} />
          <Btn label="1. List" on={() => c().toggleOrderedList().run()} active={editor.isActive("orderedList")} />
        </div>
      )}
      <EditorContent editor={editor} className="editor" />
      {doc.is_owner && (
        <div className="share">
          <input
            placeholder="username to share with"
            value={shareTo}
            onChange={(e) => setShareTo(e.target.value)}
          />
          <button onClick={share}>Share</button>{" "}
          <span className="muted">{msg}</span>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(localStorage.getItem("user"));
  const [docId, setDocId] = useState(null);
  const login = (u) => { localStorage.setItem("user", u); setUser(u); };
  const logout = () => { localStorage.removeItem("user"); setUser(null); setDocId(null); };

  return (
    <div className="app">
      <header>
        <h1>MiniDocs</h1>
        {user && (
          <span>
            👤 {user} <button onClick={logout}>Logout</button>
          </span>
        )}
      </header>
      {!user ? (
        <Login onLogin={login} />
      ) : docId ? (
        <Editor user={user} id={docId} back={() => setDocId(null)} />
      ) : (
        <Dashboard user={user} open={setDocId} />
      )}
    </div>
  );
}