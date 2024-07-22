import ast
from unittest import mock
import datetime
from rest_framework.test import APITestCase, APIRequestFactory, override_settings
from django.contrib.auth.models import User

from tracking.models import APIRequestLog
from tracking.base_mixins import BaseLoggingMixin
from . import views


@override_settings(ROOT_URLCONF='tracking.tests.urls')
class TestLoggingMixin(APITestCase):
    def test_nologging_no_log_created(self):
        response = self.client.get('/no-logging/')
        self.assertEqual(APIRequestLog.objects.all().count(), 0)

    def test_logging_creates_log(self):
        response = self.client.get('/logging/')
        self.assertEqual(APIRequestLog.objects.all().count(), 1)

    def test_log_path(self):
        response = self.client.get('/logging/')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.path, '/logging/')

    def test_log_ip_remote(self):
        request = APIRequestFactory().get('/logging/')
        request.META['REMOTE_ADDR'] = '127.0.0.9'
        views.MockLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.remote_addr, '127.0.0.9')

    def test_log_ip_remote_list(self):
        request = APIRequestFactory().get('/logging/')
        request.META['REMOTE_ADDR'] = '127.0.0.9, 128.1.1.9'
        views.MockLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.remote_addr, '127.0.0.9')

    def test_log_ip_remote_v4_with_port(self):
        request = APIRequestFactory().get('/logging/')
        request.META['REMOTE_ADDR'] = '127.0.0.9: 4090'
        views.MockLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.remote_addr, '127.0.0.9')

    def test_log_ip_remote_v6(self):
        request = APIRequestFactory().get('/logging/')
        request.META['REMOTE_ADDR'] = '2001:db8:85a3::8a2e:370:7734'
        views.MockLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.remote_addr, '2001:db8:85a3::8a2e:370:7734')

    def test_log_ip_remote_v6_loopback(self):
        request = APIRequestFactory().get('/logging/')
        request.META['REMOTE_ADDR'] = '::1'
        views.MockLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.remote_addr, '::1')

    def test_log_ip_remote_v6_with_port(self):
        request = APIRequestFactory().get('/logging/')
        request.META['REMOTE_ADDR'] = '[2001:db8:85a3::8a2e:370:7734]: 4090'
        views.MockLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.remote_addr, '2001:db8:85a3::8a2e:370:7734')

    def test_log_ip_xforwarded(self):
        request = APIRequestFactory().get('/logging/')
        request.META['HTTP_X_FORWARDED_FOR'] = '127.0.0.8'
        views.MockLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.remote_addr, '127.0.0.8')

    def test_log_ip_xforwarded_list(self):
        request = APIRequestFactory().get('/logging/')
        request.META['HTTP_X_FORWARDED_FOR'] = '127.0.0.8, 127.0.0.9, 127.0.0.10'
        views.MockLoggingView.as_view()(request).render()
        log = APIRequestLog.objects.first()
        self.assertEqual(log.remote_addr, '127.0.0.8')

    def test_log_host(self):
        self.client.get('/logging/')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.host, 'testserver')

    def test_log_method(self):
        self.client.get('/logging/')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.method, 'GET')

    def test_log_status_code(self):
        self.client.get('/logging/')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.status_code, 200)

    def test_logging_explicit(self):
        self.client.get('/explicit-logging/')
        self.client.post('/explicit-logging/')
        self.assertEqual(APIRequestLog.objects.all().count(), 1)

    def test_custom_check_logging(self):
        self.client.get('/custom-check-logging/')
        self.client.post('/custom-check-logging/')
        self.assertEqual(APIRequestLog.objects.all().count(), 1)

    def test_log_anon_user(self):
        self.client.get('/logging/')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.user, None)

    def test_log_auth_user(self):
        User.objects.create_user(username='myuser', password='secret')
        self.client.login(username='myuser', password='secret')
        user = User.objects.get(username='myuser')
        self.client.get('/session-auth-logging/')
        log = APIRequestLog.objects.first()
        self.assertEqual(log.user, user)

    def test_log_params(self):
        self.client.get('/logging/', {'p1': 'a', 'p2': 'b'})
        log = APIRequestLog.objects.first()
        self.assertEqual(ast.literal_eval(log.query_params), {'p1': 'a', 'p2': 'b'})

    def test_log_params_cleaned_form_personal_fields(self):
        self.client.get('/sensitive-field-logging/', {'api': '1234', 'capitalize': 'ABS', 'my_field': 'mysecret'})
        log = APIRequestLog.objects.first()
        self.assertEqual(ast.literal_eval(log.query_params),
                         {
                             'api': BaseLoggingMixin.CLEANED_SUBSTITUTE,
                             'capitalize': 'ABS',
                             'my_field': BaseLoggingMixin.CLEANED_SUBSTITUTE
                         })

    def test_invalid_cleaned_substitute_fails(self):
        with self.assertRaises(AssertionError):
            self.client.get('/invalid-cleaned-substitute/')

    @mock.patch('tracking.models.APIRequestLog.save')
    def test_log_doesnt_prevent_api_call_if_log_save_fails(self, mock_save):
        mock_save.side_effect = Exception('db failure...')
        response = self.client.get('/logging/')
        self.assertEqual(APIRequestLog.objects.all().count(), 0)
        self.assertEqual(response.status_code, 200)

    @override_settings(USE_TZ=False)
    @mock.patch('tracking.base_mixins.now')
    def test_log_doesnt_fail_with_negative_response_ms(self, mock_now):
        mock_now.side_effect = [
            datetime.datetime(2017, 12, 1, 10, 0, 10),
            datetime.datetime(2017, 12, 1, 10, 0, 0)
        ]
        response = self.client.get('/logging/')
        self.assertEqual(response.status_code, 200)
        log = APIRequestLog.objects.first()
        self.assertEqual(log.response_ms, 0)
