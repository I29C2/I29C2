// frontend/src/app/page.tsx
import Link from "next/link";
import { Activity, Shield, TrendingUp, Zap, BarChart2, Bell, Target, ChevronRight, CheckCircle } from "lucide-react";
import { Card } from "@/components/ui/Card";

const FEATURES = [
  {
    icon: <BarChart2 className="w-6 h-6 text-blue-400" />,
    title: "AI Value Bet Detection",
    description:
      "Our ML models calculate true probabilities and compare them to market odds to identify genuine edge opportunities.",
  },
  {
    icon: <Shield className="w-6 h-6 text-green-400" />,
    title: "Integrity Risk Monitor",
    description:
      "Automated detection of suspicious match patterns, line movements, and statistical anomalies.",
  },
  {
    icon: <TrendingUp className="w-6 h-6 text-amber-400" />,
    title: "ROI Tracking",
    description:
      "Track your betting performance over time with detailed P&L analytics and bankroll management tools.",
  },
  {
    icon: <Target className="w-6 h-6 text-red-400" />,
    title: "Multi-Market Analysis",
    description:
      "Predictions across 1X2, Over/Under, Both Teams to Score, Asian Handicap and more.",
  },
  {
    icon: <Bell className="w-6 h-6 text-purple-400" />,
    title: "Real-Time Alerts",
    description:
      "Get notified instantly via Telegram when high-value opportunities are detected.",
  },
  {
    icon: <Zap className="w-6 h-6 text-cyan-400" />,
    title: "Live Model Updates",
    description:
      "Models retrain nightly on the latest results, keeping predictions sharp and accurate.",
  },
];

const STEPS = [
  {
    step: "01",
    title: "AI Scans Matches",
    description:
      "Our models analyse every scheduled match across 30+ competitions, processing 200+ features per game.",
  },
  {
    step: "02",
    title: "Value Bets Identified",
    description:
      "Predictions with positive expected value are surfaced, ranked by edge strength and confidence.",
  },
  {
    step: "03",
    title: "You Make Informed Decisions",
    description:
      "View full AI reports, integrity scores, and suggested stakes — then decide with confidence.",
  },
];

const MOCK_STATS = {
  total_picks: 24,
  value_bets: 8,
  avg_edge: 6.4,
};

const MOCK_PICKS = [
  {
    id: "1",
    home: "Arsenal",
    away: "Chelsea",
    league: "Premier League",
    time: "20:00",
    market: "1X2",
    prediction: "Arsenal Win",
    probability: 0.67,
    odds: 1.95,
    edge: 8.2,
    confidence: "High",
    risk: "low",
  },
  {
    id: "2",
    home: "Real Madrid",
    away: "Barcelona",
    league: "La Liga",
    time: "21:00",
    market: "Over/Under",
    prediction: "Over 2.5",
    probability: 0.71,
    odds: 1.78,
    edge: 11.4,
    confidence: "Very High",
    risk: "low",
  },
  {
    id: "3",
    home: "Bayern Munich",
    away: "Dortmund",
    league: "Bundesliga",
    time: "17:30",
    market: "BTTS",
    prediction: "Yes",
    probability: 0.63,
    odds: 1.88,
    edge: 5.7,
    confidence: "Medium",
    risk: "medium",
  },
];

function ConfidenceBadge({ level }: { level: string }) {
  const map: Record<string, string> = {
    "Very High": "bg-green-500/20 text-green-400 border-green-500/30",
    "High": "bg-blue-500/20 text-blue-400 border-blue-500/30",
    "Medium": "bg-amber-500/20 text-amber-400 border-amber-500/30",
    "Low": "bg-slate-500/20 text-slate-400 border-slate-500/30",
  };
  return (
    <span
      className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${map[level] ?? map["Low"]}`}
    >
      {level}
    </span>
  );
}

function RiskBadge({ risk }: { risk: string }) {
  const map: Record<string, string> = {
    low: "bg-green-500/20 text-green-400",
    medium: "bg-amber-500/20 text-amber-400",
    high: "bg-orange-500/20 text-orange-400",
    critical: "bg-red-500/20 text-red-400",
  };
  return (
    <span
      className={`text-xs font-medium px-2 py-0.5 rounded-full ${map[risk] ?? map["low"]}`}
    >
      {risk.charAt(0).toUpperCase() + risk.slice(1)} Risk
    </span>
  );
}

export default function HomePage() {
  return (
    <div className="animate-fade-in">
      {/* Hero */}
      <section className="relative overflow-hidden bg-hero-pattern py-20 md:py-32">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-slate-900/80" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 bg-blue-600/20 border border-blue-500/30 text-blue-400 text-sm font-medium px-4 py-1.5 rounded-full mb-6">
            <Zap className="w-3.5 h-3.5" />
            Powered by Machine Learning
          </div>
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-white mb-6">
            AI-Powered{" "}
            <span className="text-gradient">Football Analysis</span>
          </h1>
          <p className="text-lg md:text-xl text-slate-300 max-w-2xl mx-auto mb-10 leading-relaxed">
            Discover genuine value bets, integrity risks, and deep match
            analysis — generated by state-of-the-art AI models trained on
            millions of matches.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/dashboard"
              className="px-8 py-3.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-all duration-200 glow-blue flex items-center justify-center gap-2"
            >
              View Today's Picks
              <ChevronRight className="w-4 h-4" />
            </Link>
            <Link
              href="/register"
              className="px-8 py-3.5 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
            >
              <Star className="w-4 h-4 text-amber-400" />
              Get Premium Access
            </Link>
          </div>
        </div>
      </section>

      {/* Stats bar */}
      <section className="bg-slate-800/50 border-y border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-white">
                {MOCK_STATS.total_picks}
              </p>
              <p className="text-xs text-slate-400 mt-0.5">Picks Today</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-400">
                {MOCK_STATS.value_bets}
              </p>
              <p className="text-xs text-slate-400 mt-0.5">Value Bets Found</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-400">
                +{MOCK_STATS.avg_edge}%
              </p>
              <p className="text-xs text-slate-400 mt-0.5">Avg Edge</p>
            </div>
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-24">
        {/* Top picks */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">
              Today's Top Picks
            </h2>
            <Link
              href="/dashboard"
              className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              View all <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="grid md:grid-cols-3 gap-5">
            {MOCK_PICKS.map((pick) => (
              <Card key={pick.id} className="p-5 flex flex-col gap-4 hover:border-blue-500/40 transition-colors">
                {/* Match header */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-slate-400 font-medium">
                      🏆 {pick.league}
                    </span>
                    <span className="text-xs text-slate-500">{pick.time}</span>
                  </div>
                  <p className="font-semibold text-white text-sm">
                    {pick.home} vs {pick.away}
                  </p>
                </div>

                {/* Prediction */}
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded font-mono">
                    {pick.market}
                  </span>
                  <span className="text-sm font-semibold text-white">
                    {pick.prediction}
                  </span>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="bg-slate-900/50 rounded-lg p-2">
                    <p className="text-xs text-slate-400">AI Prob</p>
                    <p className="text-sm font-bold text-white">
                      {(pick.probability * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div className="bg-slate-900/50 rounded-lg p-2">
                    <p className="text-xs text-slate-400">Odds</p>
                    <p className="text-sm font-bold text-white">{pick.odds}</p>
                  </div>
                  <div className="bg-slate-900/50 rounded-lg p-2">
                    <p className="text-xs text-slate-400">Edge</p>
                    <p className="text-sm font-bold text-green-400">
                      +{pick.edge}%
                    </p>
                  </div>
                </div>

                {/* Badges */}
                <div className="flex items-center gap-2">
                  <ConfidenceBadge level={pick.confidence} />
                  <RiskBadge risk={pick.risk} />
                </div>

                {/* CTA */}
                <Link
                  href="/dashboard"
                  className="mt-auto w-full text-center py-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 text-blue-400 text-sm font-medium rounded-lg transition-colors"
                >
                  Full Analysis
                </Link>
              </Card>
            ))}
          </div>
        </section>

        {/* Features */}
        <section>
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-3">
              Everything You Need to Bet Smarter
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              BetBot AI combines cutting-edge machine learning with comprehensive
              data coverage to give you a real edge.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((feature) => (
              <Card key={feature.title} className="p-6">
                <div className="w-12 h-12 rounded-xl bg-slate-900/70 flex items-center justify-center mb-4">
                  {feature.icon}
                </div>
                <h3 className="font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">
                  {feature.description}
                </p>
              </Card>
            ))}
          </div>
        </section>

        {/* How it works */}
        <section>
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-3">
              How It Works
            </h2>
            <p className="text-slate-400">
              From raw data to actionable picks in three steps.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {STEPS.map((step, i) => (
              <div key={step.step} className="relative flex flex-col items-center text-center">
                {i < STEPS.length - 1 && (
                  <div className="hidden md:block absolute top-8 left-[60%] w-[80%] h-0.5 bg-gradient-to-r from-blue-600/50 to-transparent" />
                )}
                <div className="w-16 h-16 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center mb-4">
                  <span className="text-blue-400 font-bold text-xl">
                    {step.step}
                  </span>
                </div>
                <h3 className="font-semibold text-white mb-2 text-lg">
                  {step.title}
                </h3>
                <p className="text-sm text-slate-400 leading-relaxed max-w-xs">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Premium CTA */}
        <section>
          <div className="relative rounded-2xl overflow-hidden bg-gradient-to-r from-blue-900/50 to-slate-800 border border-blue-500/30 p-8 md:p-12 text-center">
            <div className="absolute inset-0 bg-gradient-radial from-blue-600/10 to-transparent" />
            <div className="relative">
              <div className="inline-flex items-center gap-2 bg-amber-500/20 border border-amber-500/30 text-amber-400 text-sm font-medium px-4 py-1.5 rounded-full mb-4">
                <Star className="w-3.5 h-3.5" />
                Premium Plan
              </div>
              <h2 className="text-3xl font-bold text-white mb-3">
                Unlock the Full Platform
              </h2>
              <p className="text-slate-300 max-w-xl mx-auto mb-6">
                Get unlimited picks, full integrity reports, real-time Telegram
                alerts, and priority access to all competitions.
              </p>
              <ul className="flex flex-wrap justify-center gap-x-6 gap-y-2 mb-8 text-sm text-slate-300">
                {[
                  "Unlimited daily picks",
                  "All 30+ competitions",
                  "Real-time Telegram alerts",
                  "Full integrity reports",
                  "Bankroll analytics",
                  "API access",
                ].map((item) => (
                  <li key={item} className="flex items-center gap-1.5">
                    <CheckCircle className="w-4 h-4 text-green-400 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
              <Link
                href="/register"
                className="inline-flex items-center gap-2 px-8 py-3.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-all duration-200 glow-blue"
              >
                Start Free Trial
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
