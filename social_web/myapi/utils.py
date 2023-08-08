import datetime

import jwt

from users_site.models import FriendRequest, Friend


def remove_user_from_friends(me, friend):
    data = check_friends(me, friend)[0]
    data.delete()


def remove_me_from_friends(me, friend):
    data = check_friends(friend=me, me=friend)[0]
    data.delete()


def remove_requests(me, friend):
    data_to_me = check_incoming(me, friend)
    data_from_me = check_outgoing(me, friend)
    data_to_me.delete()
    data_from_me.delete()


def request_handler(me, friend):
    me_req = FriendRequest.objects.create(
        to_user=friend, from_user=me, accepted=True
    )
    friend_req = FriendRequest.objects.filter(
        to_user=me,
        from_user=friend,
    ).update(accepted=True)


def add_friend(me, friend):
    in_my_end = Friend.objects.create(
        user=me,
        friend=friend,
    )
    on_his_end = Friend.objects.create(
        user=friend,
        friend=me,
    )


def check_friends(me, friend):
    """
    Check if there is an existing friendship between the two users.
    """
    friendship = Friend.objects.filter(
        user=me,
        friend=friend,
    )
    return friendship


def check_incoming(me, friend):
    """
    Check if there is an incoming request from the user.
    """
    friendship = FriendRequest.objects.select_related(
        "to_user",
        "from_user",
    ).filter(
        to_user=me,
        from_user=friend,
        accepted=False,
    )
    return friendship


def check_outgoing(me, friend):
    """
    Check if there is an outgoing request from you.
    """
    friendship = FriendRequest.objects.select_related(
        "to_user",
        "from_user",
    ).filter(
        to_user=friend,
        from_user=me,
        accepted=False,
    )
    return friendship


def create_jwt(user):
    payload = {
        "id": user.id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
        "iat": datetime.datetime.utcnow(),
    }

    token = jwt.encode(payload, 'SECRET', algorithm="HS256")
    return token


def decode_jwt(token):
    return jwt.decode(token, 'SECRET', algorithms=["HS256", ])
