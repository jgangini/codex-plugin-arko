import { useState } from "react";
import { FeatureView } from "./features/notes/View";

export function App() {
  const [token, setToken] = useState("");
  return <main aria-label="Notes acceptance example">
    <h1>Notes — acceptance example</h1>
    <p>Ephemeral data. Enter the local API token; it stays in memory.</p>
    <label>API token<input type="password" autoComplete="off" value={token} onChange={e => setToken(e.target.value)} /></label>
    <FeatureView token={token} />
  </main>;
}
