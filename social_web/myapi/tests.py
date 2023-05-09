from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from users_site.models import Profile, Friend, FriendRequest


class Base(APITestCase):
    def setUp(self) -> None:
        # User1
        self.user = get_user_model().objects.create_user(
            username="TestUser1",
            email="testuser@example.com",
            password="Password123",
        )
        self.profile = Profile.objects.create(
            user=self.user,
            username="TestUser1",
        )
        self.client.force_authenticate(user=self.user)

        # User2
        self.user2 = get_user_model().objects.create_user(
            username="TestUser2",
            email="testuser2@example.com",
            password="Password123",
        )
        self.profile2 = Profile.objects.create(
            user=self.user2, username="TestUser2"
        )

        # User3
        self.user3 = get_user_model().objects.create_user(
            username="TestUser3",
            email="testuser3@example.com",
            password="Password123",
        )
        self.profile3 = Profile.objects.create(
            user=self.user3, username="TestUser3"
        )

        # User4
        self.user4 = get_user_model().objects.create_user(
            username="TestUser4",
            email="testuser4@example.com",
            password="Password123",
        )
        self.profile4 = Profile.objects.create(
            user=self.user4, username="TestUser4"
        )

        # Friends
        self.friends = Friend.objects.create(
            user=self.profile,
            friend=self.profile2,
        )
        self.friends = Friend.objects.create(
            user=self.profile2,
            friend=self.profile,
        )

        # Request to you user 3
        self.req_to_me = FriendRequest.objects.create(
            to_user=self.profile,
            from_user=self.profile3,
        )

        # Request from you user 4
        self.req_from_me = FriendRequest.objects.create(
            to_user=self.profile4,
            from_user=self.profile,
        )


class UserRegistrationAPIView(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("registration")

    def test_post(self):
        response = self.client.post(self.url, data=dict(
            username="TestUser",
            email="testuser@example.com",
            password="Password123",
        ))
        answer = {"message": f"New User was created"}
        self.assertEquals(response.status_code, 201)
        self.assertEquals(response.data, answer)
        user_exist = User.objects.get(id=1)
        self.assertTrue(user_exist)
        profile_exist = Profile.objects.get(id=1)
        self.assertTrue(profile_exist)



class UserFriendAPITestCase(Base):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("friends_list")
        super().setUp()

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 200)
        answer = {
            "user": {"id": 1, "username": "TestUser1"},
            "friends": [{"id": 2, "username": "TestUser2"}],
        }
        self.assertEquals(response.data, answer)


class FriendDetailAPI(Base):
    def setUp(self) -> None:
        self.client = APIClient()
        super().setUp()

    def test_get_you(self):
        url = reverse("friend_detail", kwargs={"id": 1})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        answer = {"status": "It is you're id man.", "username": "TestUser1"}

        self.assertEquals(response.data, answer)

    def test_get_friend(self):
        url = reverse("friend_detail", kwargs={"id": 2})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        answer = {"status": "Already friends.", "username": "TestUser2"}

        self.assertEquals(response.data, answer)

    def test_get_in(self):
        url = reverse("friend_detail", kwargs={"id": 3})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        answer = {'status': "Incoming request.", 'username': 'TestUser3'}
        self.assertEquals(response.data, answer)

    def test_get_out(self):
        url = reverse("friend_detail", kwargs={"id": 4})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        answer = {'status': "Outgoing request.", 'username': 'TestUser4'}
        self.assertEquals(response.data, answer)

    def test_delete(self):
        url = reverse("friend_detail", kwargs={"id": 2})
        response = self.client.delete(url)
        me = Friend.objects.filter(
            user=self.profile,
            friend=self.profile2,
        )
        friend = Friend.objects.filter(
            user=self.profile2,
            friend=self.profile,
        )
        self.assertFalse(me)
        self.assertFalse(friend)
        answer = {'message': "User TestUser2 was delete from you're friends list"}
        self.assertEquals(response.status_code, 204)
        self.assertEquals(response.data, answer)


class RequestAPI(Base):
    def setUp(self) -> None:
        self.client = APIClient()
        super().setUp()
        # User5
        self.user5 = get_user_model().objects.create_user(
            username="TestUser5",
            email="testuser5@example.com",
            password="Password123",
        )
        self.profile5 = Profile.objects.create(
            user=self.user5, username="TestUser5"
        )

    def test_get(self):
        url = reverse("requests")
        response = self.client.get(url)
        answer = {
            "username": "TestUser1",
            "incoming_requests": [{"id": 3, "username": "TestUser3"}],
            "outgoing_requests": [{"id": 4, "username": "TestUser4"}],
        }
        self.assertEquals(response.data, answer)

    def test_post(self):
        url = reverse("requests")
        response = self.client.post(url, data={"to_user": self.profile5.id})
        request = FriendRequest.objects.filter(
            to_user=self.profile5,
            from_user=self.profile,
        )
        answer = {'message': 'A friend request has been sent to user TestUser5'}
        self.assertEquals(response.data, answer)
        self.assertTrue(request)
        self.assertEquals(response.status_code, 201)

    def test_post_with_incoming_request(self):
        url = reverse("requests")
        response = self.client.post(url, data={"to_user": self.profile3.id})
        answer = {'message': 'User TestUser3 add to friends'}
        self.assertEquals(response.data, answer)
        self.assertEquals(response.status_code, 201)


class RequestDetailAPIView(Base):
    def setUp(self) -> None:
        self.client = APIClient()
        super().setUp()

    def test_get(self):
        url = reverse("requests_detail", kwargs={"id": 3})
        response = self.client.get(url)
        answer = {"message": "User TestUser3 wants to add you as a friend"}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, answer)

    def test_post_accept(self):
        url = reverse("requests_detail", kwargs={"id": 3})
        response = self.client.post(url, data={"choice": "accept"})
        friend = Friend.objects.filter(user=self.profile, friend=self.profile3)
        answer = {
            "message": "You have accepted the friend request from TestUser3"
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, answer)
        self.assertTrue(friend)

    def test_post_decline(self):
        url = reverse("requests_detail", kwargs={"id": 3})
        request_from_user = FriendRequest.objects.filter(
            to_user=self.profile, from_user=self.profile3
        )
        self.assertTrue(request_from_user)
        response = self.client.post(url, data={"choice": "not_accept"})
        request_from_user = FriendRequest.objects.filter(
            to_user=self.profile, from_user=self.profile3
        )
        answer = {'message': 'You have not accepted the friend request from TestUser3'}

        self.assertFalse(request_from_user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, answer)
