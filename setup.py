import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="chat-collection-framework",
    version="0.1.0",
    author="Frederic Bergeron",
    author_email="bergeron@nlp.ist.i.kyoto-u.ac.jp",
    description="A simple framework to implement a basic chat web application.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://bitbucket.org/ku_nlp/chatcollectionframework",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7'
)
