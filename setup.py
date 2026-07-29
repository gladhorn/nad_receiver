from setuptools import setup

setup(name='nad_receiver',
      version='0.3.0',
      description='Library to interface with NAD receivers through RS232, TCP and telnet',
      url='https://github.com/joopert/nad_receiver',
      download_url='https://github.com/joopert/nad_receiver/archive/0.3.0.tar.gz',
      author='joopert',
      license='MIT',
      packages=['nad_receiver'],
      install_requires=['serialx[esphome]>=1.8.0', 'telnetlib3>=4.0.2'],
      zip_safe=True)
