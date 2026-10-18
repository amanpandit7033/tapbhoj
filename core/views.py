from django.shortcuts import render

def index(request):
    """Phase 0 verification and health view."""
    return render(request, 'index.html')
