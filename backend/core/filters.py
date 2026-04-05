import django_filters

from apps.candidates.models import Candidate
from apps.events.models import Event
from apps.reports.models import ReportLog


class CandidateFilter(django_filters.FilterSet):
    """Фильтры для списка кандидатов."""

    is_active = django_filters.BooleanFilter()
    hard_stop_triggered = django_filters.BooleanFilter()
    ai_attachment_type = django_filters.ChoiceFilter(
        choices=Candidate.AttachmentType.choices,
    )
    created_after = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
    )

    class Meta:
        model = Candidate
        fields = [
            "is_active",
            "hard_stop_triggered",
            "ai_attachment_type",
        ]


class EventFilter(django_filters.FilterSet):
    """Фильтры для списка событий."""

    candidate = django_filters.NumberFilter()
    is_hard_stop = django_filters.BooleanFilter()
    has_bias_warning = django_filters.BooleanFilter(
        method="filter_has_bias_warning",
    )
    created_after = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
    )

    class Meta:
        model = Event
        fields = [
            "candidate",
            "is_hard_stop",
        ]

    def filter_has_bias_warning(self, queryset, name, value):
        """Фильтрует события с предупреждением о когнитивном искажении."""
        if value:
            return queryset.exclude(bias_warning="")
        return queryset.filter(bias_warning="")


class ReportFilter(django_filters.FilterSet):
    """Фильтры для списка отчётов."""

    report_type = django_filters.ChoiceFilter(
        choices=ReportLog.ReportType.choices,
    )
    trigger = django_filters.ChoiceFilter(
        choices=ReportLog.Trigger.choices,
    )
    candidate = django_filters.NumberFilter()
    generated_after = django_filters.DateTimeFilter(
        field_name="generated_at",
        lookup_expr="gte",
    )
    generated_before = django_filters.DateTimeFilter(
        field_name="generated_at",
        lookup_expr="lte",
    )

    class Meta:
        model = ReportLog
        fields = [
            "report_type",
            "trigger",
            "candidate",
        ]
