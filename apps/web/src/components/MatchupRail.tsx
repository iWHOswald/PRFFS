import { Trophy } from "lucide-react";
import { Swiper, SwiperSlide } from "swiper/react";
import "swiper/css";
import type { WeeklyResult } from "../lib/api";

type Props = {
  rows: WeeklyResult[];
};

export function MatchupRail({ rows }: Props) {
  const matchupIds = Array.from(new Set(rows.map((row) => row.matchup_id))).sort((a, b) => a - b);

  return (
    <section className="wide-panel">
      <div className="panel-heading">
        <h2>Weekly Matchups</h2>
        <Trophy size={18} />
      </div>
      <Swiper slidesPerView="auto" spaceBetween={14} className="matchup-swiper">
        {matchupIds.map((matchupId) => {
          const teams = rows.filter((row) => row.matchup_id === matchupId).sort((a, b) => b.weekly_points - a.weekly_points);
          return (
            <SwiperSlide key={matchupId} className="matchup-slide">
              <article className="matchup-card">
                <span className="matchup-id">Matchup {matchupId + 1}</span>
                {teams.map((team) => (
                  <div className="matchup-team" key={team.team_id}>
                    <span>{team.owner}</span>
                    <strong>{team.weekly_points.toFixed(2)}</strong>
                  </div>
                ))}
              </article>
            </SwiperSlide>
          );
        })}
      </Swiper>
    </section>
  );
}
