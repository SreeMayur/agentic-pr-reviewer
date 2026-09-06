import os
import hmac
import hashlib
import httpx
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Header
from dotenv import load_dotenv

# Import our Pydantic model and LangGraph app
from models import PRContext
from graph import pr_reviewer_app

load_dotenv()

app = FastAPI(title="Agentic PR Reviewer Webhook Receiver")
GITHUB_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def verify_signature(payload_body: bytes, signature_header: str):
    """Cryptographically verifies that the webhook genuinely came from GitHub."""
    if not signature_header:
        raise HTTPException(status_code=403, detail="x-hub-signature-256 header is missing!")
    
    # Calculate the expected signature using our secret
    hash_object = hmac.new(
        GITHUB_SECRET.encode('utf-8'), 
        msg=payload_body, 
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=403, detail="Request signatures didn't match!")

async def process_pr_review(context: PRContext):
    """The background worker that runs the LangGraph AI engine."""
    print(f"\n⚙️ Background worker started for PR #{context.pr_id}")
    
    initial_state = {
        "context": context,
        "comments": [],
        "retry_count": 0
    }
    
    # Execute the AI agents
    result_state = await pr_reviewer_app.ainvoke(initial_state)
    final_review = result_state.get("final_review")
    
    print("✅ AI Review Complete! Formatting comment for GitHub...")
    
    # 1. Format the Markdown comment
    status_icon = "✅ APPROVED" if final_review.approved else "❌ REJECTED - CRITICAL ISSUES"
    comment_body = f"### 🤖 Agentic PR Reviewer: {status_icon}\n\n"
    comment_body += f"**Summary:** {final_review.summary}\n\n"
    
    if final_review.comments:
        comment_body += "#### Detailed Findings:\n"
        for comment in final_review.comments:
            comment_body += f"- **`{comment.file_path}:{comment.line_number}`**: {comment.comment}\n"
            
    # 2. Post to GitHub using the Issues API (PRs are treated as issues for timeline comments)
    url = f"https://api.github.com/repos/{context.repo_name}/issues/{context.pr_id}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 3. Make the async HTTP request
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json={"body": comment_body})
        
        if response.status_code == 201:
            print("🚀 Successfully posted review to GitHub PR!")
        else:
            print(f"⚠️ Failed to post review. Status: {response.status_code}, Response: {response.text}")

@app.post("/webhook")
async def github_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None)
):
    """The main endpoint that GitHub hits when a PR is opened or updated."""
    payload_body = await request.body()
    
    # 1. Security Check: Verify it's actually GitHub
    verify_signature(payload_body, x_hub_signature_256)
    
    # 2. Parse the payload
    payload = await request.json()
    
    # We only care about pull requests being opened or updated
    if x_github_event == "pull_request" and payload.get("action") in ["opened", "synchronize"]:
        pr_data = payload["pull_request"]
        
        # Note: GitHub webhooks don't send the raw code diff directly in the JSON.
        # We will add a GitHub API fetch step here later. For now, we inject a mock diff
        # to ensure the LangGraph pipeline executes properly during our initial webhook tests.
        mock_diff = "diff --git a/app.py b/app.py\n+ DB_URL = 'postgres://admin:password@localhost'"
        
        context = PRContext(
            pr_id=pr_data["number"],
            repo_name=payload["repository"]["full_name"],
            pr_title=pr_data["title"],
            diff_text=mock_diff 
        )
        
        # 3. Hand off to the background task to avoid timeout
        background_tasks.add_task(process_pr_review, context)
        
        return {"message": "Webhook received. Review queued.", "status": "202 Accepted"}
        
    return {"message": f"Event '{x_github_event}' ignored."}