# django-whistle

Django Whistle is a Django app that provides a simple way to send notifications via different channels.
Currently supports `web`, `push`, `email` channels.

## Basic Usage

1. **Installation**: Install Django Whistle using pip:

```bash
pip install django-whistle
```

2. **Configuration in settings**: Add 'whistle' to your `INSTALLED_APPS` in the Django project settings:

 ```python
 # settings.py

INSTALLED_APPS = [
    # ...
    'whistle',
]
 ```

## Configuration

Customize Django Whistle by configuring settings in your project's `settings.py`:

### Basics

Setup events and channels for notifications like this:
**Pro tip**, you can use TextChoices for events.

```python
 # settings.py

WHISTLE_CHANNELS = ['web', 'push', 'email']
WHISTLE_NOTIFICATION_EVENTS = (
    ('NAME_OF_EVENT', gettext_lazy('Object %(object)r was updated')
)
```


```python
### Custom Notification Manager/Handlers

You can ovverride the logic of sending notifications by creating custom manager or handler. Handler is for general
availability of event/channel, and managers is for defining the behaviour. For example, you can use it to customize
emails, add context to emails, or for whatever you miss in the default implementation.

```python
# settings.py

WHISTLE_EMAIL_MANAGER_CLASS = "bidding.notifications.managers.CustomEmailManager"
WHISTLE_NOTIFICATION_MANAGER_CLASS = (
    "bidding.notifications.managers.CustomNotificationManager"
)
WHISTLE_AVAILABILITY_HANDLER = "bidding.notifications.handlers.availability_handler"
```

### Asynchronous Notifications

You can send notifications asynchronously using queues.

```python
# settings.py

WHISTLE_REDIS_QUEUE = None
WHISTLE_USE_RQ = False
RQ_QUEUES = None
WHISTLE_CACHE_TIMEOUT = None  # infinite
```

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of
conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see
the [tags on this repository](https://github.com/your/project/tags).

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone who's code was used
* Inspiration
* etc
