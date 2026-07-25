import { useState, useRef } from "react";
import { DashboardLayout } from "../components/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Upload as UploadIcon, FileText, AlertCircle, CheckCircle2, X, Table, AlertTriangle, Loader2 } from "lucide-react";
import { Progress } from "../components/ui/progress";
import { Alert, AlertDescription } from "../components/ui/alert";
import { useNavigate } from "react-router-dom";
import { Badge } from "../components/ui/badge";
import { uploadApi, type Upload as UploadType } from "../lib/api";

export default function Upload() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadComplete, setUploadComplete] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadType | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [columnMapping, setColumnMapping] = useState<any>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const expectedColumns = [
    { name: "Source_Wallet_ID", required: true },
    { name: "Dest_Wallet_ID", required: true },
    { name: "Timestamp", required: true },
    { name: "Amount", required: true },
    { name: "Token_Type", required: false }
  ];

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadComplete(false);
      parseFilePreview(file);
    }
  };

  const parseFilePreview = async (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const lines = text.split('\n').filter(line => line.trim());
      
      if (lines.length > 0) {
        const headers = lines[0].split(',').map(h => h.trim());
        const preview = lines.slice(1, 11).map(line => {
          const values = line.split(',');
          const row: any = {};
          headers.forEach((header, idx) => {
            row[header] = values[idx]?.trim() || '';
          });
          return row;
        });
        
        setPreviewData(preview);
        validateColumns(headers);
      }
    };
    reader.readAsText(file);
  };

  const validateColumns = (headers: string[]) => {
    const errors: string[] = [];
    const mapping: any = {};
    
    // Normalize string for comparison: lowercase, remove underscores, spaces, and hyphens
    const normalize = (str: string) => str.toLowerCase().replace(/[_\s-]/g, '');
    
    expectedColumns.forEach(expected => {
      const normalizedExpected = normalize(expected.name);
      const match = headers.find(h => {
        const normalizedHeader = normalize(h);
        // Check for exact match or if one contains the other
        return normalizedHeader === normalizedExpected || 
               normalizedHeader.includes(normalizedExpected) ||
               normalizedExpected.includes(normalizedHeader);
      });
      
      if (match) {
        mapping[expected.name] = match;
      } else if (expected.required) {
        errors.push(`Missing required column: ${expected.name}`);
      }
    });
    
    setColumnMapping(mapping);
    setValidationErrors(errors);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadComplete(false);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setProgress(0);
    setUploadError(null);

    // Simulate progress while uploading
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) return prev; // Stop at 90% until actual response
        return prev + 10;
      });
    }, 300);

    try {
      const result = await uploadApi.uploadFile(selectedFile);
      clearInterval(progressInterval);
      setProgress(100);
      setUploadResult(result);
      setUploadComplete(true);
    } catch (error: any) {
      clearInterval(progressInterval);
      setProgress(0);
      setUploadError(error.message || 'Upload failed. Please try again.');
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setProgress(0);
    setUploadComplete(false);
    setUploadResult(null);
    setUploadError(null);
    setPreviewData([]);
    setColumnMapping(null);
    setValidationErrors([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">Ingest ledger data</h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Load internal transfer feeds to build the fund-flow graph (accounts, amounts, product, branch, channel)
          </p>
        </div>

        {/* Upload card */}
        <Card>
          <CardHeader>
            <CardTitle>File Upload</CardTitle>
            <CardDescription>
              Supported formats: CSV, JSON, Excel (max 100MB)
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!selectedFile ? (
              <div
                className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-crypto-purple transition-colors cursor-pointer"
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => fileInputRef.current?.click()}
              >
                <UploadIcon className="mx-auto h-12 w-12 text-gray-400" />
                <p className="mt-4 text-lg font-medium text-gray-900">
                  Drop your file here or click to browse
                </p>
                <p className="mt-2 text-sm text-gray-500">
                  CSV, JSON, or Excel files up to 100MB
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  accept=".csv,.json,.xlsx,.xls"
                  onChange={handleFileSelect}
                />
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg bg-gray-50">
                  <div className="flex items-center space-x-3">
                    <FileText className="h-8 w-8 text-crypto-purple" />
                    <div>
                      <p className="font-medium text-gray-900">{selectedFile.name}</p>
                      <p className="text-sm text-gray-500">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  {!uploading && !uploadComplete && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleRemoveFile}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>

                {/* Column Mapping & Validation */}
                {previewData.length > 0 && !uploading && !uploadComplete && (
                  <Card className="mt-4 border-2 dark:bg-white/5">
                    <CardHeader>
                      <div className="flex items-center space-x-2">
                        <Table className="h-5 w-5 text-crypto-purple" />
                        <CardTitle className="text-lg text-gray-900 dark:text-white">Data Preview & Validation</CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Validation Errors */}
                      {validationErrors.length > 0 && (
                        <Alert className="border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800">
                          <AlertTriangle className="h-4 w-4 text-red-600" />
                          <AlertDescription className="text-red-800 dark:text-red-200">
                            <div className="font-semibold mb-1">Validation Issues:</div>
                            <ul className="list-disc list-inside space-y-1">
                              {validationErrors.map((error, idx) => (
                                <li key={idx} className="text-sm">{error}</li>
                              ))}
                            </ul>
                          </AlertDescription>
                        </Alert>
                      )}

                      {/* Column Mapping */}
                      {columnMapping && Object.keys(columnMapping).length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Column Mapping:</h4>
                          <div className="grid grid-cols-2 gap-2">
                            {Object.entries(columnMapping).map(([expected, actual]: [string, any]) => (
                              <div key={expected} className="flex items-center justify-between bg-green-50 dark:bg-green-900/20 p-2 rounded border border-green-200 dark:border-green-800">
                                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">{expected}</span>
                                <Badge className="bg-green-600 text-white text-xs">
                                  {actual}
                                </Badge>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Data Preview Table */}
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                          First 10 Rows:
                        </h4>
                        <div className="overflow-x-auto border dark:border-gray-700 rounded-lg">
                          <table className="w-full text-sm">
                            <thead className="bg-gray-50 dark:bg-gray-800">
                              <tr>
                                {previewData.length > 0 && Object.keys(previewData[0]).map((header, idx) => (
                                  <th key={idx} className="px-3 py-2 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                                    {header}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {previewData.map((row, rowIdx) => (
                                <tr key={rowIdx} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                                  {Object.values(row).map((value: any, cellIdx) => (
                                    <td key={cellIdx} className="px-3 py-2 border-b dark:border-gray-700 text-gray-700 dark:text-gray-300">
                                      {value}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                          Showing {previewData.length} of total rows
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {uploading && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">
                        <Loader2 className="h-4 w-4 inline mr-2 animate-spin" />
                        Uploading...
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">{progress}%</span>
                    </div>
                    <Progress value={progress} className="h-2" />
                  </div>
                )}

                {uploadError && (
                  <Alert className="border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800">
                    <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
                    <AlertDescription className="text-red-800 dark:text-red-200">
                      {uploadError}
                    </AlertDescription>
                  </Alert>
                )}

                {uploadComplete && (
                  <Alert className="border-green-200 bg-green-50 dark:bg-green-900/20 dark:border-green-800">
                    <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
                    <AlertDescription className="text-green-800 dark:text-green-200">
                      File uploaded successfully! {uploadResult?.records ? `${uploadResult.records} records processed.` : ''} Analysis is in progress.
                    </AlertDescription>
                  </Alert>
                )}

                {!uploading && !uploadComplete && previewData.length > 0 && validationErrors.length === 0 && (
                  <Button
                    className="w-full bg-crypto-purple hover:bg-crypto-dark-purple"
                    onClick={handleUpload}
                  >
                    Start Upload & Analysis
                  </Button>
                )}

                {!uploading && !uploadComplete && validationErrors.length > 0 && (
                  <Button
                    className="w-full"
                    disabled
                  >
                    Fix Validation Errors First
                  </Button>
                )}

                {uploadComplete && (
                  <Button
                    className="w-full bg-crypto-purple hover:bg-crypto-dark-purple"
                    onClick={() => navigate(`/cryptoflow/analysis${uploadResult?.id ? `?uploadId=${uploadResult.id}` : ''}`)}
                  >
                    View Analysis Results
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Data format info */}
        <Card>
          <CardHeader>
            <CardTitle>Required Data Format</CardTitle>
            <CardDescription>Ensure your data includes these fields</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Required columns:</strong> transaction_id, from_address, to_address, amount, timestamp
                </AlertDescription>
              </Alert>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm font-medium text-gray-900 mb-2">Example CSV format:</p>
                <pre className="text-xs text-gray-600 overflow-x-auto">
{`transaction_id,from_address,to_address,amount,timestamp
tx001,0x1a2b3c...,0x4d5e6f...,150.50,2026-01-31T10:30:00Z
tx002,0x7g8h9i...,0x1a2b3c...,200.00,2026-01-31T11:15:00Z`}
                </pre>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm font-medium text-gray-900 mb-2">Example JSON format:</p>
                <pre className="text-xs text-gray-600 overflow-x-auto">
{`{
  "transactions": [
    {
      "transaction_id": "tx001",
      "from_address": "0x1a2b3c...",
      "to_address": "0x4d5e6f...",
      "amount": 150.50,
      "timestamp": "2026-01-31T10:30:00Z"
    }
  ]
}`}
                </pre>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
