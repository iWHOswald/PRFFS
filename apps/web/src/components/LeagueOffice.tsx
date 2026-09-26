import { useMemo, useState } from "react";
import { BadgeDollarSign, Crown, FileText, Gavel, Landmark, Network, Scale, ShieldCheck, Users } from "lucide-react";

type OfficeNode = {
  id: string;
  title: string;
  branch: "Executive" | "Judicial" | "Advisory" | "Competitive";
  holder: string;
  tenure: string;
  filledBy: string;
  eligibility: string[];
  duties: string[];
  authorities: string[];
  notes?: string[];
  source: string;
  children?: string[];
};

const offices: OfficeNode[] = [
  {
    id: "commissioner",
    title: "League Manager / Commissioner",
    branch: "Executive",
    holder: "Iain Oswald - Granulars Geriatrics",
    tenure: "Continuing office; appointed by the current Commissioner.",
    filledBy: "Appointment by current Commissioner.",
    eligibility: ["May not be dissolved by amendment.", "Final approval authority for prospective owners."],
    duties: [
      "Uphold and protect the Constitution.",
      "Oversee amendments and the Constitutional Convention.",
      "Ratify or let amendments pass into law.",
      "Enforce Supreme Pork Court rulings and punishments.",
      "Run Game of the Week, power rankings, draft order, and draft-day logistics.",
      "Manually change a team only with owner authorization and prior league notice."
    ],
    authorities: [
      "Ultimate authority over The League.",
      "May temporarily allocate defined powers to the Vice-Commissioner.",
      "May veto propositions within the constitutional veto window.",
      "May execute the Death Penalty provision in extreme cases.",
      "Breaks tied proposition results in favor of his preference."
    ],
    notes: ["Current office holder supplied by league admin and matched to the current ESPN team list."],
    source: "Article I.1, Article IV.1, Article VI.1, Article VI.3",
    children: ["vice", "comptroller", "ombudsman", "court", "great-powers"]
  },
  {
    id: "vice",
    title: "Vice-Commissioner",
    branch: "Executive",
    holder: "marcus tatum - Midda Quiznatodd Bidness",
    tenure: "About one year; no limit on consecutive terms.",
    filledBy: "Volunteer basis at Constitutional Convention; Commissioner appoints if contested or vacant.",
    eligibility: ["Minimum two league seasons.", "Prior dues paid.", "Cannot hold another official position in the same season."],
    duties: [
      "Write and upload Game of the Week when delegated.",
      "Write post-week or other league updates when delegated.",
      "Manually change a team only with owner authorization.",
      "Execute other Commissioner powers only as expressly delegated."
    ],
    authorities: ["Second in command after the League Manager.", "Temporary delegated authority only after league notice."],
    notes: ["Current office holder supplied by league admin and matched to the current ESPN team list."],
    source: "Article I.2, Article V.1"
  },
  {
    id: "comptroller",
    title: "Comptroller",
    branch: "Executive",
    holder: "James Oswald - Wembley Dumpenshire",
    tenure: "About one year.",
    filledBy: "Volunteer basis at Constitutional Convention; Commissioner appoints if contested or vacant.",
    eligibility: ["Minimum two league seasons.", "Prior dues paid.", "Cannot hold another official position in the same season."],
    duties: [
      "Collect league dues.",
      "Distribute payouts.",
      "Coordinate payment status with the Commissioner.",
      "Enforce payment policy with haste."
    ],
    authorities: ["Controls monetary flow in The League.", "Administers dues and payouts under Article III.8."],
    notes: ["Current office holder supplied by league admin and matched to the current ESPN team list."],
    source: "Article I.4, Article III.8, Article V.1"
  },
  {
    id: "ombudsman",
    title: "Ombudsman",
    branch: "Executive",
    holder: "Grant R. - 🍆A L L - B O  N I X - M E N🍆 (tentative)",
    tenure: "Case-by-case; office surrendered when investigation ends.",
    filledBy: "Appointed by the Justices of the Pork for a specific matter; Commissioner announces within 24 hours.",
    eligibility: [
      "Must be neutral in relation to the matter.",
      "Commissioner and current Justices are ineligible.",
      "Cannot declare guilt, innocence, or punishment."
    ],
    duties: [
      "Investigate suspected collusion, bribery, bad-faith dealings, or constitutional violations.",
      "Conduct fact-finding, interviews, and evidence collection.",
      "Offer advisory opinions and recommended punishment."
    ],
    authorities: ["Independent investigative oversight.", "Advisory power only."],
    notes: ["Marked tentative because the supplied office holder was Grant??.", "The Constitution treats this as a case-by-case appointment rather than a standing annual post."],
    source: "Article I.3"
  },
  {
    id: "court",
    title: "Supreme Pork Court",
    branch: "Judicial",
    holder: "Last recorded lineage: Kelton Koch, Tristan Oswald, Michael Walton",
    tenure: "Three-year staggered terms; consecutive partial terms not allowed.",
    filledBy: "Justice nominees are selected at the Constitutional Convention.",
    eligibility: [
      "Three owners total.",
      "One representative from each division.",
      "A Justice may not hold any other office simultaneously."
    ],
    duties: [
      "Rule on constitutional interpretation and due process.",
      "Grant fair and swift hearings to owners with grievances.",
      "Issue punishments, with enforcement left to the Commissioner.",
      "Investigate executives when necessary.",
      "Approve proposition text by at least two of three Justices."
    ],
    authorities: [
      "Can appoint an Ombudsman.",
      "Can investigate Commissioner, Vice-Commissioner, Ombudsman, and Comptroller.",
      "Subject to retention/removal by supermajority vote."
    ],
    notes: [
      "Initial 2018 Justices as of May 1, 2018: Kelton Koch (Brutal), Tristan Oswald (Porker), and J.C. Francis (Dumpster).",
      "May 7, 2018 update: Commissioner Iain Oswald removed J.C. Francis and appointed Michael Walton (Dumpster Juice) to a three-season term for 2018-2020.",
      "Current Justice seats still need confirmation."
    ],
    source: "Article II, Article IV.1, Article VI.2",
    children: ["justice-porker", "justice-brutal", "justice-dumpster"]
  },
  {
    id: "justice-porker",
    title: "Justice Seat: Porker Division",
    branch: "Judicial",
    holder: "Tristan Oswald - I Stan TaliasVan (initial 2018 Justice)",
    tenure: "Three-year staggered term.",
    filledBy: "Constitutional Convention nomination/selection.",
    eligibility: ["Must represent the Porker division.", "No simultaneous office."],
    duties: ["Serve on the Supreme Pork Court.", "Vote on proposition text and disputes."],
    authorities: ["One of three judicial votes."],
    notes: ["Last known Porker lineage entry from the 2018 Justice record."],
    source: "Article II.1"
  },
  {
    id: "justice-brutal",
    title: "Justice Seat: Brutal Division",
    branch: "Judicial",
    holder: "Kelton Koch - The Brussel Wilson Sprouts (initial 2018 Justice)",
    tenure: "Three-year staggered term.",
    filledBy: "Constitutional Convention nomination/selection.",
    eligibility: ["Must represent the Brutal division.", "No simultaneous office."],
    duties: ["Serve on the Supreme Pork Court.", "Vote on proposition text and disputes."],
    authorities: ["One of three judicial votes."],
    notes: ["Last known Brutal lineage entry from the 2018 Justice record."],
    source: "Article II.1"
  },
  {
    id: "justice-dumpster",
    title: "Justice Seat: Dumpster Division",
    branch: "Judicial",
    holder: "Michael Walton - Dumpster Juice (appointed 2018-2020)",
    tenure: "Three-year staggered term.",
    filledBy: "Constitutional Convention nomination/selection.",
    eligibility: ["Must represent the Dumpster division.", "No simultaneous office."],
    duties: ["Serve on the Supreme Pork Court.", "Vote on proposition text and disputes."],
    authorities: ["One of three judicial votes."],
    notes: ["J.C. Francis was the initial 2018 Dumpster Justice before being replaced on May 7, 2018."],
    source: "Article II.1"
  },
  {
    id: "great-powers",
    title: "The Great Powers",
    branch: "Advisory",
    holder: "Top five teams by weighted final standings: TBD",
    tenure: "Recomputed from the previous three seasons.",
    filledBy: "Weighted final standings: 50%, 33 1/3%, 16 2/3%.",
    eligibility: ["Top five teams by formula.", "Do not outrank executive or judicial offices."],
    duties: ["Serve as the official council to the Commissioner.", "Vote on certain issues when called upon."],
    authorities: [
      "Priority over non-Great Power owners when volunteering for official positions.",
      "Priority when declining a Commissioner appointment."
    ],
    source: "Article V.1, Article VI.4"
  },
  {
    id: "division-champs",
    title: "Divisional Champions",
    branch: "Competitive",
    holder: "Porker, Brutal, Dumpster: TBD",
    tenure: "Annual regular-season result.",
    filledBy: "Best total record in each division.",
    eligibility: ["One champion from each of Porker, Brutal, and Dumpster."],
    duties: ["Represent division results in playoff qualification."],
    authorities: ["Each division winner receives an automatic playoff berth."],
    source: "Article III.3, Article III.7"
  }
];

const branches = [
  { key: "Executive", icon: <Crown size={17} /> },
  { key: "Judicial", icon: <Scale size={17} /> },
  { key: "Advisory", icon: <Users size={17} /> },
  { key: "Competitive", icon: <ShieldCheck size={17} /> }
] as const;

export function LeagueOffice() {
  const [selectedId, setSelectedId] = useState("commissioner");
  const selected = useMemo(() => offices.find((office) => office.id === selectedId) ?? offices[0], [selectedId]);

  return (
    <section className="league-office">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Governance</span>
          <h2>League Office</h2>
        </div>
        <div className="status-pill">
          <Landmark size={17} />
          <span>Constitution ratified August 22, 2021</span>
        </div>
      </div>

      <section className="summary-grid office-summary">
        <OfficeStat icon={<Crown size={20} />} label="Executive offices" value="4" />
        <OfficeStat icon={<Gavel size={20} />} label="Judicial seats" value="3" />
        <OfficeStat icon={<BadgeDollarSign size={20} />} label="Dues authority" value="$50" />
      </section>

      <section className="office-layout">
        <section className="wide-panel office-tree-panel">
          <div className="panel-heading">
            <h2>Government Map</h2>
            <Network size={18} />
          </div>
          <div className="office-tree" aria-label="League office structure">
            <OfficeButton office={offices[0]} selected={selected.id === "commissioner"} onSelect={setSelectedId} />
            <div className="tree-branches">
              {["vice", "comptroller", "ombudsman", "court", "great-powers", "division-champs"].map((id) => {
                const office = offices.find((item) => item.id === id);
                return office ? (
                  <OfficeButton key={office.id} office={office} selected={selected.id === office.id} onSelect={setSelectedId} />
                ) : null;
              })}
            </div>
            <div className="tree-branches tree-branches-small">
              {["justice-porker", "justice-brutal", "justice-dumpster"].map((id) => {
                const office = offices.find((item) => item.id === id);
                return office ? (
                  <OfficeButton key={office.id} office={office} selected={selected.id === office.id} onSelect={setSelectedId} />
                ) : null;
              })}
            </div>
          </div>
        </section>

        <section className="panel office-detail">
          <div>
            <span className="office-branch">{selected.branch}</span>
            <h2>{selected.title}</h2>
            <strong>{selected.holder}</strong>
          </div>
          <OfficeDetailBlock title="Tenure" rows={[selected.tenure]} />
          <OfficeDetailBlock title="Filled By" rows={[selected.filledBy]} />
          <OfficeDetailBlock title="Eligibility" rows={selected.eligibility} />
          <OfficeDetailBlock title="Duties" rows={selected.duties} />
          <OfficeDetailBlock title="Authority" rows={selected.authorities} />
          {selected.notes ? <OfficeDetailBlock title="Notes" rows={selected.notes} /> : null}
          <p className="office-source">{selected.source}</p>
        </section>
      </section>

      <section className="wide-panel office-branches">
        <div className="panel-heading">
          <h2>Constitutional Branches</h2>
        </div>
        <div className="office-branch-grid">
          {branches.map((branch) => {
            const branchOffices = offices.filter((office) => office.branch === branch.key);
            return (
              <article key={branch.key} className="office-branch-card">
                <div>
                  {branch.icon}
                  <strong>{branch.key}</strong>
                </div>
                <span>{branchOffices.length} node{branchOffices.length === 1 ? "" : "s"}</span>
                <p>{branchOffices.map((office) => office.title).join(", ")}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section className="wide-panel constitution-panel">
        <div className="panel-heading">
          <h2>Constitution</h2>
          <a className="office-link" href="/api/constitution/pdf" target="_blank" rel="noreferrer">
            <FileText size={16} />
            <span>Open PDF</span>
          </a>
        </div>
        <iframe title="Pork Rub Fantasy Football Constitution" src="/api/constitution/pdf" />
      </section>
    </section>
  );
}

function OfficeStat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
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

function OfficeButton({ office, selected, onSelect }: { office: OfficeNode; selected: boolean; onSelect: (id: string) => void }) {
  return (
    <button className={selected ? "office-node is-active" : "office-node"} type="button" onClick={() => onSelect(office.id)}>
      <span>{office.branch}</span>
      <strong>{office.title}</strong>
      <em>{office.holder}</em>
    </button>
  );
}

function OfficeDetailBlock({ title, rows }: { title: string; rows: string[] }) {
  return (
    <div className="office-detail-block">
      <h3>{title}</h3>
      <ul>
        {rows.map((row) => (
          <li key={row}>{row}</li>
        ))}
      </ul>
    </div>
  );
}
