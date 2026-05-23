// Mock data for Business Control Hub — Meridian Solutions SRL

export type InvoiceStatus = "paid" | "pending" | "overdue";
export type ExpenseCategory =
  | "Software"
  | "Travel"
  | "Office"
  | "Marketing"
  | "Utilities"
  | "HR"
  | "Equipment"
  | "Legal";

export interface Invoice {
  id: string;
  number: string;
  client: string;
  amount: number;
  currency: string;
  status: InvoiceStatus;
  issueDate: string;
  dueDate: string;
  description: string;
}

export interface Expense {
  id: string;
  description: string;
  amount: number;
  currency: string;
  category: ExpenseCategory;
  date: string;
  vendor: string;
  approved: boolean;
}

export interface CashflowMonth {
  month: string;
  income: number;
  expenses: number;
  net: number;
}

export interface AiInsight {
  id: string;
  type: "warning" | "opportunity" | "info";
  title: string;
  body: string;
  action: string;
  createdAt: string;
}

export interface Notification {
  id: string;
  title: string;
  body: string;
  type: "invoice" | "expense" | "alert" | "info";
  read: boolean;
  createdAt: string;
}

// ─── Invoices ────────────────────────────────────────────────────────────────

export const invoices: Invoice[] = [
  {
    id: "inv-001",
    number: "FAC-2024-0142",
    client: "Technobit SRL",
    amount: 28500,
    currency: "RON",
    status: "paid",
    issueDate: "2024-11-01",
    dueDate: "2024-11-15",
    description: "Consultanță IT – Octombrie 2024",
  },
  {
    id: "inv-002",
    number: "FAC-2024-0143",
    client: "Alfa Distribution SA",
    amount: 45200,
    currency: "RON",
    status: "paid",
    issueDate: "2024-11-05",
    dueDate: "2024-11-20",
    description: "Implementare ERP modul logistică",
  },
  {
    id: "inv-003",
    number: "FAC-2024-0144",
    client: "Construct Pro SRL",
    amount: 12750,
    currency: "RON",
    status: "pending",
    issueDate: "2024-11-10",
    dueDate: "2024-11-25",
    description: "Licențe software anuale",
  },
  {
    id: "inv-004",
    number: "FAC-2024-0145",
    client: "MedVita Clinic SRL",
    amount: 8900,
    currency: "RON",
    status: "pending",
    issueDate: "2024-11-12",
    dueDate: "2024-11-27",
    description: "Mentenanță aplicație pacienti",
  },
  {
    id: "inv-005",
    number: "FAC-2024-0146",
    client: "Green Energy Partners",
    amount: 67300,
    currency: "RON",
    status: "overdue",
    issueDate: "2024-10-15",
    dueDate: "2024-10-30",
    description: "Audit energetic + raport tehnic",
  },
  {
    id: "inv-006",
    number: "FAC-2024-0147",
    client: "LogiTrans SRL",
    amount: 19400,
    currency: "RON",
    status: "overdue",
    issueDate: "2024-10-20",
    dueDate: "2024-11-04",
    description: "Optimizare rute – proiect pilot",
  },
  {
    id: "inv-007",
    number: "FAC-2024-0148",
    client: "Arcadia Hotels SA",
    amount: 34600,
    currency: "RON",
    status: "paid",
    issueDate: "2024-11-14",
    dueDate: "2024-11-29",
    description: "Sistem rezervări online – faza 2",
  },
  {
    id: "inv-008",
    number: "FAC-2024-0149",
    client: "FoodFactory SRL",
    amount: 22100,
    currency: "RON",
    status: "pending",
    issueDate: "2024-11-15",
    dueDate: "2024-11-30",
    description: "Integrare POS și gestiune stocuri",
  },
  {
    id: "inv-009",
    number: "FAC-2024-0150",
    client: "BioFarm SA",
    amount: 41800,
    currency: "RON",
    status: "paid",
    issueDate: "2024-11-18",
    dueDate: "2024-12-03",
    description: "Portal angajati – HR digital",
  },
  {
    id: "inv-010",
    number: "FAC-2024-0151",
    client: "Stelar Construct SRL",
    amount: 15600,
    currency: "RON",
    status: "pending",
    issueDate: "2024-11-19",
    dueDate: "2024-12-04",
    description: "Module raportare financiara",
  },
  {
    id: "inv-011",
    number: "FAC-2024-0152",
    client: "AutoFleet Romania SRL",
    amount: 9800,
    currency: "RON",
    status: "overdue",
    issueDate: "2024-10-05",
    dueDate: "2024-10-20",
    description: "Abonament telematică flotă – Q4",
  },
  {
    id: "inv-012",
    number: "FAC-2024-0153",
    client: "Printex Media SRL",
    amount: 5400,
    currency: "RON",
    status: "paid",
    issueDate: "2024-11-20",
    dueDate: "2024-12-05",
    description: "Redesign site corporate",
  },
  {
    id: "inv-013",
    number: "FAC-2024-0154",
    client: "EduTech Platform SA",
    amount: 31200,
    currency: "RON",
    status: "paid",
    issueDate: "2024-11-21",
    dueDate: "2024-12-06",
    description: "Platformă e-learning – licență anuală",
  },
  {
    id: "inv-014",
    number: "FAC-2024-0155",
    client: "RomAlpin SRL",
    amount: 18700,
    currency: "RON",
    status: "pending",
    issueDate: "2024-11-22",
    dueDate: "2024-12-07",
    description: "Servicii cloud migration",
  },
  {
    id: "inv-015",
    number: "FAC-2024-0156",
    client: "TeleStar Communications SA",
    amount: 52400,
    currency: "RON",
    status: "pending",
    issueDate: "2024-11-23",
    dueDate: "2024-12-08",
    description: "Infrastructură VoIP – 3 sedii",
  },
  {
    id: "inv-016",
    number: "FAC-2024-0157",
    client: "Farmacia Buna Sanatate SRL",
    amount: 7200,
    currency: "RON",
    status: "paid",
    issueDate: "2024-11-24",
    dueDate: "2024-12-09",
    description: "Integrare casa marcat",
  },
  {
    id: "inv-017",
    number: "FAC-2024-0158",
    client: "IronGate Security SRL",
    amount: 14300,
    currency: "RON",
    status: "overdue",
    issueDate: "2024-10-10",
    dueDate: "2024-10-25",
    description: "Sistem supraveghere video – upgrade",
  },
  {
    id: "inv-018",
    number: "FAC-2024-0159",
    client: "UrbanEstate Developers SA",
    amount: 89500,
    currency: "RON",
    status: "paid",
    issueDate: "2024-11-25",
    dueDate: "2024-12-10",
    description: "Platforma imobiliara custom – faza 3",
  },
  {
    id: "inv-019",
    number: "FAC-2024-0160",
    client: "ColdChain Logistics SRL",
    amount: 26400,
    currency: "RON",
    status: "pending",
    issueDate: "2024-11-26",
    dueDate: "2024-12-11",
    description: "Senzori IoT + dashboard monitoring",
  },
  {
    id: "inv-020",
    number: "FAC-2024-0161",
    client: "Nexus Finance IFN SA",
    amount: 38700,
    currency: "RON",
    status: "pending",
    issueDate: "2024-11-27",
    dueDate: "2024-12-12",
    description: "Modul scorare credit AI",
  },
];

// ─── Expenses ─────────────────────────────────────────────────────────────────

export const expenses: Expense[] = [
  {
    id: "exp-001",
    description: "Abonament Microsoft 365 Business",
    amount: 2340,
    currency: "RON",
    category: "Software",
    date: "2024-11-01",
    vendor: "Microsoft Romania SRL",
    approved: true,
  },
  {
    id: "exp-002",
    description: "Bilete avion București–Londra (echipă)",
    amount: 8700,
    currency: "RON",
    category: "Travel",
    date: "2024-11-03",
    vendor: "Booking.com",
    approved: true,
  },
  {
    id: "exp-003",
    description: "Rechizite birou și consumabile",
    amount: 1250,
    currency: "RON",
    category: "Office",
    date: "2024-11-04",
    vendor: "Iris Office SRL",
    approved: true,
  },
  {
    id: "exp-004",
    description: "Campanie Google Ads – noiembrie",
    amount: 4500,
    currency: "RON",
    category: "Marketing",
    date: "2024-11-05",
    vendor: "Google Romania",
    approved: true,
  },
  {
    id: "exp-005",
    description: "Factură curent electric sediu",
    amount: 1890,
    currency: "RON",
    category: "Utilities",
    date: "2024-11-05",
    vendor: "Electrica SA",
    approved: true,
  },
  {
    id: "exp-006",
    description: "Salariu net + contribuții – octombrie",
    amount: 42000,
    currency: "RON",
    category: "HR",
    date: "2024-11-06",
    vendor: "Meridian Solutions SRL – Payroll",
    approved: true,
  },
  {
    id: "exp-007",
    description: "Laptop Dell XPS 15 – dezvoltator nou",
    amount: 7200,
    currency: "RON",
    category: "Equipment",
    date: "2024-11-07",
    vendor: "PC Garage SRL",
    approved: true,
  },
  {
    id: "exp-008",
    description: "Consultanță juridică – contract GDPR",
    amount: 3200,
    currency: "RON",
    category: "Legal",
    date: "2024-11-08",
    vendor: "Popescu & Asociații",
    approved: true,
  },
  {
    id: "exp-009",
    description: "GitHub Teams – 12 seat",
    amount: 1560,
    currency: "RON",
    category: "Software",
    date: "2024-11-09",
    vendor: "GitHub Inc.",
    approved: true,
  },
  {
    id: "exp-010",
    description: "Hotel + transport – conferință ClujTech",
    amount: 3400,
    currency: "RON",
    category: "Travel",
    date: "2024-11-10",
    vendor: "Radisson Hotel Cluj",
    approved: true,
  },
  {
    id: "exp-011",
    description: "Abonament Figma – echipă design",
    amount: 890,
    currency: "RON",
    category: "Software",
    date: "2024-11-11",
    vendor: "Figma Inc.",
    approved: true,
  },
  {
    id: "exp-012",
    description: "Cafea, apă, produse bucătărie",
    amount: 480,
    currency: "RON",
    category: "Office",
    date: "2024-11-12",
    vendor: "Metro Cash & Carry",
    approved: true,
  },
  {
    id: "exp-013",
    description: "Servicii contabilitate – octombrie",
    amount: 2800,
    currency: "RON",
    category: "Legal",
    date: "2024-11-13",
    vendor: "Contax Experts SRL",
    approved: true,
  },
  {
    id: "exp-014",
    description: "Campanie LinkedIn Ads",
    amount: 2100,
    currency: "RON",
    category: "Marketing",
    date: "2024-11-14",
    vendor: "LinkedIn Ireland",
    approved: false,
  },
  {
    id: "exp-015",
    description: "Internet fibră optică + telefonie",
    amount: 620,
    currency: "RON",
    category: "Utilities",
    date: "2024-11-14",
    vendor: "Digi Communications SA",
    approved: true,
  },
  {
    id: "exp-016",
    description: "AWS EC2 + S3 – hosting producție",
    amount: 5600,
    currency: "RON",
    category: "Software",
    date: "2024-11-15",
    vendor: "Amazon Web Services",
    approved: true,
  },
  {
    id: "exp-017",
    description: "Imprimantă HP LaserJet – recepție",
    amount: 1850,
    currency: "RON",
    category: "Equipment",
    date: "2024-11-16",
    vendor: "Flanco Retail SRL",
    approved: true,
  },
  {
    id: "exp-018",
    description: "Masă business – client TeleStar",
    amount: 780,
    currency: "RON",
    category: "Travel",
    date: "2024-11-18",
    vendor: "Restaurant Caru cu Bere",
    approved: true,
  },
  {
    id: "exp-019",
    description: "Bonus performanță Q3 – echipă",
    amount: 12000,
    currency: "RON",
    category: "HR",
    date: "2024-11-20",
    vendor: "Meridian Solutions SRL – Payroll",
    approved: false,
  },
  {
    id: "exp-020",
    description: "Curs certificare AWS – 2 persoane",
    amount: 3600,
    currency: "RON",
    category: "HR",
    date: "2024-11-21",
    vendor: "Simplilearn",
    approved: true,
  },
  {
    id: "exp-021",
    description: "Domeniu .ro + SSL wildcard",
    amount: 340,
    currency: "RON",
    category: "Software",
    date: "2024-11-22",
    vendor: "NameCheap Inc.",
    approved: true,
  },
  {
    id: "exp-022",
    description: "Chirie spațiu birou – decembrie (avans)",
    amount: 18000,
    currency: "RON",
    category: "Office",
    date: "2024-11-23",
    vendor: "Imobiliare Premium SRL",
    approved: true,
  },
  {
    id: "exp-023",
    description: "Materiale promotional – eveniment",
    amount: 2200,
    currency: "RON",
    category: "Marketing",
    date: "2024-11-24",
    vendor: "PrintXpress SRL",
    approved: false,
  },
  {
    id: "exp-024",
    description: "Asigurare RCA flotă auto – 3 vehicule",
    amount: 4100,
    currency: "RON",
    category: "Legal",
    date: "2024-11-25",
    vendor: "Generali Asigurari SA",
    approved: true,
  },
  {
    id: "exp-025",
    description: "Monitor 4K LG – birou directori",
    amount: 2900,
    currency: "RON",
    category: "Equipment",
    date: "2024-11-26",
    vendor: "eMAG SRL",
    approved: true,
  },
  {
    id: "exp-026",
    description: "Abonament Slack Pro – 15 utilizatori",
    amount: 1120,
    currency: "RON",
    category: "Software",
    date: "2024-11-27",
    vendor: "Slack Technologies",
    approved: true,
  },
  {
    id: "exp-027",
    description: "Abonament Notion – team plan",
    amount: 680,
    currency: "RON",
    category: "Software",
    date: "2024-11-28",
    vendor: "Notion Labs Inc.",
    approved: true,
  },
  {
    id: "exp-028",
    description: "Taxe poștale și curierat",
    amount: 220,
    currency: "RON",
    category: "Office",
    date: "2024-11-28",
    vendor: "DHL Romania",
    approved: true,
  },
  {
    id: "exp-029",
    description: "Abonament Jira + Confluence",
    amount: 1780,
    currency: "RON",
    category: "Software",
    date: "2024-11-29",
    vendor: "Atlassian",
    approved: true,
  },
  {
    id: "exp-030",
    description: "Team building – trimestrul 4",
    amount: 5500,
    currency: "RON",
    category: "HR",
    date: "2024-11-30",
    vendor: "Eventsphere SRL",
    approved: false,
  },
];

// ─── Cashflow (6 months) ──────────────────────────────────────────────────────

export const cashflowData: CashflowMonth[] = [
  { month: "Jun", income: 198400, expenses: 142600, net: 55800 },
  { month: "Jul", income: 212700, expenses: 158300, net: 54400 },
  { month: "Aug", income: 185200, expenses: 134900, net: 50300 },
  { month: "Sep", income: 241500, expenses: 167200, net: 74300 },
  { month: "Oct", income: 268300, expenses: 189700, net: 78600 },
  { month: "Nov", income: 294100, expenses: 142980, net: 151120 },
];

// ─── AI Insights ──────────────────────────────────────────────────────────────

export const aiInsights: AiInsight[] = [
  {
    id: "ins-001",
    type: "warning",
    title: "3 facturi scadente în 7 zile",
    body:
      "Green Energy Partners, LogiTrans SRL și AutoFleet Romania au facturi restante cu o valoare totală de 96.500 RON. Probabilitatea de încasare în termen scade cu 22% după 30 de zile.",
    action: "Vezi facturile scadente",
    createdAt: "2024-11-27T09:00:00Z",
  },
  {
    id: "ins-002",
    type: "opportunity",
    title: "Flux de numerar pozitiv — cel mai bun din semestru",
    body:
      "Noiembrie înregistrează un net cash flow de +151.120 RON, cu 92% mai mare decât luna precedentă. Se recomandă alocarea a 40% în fond de rezervă și 30% în investiții echipamente.",
    action: "Planifică alocarea",
    createdAt: "2024-11-27T09:00:00Z",
  },
  {
    id: "ins-003",
    type: "info",
    title: "Cheltuielile cu software au crescut cu 18%",
    body:
      "Costurile lunare cu abonamente software sunt acum 14.870 RON (+18% față de Q3). Consolidarea licențelor Microsoft și GitHub ar putea genera economii estimate de 2.100 RON/lună.",
    action: "Analizează abonamentele",
    createdAt: "2024-11-27T09:00:00Z",
  },
  {
    id: "ins-004",
    type: "opportunity",
    title: "Client cu potențial de upsell: Nexus Finance",
    body:
      "Nexus Finance IFN SA a achiziționat modulul de scorare AI. Profilul lor indică potențial pentru modulele de raportare reglatorie (DORA, PSD2) — valoare estimată 75.000 RON.",
    action: "Creează propunere",
    createdAt: "2024-11-26T14:30:00Z",
  },
];

// ─── Notifications ────────────────────────────────────────────────────────────

export const notifications: Notification[] = [
  {
    id: "notif-001",
    title: "Factură FAC-2024-0161 emisă",
    body: "Nexus Finance IFN SA – 38.700 RON. Scadent pe 12 dec.",
    type: "invoice",
    read: false,
    createdAt: "2024-11-27T10:00:00Z",
  },
  {
    id: "notif-002",
    title: "Cheltuială în așteptare aprobare",
    body: "Bonus performanță Q3 – 12.000 RON necesită aprobare director.",
    type: "expense",
    read: false,
    createdAt: "2024-11-27T09:45:00Z",
  },
  {
    id: "notif-003",
    title: "Factură restantă – Green Energy Partners",
    body: "FAC-2024-0146 (67.300 RON) are 28 de zile întârziere.",
    type: "alert",
    read: false,
    createdAt: "2024-11-27T08:00:00Z",
  },
  {
    id: "notif-004",
    title: "Raport lunar generat",
    body: "Raportul de activitate pentru octombrie 2024 este disponibil.",
    type: "info",
    read: true,
    createdAt: "2024-11-26T17:00:00Z",
  },
  {
    id: "notif-005",
    title: "Plată primită – BioFarm SA",
    body: "FAC-2024-0150 (41.800 RON) a fost încasată integral.",
    type: "invoice",
    read: true,
    createdAt: "2024-11-26T11:20:00Z",
  },
];

// ─── Summary Metrics ──────────────────────────────────────────────────────────

export const summaryMetrics = {
  revenueMTD: 294100,
  revenuePrev: 268300,
  expensesMTD: 142980,
  expensesPrev: 189700,
  netCashFlow: 151120,
  netCashFlowPrev: 78600,
  outstandingInvoices: invoices
    .filter((i) => i.status === "pending" || i.status === "overdue")
    .reduce((sum, i) => sum + i.amount, 0),
  outstandingCount: invoices.filter((i) => i.status === "pending" || i.status === "overdue").length,
  overdueAmount: invoices
    .filter((i) => i.status === "overdue")
    .reduce((sum, i) => sum + i.amount, 0),
  overdueCount: invoices.filter((i) => i.status === "overdue").length,
};

// ─── Document types ───────────────────────────────────────────────────────────

export interface Document {
  id: string;
  name: string;
  type: "contract" | "invoice" | "report" | "other";
  size: string;
  uploadedAt: string;
  uploadedBy: string;
  tags: string[];
}

export const documents: Document[] = [
  {
    id: "doc-001",
    name: "Contract servicii – Technobit SRL.pdf",
    type: "contract",
    size: "1.2 MB",
    uploadedAt: "2024-11-01",
    uploadedBy: "Andrei Popescu",
    tags: ["contract", "client", "IT"],
  },
  {
    id: "doc-002",
    name: "Raport financiar Q3 2024.xlsx",
    type: "report",
    size: "840 KB",
    uploadedAt: "2024-10-31",
    uploadedBy: "Maria Ionescu",
    tags: ["raport", "Q3", "financiar"],
  },
  {
    id: "doc-003",
    name: "Politică GDPR actualizată 2024.pdf",
    type: "other",
    size: "560 KB",
    uploadedAt: "2024-11-08",
    uploadedBy: "Andrei Popescu",
    tags: ["GDPR", "legal", "politică"],
  },
  {
    id: "doc-004",
    name: "FAC-2024-0150 – BioFarm SA.pdf",
    type: "invoice",
    size: "210 KB",
    uploadedAt: "2024-11-18",
    uploadedBy: "Elena Constantin",
    tags: ["factură", "BioFarm"],
  },
  {
    id: "doc-005",
    name: "Contract chirie birou – 2025.pdf",
    type: "contract",
    size: "1.8 MB",
    uploadedAt: "2024-11-23",
    uploadedBy: "Andrei Popescu",
    tags: ["contract", "chirie", "sediu"],
  },
  {
    id: "doc-006",
    name: "Bilanț contabil oct 2024.pdf",
    type: "report",
    size: "1.1 MB",
    uploadedAt: "2024-11-13",
    uploadedBy: "Maria Ionescu",
    tags: ["bilanț", "contabilitate"],
  },
  {
    id: "doc-007",
    name: "Acord confidențialitate – Green Energy.pdf",
    type: "contract",
    size: "480 KB",
    uploadedAt: "2024-10-14",
    uploadedBy: "Andrei Popescu",
    tags: ["NDA", "contract", "client"],
  },
  {
    id: "doc-008",
    name: "Raport audit intern – noiembrie.pdf",
    type: "report",
    size: "2.3 MB",
    uploadedAt: "2024-11-25",
    uploadedBy: "Elena Constantin",
    tags: ["audit", "intern", "calitate"],
  },
];
