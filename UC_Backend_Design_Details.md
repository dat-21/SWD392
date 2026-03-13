## Detailed Design Analysis based on System Architecture

This is the detailed design and system communication structure for the MC Hub system, built based on the actual source code of the `src/controllers`, `src/services`, `src/dtos`, `src/repositories`, `src/models` directories of the Node.js Backend.

### General Convention for System High-Level Design for all Use Cases

The backend architecture of all Use Cases adheres to the following model:

```mermaid
flowchart TB
    subgraph ClientLayer ["Client Layer"]
        FE[React SPA / Mobile App]
    end
    
    subgraph APILayer ["API Layer"]
        Route[Express Router]
        Auth[Auth Middleware - JWT]
    end
    
    subgraph BusinessLayer ["Business Layer"]
        Ctrl[Controller]
        Svc[Service]
        DTO[Data Transfer Object]
    end
    
    subgraph DataLayer ["Data Access Layer"]
        Repo[Repository]
        Model[Mongoose Model]
    end
    
    subgraph StorageLayer ["Storage Layer"]
        DB[(MongoDB)]
        Cloud[Cloudinary/AWS S3]
    end

    FE -->|HTTP Request| Route
    Route --> Auth
    Auth --> Ctrl
    Ctrl <--> DTO
    Ctrl --> Svc
    Svc --> Repo
    Repo --> Model
    Model --> DB
    FE -.->|Upload Media| Cloud
```

---

## UC19 - Update MC Profile

**Use Case Description:** MC updates professional profile (operating regions, experience, rates, event types, etc.)
**Actor:** MC

### State Diagram
```mermaid
stateDiagram-v2
    [*] --> ViewingProfile: Successful Login
    ViewingProfile --> EditingProfile: Click "Edit"
    EditingProfile --> ValidatingInput: Submit Form (PUT /api/v1/mc/profile)
    ValidatingInput --> EditingProfile: DTO Validation failed
    ValidatingInput --> UpdatingDatabase: DTO is valid
    UpdatingDatabase --> ProfileUpdated: Database updated successfully
    UpdatingDatabase --> ErrorState: Database Error
    ErrorState --> EditingProfile: Retry
    ProfileUpdated --> ViewingProfile: Receive HTTP 200 & Render new data
    ViewingProfile --> [*]
```

### Sequence / Interaction Diagram
```mermaid
sequenceDiagram
    actor MC
    participant FE as Frontend App
    participant Ctrl as mcController
    participant DTO as MCProfileDTO
    participant Svc as MCService
    participant Repo as MCProfileRepository
    participant DB as MongoDB (MCProfile)

    MC->>FE: Fill out profile info & Click Save
    FE->>Ctrl: PUT /api/v1/mc/profile (Body: profileData)
    Ctrl->>DTO: fromOnboardingRequest(req.body)
    DTO-->>Ctrl: sanitizedData
    Ctrl->>Svc: updateProfile(userId, sanitizedData)
    Svc->>Repo: updateByUserId(userId, sanitizedData)
    Repo->>DB: findOneAndUpdate({user: userId}, data)
    DB-->>Repo: updatedProfileDoc
    Repo-->>Svc: updatedProfileDoc
    Svc-->>Ctrl: updatedProfileDoc
    Ctrl->>DTO: new MCProfileDTO(profile)
    DTO-->>Ctrl: formattedResponse
    Ctrl-->>FE: HTTP 200 { status: 'success', data }
    FE-->>MC: Display successful update notification
```

### Integrated Communication Diagram
```mermaid
flowchart LR
    MC((MC)) -->|1. Submit form| FE[Frontend]
    FE -->|2. PUT request| Ctrl[mcController]
    Ctrl -->|3. format request| DTO[MCProfileDTO]
    Ctrl -->|4. call update| Svc[MCService]
    Svc -->|5. trigger| Repo[MCProfileRepository]
    Repo -->|6. execute query| DB[(MongoDB)]
    DB -->|7. return doc| Repo
    Repo -->|8. return data| Svc
    Svc -->|9. return data| Ctrl
    Ctrl -->|10. JSON response| FE
    FE -->|11. Notify user| MC
```

### Detail Design
- **API Endpoint:** `PUT /api/v1/mc/profile`
- **Request Body (Example):** `{ eventsType: ["Wedding"], experience: 5, rates: {min: 100, max: 500} }`
- **Controller:** `mcController.updateProfile`
- **DTO Validation:** `MCProfileDTO.fromOnboardingRequest` maps input variables (e.g., converts `niche` -> `eventTypes`).
- **Database Model:** `MCProfile` (mongoose schema) linked with `User` Model via `user` ref ObjectId.

---

## UC20 - Upload Media

**Use Case Description:** MC uploads files (photos/video showreels) via Frontend directly to Storage Cloud, sending URL back to DB.
**Actor:** MC

### State Diagram
```mermaid
stateDiagram-v2
    [*] --> UploadingToCloud: MC selects file and uploads (Client-side)
    UploadingToCloud --> UploadFailed: Weak network / File too large
    UploadFailed --> [*]: Retry
    UploadingToCloud --> CloudURLReceived: Cloud returns URL (AWS/Cloudinary)
    CloudURLReceived --> UpdatingProfile: Send PUT /api/v1/mc/profile ('media' variable)
    UpdatingProfile --> ErrorState: DB Update Error
    UpdatingProfile --> MediaSaved: DB Updated
    MediaSaved --> [*]
```

### Sequence / Interaction Diagram
```mermaid
sequenceDiagram
    actor MC
    participant FE as Frontend App
    participant Cloud as Cloud Storage (S3/Cloudinary)
    participant Ctrl as mcController
    participant Repo as MCProfileRepository
    participant DB as MongoDB

    MC->>FE: Select Video/Photo & Click Upload
    FE->>Cloud: POST Media File (Direct Upload)
    Cloud-->>FE: Return file URL
    FE->>Ctrl: PUT /api/v1/mc/profile { media: [{ url: "...", type: "video" }] }
    Ctrl->>Repo: udpateByUserId() (via MCService)
    Repo->>DB: Update `showreels` array field
    DB-->>Repo: success
    Repo-->>Ctrl: updatedProfile
    Ctrl-->>FE: HTTP 200 OK
    FE-->>MC: Preview newly uploaded photo/video
```

### Detail Design
- There is no dedicated backend controller to handle form-data file upload (Multer is not used at the profile layer).
- **Database Field:** Saved into `showreels: [ { url: String, type: Enum['image','video'] } ]` variable in `MCProfile`.

---

## UC21 - View Schedule

**Use Case Description:** Function to display the working schedule, consolidating manually blocked schedules and successfully booked Bookings by clients.
**Actor:** MC

### State Diagram
```mermaid
stateDiagram-v2
    [*] --> RequestingCalendar: Open Calendar Dashboard
    RequestingCalendar --> QueryingDB: GET /api/v1/mc/calendar
    QueryingDB --> CalculatingSchedules: Database returns Schedule & Bookings
    CalculatingSchedules --> RenderingUI: Merge and sort events
    RenderingUI --> [*]: Display calendar on screen
```

### Sequence / Interaction Diagram
```mermaid
sequenceDiagram
    actor MC
    participant FE as Frontend Calendar
    participant Ctrl as mcController
    participant AvailSvc as AvailabilityService
    participant SRepo as ScheduleRepository
    participant BRepo as BookingRepository
    participant DB as MongoDB

    MC->>FE: Open Calendar view
    FE->>Ctrl: GET /api/v1/mc/calendar
    Ctrl->>AvailSvc: getAvailability(userId)
    
    par Parallel query
        AvailSvc->>SRepo: findByMCId(userId)
        SRepo->>DB: Schedule.find({mc: userId})
        AvailSvc->>BRepo: findCalendarByMCId(userId)
        BRepo->>DB: Booking.find({mc: userId}).populate()
    end
    
    DB-->>SRepo: list of Manual Schedules
    DB-->>BRepo: list of Bookings
    SRepo-->>AvailSvc: (Busy, Available slots)
    BRepo-->>AvailSvc: (Confirmed Bookings)
    AvailSvc->>AvailSvc: Merge array & Sort by time
    AvailSvc-->>Ctrl: formatted calendar array
    Ctrl-->>FE: JSON Array (isAvailable, status, title...)
    FE-->>MC: Draw colored blocks on Calendar UI
```

### Detail Design
- **Controller:** `mcController.getCalendar`
- Statistics for the Schedule are combined from 2 independent Models: `Schedule` (schedules manually locked by MC as busy) and `Booking` (Actual contracts taking place). Mapped by `AvailabilityService`.

---

## UC22 & UC23 - Update Busy Schedule / Set Availability Status

**Use Case Description:** MC locks schedule (marks busy) for a specific time period (via UC22) or marks Slot as Available (UC23).
**Actor:** MC

*Backend shares the `Schedule` Table to mark status as "Busy" or "Available" for this time period.*

### Sequence / Interaction Diagram
```mermaid
sequenceDiagram
    actor MC
    participant FE as Frontend 
    participant Ctrl as mcController / availabilityController
    participant Svc as MCService / AvailabilitySvc
    participant Repo as ScheduleRepository
    participant DB as MongoDB (Schedule)

    MC->>FE: Select date time -> Mark Busy / Wait for Book
    FE->>Ctrl: POST /api/v1/mc/calendar/blockout (or POST /availability)
    Ctrl->>Svc: blockDate(userId, {date, startTime, endTime})
    Svc->>Repo: create({mc, date, startTime, endTime, status: 'Busy'/'Available'})
    Repo->>DB: Schedule.insert()
    DB-->>Repo: successful doc insert
    Repo-->>Svc: newSchedule
    Svc-->>Ctrl: data
    Ctrl-->>FE: HTTP 201 Created
    FE-->>MC: Change calendar cell color to Red (Busy) or Green (Available)
```

### Detail Design
- **API (Block Date):** `POST /api/v1/mc/calendar/blockout` -> automatically assigns `status = 'Busy'`.
- **API (Set Availability):** `POST /api/v1/availability` -> assigns `status` depending on `isAvailable` flag passed from Client.
- **Model:** `Schedule` contains schema `status: { enum: ["Available", "Booked", "Busy"] }`.

---

## UC32 - View Users Lists

**Use Case Description:** Admin views the list of all Users on the system.
**Actor:** Admin

### Sequence / Interaction Diagram
```mermaid
sequenceDiagram
    actor Admin
    participant FE as Admin Dashboard
    participant Ctrl as adminController
    participant DB as MongoDB (User)

    Admin->>FE: Click "User Management"
    FE->>Ctrl: GET /api/v1/admin/users
    Ctrl->>DB: User.find()
    DB-->>Ctrl: Array of User docs (email, name, role...)
    Ctrl-->>FE: HTTP 200 { data: { users } }
    FE-->>Admin: Table (DataGrid) displaying list
```

---

## UC33 & UC34 - Lock/Unlock Account & Verify MC

**Use Case Description:** Admin verifies MC's profile (Verify = true) or bans violating User (Active = false).
**Actor:** Admin

### State Diagram
```mermaid
stateDiagram-v2
    [*] --> Unverified_Active: Newly created account
    Unverified_Active --> Verified_Active: Admin approves Verify (isVerified = true)
    Verified_Active --> Verified_Banned: Admin locks account (isActive = false)
    Verified_Banned --> Verified_Active: Admin unlocks (isActive = true)
    Unverified_Active --> Unverified_Banned: Admin locks immediately (isActive = false)
```

### Sequence / Interaction Diagram
```mermaid
sequenceDiagram
    actor Admin
    participant FE as Admin UI
    participant Ctrl as adminController
    participant DB as MongoDB (User Model)

    Admin->>FE: Toggle Checkbox (Verify) / Switch (Ban User)
    FE->>Ctrl: PATCH /api/v1/admin/users/:id { isActive: false, isVerified: true }
    Ctrl->>DB: User.findByIdAndUpdate(id, body, {new:true})
    DB-->>Ctrl: updatedUserDoc / Null (if id not found)
    alt User not found
        Ctrl-->>FE: HTTP 404 (User not found)
    else Update successful
        Ctrl-->>FE: HTTP 200 { data: { user } }
        FE-->>Admin: Notification "Status updated successfully"
    end
```

### Detail Design
- Both actions (Lock/Unlock and Verify MC documentation) share 1 Controller function `adminController.updateUserStatus`.
- **Database Fields:** `User.isActive` (Default: true), `User.isVerified` (Default: false). Only changes Boolean through MongoDB Update.

---

## UC36 - View All Bookings

**Use Case Description:** Manages all contract transactions on the system to help Admin track incoming revenue and progress.
**Actor:** Admin

### Sequence / Interaction Diagram
```mermaid
sequenceDiagram
    actor Admin
    participant FE as Admin UI
    participant Ctrl as adminController
    participant DB as MongoDB (Booking Model)

    Admin->>FE: Open "All Bookings Transaction" tab
    FE->>Ctrl: GET /api/v1/admin/bookings
    Ctrl->>DB: Booking.find().populate('mc').populate('client')
    DB-->>Ctrl: Bookings populated with User Data Details
    Ctrl-->>FE: HTTP 200 JSON
    FE-->>Admin: Render table displaying purchase/sale history (Client ⇔ MC)
```

---

## UC37 - Resolve Disputes

_This feature has not materialized in the backend APIs route files (`api/v1/admin`) or `adminController.js` during code check, therefore there is no Detail Design or Sequence Diagram for backend logic. Logic is entirely Missing in Codebase._ 
_Request Backend / PM to issue a new topic to Develop Complaint/Dispute Tracking feature._
