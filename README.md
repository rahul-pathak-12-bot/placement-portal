# PLACEMENT PORTAL APPLICATION

This is a web-based Placement Portal Application built using Flask, SQLite, HTML, CSS, and Bootstrap.
It allows Admin, Companies, and Students to interact in a structured placement system.


## PROJECT FEATURES

* Role-based authentication (Admin, Company, Student)
* Company registration and admin approval system
* Placement drive creation and management
* Student application system
* Application status tracking (Applied, Shortlisted, Selected, Rejected)
* Placement history for students
* Admin dashboard for managing students, companies, drives, and applications
* Blacklisting system for students and companies
* Clean and responsive UI


## TECHNOLOGIES USED

* Flask (Backend Framework)
* SQLite (Database)
* SQLAlchemy (ORM)
* Flask-Login (Authentication)
* WTForms (Form Validation)
* Bootstrap + CSS (Frontend)



## HOW TO RUN THE PROJECT

Follow the steps below to run the application on your local machine:

1. Extract the ZIP file

   * Unzip the project folder to any location.

2. Open terminal / command prompt

   * Navigate to the project folder.

3. (Optional but recommended) Create virtual environment
   Windows:
   python -m venv venv
   venv\Scripts\activate

   Mac/Linux:
   python3 -m venv venv
   source venv/bin/activate

4. Install required dependencies
   pip install -r requirements.txt

5. Run the application
   python app.py

6. Open browser
   Go to: http://127.0.0.1:5000/



## DEFAULT ADMIN LOGIN

Email: [admin@placement.edu](mailto:admin@placement.edu)
Password: Admin@1234

(Note: Admin is automatically created when the app runs for the first time.)



## PROJECT STRUCTURE

* app.py              → Main Flask application
* models.py           → Database models
* forms.py            → Form classes
* templates/          → HTML templates
* static/             → CSS and assets
* placement.db        → SQLite database
* requirements.txt    → Dependencies



## NOTES

* The database is automatically created when the app runs.
* Do not manually modify the database file.
* Ensure all dependencies are installed before running.