from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView as SimpleJWTRefreshView

from apps.accounts.models import User
from apps.accounts.serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from apps.accounts.permissions import HasPermission, IsAdmin
from apps.audit.services import log_action


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        tokens = get_tokens_for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": tokens,
            }
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class TokenRefreshView(SimpleJWTRefreshView):
    permission_classes = [AllowAny]


class UserListView(generics.ListAPIView):
    permission_classes = [HasPermission("manage_users")]
    queryset = User.objects.select_related("account__role").all()
    serializer_class = UserSerializer
    filterset_fields = ["is_active", "account__role__name"]
    search_fields = ["email", "first_name", "last_name"]


class UserDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [HasPermission("manage_users")]
    queryset = User.objects.select_related("account__role").all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return UserUpdateSerializer
        return UserSerializer

    def perform_update(self, serializer):
        user = serializer.save()
        log_action(
            user=self.request.user,
            action="change_role" if "role" in self.request.data else "update_user",
            entity_type="user",
            entity_id=str(user.identifier),
            new_values=self.request.data,
        )
