from django import forms

class AccountApprovalForm(forms.Form):
    account_id = forms.IntegerField(widget=forms.HiddenInput())
    action = forms.ChoiceField(choices=[('approve', 'Approve'), ('reject', 'Reject')])
    remarks = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

class TransactionReviewForm(forms.Form):
    action = forms.ChoiceField(choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('review', 'Mark for Review')
    ])
    officer_notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)