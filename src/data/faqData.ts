export const faqItems = [
  {
    question: "What problem does FundFlow Trace solve (PS3)?",
    answer:
      "It maps and visualizes end-to-end movement of funds within the bank across accounts, products, branches, and channels. Graph analytics and machine learning highlight suspicious behaviors—rapid layering, circular flows, structuring, dormant-account activity, and profile mismatches—so investigators can trace journeys and assemble FIU-oriented evidence packages.",
  },
  {
    question: "What data do we ingest?",
    answer:
      "Typically core-banking or warehouse extracts with debit/credit account identifiers, amount, value date, product code, branch, channel (branch, mobile, UPI, NEFT, etc.), and customer linkage where permitted. CSV or batch APIs are supported in this prototype.",
  },
  {
    question: "How are patterns detected?",
    answer:
      "A unified fund-flow graph is built from transfers. Rules encode thresholds and typologies; ML models (including graph-based scoring) rank subgraphs and accounts. Metrics include velocity, cycle detection, amount bands near limits, dormancy breaks, and deviation from KYC-declared profile.",
  },
  {
    question: "Is this only machine learning?",
    answer:
      "No. The stack combines explicit graph algorithms (paths, cycles, communities), business rules, and ML for suspicion scores—so analysts get both explainability and ranked risk.",
  },
  {
    question: "How do investigators use it?",
    answer:
      "They open a case from an alert, expand hops on the fund-flow graph, bookmark snapshots, and export a structured package: timeline, subgraph, entity list, and rationale suitable for internal escalation and FIU reporting workflows.",
  },
  {
    question: "Does this replace core AML systems?",
    answer:
      "This prototype is a decision-support and visualization layer for internal fund-flow fraud. Production deployment would integrate with existing transaction monitoring, case management, and regulatory reporting—with appropriate model governance and privacy controls.",
  },
];
