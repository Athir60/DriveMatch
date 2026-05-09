from django import forms
from .models import Complaint, Ticket


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['subject', 'description']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Complaint subject'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Describe the issue in detail...'
            }),
        }


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['ticket_type', 'category', 'subject', 'description', 'related_id', 'attachment']
        widgets = {
            'ticket_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ticket subject'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Describe your issue in detail...'
            }),
            'related_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Order / Contract / Booking ID (optional)'
            }),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class ContactForm(forms.Form):
    """Contact page form — not tied to a model, just stored as ticket."""
    subject = forms.ChoiceField(
        choices=[
            ('', 'Select a topic'),
            ('booking', 'Booking Issue'),
            ('payment', 'Payment Issue'),
            ('driver', 'Driver Complaint'),
            ('technical', 'Technical Issue'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    full_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your full name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your email address'})
    )
    phone = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your phone number (optional)'})
    )
    related_to = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Select an option'),
            ('booking', 'Booking'),
            ('contract', 'Contract'),
            ('payment', 'Payment'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    related_id = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ID if available'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 5,
            'placeholder': 'Please describe your issue or inquiry in detail...',
            'maxlength': '1000'
        })
    )
    attachment = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
