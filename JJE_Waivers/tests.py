from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model

from JJE_Waivers.models import WaiverClaim, YahooTeam
from JJE_Standings.tests import create_standing
from JJE_oauth.tests import create_user_token

import datetime


def create_test_user(username="test@test.com", password='test'):
    User = get_user_model()
    user = User.objects.create_user(username, password=password, email=username, is_active=True)
    return user


def create_test_user_login(client, username="test@test.com", user_pass='test'):
    user = create_test_user(username, user_pass)
    logged_in = client.login(
        username=username,
        password=user_pass)
    return user, logged_in


def create_test_team(team_name, user=None):
    new_team = YahooTeam()
    new_team.team_name = team_name
    if user is not None:
        new_team.user = user
    new_team.save()
    return new_team


def create_claim(add_player, drop_player, team):
    claim = WaiverClaim()
    claim.add_player = add_player
    claim.add_C = True
    claim.drop_player = drop_player
    claim.drop_C = True
    claim.team = team
    claim.save()
    return claim


class YahooTeamTest(TestCase):
    def test_new_team(self):
        team = create_test_team("Team 1")
        teams = YahooTeam.objects.all()
        self.assertCountEqual(teams, [team])


class WaiverClaimTest(TestCase):
    def test_claim_active(self):
        claim = WaiverClaim()
        self.assertIs(claim.active_claim(), True)

    def test_old_claim_inactive(self):
        claim = WaiverClaim()
        old_time = timezone.now() - datetime.timedelta(days=2)
        claim.claim_start = old_time
        self.assertIs(claim.active_claim(), False)

    def test_cancel_claim(self):
        claim = WaiverClaim()
        claim.cancelled = True
        self.assertIs(claim.active_claim(), False)

    def test_overclaim(self):
        claim = WaiverClaim()
        claim.overclaimed = True
        self.assertIs(claim.active_claim(), False)

    def test_add_position(self):
        claim = WaiverClaim()
        claim.add_C = True
        claim.add_D = True
        self.assertEqual(claim.get_position_add, 'C/D')

    def test_drop_position(self):
        claim = WaiverClaim()
        claim.drop_IR = True
        self.assertEqual(claim.get_position_drop, 'IR')

    def test_claim_end(self):
        claim = WaiverClaim()
        st = timezone.now()
        et = (st + datetime.timedelta(days=1)).isoformat()
        claim.claim_start = st
        # claim.save()
        self.assertEqual(claim.claim_end, et)


class IndexViewTest(TestCase):
    def test_index_no_claim(self):
        response = self.client.get(reverse("index"))
        self.assertQuerysetEqual(response.context['waiverclaim_list'], [])

    def test_index_one_claim(self):
        st = (timezone.now() - datetime.timedelta(hours=5))
        team = create_test_team("Test")
        claim = create_claim("Test Player Add", "Test Player Drop", team)
        response = self.client.get(reverse("index"))
        self.assertQuerysetEqual(response.context['waiverclaim_list'], ["<WaiverClaim: Test Player Add>"])

    def test_index_two_claims(self):
        team = create_test_team("Test Team")
        claim_one = create_claim("Test A P 1", "Test D P 1", team)
        claim_two = create_claim("Test A P 2", "Test D P 2", team)
        response = self.client.get(reverse("index"))
        self.assertQuerysetEqual(response.context['waiverclaim_list'],
                                 ["<WaiverClaim: Test A P 1>", "<WaiverClaim: Test A P 2>"], ordered=False)

    def test_old_and_new_claims(self):
        team = create_test_team("Test Team")
        claim_one = create_claim("Test A P 1", "Test D P 1", team)
        claim_two = create_claim("Test A P 2", "Test D P 2", team)
        claim_one.claim_start = (timezone.now() - datetime.timedelta(days=2))
        claim_one.save()
        response = self.client.get(reverse("index"))
        self.assertQuerysetEqual(response.context['waiverclaim_list'],["<WaiverClaim: Test A P 2>"], ordered=False)

    def test_anonymous_no_new_claim_button(self):
        request = self.client.get('/')
        check = False
        self.assertNotIn('<input type="submit" class="newclaim_btn" value="New Claim">', request.rendered_content)


class IndexViewLoggedInTest(TestCase):
    def test_valid_login(self):
        user = create_test_user_login(self.client)
        User = get_user_model()
        first_user = User.objects.first()
        self.assertEqual(user, (first_user, True, ))

    def test_valid_claims(self):
        user, logged_in = create_test_user_login(self.client)
        team = create_test_team("Test Team", user)
        second_team = create_test_team("second_team", user)
        claim_one = create_claim("Test A P 1", "Test D P 1", team)
        x = [user.yahooteam_set.first().waiverclaim_set.first()]
        z = [WaiverClaim.objects.filter(team=team.id).first()]
        self.assertEqual(x, z)

    def test_cancel_valid_html(self):
        user, logged_in = create_test_user_login(self.client)
        team = create_test_team("Test Team", user)
        claim_one = create_claim("Test A P 1", "Test D P 1", team)
        request = self.client.get('/')
        self.assertInHTML('<input class="cancel_btn" type="submit" value="Cancel">', request.rendered_content)

    def test_cancel_missing_from_current_user(self):
        user1 = create_test_user()
        user2, logged_in = create_test_user_login(self.client, "test1@test.com", "test")

        t1 = create_test_team("Team1", user1)
        t2 = create_test_team("Team2", user2)

        claim = create_claim("Test", "Test", t1)

        request = self.client.get("/")
        check = False
        self.assertNotIn('<input class="cancel_btn" type="submit" value="Cancel">', request.rendered_content)


    def test_oauth_registration_link_visible(self):
        user, logged_in = create_test_user_login(self.client)
        request = self.client.get('/')
        self.assertInHTML('<input type="submit" class="newclaim_btn" value="Link Yahoo">', request.rendered_content)


    def test_oauth_registration_link_hidden(self):
        user, logged_in = create_test_user_login(self.client)
        team = create_test_team("test", user)
        token = create_user_token(user)
        request = self.client.get('/')
        self.assertInHTML('<input type="submit" class="newclaim_btn" value="New Claim">', request.rendered_content)


    def test_overclaim_valid_html_no_standings(self):
        user1 = create_test_user()
        user2, logged_in = create_test_user_login(self.client, "test1@test.com", "test")

        t1 = create_test_team("Team1", user1)
        t2 = create_test_team("Team2", user2)

        claim = create_claim("Test", "Test", t1)

        request = self.client.get('/')
        self.assertInHTML('<input class="overclaim_btn" type="submit" value="Overclaim">', request.rendered_content)


class OverclaimViewTest(TestCase):
    def test_null_overclaim(self):
        """Waiver claim matching query because requesting this section for an item that doesn't exist"""
        user2, logged_in = create_test_user_login(self.client, "test1@test.com", "test")
        team = create_test_team("Test Team", user2)
        claim_one = create_claim("Test A P 1", "Test D P 1", team)
        response = self.client.get('/waiver_claim/overclaim={}'.format(10))
        self.assertEqual(response.status_code, 302)

    def test_valid_overclaim(self):
        user, logged_in = create_test_user_login(self.client)
        team = create_test_team("Test Team", user)
        claim_one = create_claim("Test A P 1", "Test D P 1", team)
        response = self.client.get('/waiver_claim/overclaim={}'.format(1))
        self.assertEqual(response.status_code, 200)

    def test_overclaim_content(self):
        user = create_test_user()
        user2, logged_in = create_test_user_login(self.client, "test1@test.com", "test")
        team = create_test_team("Test Team", user)
        team2 = create_test_team("Test Team 2", user2)
        claim_one = create_claim("Test A P 1", "Test D P 1", team)
        response = self.client.get('/waiver_claim/overclaim={}'.format(1))
        self.assertEqual(response.context['add_name'], claim_one.add_player)

    def test_overclaim_content_same_user(self):
        user = create_test_user()
        user2, logged_in = create_test_user_login(self.client, "test1@test.com", "test")
        team = create_test_team("Test Team", user)
        team2 = create_test_team("Test Team 2", user2)
        claim_one = create_claim("Test A P 1", "Test D P 1", team2)
        response = self.client.get('/waiver_claim/overclaim={}'.format(1))
        self.assertEqual(response.context['add_name'], claim_one.add_player)

    def test_overclaim_submit(self):
        user = create_test_user()
        user2, logged_in = create_test_user_login(self.client, "test1@test.com", "test")
        team = create_test_team("Test Team", user)
        team_two = create_test_team("Team Two", user2)
        claim_one = create_claim("Test A P 1", "Test D P 1", team)

        response = self.client.post('/waiver_claim/overclaim={}'.format(1),
                                    {
                                        'team': team_two.id, 'drop_player': "Drop Test"}
                                    )
        claim_two = WaiverClaim.objects.get(id=2)
        self.assertEqual(claim_two.team.id, team_two.id)

        claim_one = WaiverClaim.objects.get(id=1)
        self.assertIs(claim_one.overclaimed, True)

        self.assertEqual(claim_two.over_claim_id, claim_one.id)

    def test_logged_in_overclaim(self):
        user, logged_in = create_test_user_login(self.client, "t1@test.com", "pass")
        team = create_test_team("t1", user)

        user2, logged_in = create_test_user_login(self.client, "test1@test.com", "test")
        team2 = create_test_team("t2", user2)

        self.client.login(username="t1@test.com", password="pass")

        claim = create_claim("ap1", "dp1", team2)

        response = self.client.get("/waiver_claim/overclaim=1")
        self.assertInHTML(
            '<option value="1" selected>t1</option>',
                          response.rendered_content)


    def test_claim_by_higher_rank_team(self):
        user, logged_in = create_test_user_login(self.client, "t1@test.com", "pass")
        team = create_test_team("t1", user)
        create_standing(team, 1)

        user2 = create_test_user("t2@test.com", "pass")
        team2 = create_test_team("t2", user2)
        create_standing(team2, 3)

        claim = create_claim("ap1", "dp1", team2)

        response = self.client.get("/waiver_claim/overclaim=1")

        self.assertEqual(response.status_code, 302)


    def test_claim_by_equal_rank_team(self):
        user, logged_in = create_test_user_login(self.client, "t1@test.com", "pass")
        team = create_test_team("t1", user)
        create_standing(team, 1)

        user2 = create_test_user("t2@test.com", "pass")
        team2 = create_test_team("t2", user2)
        create_standing(team2, 1)

        claim = create_claim("ap1", "dp1", team2)

        response = self.client.get("/waiver_claim/overclaim=1")

        self.assertEqual(response.status_code, 302)


    def test_claim_by_lower_rank_team(self):
        user, logged_in = create_test_user_login(self.client, "t1@test.com", "pass")
        team = create_test_team("t1", user)
        create_standing(team, 2)

        user2 = create_test_user("t2@test.com", "pass")
        team2 = create_test_team("t2", user2)
        create_standing(team2, 1)

        claim = create_claim("ap1", "dp1", team2)

        response = self.client.get("/waiver_claim/overclaim=1")

        self.assertEqual(response.status_code, 200)

class NewClaimTest(TestCase):
    def test_null_submission_team(self):
        user, logged_in = create_test_user_login(self.client, "t1@test.com", "pass")
        team = create_test_team("t1", user)
        response = self.client.post('/waiver_claim/new/',
                                    {
                                        'add_player': "Test A",
                                        'add_C': True,
                                        'drop_player': "Test D",
                                    }, follow=True)
        self.assertEqual(response.redirect_chain, [])
#
#     def test_null_submission_add_player(self):
#         team = create_test_team("Team")
#         response = self.client.post('/waiver_claim/new/',
#                                     {
#                                         'team': team.id,
#                                         'add_player': "Test A",
#                                         'add_C': True,
#                                         # 'drop_player': "Test D",
#                                     }, follow=True)
#         self.assertEqual(response.redirect_chain, [])
#
#     def test_null_submission_drop_player(self):
#         team = create_test_team("Team")
#         response = self.client.post('/waiver_claim/new/',
#                                     {
#                                         'team': team.id,
#                                         # 'add_player': "Test A",
#                                         'add_C': True,
#                                         'drop_player': "Test D",
#                                     }, follow=True)
#         self.assertEqual(response.redirect_chain, [])


class CancelClaimTest(TestCase):
    def test_valid_cancel(self):
        user, logged_in = create_test_user_login(self.client)
        team = create_test_team("Test Team", user)
        claim_one = create_claim("Test A P 1", "Test D P 1", team)
        response = self.client.post('/waiver_claim/cancel={}'.format(claim_one.id), follow=True)
        claim_one_test = WaiverClaim.objects.get(id=1)
        self.assertIs(claim_one_test.cancelled, True)
