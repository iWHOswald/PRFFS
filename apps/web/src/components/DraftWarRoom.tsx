import { FormEvent, useEffect, useMemo, useState } from "react";
import { Activity, Crosshair, Play, Plus, RadioTower, RefreshCw, Square, WalletCards } from "lucide-react";
import { api, type DraftLivePayload, type ManualDraftPick } from "../lib/api";
import { AdminAccess } from "./AdminAccess";

const emptyLive: DraftLivePayload = {
  league_id: 917761,
  year: 2026,
  auction_budget: 200,
  roster_size: 15,
  poll_status: { ok: false, source: "local", message: "Not checked yet", espn_pick_count: null, new_picks: 0 },
  last_checked_at: "",
  draft: { picks: 0, target_picks: 180, complete: false },
  my_team: null,
  advice: { headline: "Waiting for draft data.", bullets: [] },
  teams: [],
  recent_picks: [],
  position_market: []
};

const emptyPick: ManualDraftPick = {
  player_name: "",
  owner: "Iain",
  bid_amount: 1,
  position: "",
  pro_team: ""
};

export function DraftWarRoom() {
  return <AdminAccess><DraftWarRoomContent /></AdminAccess>;
}

function DraftWarRoomContent() {
  const [live, setLive] = useState<DraftLivePayload>(emptyLive);
  const [status, setStatus] = useState("Starting");
  const [streaming, setStreaming] = useState(false);
  const [manual, setManual] = useState<ManualDraftPick>(emptyPick);

  function refresh(pollEspn = true) {
    setStatus(pollEspn ? "Polling ESPN" : "Refreshing local");
    api.draftLive(2026, pollEspn, 1)
      .then((payload) => {
        setLive(payload);
        setStatus(payload.poll_status.message);
      })
      .catch((err: Error) => setStatus(err.message));
  }

  useEffect(() => {
    refresh(false);
  }, []);

  useEffect(() => {
    if (!streaming) return undefined;
    const handle = window.setInterval(() => refresh(true), 5000);
    return () => window.clearInterval(handle);
  }, [streaming]);

  function startStream() {
    setStreaming(true);
    refresh(true);
  }

  function stopStream() {
    setStreaming(false);
    setStatus("Stream paused");
  }

  function submitManual(event: FormEvent) {
    event.preventDefault();
    if (!manual.player_name.trim() || !manual.owner.trim()) return;
    setStatus("Recording manual pick");
    api.postManualDraftPick(manual, 2026)
      .then(() => {
        setManual({ ...emptyPick, owner: manual.owner });
        refresh(false);
      })
      .catch((err: Error) => setStatus(err.message));
  }

  const checkedLabel = useMemo(() => {
    if (!live.last_checked_at) return "Never";
    return new Date(live.last_checked_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit", second: "2-digit" });
  }, [live.last_checked_at]);

  return (
    <section className="wide-panel draft-war-room">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Auction live</span>
          <h2>Draft War Room</h2>
        </div>
        <div className="draft-live-actions">
          {streaming ? (
            <button type="button" onClick={stopStream}>
              <Square size={16} />
              <span>Stop Stream</span>
            </button>
          ) : (
            <button type="button" onClick={startStream}>
              <Play size={16} />
              <span>Start Stream</span>
            </button>
          )}
          <button type="button" onClick={() => refresh(true)}>
            <RefreshCw size={16} />
            <span>Poll Now</span>
          </button>
        </div>
      </div>

      <section className="summary-grid">
        <DraftStat icon={<RadioTower size={20} />} label="ESPN Status" value={live.poll_status.ok ? "Connected" : "Fallback"} />
        <DraftStat icon={<Activity size={20} />} label="Picks Recorded" value={`${live.draft.picks}/${live.draft.target_picks || 180}`} />
        <DraftStat icon={<WalletCards size={20} />} label="Iain Max Bid" value={`$${live.my_team?.max_bid.toFixed(0) ?? "0"}`} />
      </section>

      <section className="draft-advice">
        <div>
          <span className="eyebrow">Checked {checkedLabel}</span>
          <h3>{live.advice.headline}</h3>
          {live.advice.bullets.map((bullet) => (
            <p key={bullet}>{bullet}</p>
          ))}
        </div>
        <div className="draft-status-box">
          <strong>{status}</strong>
          <span>Stream: {streaming ? "running every 5 seconds" : "paused"}</span>
          <span>Room: {live.poll_status.in_progress ? "in progress" : live.poll_status.drafted ? "drafted" : "waiting"}</span>
          <span>Draft slots: {live.poll_status.draft_slots ?? "unknown"}</span>
          <span>ESPN picks visible: {live.poll_status.espn_pick_count ?? "unknown"}</span>
          <span>New this poll: {live.poll_status.new_picks}</span>
        </div>
      </section>

      <section className="draft-live-grid">
        <section className="panel draft-manual-panel">
          <div className="panel-heading">
            <h2>Manual Pick</h2>
            <Plus size={18} />
          </div>
          <form className="draft-manual-form" onSubmit={submitManual}>
            <input className="field" placeholder="Player" value={manual.player_name} onChange={(event) => setManual({ ...manual, player_name: event.target.value })} />
            <input className="field" placeholder="Owner or team" value={manual.owner} onChange={(event) => setManual({ ...manual, owner: event.target.value })} />
            <input className="field" placeholder="Bid" type="number" min="0" max="200" value={manual.bid_amount} onChange={(event) => setManual({ ...manual, bid_amount: Number(event.target.value) })} />
            <input className="field" placeholder="Position" value={manual.position ?? ""} onChange={(event) => setManual({ ...manual, position: event.target.value })} />
            <input className="field" placeholder="NFL team" value={manual.pro_team ?? ""} onChange={(event) => setManual({ ...manual, pro_team: event.target.value })} />
            <button type="submit">
              <Plus size={16} />
              <span>Record</span>
            </button>
          </form>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <h2>Iain Board</h2>
            <Crosshair size={18} />
          </div>
          {live.my_team ? (
            <div className="my-draft-board">
              <div>
                <span>Budget</span>
                <strong>${live.my_team.budget_left.toFixed(0)}</strong>
              </div>
              <div>
                <span>Slots</span>
                <strong>{live.my_team.remaining_slots}</strong>
              </div>
              <div>
                <span>Needs</span>
                <strong>{live.my_team.needs.join(", ") || "Depth"}</strong>
              </div>
              <div className="mini-roster">
                {live.my_team.roster.map((pick) => (
                  <span key={pick.position_drafted}>{pick.position ?? "UNK"}: {pick.player_name} ${pick.bid_amount.toFixed(0)}</span>
                ))}
              </div>
            </div>
          ) : (
            <p>No Iain team context yet.</p>
          )}
        </section>
      </section>

      <section className="draft-live-grid">
        <section className="panel">
          <div className="panel-heading">
            <h2>Recent Picks</h2>
          </div>
          <div className="table-wrap draft-live-table">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Player</th>
                  <th>Owner</th>
                  <th>Pos</th>
                  <th className="number">Bid</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {live.recent_picks.map((pick) => (
                  <tr key={pick.position_drafted}>
                    <td>{pick.position_drafted}</td>
                    <td>{pick.player_name}</td>
                    <td>{pick.owner}</td>
                    <td>{pick.position ?? "-"}</td>
                    <td className="number">${pick.bid_amount.toFixed(0)}</td>
                    <td>{pick.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <h2>Budgets</h2>
          </div>
          <div className="table-wrap draft-live-table">
            <table>
              <thead>
                <tr>
                  <th>Team</th>
                  <th>Needs</th>
                  <th className="number">Left</th>
                  <th className="number">Max</th>
                  <th className="number">Picks</th>
                </tr>
              </thead>
              <tbody>
                {live.teams.map((team) => (
                  <tr key={team.team_id} className={team.is_me ? "is-my-row" : ""}>
                    <td>
                      <strong>{team.owner}</strong>
                      <span>{team.team_name}</span>
                    </td>
                    <td>{team.needs.join(", ")}</td>
                    <td className="number">${team.budget_left.toFixed(0)}</td>
                    <td className="number">${team.max_bid.toFixed(0)}</td>
                    <td className="number">{team.picks}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </section>
    </section>
  );
}

function DraftStat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <section className="summary-panel">
      {icon}
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </section>
  );
}
