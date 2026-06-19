import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
    training_load_chart,
)
from .forms import (
    InjuryAssessmentForm,
    InjuryUpdateForm,
    PlayerForm,
    RotationPlanForm,
    SignUpForm,
    TrainingLoadForm,
)
from .models import Club, InjuryAssessment, InjuryRecord, Player, RotationPlan
from .models import DataSyncLog
from .services.fpl_sync import latest_sync_log


class DashboardView(TemplateView):
    template_name = "rotations/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        summary = dashboard_summary()
        context.update(summary)
        context["sync_log"] = latest_sync_log()
        context["tm_sync_log"] = DataSyncLog.objects.filter(source="transfermarkt").first()
        return context


class PlayerListView(ListView):
    model = Player
    template_name = "rotations/player_list.html"
    context_object_name = "players"
    paginate_by = 24

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
        context.update(
            {
                "risk_projection": player_risk_projection(player),
                "latest_injury": player.injury_records.order_by("-injury_date", "-pk").first(),
            }
        )
        return context


class InjuryListView(ListView):
    model = InjuryRecord
    template_name = "rotations/injury_list.html"
    context_object_name = "injuries"
    paginate_by = 15

    def get_queryset(self):
        queryset = InjuryRecord.objects.select_related("player", "player__club")
        severity = self.request.GET.get("severity")
        body_part = self.request.GET.get("body_part")
        club = self.request.GET.get("club")
        if severity:
            queryset = queryset.filter(severity=severity)
        if body_part:
            queryset = queryset.filter(body_part=body_part)
        if club:
            queryset = queryset.filter(player__club_id=club)
        return queryset.order_by("-injury_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clubs"] = Club.objects.all()
        context["severities"] = InjuryRecord.Severity.choices
        context["body_parts"] = InjuryRecord.BodyPart.choices
        context["selected"] = self.request.GET
        return context


class ClubListView(ListView):
    model = Club
    template_name = "rotations/club_list.html"
    context_object_name = "clubs"

    def get_queryset(self):
        return Club.objects.annotate(
            player_count=Count("players"),
            avg_risk=Avg("players__assessments__risk_score"),
            injury_count=Count("players__injury_records"),
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


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = SignUpForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Аккаунт создан. Войдите, чтобы добавлять игроков.")
        return redirect("login")
    return render(request, "registration/register.html", {"form": form})


@login_required
def player_create(request):
    form = PlayerForm(request.POST or None)
    if form.is_valid():
        player = form.save()
        form.create_injury_record(player)
        InjuryAssessment.objects.create(
            player=player,
            date=timezone.localdate(),
            muscle_fatigue=0,
            joint_stability=100,
            previous_injury_factor=player.career_injuries,
            recovery_score=100,
            notes="Первичная автоматическая оценка риска.",
        )
        messages.success(request, "Профиль игрока создан.")
        return redirect(player)
    return render(request, "rotations/form.html", {"form": form, "title": "Добавить игрока"})


def training_load_create(request, pk):
    player = get_object_or_404(Player, pk=pk)
    form = TrainingLoadForm(request.POST or None)
    if form.is_valid():
        training_load = form.save(commit=False)
        training_load.player = player
        training_load.save()
        messages.success(request, "Запись нагрузки сохранена.")
        return redirect(player)
    return render(
        request,
        "rotations/form.html",
        {"form": form, "title": f"Добавить нагрузку: {player.full_name}", "player": player},
    )


def injury_update(request, pk):
    player = get_object_or_404(Player, pk=pk)
    latest = player.injury_records.order_by("-injury_date", "-pk").first()
    form = InjuryUpdateForm(request.POST or None, instance=latest)
    if form.is_valid():
        form.save_for_player(player)
        InjuryAssessment.objects.create(
            player=player,
            date=timezone.localdate(),
            muscle_fatigue=0,
            joint_stability=100,
            previous_injury_factor=player.career_injuries,
            recovery_score=100,
            notes="Пересчёт риска после обновления травмы.",
        )
        messages.success(request, "Данные о травме обновлены.")
        return redirect(player)
    return render(
        request,
        "rotations/form.html",
        {"form": form, "title": f"Обновить последнюю травму: {player.full_name}", "player": player},
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
        messages.success(request, "Оценка риска рассчитана.")
        return redirect(player)
    return render(
        request,
        "rotations/form.html",
        {"form": form, "title": f"Новая оценка: {player.full_name}", "player": player},
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
                f"Прогноз риска {projection['projected_score']}%, "
                f"средняя нагрузка {projection['avg_load']}, сон {projection['avg_sleep']} ч."
            ),
        }
    )
    form = RotationPlanForm(request.POST or None, player=player, initial=initial)
    if form.is_valid():
        plan = form.save(commit=False)
        plan.player = player
        plan.save()
        messages.success(request, "План ротации создан.")
        return redirect(reverse("rotation_board"))
    return render(
        request,
        "rotations/form.html",
        {"form": form, "title": f"План ротации: {player.full_name}", "player": player},
    )
