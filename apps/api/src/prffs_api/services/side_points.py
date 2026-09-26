from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SidePointAwardRow:
    team_id: int
    owner: str
    category: str
    points: float
    metric_name: str
    metric_value: float
    detail: str | None = None


def _top_ties(rows: list[dict], metric: str, points: float, category: str) -> list[SidePointAwardRow]:
    if not rows:
        return []
    ordered = sorted(rows, key=lambda row: float(row.get(metric, 0)), reverse=True)
    top_value = float(ordered[0].get(metric, 0))
    return [
        SidePointAwardRow(
            team_id=int(row["team_id"]),
            owner=row["owner"],
            category=category,
            points=points,
            metric_name=metric,
            metric_value=top_value,
        )
        for row in ordered
        if float(row.get(metric, 0)) == top_value
    ]


def _bottom_ties(rows: list[dict], metric: str, points: float, category: str) -> list[SidePointAwardRow]:
    if not rows:
        return []
    ordered = sorted(rows, key=lambda row: float(row.get(metric, 0)))
    bottom_value = float(ordered[0].get(metric, 0))
    return [
        SidePointAwardRow(
            team_id=int(row["team_id"]),
            owner=row["owner"],
            category=category,
            points=points,
            metric_name=metric,
            metric_value=bottom_value,
        )
        for row in ordered
        if float(row.get(metric, 0)) == bottom_value
    ]


def calculate_side_points(rows: list[dict], lineup_points: dict[tuple[int, str], float]) -> list[SidePointAwardRow]:
    enriched = []
    for row in rows:
        team_id = int(row["team_id"])
        item = dict(row)
        item["qb_points"] = lineup_points.get((team_id, "QB"), 0.0)
        item["rb_points"] = lineup_points.get((team_id, "RB1"), 0.0) + lineup_points.get((team_id, "RB2"), 0.0)
        item["wr_points"] = lineup_points.get((team_id, "WR1"), 0.0) + lineup_points.get((team_id, "WR2"), 0.0)
        item["te_points"] = lineup_points.get((team_id, "TE"), 0.0)
        item["dst_hc_points"] = lineup_points.get((team_id, "D/ST"), 0.0) + lineup_points.get((team_id, "HC"), 0.0)
        enriched.append(item)

    awards: list[SidePointAwardRow] = []
    awards.extend(_top_ties(enriched, "weekly_points", 2.0, "Most points"))
    if lineup_points:
        awards.extend(_top_ties(enriched, "qb_points", 1.0, "Top QB"))
        awards.extend(_top_ties(enriched, "rb_points", 1.0, "Top RB"))
        awards.extend(_top_ties(enriched, "wr_points", 1.0, "Top WR"))
        awards.extend(_top_ties(enriched, "te_points", 0.5, "Top TE"))
        awards.extend(_top_ties(enriched, "dst_hc_points", 0.5, "Top DST/HC"))
    awards.extend(_bottom_ties(enriched, "weekly_points", -0.5, "Least points"))
    awards.extend(_top_ties(enriched, "plus_minus", 0.5, "Largest margin of victory"))

    losing_rows = [row for row in enriched if float(row.get("plus_minus", 0)) < 0]
    if losing_rows:
        loser = sorted(losing_rows, key=lambda row: float(row["weekly_points"]), reverse=True)[0]
        awards.append(
            SidePointAwardRow(
                team_id=int(loser["team_id"]),
                owner=loser["owner"],
                category="Highest score in loss",
                points=0.5,
                metric_name="weekly_points",
                metric_value=float(loser["weekly_points"]),
            )
        )

    overall = sorted(enriched, key=lambda row: float(row["weekly_points"]), reverse=True)
    if len(overall) > 1 and float(overall[1].get("plus_minus", 0)) < 0:
        row = overall[1]
        awards.append(
            SidePointAwardRow(
                team_id=int(row["team_id"]),
                owner=row["owner"],
                category="Second-highest score in loss",
                points=1.0,
                metric_name="weekly_points",
                metric_value=float(row["weekly_points"]),
            )
        )

    return [award for award in awards if award.points != 0]
