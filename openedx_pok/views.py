from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from openedx_pok.models import CertificateTemplate
from opaque_keys.edx.keys import CourseKey

class CourseTemplateSettingsView(APIView):
    """
    API View for managing course template settings.
    """

    def get(self, request, course_id):
        """
        Retrieve custom settings for POK certificates of a course.
        """
        try:
            course_key = CourseKey.from_string(course_id)
            course_template = CertificateTemplate.objects.get(course__id=course_key)
            return Response({
                "course_id": str(course_template.course.id),
                "template_id": course_template.template_id,
                "created": course_template.created,
                "modified": course_template.modified,
            }, status=status.HTTP_200_OK)
        except CertificateTemplate.DoesNotExist:
            return Response({
                "course_id": course_id,
                "template_id": "",
                "created": None,
                "modified": None,
            }, status=status.HTTP_200_OK)

    def put(self, request, course_id):
        return self._create_or_update(request, course_id)

    def post(self, request, course_id):
        return self._create_or_update(request, course_id)

    def _create_or_update(self, request, course_id):
        """
        Helper method to create or update course template settings.
        """
        data = request.data
        template_id = data.get("pok_template_id")

        try:
            from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
            course_key = CourseKey.from_string(course_id)
            course = CourseOverview.objects.get(id=course_key)

            course_template, created = CertificateTemplate.objects.update_or_create(
                course=course,
                defaults={
                    "template_id": template_id,
                }
            )
            return Response({
                "message": "Settings saved successfully.",
                "created": created,
                "course_id": str(course_template.course.id),
                "template_id": course_template.template_id,
                "created_at": course_template.created,
                "modified_at": course_template.modified,
            }, status=status.HTTP_200_OK)

        except CourseOverview.DoesNotExist:
            return Response({"error": f"Course '{course_id}' not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
