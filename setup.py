#!/usr/bin/env python

from setuptools import setup, find_packages
from wechat import VERSION

url="https://github.com/jeffkit/wechat"

long_description="Wechat Python SDK"

setup(name="wechat",
      version=VERSION,
      description=long_description,
      maintainer="jeff kit",
      maintainer_email="bbmyth@gmail.com",
      url = url,
      long_description=long_description,
      install_requires = ['requests'],
      packages=find_packages('.'),
     )


