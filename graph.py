import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List
from pydantic import BaseModel, Field

# Import modern LangGraph constants for cleaner routing
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# Import the state and models
from models import PRContext, PRReviewResult, ReviewComment, ReviewCommentList

# 1. Load environment variables securely
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# 2. Initialize the LLM explicitly with the key
# We use gemini-1.5-flash for free, fast, structured outputs
# We use gemini-3.5-flash for free, fast, structured outputs
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0,
    api_key=api_key
)

def append_comments(left: List[ReviewComment], right: List[ReviewComment]) -> List[ReviewComment]:
    """Reducer to ensure parallel agents don't overwrite each other's comments."""
    return left + right

class ReviewState(TypedDict):
    """The shared state/whiteboard for the graph."""
    context: PRContext
    comments: Annotated[List[ReviewComment], append_comments]
    final_review: PRReviewResult
    retry_count: int

async def security_agent(state: dict) -> dict:
    """Scans the PR diff strictly for security vulnerabilities."""
    print("🛡️ Running Security Scan...")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an elite Application Security Engineer. Review the PR diff. Ignore styling. Only flag security vulnerabilities."),
        ("human", "Repo: {repo}\nPR Title: {title}\nDiff:\n{diff}")
    ])
    
    structured_llm = llm.with_structured_output(ReviewCommentList)
    chain = prompt | structured_llm
    
    context = state["context"]
    result = await chain.ainvoke({
        "repo": context.repo_name,
        "title": context.pr_title,
        "diff": context.diff_text
    })
    
    return {"comments": result.comments}

async def architecture_agent(state: dict) -> dict:
    """Scans the PR diff for structural issues and anti-patterns."""
    print("🏗️ Running Architecture Scan...")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Staff Software Engineer. Review the PR diff for architectural anti-patterns, performance bottlenecks, and tight coupling. Do not flag security issues."),
        ("human", "Repo: {repo}\nPR Title: {title}\nDiff:\n{diff}")
    ])
    
    structured_llm = llm.with_structured_output(ReviewCommentList)
    chain = prompt | structured_llm
    
    context = state["context"]
    result = await chain.ainvoke({
        "repo": context.repo_name,
        "title": context.pr_title,
        "diff": context.diff_text
    })
    
    return {"comments": result.comments}

async def synthesizer_agent(state: dict) -> dict:
    """Reads all comments from parallel agents and makes the final decision."""
    print("🧠 Synthesizing Final Review...")
    
    comments = state.get("comments", [])
    
    has_critical = any(c.severity == "Critical" for c in comments)
    is_approved = not has_critical
    
    summary = f"Review complete. Found {len(comments)} issues."
    if has_critical:
        summary += " CRITICAL ISSUES FOUND. Do not merge."
        
    final_result = PRReviewResult(
        approved=is_approved,
        summary=summary,
        comments=comments
    )
    
    return {"final_review": final_result}

# 3. Build the parallel workflow graph
workflow = StateGraph(ReviewState)

workflow.add_node("security", security_agent)
workflow.add_node("architecture", architecture_agent)
workflow.add_node("synthesizer", synthesizer_agent)

# 4. Modern parallel routing using START
workflow.add_edge(START, "security")
workflow.add_edge(START, "architecture")

# Both branches converge on the synthesizer
workflow.add_edge("security", "synthesizer")
workflow.add_edge("architecture", "synthesizer")
workflow.add_edge("synthesizer", END)

# 5. Compile the executable application
pr_reviewer_app = workflow.compile()