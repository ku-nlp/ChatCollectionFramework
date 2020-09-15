# Manual

## Introduction

The ChatCollectionFramework is a simple framework written in Python that allows quick instanciation of a chat server that can be used to collect chat data from crowdsourcing experiments.

It provides a default functional implementation of a Chat Server.   However, in most situations, the default implementation will not be enough.  It will be used only as a starting point.  Additional customizations will need to be implemented upon it to fulfill your specific requirements.

At this moment, the typical use case that is supported is a server to which clients can connect to to find a partner and where they can chat one on one.

Eventually, other use cases could be implemented.

To demonstrate how the framework can be used, we will create a custom implementation of the dummy chat server.

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

As the framework is currently not public, you must download and install it into your home directory from this git repository[git repository](https://bitbucket.org/ku_nlp/chatcollectionframework/src/master/) :

	cd
	git clone git@bitbucket.org:ku_nlp/chatcollectionframework.git chat-collection-framework
	cd chat-collection-framework
  
Instructions can be found in the _README.md_ file to prepare the Python environment and build the wheel file.
 
Once that the chat_collection_framework-X.Y.Z-py3-none-any.whl file of the chat-collection-framework is built, you will be able to use it and install it in the Python environment of your specific project.

Let's do that.

	cd ~/my-custom-chat-server
	pipenv uninstall chat_collection_framework
	pipenv lock --clear
	pipenv install --clear ~/chat-collection-framework/dist/chat_collection_framework-X.Y.Z-py3-none-any.whl
	
The second line is only useful in the case that you have already installed the ChatCollectionFramework and that you want to uninstall it before reinstalling it in your project.  This might come handy if you need to modify the code of the ChatCollectionFramework.  That could be needed because the package is still in development and might need either bug fixes or new features.

 At this stage, the ChatCollectionFramework should be installed.  However, before we can use it, we need to configure a few elements.
 
 First, let's write a configuration file. To do that, we will use the provided sample configuration file:
 
 	cp ~/chat-collection-framework/config.json.sample config.json
 
 We could edit the config.json and replace all occurrences of ChatCollectionServer by MyCustomChatServer.
 
 Then, let's write a logging configuration file.  To do that, we will use the provided sample configuration file one more time:
 
	cp ~/chat-collection-framework/logging.conf.sample logging.conf
 
 The logging.conf file needs no modifications.  However, we need to create the log output directory so that it can work properly:
 
	 mkdir logs








you must first build it.  

  
  For example, let's assume that your project is named _MyCustomChatServer_ and that the related code is located in the _~/mycustomchatserver_ directory.
  
  Let's also assume that you are using _pipenv_ to create and manage the Python environment of your project.  To install the latest wheel file of _chat-collection-framework_, you will do:
  
	pipenv uninstall chat_collection_framework
	pipenv lock --clear
	pipenv install --clear ~/chatcollectionframework/dist/chat_collection_framework-X.Y.Z-py3-none-any.whl
	  
  That's it. From now on, you can use the framework.
  
  






## Customization

## Troubleshooting

