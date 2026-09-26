import { useEffect, useMemo, useState } from "react";
import { BadgeDollarSign, ClipboardList } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from "recharts";
import { api, type DraftPick, type DraftProjectedValue, type DraftSpenderPcaPoint, type DraftStrategyCorrelation, type DraftStrategyOutcomeRow, type DraftStrategyProfile, type DraftSummary } from "../lib/api";

type Props = {
  selectedYear?: number | "all-time" | "current" | "draft" | "admin" | "office" | "story";
};

const emptySummary: DraftSummary = {
  years: [],
  by_owner: [],
  by_position: [],
  top_values: [],
  biggest_buys: [],
  projected_best_values: [],
  spender_pca: [],
  strategy_profiles: [],
  strategy_history: [],
  strategy_outcomes: {
    rows: [],
    completed_rows: [],
    correlations: [],
    by_type: []
  }
};

export function DraftReview({ selectedYear }: Props) {
  const [draftYear, setDraftYear] = useState<number>();
  const [summary, setSummary] = useState<DraftSummary>(emptySummary);
  const [picks, setPicks] = useState<DraftPick[]>([]);
  const [selectedOwner, setSelectedOwner] = useState("");

  useEffect(() => {
    api.draftSummary().then((data) => {
      setSummary({ ...emptySummary, years: data.years });
      setDraftYear(typeof selectedYear === "number" && data.years.includes(selectedYear) ? selectedYear : data.years.at(-1));
    }).catch(() => {
      setSummary(emptySummary);
      setDraftYear(undefined);
    });
  }, [selectedYear]);

  useEffect(() => {
    if (!draftYear) return;
    Promise.all([api.draftSummary(draftYear), api.draftPicks(draftYear)]).then(([nextSummary, nextPicks]) => {
      setSummary(nextSummary);
      setPicks(nextPicks);
      setSelectedOwner((current) => current && nextSummary.strategy_profiles.some((row) => row.owner === current) ? current : nextSummary.strategy_profiles[0]?.owner ?? "");
    }).catch(() => {
      setSummary(emptySummary);
      setPicks([]);
    });
  }, [draftYear]);

  const selectedOwnerHistory = useMemo(
    () => summary.strategy_history.filter((row) => row.owner === selectedOwner).sort((a, b) => a.year - b.year),
    [selectedOwner, summary.strategy_history]
  );
  const selectedOwnerOutcomes = useMemo(
    () => summary.strategy_outcomes.rows.filter((row) => row.owner === selectedOwner).sort((a, b) => a.year - b.year),
    [selectedOwner, summary.strategy_outcomes.rows]
  );

  return (
    <section className="draft-section" id="draft">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Auction History</span>
          <h2>Draft Review</h2>
        </div>
        <div className="control-group compact-control">
          <ClipboardList size={18} />
          <select value={draftYear ?? ""} onChange={(event) => setDraftYear(Number(event.target.value))}>
            {summary.years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>
      </div>

      <section className="chart-grid">
        <DraftChart title="Spend By Owner" data={summary.by_owner.slice(0, 12).map((row) => ({ name: row.owner.split(" ")[0], spent: row.spent }))} />
        <DraftChart title="Spend By Position" data={summary.by_position.map((row) => ({ name: row.position, spent: row.spent }))} />
      </section>

      <StrategyProfiles profiles={summary.strategy_profiles} />

      <section className="chart-grid">
        <SpenderPcaPlot rows={summary.spender_pca} />
        <OwnerStrategyHistory owner={selectedOwner} owners={summary.strategy_profiles.map((row) => row.owner)} rows={selectedOwnerHistory} outcomeRows={selectedOwnerOutcomes} setOwner={setSelectedOwner} />
      </section>

      <section className="chart-grid">
        <StrategyOutcomePanel rows={summary.strategy_outcomes.by_type} />
        <CorrelationPanel rows={summary.strategy_outcomes.correlations.slice(0, 8)} />
      </section>

      <section className="records-grid">
        <ProjectedValueTable rows={summary.projected_best_values.slice(0, 12)} />
        <DraftTable title="Biggest Buys" rows={summary.biggest_buys.slice(0, 8)} metric="bid_amount" />
      </section>

      <section className="records-grid">
        <DraftTable title="Top Values" rows={summary.top_values.slice(0, 8)} metric="dollar_value" />
      </section>

      <section className="wide-panel">
        <div className="panel-heading">
          <h2>Draft Board</h2>
          <BadgeDollarSign size={18} />
        </div>
        <div className="table-wrap draft-board">
          <table>
            <thead>
              <tr>
                <th>Pick</th>
                <th>Player</th>
                <th>Pos</th>
                <th>Owner</th>
                <th>Bid</th>
                <th>Pts</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {picks.map((pick) => (
                <tr key={`${pick.year}-${pick.position_drafted}`}>
                  <td>{pick.position_drafted}</td>
                  <td>{pick.player_name}</td>
                  <td>{pick.position ?? ""}</td>
                  <td>{pick.owner}</td>
                  <td className="number">${pick.bid_amount.toFixed(0)}</td>
                  <td className="number">{pick.total_points.toFixed(1)}</td>
                  <td className="number">{pick.dollar_value?.toFixed(2) ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  );
}

function DraftChart({ title, data }: { title: string; data: { name: string; spent: number }[] }) {
  return (
    <section className="panel chart-panel">
      <div className="panel-heading">
        <h2>{title}</h2>
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 26, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" angle={-35} textAnchor="end" interval={0} height={60} tick={{ fontSize: 12 }} />
          <YAxis />
          <Tooltip />
          <Bar dataKey="spent" fill="#7a5c99" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}

function DraftTable({ title, rows, metric }: { title: string; rows: DraftPick[]; metric: "dollar_value" | "bid_amount" }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Player</th>
              <th>Owner</th>
              <th>Pos</th>
              <th>{metric === "bid_amount" ? "Bid" : "Value"}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${title}-${row.year}-${row.position_drafted}`}>
                <td>{row.player_name}</td>
                <td>{row.owner}</td>
                <td>{row.position ?? ""}</td>
                <td className="number">{metric === "bid_amount" ? `$${row.bid_amount.toFixed(0)}` : (row.dollar_value?.toFixed(2) ?? "-")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ProjectedValueTable({ rows }: { rows: DraftProjectedValue[] }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Projected Best Values</h2>
      </div>
      <p className="panel-note">Projected value estimates expected points from historical outcomes for similar position and bid tiers.</p>
      <div className="table-wrap draft-analysis-table">
        <table>
          <thead>
            <tr>
              <th>Player</th>
              <th>Owner</th>
              <th>Pos</th>
              <th>Bid</th>
              <th>Proj Pts</th>
              <th>Proj Value</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`projected-${row.year}-${row.position_drafted}`}>
                <td>
                  <strong>{row.player_name}</strong>
                  <span>{row.projection_basis}</span>
                </td>
                <td>{row.owner}</td>
                <td>{row.position ?? ""}</td>
                <td className="number">${row.bid_amount.toFixed(0)}</td>
                <td className="number">{row.projected_points.toFixed(1)}</td>
                <td className="number">{row.projected_value.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function SpenderPcaPlot({ rows }: { rows: DraftSpenderPcaPoint[] }) {
  const labels = uniqueOwnerLabels(rows);
  return (
    <section className="panel chart-panel">
      <div className="panel-heading">
        <h2>Strategy Map</h2>
      </div>
      <p className="panel-note">Owners farther apart drafted differently by top-heavy spending, patience, balance, and position lean.</p>
      <ResponsiveContainer width="100%" height={310}>
        <ScatterChart margin={{ top: 12, right: 18, bottom: 26, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" dataKey="pc1" name="PC1" tick={{ fontSize: 12 }} />
          <YAxis type="number" dataKey="pc2" name="PC2" tick={{ fontSize: 12 }} />
          <ZAxis type="number" dataKey="spent" range={[90, 260]} />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            formatter={(value, name) => {
              if (name === "spent") return [`$${Number(value).toFixed(0)}`, "Spent"];
              return [Number(value).toFixed(2), String(name).toUpperCase()];
            }}
            labelFormatter={(_, payload) => {
              const row = payload?.[0]?.payload;
              return row ? `${row.owner} · ${row.strategy_type}` : "";
            }}
          />
          <Scatter data={rows} fill="#0f8b8d" shape={<OwnerDot />} />
        </ScatterChart>
      </ResponsiveContainer>
      <div className="pca-labels">
        {labels.map((row) => (
          <span key={row.owner}>{row.label}</span>
        ))}
      </div>
    </section>
  );
}

function uniqueOwnerLabels(rows: DraftSpenderPcaPoint[]) {
  const seen = new Set<string>();
  return rows.filter((row) => {
    if (seen.has(row.owner)) return false;
    seen.add(row.owner);
    return true;
  });
}

function StrategyProfiles({ profiles }: { profiles: DraftStrategyProfile[] }) {
  return (
    <section className="wide-panel">
      <div className="panel-heading">
        <h2>Draft Strategy Types</h2>
      </div>
      <div className="strategy-grid">
        {profiles.map((profile) => (
          <article className="strategy-card" key={`${profile.year}-${profile.owner}`}>
            <div>
              <span>{profile.strategy_type}</span>
              <strong>{profile.owner}</strong>
            </div>
            <dl>
              <div><dt>Top Heavy</dt><dd>{profile.top_heavy_score.toFixed(0)}</dd></div>
              <div><dt>Patience</dt><dd>{profile.patience_score.toFixed(0)}</dd></div>
              <div><dt>Balance</dt><dd>{profile.balance_score.toFixed(0)}</dd></div>
              <div><dt>Top 3</dt><dd>{pct(profile.top3_share)}</dd></div>
              <div><dt>$1 Picks</dt><dd>{profile.one_dollar_count}</dd></div>
              <div><dt>Avg Bid</dt><dd>${profile.avg_bid.toFixed(1)}</dd></div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}

function OwnerStrategyHistory({ owner, owners, rows, outcomeRows, setOwner }: { owner: string; owners: string[]; rows: DraftStrategyProfile[]; outcomeRows: DraftStrategyOutcomeRow[]; setOwner: (owner: string) => void }) {
  const chartRows = rows.map((row) => {
    const outcome = outcomeRows.find((item) => item.year === row.year);
    return { ...row, regular_points: outcome?.regular_points ?? null, points_rank: outcome?.points_rank ?? null };
  });
  return (
    <section className="panel chart-panel">
      <div className="panel-heading">
        <h2>Owner Fingerprint</h2>
        <select className="mini-select" value={owner} onChange={(event) => setOwner(event.target.value)}>
          {owners.map((item) => (
            <option key={item} value={item}>{item}</option>
          ))}
        </select>
      </div>
      <p className="panel-note">Compare one owner's strategy type against their previous drafts and season finish.</p>
      <ResponsiveContainer width="100%" height={310}>
        <LineChart data={chartRows} margin={{ top: 12, right: 18, bottom: 20, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="year" tick={{ fontSize: 12 }} />
          <YAxis yAxisId="strategy" domain={[0, 100]} tick={{ fontSize: 12 }} />
          <YAxis yAxisId="points" orientation="right" tick={{ fontSize: 12 }} />
          <Tooltip
            formatter={(value, name) => [Number(value).toFixed(name === "regular_points" ? 1 : 0), labelMetric(String(name))]}
            labelFormatter={(year) => {
              const row = chartRows.find((item) => item.year === Number(year));
              return row ? `${year} · ${row.strategy_type}${row.points_rank ? ` · Points rank ${row.points_rank}` : ""}` : String(year);
            }}
          />
          <Line yAxisId="strategy" type="monotone" dataKey="top_heavy_score" stroke="#7a5c99" strokeWidth={2.5} dot={{ r: 4 }} />
          <Line yAxisId="strategy" type="monotone" dataKey="patience_score" stroke="#0f8b8d" strokeWidth={2.5} dot={{ r: 4 }} />
          <Line yAxisId="strategy" type="monotone" dataKey="balance_score" stroke="#f2c14e" strokeWidth={2.5} dot={{ r: 4 }} />
          <Line yAxisId="points" type="monotone" dataKey="regular_points" stroke="#d1495b" strokeWidth={2.5} dot={{ r: 4 }} connectNulls />
        </LineChart>
      </ResponsiveContainer>
      <div className="pca-labels">
        <span>Top Heavy</span>
        <span>Patience</span>
        <span>Balance</span>
        <span>Season Points</span>
      </div>
    </section>
  );
}

function StrategyOutcomePanel({ rows }: { rows: DraftSummary["strategy_outcomes"]["by_type"] }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Strategy vs Results</h2>
      </div>
      <p className="panel-note">Completed seasons only. Lower average rank is better.</p>
      <div className="table-wrap draft-analysis-table">
        <table>
          <thead>
            <tr>
              <th>Type</th>
              <th>Seasons</th>
              <th>Avg Pts</th>
              <th>Win %</th>
              <th>Pts Rank</th>
              <th>Rec Rank</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.strategy_type}>
                <td><strong>{row.strategy_type}</strong></td>
                <td className="number">{row.seasons}</td>
                <td className="number">{row.avg_points.toFixed(1)}</td>
                <td className="number">{row.avg_win_pct.toFixed(3)}</td>
                <td className="number">{row.avg_points_rank.toFixed(2)}</td>
                <td className="number">{row.avg_record_rank.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function CorrelationPanel({ rows }: { rows: DraftStrategyCorrelation[] }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Strongest Signals</h2>
      </div>
      <p className="panel-note">Pearson correlation across owner-seasons with completed regular-season results.</p>
      <div className="correlation-list">
        {rows.map((row) => (
          <article key={`${row.metric}-${row.target}`}>
            <div>
              <strong>{labelMetric(row.metric)}</strong>
              <span>vs {labelMetric(row.target)} · {row.direction} · n={row.n}</span>
            </div>
            <em className={row.correlation >= 0 ? "is-positive" : "is-negative"}>{row.correlation.toFixed(2)}</em>
          </article>
        ))}
      </div>
    </section>
  );
}

function pct(value: number) {
  return `${Math.round(value * 100)}%`;
}

function labelMetric(metric: string) {
  if (metric === "top_heavy_score") return "Top Heavy";
  if (metric === "patience_score") return "Patience";
  if (metric === "balance_score") return "Balance";
  if (metric === "regular_points") return "Season Points";
  if (metric === "average") return "Avg Score";
  if (metric === "win_pct") return "Win %";
  if (metric === "points_rank") return "Points Rank";
  if (metric === "record_rank") return "Record Rank";
  if (metric === "top3_share") return "Top 3 Share";
  if (metric === "one_dollar_share") return "$1 Share";
  if (metric === "late_spend_share") return "Late Spend";
  if (metric === "rb_share") return "RB Share";
  if (metric === "wr_share") return "WR Share";
  return metric;
}

function OwnerDot(props: unknown) {
  const { cx, cy, fill } = props as { cx?: number; cy?: number; fill?: string };
  if (cx == null || cy == null) return null;
  return <circle cx={cx} cy={cy} r={6} fill={fill ?? "#0f8b8d"} stroke="#f8faf6" strokeWidth={2} />;
}
