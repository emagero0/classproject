# Peer-to-Peer Lending Platform

This project is a web application built with Django, designed to facilitate peer-to-peer lending. It allows users to register as borrowers or lenders, apply for loans, approve loan applications, make payments, and leave reviews.

## Features

*   **User Authentication:** Users can register and log in as either borrowers or lenders.
*   **Loan Applications:** Borrowers can apply for loans, specifying the amount, purpose, and duration.
*   **Loan Approval:** Lenders can browse pending loan applications and choose to approve them.
*   **Transaction Management:** Borrowers can make payments towards loans, and lenders can track their lending activity.
*  **Reviews and Ratings:** Users can submit reviews about other users, allowing for more informed decisions.
*   **User Dashboards:** Custom dashboards for both borrowers and lenders to view their relevant data.
*   **Chat Functionality:** Integrated chat to enable communication between borrower and lender for specific loans.
*   **Profile management**: Users can set their profile picture and phone number
## Installation and Running Instructions

1. **Clone the Repository:**

   ```bash
   git clone <repository_url>
   cd emagero0-classproject

   python -m venv env
env\Scripts\activate   # On Windows
source env/bin/activate  # On macOS and Linux

python manage.py migrate
*   This creates the database tables using the Django models.

python manage.py createsuperuser
*   Follow the prompts to create an administrative user.

python manage.py collectstatic
python manage.py runserver
* The development server runs on `http://127.0.0.1:8000/` by default. Open this URL in your web browser.
