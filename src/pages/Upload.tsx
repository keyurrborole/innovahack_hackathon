import { useState, useRef } from "react";
import { DashboardLayout } from "../components/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Progress } from "../components/ui/progress";
import { Alert, AlertDescription } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { useNavigate } from "react-router-dom";
import {
  Upload as UploadIcon, FileText, AlertCircle, CheckCircle2, X,
  Loader2, Smartphone, CreditCard, FileSpreadsheet, Zap
} from "lucide-react";

/* ─── Types ─────────────────────────────────────────────────── */
interface AnalysisResult {
  overall_leak_score: number;
  subscriptions: any[];
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

const ACCEPTED = ".csv,.txt,.tsv";

const SOURCE_TYPES = [
  {
    icon: CreditCard,
    label: "Bank Statement",
    desc: "Export from net banking as CSV",
    example: "Date, Description, Debit, Credit, Balance",
    color: "from-blue-500 to-blue-700",
  },
  {
    icon: Smartphone,
    label: "SMS Export",
    desc: "Android SMS backup TXT file",
    example: "Debited Rs.499 for Netflix via UPI",
    color: "from-purple-500 to-purple-700",
  },
  {
    icon: FileSpreadsheet,
    label: "Generic CSV",
    desc: "Any CSV with date, merchant, amount",
    example: "2024-01-15, Spotify Premium, 119.00",
    color: "from-emerald-500 to-emerald-700",
  },
];

/* ─── Component ─────────────────────────────────────────────── */
export default function Upload() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading]       = useState(false);
  const [progress, setProgress]         = useState(0);
  const [stage, setStage]               = useState("");
  const [error, setError]               = useState<string | null>(null);
  const [result, setResult]             = useState<AnalysisResult | null>(null);
  const [previewRows, setPreviewRows]   = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate     = useNavigate();

  /* ── file select ─────────────────────────────────────────── */
  const onFileChange = (file: File) => {
    setSelectedFile(file);
    setError(null);
    setResult(null);
    setProgress(0);
    // Quick preview — first 5 lines
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = (e.target?.result as string) || "";
      setPreviewRows(text.split("\n").slice(0, 5).filter(Boolean));
    };
    reader.readAsText(file);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) onFileChange(f);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) onFileChange(f);
  };

  /* ── upload & analyse ────────────────────────────────────── */
  const handleAnalyse = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setError(null);
    setProgress(0);

    const stages = ["Parsing transactions…", "Clustering merchants…", "Detecting recurrence…", "Scoring leaks…"];
    let stageIdx = 0;
    setStage(stages[0]);

    const iv = setInterval(() => {
      setProgress(p => {
        const next = Math.min(p + 8, 88);
        if (next > 30 && stageIdx < 1) { stageIdx = 1; setStage(stages[1]); }
        if (next > 55 && stageIdx < 2) { stageIdx = 2; setStage(stages[2]); }
        if (next > 75 && stageIdx < 3) { stageIdx = 3; setStage(stages[3]); }
        return next;
      });
    }, 250);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      const resp = await fetch("/gnn-api/analyse", { method: "POST", body: formData });

      clearInterval(iv);
      setProgress(100);
      setStage("Complete!");

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(err.detail || `Server error ${resp.status}`);
      }

      const data: AnalysisResult = await resp.json();
      setResult(data);
    } catch (err: any) {
      clearInterval(iv);
      setProgress(0);
      setStage("");
      setError(err.message || "Analysis failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const reset = () => {
    setSelectedFile(null);
    setResult(null);
    setError(null);
    setProgress(0);
    setStage("");
    setPreviewRows([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  /* ── render ──────────────────────────────────────────────── */
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-8">

        {/* Header */}
        <div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            Upload Transaction History
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Scan bank statements, SMS exports, or any transaction CSV to detect subscription leaks
          </p>
        </div>

        {/* Source type cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {SOURCE_TYPES.map(({ icon: Icon, label, desc, example, color }) => (
            <div
              key={label}
              className="relative overflow-hidden rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 p-4 cursor-pointer hover:border-purple-400 transition-all group"
              onClick={() => fileInputRef.current?.click()}
            >
              <div className={`inline-flex p-2 rounded-lg bg-gradient-to-br ${color} mb-3`}>
                <Icon className="h-5 w-5 text-white" />
              </div>
              <p className="font-semibold text-gray-900 dark:text-white text-sm">{label}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{desc}</p>
              <p className="mt-2 font-mono text-[10px] text-gray-400 dark:text-gray-600 truncate">{example}</p>
            </div>
          ))}
        </div>

        {/* Upload zone */}
        <Card className="dark:bg-white/5 dark:border-white/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-purple-500" /> Subscription Leak Scanner
            </CardTitle>
            <CardDescription>Supports CSV, TXT (SMS backup), TSV — up to 50 MB</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">

            {!selectedFile ? (
              <div
                className="border-2 border-dashed border-gray-300 dark:border-white/20 rounded-xl p-12 text-center hover:border-purple-500 dark:hover:border-purple-500 transition-colors cursor-pointer"
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                onClick={() => fileInputRef.current?.click()}
              >
                <UploadIcon className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500 mb-4" />
                <p className="text-lg font-medium text-gray-900 dark:text-white">
                  Drop your file here or click to browse
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Bank statement CSV · SMS export TXT · Generic transaction CSV
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  accept={ACCEPTED}
                  onChange={handleFileInput}
                />
              </div>
            ) : (
              <div className="space-y-4">
                {/* File info bar */}
                <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-white/5 border dark:border-white/10">
                  <div className="flex items-center gap-3">
                    <FileText className="h-8 w-8 text-purple-500" />
                    <div>
                      <p className="font-medium text-sm text-gray-900 dark:text-white">{selectedFile.name}</p>
                      <p className="text-xs text-gray-500">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                    </div>
                  </div>
                  {!uploading && !result && (
                    <Button variant="ghost" size="sm" onClick={reset}>
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>

                {/* Preview */}
                {previewRows.length > 0 && !uploading && !result && (
                  <div className="rounded-lg border dark:border-white/10 overflow-hidden">
                    <div className="bg-gray-50 dark:bg-white/5 px-3 py-2 text-xs font-semibold text-gray-600 dark:text-gray-400">
                      Preview (first 5 lines)
                    </div>
                    <div className="p-3 space-y-1">
                      {previewRows.map((r, i) => (
                        <p key={i} className="font-mono text-xs text-gray-600 dark:text-gray-300 truncate">
                          {r}
                        </p>
                      ))}
                    </div>
                  </div>
                )}

                {/* Progress */}
                {uploading && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400 flex items-center gap-2">
                        <Loader2 className="h-3 w-3 animate-spin" /> {stage}
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">{progress}%</span>
                    </div>
                    <Progress value={progress} className="h-2" />
                  </div>
                )}

                {/* Error */}
                {error && (
                  <Alert className="border-red-300 bg-red-50 dark:bg-red-900/20 dark:border-red-700">
                    <AlertCircle className="h-4 w-4 text-red-600" />
                    <AlertDescription className="text-red-800 dark:text-red-200">{error}</AlertDescription>
                  </Alert>
                )}

                {/* Success summary */}
                {result && (
                  <Alert className="border-green-300 bg-green-50 dark:bg-green-900/20 dark:border-green-700">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    <AlertDescription className="text-green-800 dark:text-green-200">
                      Scanned <strong>{result.transactions_parsed}</strong> transactions →{" "}
                      found <strong>{result.summary.total_subscriptions}</strong> recurring subscriptions.{" "}
                      Potential savings:{" "}
                      <strong>₹{result.summary.potential_monthly_savings.toLocaleString()}/mo</strong>
                    </AlertDescription>
                  </Alert>
                )}

                {/* Action buttons */}
                <div className="flex gap-3">
                  {!uploading && !result && (
                    <Button
                      className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
                      onClick={handleAnalyse}
                    >
                      <Zap className="h-4 w-4 mr-2" /> Analyse Transactions
                    </Button>
                  )}
                  {result && (
                    <>
                      <Button
                        className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
                        onClick={() =>
                          navigate("/cryptoflow/subscriptions", { state: { result } })
                        }
                      >
                        View Leak Score Report →
                      </Button>
                      <Button variant="outline" className="dark:border-white/20 dark:text-white" onClick={reset}>
                        New File
                      </Button>
                    </>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Format guide */}
        <Card className="dark:bg-white/5 dark:border-white/10">
          <CardHeader>
            <CardTitle className="text-base">Accepted File Formats</CardTitle>
          </CardHeader>
          <CardContent className="grid md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <Badge variant="secondary">Bank Statement CSV</Badge>
              <pre className="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-white/5 p-2 rounded overflow-x-auto">
{`Date,Description,Debit,Credit,Balance
01/01/2025,NETFLIX INDIA,199,,8500
01/01/2025,SPOTIFY PREMIUM,119,,8381
15/01/2025,AMAZON PRIME,179,,8202`}
              </pre>
            </div>
            <div className="space-y-2">
              <Badge variant="secondary">SMS Export TXT</Badge>
              <pre className="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-white/5 p-2 rounded overflow-x-auto">
{`Debited Rs.199 for Netflix via UPI 01/01/25
Debited Rs.119 for Spotify via UPI 01/01/25
Rs.179 debited for Amazon Prime 15/01/25`}
              </pre>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
