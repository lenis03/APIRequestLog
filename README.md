# drf-api-tracking

## Overview

`drf-api-tracking` provides a Django model and DRF view mixin that log Django Rest Framework requests to the database. Each request/response cycle to a view using the mixin will log the following attributes:

| Model field name      | Description                                                                 | Model field type        |
|-----------------------|-----------------------------------------------------------------------------|-------------------------|
| user                  | User if authenticated, None if not                                          | ForeignKey              |
| username_persistent   | Static field that persists the username even if the User model is deleted   | CharField               |
| requested_at          | Date-time that the request was made                                         | DateTimeField           |
| response_ms           | Number of milliseconds spent in view code                                   | PositiveIntegerField    |
| path                  | Target URI of the request, e.g., "/api/"                                     | CharField               |
| view                  | Target VIEW of the request, e.g., "views.api.ApiView"                       | CharField               |
| view_method           | Target METHOD of the VIEW of the request, e.g., "get"                       | CharField               |
| remote_addr           | IP address where the request originated                                     | GenericIPAddressField   |
| host                  | Originating host of the request, e.g., "example.com"                        | URLField                |
| method                | HTTP method, e.g., "GET"                                                    | CharField               |
| query_params          | Dictionary of request query parameters, as text                             | TextField               |
| data                  | Dictionary of POST data (JSON or form), as text                             | TextField               |
| response              | JSON response data                                                          | TextField               |
| status_code           | HTTP status code, e.g., 200 or 404                                          | PositiveIntegerField    |

## Requirements

- **Django**: 1.11, 2.0, 2.1, 2.2, 3.0
- **Django REST Framework** and **Python** release supporting the version of Django you are using

| Django | Python           | DRF               |
|--------|------------------|-------------------|
| 1.11   | 2.7, 3.5, 3.6    | 3.5, 3.6, 3.7, 3.8, 3.9 |
| 2.0    | 3.5, 3.6, 3.7    | 3.7, 3.8, 3.9     |
| 2.1    | 3.5, 3.6, 3.7, 3.8 | 3.7, 3.8, 3.9  |
| 2.2    | 3.5, 3.6, 3.7, 3.8 | 3.7, 3.8, 3.9  |
| 3.0    | 3.5, 3.6, 3.7, 3.8 | 3.7, 3.8, 3.9  |

## Installation

1. **Clone the repository:**

    ```bash
    git clone [https://github.com/lenis03/APIRequestLog]
    cd APIRequestLog
    ```

2. **Create and activate a virtual environment using `pipenv`:**

    ```bash
    pipenv install
    pipenv shell
    ```

3. **Apply the migrations:**

    ```bash
    python manage.py migrate
    ```

4. **Create a superuser:**

    ```bash
    python manage.py createsuperuser
    ```

5. **Run the development server:**

    ```bash
    python manage.py runserver
    ```


## Usage

Add the `rest_framework_tracking.mixins.LoggingMixin` to any DRF view to create an instance of `APIRequestLog` every time the view is called.

### Basic Example

```python
# views.py
from rest_framework import generics
from rest_framework.response import Response
from rest_framework_tracking.mixins import LoggingMixin

class LoggingView(LoggingMixin, generics.GenericAPIView):
    def get(self, request):
        return Response('with logging')
```
### Performance Enhancement

Choose methods to be logged using `logging_methods` attribute:

```python
class LoggingView(LoggingMixin, generics.CreateModelMixin, generics.GenericAPIView):
    logging_methods = ['POST', 'PUT']
    model = ...
```

### Custom Logging Rules

Override `should_log` method to define custom rules:
```python
class LoggingView(LoggingMixin, generics.GenericAPIView):
    def should_log(self, request, response):
        """Log only errors"""
        return response.status_code >= 400
```

### Custom Log Handling

Override handle_log method for custom handling:
```python
class LoggingView(LoggingMixin, generics.GenericAPIView):
    def handle_log(self):
        # Do some stuff before saving.
        super(MockCustomLogHandlerView, self).handle_log()
        # Do some stuff after saving.
```
### Handling Large File Uploads

Disable decoding the request body globally by setting DRF_TRACKING_DECODE_REQUEST_BODY = False in settings.py, or for individual views:
```python
class LoggingView(LoggingMixin, generics.GenericAPIView):
    decode_request_body = False
```
## Security

drf-api-tracking hides sensitive fields by default. Customize the list using the sensitive_fields parameter:
```python
class LoggingView(LoggingMixin, generics.CreateModelMixin, generics.GenericAPIView):
    sensitive_fields = {'my_secret_key', 'my_secret_recipe'}
```
Set `DRF_TRACKING_ADMIN_LOG_READONLY to True in settings.py to prevent API request log entries from being modified in Django admin.

## Development

Use the sample DRF project drf_api_sample to generate new migrations if changes are made to the models.

## Testing

Run tests:

```bash
python manage.py test
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.
