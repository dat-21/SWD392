# IV. Implementation

## IV.1 Map Architecture to the Structure of the Project

In the system architecture outlined in Section 3.2, **The MC Hub** system is designed using a **Multi-client / Single-server (RESTful API)** model. It is divided into multiple client types:

- **Web Application** (React.js) — used by Customers, MCs, and Admins
- **Mobile Application** (React Native) — used by Customers and MCs
- **Backend API Server** (Node.js / Express.js) — the single server serving all clients

All clients communicate with the backend through RESTful HTTP endpoints prefixed with `/api/v1/`. Real-time features (Chat) are handled via **Socket.io** on the same server. Data persistence is managed by **MongoDB Atlas** through the **Mongoose ODM**.

### Project Structure

The backend follows a **layered architecture** organized by feature domains:

```
FPT_S7_NodeJS-Backend/
├── .env                          # Environment variables (DB URI, JWT Secret, Cloudinary keys)
├── package.json                  # Dependencies & scripts
├── src/
│   ├── index.js                  # Application entry point, Express & Socket.io setup
│   ├── config/
│   │   └── db.js                 # MongoDB connection configuration
│   ├── models/                   # Mongoose schemas (Data Layer)
│   │   ├── User.js               # User model (client, mc, admin roles)
│   │   ├── MCProfile.js          # MC professional profile
│   │   ├── Booking.js            # Booking transactions
│   │   ├── Review.js             # Client reviews for MCs
│   │   ├── Transaction.js        # Payment transactions (Escrow)
│   │   ├── Schedule.js           # MC availability calendar
│   │   ├── Message.js            # Real-time chat messages
│   │   ├── Notification.js       # Push notifications
│   │   ├── Promo.js              # Promotional codes
│   │   └── WithdrawalRequest.js  # MC withdrawal requests
│   ├── controllers/              # Business Logic Layer
│   │   ├── authController.js     # Authentication (Register, Login, JWT)
│   │   ├── bookingController.js  # Booking CRUD & status management
│   │   ├── mcController.js       # MC profile & search/ranking
│   │   ├── reviewController.js   # Review CRUD & rating calculation
│   │   ├── paymentController.js  # Payment processing & history
│   │   └── adminController.js    # Admin management operations
│   └── routes/                   # API Route Definitions (Presentation Layer)
│       ├── authRoutes.js         # /api/v1/auth/*
│       ├── bookingRoutes.js      # /api/v1/bookings/*
│       ├── mcRoutes.js           # /api/v1/mcs/*
│       ├── reviewRoutes.js       # /api/v1/reviews/*
│       ├── paymentRoutes.js      # /api/v1/payments/*
│       └── adminRoutes.js        # /api/v1/admin/*
```

### Mapping Architecture Layers to Project

| Architecture Layer | Project Component | Description |
|---|---|---|
| **Presentation Layer** | `routes/` | Defines HTTP endpoints, maps URLs to controller functions |
| **Business Logic Layer** | `controllers/` | Contains business rules, validation, data transformation |
| **Data Access Layer** | `models/` | Mongoose schemas/models, database operations via Mongoose ODM |
| **Configuration** | `config/`, `.env` | Database connection, environment variables |
| **Real-time Communication** | `index.js` (Socket.io) | WebSocket for live chat between Client and MC |

---

## IV.2 Map Class Diagram and Interaction Diagram to Code

For the **The MC Hub** system, the Class Diagram entities and their interactions are mapped to **Node.js / Express.js** code following the pattern:

- **Class Diagram Entity** → **Mongoose Model** (Data Layer)
- **Service Interface** → **Service Module** with exported functions (Business Logic)
- **Controller** → **Express Controller** handling HTTP request/response

Below, we demonstrate the mapping using two representative domains: **Booking** and **Review**.

---

### IV.2.1 Booking Domain — Service Interface, Service Class, Controller

#### a) Model — `Booking.js` (mapped from Class Diagram entity "Booking")

The `Booking` entity in the Class Diagram defines associations with `User` (as client and mc), along with attributes such as `eventDate`, `location`, `eventType`, `price`, `status`, and `paymentStatus`. This is mapped directly to a Mongoose schema:

```javascript
// src/models/Booking.js
const mongoose = require('mongoose');

const bookingSchema = new mongoose.Schema({
    client: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    mc: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    eventDate: { type: Date, required: true },
    location: { type: String, required: true },
    eventType: { type: String, required: true },
    specialRequests: { type: String },
    price: { type: Number, required: true },
    status: {
        type: String,
        enum: ['Pending', 'Accepted', 'Completed', 'Cancelled', 'Rejected'],
        default: 'Pending',
    },
    paymentStatus: {
        type: String,
        enum: ['Pending', 'DepositPaid', 'FullyPaid', 'Refunded'],
        default: 'Pending',
    }
}, { timestamps: true });

module.exports = mongoose.model('Booking', bookingSchema);
```

**UML → Code Mapping:**

| UML Class Diagram | Node.js Code |
|---|---|
| `Booking` class | `bookingSchema` + `mongoose.model('Booking', ...)` |
| Association `Booking → User` (client) | `client: { type: ObjectId, ref: 'User' }` |
| Association `Booking → User` (mc) | `mc: { type: ObjectId, ref: 'User' }` |
| Attribute `status: enum` | `status: { type: String, enum: [...] }` |
| Attribute `createdAt`, `updatedAt` | `{ timestamps: true }` (auto-generated) |

#### b) Service Interface — `bookingService.js`

In the sample C# architecture, a **Service Interface** defines the contract for business operations. In Node.js, we achieve the same pattern by exporting a module with clearly defined functions. This acts as the service layer, separating business logic from the controller:

```javascript
// src/services/bookingService.js

const Booking = require('../models/Booking');

/**
 * Service Interface (Contract):
 * - getBookings(query)          → Get filtered list of bookings
 * - getBookingById(id)          → Get single booking details
 * - createBooking(bookingData)  → Create a new booking
 * - updateBookingStatus(id, statusData) → Update booking status
 * - getUserBookings(userId, role)       → Get bookings for a specific user
 */

// Get all bookings with optional filters
const getBookings = async (query = {}) => {
    return await Booking.find(query)
        .populate('mc', 'name avatar')
        .populate('client', 'name avatar');
};

// Get a single booking by ID
const getBookingById = async (id) => {
    return await Booking.findById(id)
        .populate('mc', 'name avatar')
        .populate('client', 'name avatar');
};

// Create a new booking
const createBooking = async (bookingData) => {
    return await Booking.create(bookingData);
};

// Update booking status (Pending → Accepted → Completed / Cancelled)
const updateBookingStatus = async (id, statusData) => {
    const { status, paymentStatus } = statusData;
    return await Booking.findByIdAndUpdate(
        id,
        { status, paymentStatus },
        { new: true, runValidators: true }
    );
};

// Get bookings for a specific user based on their role
const getUserBookings = async (userId, role) => {
    let query = {};
    if (role === 'mc') query.mc = userId;
    else if (role === 'client') query.client = userId;

    return await Booking.find(query)
        .populate('mc', 'name')
        .populate('client', 'name');
};

module.exports = {
    getBookings,
    getBookingById,
    createBooking,
    updateBookingStatus,
    getUserBookings,
};
```

**UML → Code Mapping (Service Interface):**

| UML Operation | Service Function | Description |
|---|---|---|
| `+getBookings(): List<Booking>` | `getBookings(query)` | Retrieve all bookings |
| `+getBookingById(id): Booking` | `getBookingById(id)` | Retrieve a single booking |
| `+createBooking(data): Booking` | `createBooking(bookingData)` | Create new booking |
| `+updateBookingStatus(id, status): Booking` | `updateBookingStatus(id, statusData)` | Update status of a booking |
| `+getUserBookings(userId, role): List<Booking>` | `getUserBookings(userId, role)` | Filter bookings by user |

#### c) Controller — `bookingController.js`

The Controller maps HTTP routes to service calls, handles request/response formatting, and returns appropriate HTTP status codes. This corresponds to the Controller class in the UML diagrams:

```javascript
// src/controllers/bookingController.js
const bookingService = require('../services/bookingService');

// POST /api/v1/bookings — Create a new booking
exports.createBooking = async (req, res) => {
    try {
        const newBooking = await bookingService.createBooking(req.body);
        res.status(201).json({ status: 'success', data: { booking: newBooking } });
    } catch (err) {
        res.status(400).json({ status: 'fail', message: err.message });
    }
};

// GET /api/v1/bookings/:id — Get booking details
exports.getBookingDetails = async (req, res) => {
    try {
        const booking = await bookingService.getBookingById(req.params.id);
        if (!booking) return res.status(404).json({ status: 'fail', message: 'Booking not found' });
        res.status(200).json({ status: 'success', data: { booking } });
    } catch (err) {
        res.status(400).json({ status: 'fail', message: err.message });
    }
};

// PATCH /api/v1/bookings/:id — Update booking status
exports.updateBookingStatus = async (req, res) => {
    try {
        const booking = await bookingService.updateBookingStatus(req.params.id, req.body);
        if (!booking) return res.status(404).json({ status: 'fail', message: 'Booking not found' });
        res.status(200).json({ status: 'success', data: { booking } });
    } catch (err) {
        res.status(400).json({ status: 'fail', message: err.message });
    }
};

// GET /api/v1/bookings — Get bookings for a user
exports.getUserBookings = async (req, res) => {
    try {
        const { userId, role } = req.query;
        const bookings = await bookingService.getUserBookings(userId, role);
        res.status(200).json({ status: 'success', results: bookings.length, data: { bookings } });
    } catch (err) {
        res.status(400).json({ status: 'fail', message: err.message });
    }
};
```

**UML → Code Mapping (Controller):**

| UML Interaction (Sequence Diagram) | Controller Method | HTTP Method & Route |
|---|---|---|
| Client → System: `createBooking()` | `createBooking` | `POST /api/v1/bookings` |
| Client → System: `getBookingDetails(id)` | `getBookingDetails` | `GET /api/v1/bookings/:id` |
| MC → System: `updateBookingStatus(id)` | `updateBookingStatus` | `PATCH /api/v1/bookings/:id` |
| Client → System: `getUserBookings()` | `getUserBookings` | `GET /api/v1/bookings` |

---

### IV.2.2 Review Domain — Service Interface, Service Class, Controller

#### a) Model — `Review.js` (mapped from Class Diagram entity "Review")

```javascript
// src/models/Review.js
const mongoose = require('mongoose');

const reviewSchema = new mongoose.Schema({
    booking: { type: mongoose.Schema.Types.ObjectId, ref: 'Booking', required: true },
    mc: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    client: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    rating: { type: Number, required: true, min: 1, max: 5 },
    comment: { type: String, required: true },
}, { timestamps: true });

module.exports = mongoose.model('Review', reviewSchema);
```

#### b) Service Interface — `reviewService.js`

```javascript
// src/services/reviewService.js

const Review = require('../models/Review');
const Booking = require('../models/Booking');
const MCProfile = require('../models/MCProfile');

/**
 * Service Interface (Contract):
 * - createReview(bookingId, clientId, rating, comment) → Create review & update MC rating
 * - getMCReviews(mcId)         → Get all reviews for an MC
 * - updateReview(id, data)     → Update review within 24h window
 * - deleteReview(id)           → Admin delete inappropriate review
 */

// Create a review for a completed booking and recalculate MC average rating
const createReview = async (bookingId, clientId, rating, comment) => {
    const booking = await Booking.findById(bookingId);
    if (!booking) throw new Error('Booking not found');
    if (booking.status !== 'Completed') throw new Error('Can only review completed bookings');

    const review = await Review.create({
        booking: bookingId,
        mc: booking.mc,
        client: clientId,
        rating,
        comment,
    });

    // Recalculate MC Profile average rating (Smart Ranking component)
    const reviews = await Review.find({ mc: booking.mc });
    const avgRating = reviews.reduce((acc, item) => item.rating + acc, 0) / reviews.length;

    await MCProfile.findOneAndUpdate(
        { user: booking.mc },
        { rating: avgRating, reviewsCount: reviews.length }
    );

    return review;
};

// Get all reviews for a specific MC
const getMCReviews = async (mcId) => {
    return await Review.find({ mc: mcId }).populate('client', 'name avatar');
};

// Update a review (only within 24 hours of creation)
const updateReview = async (id, data) => {
    const review = await Review.findById(id);
    if (!review) throw new Error('Review not found');

    const timeDiff = new Date() - new Date(review.createdAt);
    if (timeDiff > 24 * 60 * 60 * 1000) {
        throw new Error('Review can only be edited within 24 hours');
    }

    return await Review.findByIdAndUpdate(id, data, { new: true });
};

// Delete a review (Admin only)
const deleteReview = async (id) => {
    return await Review.findByIdAndDelete(id);
};

module.exports = {
    createReview,
    getMCReviews,
    updateReview,
    deleteReview,
};
```

#### c) Controller — `reviewController.js`

```javascript
// src/controllers/reviewController.js
const reviewService = require('../services/reviewService');

// POST /api/v1/reviews — Create a new review
exports.createReview = async (req, res) => {
    try {
        const { bookingId, rating, comment } = req.body;
        const clientId = req.user ? req.user._id : req.body.clientId;
        const review = await reviewService.createReview(bookingId, clientId, rating, comment);
        res.status(201).json({ status: 'success', data: { review } });
    } catch (err) {
        res.status(400).json({ status: 'fail', message: err.message });
    }
};

// GET /api/v1/reviews/mc/:mcId — Get all reviews for an MC
exports.getMCReviews = async (req, res) => {
    try {
        const reviews = await reviewService.getMCReviews(req.params.mcId);
        res.status(200).json({ status: 'success', results: reviews.length, data: { reviews } });
    } catch (err) {
        res.status(400).json({ status: 'fail', message: err.message });
    }
};

// PATCH /api/v1/reviews/:id — Update a review (within 24h)
exports.updateReview = async (req, res) => {
    try {
        const updatedReview = await reviewService.updateReview(req.params.id, req.body);
        res.status(200).json({ status: 'success', data: { review: updatedReview } });
    } catch (err) {
        res.status(400).json({ status: 'fail', message: err.message });
    }
};

// DELETE /api/v1/reviews/:id — Admin delete review
exports.deleteReview = async (req, res) => {
    try {
        await reviewService.deleteReview(req.params.id);
        res.status(204).json({ status: 'success', data: null });
    } catch (err) {
        res.status(400).json({ status: 'fail', message: err.message });
    }
};
```

---

### IV.2.3 Summary — UML to Code Mapping Pattern

The general mapping pattern from UML Design to Node.js/Express implementation follows this structure:

```
┌─────────────────────────────────────────────────────────────┐
│                   UML Class Diagram                         │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Entity    │  │  Service     │  │  Controller         │ │
│  │  (Booking, │  │  Interface   │  │  (BookingController) │ │
│  │   Review)  │  │  (IBooking   │  │                      │ │
│  │            │  │   Service)   │  │                      │ │
│  └───────────┘  └──────────────┘  └──────────────────────┘  │
│       ↓                ↓                    ↓               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Node.js / Express Code                     ││
│  │  ┌───────────┐  ┌──────────────┐  ┌─────────────────┐  ││
│  │  │  Mongoose  │  │  Service     │  │  Express         │  ││
│  │  │  Model     │  │  Module      │  │  Controller      │  ││
│  │  │  (.js)     │  │  (.js)       │  │  (.js)           │  ││
│  │  └───────────┘  └──────────────┘  └─────────────────┘  ││
│  │  models/         services/          controllers/         ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

| UML Concept | Node.js Implementation | Location |
|---|---|---|
| **Entity Class** (attributes, associations) | Mongoose Schema + Model | `src/models/*.js` |
| **Association** (1:N, N:M) | `ObjectId` with `ref` (Mongoose populate) | Schema field with `ref: 'ModelName'` |
| **Enumeration** | `enum` validator in schema | `enum: ['Value1', 'Value2']` |
| **Service Interface** | Exported module functions (contract) | `src/services/*.js` |
| **Service Class** (implementation) | Function bodies with Mongoose queries | `src/services/*.js` |
| **Controller Class** | Express middleware `(req, res)` handlers | `src/controllers/*.js` |
| **Route/Endpoint** | Express Router definitions | `src/routes/*.js` |
| **Inheritance** (User → MC, Client) | `role` field + separate `MCProfile` model | `User.role` + `MCProfile` ref |
| **Composition** (Booking has Transactions) | `ObjectId` references between collections | `booking: { ref: 'Booking' }` |

### IV.2.4 Route Definitions — Mapping Endpoints

```javascript
// src/routes/bookingRoutes.js
const express = require('express');
const bookingController = require('../controllers/bookingController');
const router = express.Router();

router.post('/',    bookingController.createBooking);      // Create booking
router.get('/',     bookingController.getUserBookings);     // List user bookings
router.get('/:id',  bookingController.getBookingDetails);   // Get booking detail
router.patch('/:id', bookingController.updateBookingStatus); // Update status

module.exports = router;
```

```javascript
// src/routes/reviewRoutes.js
const express = require('express');
const reviewController = require('../controllers/reviewController');
const router = express.Router();

router.post('/',           reviewController.createReview);   // Create review
router.get('/mc/:mcId',    reviewController.getMCReviews);    // Get MC reviews
router.patch('/:id',       reviewController.updateReview);    // Edit review (24h)
router.delete('/:id',      reviewController.deleteReview);    // Admin delete

module.exports = router;
```

```javascript
// src/index.js — Route Registration
app.use('/api/v1/auth',     authRoutes);
app.use('/api/v1/mcs',      mcRoutes);
app.use('/api/v1/bookings',  bookingRoutes);
app.use('/api/v1/admin',     adminRoutes);
app.use('/api/v1/reviews',   reviewRoutes);
app.use('/api/v1/payments',  paymentRoutes);
```

---

---

# V. Applying Alternative Architecture Patterns

Assuming that the functional requirements remain unchanged, the system is now being expanded to incorporate additional characteristics related to **scalability** and **reusability**. This enhancement allows the system to support the integration of new user-facing applications, including the potential development of a **mobile app (React Native)**.

---

## V.1 Applying the Service-Oriented Architecture (SOA)

### NF-05 Reusability

The system should be built in a way that allows us to easily reuse the same code and features across different platforms. This means that the same functionality can be adapted for both the web and mobile apps, saving time and effort when adding new platforms or updating existing ones.

The current system architecture described in Section 3.2 does not fully meet the requirements of **NF-05**. To address this, the **MCHubData** component must be restructured as a distributed component and designed using a **service-oriented architecture (SOA)**. This adjustment will allow MCHubData to function as a distributed service, thereby enhancing the system's ability to achieve **Reusability, traceability, modularity**, and **effective maintenance**.

The software architecture is redesigned as shown below.

### Figure V-1: Deployment Diagram for The MC Hub System Architecture Based on SOA

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  <<WebBrowser>>          HTTPS        <<Webserver>>                 │
│  <<Client>>          ──────────►     MCHub Customer                 │
│  Customer                             Site (React.js)               │
│                                           │                         │
│                                           │ HTTPS                   │
│  <<WebBrowser>>          HTTPS            ▼                         │
│  <<Client>>          ──────────►  ┌───────────────┐   ADO/Mongoose  │
│  MC                               │ <<Service>>   │──────────►      │
│                                   │  MCHub        │    ┌──────────┐ │
│                                   │  Service      │    │<<DB>>    │ │
│  <<WebBrowser>>          HTTPS    │  (Express API)│    │ MongoDB  │ │
│  <<Client>>          ──────────►  └───────────────┘    │ Atlas    │ │
│  Admin                        ▲           │            └──────────┘ │
│                               │           │                         │
│                         HTTPS │     HTTPS │                         │
│  <<WebBrowser>>    ───────────┘           ▼                         │
│  <<Client>>                        <<Webserver>>                    │
│  Admin                             MCHub Admin                      │
│                                    Site (React.js)                  │
│                                                                     │
│                          HTTPS     ┌─────────────┐                  │
│                        ┌──────────►│MCHub Mobile  │                 │
│  <<MobileApp>>         │           │Customer App  │                 │
│  <<Client>>     ───────┘           │(React Native)│                 │
│  Customer/MC                       └─────────────┘                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Description:**

- **MCHub Customer Site** (React.js Web App): Serves Customers and MCs via web browser
- **MCHub Admin Site** (React.js Web App): Serves Admin users for management
- **MCHub Service** (Express.js API): A single centralized RESTful service that exposes all business logic through APIs (`/api/v1/*`)
- **MCHub Customer App** (React Native): Mobile application for Customers and MCs
- **MongoDB Atlas**: Cloud database storing all collections (Users, Bookings, MCProfiles, Reviews, Transactions, etc.)

All client applications (Web Customer, Web Admin, Mobile App) communicate with the **MCHub Service** through **HTTPS RESTful APIs**, achieving complete separation between presentation and business logic.

### Figure V-2: Class Diagram for The MC Hub System Architecture Based on SOA

```
┌──────────────────────────────────────────────────────────────────────┐
│                      <<Software System>>                             │
│                        MCHub System                                  │
│                                                                      │
│  ┌──────────────┐                                                    │
│  │<<UserInterface>>│                   ┌─────────────────┐           │
│  │<<Client>>     │     1               │  <<Webserver>>  │           │
│  │<<WebBrowser>> │────────────────────►│  MCHub Customer │           │
│  │ Customer      │                     │  Site           │           │
│  └──────────────┘                      └────────┬────────┘           │
│                                                  │                   │
│  ┌──────────────┐                                │ HTTPS             │
│  │<<Client>>     │     1                         ▼                   │
│  │<<UserInterface>>│──────────┐          ┌──────────────┐            │
│  │<<WebBrowser>> │           │          │  <<Service>>  │            │
│  │ MC            │           │          │  MCHub        │            │
│  └──────────────┘            │          │  Service      │            │
│                              ▼          │  (REST API)   │            │
│  ┌──────────────┐    ┌──────────────┐   └──────┬───────┘            │
│  │<<UserInterface>>│  │<<Webserver>> │          │                    │
│  │<<Client>>     │──►│MCHub Admin   │   HTTPS  │                    │
│  │<<WebBrowser>> │   │Site          │◄─────────┘                    │
│  │ Admin         │   └──────────────┘                                │
│  └──────────────┘                                                    │
│                                                                      │
│  ┌──────────────┐                      ┌─────────────────┐           │
│  │<<MobileApp>> │     0..*             │<<DatabaseServer>>│          │
│  │<<Client>>     │────────────────────►│  MongoDB Atlas   │          │
│  │ Customer/MC   │  (via MCHub Service)│  Database        │          │
│  └──────────────┘                      └─────────────────┘           │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Key Relationships:**

- Customer (1) → MCHub Customer Site (Web)
- MC (1) → MCHub Customer Site (Web)
- Admin (1) → MCHub Admin Site (Web)
- Customer/MC (0..*) → MCHub Customer App (Mobile)
- All Sites/Apps → MCHub Service (REST API) → MongoDB Atlas

### Figure V-3: Component Diagram for The MC Hub System Architecture Based on SOA

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   ┌──────────┐                                                      │
│   │ Customer │                    ┌────────────────────┐            │
│   │          │──── 1. HTTP Req ──►│ MCHub Customer     │            │
│   │          │◄── 2. HTTP Res ───│ Site (React.js)    │            │
│   └──────────┘                    └────────┬───────────┘            │
│                                            │                        │
│                                   5. HTTP Request                   │
│   ┌──────────┐                            │        ┌──────────────┐│
│   │ MC       │                            ▼        │              ││
│   │          │──── 3. HTTP Req ──►┌──────────────┐ │  MongoDB     ││
│   │          │◄── 4. HTTP Res ───│ MCHub Service │─┤  Atlas       ││
│   └──────────┘                   │ (Express API) │ │  Database    ││
│                                  └──────┬───────┘ │              ││
│   ┌──────────┐                          │         └──────────────┘│
│   │ Admin    │                   6. HTTP Response                   │
│   │          │──── 5. HTTP Req ──►┌──────────────┐                 │
│   │          │◄── 6. HTTP Res ───│ MCHub Admin   │                 │
│   └──────────┘                   │ Site (React)  │                 │
│                                  └──────────────┘                  │
│   ┌──────────┐                                                     │
│   │ Customer/│                                                     │
│   │ MC Mobile│──── 7. HTTP Req ──► MCHub Service                   │
│   │          │◄── 8. HTTP Res ──── (Same API)                      │
│   └──────────┘                                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Interaction Flow:**

1. **Customer** sends HTTP Request to MCHub Customer Site
2. MCHub Customer Site returns HTTP Response (rendered UI)
3. **MC** sends HTTP Request to MCHub Customer Site (shared web app)
4. MCHub Customer Site returns HTTP Response
5. All web clients send API requests to **MCHub Service** (Express.js)
6–8. MCHub Service queries **MongoDB Atlas** and returns responses
6. **Mobile App** directly calls the same MCHub Service via HTTPS

---

## V.2 Applying Service Discovery Pattern in the Service-Oriented Architecture

Assuming that user requirements change and The MC Hub's scale may later expand into a chain of event services with an increasing number of users, the system will need to address an additional non-functional requirement, **NF-06**, as follows:

### NF-06: Scalability

The system must be designed to accommodate an increasing number of stores and users while maintaining performance and reliability. This includes the ability to scale both **horizontally** and **vertically**. The architecture should support the addition of new stores and handle a growing volume of transactions and concurrent users without significant performance degradation. The system should implement **load balancing** to evenly distribute traffic and employ scalable database solutions to manage increasing amounts of data effectively.

### Figure V-4: Deployment Diagram for The MC Hub System Architecture Based on Microservice Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  <<WebBrowser>>                                         <<Microservice>>     │
│  <<Client>>           HTTPS      <<Webserver>>          Booking Service      │
│  Customer        ──────────────► MCHub Customer ──┐                          │
│                                  Site              │                         │
│                                                    │    <<Microservice>>     │
│  <<WebBrowser>>                                    │    MC Service            │
│  <<Client>>           HTTPS      <<Service>>       │                         │
│  MC              ──────────────► MCHub Service  ◄──┤    <<Microservice>>     │
│                                  Gateway           │    Payment Service      │
│                                  (API Gateway)     │                         │
│  <<WebBrowser>>       HTTPS                        │    <<Microservice>>     │
│  <<Client>>      ──────────────► <<Webserver>>     │    Review Service       │
│  Admin                           MCHub Admin   ──┘                          │
│                                  Site              │    <<Microservice>>     │
│                                                    └──► User & Auth          │
│  <<MobileApp>>        HTTPS      <<Service>>            Service              │
│  <<Client>>      ──────────────► ServiceRegister                             │
│  Customer/MC                     (Consul/Eureka)        <<Microservice>>     │
│                                                         Notification Service │
│                                                                              │
│                                                    ┌─────────────────────┐   │
│                                                    │ <<DatabaseServer>>  │   │
│                                                    │ MongoDB Atlas       │   │
│                                                    │ (Shared / Per-svc)  │   │
│                                                    └─────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Description:**

The system is decomposed into **6 independent microservices**, each responsible for a single bounded context:

| Microservice | Responsibility | Key Models |
|---|---|---|
| **Booking Service** | Booking CRUD, status lifecycle, scheduling | Booking, Schedule |
| **MC Service** | MC profiles, search, ranking algorithm | MCProfile |
| **Payment Service** | Escrow, transactions, withdrawals, promos | Transaction, WithdrawalRequest, Promo |
| **Review Service** | Reviews, ratings, MC score calculation | Review |
| **User & Auth Service** | Registration, login, JWT, role management | User |
| **Notification Service** | Push notifications, email, real-time alerts | Notification, Message |

**Key Infrastructure Components:**

- **API Gateway (MCHub Service Gateway)**: Single entry point for all clients. Routes requests to the appropriate microservice. Handles cross-cutting concerns (authentication, rate limiting, CORS).
- **Service Register (Consul / Eureka)**: Service discovery — each microservice registers itself on startup. The API Gateway queries the registry to find available service instances.
- **Load Balancer**: Distributes incoming requests across multiple instances of each microservice.

### Figure V-5: Class Diagram for The MC Hub System Architecture Based on Microservice Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         <<Software System>>                                │
│                           MCHub System                                     │
│                                                                            │
│  ┌──────────────┐                        ┌───────────────────┐             │
│  │<<UserInterface>>│     1               │  <<Microservice>> │             │
│  │<<Client>>     │─────────────────┐     │  Booking Service  │             │
│  │<<WebBrowser>> │                 │     └───────────────────┘             │
│  │ Customer      │                 │                                       │
│  └──────────────┘                 │     ┌───────────────────┐             │
│                                   │     │  <<Microservice>> │             │
│  ┌──────────────┐                 ▼     │  MC Service       │             │
│  │<<Client>>     │       ┌──────────┐   └───────────────────┘             │
│  │<<UserInterface>>│────►│<<Service>>│                                     │
│  │<<WebBrowser>> │       │ MCHub    │   ┌───────────────────┐             │
│  │ MC            │       │ Service  │──►│  <<Microservice>> │             │
│  └──────────────┘       │ Gateway  │   │  Payment Service  │             │
│                          └──┬───┬──┘   └───────────────────┘             │
│  ┌──────────────┐           │   │                                         │
│  │<<UserInterface>>│        │   │       ┌───────────────────┐             │
│  │<<Client>>     │──────────┘   │       │  <<Microservice>> │             │
│  │<<WebBrowser>> │              │       │  Review Service   │             │
│  │ Admin         │          ┌───┘       └───────────────────┘             │
│  └──────────────┘           │                                              │
│                             │           ┌───────────────────┐             │
│  ┌──────────────┐           ▼           │  <<Microservice>> │             │
│  │<<MobileApp>> │    ┌──────────┐       │  User & Auth      │             │
│  │<<Client>>     │──►│<<Service>>│──────►│  Service          │             │
│  │ Customer/MC   │   │ Service  │       └───────────────────┘             │
│  └──────────────┘   │ Register │                                          │
│                      └──────────┘       ┌───────────────────┐             │
│                                         │  <<Microservice>> │             │
│                                         │  Notification     │             │
│                                         │  Service          │             │
│                                         └───────────────────┘             │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

**Key Relationships:**

- All clients (Customer, MC, Admin, Mobile) → **MCHub Service Gateway** (1 entry point)
- MCHub Service Gateway → **Service Register** (discovers service locations)
- MCHub Service Gateway → Each **Microservice** (routes requests by path/domain)
- Each Microservice → **MongoDB Atlas** (own collection or shared database)

### Figure V-6: Component Diagram for The MC Hub System Architecture Based on Microservice Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        <<Software System>>                                 │
│                          MCHub System                                      │
│                                                                            │
│  ┌──────────────┐                                                          │
│  │<<UserInterface>>│   1. HTTP Request                                     │
│  │ Customer      │─────────────────────────┐                               │
│  └──────────────┘                          │                               │
│                                            ▼                               │
│  ┌──────────────┐              ┌──────────────────┐                        │
│  │<<UserInterface>>│  3. HTTP  │  <<Webserver>>   │    ┌────────────────┐  │
│  │ MC            │──Request──►│  MCHub Customer  │───►│<<Microservice>>│  │
│  └──────────────┘             │  Site            │    │ Booking Service│  │
│                               └──────────────────┘    └────────────────┘  │
│  ┌──────────────┐                      │                                   │
│  │<<UserInterface>>│          5. Request│via Gateway                        │
│  │ Admin         │─────┐              ▼                ┌────────────────┐  │
│  └──────────────┘      │    ┌─────────────────┐       │<<Microservice>>│  │
│                        │    │  <<Service>>    │──────►│ MC Service     │  │
│  ┌──────────────┐      │    │  MCHub Service  │       └────────────────┘  │
│  │<<MobileApp>> │      │    │  Gateway        │                            │
│  │ Customer/MC  │──────┘    │  (API Gateway)  │       ┌────────────────┐  │
│  └──────────────┘           └────────┬────────┘       │<<Microservice>>│  │
│                                      │           ────►│ Payment Service│  │
│                            10. Service│Location       └────────────────┘  │
│                                      │                                     │
│                             ┌────────▼────────┐       ┌────────────────┐  │
│                             │  <<Service>>    │       │<<Microservice>>│  │
│                             │  Service        │──────►│ Review Service │  │
│                             │  Register       │       └────────────────┘  │
│                             │  (Consul)       │                            │
│                             └─────────────────┘       ┌────────────────┐  │
│                                   │                   │<<Microservice>>│  │
│                              11. Discovery            │ User & Auth    │  │
│                                  service              │ Service        │  │
│                                   │                   └────────────────┘  │
│                                   ▼                                        │
│                             13. Health                ┌────────────────┐  │
│                                 Check                 │<<Microservice>>│  │
│                                                       │ Notification   │  │
│                                                       │ Service        │  │
│                                                       └────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

**Interaction Flow (Microservice Architecture):**

1. **Customer** sends HTTP Request to MCHub Customer Site
2. MCHub Customer Site returns HTTP Response (UI)
3. **MC** sends HTTP Request to MCHub Customer Site
4. MCHub Customer Site returns HTTP Response
5. Web clients/Mobile App send API requests to **MCHub Service Gateway**
6. API Gateway queries **Service Register** (Consul/Eureka) for service location
7. Service Register returns the address of the target microservice instance
8. API Gateway forwards the request to the appropriate **Microservice**
9. Microservice processes the request, queries **MongoDB Atlas**
10. Microservice returns response to API Gateway
11. API Gateway returns response to the client
12. **Service Discovery**: Each microservice registers itself with the Service Register on startup and sends periodic heartbeats
13. **Health Check**: Service Register monitors microservice health and removes unhealthy instances

### V.2.1 Load Balancing Architecture

```
                            ┌─────────────────────────┐
                            │     Load Balancer        │
                            │     (Nginx / AWS ALB)    │
                            └──────────┬──────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                   │
              ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐
              │ API Gateway│     │ API Gateway│     │ API Gateway│
              │ Instance 1 │     │ Instance 2 │     │ Instance 3 │
              └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
                    │                  │                   │
        ┌───────────┼──────────────────┼───────────────────┤
        │           │                  │                   │
  ┌─────▼───────┐ ┌─▼──────────┐ ┌────▼────────┐ ┌───────▼──────┐
  │ Booking Svc │ │ MC Svc     │ │ Payment Svc │ │ Review Svc   │
  │ Instance 1  │ │ Instance 1 │ │ Instance 1  │ │ Instance 1   │
  │ Instance 2  │ │ Instance 2 │ │ Instance 2  │ │ Instance 2   │
  │ Instance 3  │ │            │ │             │ │              │
  └─────────────┘ └────────────┘ └─────────────┘ └──────────────┘
```

**Load Balancing Strategy:**

| Strategy | Description | Use Case |
|---|---|---|
| **Round Robin** | Requests distributed sequentially across instances | Default for stateless services (Booking, MC, Review) |
| **Least Connections** | Routes to instance with fewest active connections | Payment Service (long-running transactions) |
| **IP Hash** | Same client IP always routes to same instance | Session-sticky services if needed |
| **Health-based** | Only routes to healthy instances (health check endpoint) | All services — removes failed instances automatically |

### V.2.2 Service Discovery Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                  Service Discovery Flow                      │
│                                                              │
│  1. Service Registration (on startup)                        │
│     ┌──────────────┐    Register(name, host, port)          │
│     │ Booking Svc  │──────────────────────────┐              │
│     │ :3001        │                          │              │
│     └──────────────┘                          ▼              │
│     ┌──────────────┐    Register           ┌─────────────┐  │
│     │ MC Svc       │─────────────────────►│  Service     │  │
│     │ :3002        │                      │  Registry    │  │
│     └──────────────┘                      │  (Consul)    │  │
│     ┌──────────────┐    Register          │              │  │
│     │ Payment Svc  │─────────────────────►│  Registry:   │  │
│     │ :3003        │                      │  booking-svc │  │
│     └──────────────┘                      │  → :3001     │  │
│     ┌──────────────┐    Register          │  mc-svc      │  │
│     │ Review Svc   │─────────────────────►│  → :3002     │  │
│     │ :3004        │                      │  payment-svc │  │
│     └──────────────┘                      │  → :3003     │  │
│     ┌──────────────┐    Register          │  review-svc  │  │
│     │ Auth Svc     │─────────────────────►│  → :3004     │  │
│     │ :3005        │                      │  auth-svc    │  │
│     └──────────────┘                      │  → :3005     │  │
│                                           └──────┬──────┘  │
│  2. Service Lookup (on request)                   │          │
│     ┌──────────────┐   Lookup("booking-svc")     │          │
│     │ API Gateway  │◄────────────────────────────┘          │
│     │              │   Returns: [host:3001]                  │
│     │              │──────── Forward Request ──────►         │
│     └──────────────┘                                         │
│                                                              │
│  3. Heartbeat (periodic)                                     │
│     Each service sends health check every 10s                │
│     If no heartbeat for 30s → mark as unhealthy              │
│     If no heartbeat for 90s → deregister                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### V.2.3 Scalability Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                     Horizontal Scaling Architecture                     │
│                                                                        │
│  ┌──────────┐    ┌──────────┐    ┌─────────────────────────────────┐  │
│  │ Clients  │───►│   CDN    │───►│  Static Assets (React Build)   │  │
│  │ (Web/    │    │(CloudFront)   │  - Customer Site                │  │
│  │  Mobile) │    └──────────┘    │  - Admin Site                   │  │
│  │          │                    └─────────────────────────────────┘  │
│  │          │                                                        │
│  │          │    ┌──────────────────────────────────────────────┐     │
│  │          │───►│         Load Balancer (Nginx / AWS ALB)      │     │
│  └──────────┘    └────────────────────┬─────────────────────────┘     │
│                                       │                               │
│            ┌──────────────────────────┼──────────────────┐            │
│            │                          │                  │            │
│     ┌──────▼──────┐           ┌──────▼──────┐    ┌──────▼──────┐     │
│     │ API Gateway │           │ API Gateway │    │ API Gateway │     │
│     │ Instance 1  │           │ Instance 2  │    │ Instance N  │     │
│     └──────┬──────┘           └──────┬──────┘    └──────┬──────┘     │
│            │          Service Discovery (Consul)         │            │
│            └──────────────────┬───────────────────────────┘            │
│                               │                                       │
│    ┌──────────────────────────┼──────────────────────────────┐        │
│    │                          │                              │        │
│    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │        │
│    │  │Booking Svc  │  │MC Svc       │  │Payment Svc  │    │        │
│    │  │ x3 instances│  │ x2 instances│  │ x2 instances│    │        │
│    │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │        │
│    │         │                │                │            │        │
│    │  ┌──────┴──────┐  ┌─────┴───────┐  ┌─────┴───────┐   │        │
│    │  │Review Svc   │  │Auth Svc     │  │Notification │   │        │
│    │  │ x2 instances│  │ x2 instances│  │Svc x1       │   │        │
│    │  └─────────────┘  └─────────────┘  └─────────────┘   │        │
│    │                  Microservice Layer                    │        │
│    └───────────────────────────┬────────────────────────────┘        │
│                                │                                      │
│                     ┌──────────▼──────────┐                           │
│                     │   MongoDB Atlas     │                           │
│                     │   Replica Set       │                           │
│                     │   ┌───────┐         │                           │
│                     │   │Primary│         │                           │
│                     │   └───┬───┘         │                           │
│                     │   ┌───▼───┐ ┌──────┐│                           │
│                     │   │Second.│ │Second.││                           │
│                     │   └───────┘ └──────┘│                           │
│                     └─────────────────────┘                           │
│                                                                       │
│                     ┌─────────────────────┐                           │
│                     │   Redis Cache       │                           │
│                     │   (Session, Rate    │                           │
│                     │    Limiting, Queue) │                           │
│                     └─────────────────────┘                           │
│                                                                       │
└────────────────────────────────────────────────────────────────────────┘
```

**Scalability Strategies:**

| Strategy | Implementation | Benefit |
|---|---|---|
| **Horizontal Scaling** | Add more instances of any microservice via Docker/Kubernetes | Handle traffic spikes during event seasons |
| **Database Replica Set** | MongoDB Atlas Replica Set (1 Primary + 2 Secondary) | Read scaling, failover, data redundancy |
| **CDN** | CloudFront/CloudFlare for static React assets | Reduce server load, faster page loads globally |
| **Redis Cache** | Cache frequently accessed data (MC listings, popular profiles) | Reduce database queries, sub-millisecond responses |
| **Message Queue** | RabbitMQ/Redis for async tasks (notifications, email) | Decouple services, handle bursts gracefully |
| **Auto-scaling** | Kubernetes HPA (Horizontal Pod Autoscaler) | Scale pods based on CPU/memory/request metrics |

### V.2.4 Comparison: Monolith vs SOA vs Microservice

| Criteria | Current (Monolith) | SOA (V.1) | Microservice (V.2) |
|---|---|---|---|
| **Deployment** | Single Express.js server | Single service + multiple UI apps | Independent services per domain |
| **Scalability** | Scale entire server | Scale service + UI independently | Scale individual microservices |
| **Technology** | All Node.js | All Node.js | Mixed (Node.js, Python for AI, etc.) |
| **Database** | Single MongoDB | Single MongoDB | Shared or per-service databases |
| **Complexity** | Low | Medium | High |
| **Fault Isolation** | One failure = full outage | Better isolation | Best isolation per service |
| **Team Independence** | Single team | UI team + Backend team | Team per microservice |
| **Reusability (NF-05)** | Low — tightly coupled | High — API shared | Highest — each service reusable |
| **Scalability (NF-06)** | Limited | Better | Best — granular scaling |
| **Best For** | MVP / Small scale | Medium scale, multi-platform | Large scale, high availability |
