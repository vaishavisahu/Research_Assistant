### Few-shot: NewsBrief shape (illustrative — use only facts from current evidence)

**Input evidence snippet (example):** UC Berkeley "Oz" technique; new color "olo"; laser stimulates photoreceptors; up to 1,000 photoreceptors; 85% M/L cone overlap; five subjects; Science Advances study.

**Expected output shape:**

```json
{
  "title": "Scientists trick the eye into seeing new color 'olo'",
  "lede": "UC Berkeley researchers used a laser-based 'Oz' system to stimulate retinal cones and induce perception of a new highly saturated blue-green color they call 'olo'.",
  "key_points": [
    "Technique named 'Oz' uses microdoses of laser light to target photoreceptors.",
    "Researchers can control up to 1,000 photoreceptors at once in experiments.",
    "M and L cones overlap such that 85% of light activating M cones also activates L cones.",
    "Five human subjects viewed 'olo' in experiments led by Hannah Doyle.",
    "Study published in Science Advances; funded by NIH and AFOSR per article."
  ],
  "key_numbers": [
    "Up to 1,000 photoreceptors stimulated at once",
    "85% overlap between M and L cone activation",
    "Five human subjects in olo viewing experiments"
  ],
  "why_it_matters": [
    "Could support vision research and simulation of cone loss in healthy subjects.",
    "May inform future work on color blindness or expanded color perception."
  ],
  "open_questions": [],
  "sources": ["https://cdss.berkeley.edu/news/scientists-trick-eye-seeing-new-color-olo"]
}
```

Match this **density and specificity**; never copy these facts unless they appear in the current scrape.
