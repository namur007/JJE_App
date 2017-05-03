from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from django.urls import reverse

from JJE_Waivers.models import WaiverClaim

from django.utils import timezone
from datetime import timedelta


class IndexView(ListView):
    template_name = "JJE_Waivers/waivers_index.html"

    def get_queryset(self):
        now = timezone.now() - timedelta(days=1)
        claims = WaiverClaim.objects.filter(cancelled=False).filter(overclaimed=False).filter(claim_start__gt=now)
        return claims


class WaiverClaimCreate(CreateView):
    model = WaiverClaim
    template_name_suffix = "_new"
    fields = [
        "team",
        "add_player", "add_LW", "add_C", "add_RW", "add_D", "add_G", "add_Util", "add_IR",
        "drop_player", "drop_LW", "drop_C", "drop_RW", "drop_D", "drop_G", "drop_Util", "drop_IR"
    ]
    
    def form_valid(self, form):
        return super(WaiverClaimCreate, self).form_valid(form)


class OverclaimCreate(CreateView):
    model = WaiverClaim
    template_name_suffix = "_overclaim"
    fields = [
        "team",
        "drop_player", "drop_LW", "drop_C", "drop_RW", "drop_D", "drop_G", "drop_Util", "drop_IR"
    ]

    def get(self, request, *args, **kwargs):
        try:
            wc_id = self.kwargs.get("waiver_claim_id")
            player = WaiverClaim.objects.get(id=wc_id)
            assert player.active_claim()
            return super(OverclaimCreate, self).get(request, *args, **kwargs)
        except Exception as e:
            return redirect(reverse("index"))

    def get_context_data(self, **kwargs):
        context = super(OverclaimCreate, self).get_context_data(**kwargs)
        wc_id = self.kwargs.get("waiver_claim_id")
        player = WaiverClaim.objects.get(id=wc_id)

        context["add_name"] = player.add_player
        context["add_pos"] = player.get_position_add
        return context

    def form_valid(self, form):
        wc_id = self.kwargs.get("waiver_claim_id")
        player = WaiverClaim.objects.get(id=wc_id)
        player.overclaimed = True
        player.save()

        form.instance.claim_start = player.claim_start
        form.instance.add_player = player.add_player
        form.instance.add_LW = player.add_LW
        form.instance.add_C = player.add_C
        form.instance.add_RW = player.add_RW
        form.instance.add_D = player.add_D
        form.instance.add_G = player.add_G
        form.instance.add_Util = player.add_Util
        form.instance.add_IR = player.add_IR
        form.instance.over_claim_id = int(wc_id)

        return super(OverclaimCreate, self).form_valid(form)


class CancelClaimView(DetailView):
    template_name = 'JJE_Waivers/waiverclaim_cancel.html'
    model = WaiverClaim

    def post(self, request, *args, **kwargs):
        claim_id = kwargs.get("pk")
        claim = get_object_or_404(WaiverClaim, id=claim_id)
        claim.cancelled = True
        claim.save()

        return redirect(reverse('index'))
