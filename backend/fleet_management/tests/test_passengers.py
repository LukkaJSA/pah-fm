from urllib.parse import urlencode

from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from fleet_management.constants import Groups
from fleet_management.factories import UserFactory


class PassengersApiTestCase(APITestCase):
    def setUp(self):
        self.url = reverse("passengers")
        self.user = UserFactory.create(
            groups=[Group.objects.get(name=Groups.Driver.name)]
        )
        self.passengers = UserFactory.create_batch(
            size=5,
            country=self.user.country,
            groups=[Group.objects.get(name=Groups.Passenger.name)],
        )

    def test_403_for_unlogged_user(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_all_passengers(self):
        self.client.force_login(self.user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.passengers), len(res.data))
        for idx, passenger in enumerate(sorted(res.data, key=lambda p: p["id"])):
            self.assertEqual(passenger["id"], self.passengers[idx].id)
            self.assertEqual(passenger["first_name"], self.passengers[idx].first_name)
            self.assertEqual(passenger["last_name"], self.passengers[idx].last_name)
            self.assertEqual(passenger["rsa_pub_e"], self.passengers[idx].rsa_pub_e)
            self.assertEqual(
                passenger["rsa_modulus_n"], self.passengers[idx].rsa_modulus_n
            )

    def test_search_passengers_by_first_name(self):
        self.client.force_login(self.user)
        searched_passenger = self.passengers[0]
        url_params = urlencode({"search": searched_passenger.first_name})
        res = self.client.get(f"{self.url}?{url_params}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        returned_ids = map(lambda p: p["id"], res.data)
        self.assertIn(searched_passenger.id, returned_ids)
        self.assertTrue(len(res.data))
