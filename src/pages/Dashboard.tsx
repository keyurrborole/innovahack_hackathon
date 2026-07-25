import { useState, useEffect } from "react";
import { DashboardLayout } from "../components/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Activity, AlertTriangle, TrendingUp, Users, Loader2 } from "lucide-react";
import { Button } from "../components/ui/button";
import { Link } from "react-router-dom";
import { useTheme } from "../contexts/ThemeContext";
import ThreeBackground from "../components/ThreeBackground";
import { dashboardApi, uploadApi, type Upload } from "../lib/api";

interface DashboardStats {
  totalTransactions: number;
  suspiciousPatterns: number;
  riskScore: number;
  addressesMonitored: number;
}

export default function Dashboard() {
  const { theme } = useTheme();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentUploads, setRecentUploads] = useState<Upload[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // Fetch dashboard stats and recent uploads in parallel
        const [statsResponse, uploadsResponse] = await Promise.all([
          dashboardApi.getStats().catch(() => null),
          uploadApi.getHistory(1, 5).catch(() => ({ uploads: [], pagination: {} })),
        ]);

        if (statsResponse) {
          // Handle nested response from backend (stats.totalTransactions vs total_transactions)
          const statsData = (statsResponse as any).stats || statsResponse;
          setStats({
            totalTransactions: statsData.totalTransactions || statsData.total_transactions || 0,
            suspiciousPatterns: statsData.suspiciousCount || statsData.suspicious_count || 0,
            riskScore: Math.round((1 - (statsData.riskScore || 0)) * 100), // Convert risk to improvement %
            addressesMonitored: statsData.addressesMonitored || statsData.activeCases || statsData.total_uploads || 0,
          });
        }

        setRecentUploads(uploadsResponse.uploads || []);
      } catch (err) {
        console.error('Dashboard fetch error:', err);
        setError('Failed to load dashboard data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Format number with commas
  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  // Map upload status to risk level (placeholder logic)
  const getRiskLevel = (upload: Upload): string => {
    if (upload.status === 'completed') return 'Medium';
    if (upload.status === 'failed') return 'High';
    return 'Low';
  };

  const statsDisplay = [
    {
      title: "Internal transfers ingested",
      value: stats ? formatNumber(stats.totalTransactions) : "—",
      change: "+12.5%",
      icon: Activity,
      color: "text-blue-600",
      bgColor: "bg-blue-100",
    },
    {
      title: "Pattern alerts (open)",
      value: stats ? formatNumber(stats.suspiciousPatterns) : "—",
      change: "+4.2%",
      icon: AlertTriangle,
      color: "text-red-600",
      bgColor: "bg-red-100",
    },
    {
      title: "Model risk coverage",
      value: stats ? `${stats.riskScore}%` : "—",
      change: "+8.1%",
      icon: TrendingUp,
      color: "text-green-600",
      bgColor: "bg-green-100",
    },
    {
      title: "Accounts / branches on watch",
      value: stats ? formatNumber(stats.addressesMonitored) : "—",
      change: "+18.3%",
      icon: Users,
      color: "text-purple-600",
      bgColor: "bg-purple-100",
    },
  ];

  return (
    <DashboardLayout>
      <ThreeBackground variant="cubes" />
      <div className="space-y-8">
        {/* Welcome section */}
        <div className="rounded-xl p-6 border bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200 dark:from-crypto-purple/20 dark:to-pink-600/20 dark:border-crypto-purple/30">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">Welcome back!</h2>
          <p className="mt-1 text-gray-700 dark:text-gray-300">
            PS3 fund-flow monitoring: internal movement, typology alerts, and investigator queue at a glance.
          </p>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {statsDisplay.map((stat) => (
            <Card key={stat.title} className="backdrop-blur-sm hover:shadow-xl transition-all duration-300 bg-white border-gray-200 hover:bg-gray-50 dark:bg-white/5 dark:border-crypto-purple/20 dark:hover:bg-white/10 dark:hover:shadow-crypto-purple/20">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {stat.title}
                </CardTitle>
                <div className={`p-2 rounded-lg ${stat.bgColor} bg-opacity-20`}>
                  <stat.icon className={`h-4 w-4 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {isLoading ? <Loader2 className="h-6 w-6 animate-spin" /> : stat.value}
                </div>
                <p className="text-xs text-green-400 mt-1">
                  {stat.change} from last month
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Recent uploads */}
        <Card className="backdrop-blur-sm bg-white border-gray-200 dark:bg-white/5 dark:border-crypto-purple/20">
          <CardHeader>
            <CardTitle className="text-gray-900 dark:text-white">Recent data loads</CardTitle>
            <CardDescription className="text-gray-600 dark:text-gray-400">
              Latest core-banking / ledger extracts submitted for graph build
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex justify-center items-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-crypto-purple" />
              </div>
            ) : recentUploads.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No uploads yet. Ingest a sample ledger extract to build the fund-flow graph.
              </div>
            ) : (
              <div className="space-y-4">
                {recentUploads.map((upload) => (
                  <div key={upload.id} className="flex items-center justify-between p-4 border rounded-lg transition-colors border-gray-200 bg-gray-50 hover:bg-gray-100 dark:border-crypto-purple/20 dark:bg-white/5 dark:hover:bg-white/10">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 dark:text-white">{upload.name || upload.filename}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {new Date(upload.date || upload.uploadedAt || '').toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center space-x-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        upload.status === 'completed' 
                          ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                          : upload.status === 'processing'
                          ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                          : upload.status === 'failed'
                          ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                          : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      }`}>
                        {upload.status.charAt(0).toUpperCase() + upload.status.slice(1)}
                      </span>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        getRiskLevel(upload) === 'High' 
                          ? 'bg-red-500/20 text-red-400 border border-red-500/30' 
                          : getRiskLevel(upload) === 'Medium'
                          ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                          : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      }`}>
                        {getRiskLevel(upload)} Risk
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <Link to="/cryptoflow/upload">
              <Button className="w-full mt-4 bg-gradient-to-r from-crypto-purple to-pink-600 hover:from-crypto-dark-purple hover:to-pink-700 text-white shadow-lg shadow-crypto-purple/50">
                Ingest new data
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Quick actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="backdrop-blur-sm hover:shadow-xl transition-all duration-300 cursor-pointer bg-white border-gray-200 hover:bg-gray-50 dark:bg-white/5 dark:border-crypto-purple/20 dark:hover:bg-white/10 dark:hover:shadow-crypto-purple/20">
            <Link to="/cryptoflow/analysis">
              <CardHeader>
                <CardTitle className="text-lg text-gray-900 dark:text-white">Analysis & scores</CardTitle>
                <CardDescription className="text-gray-600 dark:text-gray-400">
                  Typology hits and ML risk breakdown per batch
                </CardDescription>
              </CardHeader>
            </Link>
          </Card>
          <Card className="backdrop-blur-sm hover:shadow-xl transition-all duration-300 cursor-pointer bg-white border-gray-200 hover:bg-gray-50 dark:bg-white/5 dark:border-crypto-purple/20 dark:hover:bg-white/10 dark:hover:shadow-crypto-purple/20">
            <Link to="/cryptoflow/graph">
              <CardHeader>
                <CardTitle className="text-lg text-gray-900 dark:text-white">Fund flow graph</CardTitle>
                <CardDescription className="text-gray-600 dark:text-gray-400">
                  Explore accounts, products, branches, and channels as a network
                </CardDescription>
              </CardHeader>
            </Link>
          </Card>
          <Card className="backdrop-blur-sm hover:shadow-xl transition-all duration-300 cursor-pointer bg-white border-gray-200 hover:bg-gray-50 dark:bg-white/5 dark:border-crypto-purple/20 dark:hover:bg-white/10 dark:hover:shadow-crypto-purple/20">
            <Link to="/cryptoflow/reports">
              <CardHeader>
                <CardTitle className="text-lg text-gray-900 dark:text-white">FIU evidence package</CardTitle>
                <CardDescription className="text-gray-600 dark:text-gray-400">
                  Export timeline, subgraph, and narrative for regulators
                </CardDescription>
              </CardHeader>
            </Link>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
