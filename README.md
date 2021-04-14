# Orbitscalc: Satellite Data Transmission Analysis
Orbitscalc is a Django web application that calculates the maximum amount of data that can be sent from a satellite to a number of ground stations over a certain time period.
This application as been developed as a complex project in highschool. Read the detailed German project documentation [here](https://github.com/Surf1sh/Orbitscalc/blob/master/Dokumentation%20BeLL.pdf). 

## Setup
The following python-packages are needed in order to run this application locally (versions used for development in brackets):
* Python (3.7.4) - https://www.python.org/downloads/ MIT License
* Django (3.0.8) - https://www.djangoproject.com/download/ 3-Clause BSD License
````
pip install django
````
* Skyfield (1.30) - https://rhodesmill.org/skyfield/installation.html
````
pip install skyfield
````
Clone the repository and go to the project directory with the file `manage.py`.
Start the development server by executing `py manage.py runserver` on Windows or `python manage.py runserver`.
For detailed information on running a Django project locally see the [Django documentation](https://docs.djangoproject.com/en/).

## Usage
If you haven't set up Orbitscalc locally you might be able to use the web app by going to http://surf1sh.pythonanywhere.com/.
Disclaimer #1: The ground station data there strictly for demonstrational purposes.
Disclaimer #2: Because the website is hosted using a free service, availability and performance might be limited.

When running Orbitscalc locally, create a superuser, in order to access the database.
````
python manage.py createsuperuser
````
There currently is no example data in the data base. Go to http://surf1sh.pythonanywhere.com/ to try out the application.
