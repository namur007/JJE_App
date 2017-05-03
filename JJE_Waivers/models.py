from django.db import models
from django.utils import timezone
from django.urls import reverse
import datetime


class YahooTeam(models.Model):
    team_name = models.CharField(max_length=50)
    logo_url = models.TextField(blank=True)
    manager_name = models.CharField(max_length=200, blank=True)
    manager_email = models.EmailField(blank=True)

    def __str__(self):
        return self.team_name


class WaiverClaim(models.Model):
    team = models.ForeignKey(YahooTeam)

    claim_start = models.DateTimeField(default=timezone.now)

    add_player = models.CharField(max_length=255)

    add_LW = models.BooleanField(default=False)
    add_C = models.BooleanField(default=False)
    add_RW = models.BooleanField(default=False)
    add_D = models.BooleanField(default=False)
    add_G = models.BooleanField(default=False)
    add_Util = models.BooleanField(default=False)
    add_IR = models.BooleanField(default=False)

    drop_player = models.CharField(max_length=255)

    drop_LW = models.BooleanField(default=False)
    drop_C = models.BooleanField(default=False)
    drop_RW = models.BooleanField(default=False)
    drop_D = models.BooleanField(default=False)
    drop_G = models.BooleanField(default=False)
    drop_Util = models.BooleanField(default=False)
    drop_IR = models.BooleanField(default=False)

    over_claim_id = models.IntegerField(default=0)

    overclaimed = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)

    # this should be a relationship to the team table
    # team_id = db.Column(db.Integer, db.ForeignKey('yahoo_teams.team_id'))

    def get_absolute_url(self):
        return reverse('index')
        # return reverse('waiver-claim-detail', kwargs={'pk': self.pk})

    def active_claim(self):
        if (not self.overclaimed)\
                and (not self.cancelled)\
                and self.claim_start + datetime.timedelta(days=1) >= timezone.now():
            return True
        else:
            return False

    active_claim.admin_order_field = 'claim_start'
    active_claim.boolean = True
    active_claim.short_description = "Is Active"

    def get_position_string(self):
        out_positions_add = self.get_position_add
        out_positions_drop = self.get_position_drop

        return out_positions_add, out_positions_drop

    @property
    def get_position_add(self):
        add = {
            "LW": self.add_LW, "C": self.add_C, "RW": self.add_RW,
            "D": self.add_D, "G": self.add_G,
            "Utils": self.add_Util, "IR": self.add_IR
        }
        out_positions_add = "/".join([item for item in add if add[item] is True])
        return out_positions_add

    @property
    def get_position_drop(self):
        drop = {
            "LW": self.drop_LW, "C": self.drop_C, "RW": self.drop_RW,
            "D": self.drop_D, "G": self.drop_G,
            "Utils": self.drop_Util, "IR": self.drop_IR
        }
        out_positions_drop = "/".join([item for item in drop if drop[item] is True])
        return out_positions_drop

    @property
    def claim_end(self):
        return (self.claim_start + datetime.timedelta(days=1)).isoformat()

    def __str__(self):
        return self.add_player


