### Few-shot: orchestrator decision style (illustrative)

**Scenario A — good scrape**
- Action: scrape_url → judge score 0.92 → write_paper_summary → done
- Do NOT call search_with_scrape (wastes tokens; evidence already sufficient)

**Scenario B — thin abstract page**
- Action: scrape_url → judge score 0.65, missing "methods, results metrics"
- Action: search_with_scrape("Attention Is All You Need transformer BLEU") → judge 0.88 → write_paper_summary

**Scenario C — paywall**
- Action: scrape_url → empty/paywall → judge 0.20
- Action: search_with_scrape("paper title open access PDF") → judge → write_paper_summary (analyst notes gaps)
