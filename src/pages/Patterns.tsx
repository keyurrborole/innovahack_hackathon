import { DashboardLayout } from "../components/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Layers, Repeat, BarChart3, Moon, UserSearch } from "lucide-react";

const patterns = [
  {
    id: 1,
    name: "Rapid layering",
    icon: Layers,
    description:
      "Funds move quickly through many internal accounts, products, or branches to obscure origin before settlement or external transfer.",
    color: "text-red-500",
    bgColor: "bg-red-50 dark:bg-red-900/20",
    borderColor: "border-red-200 dark:border-red-800",
    riskLevel: "Critical",
    example: "Savings → current → NEFT hub → sweep → forex desk within minutes",
    indicators: [
      "High hop count in a short time window",
      "Small residual balance left at each hop",
      "Cross-product jumps (e.g. loan disbursement → CASA → card load)",
      "Velocity inconsistent with declared business use",
    ],
    detection: "Temporal graph walks + shortest-time path scoring; ML risk score on path features",
    svg: (
      <svg viewBox="0 0 200 120" className="w-full h-32">
        {[0, 1, 2, 3, 4].map((i) => (
          <g key={i}>
            <circle cx={25 + i * 35} cy={60 - (i % 2) * 15} r={10} fill={i % 2 === 0 ? "#ef4444" : "#64748b"} />
            {i < 4 && (
              <line
                x1={35 + i * 35}
                y1={60 - (i % 2) * 15}
                x2={25 + (i + 1) * 35 - 10}
                y2={60 - ((i + 1) % 2) * 15}
                stroke="#94a3b8"
                strokeWidth="2"
              />
            )}
          </g>
        ))}
        <text x="100" y="105" textAnchor="middle" className="fill-gray-500 text-[9px]">
          fast hops across accounts
        </text>
      </svg>
    ),
  },
  {
    id: 2,
    name: "Circular transactions (round-tripping)",
    icon: Repeat,
    description:
      "Money leaves an account or branch and returns through a loop of related parties, inflating turnover or hiding beneficial ownership.",
    color: "text-purple-500",
    bgColor: "bg-purple-50 dark:bg-purple-900/20",
    borderColor: "border-purple-200 dark:border-purple-800",
    riskLevel: "High",
    example: "A → B → C → D → A with correlated timing and rounded amounts",
    indicators: [
      "Directed cycle in the account graph within reporting period",
      "Similar amounts at cycle closure",
      "Related customer IDs or shared branch/channel fingerprints",
    ],
    detection: "Cycle enumeration (SCC + DFS) on daily slices; pattern rules + GNN edge attention",
    svg: (
      <svg viewBox="0 0 200 120" className="w-full h-32">
        {["A", "B", "C", "D", "E"].map((label, i) => {
          const angle = (i * (360 / 5) - 90) * (Math.PI / 180);
          const x = 100 + 55 * Math.cos(angle);
          const y = 55 + 38 * Math.sin(angle);
          const nextAngle = ((i + 1) * (360 / 5) - 90) * (Math.PI / 180);
          const nx = 100 + 55 * Math.cos(nextAngle);
          const ny = 55 + 38 * Math.sin(nextAngle);
          return (
            <g key={i}>
              <line x1={x} y1={y} x2={nx} y2={ny} stroke="#94a3b8" strokeWidth="2" />
              <circle cx={x} cy={y} r="11" fill="#a855f7" />
              <text x={x} y={y + 4} textAnchor="middle" fill="white" fontSize="10">
                {label}
              </text>
            </g>
          );
        })}
      </svg>
    ),
  },
  {
    id: 3,
    name: "Structuring",
    icon: BarChart3,
    description:
      "Multiple transfers sized just below internal or regulatory reporting thresholds to avoid automated controls.",
    color: "text-orange-500",
    bgColor: "bg-orange-50 dark:bg-orange-900/20",
    borderColor: "border-orange-200 dark:border-orange-800",
    riskLevel: "High",
    example: "Repeated ₹49,000 / ₹9,900 legs when threshold is ₹50,000 / ₹10,000",
    indicators: [
      "Cluster of amounts in a band just under threshold",
      "Same initiator or beneficiary pattern",
      "Channel split (branch + mobile + UPI) in one day",
    ],
    detection: "Histogram proximity to thresholds + burst detection; ensemble with ML amount-embedding",
    svg: (
      <svg viewBox="0 0 200 120" className="w-full h-32">
        {[48, 49, 49.5, 49.2, 49.8].map((v, i) => (
          <rect
            key={i}
            x={30 + i * 28}
            y={80 - v}
            width="18"
            height={v}
            fill="#f97316"
            opacity={0.7 + i * 0.05}
          />
        ))}
        <line x1="20" y1="30" x2="180" y2="30" stroke="#ef4444" strokeDasharray="4" />
        <text x="140" y="24" fontSize="9" fill="#ef4444">
          threshold
        </text>
      </svg>
    ),
  },
  {
    id: 4,
    name: "Dormant account activity",
    icon: Moon,
    description:
      "Long-inactive CASA or term-linked accounts suddenly receive or send large-value transfers.",
    color: "text-yellow-500",
    bgColor: "bg-yellow-50 dark:bg-yellow-900/20",
    borderColor: "border-yellow-200 dark:border-yellow-800",
    riskLevel: "Medium",
    example: "No txn for 18 months → sudden ₹25L inward via IMPS",
    indicators: [
      "Days-since-last-txn exceeds policy",
      "First large credit or debit after dormancy",
      "Mismatch with historical velocity",
    ],
    detection: "Account state features + survival-style dormancy score; rule triggers for investigators",
    svg: (
      <svg viewBox="0 0 200 120" className="w-full h-32">
        <text x="30" y="95" fontSize="10" fill="#64748b">
          quiet
        </text>
        <line x1="40" y1="70" x2="120" y2="70" stroke="#cbd5e1" strokeWidth="3" />
        <circle cx="130" cy="70" r="14" fill="#eab308" />
        <text x="120" y="50" fontSize="9" fill="#ca8a04">
          spike
        </text>
        <path d="M 130 56 L 160 30" stroke="#eab308" strokeWidth="2" />
      </svg>
    ),
  },
  {
    id: 5,
    name: "Profile mismatch",
    icon: UserSearch,
    description:
      "Observed fund movement (velocity, counterparties, channels) diverges from KYC-declared occupation, turnover, or geography.",
    color: "text-pink-500",
    bgColor: "bg-pink-50 dark:bg-pink-900/20",
    borderColor: "border-pink-200 dark:border-pink-800",
    riskLevel: "High",
    example: "Salaried profile with daily high-value business-like counterparty fan-out",
    indicators: [
      "Deviation from peer cluster in embedding space",
      "Channel mix unlike declared segment",
      "Counterparty concentration vs stated activity",
    ],
    detection: "Customer profile vector vs graph-derived behavior vector; cosine / classifier mismatch flag",
    svg: (
      <svg viewBox="0 0 200 120" className="w-full h-32">
        <circle cx="50" cy="55" r="22" fill="#fce7f3" stroke="#ec4899" />
        <text x="50" y="58" textAnchor="middle" fontSize="9" fill="#9d174d">
          KYC
        </text>
        <circle cx="150" cy="55" r="28" fill="none" stroke="#94a3b8" strokeDasharray="4" />
        <text x="150" y="58" textAnchor="middle" fontSize="9" fill="#64748b">
          actual flow
        </text>
        <line x1="72" y1="55" x2="122" y2="55" stroke="#ec4899" strokeWidth="2" markerEnd="url(#arr)" />
        <defs>
          <marker id="arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <polygon points="0 0, 6 3, 0 6" fill="#ec4899" />
          </marker>
        </defs>
      </svg>
    ),
  },
];

export default function Patterns() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">Fraud pattern library</h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            PS3-aligned typologies: graph analytics and ML surface these for analyst review and FIU packaging.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {patterns.map((pattern) => (
            <Card
              key={pattern.id}
              className={`${pattern.bgColor} ${pattern.borderColor} border-2 hover:shadow-xl transition-all duration-300`}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`p-3 rounded-lg ${pattern.bgColor}`}>
                      <pattern.icon className={`h-6 w-6 ${pattern.color}`} />
                    </div>
                    <div>
                      <CardTitle className="text-xl text-gray-900 dark:text-white">{pattern.name}</CardTitle>
                      <Badge
                        className={`mt-1 ${
                          pattern.riskLevel === "Critical"
                            ? "bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-200"
                            : pattern.riskLevel === "High"
                              ? "bg-orange-100 text-orange-800 dark:bg-orange-900/50 dark:text-orange-200"
                              : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-200"
                        }`}
                      >
                        {pattern.riskLevel} risk
                      </Badge>
                    </div>
                  </div>
                </div>
                <CardDescription className="mt-3 text-gray-700 dark:text-gray-300">
                  {pattern.description}
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="bg-white dark:bg-gray-800/50 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                  {pattern.svg}
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Example</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 font-mono bg-white dark:bg-gray-800/50 p-2 rounded border border-gray-200 dark:border-gray-700">
                    {pattern.example}
                  </p>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Detection approach</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-800/50 p-2 rounded border border-gray-200 dark:border-gray-700">
                    {pattern.detection}
                  </p>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Key indicators</h4>
                  <ul className="space-y-1">
                    {pattern.indicators.map((indicator, idx) => (
                      <li key={idx} className="text-sm text-gray-600 dark:text-gray-400 flex items-start space-x-2">
                        <span className={`${pattern.color} mt-1`}>•</span>
                        <span>{indicator}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card className="bg-gradient-to-br from-crypto-purple/10 to-pink-600/10 dark:from-crypto-purple/20 dark:to-pink-600/20 border-crypto-purple/30">
          <CardHeader>
            <CardTitle className="text-gray-900 dark:text-white">How graph analytics and ML fit together</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white dark:bg-gray-800/50 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">1. Unified fund-flow graph</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Nodes: accounts and customers; edges: transfers enriched with product, branch, channel, and timestamp.
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800/50 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">2. Rich features</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Graph metrics (centrality, cycles), sequence features (velocity), and KYC/profile embeddings per
                  customer.
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800/50 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">3. Detection stack</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Rule graph (thresholds, dormancy) plus ML classifiers / GNN layers for suspicion scoring and
                  explainable subgraphs for investigators.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
