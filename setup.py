import setuptools

setuptools.setup(
    name = 'TMCM-Lib',
    description = 'Trinamic Module Library for Python',
    keywords = ['Trinamic', 'TMCM', 'TMCL', 'Stepper-Motor-Control'],
    version = '0.5.0',
    url = 'https://github.com/florian-lapp/tmcm-lib-py',
    packages = ['tmcm_lib', 'tmcm_lib.tmcm_3110'],
    install_requires = ['pyserial'],
    author = 'Florian Lapp',
    author_email = 'e5abed0c@gmail.com'
)