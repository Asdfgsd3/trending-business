from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass
class Company:
    name: str
    ticker: str | None
    aliases: List[str]


def load_companies(csv_path: str) -> List[Company]:
    companies: List[Company] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            ticker = (row.get("ticker") or "").strip() or None
            aliases_raw = (row.get("aliases") or "").strip()
            aliases = [a.strip() for a in aliases_raw.split(";") if a.strip()]
            if not name:
                continue
            companies.append(Company(name=name, ticker=ticker, aliases=aliases))
    return companies


class TrendingDetector:
    def __init__(self, companies: List[Company], baseline_state: Dict | None = None):
        self.companies = companies
        # Build patterns for matching names, aliases, and tickers
        self.company_patterns: List[Tuple[Company, List[re.Pattern[str]]]] = []
        for c in companies:
            patterns: List[re.Pattern[str]] = []
            # Name
            patterns.append(self._compile_word_pattern(c.name))
            # Aliases
            for a in c.aliases:
                patterns.append(self._compile_word_pattern(a))
            # Ticker and $ticker forms
            if c.ticker:
                patterns.append(self._compile_ticker_pattern(c.ticker))
            self.company_patterns.append((c, patterns))

        # Baseline EMA per company
        self.alpha = 0.3  # EMA smoothing factor for baseline
        self.recent_alpha = 0.5 # EMA smoothing factor for recent counts (faster adaptation)
        self.min_mentions_for_trend = 2.0
        self.baseline: Dict[str, float] = {}
        self.recent_ema: Dict[str, float] = {} # Track smoothed recent counts
        
        if baseline_state and isinstance(baseline_state, dict):
            self.baseline = {k: float(v) for k, v in baseline_state.get("baseline", {}).items()}
            self.recent_ema = {k: float(v) for k, v in baseline_state.get("recent_ema", {}).items()}

    def _compile_word_pattern(self, phrase: str) -> re.Pattern[str]:
        escaped = re.escape(phrase)
        return re.compile(rf"(?i)(?<![\w$]){escaped}(?![\w$])")

    def _compile_ticker_pattern(self, ticker: str) -> re.Pattern[str]:
        escaped = re.escape(ticker)
        return re.compile(rf"(?i)(?<![\w])\$?{escaped}(?![\w])")

    def _count_mentions(self, text: str) -> Dict[str, Tuple[int, str | None]]:
        counts: Dict[str, Tuple[int, str | None]] = {}
        for company, patterns in self.company_patterns:
            total = 0
            alias_used: str | None = None
            for i, p in enumerate(patterns):
                matches = p.findall(text)
                if matches:
                    total += len(matches)
                    if alias_used is None:
                        # Try to get the actual alias from the company's alias list
                        if i == 0:
                            alias_used = company.name  # First pattern is company name
                        elif i - 1 < len(company.aliases):
                            alias_used = company.aliases[i - 1]  # Subsequent patterns are aliases
                        elif company.ticker and i == len(company.aliases) + 1:
                            alias_used = f"${company.ticker}"  # Ticker pattern
                        else:
                            alias_used = None  # Unknown, don't show
            if total > 0:
                counts[company.name] = (total, alias_used)
        return counts

    def score_titles(self, titles: Iterable[str], timestamp: str) -> List[Dict]:
        # Aggregate counts over titles
        agg_counts: Dict[str, Tuple[int, str | None]] = {}
        for title in titles:
            counts = self._count_mentions(title)
            for name, (c, alias_used) in counts.items():
                prev = agg_counts.get(name)
                if prev:
                    agg_counts[name] = (prev[0] + c, prev[1] or alias_used)
                else:
                    agg_counts[name] = (c, alias_used)

        # Compute lift over baseline and update EMA for ALL companies (to maintain baselines)
        all_results: List[Dict] = []
        for company, _ in self.company_patterns:
            raw_recent = float(agg_counts.get(company.name, (0, None))[0])
            alias_used = agg_counts.get(company.name, (0, None))[1]
            baseline = float(self.baseline.get(company.name, 0.0))
            
            # Update smoothed recent count
            prev_recent_ema = self.recent_ema.get(company.name, raw_recent)
            # If we have no history, start with raw. Otherwise smooth it.
            # If raw is 0, we don't want to drop instantly to 0.
            smoothed_recent = (1 - self.recent_alpha) * prev_recent_ema + self.recent_alpha * raw_recent
            self.recent_ema[company.name] = smoothed_recent
            
            # Trend score: lift = (smoothed_recent + 1) / (baseline + 1)
            # Use smoothed_recent for lift calculation to prevent sharp drops
            lift = (smoothed_recent + 1.0) / (baseline + 1.0)

            # Update EMA baseline toward smoothed recent (more stable)
            new_baseline = (1 - self.alpha) * baseline + self.alpha * smoothed_recent
            self.baseline[company.name] = new_baseline

            # Add to results if it has any activity or significant lift
            # Use raw_recent > 0 check so we still see active things, but rank by smoothed lift
            if raw_recent > 0 or lift > 1.2:  # Lower threshold to capture more companies
                all_results.append(
                    {
                        "name": company.name,
                        "ticker": company.ticker,
                        "recent_count": smoothed_recent, # Return smoothed count for display consistency
                        "baseline": baseline,
                        "lift": lift,
                        "timestamp": timestamp,
                        "alias_used": None,
                    }
                )
                if alias_used:
                    # Provide a more human alias string rather than regex source
                    all_results[-1]["alias_used"] = self._clean_alias(alias_used)

        # Sort by lift then by recent counts
        all_results.sort(key=lambda r: (r["lift"], r["recent_count"]), reverse=True)
        
        # Return top 20 trending companies for a clean, focused display
        return all_results[:20]

    def serialize_state(self) -> Dict:
        return {
            "baseline": self.baseline,
            "recent_ema": self.recent_ema
        }

    def _clean_alias(self, regex_pattern: str) -> str:
        # Convert from compiled pattern text to something readable; best-effort
        if not regex_pattern:
            return ""
        
        cleaned = regex_pattern
        # Remove case-insensitive flag
        cleaned = cleaned.replace("(?i)", "")
        # Remove word boundary patterns
        cleaned = re.sub(r"\(\?\<![^)]*\)", "", cleaned)  # Remove negative lookbehinds
        cleaned = re.sub(r"\(\?\![^)]*\)", "", cleaned)   # Remove negative lookaheads
        # Remove escape characters for common chars
        cleaned = cleaned.replace("\\", "")
        # Remove dollar signs from ticker patterns
        cleaned = cleaned.strip("$")
        # If it's still too complex, return None to hide it
        if any(char in cleaned for char in ["(", ")", "[", "]", "?", "*", "+"]):
            return ""
        
        return cleaned.strip()


