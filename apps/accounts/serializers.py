from rest_framework import serializers
from django.contrib.auth import authenticate
from apps.accounts.models import User, Account, Role, Permission


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        role = Role.objects.filter(name="viewer").first()
        if not role:
            raise serializers.ValidationError("Default viewer role not found.")

        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        Account.objects.create(user=user, role=role)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            email=attrs["email"],
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account is deactivated.")
        attrs["user"] = user
        return attrs


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["identifier", "name", "description"]


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["identifier", "codename", "name", "description"]


class RoleDetailSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = ["identifier", "name", "description", "permissions"]


class AccountSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)

    class Meta:
        model = Account
        fields = ["identifier", "role", "is_active"]


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    account = AccountSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "identifier",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "is_active",
            "is_staff",
            "date_joined",
            "account",
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    role = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "is_active", "role"]

    def update(self, instance, validated_data):
        role_name = validated_data.pop("role", None)
        if role_name is not None:
            try:
                new_role = Role.objects.get(name=role_name)
                instance.account.role = new_role
                instance.account.save(update_fields=["role"])
            except Role.DoesNotExist:
                raise serializers.ValidationError({"role": f"Role '{role_name}' not found."})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
