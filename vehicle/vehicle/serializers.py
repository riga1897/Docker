from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .models import Car, Moto, Milage
from .validators import TitleValidator



class MilageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Milage
        fields = "__all__"


class CarSerializer(serializers.ModelSerializer):
    last_milage = serializers.IntegerField(source="milage.all.first.milage", read_only=True)
    milage = MilageSerializer(many=True, read_only=True)

    class Meta:
        model = Car
        fields = "__all__"
        # fields = ("title", "description")


class MotoSerializer(serializers.ModelSerializer):
    last_milage = serializers.SerializerMethodField()

    class Meta:
        model = Moto
        fields = "__all__"
        # fields = ("title", "description")

    @staticmethod
    # def  get_last_milage(self, obj):  #  Так тоже можно
    def get_last_milage(instance):
        if instance.milage.all().first():
            return instance.milage.all().first().milage
        return 0


class MotoMilageSerializer(serializers.ModelSerializer):
    moto = MotoSerializer()

    class Meta:
        model = Milage
        fields = ("milage", "year", "moto")


class MotoCreateSerializer(serializers.ModelSerializer):
    milage = MilageSerializer(many=True, required=False)  # required=False важно!

    class Meta:
        model = Moto
        fields = "__all__"
        validators = [
            TitleValidator(field="title"),
            UniqueTogetherValidator(fields=("title", "description"), queryset=Moto.objects.all()),
        ]

    def create(self, validated_data):
        milage_data = validated_data.pop("milage", [])  # С default value!

        moto_item = Moto.objects.create(**validated_data)

        for m in milage_data:
            Milage.objects.create(**m, moto=moto_item)

        return moto_item
