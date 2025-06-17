from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator
from .models import RepoIdea, IdeaDetail
import requests
import os
import logging
import re
from django.views.decorators.http import require_POST


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def query_groq(prompt):
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable is not set!")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1024
    }
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]



def ideas_list(request):
    idea_list = RepoIdea.objects.prefetch_related("idea_details").order_by("-created_at")
    paginator = Paginator(idea_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "ideas_app/ideas_list.html", {"page_obj": page_obj})

@require_POST
def update_feedback(request, detail_id):
    detail = get_object_or_404(IdeaDetail, id=detail_id)
    user_score = request.POST.get("user_score")
    user_feedback = request.POST.get("user_feedback")
    if user_score:
        try:
            detail.user_score = float(user_score)
        except ValueError:
            pass
    if user_feedback is not None:
        detail.user_feedback = user_feedback
    detail.save()
    return redirect("ideas_app:ideas_list")

def explore_idea(request, repo_idea_id):
    if request.method == "POST":
        snippet = request.POST.get("snippet")
        repo_idea = get_object_or_404(RepoIdea, id=repo_idea_id)
        detail = IdeaDetail.objects.filter(repo_idea=repo_idea, idea_snippet=snippet).first()
        if not detail:
            try:
                detailed = query_groq(f"""
You are an expert business strategist and technologist. For the following idea, provide a detailed analysis focusing on:

- Clear actionable steps to implement it
- Recommended tools and technologies
- Estimated effort and complexity (prioritize easy wins)
- Potential for generating revenue, especially passive revenue
- Ways this idea can enable or unlock other valuable ideas
- Why this idea deserves attention and investment

Idea:
{snippet}
""")
                score_response = query_groq(f"""
Please provide a numeric score from 0 to 10 evaluating the potential of the following idea, considering feasibility, revenue potential, and innovation.
Also include a short one-sentence explanation of the score.

Idea:
{snippet}
""")
                match = re.search(r'(\d+(\.\d+)?)', score_response)
                groq_score = float(match.group(1)) if match else None
            except requests.RequestException as e:
                logging.error(f"Groq API error: {e}")
                detailed = "Sorry, detailed analysis is currently unavailable."
                groq_score = None

            IdeaDetail.objects.create(
                repo_idea=repo_idea,
                idea_snippet=snippet,
                detailed_info=detailed,
                groq_score=groq_score
            )
        return redirect("ideas_app:ideas_list")
    else:
        return HttpResponseRedirect(reverse("ideas_app:ideas_list"))

@require_POST
def deep_dive_idea(request, detail_id):
    detail = get_object_or_404(IdeaDetail, id=detail_id)
    prompt = f"""
You are an expert strategist. Provide a detailed deep dive for this idea, including:
- Clear actionable steps to implement it
- Recommended tools/technologies
- Estimated effort and complexity (prioritize easy wins)
- Potential for generating passive revenue
- Ways this idea could enable other valuable ideas
- Why this idea deserves attention

Idea:
{detail.idea_snippet}
"""
    try:
        deep_dive_result = query_groq(prompt)
        detail.deep_dive_info = deep_dive_result
        detail.save()
    except requests.RequestException as e:
        logging.error(f"Groq API error during deep dive: {e}")
        # Optionally handle error feedback

    return redirect("ideas_app:ideas_list")