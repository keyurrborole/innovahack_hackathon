import { DashboardLayout } from "../components/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { TrendingUp, Target, Clock, Award, Cpu, Database } from "lucide-react";
import { Progress } from "../components/ui/progress";

export default function Benchmarks() {
  const performanceMetrics = [
    { label: "Accuracy", value: 98.5, color: "text-green-600", description: "Offline validation on synthetic + sampled internal labels (demo)" },
    { label: "Precision", value: 96.2, color: "text-blue-600", description: "Alert precision on confirmed investigation cases (demo)" },
    { label: "Recall", value: 94.8, color: "text-purple-600", description: "Recall on seeded typology cases (demo)" },
    { label: "F1-Score", value: 95.5, color: "text-orange-600", description: "Harmonic mean of precision & recall (demo)" },
  ];

  const comparisonData = [
    { method: "FundFlow GNN + rules", accuracy: 98.5, speed: "2.4s", memory: "1.2GB" },
    { method: "Traditional ML", accuracy: 85.3, speed: "8.1s", memory: "2.5GB" },
    { method: "Rule-Based", accuracy: 72.1, speed: "15.3s", memory: "0.8GB" },
    { method: "Random Forest", accuracy: 88.7, speed: "6.2s", memory: "1.8GB" },
  ];

  const patternDetectionRates = [
    { pattern: "Rapid layering", truePositives: 247, falsePositives: 8, falseNegatives: 12, accuracy: 95.4 },
    { pattern: "Circular flow", truePositives: 156, falsePositives: 6, falseNegatives: 9, accuracy: 94.2 },
    { pattern: "Structuring", truePositives: 89, falsePositives: 11, falseNegatives: 7, accuracy: 89.5 },
    { pattern: "Profile mismatch", truePositives: 124, falsePositives: 5, falseNegatives: 8, accuracy: 93.8 },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">Model Performance Benchmarks</h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Illustrative metrics for graph + ML detection on internal fund-flow data (prototype)
          </p>
        </div>

        {/* Key Performance Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {performanceMetrics.map((metric) => (
            <Card key={metric.label} className="hover:shadow-lg transition-shadow dark:bg-white/5">
              <CardHeader className="pb-3">
                <CardDescription className="text-gray-600 dark:text-gray-400">{metric.label}</CardDescription>
                <CardTitle className={`text-4xl font-bold ${metric.color}`}>
                  {metric.value}%
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Progress value={metric.value} className="h-2 mb-2" />
                <p className="text-xs text-gray-500 dark:text-gray-400">{metric.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* ROC Curve Visualization */}
        <Card className="dark:bg-white/5">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-crypto-purple" />
              <CardTitle className="text-gray-900 dark:text-white">ROC Curve Analysis</CardTitle>
            </div>
            <CardDescription className="text-gray-600 dark:text-gray-400">
              Offline evaluation, not live inference
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="relative w-full h-80 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 rounded-lg p-6">
              {/* ROC Curve SVG */}
              <svg viewBox="0 0 400 400" className="w-full h-full">
                {/* Grid lines */}
                {[0, 1, 2, 3, 4].map((i) => (
                  <g key={i}>
                    <line
                      x1={i * 100}
                      y1="0"
                      x2={i * 100}
                      y2="400"
                      stroke="#e5e7eb"
                      strokeWidth="1"
                      strokeDasharray="5,5"
                    />
                    <line
                      x1="0"
                      y1={i * 100}
                      x2="400"
                      y2={i * 100}
                      stroke="#e5e7eb"
                      strokeWidth="1"
                      strokeDasharray="5,5"
                    />
                  </g>
                ))}
                
                {/* Diagonal baseline */}
                <line x1="0" y1="400" x2="400" y2="0" stroke="#9ca3af" strokeWidth="2" strokeDasharray="10,5" />
                
                {/* ROC Curve */}
                <path
                  d="M 0 400 Q 50 350, 100 280 T 200 120 T 350 20 T 400 0"
                  fill="none"
                  stroke="#8b5cf6"
                  strokeWidth="3"
                />
                
                {/* Area under curve */}
                <path
                  d="M 0 400 Q 50 350, 100 280 T 200 120 T 350 20 T 400 0 L 400 400 Z"
                  fill="#8b5cf6"
                  fillOpacity="0.1"
                />
                
                {/* Axes */}
                <line x1="0" y1="400" x2="400" y2="400" stroke="#374151" strokeWidth="2" />
                <line x1="0" y1="0" x2="0" y2="400" stroke="#374151" strokeWidth="2" />
                
                {/* Labels */}
                <text x="200" y="430" textAnchor="middle" className="fill-gray-600 dark:fill-gray-400" fontSize="14">
                  False Positive Rate
                </text>
                <text x="-200" y="15" textAnchor="middle" className="fill-gray-600 dark:fill-gray-400" fontSize="14" transform="rotate(-90)">
                  True Positive Rate
                </text>
                
                {/* AUC Score */}
                <text x="320" y="350" className="fill-purple-600 dark:fill-purple-400" fontSize="16" fontWeight="bold">
                  AUC = 0.985
                </text>
              </svg>
            </div>
          </CardContent>
        </Card>

        {/* Comparison with Other Methods */}
        <Card className="dark:bg-white/5">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Award className="h-5 w-5 text-yellow-600" />
              <CardTitle className="text-gray-900 dark:text-white">Comparison with Baseline Methods</CardTitle>
            </div>
            <CardDescription className="text-gray-600 dark:text-gray-400">
              FundFlow graph model vs traditional baselines (offline benchmark)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b-2 dark:border-gray-700">
                  <tr>
                    <th className="text-left py-3 px-4 text-gray-700 dark:text-gray-300">Method</th>
                    <th className="text-center py-3 px-4 text-gray-700 dark:text-gray-300">Accuracy</th>
                    <th className="text-center py-3 px-4 text-gray-700 dark:text-gray-300">Speed</th>
                    <th className="text-center py-3 px-4 text-gray-700 dark:text-gray-300">Memory</th>
                    <th className="text-center py-3 px-4 text-gray-700 dark:text-gray-300">Rank</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonData.map((row, idx) => (
                    <tr key={row.method} className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <td className="py-4 px-4">
                        <div className="flex items-center space-x-2">
                          {idx === 0 && <Cpu className="h-4 w-4 text-crypto-purple" />}
                          <span className={`font-medium ${idx === 0 ? 'text-crypto-purple dark:text-purple-400' : 'text-gray-900 dark:text-gray-300'}`}>
                            {row.method}
                          </span>
                          {idx === 0 && <Badge className="bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-200">Our Model</Badge>}
                        </div>
                      </td>
                      <td className="py-4 px-4 text-center">
                        <div className="flex flex-col items-center">
                          <span className="font-bold text-gray-900 dark:text-white">{row.accuracy}%</span>
                          <Progress value={row.accuracy} className="w-20 h-1.5 mt-1" />
                        </div>
                      </td>
                      <td className="py-4 px-4 text-center">
                        <Badge variant="outline" className="dark:border-gray-600 dark:text-gray-300">
                          <Clock className="h-3 w-3 mr-1" />
                          {row.speed}
                        </Badge>
                      </td>
                      <td className="py-4 px-4 text-center">
                        <Badge variant="outline" className="dark:border-gray-600 dark:text-gray-300">
                          <Database className="h-3 w-3 mr-1" />
                          {row.memory}
                        </Badge>
                      </td>
                      <td className="py-4 px-4 text-center">
                        <Badge className={idx === 0 ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-200" : "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300"}>
                          #{idx + 1}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Pattern-Specific Performance */}
        <Card className="dark:bg-white/5">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Target className="h-5 w-5 text-red-600" />
              <CardTitle className="text-gray-900 dark:text-white">Pattern-Specific Detection Rates</CardTitle>
            </div>
            <CardDescription className="text-gray-600 dark:text-gray-400">
              Performance breakdown by laundering pattern type
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {patternDetectionRates.map((pattern) => (
                <div key={pattern.pattern} className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold text-gray-900 dark:text-white">{pattern.pattern}</h4>
                    <Badge className="bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-200">
                      {pattern.accuracy}% Accurate
                    </Badge>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 mb-3">
                    <div className="text-center p-3 bg-white dark:bg-gray-900/50 rounded">
                      <p className="text-2xl font-bold text-green-600 dark:text-green-400">{pattern.truePositives}</p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">True Positives</p>
                    </div>
                    <div className="text-center p-3 bg-white dark:bg-gray-900/50 rounded">
                      <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">{pattern.falsePositives}</p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">False Positives</p>
                    </div>
                    <div className="text-center p-3 bg-white dark:bg-gray-900/50 rounded">
                      <p className="text-2xl font-bold text-red-600 dark:text-red-400">{pattern.falseNegatives}</p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">False Negatives</p>
                    </div>
                  </div>

                  <Progress value={pattern.accuracy} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Model Architecture Info */}
        <Card className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border-purple-200 dark:border-purple-800">
          <CardHeader>
            <CardTitle className="text-gray-900 dark:text-white">Model Architecture</CardTitle>
            <CardDescription className="text-gray-700 dark:text-gray-300">
              Graph Neural Network specifications
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-gray-800/50 p-4 rounded-lg border border-purple-200 dark:border-purple-800">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Architecture</h4>
              <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-1">
                <li>• Graph Convolutional Network (GCN)</li>
                <li>• 3 hidden layers (128, 64, 32)</li>
                <li>• ReLU activation</li>
                <li>• Dropout: 0.3</li>
              </ul>
            </div>
            <div className="bg-white dark:bg-gray-800/50 p-4 rounded-lg border border-purple-200 dark:border-purple-800">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Training</h4>
              <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-1">
                <li>• Dataset: 2.5M transactions</li>
                <li>• Epochs: 100</li>
                <li>• Optimizer: Adam (lr=0.001)</li>
                <li>• Loss: Binary Cross-Entropy</li>
              </ul>
            </div>
            <div className="bg-white dark:bg-gray-800/50 p-4 rounded-lg border border-purple-200 dark:border-purple-800">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Features</h4>
              <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-1">
                <li>• Node degree centrality</li>
                <li>• Transaction amount</li>
                <li>• Temporal features</li>
                <li>• Wallet age</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
