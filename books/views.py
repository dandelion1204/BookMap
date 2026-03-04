from django.http import JsonResponse
from books.models import SchoolTexbook
from books.utils import sync_excel_to_db, sync_excel_to_db_jr
from books.serializers import SchoolListSerializer, SchoolDetailSerializer
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer



# --- 新增：專門給 AJAX 呼叫的 API ---
def get_districts_api(request):
    level = request.GET.get('level', '國小')
    districts = list(SchoolTexbook.objects.filter(level__contains=level).values_list('district', flat=True).distinct())
    return JsonResponse({'districts': districts})


class SyncDatabaseAPIView(APIView):

    def post(self, request):
        results = {}

        #同步國小xlsx檔
        try:
            results['main'] = sync_excel_to_db()
        except Exception as e:
            results['main'] = f"Error: {str(e)}"

        #同步國中xlsx檔
        try:
            results['jr'] = sync_excel_to_db_jr()
        except Exception as e:
            results['jr'] = f"Error: {str(e)}"

        return Response({'message': '同步作業完成', 'detail': results})


class DistrictListAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'index.html'

    def get(self, request):
        districts = SchoolTexbook.objects.filter(level__contains='國小').values_list('district', flat=True).distinct()
        return Response({'districts': districts})


class SchoolListAPIView(generics.ListAPIView):
    serializer_class = SchoolListSerializer

    def get_queryset(self):
        queryset = SchoolTexbook.objects.all()
        district = self.request.query_params.get('district')
        if district:
            queryset = queryset.filter(district=district).values('school').distinct()
        return queryset


class SchoolDetailAPIView(generics.ListAPIView):
    serializer_class = SchoolDetailSerializer

    def get_queryset(self):
        level = self.request.GET.get('level', '國小')
        school_name = self.kwargs.get('school')
        search_query = self.request.query_params.get('search')
        print('level',level)
        print('search_query', search_query)
        print('school_name', school_name)

        if level == '國小':
            queryset = SchoolTexbook.objects.filter(level='國小')
        else:
            queryset = SchoolTexbook.objects.filter(level='國中')

        if school_name:
            return queryset.filter(school=school_name).order_by('grade_num')
        elif search_query:
            return queryset.filter(school__icontains=search_query).order_by('grade_num')

        return queryset.none()



