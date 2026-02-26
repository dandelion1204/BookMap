from rest_framework import serializers
from books.models import SchoolTexbook


class SchoolListSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolTexbook
        fields = ['district', 'level', 'school']
        read_only_fields = ['district', 'level', 'school']


class SchoolDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolTexbook
        fields = '__all__'
