from django import forms

class DepositForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))

class WithdrawalForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))

class TransferForm(forms.Form):
    recipient_account_number = forms.CharField(max_length=20)
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))