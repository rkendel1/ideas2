from django.db import models

class RepoIdea(models.Model):
    repo_name = models.CharField(max_length=200)
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # New fields for scoring and feedback
    groq_score = models.FloatField(null=True, blank=True, help_text="Score or ranking from Groq LLM evaluation")
    user_score = models.FloatField(null=True, blank=True, help_text="User assigned score or rating")
    user_feedback = models.TextField(null=True, blank=True, help_text="User feedback or comments")

    def __str__(self):
        return f"{self.repo_name} (Score: {self.user_score or 'N/A'})"

class IdeaDetail(models.Model):
    repo_idea      = models.ForeignKey(RepoIdea, on_delete=models.CASCADE, related_name="idea_details")
    idea_snippet   = models.TextField()
    detailed_info  = models.TextField(blank=True)
    deep_dive_info = models.TextField(blank=True, help_text="Deeper analysis or exploration of the idea")
    created_at     = models.DateTimeField(auto_now_add=True)
    groq_score     = models.FloatField(null=True, blank=True)
    user_score     = models.FloatField(null=True, blank=True)
    user_feedback  = models.TextField(null=True, blank=True)

    def __str__(self):
        snippet_preview = (self.idea_snippet[:50] + '...') if len(self.idea_snippet) > 50 else self.idea_snippet
        return f"IdeaDetail for {self.repo_idea.repo_name}: {snippet_preview} (Score: {self.user_score or 'N/A'})"