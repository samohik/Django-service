import jwt
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ViewSet, ModelViewSet

from myapi.serializers import (
    RequestSerializer,
    RegistrationSerializer,
    ProfileSerializer,
    FriendSerializer,
    RequestDetailSerializer,
    LoginSerializer,
    MessageSerializer,
)
from myapi.utils import (
    request_handler,
    add_friend,
    remove_requests,
    check_incoming,
    check_outgoing,
    remove_user_from_friends,
    remove_me_from_friends,
    check_friends, create_jwt, decode_jwt,
)
from users_site.models import Profile, Friend


class UserRegistrationViewSet(GenericViewSet):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request: Request, *args, **kwargs) -> Response:
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


class LoginViewSet(GenericViewSet):
    queryset = User.objects.all()
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        token = create_jwt(user)

        response = Response(status=status.HTTP_200_OK)
        response.set_cookie(key="jwt", value=token, httponly=True)
        response.data = {
            "message": "Login was success",
            "jwt": token,
        }

        return response


class TokenAuthenticateViewSet(ViewSet):
    permission_classes = [AllowAny, ]

    def list(self, request):
        token = request.COOKIES.get("jwt")
        try:
            data = decode_jwt(token)

            user = User.objects.get(id=data["id"])
            login(request, user)

            return Response({"message": f"User {user.username} authorize"})

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("JWT token has expired.")

        except jwt.InvalidTokenError:
            raise AuthenticationFailed(f"Invalid JWT token.Token {token}")

        except Exception as e:
            raise AuthenticationFailed(f"{e}")


class ProfileViewSet(
    ViewSet,
):
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    lookup_field = 'username'

    def get_object(self):
        lookup_value = self.kwargs[self.lookup_field]
        return self.queryset.get(**{self.lookup_field: lookup_value})

    def list(self, request, *args, **kwargs):
        try:
            user = self.queryset.get(id=request.user.id)
        except Exception as e:
            raise AuthenticationFailed("Unauthenticated")

        return Response(
            self.serializer_class(user).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['put'])
    def update_user(self, request, *args, **kwargs):
        try:
            user = self.queryset.get(id=request.user.id)
        except Exception as e:
            raise AuthenticationFailed("Unauthenticated")

        serializer = self.serializer_class(
            user,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            {"message": "Data incorrect"},
            status=status.HTTP_400_BAD_REQUEST
        )


class FriendViewSet(GenericViewSet):
    queryset = Profile.objects.all()
    serializer_class = FriendSerializer

    def list(self, request: Request, *args, **kwargs) -> Response:
        """
        View a user's list of friends.
        """
        context = {}
        try:
            user = self.queryset.get(id=request.user.id)
        except Exception as e:
            raise AuthenticationFailed("Unauthenticated")

        # My data
        context["user"] = {}
        context["user"]["id"] = user.id
        context["user"]["username"] = user.username

        data = user.user_friends.select_related(
            "user",
            "friend",
        ).all()

        # Data friends
        friends_list = [
            {"id": x.friend.id, "username": f"{x.friend}"} for x in data
        ]
        context["friends"] = friends_list

        return Response(context, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def list_message(self, request, pk, *args, **kwargs) -> Response:
        try:
            me = self.queryset.get(username=request.user)
        except Exception as e:
            raise AuthenticationFailed("Unauthenticated")

        if request.user.id == int(pk):
            return Response(
                {"message": "Hello I am you"},
                status=status.HTTP_200_OK,
            )

        message_from_me = Friend.objects.filter(
            user=request.user.id,
            friend=int(pk),
        ).first()

        data = message_from_me.message

        format_text = data.split("\n")

        return Response(
            format_text,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], serializer_class=MessageSerializer)
    def create_message(self, request, pk, *args, **kwargs) -> Response:
        try:
            me = self.queryset.get(username=request.user)
        except Exception as e:
            raise AuthenticationFailed("Unauthenticated")

        user = Profile.objects.get(user=request.user.id)
        friend = Profile.objects.get(id=int(pk))

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():

            serializer.validated_data["user"] = user
            serializer.validated_data["friend"] = friend

            data = serializer.save()
            return Response(
                {"message": f"{data}"},
                status=status.HTTP_200_OK,
            )
        return Response(
                serializer.data,
                status=status.HTTP_400_BAD_REQUEST,
            )


    def retrieve(self, request: Request, pk, *args, **kwargs) -> Response:
        """
        Get a user friend status with some other user.
        """
        context = {}

        try:
            me = self.queryset.get(username=request.user)
        except Exception as e:
            raise AuthenticationFailed("Unauthenticated")

        friend = Profile.objects.filter(id=pk).first()
        if not friend:
            return Response(
                {"message": f"User {pk} dont exist "},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if int(pk) == int(request.user.id):
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
            context["status"] = f"Nothing"
            context["username"] = str(friend)
            return Response(context, status=status.HTTP_400_BAD_REQUEST)

        return Response(context, status=status.HTTP_200_OK)

    def destroy(self, request: Request, pk):
        """Remove a user from another user from their friends."""
        context = {}
        try:
            me = self.queryset.get(id=request.user.id)
        except Exception as e:
            raise AuthenticationFailed("Unauthenticated")

        friend = self.queryset.filter(id=pk).first()

        if not friend:
            return Response(
                {"message": f"User {pk} dont exist "},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if friend.id == me.id:
            return Response(
                {"message": f"You cant delete yourself from friends"},
                status=status.HTTP_400_BAD_REQUEST,
            )

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


class RequestViewSet(GenericViewSet):
    serializer_class = RequestSerializer
    queryset = Profile.objects.all()

    def list(self, request, *args, **kwargs) -> Response:
        """
        View to the user a list of their outgoing and incoming friend requests.
        """
        context = {}
        try:
            me = self.queryset.get(id=request.user.id)
        except Exception as e:
            raise AuthenticationFailed("Unauthenticated")

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

    def create(self, request, *args, **kwargs):
        """
        If user1 sends a friend request to user2 and user2
        sends an application to user1, after which they automatically become
        friends, their applications automatically accepted.
        """
        serializer = self.serializer_class(data=request.data)
        try:
            me = self.queryset.get(username=request.user)
        except Exception as e:
            raise AuthenticationFailed("Unauthenticated")

        if serializer.is_valid():
            friend_name = serializer.validated_data["to_user"]
            friend = self.queryset.filter(username=friend_name)[0]

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

    def retrieve(self, request: Request, pk):
        """Status check with user."""
        context = {}

        try:
            me = self.queryset.get(id=request.user.id)
        except Exception as e:
            raise AuthenticationFailed("Unauthenticated")

        user = self.queryset.filter(id=pk).first()
        if not user:
            return Response(
                {"message": f"User {pk} dont exist "},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_from_me = check_incoming(me, user)
        if request_from_me:
            context["message"] = f"User {user.username} wants to add you as a friend"
        else:
            context["message"] = f"Request to friend user {user.username}"

        return Response(context)

    @action(detail=True, methods=['post'], serializer_class=RequestDetailSerializer)
    def create_friend(self, request: Request, pk) -> Response:
        """Accept or reject a user's friend request from another user."""
        try:
            me = self.queryset.get(id=request.user.id)
        except Exception as e:
            raise AuthenticationFailed("Unauthenticated")

        friend = self.queryset.filter(id=pk).first()
        if not friend:
            return Response(
                {"message": f"User {pk} dont exist "},
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif friend.id == me.id:
            return Response(
                {"message": f"You cant accept from yourself request"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RequestDetailSerializer(data=request.data)

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
