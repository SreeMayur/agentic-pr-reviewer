import asyncio
import json
from models import PRContext
from graph import pr_reviewer_app

# 1. Create a synthetic PR diff to test our agents
MOCK_DIFF = """
diff --git a/app/database.py b/app/database.py
new file mode 100644
--- /dev/null
+++ b/app/database.py
@@ -0,0 +1,18 @@
+# Database configuration module
+
+# Global shared state
+global_db_connections = []
+
+def connect_and_process_all_records(data):
+    # Hardcoded sensitive credentials
+    DB_URL = "postgres://admin:SuperSecretP@ssword123@prod-cluster.db.internal:5432/main"
+    
+    # Connecting, parsing, and sending telemetry in a single monolithic function
+    conn = open_connection(DB_URL)
+    global_db_connections.append(conn)
+    records = conn.execute("SELECT * FROM users")
+    send_telemetry_to_cloud(records)
+    return records
+"""

async def run_local_test():
    print("🚀 Initializing mock PR payload...")
    
    # 2. Package the synthetic data into our validated Pydantic model
    mock_context = PRContext(
        pr_id=42,
        repo_name="acme-corp/core-api",
        pr_title="feat: Add database processing helper",
        diff_text=MOCK_DIFF
    )
    
    initial_state = {
        "context": mock_context,
        "comments": [],
        "retry_count": 0
    }
    
    print("⏳ Invoking LangGraph asynchronously...\n")
    
    # 3. Execute the graph
    result_state = await pr_reviewer_app.ainvoke(initial_state)
    final_review = result_state.get("final_review")
    
    # 4. Display formatted results
    print("=" * 60)
    print(f"REVIEW STATUS : {'APPROVED' if final_review.approved else 'REJECTED'}")
    print(f"SUMMARY       : {final_review.summary}")
    print("=" * 60)
    print("\nDETAILED COMMENTS:\n")
    
    for idx, comment in enumerate(final_review.comments, start=1):
        print(f"[{idx}] Category: {comment.category} | Severity: {comment.severity}")
        print(f"    File:Line : {comment.file_path}:{comment.line_number}")
        print(f"    Issue     : {comment.comment}")
        print(f"    Fix       : {comment.suggested_fix}\n")

if __name__ == "__main__":
    asyncio.run(run_local_test())