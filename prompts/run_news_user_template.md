## Task

Summarize this **news / press article** (not a scientific paper):

{paper_url}

## Output requirements

- Return a **NewsBrief** (not IMRaD).
- Include **key_numbers**: every numeric fact in the evidence (counts, percentages, dates, durations).
- **sources** must include the original URL above.
- Add other URLs to sources **only if** they appear in the scrape/search evidence passed to you.

{project_context}

Follow workflow: scrape primary URL → judge → search only if weak → write_news_brief once.
