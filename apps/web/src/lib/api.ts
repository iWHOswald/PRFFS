import { getAdminToken, setAdminToken } from "./adminSession";

export type Season = {
  league_id: number;
  year: number;
  source: string;
};

export type WeeklyResult = {
  league_id: number;
  year: number;
  week: number;
  season_phase?: string;
  is_playoff?: boolean;
  team_id: number;
  owner: string;
  team_name: string;
  matchup_id: number;
  weekly_points: number;
  cumulative_points: number;
  plus_minus: number;
  record: string;
};

export type SidePointAward = {
  year: number;
  week: number;
  team_id: number;
  owner: string;
  category: string;
  points: number;
  metric_name: string;
  metric_value: number;
};

export type MediaAsset = {
  id: number;
  path: string;
  url: string;
  title: string;
  type: string;
  year: number | null;
  week: number | null;
  category: string | null;
};

export type Records = {
  most_points: WeeklyResult[];
  largest_margin: WeeklyResult[];
  side_point_totals: { owner: string; points: number }[];
};

export type DraftPick = {
  year: number;
  team_id: number;
  owner: string;
  division: string | null;
  player_id: number | null;
  player_name: string;
  pro_team: string | null;
  position: string | null;
  total_points: number;
  round_drafted: number;
  round_pick: number;
  position_drafted: number;
  bid_amount: number;
  dollar_value: number | null;
  source: string;
};

export type DraftProjectedValue = DraftPick & {
  projected_points: number;
  projected_value: number;
  projection_basis: string;
};

export type DraftSpenderPcaPoint = {
  owner: string;
  label: string;
  pc1: number;
  pc2: number;
  spent: number;
  picks: number;
  strategy_type: string;
};

export type DraftStrategyProfile = {
  year: number;
  owner: string;
  label: string;
  spent: number;
  picks: number;
  avg_bid: number;
  median_bid: number;
  top1_share: number;
  top2_share: number;
  top3_share: number;
  gini: number;
  one_dollar_count: number;
  one_dollar_share: number;
  high_bid_count: number;
  high_bid_share: number;
  mid_bid_count: number;
  plus_10_count: number;
  weighted_pick: number;
  late_spend_share: number;
  first_big_pick: number;
  qb_share: number;
  rb_share: number;
  wr_share: number;
  te_share: number;
  top_heavy_score: number;
  patience_score: number;
  balance_score: number;
  strategy_type: string;
};

export type DraftStrategyOutcomeRow = DraftStrategyProfile & {
  team_name?: string;
  wins?: number;
  losses?: number;
  ties?: number;
  win_pct?: number;
  regular_points?: number;
  average?: number;
  points_rank?: number;
  record_rank?: number;
};

export type DraftStrategyCorrelation = {
  metric: string;
  target: string;
  correlation: number;
  n: number;
  direction: string;
};

export type DraftStrategyTypeOutcome = {
  strategy_type: string;
  seasons: number;
  avg_points: number;
  avg_win_pct: number;
  avg_points_rank: number;
  avg_record_rank: number;
};

export type DraftSummary = {
  years: number[];
  by_owner: { owner: string; spent: number; points: number; picks: number; value: number }[];
  by_position: { position: string; spent: number; points: number; picks: number; value: number }[];
  top_values: DraftPick[];
  biggest_buys: DraftPick[];
  projected_best_values: DraftProjectedValue[];
  spender_pca: DraftSpenderPcaPoint[];
  strategy_profiles: DraftStrategyProfile[];
  strategy_history: DraftStrategyProfile[];
  strategy_outcomes: {
    rows: DraftStrategyOutcomeRow[];
    completed_rows: DraftStrategyOutcomeRow[];
    correlations: DraftStrategyCorrelation[];
    by_type: DraftStrategyTypeOutcome[];
  };
};

export type DraftLiveTeam = CurrentTeam & {
  is_me: boolean;
  spent: number;
  budget_left: number;
  picks: number;
  remaining_slots: number;
  max_bid: number;
  avg_spend_per_pick: number;
  positions: Record<string, number>;
  needs: string[];
  roster: DraftPick[];
};

export type DraftLivePayload = {
  league_id: number;
  year: number;
  auction_budget: number;
  roster_size: number;
  poll_status: {
    ok: boolean;
    source: string;
    message: string;
    espn_pick_count: number | null;
    new_picks: number;
    in_progress?: boolean | null;
    drafted?: boolean | null;
    draft_slots?: number | null;
  };
  last_checked_at: string;
  draft: {
    picks: number;
    target_picks: number;
    complete: boolean;
  };
  my_team: DraftLiveTeam | null;
  advice: {
    headline: string;
    bullets: string[];
  };
  teams: DraftLiveTeam[];
  recent_picks: DraftPick[];
  position_market: {
    position: string;
    picks: number;
    average_bid: number;
    historical_average_bid: number;
    inflation: number;
    high_bid: number;
  }[];
};

export type ManualDraftPick = {
  player_name: string;
  owner: string;
  bid_amount: number;
  position?: string;
  pro_team?: string;
  team_id?: number;
  player_id?: number;
  position_drafted?: number;
  round_drafted?: number;
  round_pick?: number;
};

export type HistorySummary = {
  overview: {
    season_years: number[];
    draft_years: number[];
    team_week_rows: number;
    regular_team_week_rows: number;
    playoff_team_week_rows: number;
    draft_picks: number;
  };
  game_records: {
    highest_scores: WeeklyResult[];
    lowest_scores: WeeklyResult[];
    largest_margins: WeeklyResult[];
    worst_losses: WeeklyResult[];
    best_regular_seasons: {
      year: number;
      team_id: number;
      owner: string;
      team_name: string;
      points: number;
      games: number;
      average: number;
      wins: number;
      losses: number;
      ties: number;
    }[];
    worst_regular_seasons: {
      year: number;
      team_id: number;
      owner: string;
      team_name: string;
      points: number;
      games: number;
      average: number;
      wins: number;
      losses: number;
      ties: number;
    }[];
    owner_totals: { owner: string; points: number; games: number; average: number; high_score: number }[];
  };
  playoff_records: {
    highest_scores: WeeklyResult[];
    lowest_scores: WeeklyResult[];
    largest_margins: WeeklyResult[];
    owner_totals: { owner: string; points: number; games: number; average: number; high_score: number }[];
  };
  division_records: {
    owner_totals: { division: string; owner: string; points: number; games: number; average: number; high_score: number }[];
    season_totals: { division: string; year: number; team_id: number; owner: string; team_name: string; points: number; games: number; average: number }[];
  };
  playoff_justice: {
    seasons: PlayoffJusticeSeason[];
    biggest_snubs: PlayoffJusticeSnub[];
    biggest_beneficiaries: PlayoffJusticeBeneficiary[];
  };
  player_records: {
    best_player_games: PlayerGame[];
    worst_starter_games: PlayerGame[];
    best_player_totals: PlayerTotal[];
    best_player_averages: PlayerTotal[];
  };
  blunder_records: {
    bench_blunders: BenchBlunder[];
    costly_bench_blunders: BenchBlunder[];
  };
  side_point_records: {
    owner_totals: { owner: string; points: number; awards: number }[];
  };
  draft_records: {
    biggest_buys: DraftPick[];
    best_values: DraftPick[];
    most_points: DraftPick[];
    owner_value: { owner: string; spent: number; points: number; picks: number; value: number }[];
  };
};

export type PlayoffJusticeTeam = {
  year: number;
  team_id: number;
  owner: string;
  team_name: string;
  division: string;
  wins: number;
  losses: number;
  ties: number;
  regular_points: number;
  average: number;
  points_rank: number;
  record_rank: number;
  made_actual_playoffs: boolean;
  made_points_playoffs: boolean;
  made_record_playoffs: boolean;
  division_winner: boolean;
  qualification_type: "division_winner" | "wildcard" | "points_snub" | "missed";
};

export type PlayoffJusticeSnub = PlayoffJusticeTeam & {
  replaced_by_owner: string | null;
  replaced_by_team_name: string | null;
  points_gap: number;
  label: string;
};

export type PlayoffJusticeBeneficiary = PlayoffJusticeTeam & {
  replaced_owner: string | null;
  replaced_team_name: string | null;
  points_gap: number;
  label: string;
};

export type PlayoffJusticeSeason = {
  year: number;
  playoff_slots: number;
  teams: PlayoffJusticeTeam[];
  actual_playoff_teams: PlayoffJusticeTeam[];
  points_only_playoff_teams: PlayoffJusticeTeam[];
  record_only_playoff_teams: PlayoffJusticeTeam[];
  division_winners: PlayoffJusticeTeam[];
  snubs: PlayoffJusticeSnub[];
  beneficiaries: PlayoffJusticeBeneficiary[];
  record_snubs: PlayoffJusticeTeam[];
};

export type PlayerGame = {
  year: number;
  week: number;
  team_id: number;
  owner: string;
  slot_key: string;
  player_name: string;
  position: string | null;
  points: number;
};

export type PlayerTotal = {
  player_name: string;
  position: string;
  points: number;
  starts: number;
  average: number;
  high_score: number;
};

export type BenchBlunder = PlayerGame & {
  team_score: number;
  plus_minus: number;
  loss_margin: number | null;
  would_cover_loss: boolean;
  season_phase: string;
};

export type CurrentTeam = {
  team_id: number;
  owner: string;
  team_name: string;
  division: string | null;
  wins: number;
  losses: number;
  ties: number;
  points_for: number;
};

export type CurrentMatchup = {
  matchup_id: number;
  week: number;
  home: CurrentTeam | null;
  away: CurrentTeam | null;
  home_score: number;
  away_score: number;
  gotw_score?: number;
  reason?: string;
};

export type CurrentPoll = {
  id: number;
  question: string;
  total_votes: number;
  options: { id: number; label: string; votes: number }[];
};

export type ChatMessage = {
  id: number;
  author: string;
  body: string;
  created_at: string;
};

export type CurrentSeason = {
  league_id: number;
  year: number;
  league_name: string;
  phase: "pre_draft" | "preseason" | "in_season";
  current_week: number;
  display_week: number;
  nfl_week: number;
  regular_season_weeks: number;
  final_scoring_period: number;
  draft: { completed: boolean; picks: number; teams: number };
  teams: CurrentTeam[];
  matchups: CurrentMatchup[];
  gotw: CurrentMatchup[];
  polls: CurrentPoll[];
};

export type ContextBlock = {
  public_notes: string;
  background_notes: string;
  off_limits: string;
};

export type LeagueContext = ContextBlock & {
  tone_guide: string;
};

export type OwnerContext = ContextBlock & {
  owner: string;
  team_name: string;
  nickname: string;
  roast_level: string;
  political_affiliation: string;
  veto_hunter: string;
  rival_owner: string;
};

export type MatchupContext = ContextBlock & {
  matchup_id: number;
  label: string;
};

export type AdminContext = {
  year: number;
  week: number;
  league_context: LeagueContext;
  weekly_context: ContextBlock;
  owner_contexts: OwnerContext[];
  matchup_contexts: MatchupContext[];
};

export type MatchupBrief = {
  year: number;
  week: number;
  matchup_id: number;
  label: string;
  home: CurrentTeam | null;
  away: CurrentTeam | null;
  signals: {
    combined_previous_average: number;
    combined_high_score: number;
    same_division: boolean;
  };
  history: {
    home: { owner: string; games: number; wins: number; losses: number; ties: number; points: number; average: number; high_score: number };
    away: { owner: string; games: number; wins: number; losses: number; ties: number; points: number; average: number; high_score: number };
  };
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, options);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

async function adminRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getAdminToken();
  const headers = new Headers(options?.headers);
  headers.set("X-Admin-Token", token);
  const response = await fetch(`${apiBaseUrl}${path}`, { ...options, headers });
  if (response.status === 401) {
    if (getAdminToken() === token) setAdminToken("");
    throw new Error("Please sign in again.");
  }
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json() as Promise<T>;
}

export const api = {
  checkAdmin: (token: string) => request<{ ok: boolean }>("/api/admin/session", {
    headers: { "X-Admin-Token": token }
  }),
  seasons: () => request<Season[]>("/api/seasons"),
  records: () => request<Records>("/api/records"),
  weeklyResults: (year?: number, week?: number) => {
    const params = new URLSearchParams();
    if (year) params.set("year", String(year));
    if (week) params.set("week", String(week));
    return request<WeeklyResult[]>(`/api/weekly-results?${params.toString()}`);
  },
  sidePoints: (year?: number, week?: number) => {
    const params = new URLSearchParams();
    if (year) params.set("year", String(year));
    if (week) params.set("week", String(week));
    return request<SidePointAward[]>(`/api/side-points?${params.toString()}`);
  },
  media: (year?: number) => {
    const params = new URLSearchParams();
    if (year) params.set("year", String(year));
    return request<MediaAsset[]>(`/api/media?${params.toString()}`);
  },
  draftSummary: (year?: number) => {
    const params = new URLSearchParams();
    if (year) params.set("year", String(year));
    return request<DraftSummary>(`/api/draft/summary?${params.toString()}`);
  },
  draftPicks: (year?: number) => {
    const params = new URLSearchParams();
    if (year) params.set("year", String(year));
    return request<DraftPick[]>(`/api/draft/picks?${params.toString()}`);
  },
  draftLive: (year = 2026, pollEspn = false, myTeamId = 1) =>
    (pollEspn ? adminRequest<DraftLivePayload> : request<DraftLivePayload>)(`/api/draft/live?year=${year}&my_team_id=${myTeamId}&poll_espn=${pollEspn}`),
  postManualDraftPick: (pick: ManualDraftPick, year = 2026) =>
    adminRequest<DraftPick>(`/api/draft/live/manual?year=${year}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pick)
    }),
  historySummary: () => request<HistorySummary>("/api/history/summary"),
  currentSeason: (year = 2026) => request<CurrentSeason>(`/api/current-season?year=${year}`),
  adminContext: (year = 2026, week = 1) => adminRequest<AdminContext>(`/api/admin/context?year=${year}&week=${week}`),
  saveAdminContext: (context: AdminContext, year = 2026, week = 1) =>
    adminRequest<AdminContext>(`/api/admin/context?year=${year}&week=${week}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(context)
    }),
  matchupBriefs: (year = 2026, week = 1) => adminRequest<MatchupBrief[]>(`/api/admin/matchup-briefs?year=${year}&week=${week}`),
  currentChat: (year = 2026) => request<ChatMessage[]>(`/api/current-season/chat?year=${year}`),
  postCurrentChat: (message: { author: string; body: string }, year = 2026) =>
    fetch(`${apiBaseUrl}/api/current-season/chat?year=${year}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(message)
    }).then((response) => {
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      return response.json() as Promise<ChatMessage>;
    }),
  votePoll: (pollId: number, optionId: number, voter: string) =>
    fetch(`${apiBaseUrl}/api/current-season/polls/${pollId}/vote`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ option_id: optionId, voter })
    }).then((response) => {
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      return response.json() as Promise<{ ok: boolean }>;
    })
};
