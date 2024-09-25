import tempfile
import os
from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from theatre.models import Play, Actor, Genre, TheatreHall, Performance
from theatre.serializers import PlayListSerializer, PlayRetrieveSerializer

THEATRE_URL = reverse("theatre:play-list")
THEATRE_SESSION_URL = reverse("theatre:performance-list")


def sample_play(**params):
    defaults = {
        "title": "Sample play",
        "description": "Sample description",
    }
    defaults.update(params)
    actors = params.pop("actors", None)
    genres = params.pop("genres", None)
    play = Play.objects.create(**defaults)
    if actors:
        play.actors.set(actors)
    if genres:
        play.genres.set(genres)

    return play


def sample_play_session(**params):
    theatre_hall = TheatreHall.objects.create(name="Blue", rows=20, seats_in_row=20)

    defaults = {
        "show_time": "2022-06-02 14:00:00",
        "play": None,
        "theatre_hall": theatre_hall,
    }
    defaults.update(params)

    return Performance.objects.create(**defaults)


def image_upload_url(play_id):
    """Return URL for recipe image upload"""
    return reverse("theatre:play-upload-image", args=[play_id])


def detail_url(play_id):
    return reverse("theatre:play-detail", args=(play_id,))


class UnauthenticatedTheatreApiTests(TestCase):
    def setUp(self):
        """Initializes a test client to execute requests to the API"""
        self.client = APIClient()

    def test_auth_required(self):
        """Checks that API access requires authentication"""
        res = self.client.get(THEATRE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTheatreApiTests(TestCase):
    def setUp(self):
        """Configures the environment for tests with an authenticated user"""
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_plays(self):
        """Tests that the API correctly returns the list of  plays"""
        sample_play()
        play_actor_genre = sample_play()
        actors = Actor.objects.create(first_name="first_test", last_name="last_test")

        genres = Genre.objects.create(name="test")
        play_actor_genre.actors.add(actors)
        play_actor_genre.genres.add(genres)

        res = self.client.get(THEATRE_URL)

        plays = Play.objects.all()
        serializer = PlayListSerializer(plays, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_plays_by_genres_actors_title(self):
        """Tests filtering of plays by genre, actor and title"""
        play1 = sample_play(title="Play 1")
        play2 = sample_play(title="Play 2")
        play3 = sample_play()

        genre1 = Genre.objects.create(name="Genre 1")
        genre2 = Genre.objects.create(name="Genre 2")
        actor1 = Actor.objects.create(first_name="Actor 1", last_name="Actor 1")
        actor2 = Actor.objects.create(first_name="Actor 2", last_name="Actor 2")
        play1.actors.add(actor1)
        play2.actors.add(actor2)
        play1.genres.add(genre1)
        play2.genres.add(genre2)

        res_genres = self.client.get(
            THEATRE_URL, {"genres": f"{genre1.id},{genre2.id}"}
        )
        res_actor = self.client.get(THEATRE_URL, {"actors": f"{actor1.id},{actor2.id}"})
        res_title = self.client.get(THEATRE_URL, {"title": "Play 1"})
        serializer1 = PlayListSerializer(play1)
        serializer2 = PlayListSerializer(play2)
        serializer3 = PlayListSerializer(play3)

        results_genres = [dict(play) for play in res_genres.data["results"]]
        results_actor = [dict(play) for play in res_actor.data["results"]]
        results_title = [dict(play) for play in res_title.data["results"]]

        self.assertIn(dict(serializer1.data), results_genres)
        self.assertIn(dict(serializer2.data), results_genres)
        self.assertNotIn(dict(serializer3.data), results_genres)

        self.assertIn(dict(serializer1.data), results_actor)
        self.assertIn(dict(serializer2.data), results_actor)
        self.assertNotIn(dict(serializer3.data), results_actor)

        self.assertIn(dict(serializer1.data), results_title)
        self.assertNotIn(dict(serializer2.data), results_title)
        self.assertNotIn(dict(serializer3.data), results_title)

    def test_retrieve_play_detail(self):
        """Tests retrieving a play's details"""
        play = sample_play()
        play.genres.add(Genre.objects.create(name="Genre"))
        play.actors.add(Actor.objects.create(first_name="Actor", last_name="Last"))

        url = detail_url(play.id)
        res = self.client.get(url)

        serializer = PlayRetrieveSerializer(play)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_play_forbidden(self):
        """Tests that the creation of a play is prohibited for unauthenticated users"""

        payload = {
            "title": "Play",
            "description": "Description",
        }
        res = self.client.post(THEATRE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminPlayApiTests(TestCase):
    def setUp(self):
        """Configures the environment for tests with an authenticated admin user"""
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_play(self):
        """Tests the creation of a play"""
        payload = {
            "title": "Play",
            "description": "Description",
        }
        res = self.client.post(THEATRE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(id=res.data["id"])

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(play, key))

    def test_create_play_with_actors_genres(self):
        """Tests the creation of a play with actors and genres"""
        genre1 = Genre.objects.create(name="Action")
        actors1 = Actor.objects.create(first_name="Tom", last_name="Holland")
        payload = {
            "title": "Spider Man",
            "description": "With Spider-Man's identity now revealed",
            "actors": (actors1.id,),
            "genres": (genre1.id,),
        }
        res = self.client.post(THEATRE_URL, payload)
        play = Play.objects.get(id=res.data["id"])
        genres = play.genres.all()
        actors = play.actors.all()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(genres.count(), 1)
        self.assertEqual(actors.count(), 1)
        self.assertIn(genre1, genres)
        self.assertIn(actors1, actors)


class PlayImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@myproject.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.play = sample_play()
        self.play_session = sample_play_session(play=self.play)

    def tearDown(self):
        self.play.image.delete()

    def test_upload_image_to_play(self):
        """Test uploading an image to play"""
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.play.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.play.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.play.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_play_list_should_not_work(self):
        """Test that posting an image to the play list endpoint does not work"""
        url = THEATRE_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {
                    "title": "Title",
                    "description": "Description",
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(title="Title")
        self.assertFalse(play.image)

    def test_image_url_is_shown_on_play_detail(self):
        """Test that the image URL is shown on the play detail endpoint"""
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(detail_url(self.play.id))

        self.assertIn("image", res.data)

    def test_image_url_is_shown_on_play_list(self):
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(THEATRE_URL)

        self.assertIn("image", res.data["results"][0].keys())

    def test_image_url_is_shown_on_play_session_detail(self):
        """Test that the image URL is shown on the play detail endpoint"""
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(THEATRE_SESSION_URL)

        self.assertIn("play_image", res.data["results"][0].keys())

    def test_put_play_not_allowed(self):
        """Test that PUT method is not allowed on the play detail endpoint"""
        payload = {
            "title": "New movie",
            "description": "New description",
        }

        movie = sample_play()
        url = detail_url(movie.id)

        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_play_not_allowed(self):
        play = sample_play()
        url = detail_url(play.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
