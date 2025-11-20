"""
OptiMax Workspace Management API  (Blueprint / Safe Template)
--------------------------------------------------------------
This file illustrates the full structure of your management API.

- Rebuilds OptiMax Hub (Command Center + Brands)
- Timestamped activity logging
- Permission system using AGENT_AUTH_KEY
- Safe markers (# TODO enable) where real Notion write actions go
"""

from fastapi import FastAPI, Request
from notion_client import Client
from dotenv import load_dotenv
import os, datetime

# --------------------------------------------------
# Load environment and init
# --------------------------------------------------
load_dotenv()
app = FastAPI()

notion = Client(auth=os.getenv("NOTION_API_KEY"))
MAIN_PAGE_ID = os.getenv("MAIN_PAGE_ID") or "2aede0a2707080cbb154cafd88390564"
AGENT_AUTH_KEY = os.getenv("AGENT_AUTH_KEY")

# --------------------------------------------------
# Core data structures
# --------------------------------------------------
BRAND_CATEGORY_STRUCTURE = {
    "Brand HQ": ["Vision & Mission","Brand Identity","Market Positioning","Brand Guidelines"],
    "Products & Services": ["Core Offers","Pricing Structure","Service Delivery Process","Product Assets"],
    "Operations & Systems": ["Workflows","SOPs","Tools & Integrations","KPIs & Performance"],
    "Marketing & Sales": ["Funnels & Campaigns","Content & Messaging","Lead Management","Ads & Tracking"],
    "Client Work": ["Active Clients","Client Onboarding","Client Deliverables","Case Studies"],
    "Development": ["Websites","Apps & Software","Dev Environments & Credentials","Tech Stack Notes"],
}

COMMAND_CENTER_STRUCTURE = {
    "Planner (Task System & Execution Engine)": {
        "Task Management": ["Current Tasks","Urgent / Important Matrix","Today’s Priorities",
                             "Active Projects List","Blocked Items","Delegated / Agent Tasks"],
        "Weekly Planning": ["Weekly Objectives","Weekly Breakdown","Wins & Lessons","Review & Adjust"],
        "Monthly / Quarterly Planning": ["Monthly Goals","Quarterly Roadmap","OKRs / Key Targets",
                                         "Brand-Level Initiatives"],
        "Life & Business Planning": ["1-Year Vision","12-Week Year Plan","Long-Term Vision & Identity",
                                     "Personal Development Map"],
    },
    "Knowledge Base (Static Long-Term Memory)": {
        "Global Knowledge": ["Big Picture Strategy","System Architecture","Brand Ecosystem Map","Roles & Agent Definitions"],
        "AI & Automation Knowledge": ["Agent Structure","API Documentation","Workflows & Routes","System Prompts (Archived Versions)"],
        "Personal Knowledge": ["Your Story / Background","Personality Notes","ADHD Support Preferences",
                               "Work Style Notes","Rules for How Agents Should Work With You"],
        "Policies & Standards": ["Naming Standards","Folder Structure Rules","Brand Consistency Rules","Documentation SOPs"],
        "Reference Library": ["Glossary of Terms","Templates Library","Frameworks & Models","Resources & Links"],
    },
    "Activity Log (System Memory / Historical Trace)": {
        "Daily Log": ["Time-Stamped Entries","Agent Actions","System Updates","Completed Tasks"],
        "Weekly Summary": ["Accomplishments","Problems Solved","Bottlenecks Identified","Next Steps"],
        "Monthly Summary": ["Key Metrics","Progress Toward Goals","Strategic Notes"],
        "Agent Logs": [],
        "Human Logs": [],
        "Archive": [],
    },
}

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def verify_permission(key:str):
    if key != AGENT_AUTH_KEY:
        raise PermissionError("Invalid AGENT_AUTH_KEY.")

def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def list_child_pages(parent_id:str):
    results, cursor = {}, None
    resp = notion.blocks.children.list(block_id=parent_id, start_cursor=cursor)
    for b in resp.get("results", []):
        if b.get("type") == "child_page":
            results[b["child_page"]["title"]] = b
    return results

def ensure_child_page(parent_id, title):
    existing = list_child_pages(parent_id)
    if title in existing:
        return existing[title]["id"]
    # enable create page
    page = notion.pages.create(parent={"page_id": parent_id},
                               properties={"title":[{"type":"text","text":{"content":title}}]})
    return page["id"]

def resolve_page_id(identifier):
    if not identifier:
        raise ValueError("No page identifier provided")
    if len(identifier.replace("-","")) == 32:
        return identifier
    pages = list_child_pages(MAIN_PAGE_ID)
    for t, b in pages.items():
        if identifier.lower() in t.lower():
            return b["id"]
    raise ValueError("Page not found")

def log_action(action, target, result="ok"):
    """Record to Activity Log → Agent Logs"""
    stamp = timestamp()
    entry = f"[{stamp}] {action} → {target}: {result}"
    # enable append to Agent Logs
    print("LOG:", entry)

# --------------------------------------------------
# ROUTES
# --------------------------------------------------
@app.get("/")
def health(): return {"status":"OptiMax API ready"}

@app.post("/bootstrap_workspace")
async def bootstrap(request:Request):
    """
    Rebuild the OptiMax workspace.
    Body: {"auth_key":"PIN","reset":true}
    """
    body=await request.json()
    reset=body.get("reset",False)
    try:
        verify_permission(body.get("auth_key"))
    except PermissionError as e:
        return {"error":str(e)}

    if reset:
        log_action("RESET", "Workspace", "initiated")
        children = list_child_pages(MAIN_PAGE_ID)
        for title, block in children.items():
            if title not in ["OptiMax Hub", "Command Center", "Activity Log"]:
                try:
                    notion.blocks.delete(block_id=block["id"])
                    log_action("DELETE", title, "removed")
                except Exception as e:
                    log_action("DELETE_FAILED", title, str(e))



    # Build Command Center
    cc_id=ensure_child_page(MAIN_PAGE_ID,"Command Center")
    for sec,subs in COMMAND_CENTER_STRUCTURE.items():
        sec_id=ensure_child_page(cc_id,sec)
        for cat,children in subs.items():
            cat_id=ensure_child_page(sec_id,cat)
            for ch in children:
                ensure_child_page(cat_id,ch)
    # Build Brand Pages
    for brand in ["OptiMax","VETTA","Prosperyn","Nuvora"]:
        b_id=ensure_child_page(MAIN_PAGE_ID,brand)
        for cat,subs in BRAND_CATEGORY_STRUCTURE.items():
            c_id=ensure_child_page(b_id,cat)
            for s in subs: ensure_child_page(c_id,s)
    log_action("BOOTSTRAP","Workspace","complete")
    return {"status":"structure built (simulation)"}

@app.post("/append_to_page")
async def append_to_page(request:Request):
    """Append text block (requires auth)"""
    body=await request.json()
    try:
        verify_permission(body.get("auth_key"))
        pid = body.get("page_id")
        txt = body.get("text", "")

        notion.blocks.children.append(
            block_id=pid,
            children=[{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": txt}}]
                }
            }]
        )

        log_action("append", pid)
        return {"status": "success", "action": "append", "page": pid}
    except Exception as e:
        return {"error":str(e)}

@app.patch("/update_page_title")
async def update_page_title(request:Request):
    """Rename a page"""
    body=await request.json()
    try:
        verify_permission(body.get("auth_key"))
        pid=resolve_page_id(body.get("page_id"))
        new=body.get("new_title")
        notion.pages.update(
            page_id=pid,
            properties={
                "title": [{"type": "text", "text": {"content": new}}]
            }
        )
        return {"status":"renamed", "page": pid}
    except Exception as e:
        return {"error":str(e)}
@app.delete("/delete_block")
async def delete_block(request:Request):
    """Delete a page/block"""
    b=await request.json()
    try:
        verify_permission(b.get("auth_key"))
        pid=resolve_page_id(b.get("page_id"))
        notion.blocks.delete(block_id=pid)
        return {"status":"deleted", "page": pid}
    except Exception as e:
        return {"error":str(e)}

@app.post("/archive_page")
async def archive_page(request:Request):
    """Move page to Activity Log → Archive"""
    b=await request.json()
    try:
        # Make sure the Archive page exists
        activity_log_id = ensure_child_page(MAIN_PAGE_ID, "Activity Log")
        archive_id = ensure_child_page(activity_log_id, "Archive")

        # Move (duplicate and delete original)
        notion.blocks.children.append(
            block_id=archive_id,
            children=[{
                "object": "block",
                "type": "child_page",
                "child_page": {"title": f"Archived - {b.get('page_id')}"}
            }]
        )

        # Optionally delete the old page
        # notion.blocks.delete(block_id=pid)

    except Exception as e:
        return {"error":str(e)}

@app.post("/log_action")
async def manual_log(request:Request):
    """Manually log an event"""
    d=await request.json()
    log_action(d.get("action"), d.get("target"))
    return {"status":"logged (simulated)"}

@app.get("/get_recent_activity")
def get_recent_activity(limit:int=10):
    """Return last N log entries (placeholder)"""
    return {"recent":[f"Example log {i}" for i in range(limit)]}

@app.post("/summarize_activity")
def summarize_activity():
    """Placeholder summarization endpoint"""
    return {"summary":"(AI summary placeholder)"}

@app.post("/create_template")
async def create_template(request:Request):
    """Create a planner/summary template (requires auth)"""
    d=await request.json()
    try:
        verify_permission(d.get("auth_key"))
        ttype=d.get("template_type")
        notion.pages.create(
    parent={"page_id": MAIN_PAGE_ID},
    properties={
        "title": [{"type": "text", "text": {"content": f"{ttype} Template"}}]
    }
)
        return {"status":"template created"}
    except Exception as e: return {"error":str(e)}
