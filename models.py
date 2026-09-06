from pydantic import BaseModel, Field
from typing import List, Literal

class PRContext(BaseModel):
    """The payload we extract from the GitHub Webhook to feed the graph."""
    pr_id: int
    repo_name: str
    diff_text: str
    pr_title: str

class ReviewComment(BaseModel):
    """A single actionable review comment."""
    file_path: str = Field(..., description="The exact file path of the issue.")
    line_number: int = Field(..., description="The exact line number where the issue occurs.")
    category: Literal["Security", "Architecture", "Style", "Bug"] = Field(..., description="The type of issue.")
    severity: Literal["Critical", "Medium", "Low"] = Field(..., description="How severe the issue is.")
    comment: str = Field(..., description="A concise, actionable explanation of the problem.")
    suggested_fix: str = Field(..., description="A code snippet showing how to fix it.")

class PRReviewResult(BaseModel):
    """The final payload produced by the AI agents."""
    approved: bool = Field(..., description="False if there are Critical severity issues, True otherwise.")
    summary: str = Field(..., description="A 2-sentence summary of the review.")
    comments: List[ReviewComment] = Field(default_factory=list)

class ReviewCommentList(BaseModel):
    """Wrapper to force the LLM to return a list of comments."""
    comments: List[ReviewComment] = Field(default_factory=list)