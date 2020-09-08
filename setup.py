import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="chat-collection-framework",
    version="0.2.0",
    author="Frederic Bergeron",
    author_email="bergeron@nlp.ist.i.kyoto-u.ac.jp",
    description="A simple framework to implement a basic chat web application.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://bitbucket.org/ku_nlp/chatcollectionframework",
    packages=setuptools.find_packages(),
    data_files=[
        ('static', [
            'static/default_chat_prologue.js',
            'static/default_chat.js',
            'static/default_chat_epilogue.js',
            'static/default_style.css',
            'static/default_utils.js',
        ]),
        ('static/images', [
            'static/images/bubbles.png',
            'static/images/green.png',
            'static/images/paper.jpg',
            'static/images/red.png',
            'static/images/yellow.png'
        ]),
        ('templates', [
            'templates/default_admin.html',
            'templates/default_chatroom.html',
            'templates/default_chatroom.json',
            'templates/default_index.html',
            'templates/default_version.html',
            'templates/default_errorForbiddenAccess.html'
        ])
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7'
)
