import React from "react";
import { Upload, Network, BarChart4 } from "lucide-react";


export const steps = [
    {
      number: "01",
      icon: <Upload className="h-6 w-6" />,
      title: "Ingest core-banking feeds",
      description: "Load ledger extracts or batch files with account pairs, amount, value date, product code, branch, and channel."
    },
    {
      number: "02",
      icon: <Network className="h-6 w-6" />,
      title: "Graph + ML detection",
      description: "Rules and models flag layering, cycles, structuring bands, dormancy breaks, and profile mismatch in the unified fund-flow graph."
    },
    {
      number: "03",
      icon: <BarChart4 className="h-6 w-6" />,
      title: "Trace & FIU package",
      description: "Investigators explore paths and export an evidence package (timeline + subgraph + scores) for the FIU."
    }
  ];
  