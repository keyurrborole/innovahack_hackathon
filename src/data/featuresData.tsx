import React from 'react';
import { Network, Shield, Brain, TrendingUp, AlertTriangle, Search } from 'lucide-react';

export const features = [
  {
    icon: <Network className="h-6 w-6" />,
    title: "Fund-flow graph",
    description: "Build a single graph of internal transfers with product, branch, channel, and timestamp on every edge—ready for graph algorithms and GNN layers."
  },
  {
    icon: <Shield className="h-6 w-6" />,
    title: "FIU-ready reporting",
    description: "Generate structured evidence packages: subgraphs, timelines, and risk rationale suitable for Financial Intelligence Unit workflows."
  },
  {
    icon: <Brain className="h-6 w-6" />,
    title: "Pattern library",
    description: "Detect rapid layering, circular flows, structuring under thresholds, dormant-account spikes, and KYC/behavior profile mismatches."
  },
  {
    icon: <Search className="h-6 w-6" />,
    title: "Investigator trace",
    description: "Follow the full journey of funds—expand hops, highlight paths, and bookmark snapshots for case files."
  },
  {
    icon: <TrendingUp className="h-6 w-6" />,
    title: "ML suspicion scores",
    description: "Score accounts and subgraphs using graph features, velocity, and profile deviation—not just static rules."
  },
  {
    icon: <AlertTriangle className="h-6 w-6" />,
    title: "Operational alerts",
    description: "Route high-risk typologies to queues with severity, entity context, and links into the fund-flow explorer."
  }
];

