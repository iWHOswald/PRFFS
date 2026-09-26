import { useEffect, useState } from "react";
import { AlertTriangle, Landmark, Medal, Scale, Shield, TrendingDown, TrendingUp, Users } from "lucide-react";
import {
  api,
  type BenchBlunder,
  type DraftPick,
  type HistorySummary,
  type PlayerGame,
  type PlayerTotal,
  type PlayoffJusticeBeneficiary,
  type PlayoffJusticeSeason,
  type PlayoffJusticeSnub,
  type PlayoffJusticeTeam,
  type WeeklyResult
} from "../lib/api";

type HistoryTab = "top" | "worst" | "divisions" | "playoffs" | "players" | "blunders";

const emptyHistory: HistorySummary = {
  overview: {
    season_years: [],
    draft_years: [],
    team_week_rows: 0,
    regular_team_week_rows: 0,
    playoff_team_week_rows: 0,
    draft_picks: 0
  },
  game_records: {
    highest_scores: [],
    lowest_scores: [],
    largest_margins: [],
    worst_losses: [],
    best_regular_seasons: [],
    worst_regular_seasons: [],
    owner_totals: []
  },
  playoff_records: {
    highest_scores: [],
    lowest_scores: [],
    largest_margins: [],
    owner_totals: []
  },
  division_records: {
    owner_totals: [],
    season_totals: []
  },
  playoff_justice: {
    seasons: [],
    biggest_snubs: [],
    biggest_beneficiaries: []
  },
  player_records: {
    best_player_games: [],
    worst_starter_games: [],
    best_player_totals: [],
    best_player_averages: []
  },
  blunder_records: {
    bench_blunders: [],
    costly_bench_blunders: []
  },
  side_point_records: {
    owner_totals: []
  },
  draft_records: {
    biggest_buys: [],
    best_values: [],
    most_points: [],
    owner_value: []
  }
};

export function LeagueHistory() {
  const [history, setHistory] = useState<HistorySummary>(emptyHistory);
  const [tab, setTab] = useState<HistoryTab>("top");

  useEffect(() => {
    api.historySummary().then(setHistory).catch(() => setHistory(emptyHistory));
  }, []);

  return (
    <section className="history-section" id="history">
      <div className="section-heading">
        <div>
          <span className="eyebrow">All Time</span>
          <h2>League History</h2>
        </div>
        <div className="status-pill">
          <Landmark size={17} />
          <span>{history.overview.season_years[0] ?? ""}-{history.overview.season_years.at(-1) ?? ""}</span>
        </div>
      </div>

      <section className="summary-grid">
        <HistoryStat label="Game Rows" value={String(history.overview.team_week_rows)} tone="good" />
        <HistoryStat label="Playoff Rows" value={String(history.overview.playoff_team_week_rows)} tone="neutral" />
        <HistoryStat label="Draft Picks" value={String(history.overview.draft_picks)} tone="neutral" />
      </section>

      <div className="history-tabs" role="tablist" aria-label="League history views">
        <TabButton active={tab === "top"} onClick={() => setTab("top")} icon={<TrendingUp size={16} />} label="Top" />
        <TabButton active={tab === "worst"} onClick={() => setTab("worst")} icon={<TrendingDown size={16} />} label="Worst" />
        <TabButton active={tab === "divisions"} onClick={() => setTab("divisions")} icon={<Users size={16} />} label="Divisions" />
        <TabButton active={tab === "playoffs"} onClick={() => setTab("playoffs")} icon={<Scale size={16} />} label="Playoff Justice" />
        <TabButton active={tab === "players"} onClick={() => setTab("players")} icon={<Medal size={16} />} label="Players" />
        <TabButton active={tab === "blunders"} onClick={() => setTab("blunders")} icon={<AlertTriangle size={16} />} label="Blunders" />
      </div>

      {tab === "top" ? <TopHistory history={history} /> : null}
      {tab === "worst" ? <WorstHistory history={history} /> : null}
      {tab === "divisions" ? <DivisionHistory history={history} /> : null}
      {tab === "playoffs" ? <PlayoffJusticeHistory history={history} /> : null}
      {tab === "players" ? <PlayerHistory history={history} /> : null}
      {tab === "blunders" ? <BlunderHistory history={history} /> : null}
    </section>
  );
}

function TopHistory({ history }: { history: HistorySummary }) {
  return (
    <>
      <section className="records-grid">
        <GameRecordTable title="Highest Scores" rows={history.game_records.highest_scores} metric="weekly_points" tone="good" />
        <GameRecordTable title="Largest Margins" rows={history.game_records.largest_margins} metric="plus_minus" tone="good" />
      </section>
      <section className="records-grid">
        <SeasonTable title="Best Regular Seasons" rows={history.game_records.best_regular_seasons.slice(0, 8)} tone="good" />
        <OwnerTotalTable title="Side Point Kings" rows={history.side_point_records.owner_totals.slice(0, 8)} />
      </section>
      <section className="records-grid">
        <GameRecordTable title="Playoff High Scores" rows={history.playoff_records.highest_scores} metric="weekly_points" tone="good" />
        <DraftRecordTable title="Draft Steals" rows={history.draft_records.best_values.slice(0, 8)} metric="dollar_value" tone="good" />
      </section>
    </>
  );
}

function WorstHistory({ history }: { history: HistorySummary }) {
  return (
    <>
      <section className="records-grid">
        <GameRecordTable title="Lowest Scores" rows={history.game_records.lowest_scores} metric="weekly_points" tone="bad" />
        <GameRecordTable title="Worst Losses" rows={history.game_records.worst_losses} metric="plus_minus" tone="bad" />
      </section>
      <section className="records-grid">
        <SeasonTable title="Lowest Regular Seasons" rows={(history.game_records.worst_regular_seasons ?? []).slice(0, 8)} tone="bad" />
        <GameRecordTable title="Playoff Lows" rows={history.playoff_records.lowest_scores ?? []} metric="weekly_points" tone="bad" />
      </section>
      <section className="records-grid">
        <DraftRecordTable title="Biggest Draft Burns" rows={history.draft_records.biggest_buys.slice(0, 8)} metric="bid_amount" tone="bad" />
        <PlayerGameTable title="Worst Starter Games" rows={(history.player_records.worst_starter_games ?? []).slice(0, 8)} tone="bad" />
      </section>
    </>
  );
}

function DivisionHistory({ history }: { history: HistorySummary }) {
  return (
    <section className="records-grid">
      <DivisionOwnerTable rows={(history.division_records.owner_totals ?? []).slice(0, 12)} />
      <DivisionSeasonTable rows={(history.division_records.season_totals ?? []).slice(0, 12)} />
    </section>
  );
}

function PlayoffJusticeHistory({ history }: { history: HistorySummary }) {
  const seasons = history.playoff_justice?.seasons ?? [];
  const latest = seasons.at(-1);
  const snubYears = seasons.filter((season) => season.snubs.length).length;
  const beneficiaryYears = seasons.filter((season) => season.beneficiaries.length).length;
  return (
    <>
      <section className="summary-grid">
        <HistoryStat label="Snub Seasons" value={String(snubYears)} tone={snubYears ? "bad" : "good"} />
        <HistoryStat label="Bypass Years" value={String(beneficiaryYears)} tone={beneficiaryYears ? "blunder" : "good"} />
        <HistoryStat label="Latest Slots" value={String(latest?.playoff_slots ?? 0)} tone="neutral" />
      </section>
      <section className="records-grid">
        <PlayoffSnubTable rows={(history.playoff_justice?.biggest_snubs ?? []).slice(0, 8)} />
        <PlayoffBeneficiaryTable rows={(history.playoff_justice?.biggest_beneficiaries ?? []).slice(0, 8)} />
      </section>
      <section className="records-grid">
        <PlayoffSeasonTable rows={seasons.slice().reverse().slice(0, 8)} />
        <PlayoffQualifierTable title="Latest Actual Playoff Field" rows={latest?.actual_playoff_teams ?? []} />
      </section>
    </>
  );
}

function PlayerHistory({ history }: { history: HistorySummary }) {
  return (
    <>
      <section className="records-grid">
        <PlayerGameTable title="Best Player Games" rows={(history.player_records.best_player_games ?? []).slice(0, 8)} tone="good" />
        <PlayerTotalTable title="Best Player Totals" rows={(history.player_records.best_player_totals ?? []).slice(0, 8)} />
      </section>
      <section className="records-grid">
        <PlayerTotalTable title="Best Player Averages" rows={(history.player_records.best_player_averages ?? []).slice(0, 8)} />
        <DraftRecordTable title="Drafted Point Monsters" rows={history.draft_records.most_points.slice(0, 8)} metric="total_points" tone="good" />
      </section>
    </>
  );
}

function BlunderHistory({ history }: { history: HistorySummary }) {
  return (
    <section className="records-grid">
      <BenchBlunderTable title="Costly Bench Blunders" rows={(history.blunder_records.costly_bench_blunders ?? []).slice(0, 10)} />
      <BenchBlunderTable title="Largest Bench Scores" rows={(history.blunder_records.bench_blunders ?? []).slice(0, 10)} />
    </section>
  );
}

function TabButton({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) {
  return (
    <button className={active ? "is-active" : ""} onClick={onClick} type="button">
      {icon}
      <span>{label}</span>
    </button>
  );
}

function HistoryStat({ label, value, tone }: { label: string; value: string; tone: "good" | "bad" | "neutral" | "blunder" }) {
  return (
    <section className={`summary-panel tone-${tone}`}>
      <Medal size={20} />
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </section>
  );
}

function ToneBadge({ tone }: { tone: "good" | "bad" | "blunder" | "neutral" }) {
  const label = tone === "good" ? "good" : tone === "bad" ? "bad" : tone === "blunder" ? "blunder" : "record";
  return <span className={`tone-badge tone-${tone}`}>{label}</span>;
}

function GameRecordTable({ title, rows, metric, tone }: { title: string; rows: WeeklyResult[]; metric: "weekly_points" | "plus_minus"; tone: "good" | "bad" }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
        {title.includes("Playoff") ? <Shield size={18} /> : <ToneBadge tone={tone} />}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Owner</th>
              <th>Week</th>
              <th>Phase</th>
              <th>{metric === "weekly_points" ? "Pts" : "+/-"}</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 8).map((row) => (
              <tr key={`${title}-${row.year}-${row.week}-${row.team_id}`}>
                <td>{row.owner}</td>
                <td>{row.year}.{row.week}</td>
                <td>{row.season_phase ?? "regular"}</td>
                <td className={`number text-${tone}`}>{row[metric].toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function SeasonTable({ title, rows, tone }: { title: string; rows: HistorySummary["game_records"]["best_regular_seasons"]; tone: "good" | "bad" }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
        <ToneBadge tone={tone} />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Owner</th>
              <th>Year</th>
              <th>Record</th>
              <th>Pts</th>
              <th>Avg</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${row.year}-${row.team_id}`}>
                <td>{row.owner}</td>
                <td>{row.year}</td>
                <td>{row.wins}-{row.losses}-{row.ties}</td>
                <td className={`number text-${tone}`}>{row.points.toFixed(2)}</td>
                <td className="number">{row.average.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function OwnerTotalTable({ title, rows }: { title: string; rows: { owner: string; points: number; awards: number }[] }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
        <ToneBadge tone="good" />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Owner</th>
              <th>Awards</th>
              <th>Pts</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.owner}>
                <td>{row.owner}</td>
                <td>{row.awards}</td>
                <td className="number text-good">{row.points.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function DraftRecordTable({ title, rows, metric, tone }: { title: string; rows: DraftPick[]; metric: "dollar_value" | "bid_amount" | "total_points"; tone: "good" | "bad" }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
        <ToneBadge tone={tone} />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Player</th>
              <th>Year</th>
              <th>Owner</th>
              <th>{metric === "bid_amount" ? "Bid" : metric === "total_points" ? "Pts" : "Value"}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${title}-${row.year}-${row.position_drafted}`}>
                <td>{row.player_name}</td>
                <td>{row.year}</td>
                <td>{row.owner}</td>
                <td className={`number text-${tone}`}>
                  {metric === "bid_amount" ? `$${row.bid_amount.toFixed(0)}` : metric === "total_points" ? row.total_points.toFixed(1) : (row.dollar_value?.toFixed(2) ?? "-")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function PlayoffSnubTable({ rows }: { rows: PlayoffJusticeSnub[] }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Biggest Points Snubs</h2>
        <ToneBadge tone="bad" />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Owner</th>
              <th>Year</th>
              <th>Pts Rank</th>
              <th>Pts</th>
              <th>Gap</th>
              <th>Lost To</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`snub-${row.year}-${row.team_id}`}>
                <td>{row.owner}</td>
                <td>{row.year}</td>
                <td>{row.points_rank}</td>
                <td className="number text-bad">{row.regular_points.toFixed(2)}</td>
                <td className="number text-bad">{row.points_gap.toFixed(2)}</td>
                <td>{row.replaced_by_owner ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function PlayoffBeneficiaryTable({ rows }: { rows: PlayoffJusticeBeneficiary[] }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Biggest Playoff Beneficiaries</h2>
        <ToneBadge tone="blunder" />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Owner</th>
              <th>Year</th>
              <th>Type</th>
              <th>Pts Rank</th>
              <th>Pts</th>
              <th>Gap</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`beneficiary-${row.year}-${row.team_id}`}>
                <td>{row.owner}</td>
                <td>{row.year}</td>
                <td>{row.label}</td>
                <td>{row.points_rank}</td>
                <td className="number text-blunder">{row.regular_points.toFixed(2)}</td>
                <td className="number text-blunder">{row.points_gap.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function PlayoffSeasonTable({ rows }: { rows: PlayoffJusticeSeason[] }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Year By Year Justice</h2>
        <Scale size={18} />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Year</th>
              <th>Slots</th>
              <th>Snubs</th>
              <th>Beneficiaries</th>
              <th>Worst Gap</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const worstGap = Math.max(0, ...row.snubs.map((snub) => snub.points_gap));
              return (
                <tr key={`justice-${row.year}`}>
                  <td>{row.year}</td>
                  <td>{row.playoff_slots}</td>
                  <td className={row.snubs.length ? "text-bad" : "text-good"}>{row.snubs.length}</td>
                  <td className={row.beneficiaries.length ? "text-blunder" : "text-good"}>{row.beneficiaries.length}</td>
                  <td className="number">{worstGap.toFixed(2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function PlayoffQualifierTable({ title, rows }: { title: string; rows: PlayoffJusticeTeam[] }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
        <Shield size={18} />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Owner</th>
              <th>Division</th>
              <th>Record</th>
              <th>Pts Rank</th>
              <th>Type</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`qualifier-${row.year}-${row.team_id}`}>
                <td>{row.owner}</td>
                <td>{row.division}</td>
                <td>{row.wins}-{row.losses}-{row.ties}</td>
                <td>{row.points_rank}</td>
                <td>
                  <span className={`tone-badge ${row.qualification_type === "division_winner" ? "tone-blunder" : "tone-neutral"}`}>
                    {row.qualification_type === "division_winner" ? "auto" : "wildcard"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function PlayerGameTable({ title, rows, tone }: { title: string; rows: PlayerGame[]; tone: "good" | "bad" }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
        <ToneBadge tone={tone} />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Player</th>
              <th>Owner</th>
              <th>Week</th>
              <th>Slot</th>
              <th>Pts</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${title}-${row.year}-${row.week}-${row.team_id}-${row.player_name}`}>
                <td>{row.player_name}</td>
                <td>{row.owner}</td>
                <td>{row.year}.{row.week}</td>
                <td>{row.slot_key}</td>
                <td className={`number text-${tone}`}>{row.points.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function PlayerTotalTable({ title, rows }: { title: string; rows: PlayerTotal[] }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
        <ToneBadge tone="good" />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Player</th>
              <th>Pos</th>
              <th>Starts</th>
              <th>Pts</th>
              <th>Avg</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${title}-${row.player_name}-${row.position}`}>
                <td>{row.player_name}</td>
                <td>{row.position}</td>
                <td>{row.starts}</td>
                <td className="number text-good">{row.points.toFixed(2)}</td>
                <td className="number">{row.average.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function BenchBlunderTable({ title, rows }: { title: string; rows: BenchBlunder[] }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
        <ToneBadge tone="blunder" />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Player</th>
              <th>Owner</th>
              <th>Week</th>
              <th>Bench</th>
              <th>Margin</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${title}-${row.year}-${row.week}-${row.team_id}-${row.player_name}`}>
                <td>{row.player_name}</td>
                <td>{row.owner}</td>
                <td>{row.year}.{row.week}</td>
                <td className="number text-blunder">{row.points.toFixed(2)}</td>
                <td className="number">{row.loss_margin !== null ? row.loss_margin.toFixed(2) : row.plus_minus.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function DivisionOwnerTable({ rows }: { rows: HistorySummary["division_records"]["owner_totals"] }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Division Owner Totals</h2>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Division</th>
              <th>Owner</th>
              <th>Games</th>
              <th>Pts</th>
              <th>Avg</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${row.division}-${row.owner}`}>
                <td>{row.division}</td>
                <td>{row.owner}</td>
                <td>{row.games}</td>
                <td className="number">{row.points.toFixed(2)}</td>
                <td className="number">{row.average.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function DivisionSeasonTable({ rows }: { rows: HistorySummary["division_records"]["season_totals"] }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Division Season Peaks</h2>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Division</th>
              <th>Owner</th>
              <th>Year</th>
              <th>Pts</th>
              <th>Avg</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${row.division}-${row.year}-${row.team_id}`}>
                <td>{row.division}</td>
                <td>{row.owner}</td>
                <td>{row.year}</td>
                <td className="number">{row.points.toFixed(2)}</td>
                <td className="number">{row.average.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
