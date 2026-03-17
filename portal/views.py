from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from .models import Item, ClaimRequest


# =========================
# ROLE BASED LOGIN
# =========================
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        role = request.POST.get("role")  # 'student' or 'admin'

        # role not selected
        if not role:
            return render(request, "login.html", {"error": "Please select Student or Admin."})

        user = authenticate(request, username=username, password=password)

        # wrong credentials
        if user is None:
            return render(request, "login.html", {"error": "Invalid username or password."})

        # ADMIN ROLE
        if role == "admin":
            if user.is_superuser:
                login(request, user)
                return redirect("/admin/")
            else:
                return render(request, "login.html", {"error": "You are not authorized as Admin."})

        # STUDENT ROLE
        if role == "student":
            if user.is_superuser:
                return render(request, "login.html", {"error": "Admin account cannot login as Student."})
            login(request, user)
            return redirect("home")

        return render(request, "login.html", {"error": "Invalid role selected."})

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# =========================
# HOME PAGE (with search)
# =========================
@login_required
def home(request):
    q = request.GET.get("q", "").strip()

    items = Item.objects.all().order_by("-date_posted")

    if q:
        items = items.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(location__icontains=q) |
            Q(item_type__icontains=q)
        )

    # Get user's claims for each item
    user_claims = {}
    if request.user.is_authenticated and not request.user.is_superuser:
        claims = ClaimRequest.objects.filter(user=request.user).select_related('item')
        user_claims = {claim.item_id: claim for claim in claims}

    return render(request, "home.html", {
        "items": items,
        "q": q,
        "user_claims": user_claims
    })


# =========================
# LOST ITEMS PAGE
# =========================
@login_required
def lost_items(request):
    items = Item.objects.filter(item_type="Lost", is_claimed=False).order_by("-date_posted")
    
    # Get user's claims for each item
    user_claims = {}
    if request.user.is_authenticated and not request.user.is_superuser:
        claims = ClaimRequest.objects.filter(user=request.user).select_related('item')
        user_claims = {claim.item_id: claim for claim in claims}
    
    return render(request, "lost.html", {
        "items": items,
        "user_claims": user_claims
    })


# =========================
# FOUND ITEMS PAGE
# =========================
@login_required
def found_items(request):
    items = Item.objects.filter(item_type="Found", is_claimed=False).order_by("-date_posted")
    
    # Get user's claims for each item
    user_claims = {}
    if request.user.is_authenticated and not request.user.is_superuser:
        claims = ClaimRequest.objects.filter(user=request.user).select_related('item')
        user_claims = {claim.item_id: claim for claim in claims}
    
    return render(request, "found.html", {
        "items": items,
        "user_claims": user_claims
    })


# =========================
# ADD ITEM PAGE (Student only)
# =========================
@login_required
def add_item(request):
    # Block admin from using student add page (optional)
    if request.user.is_superuser:
        return redirect("/admin/")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        location = request.POST.get("location")
        item_type = request.POST.get("item_type")
        image = request.FILES.get("image")  # for image upload

        Item.objects.create(
            title=title,
            description=description,
            location=location,
            item_type=item_type,
            image=image
        )

        return redirect("home")

    return render(request, "add_item.html")


# =========================
# CLAIM ITEM (Student)
# =========================
@login_required
def claim_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    # Check if user already claimed this item
    existing_claim = ClaimRequest.objects.filter(item=item, user=request.user).first()
    if existing_claim:
        messages.warning(request, f"You already have a claim request for this item (Status: {existing_claim.get_status_display()})")
        return redirect("home")

    # Create a claim request instead of marking as claimed
    ClaimRequest.objects.create(
        item=item,
        user=request.user,
        message=""
    )

    messages.success(request, "Claim request sent to admin! You will be notified once it's reviewed.")
    return redirect("home")


# =========================
# MY CLAIMS (Student - View their claim requests)
# =========================
@login_required
def my_claims(request):
    # Show only student's claims
    if request.user.is_superuser:
        return redirect("/admin/")
    
    claims = ClaimRequest.objects.filter(user=request.user).order_by("-date_requested")
    
    # Count claims by status
    pending_count = claims.filter(status='pending').count()
    approved_count = claims.filter(status='approved').count()
    rejected_count = claims.filter(status='rejected').count()
    
    context = {
        'claims': claims,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    
    return render(request, "my_claims.html", context)