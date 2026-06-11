// Navigație minimă între cele două ecrane MVP. Fără router la început — un state.
import { useState } from "react";
import { CallsList } from "./screens/CallsList";
import { ValidationScreen } from "./screens/ValidationScreen";

export function App() {
  const [selectedCallId, setSelectedCallId] = useState<number | null>(null);

  return (
    <div style={{ fontFamily: "system-ui", padding: 16 }}>
      <h1>Funding Intelligence — MVP</h1>
      {selectedCallId === null ? (
        <CallsList onSelect={setSelectedCallId} />
      ) : (
        <ValidationScreen
          callId={selectedCallId}
          onBack={() => setSelectedCallId(null)}
        />
      )}
    </div>
  );
}
