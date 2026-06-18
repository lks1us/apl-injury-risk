import json

from django.contrib import messages
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView

from .analytics import (
    assessment_trend,
    dashboard_summary,
    filtered_players,
    player_risk_projection,
)
from .forms import InjuryAssessmentForm, PlayerForm, RotationPlanForm, TrainingLoadForm
from .models import Club, InjuryAssessment, Player, RotationPlan


class DashboardView(TemplateView):
    template_name = "rotations/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        summary = dashboard_summary()
        context.update(summary)
        context["risk_distribution_json"] = json.dumps(
            [
                summary["risk_distribution"].get("low", 0),
                summary["risk_distribution"].get("medium", 0),
                summary["risk_distribution"].get("high", 0),
            ]
        )
        context["club_labels_json"] = json.dumps(summary["club_labels"])
        context["club_risks_json"] = json.dumps(summary["club_risks"])
        return context


class PlayerListView(ListView):
    model = Player
    template_name = "rotations/player_list.html"
    context_object_name = "players"
    paginate_by = 12

    def get_queryset(self):
        return filtered_players(self.request.GET)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clubs"] = Club.objects.all()
        context["positions"] = Player.Position.choices
        context["selected"] = self.request.GET
        return context


class PlayerDetailView(DetailView):
    model = Player
    template_name = "rotations/player_detail.html"
    context_object_name = "player"

    def get_queryset(self):
        return Player.objects.select_related("club")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        player = self.object
        risk_projection = player_risk_projection(player)
        trend = assessment_trend(player)
        context.update(
            {
                "risk_projection": risk_projection,
                "latest_assessment": player.latest_assessment,
                "trend_json": json.dumps(trend),
                "assessments": player.assessments.all()[:8],
            }
        )
        return context


class ClubListView(ListView):
    model = Club
    template_name = "rotations/club_list.html"
    context_object_name = "clubs"

    def get_queryset(self):
        return Club.objects.annotate(
            player_count=Count("players"),
            avg_risk=Avg("players__assessments__risk_score"),
        ).order_by("name")


class RotationBoardView(ListView):
    model = RotationPlan
    template_name = "rotations/rotation_board.html"
    context_object_name = "rotation_plans"
    paginate_by = 15

    def get_queryset(self):
        queryset = RotationPlan.objects.select_related("player", "player__club", "assessment")
        recommendation = self.request.GET.get("recommendation")
        if recommendation:
            queryset = queryset.filter(recommendation=recommendation)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recommendations"] = RotationPlan.Recommendation.choices
        context["selected_recommendation"] = self.request.GET.get("recommendation", "")
        return context


def player_create(request):
    form = PlayerForm(request.POST or None)
    if form.is_valid():
        player = form.save()
        InjuryAssessment.objects.create(
            player=player,
            date=timezone.localdate(),
            muscle_fatigue=0,
            joint_stability=100,
            previous_injury_factor=player.career_injuries,
            recovery_score=100,
            notes="Initial automatic risk assessment.",
        )
        messages.success(request, "Player profile has been created.")
        return redirect(player)
    return render(request, "rotations/form.html", {"form": form, "title": "Add player"})


def training_load_create(request, pk):
    player = get_object_or_404(Player, pk=pk)
    form = TrainingLoadForm(request.POST or None)
    if form.is_valid():
        training_load = form.save(commit=False)
        training_load.player = player
        training_load.save()
        messages.success(request, "Training load has been saved.")
        return redirect(player)
    return render(
        request,
        "rotations/form.html",
        {"form": form, "title": f"Add load: {player.full_name}", "player": player},
    )


def assessment_create(request, pk):
    player = get_object_or_404(Player, pk=pk)
    form = InjuryAssessmentForm(request.POST or None)
    if form.is_valid():
        assessment = form.save(commit=False)
        assessment.player = player
        assessment.muscle_fatigue = 0
        assessment.joint_stability = 100
        assessment.previous_injury_factor = player.career_injuries
        assessment.recovery_score = 100
        assessment.save()
        messages.success(request, "Risk assessment has been calculated.")
        return redirect(player)
    return render(
        request,
        "rotations/form.html",
        {"form": form, "title": f"Add assessment: {player.full_name}", "player": player},
    )


def rotation_plan_create(request, pk):
    player = get_object_or_404(Player, pk=pk)
    initial = {}
    projection = player_risk_projection(player)
    latest_assessment = player.latest_assessment
    if latest_assessment:
        initial["assessment"] = latest_assessment
    initial.update(
        {
            "planned_minutes": projection["planned_minutes"],
            "recommendation": projection["recommendation"],
            "rationale": (
                f"Projected risk {projection['projected_score']}%, "
                f"average load {projection['avg_load']}, sleep {projection['avg_sleep']}h."
            ),
        }
    )
    form = RotationPlanForm(request.POST or None, player=player, initial=initial)
    if form.is_valid():
        plan = form.save(commit=False)
        plan.player = player
        plan.save()
        messages.success(request, "Rotation plan has been created.")
        return redirect(reverse("rotation_board"))
    return render(
        request,
        "rotations/form.html",
        {"form": form, "title": f"Plan rotation: {player.full_name}", "player": player},
    )
