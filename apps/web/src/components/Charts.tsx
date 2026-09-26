import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SidePointAward, WeeklyResult } from "../lib/api";

type Props = {
  weeklyRows: WeeklyResult[];
  sidePoints: SidePointAward[];
};

export function Charts({ weeklyRows, sidePoints }: Props) {
  const weeklyData = weeklyRows
    .slice()
    .sort((a, b) => b.weekly_points - a.weekly_points)
    .map((row) => ({ owner: row.owner.split(" ")[0], points: row.weekly_points }));

  const sideTotals = Object.values(
    sidePoints.reduce<Record<string, { owner: string; points: number }>>((acc, award) => {
      acc[award.owner] ??= { owner: award.owner.split(" ")[0], points: 0 };
      acc[award.owner].points += award.points;
      return acc;
    }, {})
  ).sort((a, b) => b.points - a.points);

  return (
    <section className="chart-grid">
      <ChartPanel title="Weekly Points" data={weeklyData} dataKey="points" />
      <ChartPanel title="Side Points" data={sideTotals} dataKey="points" />
    </section>
  );
}

function ChartPanel({ title, data, dataKey }: { title: string; data: object[]; dataKey: string }) {
  return (
    <section className="panel chart-panel">
      <div className="panel-heading">
        <h2>{title}</h2>
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 26, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="owner" angle={-35} textAnchor="end" interval={0} height={60} tick={{ fontSize: 12 }} />
          <YAxis />
          <Tooltip />
          <Bar dataKey={dataKey} fill="#0f8b8d" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}
