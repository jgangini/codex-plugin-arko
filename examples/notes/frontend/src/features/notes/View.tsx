import { useState, type FormEvent } from "react";
import { createItem } from "./api";

export function FeatureView({ token }: { token: string }) {
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState(3);
  const [status, setStatus] = useState("");
  const [pending, setPending] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    try {
      const item = await createItem(token, { title, priority });
      setStatus(`Created: ${item.title}`);
    } catch { setStatus("Could not create item"); }
    finally { setPending(false); }
  }
  return <form onSubmit={submit}>
    <label>Title<input required maxLength={120} value={title} onChange={e => setTitle(e.target.value)} /></label>
    <label>Priority<input type="number" required min={1} max={5} step={1} value={priority} onChange={e => setPriority(e.target.valueAsNumber)} /></label>
    <button disabled={pending || !title.trim()}>Create</button>
    <p role="status">{status}</p>
  </form>;
}
