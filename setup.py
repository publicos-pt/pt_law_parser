from setuptools import setup, find_packages


setup(name='pt-law-parser',
      version='1.0',
      description='Parser of the portuguese law',
      author='Jorge C. Leitão',
      author_email='jorgecarleitao@gmail.com',
      packages=find_packages(),
      license='MIT',
      classifiers=[
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3',
          'Topic :: Utilities',
      ],
      install_requires=['pt_law_downloader'],
)
