# Vertical Structure Activity Diagrams (with Swimlanes)

Based on the actual Backend Node.js structure of the system (`controllers`, `services`, `repositories`, `models`), below are the Activity Diagrams with clear swimlanes between the **User Side (Client / Guest / MC / Admin)** and the **System Side (System / Backend API)**. 

---

## UC19 - Update MC Profile

**API Endpoint:** `PUT /api/v1/mc/profile`

```mermaid
flowchart TD
    %% Styling for Start/End
    style Start fill:#333,stroke:#333,stroke-width:2px,color:#fff
    style End1 fill:#333,stroke:#333,stroke-width:2px,color:#fff
    style End2 fill:#333,stroke:#333,stroke-width:2px,color:#fff
    
    subgraph Client [User Side / MC Client]
        Start((Start)) --> U1(Fill out information and click Save Profile Form)
    end

    subgraph System [System Side / Backend API]
        S1(mcController.updateProfile receives Request)
        S2(MCProfileDTO.fromOnboardingRequest validates & sanitizes data)
        S3(Call MCService.updateProfile to handle business logic)
        S4(MCProfileRepository.updateByUserId interacts with Database)
        S5{Database Update<br/>successful?}
        S6(Return Validation/DB Error - HTTP 400)
        S7(Transform data into a new MCProfileDTO)
        S8(Return Success Response - HTTP 200)
    end

    U1 --> S1
    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> S5
    S5 -- No --> S6
    S5 -- Yes --> S7
    S7 --> S8
    
    S6 --> End1((End))
    S8 --> End2((End))
```

---

## UC20 - Upload Media (Showreels)

*Note: The actual Media Upload flow is handled by the Client uploading directly to Cloud Storage first, then sending the URL to the Backend via the update Profile API.*

**API Endpoint:** `PUT /api/v1/mc/profile`

```mermaid
flowchart TD
    style Start fill:#333,stroke:#333,stroke-width:2px,color:#fff
    style End1 fill:#333,stroke:#333,stroke-width:2px,color:#fff
    style End2 fill:#333,stroke:#333,stroke-width:2px,color:#fff

    subgraph Client [User Side / MC Client]
        Start((Start)) --> U1(Upload media file directly to Cloud Storage via SDK)
        U1 --> U2(Receive returned URL from Cloud Storage)
        U2 --> U3(Send Update Profile form with URL in 'media' variable)
    end

    subgraph System [System Side / Backend API]
        S1(mcController.updateProfile receives Request containing URL data)
        S2(MCProfileDTO maps URL into 'showreels' array)
        S3(Call MCService.updateProfile to process saving)
        S4(MCProfileRepository.updateByUserId saves URL to Database)
        S5{Database Save<br/>successful?}
        S6(Return Error - HTTP 400)
        S7(Return successful update - HTTP 200)
    end

    U3 --> S1
    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> S5
    S5 -- No --> S6
    S5 -- Yes --> S7

    S6 --> End1((End))
    S7 --> End2((End))
```

---

## UC21 - View Schedule (Personal Working Schedule)

**API Endpoint:** `GET /api/v1/mc/calendar`

```mermaid
flowchart TD
    style Start fill:#333,stroke:#333,stroke-width:2px,color:#fff
    style End1 fill:#333,stroke:#333,stroke-width:2px,color:#fff
    style End2 fill:#333,stroke:#333,stroke-width:2px,color:#fff

    subgraph Client [User Side / MC Client]
        Start((Start)) --> U1(Access Calendar / Dashboard page)
    end

    subgraph System [System Side / Backend API]
        S1(mcController.getCalendar processes Request)
        S2(Call MCService.getCalendar -> AvailabilityService.getAvailability)
        S3(MCProfileRepository.findByIdentifier verifies MC)
        S4{Does MC Profile<br/>exist?}
        S5(Return error "MC profile not found" - HTTP 400)
        S6(Parallel: Query ScheduleRepository & BookingRepository)
        S7{Database Query<br/>successful?}
        S8(Report system error - HTTP 400)
        S9(Merge / Calculate / Categorize Schedule & Booking)
        S10(Sort by date and return Calendar Data array - HTTP 200)
    end

    U1 --> S1
    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 -- No --> S5
    S4 -- Yes --> S6
    S6 --> S7
    S7 -- No --> S8
    S7 -- Yes --> S9
    S9 --> S10

    S5 --> End1((End))
    S8 --> End1
    S10 --> End2((End))
```

---

## UC22 - Update Busy Schedule

**API Endpoint:** `POST /api/v1/mc/calendar/blockout`

```mermaid
flowchart TD
    style Start fill:#333,stroke:#333,stroke-width:2px,color:#fff
    style End1 fill:#333,stroke:#333,stroke-width:2px,color:#fff
    style End2 fill:#333,stroke:#333,stroke-width:2px,color:#fff

    subgraph Client [User Side / MC Client]
        Start((Start)) --> U1(Select date/time on interface and click Block Date)
    end

    subgraph System [System Side / Backend API]
        S1(mcController.blockDate processes Request)
        S2(MCService.blockDate receives data)
        S3(ScheduleRepository.create saves with "Busy" status)
        S4{Database Save<br/>successful?}
        S5(Return Validation / DB Error - HTTP 400)
        S6(Return new Schedule record - HTTP 201 Created)
    end

    U1 --> S1
    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 -- No --> S5
    S4 -- Yes --> S6

    S5 --> End1((End))
    S6 --> End2((End))
```

---

## UC23 - Set Availability Status

**API Endpoint:** `POST /api/v1/availability`

```mermaid
flowchart TD
    style Start fill:#333,stroke:#333,stroke-width:2px,color:#fff
    style End1 fill:#333,stroke:#333,stroke-width:2px,color:#fff
    style End2 fill:#333,stroke:#333,stroke-width:2px,color:#fff

    subgraph Client [User Side / MC Client]
        Start((Start)) --> U1(Create available/busy status slot on UI)
    end

    subgraph System [System Side / Backend API]
        S1(availabilityController.createAvailability receives Request)
        S2(AvailabilityService.createAvailability handles it)
        S3(MCProfileRepository checks for MC existence)
        S4{Does MC Profile<br/>exist?}
        S5(Return Profile Not Found error - HTTP 400)
        S6(Assign "Busy" or "Available" status based on data)
        S7(ScheduleRepository.create saves information to Database)
        S8{Database Save<br/>successful?}
        S9(Return DB operation error - HTTP 400)
        S10(Return newly created Availability slot - HTTP 201)
    end

    U1 --> S1
    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 -- No --> S5
    S4 -- Yes --> S6
    S6 --> S7
    S7 --> S8
    S8 -- No --> S9
    S8 -- Yes --> S10

    S5 --> End1((End))
    S9 --> End1
    S10 --> End2((End))
```

---

## UC32 - View Users Lists

**API Endpoint:** `GET /api/v1/admin/users`

```mermaid
flowchart TD
    style Start fill:#333,stroke:#333,stroke-width:2px,color:#fff
    style End1 fill:#333,stroke:#333,stroke-width:2px,color:#fff
    style End2 fill:#333,stroke:#333,stroke-width:2px,color:#fff

    subgraph Admin [Admin Side / Admin Client]
        Start((Start)) --> U1(Access User Management page)
    end

    subgraph System [System Side / Backend API]
        S1(adminController.getAllUsers receives Request)
        S2(User Model queries '.find()' to Database)
        S3{Extraction process<br/>successful?}
        S4(Report Error / System Fail - HTTP 400)
        S5(Return Users Array Data - HTTP 200)
    end

    U1 --> S1
    S1 --> S2
    S2 --> S3
    S3 -- No --> S4
    S3 -- Yes --> S5

    S4 --> End1((End))
    S5 --> End2((End))
```

---

## UC33 & UC34 - Lock/Unlock Account & Verify MC

*Both Lock/Unlock account and MC Account Verification use the same User status update API flow in Backend.*

**API Endpoint:** `PATCH /api/v1/admin/users/:id`

```mermaid
flowchart TD
    style Start fill:#333,stroke:#333,stroke-width:2px,color:#fff
    style End1 fill:#333,stroke:#333,stroke-width:2px,color:#fff
    style End2 fill:#333,stroke:#333,stroke-width:2px,color:#fff

    subgraph Admin [Admin Side / Admin Client]
        Start((Start)) --> U1(Click Verify Approval or Lock/Unlock Account button)
    end

    subgraph System [System Side / Backend API]
        S1(adminController.updateUserStatus gets Request)
        S2(Extract isActive, isVerified parameters from request)
        S3(User Model executes findByIdAndUpdate on Database)
        S4{Database Operation<br/>successful?}
        S5(Return DB Error - HTTP 400)
        S6{Check<br/>if User exists?}
        S7(Return 'User not found' error - HTTP 404)
        S8(Return new Database User object - HTTP 200)
    end

    U1 --> S1
    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 -- No --> S5
    S4 -- Yes --> S6
    S6 -- No --> S7
    S6 -- Yes --> S8

    S5 --> End1((End))
    S7 --> End1
    S8 --> End2((End))
```

---

## UC36 - View All Bookings

**API Endpoint:** `GET /api/v1/admin/bookings`

```mermaid
flowchart TD
    style Start fill:#333,stroke:#333,stroke-width:2px,color:#fff
    style End1 fill:#333,stroke:#333,stroke-width:2px,color:#fff
    style End2 fill:#333,stroke:#333,stroke-width:2px,color:#fff

    subgraph Admin [Admin Side / Admin Client]
        Start((Start)) --> U1(Access Booking Management page)
    end

    subgraph System [System Side / Backend API]
        S1(adminController.getAllBookings processes Request)
        S2(Booking Model queries '.find().populate('mc').populate('client')')
        S3{Database Query<br/>successful?}
        S4(Report Server Error - HTTP 400)
        S5(Return populated Bookings List - HTTP 200)
    end

    U1 --> S1
    S1 --> S2
    S2 --> S3
    S3 -- No --> S4
    S3 -- Yes --> S5

    S4 --> End1((End))
    S5 --> End2((End))
```

---

**Note about UC37 (Resolve Disputes):** 
The dispute management feature (ticketing, disputes API) has not currently been developed in the backend source code (`adminController.js`, `adminRoutes.js`), so a standard Diagram cannot be established for the actual processing flow.
