# 🚗 DriveMatch

## 📖 Project Description
DriveMatch is a Django-based web application designed to connect passengers with monthly private drivers. The platform allows passengers to search for available drivers, view driver profiles, book monthly routes, complete payments, view contracts and invoices, communicate with drivers, and submit support tickets.

The system also provides a dedicated driver side, where drivers can register, upload required documents, add vehicle information, manage routes and availability, view trips, track earnings, manage subscriptions, and communicate with passengers.

Guests can access the platform with limited permissions. They can browse general pages, view public information, search or explore available drivers with limited access, and create a passenger or driver account. However, main actions such as booking, messaging, viewing personal bookings, and completing payments require login.

## 👥 Team Members
- Sharifah Aljuhani
- Atheer Alharthi

## ✨ Main Features

### Guest Features
- Browse the landing page
- View general platform information
- Search or explore available drivers with limited access
- Register as a passenger
- Register as a driver
- Sign in

### Passenger Features
- Passenger registration and login
- Email OTP verification
- Driver search
- Driver profile viewing
- Favorite drivers
- Monthly driver booking
- Payment through Moyasar test environment
- Booking details
- Contract viewing
- Invoice viewing
- Driver rating
- Messaging with drivers
- Support tickets and complaints

### Driver Features
- Multi-step driver registration
- Document upload
- Vehicle information management
- Route and availability management
- Subscription plan selection
- Driver dashboard
- Trips and subscribers management
- Earnings overview
- Ratings page
- Driver invoices
- Messaging with passengers

### Admin Features
- Manage passengers and drivers
- Approve or reject driver profiles
- Manage bookings
- Manage payments
- Manage contracts
- Manage invoices
- Manage refunds
- Review complaints and support tickets

## 🛠️ Technologies Used
- Python / Django
- SQLite / PostgreSQL
- HTML, CSS, JavaScript
- Bootstrap / Custom CSS
- Moyasar Payment Gateway (Test Mode)
- Git & GitHub
- Railway (Deployment)

## 📂 Project Structure
DriveMatch/
├── accounts/
├── bookings/
├── drivers/
├── main/
├── messaging/
├── support/
├── DriveMatch/
├── docs/
├── media/
├── static/
├── manage.py
├── README.md
└── .gitignore


## 📄 Project Documentation
- **User Stories:** [https://drive.google.com/file/d/12IdAkSYwQgLDzQShfqBCyuDEGePURd6r/view?usp=drivesdk](https://drive.google.com/file/d/12IdAkSYwQgLDzQShfqBCyuDEGePURd6r/view?usp=drivesdk)
- **UML Diagrams:** [https://drive.google.com/file/d/10YzSvkUs9MMkaLZSZbH7e8-dJW0E6fuY/view?usp=drivesdk](https://drive.google.com/file/d/10YzSvkUs9MMkaLZSZbH7e8-dJW0E6fuY/view?usp=drivesdk)
- **Wireframe:** [https://drive.google.com/file/d/1wKjzfuyjC0YpPnoTovqw9bIQQxV-so10/view?usp=drivesdk](https://drive.google.com/file/d/1wKjzfuyjC0YpPnoTovqw9bIQQxV-so10/view?usp=drivesdk)

## 🔗 Important Links
- **GitHub Repository:** [https://github.com/Athir60/DriveMatch](https://github.com/Athir60/DriveMatch)
- **Live Demo:** [https://drivematch-production.up.railway.app](https://drivematch-production.up.railway.app)

## 🚀 How to Run Locally
```bash
git clone https://github.com/Athir60/DriveMatch.git
cd DriveMatch
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py loaddata initial_data.json
python manage.py createsuperuser
python manage.py runserver