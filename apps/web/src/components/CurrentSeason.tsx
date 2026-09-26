import { FormEvent, useEffect, useMemo, useState } from "react";
import { CalendarClock, ClipboardList, MessageSquare, RadioTower, Star, Trophy, Users } from "lucide-react";
import { Swiper, SwiperSlide } from "swiper/react";
import "swiper/css";
import { api, type ChatMessage, type CurrentSeason as CurrentSeasonData } from "../lib/api";

const emptySeason: CurrentSeasonData = {
  league_id: 917761,
  year: 2026,
  league_name: "Pork Rub Fantasy",
  phase: "pre_draft",
  current_week: 0,
  display_week: 1,
  nfl_week: 0,
  regular_season_weeks: 14,
  final_scoring_period: 17,
  draft: { completed: false, picks: 0, teams: 12 },
  teams: [],
  matchups: [],
  gotw: [],
  polls: []
};

export function CurrentSeason({ onViewDraft }: { onViewDraft?: () => void }) {
  const [season, setSeason] = useState<CurrentSeasonData>(emptySeason);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [author, setAuthor] = useState("Commissioner");
  const [body, setBody] = useState("");
  const [voter, setVoter] = useState("Commissioner");

  const phaseLabel = useMemo(() => {
    if (season.phase === "pre_draft") return "Preseason";
    if (season.phase === "preseason") return "Roster prep";
    return `Week ${season.current_week}`;
  }, [season.phase, season.current_week]);

  function refresh() {
    api.currentSeason(2026)
      .then((current) => Promise.all([Promise.resolve(current), api.currentChat(2026)]))
      .then(([current, chat]) => {
        setSeason(current);
        setMessages(chat);
      }).catch(() => {
        setSeason(emptySeason);
        setMessages([]);
      });
  }

  useEffect(() => {
    refresh();
  }, []);

  function submitMessage(event: FormEvent) {
    event.preventDefault();
    if (!body.trim() || !author.trim()) return;
    api.postCurrentChat({ author, body }, 2026).then(() => {
      setBody("");
      return api.currentChat(2026).then(setMessages);
    }).catch(() => undefined);
  }

  function vote(pollId: number, optionId: number) {
    if (!voter.trim()) return;
    api.votePoll(pollId, optionId, voter).then(() => api.currentSeason(2026).then(setSeason)).catch(() => undefined);
  }

  return (
    <section className="current-season">
      <div className="section-heading">
        <div>
          <span className="eyebrow">2026</span>
          <h2>Current Season</h2>
        </div>
        <div className="status-pill">
          <RadioTower size={17} />
          <span>{phaseLabel}</span>
        </div>
      </div>

      <section className="summary-grid">
        <CurrentStat icon={<CalendarClock size={20} />} label="Display Week" value={String(season.display_week || "Pre")} />
        <CurrentStat icon={<Trophy size={20} />} label="GOTW Candidates" value={String(season.gotw.length)} />
        <CurrentStat icon={<Users size={20} />} label="Teams" value={String(season.teams.length)} />
      </section>

      <section className="wide-panel current-brief">
        <div>
          <h2>{season.league_name}</h2>
          <p>
            Week {season.display_week} schedule hub with GOTW voting, matchup context, chat, and team directory.
          </p>
        </div>
        <div className="current-brief-actions">
          <button type="button" onClick={refresh}>Refresh</button>
          <button type="button" onClick={onViewDraft}>
            <ClipboardList size={17} />
            <span>View Draft Results</span>
          </button>
        </div>
      </section>

      <section className="wide-panel">
        <div className="panel-heading">
          <h2>GOTW Watch</h2>
          <Star size={18} />
        </div>
        <Swiper slidesPerView="auto" spaceBetween={14}>
          {season.gotw.map((matchup) => (
            <SwiperSlide className="matchup-slide" key={matchup.matchup_id}>
              <article className="matchup-card gotw-card">
                <span className="matchup-id">Week {matchup.week} Candidate</span>
                <div className="matchup-team">
                  <span>{matchup.home?.owner ?? "TBD"}</span>
                  <strong>{matchup.home?.division ?? ""}</strong>
                </div>
                <div className="matchup-team">
                  <span>{matchup.away?.owner ?? "TBD"}</span>
                  <strong>{matchup.away?.division ?? ""}</strong>
                </div>
                <p>{matchup.reason}</p>
              </article>
            </SwiperSlide>
          ))}
        </Swiper>
      </section>

      <section className="current-grid">
        <PollPanel polls={season.polls} voter={voter} setVoter={setVoter} vote={vote} />
        <ChatPanel messages={messages} author={author} setAuthor={setAuthor} body={body} setBody={setBody} submitMessage={submitMessage} />
      </section>

      <section className="wide-panel">
        <div className="panel-heading">
          <h2>Teams</h2>
        </div>
        <div className="team-grid">
          {season.teams.map((team) => (
            <article className="team-tile" key={team.team_id}>
              <span>{team.division}</span>
              <strong>{team.team_name}</strong>
              <em>{team.owner}</em>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}

function CurrentStat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
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

function PollPanel({ polls, voter, setVoter, vote }: { polls: CurrentSeasonData["polls"]; voter: string; setVoter: (value: string) => void; vote: (pollId: number, optionId: number) => void }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Polls</h2>
      </div>
      <input className="field" value={voter} onChange={(event) => setVoter(event.target.value)} placeholder="Voter" />
      <div className="poll-list">
        {polls.map((poll) => (
          <article className="poll-card" key={poll.id}>
            <strong>{poll.question}</strong>
            {poll.options.map((option) => {
              const pct = poll.total_votes ? Math.round((option.votes / poll.total_votes) * 100) : 0;
              return (
                <button key={option.id} type="button" onClick={() => vote(poll.id, option.id)}>
                  <span>{option.label}</span>
                  <em>{option.votes} votes</em>
                  <i style={{ width: `${pct}%` }} />
                </button>
              );
            })}
          </article>
        ))}
      </div>
    </section>
  );
}

function ChatPanel({ messages, author, setAuthor, body, setBody, submitMessage }: { messages: ChatMessage[]; author: string; setAuthor: (value: string) => void; body: string; setBody: (value: string) => void; submitMessage: (event: FormEvent) => void }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>League Chat</h2>
        <MessageSquare size={18} />
      </div>
      <div className="chat-log">
        {messages.map((message) => (
          <article key={message.id}>
            <strong>{message.author}</strong>
            <p>{message.body}</p>
          </article>
        ))}
      </div>
      <form className="chat-form" onSubmit={submitMessage}>
        <input className="field" value={author} onChange={(event) => setAuthor(event.target.value)} placeholder="Name" />
        <textarea className="field" value={body} onChange={(event) => setBody(event.target.value)} placeholder="Talk your talk" />
        <button type="submit">Send</button>
      </form>
    </section>
  );
}
