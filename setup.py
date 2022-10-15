from setuptools import setup

setup(
    name='pyRemoteChart',
    version='0.0.1',
    description='zmq based remote chart drawing library',
    author='Jongheum Park',
    author_email='parkj0821@gmail.com',
    license='GPLv2',
    packages=['pyRemoteChart'],
    install_requires=['zmq', 'pandas', 'matplotlib', 'tornado']
)