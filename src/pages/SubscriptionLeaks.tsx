import { useLocation, useNavigate } from "react-router-dom";
import { DashboardLayout } from "../components/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import {
  AlertTriangle, TrendingUp, Clock, CheckCircle2,
  XCircle, ArrowDownCircle, MessageSquare, ChevronDown,
  ChevronUp, Upload, IndianRupee
} from "lucide-react";
import { useState } from "react";

/* ─── Types ───────────────────────────────────────────────── */
interface Subscription {
  merchant: string;
  interval: string;
  recurrence_confidence: number;
  avg_amount: number;
  monthly_cost: number;
  total_paid: number;
  transaction_count: number;
  last_seen: string;
  first_seen: string;
  days_since_last: number;
  price_increase: { detected: boolean; pct_change?: number; first_avg?: number; last_avg?: number };
  leak_score: number;
  action: { action: string; reason: string; savings_estimate: number };
  is_known_subscription: boolean;
  sample_transactions: { date: string; amount: number; description: string }[];
}

interface AnalysisResult {
  overall_leak_score: number;
  subscriptions: Subscription[];
  summary: {
    total_subscriptions: number;
    total_monthly_spend: number;
    potential_monthly_savings: number;
    cancel_count: number;
    downgrade_count: number;
    renegotiate_count: number;
    price_increase_count: number;
  };
  transactions_parsed: number;
}

/* ─── Helpers ─────────────────────────────────────────────── */
const ACTION_CONFIG: Record<string, { color: string; icon: React.ElementType; label: string; bg: string }> = {
  cancel:      { color: "text-red-600 dark:text-red-400",    icon: XCircle,          label: "Cancel",      bg: "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800" },
  downgrade:   { color: "text-orange-600 dark:text-orange-400", icon: ArrowDownCircle, label: "Downgrade",   bg: "bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800" },
  renegotiate: { color: "text-yellow-600 dark:text-yellow-400", icon: MessageSquare,  label: "Renegotiate", bg: "bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800" },
  keep:        { color: "text-green-600 dark:text-green-400",  icon: CheckCircle2,    label: "Keep",        bg: "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800" },
};

const leakColor = (score: number) => {
  if (score >= 70) return "text-red-500";
  if (score >= 45) return "text-orange-500";
  if (score >= 25) return "text-yellow-500";
  return "text-green-500";
};

const LeakGauge = ({ score }: { score: number }) => {
  const color = score >= 70 ? "#ef4444" : score >= 45 ? "#f97316" : score >= 25 ? "#eab308" : "#22c55e";
  const r = 54;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  return (
    <svg viewBox="0 0 120 120" className="w-32 h-32">
      <circle cx="60" cy="60" r={r} fill="none" stroke="#e5e7eb" strokeWidth="12" className="dark:stroke-white/10" />
      <circle
        cx="60" cy="60" r={r} fill="none" stroke={color} strokeWidth="12"
        strokeDasharray={`${dash} ${circ - dash}`}
        strokeLinecap="round"
        transform="rotate(-90 60 60)"
        style={{ transition: "stroke-dasharray 1s ease" }}
      />
      <text x="60" y="55" textAnchor="middle" className="fill-gray-900 dark:fill-white font-bold" fontSize="22" fontWeight="bold" fill={color}>{score}</text>
      <text x="60" y="72" textAnchor="middle" fontSize="9" fill="#9ca3af">LEAK SCORE</text>
    </svg>
  );
};

/* ─── Card ────────────────────────────────────────────────── */
function SubCard({ sub }: { sub: Subscription }) {
  const [open, setOpen] = useState(false);
  const cfg = ACTION_CONFIG[sub.action.action] || ACTION_CONFIG.keep;
  const ActionIcon = cfg.icon;

  return (
    <div className={`rounded-xl border p-4 ${cfg.bg} transition-all`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-bold text-gray-900 dark:text-white text-sm">{sub.merchant}</h3>
            {sub.is_known_subscription && (
              <Badge variant="secondary" className="text-[10px] px-1.5 py-0">subscription</Badge>
            )}
            {sub.price_increase.detected && (
              <Badge className="bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300 text-[10px] px-1.5 py-0 flex items-center gap-1">
                <TrendingUp className="h-2.5 w-2.5" />
                +{sub.price_increase.pct_change?.toFixed(0)}% price rise
              </Badge>
            )}
            {sub.days_since_last > 60 && (
              <Badge className="bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300 text-[10px] px-1.5 py-0 flex items-center gap-1">
                <Clock className="h-2.5 w-2.5" />
                {sub.days_since_last}d inactive
              </Badge>
            )}
          </div>
          <div className="mt-1 flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400 flex-wrap">
            <span className="capitalize">{sub.interval || "recurring"}</span>
            <span>·</span>
            <span>₹{sub.avg_amount.toLocaleString()} avg</span>
            <span>·</span>
            <span>{sub.transaction_count} transactions</span>
            <span>·</span>
            <span>Since {sub.first_seen}</span>
          </div>
          <div className={`mt-2 flex items-center gap-1.5 text-xs font-medium ${cfg.color}`}>
            <ActionIcon className="h-3.5 w-3.5" />
            <span>{cfg.label}{sub.action.savings_estimate > 0 ? ` — save ₹${sub.action.savings_estimate.toLocaleString()}/mo` : ""}</span>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{sub.action.reason}</p>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          <div className={`text-2xl font-bold ${leakColor(sub.leak_score)}`}>{sub.leak_score}</div>
          <div className="text-[10px] text-gray-400">leak score</div>
          <button
            onClick={() => setOpen(o => !o)}
            className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 flex items-center gap-1"
          >
            {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            {open ? "Less" : "Details"}
          </button>
        </div>
      </div>

      {open && (
        <div className="mt-4 pt-4 border-t border-black/10 dark:border-white/10 space-y-3">
          {sub.price_increase.detected && (
            <div className="flex items-center gap-4 text-xs">
              <span className="text-gray-500">Price trend</span>
              <span className="text-gray-700 dark:text-gray-300">
                ₹{sub.price_increase.first_avg?.toFixed(0)} → ₹{sub.price_increase.last_avg?.toFixed(0)}
                <span className="text-red-500 ml-1">(+{sub.price_increase.pct_change?.toFixed(1)}%)</span>
              </span>
            </div>
          )}
          <div className="text-xs text-gray-500 dark:text-gray-400">
            <span className="font-medium">Recent transactions:</span>
            <div className="mt-1 space-y-0.5">
              {sub.sample_transactions.map((t, i) => (
                <div key={i} className="flex justify-between font-mono">
                  <span className="text-gray-400">{t.date}</span>
                  <span className="text-gray-700 dark:text-gray-300">₹{t.amount.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs text-center">
            <div className="bg-white/50 dark:bg-white/5 rounded p-2">
              <div className="font-bold text-gray-900 dark:text-white">₹{sub.total_paid.toLocaleString()}</div>
              <div className="text-gray-500">Total paid</div>
            </div>
            <div className="bg-white/50 dark:bg-white/5 rounded p-2">
              <div className="font-bold text-gray-900 dark:text-white">₹{sub.monthly_cost.toLocaleString()}</div>
              <div className="text-gray-500">/month</div>
            </div>
            <div className="bg-white/50 dark:bg-white/5 rounded p-2">
              <div className="font-bold text-gray-900 dark:text-white">{sub.days_since_last}d</div>
              <div className="text-gray-500">Since last</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Page ────────────────────────────────────────────────── */
export default function SubscriptionLeaks() {
  const location = useLocation();
  const navigate  = useNavigate();
  const result: AnalysisResult | undefined = location.state?.result;

  if (!result) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6 text-center">
          <AlertTriangle className="h-16 w-16 text-yellow-400" />
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">No Analysis Data</h2>
            <p className="text-gray-500 dark:text-gray-400 mt-2">
              Upload a bank statement or SMS export to see your subscription leaks.
            </p>
          </div>
          <Button
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
            onClick={() => navigate("/cryptoflow/upload")}
          >
            <Upload className="h-4 w-4 mr-2" /> Upload Transactions
          </Button>
        </div>
      </DashboardLayout>
    );
  }

  const { summary, subscriptions, overall_leak_score, transactions_parsed } = result;
  const cancelSubs      = subscriptions.filter(s => s.action.action === "cancel");
  const downgradeSubs   = subscriptions.filter(s => s.action.action === "downgrade");
  const renegotiateSubs = subscriptions.filter(s => s.action.action === "renegotiate");
  const keepSubs        = subscriptions.filter(s => s.action.action === "keep");

  return (
    <DashboardLayout>
      <div className="max-w-5xl mx-auto space-y-8">

        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">Subscription Leak Report</h2>
            <p className="text-gray-500 dark:text-gray-400 mt-1">
              Scanned {transactions_parsed.toLocaleString()} transactions &nbsp;·&nbsp;
              {subscriptions.length} recurring subscriptions detected
            </p>
          </div>
          <Button variant="outline" className="dark:border-white/20 dark:text-white" onClick={() => navigate("/cryptoflow/upload")}>
            <Upload className="h-4 w-4 mr-2" /> New Scan
          </Button>
        </div>

        {/* KPI row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Monthly Spend",   value: `₹${summary.total_monthly_spend.toLocaleString()}`,      icon: IndianRupee,    color: "text-purple-500" },
            { label: "Potential Savings", value: `₹${summary.potential_monthly_savings.toLocaleString()}`, icon: TrendingUp,   color: "text-green-500" },
            { label: "Cancel",          value: summary.cancel_count,                                      icon: XCircle,        color: "text-red-500" },
            { label: "Price Increases",  value: summary.price_increase_count,                              icon: AlertTriangle, color: "text-orange-500" },
          ].map(({ label, value, icon: Icon, color }) => (
            <Card key={label} className="dark:bg-white/5 dark:border-white/10">
              <CardContent className="p-4 flex items-center gap-3">
                <Icon className={`h-8 w-8 ${color} shrink-0`} />
                <div>
                  <div className="text-xl font-bold text-gray-900 dark:text-white">{value}</div>
                  <div className="text-xs text-gray-500">{label}</div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Leak score + action summary */}
        <div className="grid md:grid-cols-2 gap-6">
          <Card className="dark:bg-white/5 dark:border-white/10">
            <CardHeader><CardTitle>Overall Leak Score</CardTitle></CardHeader>
            <CardContent className="flex items-center justify-center gap-8 py-6">
              <LeakGauge score={overall_leak_score} />
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-green-500" /> <span className="text-gray-600 dark:text-gray-300">0–24 Healthy</span></div>
                <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-yellow-400" /> <span className="text-gray-600 dark:text-gray-300">25–44 Watch</span></div>
                <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-orange-500" /> <span className="text-gray-600 dark:text-gray-300">45–69 Action needed</span></div>
                <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-red-500"    /> <span className="text-gray-600 dark:text-gray-300">70–100 Critical leaks</span></div>
              </div>
            </CardContent>
          </Card>

          <Card className="dark:bg-white/5 dark:border-white/10">
            <CardHeader><CardTitle>Action Plan</CardTitle></CardHeader>
            <CardContent className="space-y-3 py-4">
              {[
                { label: "Cancel immediately",  count: summary.cancel_count,      color: "bg-red-500",    savings: cancelSubs.reduce((a, s) => a + s.action.savings_estimate, 0) },
                { label: "Downgrade plan",       count: summary.downgrade_count,   color: "bg-orange-500", savings: downgradeSubs.reduce((a, s) => a + s.action.savings_estimate, 0) },
                { label: "Renegotiate",          count: summary.renegotiate_count, color: "bg-yellow-400", savings: 0 },
                { label: "Keep as-is",           count: keepSubs.length,           color: "bg-green-500",  savings: 0 },
              ].map(({ label, count, color, savings }) => (
                <div key={label} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${color}`} />
                    <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
                    <Badge variant="secondary" className="text-xs">{count}</Badge>
                  </div>
                  {savings > 0 && (
                    <span className="text-xs font-medium text-green-600 dark:text-green-400">
                      save ₹{savings.toLocaleString()}/mo
                    </span>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Subscription cards by action group */}
        {[
          { title: "🚨 Cancel These Now", list: cancelSubs },
          { title: "⬇️  Downgrade These", list: downgradeSubs },
          { title: "💬 Renegotiate", list: renegotiateSubs },
          { title: "✅ Healthy Subscriptions", list: keepSubs },
        ].map(({ title, list }) => list.length > 0 && (
          <div key={title} className="space-y-3">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200">{title}</h3>
            <div className="space-y-3">
              {list.map((sub, i) => <SubCard key={i} sub={sub} />)}
            </div>
          </div>
        ))}
      </div>
    </DashboardLayout>
  );
}
