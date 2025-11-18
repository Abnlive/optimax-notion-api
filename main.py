from fastapi import FastAPI
from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

notion = Client(auth=os.getenv("NOTION_API_KEY"))

# ---- BRAND ROOT PAGES (page IDs from your URLs) ----
BRAND_ROOT_PAGES = {
    "OptiMax":   "2aede0a2707080b5a961d1bb30849881",
    "VETTA":     "2aede0a2707080f28737e6e943c90a24",
    "Prosperyn": "2aede0a27070809792bcc386fec9d538",
    "Nuvora":    "2aede0a2707080599185e4f0eb15f96f",
}

# ---- CATEGORY + SUBPAGE STRUCTURE ----
CATEGORY_STRUCTURE = {
    "Brand HQ": [
        "Vision & Mission",
        "Brand Identity (Voice, Tone, Story)",
        "Market Positioning",
        "Brand Guidelines",
    ],
    "Products & Services": [
        "Core Offers",
        "Pricing Structure",
        "Service Delivery Process",
        "Product Assets",
    ],
    "Operations & Systems": [
        "Workflows",
        "SOPs",
        "Tools & Integrations",
        "KPIs & Performance",
    ],
    "Marketing & Sales": [
        "Funnels & Campaigns",
        "Content & Messaging",
        "Lead Management",
        "Ads & Tracking",
    ],
    "Client Work": [
        "Active Clients",
        "Client Onboarding",
        "Client Deliverables",
        "Case Studies",
    ],
    "Development": [
        "Websites",
        "Apps & Software",
        "Dev Environments & Credentials",
        "Tech Stack Notes",
    ],
}


# ---------- Helper functions ----------

def list_child_pages(parent_page_id: str):
    """Return a dict: {title: block} for all child_page blocks under parent."""
    results = {}
    cursor = None

    while True:
        resp = notion.blocks.children.list(
            block_id=parent_page_id,
            start_cursor=cursor
        )
        for block in resp.get("results", []):
            if block.get("type") == "child_page":
                title = block["child_page"]["title"]
                results[title] = block
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    return results


def ensure_child_page(parent_page_id: str, title: str) -> str:
    """
    Ensure a child page with this title exists under parent_page_id.
    Return the page ID.
    """

    # 1. Check for existing pages
    existing = list_child_pages(parent_page_id)
    if title in existing:
        return existing[title]["id"]

    # 2. Create page using pages.create (correct method)
    page = notion.pages.create(
        parent={"page_id": parent_page_id},
        properties={
            "title": [
                {
                    "type": "text",
                    "text": {"content": title}
                }
            ]
        }
    )

    return page["id"]


# ---------- API endpoints ----------

@app.get("/")
def root():
    return {"status": "API is running"}


@app.post("/bootstrap_brand_structure")
def bootstrap_brand_structure():
    """
    For each brand:
      - ensure the 6 category pages exist
      - under each category, ensure the correct subpages exist
    """
    summary = {}

    for brand_name, brand_page_id in BRAND_ROOT_PAGES.items():
        brand_result = {"categories": {}}

        for category_name, subpages in CATEGORY_STRUCTURE.items():
            # Create / reuse category page under the brand
            category_page_id = ensure_child_page(brand_page_id, category_name)

            # Create / reuse each subpage under the category
            created_or_found = []
            for subpage_title in subpages:
                subpage_id = ensure_child_page(category_page_id, subpage_title)
                created_or_found.append(
                    {"title": subpage_title, "id": subpage_id}
                )

            brand_result["categories"][category_name] = created_or_found

        summary[brand_name] = brand_result

    return summary
