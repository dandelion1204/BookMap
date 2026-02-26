from django.shortcuts import render
from books.models import SchoolTexbook
from books.utils import sync_excel_to_db
from rest_framework import generics
from books.serializers import SchoolListSerializer, SchoolDetailSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer

class SyncDatabaseAPIView(APIView):

    def post(self, request):
        success = sync_excel_to_db()
        if success:
            return Response({'message': '資料庫更新成功'})
        else:
            return Response({'message': '資料已是最新，無需更新或更新失敗。'}, status=200)


class DistrictListAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'index.html'

    def get(self, request):
        districts = SchoolTexbook.objects.values_list('district', flat=True).distinct()
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
        school_name = self.kwargs.get('school')

        search_query = self.request.query_params.get('search')
        print('search_query', search_query)
        print('school_name', school_name)

        if school_name:
            return SchoolTexbook.objects.filter(school=school_name).order_by('grade_num')
        elif search_query:
            return SchoolTexbook.objects.filter(school__icontains=search_query).order_by('grade_num')

        return SchoolTexbook.objects.none()


