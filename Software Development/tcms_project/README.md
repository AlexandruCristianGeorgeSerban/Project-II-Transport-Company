# Transport Company Management System (TCMS)

## Project Overview
The Transport Company Management System is a client-server web application designed to help a commercial transport company organize its merchandise fleet, staff, and transport requests. It features dedicated portals for Administrators, Staff (Logistics), and Customers.

## Features
* **Role-Based Access Control:** Secure authentication for Admins, Staff, and Customers.
* **Fleet & Driver Management:** Administrators can register vehicles and manage driver profiles.
* **Client Portal:** Customers (13+ years old) can submit detailed transport requests and view statuses.
* **Smart Allocation:** Staff can filter available resources based on cargo capacity constraints and assign drivers.
* **Automated Quoting:** Dynamic price generation based on distance and cargo specifications.

## Tech Stack
* **Backend:** Python 3.14.x, Flask 3.1.x
* **Frontend:** HTML5, CSS3, JavaScript (ES2025), Bootstrap 5.3
* **Database:** SQLite 3

## Local Setup Instructions
1. Clone the repository: `git clone <your-repo-url>`
2. Navigate into the folder: `cd tcms_project`
3. Activate the virtual environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. Install dependencies: `pip install -r requirements.txt`
5. Run the application: `python run.py`