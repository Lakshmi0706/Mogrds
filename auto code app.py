#!/usr/bin/env python3
"""
company_website_finder.py

Usage:
    python company_website_finder.py input.csv output.csv

Description:
    - Reads company names from Column A (first column) of input CSV.
    - Uses DuckDuckGo search (via duckduckgo_search package) to find candidate websites.
    - Applies heuristic scoring to pick the most likely official website and a confidence score (0-1).
    - Writes output CSV with Company Name, Website (best match or "Not Found"), Confidence (0-1).

Requirements:
    pip install duckduckgo_search requests beautifulsoup4
    (Installation instructions shown below for Windows PowerShell)

Author:
    Generated with helpful heuristics and comments.
"""

import sys
import csv
import re
import time
import argparse
from urllib.parse import urlparse
from collections import Counter
import requests
from bs4 import BeautifulSoup

# External libs (must be installed)
# We'll try to support both older and newer versions of the package:
# - older: from duckduckgo_search import ddg (function)
# - newer: from duckduckgo_search import DDGS (class with methods like .text / .search)
search_func = None
try:
    # Try older, function-style API first
    from duckduckgo_search import ddg  # pip install duckduckgo_search

    def search_func(query, max_results=10):
        """Adapter for older ddg(...) function.

        Returns a list-like of result dicts compatible with the rest of the code.
        """
        return ddg(query, max_results=max_results)
except Exception:
    try:
        # Try newer DDGS class-based API
        from duckduckgo_search import DDGS

        def search_func(query, max_results=10):
            """Adapter for DDGS class: prefer a method named 'text' or 'search'.

            This returns a list of dicts similar to the older ddg function.
            """
            with DDGS() as ddgs:
                # some versions expose text, others search; try in this order
                if hasattr(ddgs, "text"):
                    return list(ddgs.text(query, max_results=max_results))
                if hasattr(ddgs, "search"):
                    return list(ddgs.search(query, max_results=max_results))
                # If none available, return empty list
                return []
    except Exception as exc:
        print("Missing required package 'duckduckgo_search' or failed to initialize search client.")
        print("Install with:")
        print("  pip install duckduckgo_search requests beautifulsoup4")
        sys.exit(1)


def duckduckgo_html_search(query, max_results=10, timeout=10):
    """
    Fallback HTML scrape of DuckDuckGo results page using requests+BeautifulSoup.
    Returns a list of dicts with keys similar to ddg results: 'href', 'title', 'body'.
    """
    url = "https://html.duckduckgo.com/html/"
    try:
        resp = requests.post(url, data={"q": query}, timeout=timeout)
        resp.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    results = []
    for a in soup.select("a.result__a"):
        href = a.get("href")
        title = a.get_text(strip=True)
        # body snippet may be in sibling
        snippet_tag = a.find_parent().select_one("a.result_snippet, .result_snippet")
        body = snippet_tag.get_text(strip=True) if snippet_tag else ""
        results.append({"href": href, "title": title, "body": body})
        if len(results) >= max_results:
            break
    # Alternative selector fallback
    if not results:
        for div in soup.select("div.result"):
            a = div.select_one("a")
            if not a:
                continue
            href = a.get("href")
            title = a.get_text(strip=True)
            body = div.get_text(strip=True)
            results.append({"href": href, "title": title, "body": body})
            if len(results) >= max_results:
                break
    return results

# ---------------------------
# Configuration / parameters
# ---------------------------

MAX_RESULTS = 10            # how many search results to evaluate per company
MIN_CONFIDENCE = 0.25      # below this, treat as "Not Found" and score 0
REQUEST_DELAY = 0.5        # seconds between searches to be polite (DuckDuckGo wrapper is lightweight)
COMMON_TLDS = (".com", ".in", ".co.in", ".org", ".net", ".io", ".biz", ".co", ".info")

# Domains considered social/aggregator (we'll treat these as low-confidence by default)
SOCIAL_DOMAINS = [
    "facebook.com", "linkedin.com", "twitter.com", "instagram.com", "youtube.com",
    "crunchbase.com", "glassdoor.com", "indeed.com", "angel.co", "pitchbook.com",
    "zoominfo.com", "yellowpages.com", "justdial.com", "tradeindia.com", "indiamart.com"
]
# Aggregators to penalize (marketplaces, directories)
AGGREGATOR_DOMAINS = [
    "alibaba.com", "amazon.in", "amazon.com", "flipkart.com", "made-in-china.com",
    "etsy.com", "tradeindia.com", "indiamart.com"
]

# Keywords in URL path that suggest authority pages on a company's site (helpful if domain matches)
PATH_KEYWORDS = [
    "about", "contact", "careers", "jobs", "investor", "investors", "press", "news", "team", "leadership"
]

# Lowercase tokens to ignore when matching company name in domain (common words)
STOP_TOKENS = set(["the", "company", "inc", "ltd", "private", "pvt", "co", "llp", "limited", "group", "corporation", "corp"])

# ---------------------------
# Utility helpers
# ---------------------------

def normalize_text(s):
    """Lowercase, strip multiple whitespace."""
    return re.sub(r"\s+", " ", (s or "").strip().lower())

def tokenize_company(name):
    """Tokenize company name into meaningful words for domain matching."""
    if not name:
        return []
    # Keep alphanumeric tokens
    tokens = re.findall(r"[A-Za-z0-9]+", name.lower())
    # Filter out stop tokens and very short tokens
    tokens = [t for t in tokens if t not in STOP_TOKENS and len(t) >= 2]
    return tokens

def get_domain_from_url(url):
    """Return normalized domain (no www) from a URL string."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove port if present
        domain = domain.split(":")[0]
        # Remove common www or m subdomains
        if domain.startswith("www."):
            domain = domain[4:]
        if domain.startswith("m."):
            domain = domain[2:]
        return domain
    except Exception:
        return ""

def contains_any(text, arr):
    """Case-insensitive substring check for any of arr inside text."""
    text = (text or "").lower()
    for a in arr:
        if a.lower() in text:
            return True
    return False

# ---------------------------
# Scoring heuristic
# ---------------------------

def score_candidate(company_name, result, rank, max_rank=MAX_RESULTS):
    """
    Compute a heuristic confidence score (0-1) for a search result representing a candidate website.

    Inputs:
        - company_name: original company name string
        - result: dict from duckduckgo_search with keys like 'href', 'title', 'body'
        - rank: 0-based index (0 = top result)
    Returns:
        (score: float in 0..1, reason: str)
    """
    href = result.get("href") or result.get("link") or ""
    title = (result.get("title") or "").lower()
    body = (result.get("body") or "").lower()
    domain = get_domain_from_url(href)
    path = urlparse(href).path.lower()

    cname = normalize_text(company_name)
    tokens = tokenize_company(company_name)
    title_l = title.lower()
    body_l = body.lower()

    # Preliminary checks
    if not href or not domain:
        return 0.0, "no-url"

    # Social or aggregator penalty / low baseline
    for soc in SOCIAL_DOMAINS:
        if soc in domain:
            # If it's social and the title/body strongly suggests official (rare), give small score; otherwise low.
            return 0.20, f"social:{soc}"

    for agg in AGGREGATOR_DOMAINS:
        if agg in domain:
            return 0.10, f"aggregator:{agg}"

    score = 0.0
    reasons = []

    # 1) Domain token matching (strong signal)
    if tokens:
        matched = sum(1 for t in tokens if t in domain)
        # proportion of tokens matched (capped)
        prop = matched / max(1, len(tokens))
        # reward proportional, up to 0.6
        add = min(0.6, 0.6 * prop)
        score += add
        reasons.append(f"token_match({matched}/{len(tokens)})+{add:.2f}")

    # 2) Title contains company name or tokens (medium signal)
    title_matches = sum(1 for t in tokens if t in title_l)
    if title_matches:
        add = 0.20 * min(1.0, title_matches / len(tokens))
        score += add
        reasons.append(f"title_matches+{add:.2f}")

    # 3) Clear 'official' phrasing in title/body
    if "official site" in title or "official website" in title or "official site" in body or "official website" in body:
        score += 0.15
        reasons.append("official-phrase+0.15")

    # 4) Path keywords boost (e.g., domain.com/about -> suggests company site)
    if contains_any(path, PATH_KEYWORDS):
        # If domain contains company tokens, this is stronger.
        if any(t in domain for t in tokens):
            score += 0.12
            reasons.append("path_keyword+0.12")
        else:
            score += 0.06
            reasons.append("path_keyword+0.06")

    # 5) Common TLD small boost
    if domain.endswith(COMMON_TLDS):
        score += 0.05
        reasons.append("common_tld+0.05")

    # 6) Rank-based slight boost (top results slightly more trustworthy)
    rank_boost = max(0.0, (max_rank - rank) / (max_rank * 10.0))  # up to ~0.1 for rank=0
    score += rank_boost
    if rank_boost > 0:
        reasons.append(f"rank_boost+{rank_boost:.3f}")

    # 7) Penalize domains that look like directories or third-party references
    if any(x in domain for x in ["wikipedia.org", "yellowpages", "yelp", "glassdoor", "crunchbase"]):
        score -= 0.20
        reasons.append("directory_penalty-0.20")

    # 8) Final normalization & clipping
    score = max(0.0, min(1.0, score))
    reason = "|".join(reasons) if reasons else "no-signals"
    return score, reason

# ---------------------------
# Search & selection
# ---------------------------

def find_best_website_for_company(
    company_name, max_results=MAX_RESULTS, verbose=False, min_confidence=MIN_CONFIDENCE, force_return_low=False
):
    """
    Query DuckDuckGo with multiple query variants and an HTML fallback. Evaluate candidate URLs
    and return the best website and confidence.

    Returns:
        (best_url_or_NotFound, confidence_float_0_to_1, details_dict)
    """
    if not company_name or not company_name.strip():
        return "Not Found", 0.0, {"reason": "empty-name"}

    queries = [
        company_name,
        f"{company_name} official website",
        f"{company_name} official site",
        f"{company_name} company",
        f"{company_name} website",
        f"{company_name} headquarters",
    ]

    seen_urls = {}
    all_results = []

    # Try multiple query variants
    for q in queries:
        try:
            res = search_func(q, max_results=max_results)
        except Exception:
            res = []

        # If wrapper returned few/no results, try HTML fallback
        if not res or len(res) < 3:
            try:
                res_html = duckduckgo_html_search(q, max_results=max_results)
                if res_html:
                    res = res + res_html
            except Exception:
                pass

        # Collect unique results preserving order
        for r in res:
            href = r.get("href") or r.get("link") or ""
            if not href:
                continue
            if href in seen_urls:
                continue
            seen_urls[href] = r
            all_results.append(r)
            if len(all_results) >= max_results:
                break
        if len(all_results) >= max_results:
            break

    if not all_results:
        return "Not Found", 0.0, {"reason": "no-results"}

    best = {"url": None, "score": 0.0, "reason": None, "domain": None, "rank": None}

    # Evaluate aggregated results
    for idx, res in enumerate(all_results):
        url = res.get("href") or res.get("link") or ""
        score, reason = score_candidate(company_name, res, idx, max_results)
        domain = get_domain_from_url(url)
        if verbose:
            print(f"    candidate #{idx+1}: {url} score={score:.3f} reason={reason}")
        if score > best["score"]:
            best.update({"url": url, "score": score, "reason": reason, "domain": domain, "rank": idx})

    if best["score"] < min_confidence and not force_return_low:
        return "Not Found", 0.0, {"reason": f"best_below_threshold ({best['score']:.2f})", "candidate": best}
    # If force_return_low is True, return the best candidate but keep its low score
    return best["url"], round(best["score"], 3), {"reason": best["reason"], "domain": best["domain"], "rank": best["rank"]}

# ---------------------------
# CSV I/O
# ---------------------------

def read_input_csv(input_csv_path):
    """
    Read CSV and return list of (original_row, company_name) tuples.

    - We preserve the original row so we can write other columns easily if needed.
    - Company name is taken from first column (index 0).
    """
    rows = []
    with open(input_csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for r in reader:
            # Treat empty rows as skip
            if not r:
                continue
            company = r[0].strip() if len(r) > 0 else ""
            rows.append((r, company))
    return rows

def write_output_csv(output_csv_path, rows_with_results, header_written=False):
    """
    rows_with_results: list of tuples (company_name, best_url_or_NotFound, confidence_float)
    Writes a CSV with columns: Company Name, Website, Confidence
    """
    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Company Name", "Website", "Confidence"])
        for company, website, confidence in rows_with_results:
            # Format confidence as decimal 0-1 (rounded) - you can change to percent if preferred
            writer.writerow([company, website, confidence])

# ---------------------------
# Main runner
# ---------------------------

def main(argv):
    parser = argparse.ArgumentParser(description="Find official company websites using DuckDuckGo searches")
    parser.add_argument("input_csv", help="Input CSV path with company names in first column")
    parser.add_argument("output_csv", help="Output CSV path")
    parser.add_argument("--max-results", type=int, default=MAX_RESULTS, help="Max results to evaluate per company")
    parser.add_argument("--min-confidence", type=float, default=MIN_CONFIDENCE, help="Minimum confidence to accept a match (0-1)")
    parser.add_argument("--verbose", action="store_true", help="Print candidate URLs and scoring reasons")
    parser.add_argument("--force-return-low", action="store_true", help="Return best candidate even if below min-confidence")
    args = parser.parse_args(argv[1:])

    input_csv = args.input_csv
    output_csv = args.output_csv

    # Read input
    print(f"Reading input file: {input_csv}")
    rows = read_input_csv(input_csv)
    print(f"Found {len(rows)} rows. Processing up to {args.max_results} aggregated search results per company...")

    results_out = []
    for i, (orig_row, company) in enumerate(rows, start=1):
        print(f"[{i}/{len(rows)}] Searching for: {company}")
        try:
            url, score, details = find_best_website_for_company(
                company,
                max_results=args.max_results,
                verbose=args.verbose,
                min_confidence=args.min_confidence,
                force_return_low=args.force_return_low,
            )
        except Exception as exc:
            url, score, details = "Not Found", 0.0, {"reason": f"exception:{exc}"}

        # Log short debug
        print(f"  -> result: {url} (score={score}) reason={details.get('reason')}")
        results_out.append((company, url, score))

        # Be polite / avoid rapid-fire requests
        time.sleep(REQUEST_DELAY)

    # Write CSV
    print(f"Writing output to: {output_csv}")
    write_output_csv(output_csv, results_out)
    print("Done.")
    return 0

if _name_ == "_main_":
    sys.exit(main(sys.argv))
