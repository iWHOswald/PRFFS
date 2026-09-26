import { CalendarDays, Filter } from "lucide-react";
import type { Season } from "../lib/api";

type Props = {
  seasons: Season[];
  selectedYear?: number | "all-time" | "current" | "draft" | "admin" | "office" | "story";
  selectedWeek: number;
  onYearChange: (year: number | "all-time" | "current" | "draft" | "admin" | "office" | "story") => void;
  onWeekChange: (week: number) => void;
};

export function Controls({ seasons, selectedYear, selectedWeek, onYearChange, onWeekChange }: Props) {
  const weeks = Array.from({ length: 17 }, (_, index) => index + 1);

  return (
    <section className="controls-band">
      <div className="control-group">
        <CalendarDays size={18} />
        <select
          value={selectedYear ?? ""}
          onChange={(event) => {
            const value = event.target.value;
            onYearChange(value === "all-time" || value === "current" || value === "draft" || value === "admin" || value === "office" || value === "story" ? value : Number(value));
          }}
        >
          <option value="current">Current Season</option>
          <option value="draft">Draft Results</option>
          <option value="admin">Admin Studio</option>
          <option value="office">League Office</option>
          <option value="story">Mega Cat Story</option>
          <option value="all-time">All Time</option>
          {seasons.map((season) => (
            <option key={season.year} value={season.year}>
              {season.year}
            </option>
          ))}
        </select>
      </div>
      {selectedYear !== "all-time" && selectedYear !== "current" && selectedYear !== "draft" && selectedYear !== "admin" && selectedYear !== "office" && selectedYear !== "story" ? <div className="control-group week-strip" aria-label="Week filter">
        <Filter size={18} />
        {weeks.map((week) => (
          <button
            key={week}
            className={week === selectedWeek ? "is-active" : ""}
            onClick={() => onWeekChange(week)}
            type="button"
          >
            {week}
          </button>
        ))}
      </div> : null}
    </section>
  );
}
