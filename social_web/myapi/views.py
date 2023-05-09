from django.contrib.auth.models import User
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from myapi.serializers import (
    RequestSerializer,
    RegistrationSerializer,
    RequestDetailSerializer,
    ProfileSerializer,
)
from myapi.utils import (
    request_handler,
    add_friend,
    remove_requests,
    check_incoming,
    check_outgoing,
    remove_user_from_friends,
    remove_me_from_friends,
    check_friends,
)
from users_site.models import Profile


class UserRegistrationAPIView(APIView):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Create a new user",
        request_body=RegistrationSerializer,
        responses={
            201: openapi.Response(
                description='User created successfully',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'username': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Username'
                        ),
                        'email': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Email address'
                        ),
                        'password': openapi.Schema(
                            type=openapi.FORMAT_PASSWORD,
                            description='Password'
                        ),
                    },
                ),
            ),
            400: 'Bad Request',
        },
    )
    def post(self, request: Request) -> Response:
        """Register new User."""
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():

            user = serializer.create(serializer.validated_data)

            # Create profile for the user
            profile_serializer = ProfileSerializer(data={"username": user.username})

            if profile_serializer.is_valid():
                profile_serializer.save(user=user)
            return Response({"message": f"New User was created"}, status=status.HTTP_201_CREATED)

        else:
            return Response({"message": "Not valid data"}, status=status.HTTP_400_BAD_REQUEST)


class UserFriendAPIView(APIView):
    def get_queryset(self):
        return Profile.objects.all()

    @swagger_auto_schema(
        operation_description="View a user's list of friends.",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Successful response",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "user": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "username": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                        "friends": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                    "username": openapi.Schema(type=openapi.TYPE_STRING),
                                },
                            ),
                        ),
                    },
                ),
            ),
        },
    )
    def get(self, request: Request) -> Response:
        """
        View a user's list of friends.
        """
        context = {}
        query = self.get_queryset().get(id=self.request.user.id)

        # My data
        context["user"] = {}
        context["user"]["id"] = query.id
        context["user"]["username"] = query.username

        data = query.user_friends.select_related(
            "user",
            "friend",
        ).all()

        # Data friends
        friends_list = [
            {"id": x.friend.id, "username": f"{x.friend}"} for x in data
        ]
        context["friends"] = friends_list

        return Response(context, status=status.HTTP_200_OK)


class FriendDetailAPIView(APIView):
    def get_queryset(self):
        return Profile.objects.all()

    @swagger_auto_schema(
        operation_description="Get a user friend status with some other user.",
        responses={status.HTTP_200_OK: openapi.Response(
            description="Successful response",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "username": openapi.Schema(
                        type=openapi.TYPE_STRING,
                    ),
                    "status": openapi.Schema(
                        type=openapi.TYPE_STRING,
                    ),
                },
            ),
        ),
        },
    )
    def get(self, request: Request, id, ) -> Response:
        """
        Get a user friend status with some other user.
        """
        context = {}

        me = self.get_queryset().filter(username=self.request.user)[0]
        friend = Profile.objects.get(id=id)

        if id == self.request.user.id:
            context["username"] = str(friend)
            context["status"] = "It is you're id man."

        elif check_friends(me, friend):
            context["username"] = str(friend)
            context["status"] = "Already friends."

        elif check_incoming(me, friend):
            context["status"] = "Incoming request."
            context["username"] = str(friend)

        elif check_outgoing(me, friend):
            context["status"] = "Outgoing request."
            context["username"] = str(friend)
        else:
            context["status"] = "Nothing"
            context["username"] = str(friend)
            return Response(context, status=status.HTTP_400_BAD_REQUEST)

        return Response(context, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Remove a user from another user from their friends.",
        responses={status.HTTP_200_OK: openapi.Response(
            description="Successful response",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                    ),
                },
            ),
        ),
        },
    )
    def delete(self, request: Request, id):
        """Remove a user from another user from their friends."""
        context = {}
        me = self.get_queryset().get(id=self.request.user.id)
        friend = self.get_queryset().get(id=id)

        if check_friends(me, friend):
            # Remove user from table Friend.
            remove_user_from_friends(me, friend)

            # Remove me from table Friend.
            remove_me_from_friends(me, friend)

            # Remove all requests from user and me
            remove_requests(me, friend)

            context["message"] = f"User {friend} was delete from you're friends list"
            return Response(context, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)


class RequestAPIView(APIView):
    serializer_class = RequestSerializer

    def get_queryset(self):
        return Profile.objects.all()

    @swagger_auto_schema(
        operation_description="View to the user a list of their outgoing and incoming friend requests.",
        responses={status.HTTP_200_OK: openapi.Response(
            description="Successful response",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "username": openapi.Schema(
                        type=openapi.TYPE_STRING,
                    ),
                    "incoming_requests": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                        )
                    ),
                    "outgoing_requests": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_STRING,
                        )
                    ),
                },
            ),
        ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        View to the user a list of their outgoing and incoming friend requests.
        """
        context = {}
        me = self.get_queryset().get(id=self.request.user.id)
        context["username"] = str(me.username)

        # To me
        data = me.to_user.select_related(
            "to_user",
            "from_user",
        ).filter(accepted=False)
        to_me = [
            {"id": x.from_user.id, "username": f"{x.from_user.username}"}
            for x in data
        ]
        context["incoming_requests"] = to_me

        # From me
        data = me.from_user.select_related(
            "to_user",
            "from_user",
        ).filter(accepted=False)
        from_me = [
            {"id": x.to_user.id, "username": f"{x.to_user.username}"}
            for x in data
        ]
        context["outgoing_requests"] = from_me

        return Response(context, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Sends a friend request and works out according to the situation.",
        request_body=RequestSerializer,
        responses={status.HTTP_200_OK: openapi.Response(
            description="Successful response",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                    ),
                },
            ),
        ),
        },
    )
    def post(self, request):
        """
        If user1 sends a friend request to user2 and user2
        sends an application to user1, after which they automatically become
        friends, their applications automatically accepted.
        """
        serializer = self.serializer_class(data=request.data)

        me = self.get_queryset().filter(username=self.request.user)[0]

        if serializer.is_valid():
            friend_name = serializer.validated_data["to_user"]
            friend = self.get_queryset().filter(username=friend_name)[0]

            existing_incoming_request = check_incoming(me, friend)

            if existing_incoming_request:
                # If there is already a request, then we create
                # an incoming request and automatically accept both requests
                request_handler(me, friend)

                # Add automatically to friends
                add_friend(me=me, friend=friend)
                context = {"message": f"User {friend} add to friends"}

            else:
                # If there is no request, then create a new outgoing request
                serializer.save(from_user=me)
                context = {"message": f"A friend request has been sent to user {friend}"}

            return Response(context, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"message": "Not valid data"}, status.HTTP_400_BAD_REQUEST
            )


class RequestDetailAPIView(APIView):
    serializer_class = RequestDetailSerializer

    def get_queryset(self):
        return Profile.objects.all()

    @swagger_auto_schema(
        operation_description="Status check with user.",
        responses={status.HTTP_200_OK: openapi.Response(
            description="Successful response",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                    ),
                },
            ),
        ),
        },
    )
    def get(self, request: Request, id):
        """Status check with user."""
        context = {}
        me = self.get_queryset().get(id=self.request.user.id)
        user = self.get_queryset().get(id=id)
        request_from_me = check_incoming(me, user)
        if request_from_me:
            context["message"] = f"User {user.username} wants to add you as a friend"
        else:
            context["message"] = f"Request to friend user {user.username}"

        return Response(context)

    @swagger_auto_schema(
        operation_description="Accept or reject a user's friend request from another user.",
        request_body=RequestDetailSerializer,
        responses={status.HTTP_200_OK: openapi.Response(
            description="Successful response",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                    ),
                },
            ),
        ),
        },
    )
    def post(self, request: Request, id) -> Response:
        """Accept or reject a user's friend request from another user."""
        me = self.get_queryset().get(id=self.request.user.id)
        friend = self.get_queryset().get(id=id)
        serializer = self.serializer_class(data=request.data)

        friend_request_to_me_exist = check_incoming(me, friend)
        if friend_request_to_me_exist:
            context = self.checking_friend_request_acceptance(
                me, friend, serializer
            )
            return Response(context)
        else:
            return Response({"message": "Not valid data"}, status.HTTP_400_BAD_REQUEST)

    @classmethod
    def checking_friend_request_acceptance(cls, me, friend, serializer):
        if serializer.is_valid():
            if serializer.validated_data["choice"] == "accept":

                # We create applications and accept them
                request_handler(me, friend)

                # Add to friend
                add_friend(me=me, friend=friend)

                return {
                    "message": f"You have accepted the friend request from {friend.username}"
                }
            elif serializer.validated_data["choice"] == "not_accept":
                # Remove all requests from user and me
                remove_requests(me, friend)
                return {
                    "message": f"You have not accepted the friend request from {friend.username}"
                }
