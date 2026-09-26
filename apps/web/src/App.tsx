import { useEffect, useMemo, useState } from "react";
import { Activity, Database, RadioTower } from "lucide-react";
import { motion } from "framer-motion";
import { api, type MediaAsset, type Records, type Season, type SidePointAward, type WeeklyResult } from "./lib/api";
import { AdminStudio } from "./components/AdminStudio";
import { AdminAccess } from "./components/AdminAccess";
import { Charts } from "./components/Charts";
import { Controls } from "./components/Controls";
import { CurrentSeason } from "./components/CurrentSeason";
import { DraftReview } from "./components/DraftReview";
import { LeagueHistory } from "./components/LeagueHistory";
import { LeagueOffice } from "./components/LeagueOffice";
import { MatchupRail } from "./components/MatchupRail";
import { MediaGallery } from "./components/MediaGallery";
import { MetricTable } from "./components/MetricTable";
import { StoryPlayer } from "./story/components/StoryPlayer";
import { megaCatStory } from "./story/megaCatStory";
import "./styles.css";

const emptyRecords: Records = { most_points: [], largest_margin: [], side_point_totals: [] };

export default function App() {
  const [seasons, setSeasons] = useState<Season[]>([]);
  const [records, setRecords] = useState<Records>(emptyRecords);
  const [weeklyRows, setWeeklyRows] = useState<WeeklyResult[]>([]);
  const [sidePoints, setSidePoints] = useState<SidePointAward[]>([]);
  const [media, setMedia] = useState<MediaAsset[]>([]);
  const [selectedYear, setSelectedYear] = useState<number | "all-time" | "current" | "draft" | "admin" | "office" | "story">();
  const [selectedWeek, setSelectedWeek] = useState(1);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.seasons(), api.records()])
      .then(([seasonRows, recordRows]) => {
        setSeasons(seasonRows);
        setRecords(recordRows);
        setSelectedYear("current");
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!selectedYear || selectedYear === "all-time" || selectedYear === "current" || selectedYear === "draft" || selectedYear === "admin" || selectedYear === "office" || selectedYear === "story") return;
    Promise.all([api.weeklyResults(selectedYear, selectedWeek), api.sidePoints(selectedYear, selectedWeek), api.media(selectedYear)])
      .then(([weekly, side, mediaAssets]) => {
        setWeeklyRows(weekly);
        setSidePoints(side);
        setMedia(mediaAssets);
      })
      .catch((err: Error) => setError(err.message));
  }, [selectedYear, selectedWeek]);

  const sideTotal = useMemo(() => sidePoints.reduce((sum, award) => sum + award.points, 0), [sidePoints]);

  return (
    <main className={selectedYear === "story" ? "story-main" : undefined}>
      {selectedYear === "story" ? null : (
        <>
          <header className="topbar">
            <div>
              <span className="eyebrow">Pork Rub Fantasy Football</span>
              <h1>League Ops</h1>
            </div>
            <div className="status-pill">
              <RadioTower size={17} />
              <span>Live tracker ready</span>
            </div>
          </header>

          <Controls
            seasons={seasons}
            selectedYear={selectedYear}
            selectedWeek={selectedWeek}
            onYearChange={setSelectedYear}
            onWeekChange={setSelectedWeek}
          />
        </>
      )}

      {error ? <div className="error-strip">{error}</div> : null}

      {selectedYear === "story" ? (
        <StoryPlayer story={megaCatStory} onExit={() => setSelectedYear("current")} />
      ) : selectedYear === "current" ? (
        <CurrentSeason onViewDraft={() => setSelectedYear("draft")} />
      ) : selectedYear === "draft" ? (
        <DraftReview />
      ) : selectedYear === "admin" ? (
        <AdminAccess><AdminStudio /></AdminAccess>
      ) : selectedYear === "office" ? (
        <LeagueOffice />
      ) : selectedYear === "all-time" ? (
        <LeagueHistory />
      ) : (
        <>
          <section className="summary-grid">
            <Summary icon={<Database size={20} />} label="Imported Seasons" value={String(seasons.length)} />
            <Summary icon={<Activity size={20} />} label="Week Teams" value={String(weeklyRows.length)} />
            <Summary icon={<RadioTower size={20} />} label="Side Points" value={sideTotal.toFixed(1)} />
          </section>

          <MatchupRail rows={weeklyRows} />
          <Charts weeklyRows={weeklyRows} sidePoints={sidePoints} />

          <section className="records-grid">
            <MetricTable title="Season Points Records" rows={records.most_points} metric="weekly_points" />
            <MetricTable title="Season Margin Records" rows={records.largest_margin} metric="plus_minus" />
          </section>

          <MediaGallery assets={media} />
          <DraftReview selectedYear={selectedYear} />
        </>
      )}
    </main>
  );
}

function Summary({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <motion.section className="summary-panel" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      {icon}
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </motion.section>
  );
}
