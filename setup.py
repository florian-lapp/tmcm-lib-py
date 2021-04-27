import setuptools

setuptools.setup(
    name = 'TMCM-Lib',
    description = 'Trinamic Motion Control Module Library for Python',
    keywords = ['Trinamic', 'TMCM', 'TMCL', 'Stepper-Motor-Control'],
    version = '0.6.0',
    url = 'https://github.com/florian-lapp/tmcm-lib-py',
    packages = ['tmcm_lib', 'tmcm_lib.module_3110'],
    install_requires = ['pyserial'],
    author = 'Florian Lapp',
    author_email = 'e5abed0c@gmail.com'
)