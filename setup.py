from setuptools import setup


version = '0.7.0'
description = "Sync github release notes with your project's changelog"

setup(
    name='gitch',
    version=version,
    description=description,
    long_description=description,
    classifiers=[],
    keywords=[
        'gitch',
        'github',
        'github-releases',
        'changelog',
        'release',
        'release-automation'
    ],
    author='Allan Johns',
    author_email='nerdvegas@gmail.com',
    url='https://github.com/nerdvegas/gitch',
    license='Apache 2.0',
    py_modules=['gitch'],
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'requests>=2.0,<3.0'
    ],
    entry_points={
        'console_scripts': [
            'gitch = gitch:_main',
        ]
    }
)
