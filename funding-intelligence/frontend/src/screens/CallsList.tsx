// Lista de apeluri (dashboard). Tabel banal — nu e diferențiatorul produsului.
// TODO: filtre status, sortare deadline, badge „modificat recent".
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../api/client";

type CallItem = {
  id: number;
  title: string;
  program: string | null;
  status: string;
  deadline_submission: string | null;
  last_changed_at: string | null;
};

type Paginated = { items: CallItem[]; next_cursor: number | null };

export function CallsList({ onSelect }: { onSelect: (id: number) => void }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["calls"],
    queryFn: () => apiGet<Paginated>("/calls"),
  });

  if (isLoading) return <p>Se încarcă…</p>;
  if (error) return <p>Eroare la încărcarea apelurilor.</p>;

  return (
    <table cellPadding={6}>
      <thead>
        <tr>
          <th>Titlu</th>
          <th>Program</th>
          <th>Status</th>
          <th>Deadline</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {data?.items.map((c) => (
          <tr key={c.id}>
            <td>{c.title}</td>
            <td>{c.program ?? "—"}</td>
            <td>{c.status}</td>
            <td>{c.deadline_submission ?? "—"}</td>
            <td>
              <button onClick={() => onSelect(c.id)}>Validează</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
