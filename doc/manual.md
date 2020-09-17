# Manual

## Introduction

The ChatCollectionFramework is a simple framework written in Python that allows quick instanciation of a chat server that can be used to collect chat data from crowdsourcing experiments.

It provides a default functional implementation of a Chat Server.   However, in most situations, the default implementation will not be enough.  It will be used only as a starting point.  Additional customizations will need to be implemented upon it to fulfill your specific requirements.

At this moment, the typical use case that is supported is a server to which clients can connect to to find a partner and where they can chat one on one.

Eventually, other use cases could be implemented.

To demonstrate how the framework can be used, we will create a custom implementation of the dummy chat server.  But first, let's take an overview of the architecture of the ChatCollectionFramework.

## Overview

Here is at a glance how a chat collection web application using the framework should look like:

![Webapp Overview](images/overview.png  "Webapp Overview")

The classes in dark gray are dependencies.  The classes in light gray come from the framework.  The classes in white come from the customized web application.

In some cases, some of the white classes might not be required because the inherited class already provides sufficient functionality and does not need to be extended.  For instance, for some systems, the BaseUser class might be enough and there would no reasons to have a User subclass.

The main class is the App that inherits from BaseApp that is a specialization of a Flask application. It implements HTTP requests of a basic chat application like:
- join
- post
- leave
- etc.

The Api class implements all the business logic and models specific to the chat application. 

User and Chatroom classes are data structures that are used by the model in the Api.  The BaseUser and BaseChatroom already provide some basic functionalities but in many cases, they will need to be customized.

The ChatroomCleaner class is an utility class that runs a thread that cleans periodically inactive users that joined the system.  

We will take a deeper look at these classes later.

## Installation

Before installing the framework, let's prepare the working directory of our dummy chat server.

Let's make a directory in our home directory:

	cd
	mkdir my-custom-chat-server
	cd my-custom-chat-server

To prepare the Python environment of our project, we do:

	pipenv --python python3

That's it. We have now an empty project.

It's time to integrate the ChatCollectionFramework into our project.  Before we can do that, we must first build it from source.

As the framework is currently not public, you must download and install it into your home directory from this [git repository](https://bitbucket.org/ku_nlp/chatcollectionframework/src/master/) :

	cd
	git clone git@bitbucket.org:ku_nlp/chatcollectionframework.git chat-collection-framework
	cd chat-collection-framework
  
You might find additional Instructions in the _README.md_ file but essentially, to build the wheel file, you need to do that:

	pipenv sync
	pipenv shell
	rm -rf dist/*
	python setup.py clean --all 
	python setup.py sdist bdist_wheel

The third and fourth commands are not needed the very first time that you build the package.  However, they will be needed for ulterior builds.

At this point, you should have the chat_collection_framework-X.Y.Z-py3-none-any.whl in the dist directory.  This file needs to be installed in the Python environment of your specific project.

Let's do that.

	cd ~/my-custom-chat-server
	pipenv uninstall chat_collection_framework
	pipenv lock --clear
	pipenv install --clear ~/chat-collection-framework/dist/chat_collection_framework-X.Y.Z-py3-none-any.whl
	
The second line is only useful in the case that you have already installed the ChatCollectionFramework and that you want to uninstall it before reinstalling it in your project.  This might come handy if you need to modify the code of the ChatCollectionFramework or if you want to upgrade it to a newer version.

 At this stage, the ChatCollectionFramework should be installed.  However, before we can use it, we need to configure a few elements.
 
 First, let's write a configuration file. To do that, we will use the provided sample configuration file:
 
 	cp ~/chat-collection-framework/config.json.sample config.json
 
 We should edit the config.json and replace all occurrences of ChatCollectionServer by my-custom-chat-server.
 
 For more information about the configuration parameters, check the appendices.
 
 Then, let's write a logging configuration file.  To do that, we will use the provided sample configuration file one more time:
 
	cp ~/chat-collection-framework/logging.conf.sample logging.conf
 
 The logging.conf file needs no modifications.  However, we need to create the log output directory so that it can work properly:
 
	 mkdir logs

The last step is to use the provided App.py.sample file as a starting point:

	cp ~/chat-collection-framework/App.py.sample App.py

You are now ready to start the server and check if it works.

	pipenv shell
	python App.py

For example, if you're running the server on the host basil501, launch a browser pointing to this page:

	http://basil501:8993/my-custom-chat-server/index

You should see something that looks like this:

![Default Index Page](images/my-custom-chat-server-default-index-page.png  "Default Index Page")

If you set up the Nginx web server properly to that it redirects the requests from the my-custom-chat-server context to your server running on basil503, you should already be able to use the system with 2 different browsers and simulate a conversation between 2 users.  The configuration with Nginx web server is mandatory because the framework assumes that https is used and it will not work well without it.   The configuration of the Nginx server is out of scope of this document.  

When configured with Nginx, it should look like this:

![Conversation sample with default implementation](images/my-custom-chat-server-default-chat-sample.png  "Conversation sample with default implementation")

It might be a good idea to reuse the automated tests from the framework and integrate them to your custom application.  This way, you can leverage the framework even more:

	cp -ra ~/chat-collection-framework/tests .

Before running the tests, you will need to install some additional modules into your Python environment:

	exit
	pipenv install pytest psutil bs4
	pipenv shell

Also, by defaut, the tests use the files config.json.sample and logging.conf.sample instead of config.json and logging.conf because the latter should not be versioned in the code repository.  You should do the same thing as well:

	cp config.json config.json.sample
	cp logging.conf logging.conf.sample
	echo config.json >> .gitignore
	echo logging.conf >> .gitignore

To run the tests, we do:

	pytest -s

As we have not started yet to customize the application, all the tests should pass successfully.

If you're using bitbucket to host your code repository, you could also reuse the configuration file from the framework that will run the tests automatically each time that you push commits on the repository:

	cp ~/chat-collection-framework/bitbucket-pipelines.yml .

And edit the bitbucket-pipelines.yml and remove the line that refers to App.py.sample file.  This file doesn't exist in our case and is not needed. 

Then you will have to activate the pipelines in your bitbucket settings page to use this feature.

If your code repository is hosted on Github, you will need to write a .travis.yml file instead.  Read documentation on Github for more information.


## Customization

At this stage, we have a basic functional chat server but it needs to be customized to your specific requirements.  For example, most likely that the look must be changed. And possibly that some behavior must be different too.  In this section, we will explain different ways to modify the default behavior of the framework to fulfill your needs.

First, let's try to change the look of the welcoming page.

The framework assumes that the first page is called index.  Let's take a look at the framework code handling this request.

The entry points of the requests are defined in the class BaseApp that can be found in ~/chat-collection-framework/server/base.py:

	class BaseApp(Flask):
	
	    def __init__(self, import_name, api):
	        Flask.__init__(self, import_name)
	
	        my_loader = jinja2.ChoiceLoader([
	            self.jinja_loader,
	            jinja2.FileSystemLoader(os.path.join(sys.prefix, 'templates')),
	        ])
	        self.jinja_loader = my_loader
	
	        self.api = api
	        self.cfg = api.cfg
	        self.logger = api.logger
	
	        self.SESSION_TYPE = 'filesystem'
	        self.SESSION_COOKIE_NAME = 'CGISESSID'
	        self.SESSION_FILE_DIR = self.cfg['sessions']
	        self.SESSION_COOKIE_PATH = self.cfg['cookiePath']
	        self.SESSION_COOKIE_SECURE = True
	
	        self.config.from_object(self)
	        Session(self)
	
	        @self.route(f"/{self.cfg['web_context']}/static/<path:path>")
	        def get_static(path):
	            return self.get_static(path)
	
	        @self.route(f"/{self.cfg['web_context']}/default_static/<path:path>")
	        def get_default_static(path):
	            return self.get_default_static(path)
	
	        @self.route(f"/{self.cfg['web_context']}/version")
	        def version():
	            return self.version()
	
	        @self.route(f"/{self.cfg['web_context']}/index")
	        def index():
	            return self.index()
	
	        @self.route(f"/{self.cfg['web_context']}/admin")
	        def admin():
	            return self.admin()
	         
	        ... 
	           
	
A BaseApp is basically a Flask App that handles a predetermined set of requests.  The supported requests are:

- version: shows the version of the web application.
- index: shows the welcome page.
- admin: shows the administrator's page.
- join: add a user to a chatroom.
- chatroom: retrieve the state of a chatroom.
- post: add a new message to a chatroom.
- leave: remove a user from the chatroom.

As we can see, a route is declared for each request and a corresponding function is called.

In our case, for the index request, the default behavior looks like this:

 
	    def index(self):
	        try:
	            return render_template(template_name_or_list='index.html')
	        except TemplateNotFound:
	            return render_template(template_name_or_list='default_index.html')
	
As we can see, it tries first to render the index.html template page if it can find it. Otherwise, it will render the default_index.html template page that comes from the framework.

So if we just want to change the look of the index page, we should make a templates directory and copy the default_index.html into it with the name index.html:

	mkdir templates
	cp ~/chat-collection-framework/default_index.html templates/index.html

Let's edit the templates/index.html file and customize it a little bit.

The file should look something like this:

	<!DOCTYPE html>
	<html lang="ja">
	<head>
	    <meta charset="utf-8">
	    <title>チャットサーバー</title>
	    <link rel="stylesheet" href="default_static/default_style.css">
	    <link rel="stylesheet" href="static/style.css">
	    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js"></script>
	    <link rel="stylesheet" href="https://ajax.googleapis.com/ajax/libs/jqueryui/1.12.1/themes/smoothness/jquery-ui.css">
	    <script src="https://ajax.googleapis.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js"></script>
	    <script src="default_static/default_utils.js"></script>
	    <script src="static/utils.js"></script>
	    <script>
	        function validateForm(evt) {
	            // Perform some validations here.
	            // If something is invalid, show an error message and return false.
	            // Otherwise return true.
	            //
	            // For example: 
	            //
	            // var selectedPartnerType = $('input[name="partner-type"]:checked').val();
	            // if (selectedPartnerType == 'gender-same' && (!selectedGender || selectedGender == 'unknown')) {
	            //     showSimpleDialog('注意', '同性とのチャットを希望される場合は、あなたの性別を選択してください。');
	            //     return false;
	            //}
	            return true;
	        }
	
	        $(document).ready(function(evt) {
	            // The clientTabId is used to differentiate users
	            // when the client uses more than one tab in his browser.
	            var clientTabId = new Date().getTime();
	            $('#client-tab-id').val(clientTabId);
	
	            $('#join-chat').on('click', validateForm);
	        });
	    </script>
	</head>
	<body class="column">
	<h1>対話収集タスクへようこそ</h1>
	<br/><br/>
	<p>チャットをスタートする時はボトンをクリックして下さい。</p>
	<br/><br/>
	<form id="form-join" action="join" method="POST">
	<input type="hidden" id="client-tab-id" name="clientTabId"/>
	</form>
	<input type="submit" id="join-chat" value="チャットを始める" class="button" form="form-join"/>
	<div id="dialog-simple"></div>
	</body>
	
As long as we keep the essential parts, that are, the form containing the join-chat button, the Javascript code that handles the event associated with the join-chat button, and the initialization of the clientTabId variable, it should work normally.

So it's possible to add some text, change the CSS attributes, alter the structure of the document and make it look as we want.  

We can see that by default, 2 CSS files are referred: 

- default_static/default_style.css
- static/style.css

The first contains the default CSS definitions.  The second one contains customized definitions that will be loaded on top of the default ones.  So if we want to reuse the default style, we can keep the reference to the default_style.css and add a new file static/style.css to override some style definitions when needed.  In the case where a completely different style is desired, it might be better to remove the reference to default_style.css altogether.

For example, if we want to change the background and foreground colors, we could do:

	mkdir static
	cp ~/chat-collection-framework/static/default_style.css static/style.css

And edit the static/style.css file so that it contains only:

	body {
	    background-color: #333333;
	    color: #ffffff;
	}

However, if there are some changes in the behavior, some modifications on the server code will also be needed.   For example, let's say that we want to add mandatory values into the form that must be provided before joining the chat system.  We could add some client-side validations but we should also add some server-side validations as well.

Let's say that we want each user to provide their name before joining the chat, we could modify the original form and add a Name field like this:

	<form id="form-join" action="join" method="POST">
	名前：<input type="text" id="username" name="username"/><br/><br/>
	
On the server-side, we will have to modify the join request handling so that the user-name parameter must be provided or return an 400 HTTP response if none is provided.

The recommended approach is to copy the code from the framework and adapt it to our needs.  There are usually 3 levels of changes:

- App
- Api
- Templates

Depending on the situation, not all levels need to be changed. The fewer changes, the better.

In our case, we want first to override the App.join() method.  The code can be found in ~/chat-collection-framework/server/base.py.  It looks like this:

    def join(self, session, request):
        if 'clientTabId' not in request.form:
            return '', 400

        client_tab_id = request.form['clientTabId']
        user_id = f'{session.sid}_{client_tab_id}'
        data = self.api.join(user_id)

        if isinstance(data, str) and data.startswith("Error: MultipleTabAccessForbidden"):
            return self.error_forbidden_access_multiple_tabs()

        try:
            return render_template(
                template_name_or_list='chatroom.html',
                client_tab_id=client_tab_id,
                msg_count_low=data['msg_count_low'],
                msg_count_high=data['msg_count_high'],
                poll_interval=data['poll_interval'],
                delay_for_partner=0 if data['chatroom'].closed else data['delay_for_partner'],
                experiment_id=data['chatroom'].experiment_id,
                chatroom_id=data['chatroom'].id,
                is_first_user=(data['chatroom'].initiator == user_id),
                server_url=''
            )
        except TemplateNotFound:
            return render_template(
                template_name_or_list='default_chatroom.html',
                client_tab_id=client_tab_id,
                msg_count_low=data['msg_count_low'],
                msg_count_high=data['msg_count_high'],
                poll_interval=data['poll_interval'],
                delay_for_partner=0 if data['chatroom'].closed else data['delay_for_partner'],
                experiment_id=data['chatroom'].experiment_id,
                chatroom_id=data['chatroom'].id,
                is_first_user=(data['chatroom'].initiator == user_id)
            )

Basically, it makes sure that the clientTabId is provided and it returns the chatroom.html page if it's defined or the default _chatroom.html if it's not.

We can copy the whole method into our App class and adjust it so that it tests if the mandatory username parameter is found or not.  Pass the username to the Api so that we can update our model accordingly and pass it too to our chatroom.html template so that it's shown to the user:

    class App(BaseApp):

	...
	
      def join(self, session, request):
        if 'clientTabId' not in request.form or 'username' not in request.form:
            return '', 400

        client_tab_id = request.form['clientTabId']
        user_id = f'{session.sid}_{client_tab_id}'
        username = request.form['username']
        attribs = {'username': username}
        data = self.api.join(user_id, attribs)

        if isinstance(data, str) and data.startswith("Error: MultipleTabAccessForbidden"):
            return self.error_forbidden_access_multiple_tabs()

        return render_template(
            template_name_or_list='chatroom.html',
            client_tab_id=client_tab_id,
            msg_count_low=data['msg_count_low'],
            msg_count_high=data['msg_count_high'],
            poll_interval=data['poll_interval'],
            delay_for_partner=0 if data['chatroom'].closed else data['delay_for_partner'],
            experiment_id=data['chatroom'].experiment_id,
            chatroom_id=data['chatroom'].id,
            is_first_user=(data['chatroom'].initiator == user_id),
            server_url='',
            username=username
        )

We removed the default_chatroom.html because we will need it no longer because our chatroom.html page needs to be customized anyway so that it shows the username.

Again to customize the chatroom.html, it's recommended to copy the default_chatroom.html page from the framework and adjust it to our needs:

	cp ~/chat-collection-framework/templates/default_chatroom.html templates/chatroom.html

And we adjust it a little bit to show the username in the header:

	<body class="column fixed-height">
	    <h2>チャットルーム({{username}})</h2>
	
That's it!

Let's start the server and see if our changes work properly:

	python App.py

The index page now looks like this:

![Custom index page with username](images/my-custom-chat-server-index-with-username.png  "Custom index page with username")

And once that the チャットを始める button is clicked, the next page looks like this:

![Custom chatroom page with username](images/my-custom-chat-server-chatroom-with-username.png  "Custom chatroom page with username")

One last thing that needs to be addressed is that the automated tests need to be updated according to our latest changes.

As we have added a new mandatory parameter to the join request, some tests will fail.  They must be adjusted to reflect this change.

The file tests/chat_test.py must be edited so that every call to join request must now pass the username parameter like this:

	usernames = [
	    "John",
	    "Sora",
	    "Eric",
	    "Tanaka",
	    "Gary",
	    "Kodama",
	    "Stanley",
	    "Kyosuke",
	    "Harry",
	    "Juan"
	]
	username = username = usernames[randint(0, len(usernames) -1)]
	command = f'curl -X POST http://127.0.0.1:{PORT}/{WEBAPP_CONTEXT}/join -d "clientTabId=11111" -d"username={username}"'

That's how you can customize the framework.

In our case, the changes were very simple.  Some major changes might be needed for some situations.  For more real examples, it's recommended to check the code of other existing projects that are using the ChatCollectionFramework.

As much as possible, it's recommended to try minimizing changes and try reusing code from the framework as much as possible.  For example, in some circumstances, it might be better to override an Api's method and call its super behavior instead of duplicating the code.  This way, if the framework is upgraded, it's more likely not to provoke bugs.  Of course, as the framework is still in development, it's possible that some non backward-compatible changes are introduced and that some fixes will need to be applied to our custom code.





##  Appendices

### Config.json

This section explains the configuration parameters:

- sessions

This is the directory where the HTTP sessions will be stored by Flask.  When users access the chat system, the web server can keep data associated to the connection.  These data are kept in text files in this directory.

- sessionTimeout

This is the delay where the sessions will be automatically removed from the server when a user is inactive for too long.

- cookiePath

This is the url to which the session cookie will be associated with.

- archives

The location on disk where the dialgos will be archived.

- web_context

The name of the web app on the server. This is the string that you see in the URL of the server just after the domain name and before the request action verb.

- poll_interval

The number of seconds that the client issues a poll request to the server to retrieve updated state of his chatroom.

- delay_for_partner

The number of seconds that  a client will wait in order to be matched with another chat partner.  After this delay, the client will be forced to leave  the chat system and try again later.

- chatroom_cleaning_interval

The number of seconds between each time the ChatroomCleaner thread will perform his routine cleaning task.

- msg_count_low

The minimum number of messages a user must post before that a dialog can be terminated.  Before that threshold, user will still be able to leave the chat but a warning message will tell him  that the dialog is too short.

- msg_count_high

After a user has posted this amount of message, a warning message will be shown indicating that the dialog is long enough and that it should be concluded soon.

- experiment_id

The identifier of the crowdsourcing experiment that will be shown to the users when the chat is terminated propperly.

- prevent_multiple_tabs

When "True", a user will not be able to access the chat system using multiple tabs on the same browser.

## Troubleshooting

