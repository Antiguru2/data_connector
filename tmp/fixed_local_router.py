from rest_framework import routers

from . import views
from . import api


router = routers.DefaultRouter()


try:
    from . import local_api
    router.register(r'search_rows', local_api.SearchRowModelViewSet)
    router.register(r'search_criteria', local_api.SearchCriteriaModelViewSet)
    router.register(r'projects', local_api.ProjectsModelViewSet)
    router.register(r'candidates', local_api.CandidateModelViewSet)
    router.register(r'analysis_statistics', local_api.AnalysisStatisticsModelViewSet)
    router.register(r'prompts', local_api.PromptsModelViewSet)
    router.register(r'project_meta_data', local_api.ProjectMetaDataModelViewSet)
    router.register(r'hh_areas', local_api.HHAreaModelViewSet)
    router.register(r'ai_tasks', local_api.AITaskModelViewSet)

except ImportError:
    pass
