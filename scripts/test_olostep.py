import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from olostep import Olostep
import os

load_dotenv()

url = sys.argv[1] if len(sys.argv) > 1 else "https://arxiv.org/abs/1706.03762"
client = Olostep(api_key=os.environ["OLOSTEP_API_KEY"])
scrape = client.scrapes.create(url=url, formats=["markdown"])
print("Scraped OK for:", url)
print("Keys:", scrape.model_dump().keys() if hasattr(scrape, "model_dump") else type(scrape))