from django.core.management.base import BaseCommand
from ideas_app.models import RepoIdea, IdeaDetail
import requests
import os
import time
import re

def query_groq(prompt):
    headers = {"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}", "Content-Type": "application/json"}
    data = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1024
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        headers = {"Accept": "application/vnd.github.v3+json"}
        params = {
            "q": "stars:>1000",
            "sort": "stars",
            "order": "desc",
            "per_page": 30
        }
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            self.stdout.write(self.style.WARNING("GITHUB_TOKEN is not set! You are using unauthenticated requests (low rate limits)."))
        else:
            self.stdout.write(self.style.SUCCESS("GITHUB_TOKEN is set. Using authenticated requests for higher API limits."))
            headers["Authorization"] = f"token {token}"

        response = requests.get("https://api.github.com/search/repositories", params=params, headers=headers)
        response.raise_for_status()
        trending = response.json()["items"]

        for repo in trending[:10]:
            name = repo['full_name']
            desc = repo.get('description') or ''
            summary = query_groq(f"Summarize what {name} does and its purpose:\n{desc}")

            score_response = query_groq(f"""
Please provide a numeric score from 0 to 10 evaluating the potential of this project summary, considering feasibility, revenue potential, and innovation.

Project summary:
{summary}
""")
            match = re.search(r'(\d+(\.\d+)?)', score_response)
            groq_score = float(match.group(1)) if match else None

            repo_idea = RepoIdea.objects.create(repo_name=name, summary=summary, groq_score=groq_score)

            ideas_text = query_groq(f"""
You are a world-class software visionary. Your goal is to create highly unique, practical ideas that are clearly solvable with software solutions—not vague societal problems.

Given this project summary:

{summary}

Generate 10 distinct software application ideas that:
- Adapt or extend this functionality
- Solve a specific, practical, clearly achievable problem using software
- Avoid proposing solutions to broad societal issues (e.g. climate change)

For each idea, present in a ShareTank-style gripping proposal:
- The solvable problem and why it matters
- Who faces this problem (target users)
- When and where it happens
- What the problem looks like in their daily work/life
- How this software solution fixes it in a novel, efficient way
- Why this solution deserves attention (benefits, potential impact)

Write persuasively to make the reader care about the problem and solution.

Number each idea 1-10.
""")

            # Updated splitting logic to handle **1., 1., or  1. patterns and strip extra chars
            idea_snippets = re.split(r'(?:\n|\r\n)?\s*(?:\*\*)?\d+\.\s', ideas_text.strip())
            idea_snippets = [snippet.strip('* ').strip() for snippet in idea_snippets if snippet.strip()]

            for idea in idea_snippets:
                idea_score_response = query_groq(f"""
Please provide a numeric score from 0 to 10 evaluating the potential of this idea, considering feasibility, revenue potential, and innovation. Respond only with the numeric score.

Idea:
{idea}
""")
                match_idea = re.search(r'(\d+(\.\d+)?)', idea_score_response)
                idea_score = float(match_idea.group(1)) if match_idea else None

                detail = IdeaDetail.objects.create(
                    repo_idea=repo_idea,
                    idea_snippet=idea,
                    groq_score=idea_score
                )

                # Optional: Automatically do a deep dive on each idea (or trigger manually later)
                deep_dive_response = query_groq(f"""
You are an expert strategist. Provide a detailed deep dive for this idea, including:
- Clear actionable steps to implement
- Recommended tools/technologies
- Estimated effort and complexity (prioritize easy wins)
- Potential for generating passive revenue
- Ways this idea could enable other valuable ideas
- Why this idea deserves attention

Idea:
{idea}
""")
                detail.deep_dive_info = deep_dive_response
                detail.save()

            self.stdout.write(self.style.SUCCESS(f"Saved ideas for {name} with repo score {groq_score}"))
            time.sleep(1)