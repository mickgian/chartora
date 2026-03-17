/** TypeScript types matching the backend API response schemas. */

export interface CompanyResponse {
  id: number;
  name: string;
  slug: string;
  sector: "pure_play" | "big_tech" | "etf";
  ticker: string | null;
  description: string | null;
  is_etf: boolean;
  website: string | null;
  logo_url: string | null;
}

export interface ScoreResponse {
  total_score: number;
  stock_momentum: number;
  patent_velocity: number;
  qubit_progress: number;
  funding_strength: number;
  news_sentiment: number;
  score_date: string;
  rank: number | null;
  rank_change: number | null;
}

export interface LeaderboardEntry {
  rank: number;
  company: CompanyResponse;
  score: ScoreResponse;
  trend: "up" | "down" | "flat";
  metric_value: number;
}

export interface LeaderboardResponse {
  metric: string;
  entries: LeaderboardEntry[];
  count: number;
  updated_at: string | null;
  hardcoded_metrics: string[];
}

export interface StockPriceResponse {
  price_date: string;
  close_price: number;
  open_price: number | null;
  high_price: number | null;
  low_price: number | null;
  volume: number | null;
  market_cap: number | null;
}

export interface StockHistoryResponse {
  company_slug: string;
  prices: StockPriceResponse[];
  count: number;
}

export interface IntradayPriceResponse {
  timestamp: string;
  price: number;
  volume: number | null;
}

export interface IntradayResponse {
  company_slug: string;
  prices: IntradayPriceResponse[];
  count: number;
}

export interface PatentResponse {
  patent_number: string;
  title: string;
  filing_date: string;
  source: "USPTO" | "EPO";
  abstract: string | null;
  grant_date: string | null;
  classification: string | null;
}

export interface PatentListResponse {
  company_slug: string;
  patents: PatentResponse[];
  count: number;
}

export interface NewsArticleResponse {
  title: string;
  url: string;
  published_at: string;
  source_name: string | null;
  sentiment: "bullish" | "bearish" | "neutral" | null;
  sentiment_score: number | null;
}

export interface NewsListResponse {
  company_slug: string;
  articles: NewsArticleResponse[];
  count: number;
}

export interface FilingResponse {
  filing_type: "10-K" | "10-Q" | "Form4" | "13F";
  filing_date: string;
  description: string | null;
  url: string | null;
}

export interface FilingListResponse {
  company_slug: string;
  filings: FilingResponse[];
  count: number;
}

export interface RankingEntry {
  rank: number;
  company: CompanyResponse;
  metric_value: number;
  trend: "up" | "down" | "flat";
}

export interface RankingResponse {
  metric: string;
  entries: RankingEntry[];
  count: number;
}

export interface CompanyDetailResponse {
  company: CompanyResponse;
  score: ScoreResponse | null;
}

export interface GovernmentContractResponse {
  award_id: string;
  title: string;
  amount: number;
  awarding_agency: string;
  start_date: string;
  end_date: string | null;
  description: string | null;
}

export interface GovernmentContractListResponse {
  company_slug: string;
  company_name: string;
  contracts: GovernmentContractResponse[];
  total_value: number;
  count: number;
}

export interface RdSpendingResponse {
  company_slug: string;
  company_name: string;
  rd_expense: number | null;
  total_revenue: number | null;
  rd_ratio: number | null;
}

export interface HistoricalScoreEntry {
  date: string;
  total_score: number;
  stock_momentum: number;
  patent_velocity: number;
  qubit_progress: number;
  funding_strength: number;
  news_sentiment: number;
  rank: number | null;
}

export interface HistoricalScoresResponse {
  company_slug: string;
  company_name: string;
  period_days: number;
  scores: HistoricalScoreEntry[];
  count: number;
}

export interface InsiderTradeEntry {
  filing_date: string;
  description: string | null;
  url: string | null;
  data: Record<string, unknown> | null;
}

export interface InsiderTradingResponse {
  company_slug: string;
  company_name: string;
  insider_trades: InsiderTradeEntry[];
  count: number;
}

export interface InstitutionalOwnershipResponse {
  company_slug: string;
  company_name: string;
  institutional_filings: InsiderTradeEntry[];
  count: number;
}

export interface ErrorResponse {
  detail: string;
}

export type SortableMetric =
  | "total_score"
  | "stock_momentum"
  | "patent_velocity"
  | "qubit_progress"
  | "funding_strength"
  | "news_sentiment";

export type RankingMetric = "stock-performance" | "patents" | "funding" | "sentiment";
