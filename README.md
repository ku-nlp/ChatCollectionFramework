# Chat Collection Framework

## Requirements

- python-3.7

To prepare the environment:

```sh
pipenv sync --python /mnt/orange/brew/data/bin/python3.7
```

## Configuration

### Server

Some configuration parameters must be specified in the config.json file.
Sample config files is provided.  Copy the sample file into the same name but without the ".sample" suffix. 
Then, edit its content to specify parameter values in function of your environment.

config.json:

sessions: Directory where sessions will be stored during execution.
sessionTimeout: Number of minutes before a session expires automatically.
cookiePath: Path identifing the cookie that will be stored on the client side.
archives: Directory where the dialogs will be archived.
web_context: Virtual directory of the web application.
poll_interval: If a client does not poll the server within this period (in secs), the client will be considered as non-responsive.
delay_for_partner: Number of seconds that the client will wait for partners before aborting the experiment.
chatroom_cleaning_interval: Delay (in secs) where the room cleanup will be performed automatically.
msg_count_low: Minimum number of messages before the is considered long enough.
msg_count_high: Maximum number of messages before the chat is considered too long.
experiment_id: Identifier of the experiment (can be used for user payment).
prevent_multiple_tabs: If True, an error page will be shown if the user tries to use more than one tab to chat.

### Logging

Copy the logging.conf.sample file into logging.conf and create a logs directory so that the server can write logging info.


### App

Most likely that custom behavior will need to be implemented for your chat application.  The framework provides a base App.py.sample which should be copied under App.py and customized according to your particular needs.


## Usage

To start the server:

```sh
python App.py
```

To stop the server:

For now, hit CTRL + C.  Eventually, the server should run as a system-level service.


## Building

To build the framework package so that it can be used into another project:

```sh
rm -rf dist/*
python setup.py clean --all
python setup.py sdist bdist_wheel
```

This will build a wheel file that can be installed into a Python environment.

To update the framework into another project (assuming you're outside the pipenv shell):

```sh
pipenv uninstall chat_collection_framework
pipenv lock --clear
pipenv install --clear $CHAT_COLLECTION_FRAMEWORK/dist/chat_collection_framework-X.Y.Z-py3-none-any.whl
```
