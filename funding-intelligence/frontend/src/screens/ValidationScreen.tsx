// ECRANUL DE VALIDARE — cel mai important UI din produs (Ghid Tehnic §4.3).
// Ținta de <10 min/ghid se câștigă sau se pierde aici.
//
// Split-view: stânga câmpurile extrase (cu confidence + marcaj „nevalidat"),
// dreapta PDF-ul scrollat automat la pagina-sursă a câmpului selectat.
// Acțiuni: confirmă / corectează / respinge — navigabile din tastatură.
//
// TODO (sesiunea de implementare):
// - viewer PDF (react-pdf) care sare la source_page la selectarea unui câmp
// - navigare cu tastatura (↑/↓ între câmpuri, Enter=confirmă, etc.)
// - marcaj vizual distinct pentru validation_status === "auto" (nevalidat)
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../api/client";

type Criterion = {
  id: number;
  field_name: string;
  value: unknown;
  confidence: number | null;
  source_page: number | null;
  source_quote: string | null;
  validation_status: "auto" | "validated" | "corrected" | "rejected";
};

export function ValidationScreen({
  callId,
  onBack,
}: {
  callId: number;
  onBack: () => void;
}) {
  const { data, isLoading } = useQuery({
    queryKey: ["criteria", callId],
    queryFn: () => apiGet<Criterion[]>(`/validation/${callId}/criteria`),
  });

  return (
    <div>
      <button onClick={onBack}>← Înapoi la listă</button>
      <div style={{ display: "flex", gap: 16, marginTop: 12 }}>
        {/* Stânga: câmpurile extrase */}
        <div style={{ flex: 1 }}>
          <h3>Câmpuri extrase</h3>
          {isLoading && <p>Se încarcă…</p>}
          {data?.map((c) => (
            <div
              key={c.id}
              style={{
                border: "1px solid #ddd",
                padding: 8,
                marginBottom: 8,
                // Marcaj „nevalidat" pentru datele propuse de AI.
                background: c.validation_status === "auto" ? "#fff8e1" : "#fff",
              }}
            >
              <strong>{c.field_name}</strong>{" "}
              {c.validation_status === "auto" && (
                <span style={{ color: "#b26a00" }}>(nevalidat)</span>
              )}
              <div>Valoare: {JSON.stringify(c.value)}</div>
              <div>
                Confidence: {c.confidence ?? "—"} · pag. {c.source_page ?? "—"}
              </div>
              {/* TODO: butoane confirmă / corectează / respinge → POST /validation/criteria/:id */}
            </div>
          ))}
        </div>
        {/* Dreapta: viewer PDF (placeholder) */}
        <div style={{ flex: 1, borderLeft: "1px solid #eee", paddingLeft: 16 }}>
          <h3>Document sursă</h3>
          <p style={{ color: "#888" }}>
            TODO: viewer PDF care sare la pagina-sursă a câmpului selectat.
          </p>
        </div>
      </div>
    </div>
  );
}
