import { useEffect, useState } from "react";
import { FileText, RadioTower, Save } from "lucide-react";
import { api, type AdminContext, type MatchupBrief } from "../lib/api";

const emptyContext: AdminContext = {
  year: 2026,
  week: 1,
  league_context: {
    tone_guide: "",
    public_notes: "",
    background_notes: "",
    off_limits: ""
  },
  weekly_context: {
    public_notes: "",
    background_notes: "",
    off_limits: ""
  },
  owner_contexts: [],
  matchup_contexts: []
};

export function AdminStudio() {
  const [week, setWeek] = useState(1);
  const [context, setContext] = useState<AdminContext>(emptyContext);
  const [briefs, setBriefs] = useState<MatchupBrief[]>([]);
  const [status, setStatus] = useState("Ready");

  function refresh(targetWeek = week) {
    setStatus("Loading admin data");
    Promise.all([
      api.adminContext(2026, targetWeek),
      api.matchupBriefs(2026, targetWeek)
    ]).then(([contextPayload, briefRows]) => {
      setContext(contextPayload);
      setBriefs(briefRows);
      setStatus("Ready");
    }).catch((err: Error) => setStatus(err.message));
  }

  useEffect(() => {
    refresh(week);
  }, [week]);

  function saveContext() {
    setStatus("Saving context");
    api.saveAdminContext(context, 2026, week)
      .then((payload) => {
        setContext(payload);
        setStatus("Context saved");
      })
      .catch((err: Error) => setStatus(err.message));
  }

  return (
    <section className="admin-studio">
      <div className="section-heading">
        <div>
          <span className="eyebrow">League tools</span>
          <h2>Admin Studio</h2>
        </div>
        <div className="status-pill">
          <RadioTower size={17} />
          <span>{status}</span>
        </div>
      </div>

      <section className="wide-panel admin-toolbar">
        <label className="control-group compact-control">
          <span>Week</span>
          <select value={week} onChange={(event) => setWeek(Number(event.target.value))}>
            {Array.from({ length: 17 }, (_, index) => index + 1).map((value) => (
              <option key={value} value={value}>Week {value}</option>
            ))}
          </select>
        </label>
        <button type="button" onClick={saveContext}>
          <Save size={16} />
          <span>Save Context</span>
        </button>
        <button type="button" onClick={() => refresh()}>
          <RadioTower size={16} />
          <span>Refresh</span>
        </button>
      </section>

      <section className="admin-grid">
        <section className="panel admin-panel">
          <div className="panel-heading">
            <h2>League Tone</h2>
            <FileText size={18} />
          </div>
          <AdminTextarea
            label="Tone guide"
            value={context.league_context.tone_guide}
            onChange={(value) => setContext({ ...context, league_context: { ...context.league_context, tone_guide: value } })}
          />
          <AdminTextarea
            label="Public league notes"
            value={context.league_context.public_notes}
            onChange={(value) => setContext({ ...context, league_context: { ...context.league_context, public_notes: value } })}
          />
          <AdminTextarea
            label="Background only"
            value={context.league_context.background_notes}
            onChange={(value) => setContext({ ...context, league_context: { ...context.league_context, background_notes: value } })}
          />
          <AdminTextarea
            label="Off limits"
            value={context.league_context.off_limits}
            onChange={(value) => setContext({ ...context, league_context: { ...context.league_context, off_limits: value } })}
          />
        </section>

        <section className="panel admin-panel">
          <div className="panel-heading">
            <h2>Weekly Notes</h2>
          </div>
          <AdminTextarea
            label="Public weekly notes"
            value={context.weekly_context.public_notes}
            onChange={(value) => setContext({ ...context, weekly_context: { ...context.weekly_context, public_notes: value } })}
          />
          <AdminTextarea
            label="Background only"
            value={context.weekly_context.background_notes}
            onChange={(value) => setContext({ ...context, weekly_context: { ...context.weekly_context, background_notes: value } })}
          />
          <AdminTextarea
            label="Off limits"
            value={context.weekly_context.off_limits}
            onChange={(value) => setContext({ ...context, weekly_context: { ...context.weekly_context, off_limits: value } })}
          />
        </section>
      </section>

      <section className="wide-panel">
        <div className="panel-heading">
          <h2>Owner Profiles</h2>
        </div>
        <div className="owner-context-grid">
          {context.owner_contexts.map((owner, index) => (
            <article className="owner-context-card" key={owner.owner}>
              <strong>{owner.team_name}</strong>
              <span>{owner.owner}</span>
              <input
                className="field"
                placeholder="Nickname"
                value={owner.nickname}
                onChange={(event) => updateOwner(index, { nickname: event.target.value })}
              />
              <select className="field" value={owner.roast_level} onChange={(event) => updateOwner(index, { roast_level: event.target.value })}>
                <option value="light">Light</option>
                <option value="medium">Medium</option>
                <option value="hot">Hot</option>
              </select>
              <select className="field" value={owner.political_affiliation} onChange={(event) => updateOwner(index, { political_affiliation: event.target.value })}>
                <option value="unassigned">Political affiliation</option>
                <option value="traditionalist">Traditionalist</option>
                <option value="reformer">Reformer</option>
                <option value="chaos caucus">Chaos caucus</option>
                <option value="pragmatist">Pragmatist</option>
              </select>
              <select className="field" value={owner.veto_hunter} onChange={(event) => updateOwner(index, { veto_hunter: event.target.value })}>
                <option value="unknown">Veto hunter?</option>
                <option value="yes">Yes</option>
                <option value="situational">Situational</option>
                <option value="no">No</option>
              </select>
              <select className="field" value={owner.rival_owner} onChange={(event) => updateOwner(index, { rival_owner: event.target.value })}>
                <option value="">Primary rival</option>
                {context.owner_contexts.filter((candidate) => candidate.owner !== owner.owner).map((candidate) => (
                  <option key={candidate.owner} value={candidate.owner}>{candidate.owner}</option>
                ))}
              </select>
              <textarea className="field" placeholder="Public notes" value={owner.public_notes} onChange={(event) => updateOwner(index, { public_notes: event.target.value })} />
              <textarea className="field" placeholder="Background only" value={owner.background_notes} onChange={(event) => updateOwner(index, { background_notes: event.target.value })} />
              <textarea className="field" placeholder="Off limits" value={owner.off_limits} onChange={(event) => updateOwner(index, { off_limits: event.target.value })} />
            </article>
          ))}
        </div>
      </section>

      <section className="wide-panel">
        <div className="panel-heading">
          <h2>Weekly Matchup Context</h2>
        </div>
        <div className="admin-matchup-list">
          {briefs.map((brief) => {
            const contextRow = context.matchup_contexts.find((row) => row.matchup_id === brief.matchup_id);
            return (
              <article className="admin-matchup-card" key={brief.matchup_id}>
                <div>
                  <span className="eyebrow">Matchup {brief.matchup_id + 1}</span>
                  <h3>{brief.label}</h3>
                  <p>
                    Combined historical avg {brief.signals.combined_previous_average.toFixed(1)}
                    {brief.signals.same_division ? " · division matchup" : ""}
                  </p>
                </div>
                <textarea
                  className="field"
                  placeholder="Public matchup notes"
                  value={contextRow?.public_notes ?? ""}
                  onChange={(event) => updateMatchupContext(brief.matchup_id, { public_notes: event.target.value })}
                />
                <textarea
                  className="field"
                  placeholder="Background only"
                  value={contextRow?.background_notes ?? ""}
                  onChange={(event) => updateMatchupContext(brief.matchup_id, { background_notes: event.target.value })}
                />
                <textarea
                  className="field"
                  placeholder="Off limits"
                  value={contextRow?.off_limits ?? ""}
                  onChange={(event) => updateMatchupContext(brief.matchup_id, { off_limits: event.target.value })}
                />
              </article>
            );
          })}
        </div>
      </section>
    </section>
  );

  function updateOwner(index: number, patch: Partial<AdminContext["owner_contexts"][number]>) {
    const next = [...context.owner_contexts];
    next[index] = { ...next[index], ...patch };
    setContext({ ...context, owner_contexts: next });
  }

  function updateMatchupContext(matchupId: number, patch: Partial<AdminContext["matchup_contexts"][number]>) {
    const current = context.matchup_contexts.find((row) => row.matchup_id === matchupId);
    const nextRow = { matchup_id: matchupId, label: current?.label ?? "", public_notes: "", background_notes: "", off_limits: "", ...current, ...patch };
    const nextRows = context.matchup_contexts.some((row) => row.matchup_id === matchupId)
      ? context.matchup_contexts.map((row) => row.matchup_id === matchupId ? nextRow : row)
      : [...context.matchup_contexts, nextRow];
    setContext({ ...context, matchup_contexts: nextRows });
  }
}

function AdminTextarea({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="admin-field">
      <span>{label}</span>
      <textarea className="field" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}
