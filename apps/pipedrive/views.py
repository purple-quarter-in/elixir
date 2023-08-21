from django.shortcuts import render

from pipedrive.models import ContactLead
from pipedrive.serializer import ContactLeadSerializer
from elixir.utils import custom_send_email, custom_success_response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet

def say_hello(request):
    return render(request=request, template_name="email/contact.html")
# Create your views here.
class ContactLeadViewSet(ModelViewSet):
    queryset = ContactLead.objects.all()
    serializer_class = ContactLeadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        custom_send_email("info@purplequarter.com",[serializer.validated_data['company_email']],"We are happy to hear from you!",[],["abhinav.pandey@purplequarter.com","anmol.goel@purplequarter.com"],
                          serializer.data,"email/contact.html")
        return custom_success_response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk):
        lead = self.get_object()
        serializer = self.serializer_class(lead, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return custom_success_response(serializer.data, status=status.HTTP_200_OK)
