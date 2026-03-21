/**
 * Mock data for GitHub Pages static preview (demo mode).
 * Provides realistic sample data for all tracked quantum computing companies.
 */

import type {
  CompanyResponse,
  CompanyDetailResponse,
  IntradayResponse,
  LeaderboardEntry,
  LeaderboardResponse,
  StockHistoryResponse,
  PatentListResponse,
  NewsListResponse,
  FilingListResponse,
  RankingEntry,
  RankingResponse,
  RankingMetric,
  ScoreResponse,
  SortableMetric,
} from "@/types/api";

const MOCK_DATE = "2026-03-15";

const companies: CompanyResponse[] = [
  { id: 1, name: "IonQ", slug: "ionq", sector: "pure_play", ticker: "IONQ", description: "IonQ is a leader in trapped-ion quantum computing, offering cloud-based quantum computing services through major cloud providers.", is_etf: false, website: "https://ionq.com", logo_url: null },
  { id: 2, name: "D-Wave Quantum", slug: "d-wave-quantum", sector: "pure_play", ticker: "QBTS", description: "D-Wave is the world's first commercial quantum computing company, specializing in quantum annealing systems.", is_etf: false, website: "https://dwavesys.com", logo_url: null },
  { id: 3, name: "Rigetti Computing", slug: "rigetti-computing", sector: "pure_play", ticker: "RGTI", description: "Rigetti designs and manufactures superconducting quantum processors and provides cloud access to its quantum systems.", is_etf: false, website: "https://rigetti.com", logo_url: null },
  { id: 4, name: "Quantum Computing Inc", slug: "quantum-computing-inc", sector: "pure_play", ticker: "QUBT", description: "Quantum Computing Inc focuses on making quantum computing accessible through innovative software and hardware solutions.", is_etf: false, website: "https://quantumcomputinginc.com", logo_url: null },
  { id: 5, name: "Arqit Quantum", slug: "arqit-quantum", sector: "pure_play", ticker: "ARQQ", description: "Arqit supplies a unique quantum encryption platform that makes the communications links of any networked device secure.", is_etf: false, website: "https://arqit.uk", logo_url: null },
  { id: 6, name: "Infleqtion", slug: "infleqtion", sector: "pure_play", ticker: "INFQ", description: "Infleqtion develops cold atom quantum technologies for sensing, networking, and computing applications.", is_etf: false, website: "https://infleqtion.com", logo_url: null },
  { id: 7, name: "SEALSQ", slug: "sealsq", sector: "pure_play", ticker: "LAES", description: "SEALSQ focuses on post-quantum semiconductors and security solutions for IoT and blockchain applications.", is_etf: false, website: "https://sealsq.com", logo_url: null },
  { id: 8, name: "BTQ Technologies", slug: "btq-technologies", sector: "pure_play", ticker: "BTQ", description: "BTQ Technologies develops post-quantum cryptographic solutions to secure blockchain and digital infrastructure.", is_etf: false, website: "https://btq.com", logo_url: null },
  { id: 9, name: "QuantumCTek", slug: "quantumctek", sector: "pure_play", ticker: "688027.SS", description: "QuantumCTek is a Chinese quantum information technology company specializing in quantum communication products.", is_etf: false, website: null, logo_url: null },
  { id: 10, name: "Quantum eMotion", slug: "quantum-emotion", sector: "pure_play", ticker: "QNC.V", description: "Quantum eMotion develops quantum random number generators for cybersecurity applications.", is_etf: false, website: "https://quantumemotion.com", logo_url: null },
  { id: 11, name: "01 Communique", slug: "01-communique", sector: "pure_play", ticker: "ONE.V", description: "01 Communique develops IronCAP, a post-quantum cryptographic solution for securing digital communications.", is_etf: false, website: "https://01com.com", logo_url: null },
  { id: 12, name: "IBM", slug: "ibm", sector: "big_tech", ticker: "IBM", description: "IBM is a pioneer in quantum computing with its IBM Quantum platform, offering access to over 100-qubit processors.", is_etf: false, website: "https://ibm.com", logo_url: null },
  { id: 13, name: "Alphabet (Google)", slug: "alphabet-google", sector: "big_tech", ticker: "GOOGL", description: "Google's quantum AI lab achieved quantum supremacy in 2019 and continues to advance error-corrected quantum computing.", is_etf: false, website: "https://quantumai.google", logo_url: null },
  { id: 14, name: "Microsoft", slug: "microsoft", sector: "big_tech", ticker: "MSFT", description: "Microsoft is developing topological qubits and offers Azure Quantum, a cloud platform for quantum computing.", is_etf: false, website: "https://azure.microsoft.com/quantum", logo_url: null },
  { id: 15, name: "Amazon (AWS)", slug: "amazon-aws", sector: "big_tech", ticker: "AMZN", description: "Amazon offers Amazon Braket, a fully managed quantum computing service, and invests in quantum networking research.", is_etf: false, website: "https://aws.amazon.com/braket", logo_url: null },
  { id: 16, name: "Intel", slug: "intel", sector: "big_tech", ticker: "INTC", description: "Intel is developing silicon-based quantum processors, leveraging its semiconductor manufacturing expertise.", is_etf: false, website: "https://intel.com", logo_url: null },
  { id: 17, name: "Honeywell (Quantinuum)", slug: "honeywell-quantinuum", sector: "big_tech", ticker: "HON", description: "Quantinuum, formed from Honeywell Quantum Solutions and Cambridge Quantum, operates the highest-fidelity quantum computers.", is_etf: false, website: "https://quantinuum.com", logo_url: null },
  { id: 18, name: "NVIDIA", slug: "nvidia", sector: "big_tech", ticker: "NVDA", description: "NVIDIA provides GPU-accelerated quantum circuit simulation and partners with quantum hardware companies.", is_etf: false, website: "https://nvidia.com", logo_url: null },
  { id: 19, name: "Fujitsu", slug: "fujitsu", sector: "big_tech", ticker: "6702.T", description: "Fujitsu develops quantum-inspired digital annealer technology and superconducting quantum computing hardware.", is_etf: false, website: "https://fujitsu.com", logo_url: null },
  { id: 20, name: "Defiance Quantum ETF", slug: "defiance-quantum-etf", sector: "etf", ticker: "QTUM", description: "The Defiance Quantum ETF tracks companies involved in quantum computing, machine learning, and other transformative technologies.", is_etf: true, website: null, logo_url: null },
  { id: 21, name: "WisdomTree Quantum Computing Fund", slug: "wisdomtree-quantum-etf", sector: "etf", ticker: "WQTM", description: "WisdomTree Quantum Computing Fund provides targeted exposure to companies advancing quantum computing.", is_etf: true, website: null, logo_url: null },
  { id: 22, name: "VanEck Quantum Computing UCITS ETF", slug: "vaneck-quantum-etf", sector: "etf", ticker: "QNTM.L", description: "VanEck Quantum Computing UCITS ETF invests in global quantum computing companies.", is_etf: true, website: null, logo_url: null },
  { id: 23, name: "iShares Quantum Computing UCITS ETF", slug: "ishares-quantum-etf", sector: "etf", ticker: "QANT.AS", description: "iShares Quantum Computing UCITS ETF tracks an index of quantum computing companies worldwide.", is_etf: true, website: null, logo_url: null },
  { id: 24, name: "Global X AI Semiconductor & Quantum ETF", slug: "globalx-ai-quantum-etf", sector: "etf", ticker: "CHPX", description: "Global X AI Semiconductor & Quantum ETF provides exposure to AI semiconductor and quantum computing companies.", is_etf: true, website: null, logo_url: null },
];

const scores: Record<string, ScoreResponse> = {
  ionq: { total_score: 82.4, stock_momentum: 17.2, patent_velocity: 21.8, qubit_progress: 16.5, funding_strength: 15.4, news_sentiment: 11.5, score_date: MOCK_DATE, rank: 1, rank_change: 0 },
  "d-wave-quantum": { total_score: 76.1, stock_momentum: 14.8, patent_velocity: 19.2, qubit_progress: 18.0, funding_strength: 13.6, news_sentiment: 10.5, score_date: MOCK_DATE, rank: 2, rank_change: 1 },
  "rigetti-computing": { total_score: 71.3, stock_momentum: 15.6, patent_velocity: 16.4, qubit_progress: 15.8, funding_strength: 12.9, news_sentiment: 10.6, score_date: MOCK_DATE, rank: 3, rank_change: -1 },
  ibm: { total_score: 69.8, stock_momentum: 11.2, patent_velocity: 22.5, qubit_progress: 17.2, funding_strength: 9.8, news_sentiment: 9.1, score_date: MOCK_DATE, rank: 4, rank_change: 0 },
  "alphabet-google": { total_score: 67.5, stock_momentum: 12.4, patent_velocity: 20.1, qubit_progress: 16.8, funding_strength: 8.9, news_sentiment: 9.3, score_date: MOCK_DATE, rank: 5, rank_change: 2 },
  "honeywell-quantinuum": { total_score: 65.2, stock_momentum: 10.8, patent_velocity: 18.6, qubit_progress: 17.5, funding_strength: 9.2, news_sentiment: 9.1, score_date: MOCK_DATE, rank: 6, rank_change: -1 },
  microsoft: { total_score: 63.9, stock_momentum: 11.6, patent_velocity: 17.8, qubit_progress: 14.2, funding_strength: 10.5, news_sentiment: 9.8, score_date: MOCK_DATE, rank: 7, rank_change: 0 },
  nvidia: { total_score: 62.1, stock_momentum: 15.8, patent_velocity: 14.2, qubit_progress: 10.5, funding_strength: 12.8, news_sentiment: 8.8, score_date: MOCK_DATE, rank: 8, rank_change: 2 },
  "quantum-computing-inc": { total_score: 58.4, stock_momentum: 16.1, patent_velocity: 10.2, qubit_progress: 11.5, funding_strength: 12.4, news_sentiment: 8.2, score_date: MOCK_DATE, rank: 9, rank_change: -1 },
  "amazon-aws": { total_score: 55.7, stock_momentum: 10.2, patent_velocity: 14.5, qubit_progress: 12.8, funding_strength: 9.6, news_sentiment: 8.6, score_date: MOCK_DATE, rank: 10, rank_change: -1 },
  infleqtion: { total_score: 54.3, stock_momentum: 12.1, patent_velocity: 13.8, qubit_progress: 11.2, funding_strength: 10.1, news_sentiment: 7.1, score_date: MOCK_DATE, rank: 11, rank_change: 1 },
  "arqit-quantum": { total_score: 52.1, stock_momentum: 13.4, patent_velocity: 11.8, qubit_progress: 8.2, funding_strength: 11.2, news_sentiment: 7.5, score_date: MOCK_DATE, rank: 12, rank_change: -1 },
  fujitsu: { total_score: 50.8, stock_momentum: 9.4, patent_velocity: 16.2, qubit_progress: 11.8, funding_strength: 7.2, news_sentiment: 6.2, score_date: MOCK_DATE, rank: 13, rank_change: 0 },
  intel: { total_score: 48.6, stock_momentum: 8.9, patent_velocity: 15.2, qubit_progress: 10.4, funding_strength: 7.8, news_sentiment: 6.3, score_date: MOCK_DATE, rank: 14, rank_change: 1 },
  sealsq: { total_score: 46.2, stock_momentum: 14.5, patent_velocity: 8.4, qubit_progress: 6.8, funding_strength: 10.2, news_sentiment: 6.3, score_date: MOCK_DATE, rank: 15, rank_change: 2 },
  "btq-technologies": { total_score: 44.8, stock_momentum: 13.2, patent_velocity: 7.6, qubit_progress: 6.2, funding_strength: 11.4, news_sentiment: 6.4, score_date: MOCK_DATE, rank: 16, rank_change: -1 },
  quantumctek: { total_score: 43.5, stock_momentum: 8.8, patent_velocity: 12.4, qubit_progress: 10.2, funding_strength: 6.8, news_sentiment: 5.3, score_date: MOCK_DATE, rank: 17, rank_change: -1 },
  "quantum-emotion": { total_score: 41.2, stock_momentum: 11.8, patent_velocity: 6.2, qubit_progress: 5.8, funding_strength: 10.8, news_sentiment: 6.6, score_date: MOCK_DATE, rank: 18, rank_change: 0 },
  "01-communique": { total_score: 39.8, stock_momentum: 10.4, patent_velocity: 5.8, qubit_progress: 5.2, funding_strength: 12.2, news_sentiment: 6.2, score_date: MOCK_DATE, rank: 19, rank_change: 0 },
  "defiance-quantum-etf": { total_score: 41.8, stock_momentum: 12.8, patent_velocity: 0, qubit_progress: 0, funding_strength: 18.2, news_sentiment: 10.8, score_date: MOCK_DATE, rank: 20, rank_change: 0 },
  "wisdomtree-quantum-etf": { total_score: 40.2, stock_momentum: 11.6, patent_velocity: 0, qubit_progress: 0, funding_strength: 17.8, news_sentiment: 10.8, score_date: MOCK_DATE, rank: 21, rank_change: 0 },
  "vaneck-quantum-etf": { total_score: 39.4, stock_momentum: 11.2, patent_velocity: 0, qubit_progress: 0, funding_strength: 17.4, news_sentiment: 10.8, score_date: MOCK_DATE, rank: 22, rank_change: 0 },
  "ishares-quantum-etf": { total_score: 38.8, stock_momentum: 10.8, patent_velocity: 0, qubit_progress: 0, funding_strength: 17.2, news_sentiment: 10.8, score_date: MOCK_DATE, rank: 23, rank_change: 0 },
  "globalx-ai-quantum-etf": { total_score: 38.5, stock_momentum: 11.4, patent_velocity: 0, qubit_progress: 0, funding_strength: 16.8, news_sentiment: 10.3, score_date: MOCK_DATE, rank: 24, rank_change: 0 },
};

function getTrend(rankChange: number | null): "up" | "down" | "flat" {
  if (!rankChange) return "flat";
  return rankChange > 0 ? "up" : rankChange < 0 ? "down" : "flat";
}

function buildLeaderboardEntries(sortBy: SortableMetric): LeaderboardEntry[] {
  return companies
    .map((company) => {
      const score = scores[company.slug];
      return {
        rank: 0,
        company,
        score,
        trend: getTrend(score.rank_change),
        metric_value: score[sortBy] as number,
      };
    })
    .sort((a, b) => (b.score[sortBy] as number) - (a.score[sortBy] as number))
    .map((entry, i) => ({ ...entry, rank: i + 1 }));
}

function generateStockHistory(slug: string, days: number | 0): StockHistoryResponse {
  const effectiveDays = days === 0 ? 3650 : days;
  const basePrice: Record<string, number> = {
    ionq: 32.5, "d-wave-quantum": 8.2, "rigetti-computing": 12.4,
    "quantum-computing-inc": 3.8, "arqit-quantum": 5.1, ibm: 198.5,
    "alphabet-google": 178.2, microsoft: 428.6, "amazon-aws": 192.3,
    intel: 28.7, "honeywell-quantinuum": 215.8, nvidia: 142.5,
    fujitsu: 18.4, infleqtion: 6.8, sealsq: 4.2,
    "btq-technologies": 2.8, quantumctek: 45.6, "quantum-emotion": 1.5,
    "01-communique": 0.85, "defiance-quantum-etf": 72.4,
    "wisdomtree-quantum-etf": 28.6, "vaneck-quantum-etf": 15.2,
    "ishares-quantum-etf": 12.8, "globalx-ai-quantum-etf": 22.4,
  };
  const base = basePrice[slug] ?? 10;
  const prices = [];
  for (let i = effectiveDays; i >= 0; i--) {
    const date = new Date(2026, 2, 15);
    date.setDate(date.getDate() - i);
    const drift = (Math.sin(i * 0.15) * 0.08 + Math.cos(i * 0.07) * 0.05) * base;
    const close = Math.round((base + drift + (effectiveDays - i) * base * 0.001) * 100) / 100;
    prices.push({
      price_date: date.toISOString().split("T")[0],
      close_price: close,
      open_price: Math.round((close * (1 + (Math.sin(i) * 0.01))) * 100) / 100,
      high_price: Math.round((close * 1.02) * 100) / 100,
      low_price: Math.round((close * 0.98) * 100) / 100,
      volume: Math.floor(1000000 + Math.random() * 5000000),
      market_cap: Math.floor(close * 100000000),
    });
  }
  return { company_slug: slug, prices, count: prices.length };
}

function generateIntradayHistory(slug: string): IntradayResponse {
  const basePrice: Record<string, number> = {
    ionq: 32.5, "d-wave-quantum": 8.2, "rigetti-computing": 12.4,
    "quantum-computing-inc": 3.8, "arqit-quantum": 5.1, ibm: 198.5,
    "alphabet-google": 178.2, microsoft: 428.6, "amazon-aws": 192.3,
    intel: 28.7, "honeywell-quantinuum": 215.8, nvidia: 142.5,
    fujitsu: 18.4, infleqtion: 6.8, sealsq: 4.2,
    "btq-technologies": 2.8, quantumctek: 45.6, "quantum-emotion": 1.5,
    "01-communique": 0.85, "defiance-quantum-etf": 72.4,
    "wisdomtree-quantum-etf": 28.6, "vaneck-quantum-etf": 15.2,
    "ishares-quantum-etf": 12.8, "globalx-ai-quantum-etf": 22.4,
  };
  const base = basePrice[slug] ?? 10;
  const prices = [];
  const today = new Date(2026, 2, 15);
  for (let h = 0; h <= 13; h++) {
    const ts = new Date(today);
    ts.setHours(9, 30 + h * 30, 0, 0);
    const drift = (Math.sin(h * 0.8) * 0.02 + Math.cos(h * 0.5) * 0.01) * base;
    const price = Math.round((base + drift) * 100) / 100;
    prices.push({
      timestamp: ts.toISOString(),
      price,
      volume: Math.floor(100000 + Math.random() * 500000),
    });
  }
  return { company_slug: slug, prices, count: prices.length };
}

function generatePatents(slug: string): PatentListResponse {
  const patentCounts: Record<string, number> = {
    ionq: 18, ibm: 45, "alphabet-google": 38, microsoft: 28,
    "honeywell-quantinuum": 32, "d-wave-quantum": 22, "rigetti-computing": 15,
    intel: 20, "amazon-aws": 14, nvidia: 12, fujitsu: 16,
    infleqtion: 10, sealsq: 6, "btq-technologies": 4,
    quantumctek: 24, "quantum-emotion": 5, "01-communique": 3,
    "quantum-computing-inc": 6, "arqit-quantum": 10,
  };
  const count = patentCounts[slug] ?? 0;
  const patents = [];
  for (let i = 0; i < Math.min(count, 10); i++) {
    const date = new Date(2025, 2 + Math.floor(i / 3), 1 + i * 3);
    patents.push({
      patent_number: `US${11000000 + i * 137 + companies.findIndex((c) => c.slug === slug) * 1000}`,
      title: `Quantum ${["Error Correction", "Gate Optimization", "Qubit Coupling", "Entanglement Protocol", "Noise Reduction", "Circuit Design", "Readout Enhancement", "Calibration Method", "Coherence Extension", "Control System"][i]} Method`,
      filing_date: date.toISOString().split("T")[0],
      source: (i % 3 === 0 ? "EPO" : "USPTO") as "USPTO" | "EPO",
      abstract: `A novel approach to quantum computing involving advanced ${["error correction", "gate operations", "qubit coupling", "entanglement", "noise mitigation", "circuit optimization", "readout fidelity", "system calibration", "coherence time", "feedback control"][i]} techniques.`,
      grant_date: i < 5 ? new Date(2025, 6 + Math.floor(i / 2), 15).toISOString().split("T")[0] : null,
      classification: "G06N 10/00",
    });
  }
  return { company_slug: slug, patents, count };
}

function generateNews(slug: string): NewsListResponse {
  const company = companies.find((c) => c.slug === slug);
  const name = company?.name ?? slug;
  const sentiments: Array<"bullish" | "bearish" | "neutral"> = ["bullish", "neutral", "bullish", "neutral", "bearish", "bullish", "neutral", "bullish"];
  const articles = sentiments.map((sentiment, i) => {
    const date = new Date(2026, 2, 15 - i * 2);
    return {
      title: [
        `${name} Announces Major Quantum Computing Breakthrough`,
        `Analysts Weigh In on ${name}'s Quarterly Earnings`,
        `${name} Expands Quantum Cloud Services Partnership`,
        `New Research Paper from ${name} Team Published in Nature`,
        `Market Volatility Impacts ${name} Stock Price`,
        `${name} Secures Government Contract for Quantum Research`,
        `Industry Report Highlights ${name}'s Patent Portfolio`,
        `${name} CEO Discusses Quantum Roadmap at Tech Summit`,
      ][i],
      url: `https://example.com/news/${slug}-${i}`,
      published_at: date.toISOString(),
      source_name: ["TechCrunch", "Bloomberg", "Reuters", "Nature", "MarketWatch", "Defense News", "IEEE Spectrum", "CNBC"][i],
      sentiment,
      sentiment_score: sentiment === "bullish" ? 0.7 + Math.random() * 0.25 : sentiment === "bearish" ? 0.2 + Math.random() * 0.15 : 0.45 + Math.random() * 0.1,
    };
  });
  return { company_slug: slug, articles, count: articles.length };
}

function generateFilings(slug: string): FilingListResponse {
  const filings = [
    { filing_type: "10-K" as const, filing_date: "2025-12-15", description: "Annual report for fiscal year 2025", url: `https://sec.gov/filing/${slug}/10k-2025` },
    { filing_type: "10-Q" as const, filing_date: "2025-09-30", description: "Quarterly report Q3 2025", url: `https://sec.gov/filing/${slug}/10q-q3-2025` },
    { filing_type: "Form4" as const, filing_date: "2025-11-20", description: "Insider transaction — CEO purchase of shares", url: `https://sec.gov/filing/${slug}/form4-nov2025` },
    { filing_type: "10-Q" as const, filing_date: "2025-06-30", description: "Quarterly report Q2 2025", url: `https://sec.gov/filing/${slug}/10q-q2-2025` },
    { filing_type: "13F" as const, filing_date: "2025-08-14", description: "Institutional holdings report", url: `https://sec.gov/filing/${slug}/13f-2025` },
  ];
  return { company_slug: slug, filings, count: filings.length };
}

// --- Public API matching apiClient interface ---

export const mockApi = {
  getLeaderboard(params?: { sort_by?: SortableMetric; limit?: number }): LeaderboardResponse {
    const sortBy = params?.sort_by ?? "total_score";
    let entries = buildLeaderboardEntries(sortBy);
    if (params?.limit) entries = entries.slice(0, params.limit);
    return { metric: sortBy, entries, count: entries.length, updated_at: `${MOCK_DATE}T08:00:00Z`, hardcoded_metrics: ["qubit_progress", "funding_strength", "patent_velocity"] };
  },

  getCompany(slug: string): CompanyDetailResponse {
    const company = companies.find((c) => c.slug === slug);
    if (!company) {
      return { company: { id: 0, name: slug, slug, sector: "pure_play", ticker: null, description: null, is_etf: false, website: null, logo_url: null }, score: null };
    }
    return { company, score: scores[slug] ?? null };
  },

  getStockHistory(slug: string, days = 90): StockHistoryResponse {
    return generateStockHistory(slug, days);
  },

  getIntradayHistory(slug: string): IntradayResponse {
    return generateIntradayHistory(slug);
  },

  getPatents(slug: string): PatentListResponse {
    return generatePatents(slug);
  },

  getNews(slug: string): NewsListResponse {
    return generateNews(slug);
  },

  getFilings(slug: string): FilingListResponse {
    return generateFilings(slug);
  },

  getRanking(metric: RankingMetric): RankingResponse {
    const metricToSort: Record<RankingMetric, SortableMetric> = {
      "stock-performance": "stock_momentum",
      patents: "patent_velocity",
      funding: "funding_strength",
      sentiment: "news_sentiment",
    };
    const sortBy = metricToSort[metric];
    const entries: RankingEntry[] = companies
      .map((company) => {
        const score = scores[company.slug];
        return {
          rank: 0,
          company,
          metric_value: score[sortBy] as number,
          trend: getTrend(score.rank_change),
        };
      })
      .sort((a, b) => b.metric_value - a.metric_value)
      .map((entry, i) => ({ ...entry, rank: i + 1 }));

    return { metric, entries, count: entries.length };
  },
};

/** All company slugs — used by generateStaticParams */
export const ALL_COMPANY_SLUGS = companies.map((c) => c.slug);
