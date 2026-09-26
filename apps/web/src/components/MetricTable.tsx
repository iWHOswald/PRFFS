import type { WeeklyResult } from "../lib/api";

type Props = {
  title: string;
  rows: WeeklyResult[];
  metric: "weekly_points" | "plus_minus";
};

export function MetricTable({ title, rows, metric }: Props) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Owner</th>
              <th>Week</th>
              <th>Team</th>
              <th>{metric === "weekly_points" ? "Pts" : "+/-"}</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 8).map((row) => (
              <tr key={`${title}-${row.year}-${row.week}-${row.team_id}`}>
                <td>{row.owner}</td>
                <td>
                  {row.year}.{row.week}
                </td>
                <td>{row.team_name}</td>
                <td className="number">{row[metric].toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
