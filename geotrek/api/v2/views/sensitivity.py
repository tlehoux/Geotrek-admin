from __future__ import unicode_literals

from django.conf import settings
from django.db.models import F, Case, When
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from geotrek.api.v2 import serializers as api_serializers, \
    viewsets as api_viewsets
from geotrek.api.v2.functions import Transform, Buffer, GeometryType
from geotrek.sensitivity import models as sensitivity_models
from ..filters import GeotrekQueryParamsFilter, GeotrekInBBoxFilter, GeotrekSensitiveAreaFilter


class SensitiveAreaViewSet(api_viewsets.GeotrekViewset):
    filter_backends = (
        DjangoFilterBackend,
        GeotrekQueryParamsFilter,
        GeotrekInBBoxFilter,
        GeotrekSensitiveAreaFilter,
    )
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = []

    def get_serializer_class(self):
        if 'bubble' in self.request.GET:
            return api_serializers.BubbleSensitiveAreaListSerializer
        else:
            return api_serializers.SensitiveAreaListSerializer

    def get_queryset(self):
        queryset = sensitivity_models.SensitiveArea.objects.existing() \
            .filter(published=True) \
            .select_related('species', 'structure') \
            .prefetch_related('species__practices') \
            .annotate(geom_type=GeometryType(F('geom')))
        if 'bubble' in self.request.GET:
            queryset = queryset.annotate(geom2d_transformed=Transform(F('geom'), settings.API_SRID))
        else:
            queryset = queryset.annotate(geom2d_transformed=Case(
                When(geom_type='POINT', then=Transform(Buffer(F('geom'), F('species__radius'), 4), settings.API_SRID)),
                When(geom_type='POLYGON', then=Transform(F('geom'), settings.API_SRID))
            ))
        return queryset
