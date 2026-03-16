# Detailed Design Analysis based on System Architecture

This is the detailed design and system communication structure for the MC Hub system, built strictly based on the actual source code of the `src/controllers`, `src/services`, `src/dtos`, `src/repositories`, `src/models` directories of the Node.js Backend. Every Use Case (UC) is fully separated and includes all requested diagrams.

---

## UC19 - Update MC Profile

### 1. Use Case Description

**Name:** Update MC Profile
**Actor:** MC
**Description:** MC updates their professional profile (operating regions, experience, rates, event types, biography, etc.). The backend maps the raw input using a Data Transfer Object (DTO) before updating the database.

### 2. State Diagram

```mermaid
stateDiagram-v2
    [*] --> ViewingProfile : "Successful Login"
    ViewingProfile --> EditingProfile : "Click 'Edit Profile'"
    EditingProfile --> ValidatingInput : "Submit Form (PUT /api/v1/mc/profile)"
    ValidatingInput --> EditingProfile : "DTO Validation failed"
    ValidatingInput --> UpdatingDatabase : "DTO is valid"
    UpdatingDatabase --> ProfileUpdated : "Database updated successfully"
    UpdatingDatabase --> ErrorState : "Database Error"
    ErrorState --> EditingProfile : "Retry"
    ProfileUpdated --> ViewingProfile : "Receive HTTP 200 & Render new data"
    ViewingProfile --> [*]
```

### 3. Interaction / Sequence Diagram

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

### 4. Integrated Communication Diagram

```mermaid
flowchart LR
    MC((MC)) -->|1. Submit form| FE[Frontend]
    FE -->|2. PUT request| Ctrl[mcController]
    Ctrl -->|3. format request| DTO[MCProfileDTO]
    Ctrl -->|4. call service| Svc[MCService]
    Svc -->|5. trigger update| Repo[MCProfileRepository]
    Repo -->|6. execute query| DB[(MongoDB)]
    DB -->|7. return updated doc| Repo
    Repo -->|8. return doc| Svc
    Svc -->|9. return doc| Ctrl
    Ctrl -->|10. JSON response| FE
    FE -->|11. Notify user| MC
```

### 5. Detail Design

**Figure III-4.19** Detailed Design Classes for UC: Update MC Profile

| Component | Detail |
|-----------|--------|
| **API Endpoint** | `PUT /api/v1/mc/profile` |
| **Request Body** | `{ niche: "Wedding", experience: 5, rates: {min: 100, max: 500}, languages: ["EN", "VN"] }` |
| **Controller** | `mcController.updateProfile(req, res)` |
| **DTO** | `MCProfileDTO.fromOnboardingRequest` maps input variables (e.g., converts `niche` → `eventTypes`) |
| **Service** | `MCService.updateProfile(userId, sanitizedData)` |
| **Repository** | `MCProfileRepository.updateByUserId(userId, data)` |
| **Database Query** | `MCProfile.findOneAndUpdate({ user: userId }, data)` |
| **Database Model** | `MCProfile` linked with `User` Model via `user` ref ObjectId |
| **Response** | Formatted via `new MCProfileDTO(profile)` → HTTP 200 `{ status: 'success', data }` |

### 6. System High-Level Design

```mermaid
flowchart TB
    subgraph ClientLayer ["Client Layer"]
        FE[React SPA]
    end
    subgraph APILayer ["API Layer"]
        Route[Express Router]
        Auth[JWT Middleware]
    end
    subgraph BusinessLayer ["Business Layer"]
        Ctrl[mcController]
        DTO[MCProfileDTO]
        Svc[MCService]
    end
    subgraph DataLayer ["Data Access Layer"]
        Repo[MCProfileRepository]
        Model[MCProfile Model]
    end
    subgraph StorageLayer ["Storage Layer"]
        DB[(MongoDB)]
    end

    FE -->|PUT Request| Route
    Route --> Auth --> Ctrl
    Ctrl <--> DTO
    Ctrl --> Svc --> Repo --> Model --> DB
```

---

## UC20 - Upload Media

### 1. Use Case Description

**Name:** Upload Media
**Actor:** MC
**Description:** MC uploads media files (photos/video showreels). The Client directly uploads files to a Cloud Storage service, receives the URLs, and submits them to the backend via the Profile update API.

### 2. State Diagram

```mermaid
stateDiagram-v2
    [*] --> UploadingToCloud : "MC selects file and uploads (Client-side)"
    UploadingToCloud --> UploadFailed : "Weak network / File too large"
    UploadFailed --> [*] : "Retry"
    UploadingToCloud --> CloudURLReceived : "Cloud returns URL (AWS/Cloudinary)"
    CloudURLReceived --> UpdatingProfile : "Send PUT /api/v1/mc/profile ('media' var)"
    UpdatingProfile --> ErrorState : "DB Update Error"
    UpdatingProfile --> MediaSaved : "DB Updated successfully"
    MediaSaved --> [*]
```

### 3. Interaction / Sequence Diagram

```mermaid
sequenceDiagram
    actor MC
    participant FE as Frontend App
    participant Cloud as Cloud Storage (S3 / Cloudinary)
    participant Ctrl as MCController
    participant Svc as MCService
    participant Repo as MCProfileRepository
    participant DB as MongoDB

    MC->>FE: Select Video/Photo & Click Upload
    FE->>Cloud: POST Media File (Direct SDK Upload)
    Cloud-->>FE: Return file URL
    FE->>Ctrl: PUT /api/v1/mc/profile { media: [{ url: "...", type: "video" }] }
    Ctrl->>Svc: updateProfile()
    Svc->>Svc: Process business logic & map media into showreels
    Svc->>Repo: updateByUserId()
    Repo->>DB: Update showreels array field
    DB-->>Repo: Returns success
    Repo-->>Svc: Returns updated profile
    Svc-->>Ctrl: Returns updated profile
    Ctrl-->>FE: HTTP 200 OK (updated profile data)
    FE-->>MC: Display preview of the newly uploaded photo/video
```

### 4. Integrated Communication Diagram

```mermaid
flowchart LR
    MC((MC)) -->|1. Upload File| FE[Frontend]
    FE -->|2. Direct Upload via SDK| Cloud[Cloud Storage]
    Cloud -->|3. URL Returned| FE
    FE -->|4. PUT Request| Ctrl[mcController]
    Ctrl -->|5. call repo via Service| Repo[MCProfileRepository]
    Repo -->|6. execute query| DB[(MongoDB)]
    DB -->|7. return doc| Repo
    Repo -->|8. return data| Ctrl
    Ctrl -->|9. JSON response| FE
    FE -->|10. Update Gallery| MC
```

### 5. Detail Design

**Figure III-4.20** Detailed Design Classes for UC: Upload Media

| Component | Detail |
|-----------|--------|
| **Mechanism** | No dedicated backend file upload handler. The backend solely stores URL strings received from the client. |
| **API Endpoint** | `PUT /api/v1/mc/profile` |
| **Request Body** | `{ media: [{ url: "https://...", type: "video" }] }` |
| **Controller** | `mcController.updateProfile(req, res)` |
| **Service** | `MCService.updateProfile()` — maps `media` array into `showreels` field |
| **Repository** | `MCProfileRepository.updateByUserId()` |
| **Database Query** | Update `showreels` array field in `MCProfile` collection |
| **Database Field** | `showreels: [ { url: String, type: Enum['image','video'] } ]` |
| **External Dependency** | Cloudinary / AWS S3 (client-side SDK upload only) |
| **Response** | HTTP 200 OK with updated profile data |

### 6. System High-Level Design

```mermaid
flowchart TB
    subgraph ClientLayer ["Client Layer"]
        FE[React SPA]
    end
    subgraph External ["External Cloud"]
        Cloud[Cloudinary / AWS S3]
    end
    subgraph BusinessLayer ["Business Layer"]
        Ctrl[mcController]
    end
    subgraph DataLayer ["Data Access Layer"]
        Repo[MCProfileRepository]
    end
    subgraph StorageLayer ["Storage Layer"]
        DB[(MongoDB)]
    end

    FE -->|Upload Media| Cloud
    FE -->|Pass URL| Ctrl
    Ctrl --> Repo --> DB
```

---

## UC21 - View Schedule

### 1. Use Case Description

**Name:** View Schedule
**Actor:** MC
**Description:** Consolidates data to display the working schedule, merging manually blocked schedules (Busy/Available) with actually confirmed Bookings.

### 2. State Diagram

```mermaid
stateDiagram-v2
    [*] --> RequestingCalendar : "Open Calendar Dashboard"
    RequestingCalendar --> QueryingDB : "GET /api/v1/mc/calendar"
    QueryingDB --> DBError : "Database failure"
    DBError --> RequestingCalendar : "Retry"
    QueryingDB --> CalculatingSchedules : "DB returns Schedule & Bookings"
    CalculatingSchedules --> RenderingUI : "Merge and sort events"
    RenderingUI --> [*]: Display calendar on screen
```

### 3. Interaction / Sequence Diagram

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

    par Schedule Query
        AvailSvc->>SRepo: findByMCId(userId)
        SRepo->>DB: Schedule.find({mc: userId})
    and Booking Query
        AvailSvc->>BRepo: findCalendarByMCId(userId)
        BRepo->>DB: Booking.find({mc: userId}).populate()
    end

    DB-->>SRepo: list of Manual Schedules
    DB-->>BRepo: list of Confirmed Bookings
    SRepo-->>AvailSvc: (Busy, Available slots)
    BRepo-->>AvailSvc: (Bookings)
    AvailSvc->>AvailSvc: Merge arrays & Sort by date/time
    AvailSvc-->>Ctrl: formatted calendar array
    Ctrl-->>FE: JSON Array Response
    FE-->>MC: Draw colored blocks on Calendar UI
```

### 4. Integrated Communication Diagram

```mermaid
flowchart LR
    MC((MC)) -->|1. Request Calendar| FE[Frontend]
    FE -->|2. GET Request| Ctrl[mcController]
    Ctrl -->|3. call| Svc[AvailabilitySvc]
    Svc -->|4. fetch parallel| SRepo[ScheduleRepo]
    Svc -->|4. fetch parallel| BRepo[BookingRepo]
    SRepo -->|5. query| DB[(MongoDB)]
    BRepo -->|5. query| DB
    DB -->|6. schedules| SRepo
    DB -->|6. bookings| BRepo
    SRepo -->|7. results| Svc
    BRepo -->|7. results| Svc
    Svc -->|8. merged array| Ctrl
    Ctrl -->|9. JSON Response| FE
    FE -->|10. Render View| MC
```

### 5. Detail Design

**Figure III-4.21** Detailed Design Classes for UC: View Schedule

| Component | Detail |
|-----------|--------|
| **API Endpoint** | `GET /api/v1/mc/calendar` |
| **Controller** | `mcController.getCalendar(req, res)` |
| **Service** | `AvailabilityService.getAvailability(userId)` — merges and sorts both data sources |
| **Repository 1** | `ScheduleRepository.findByMCId(userId)` → `Schedule.find({ mc: userId })` |
| **Repository 2** | `BookingRepository.findCalendarByMCId(userId)` → `Booking.find({ mc: userId }).populate()` |
| **Merge Logic** | Both arrays merged and sorted by date/time inside `AvailabilityService` |
| **Data Sources** | `Schedule` model (manual slots) + `Booking` model (confirmed bookings) |
| **Response** | HTTP 200 with unified calendar JSON array |

### 6. System High-Level Design

```mermaid
flowchart TB
    subgraph ClientLayer ["Client Layer"]
        FE[Calendar Component]
    end
    subgraph BusinessLayer ["Business Layer"]
        Ctrl[mcController]
        Svc[AvailabilityService]
    end
    subgraph DataLayer ["Data Access Layer"]
        SRepo[ScheduleRepository]
        BRepo[BookingRepository]
    end
    subgraph StorageLayer ["Storage Layer"]
        DB[(MongoDB)]
    end

    FE --> Ctrl --> Svc
    Svc --> SRepo --> DB
    Svc --> BRepo --> DB
```

---

## UC22 - Update Busy Schedule

### 1. Use Case Description

**Name:** Update Busy Schedule
**Actor:** MC
**Description:** MC locks their schedule, marking specific dates and time slots as explicitly "Busy" so clients cannot book them in those slots.

### 2. State Diagram

```mermaid
stateDiagram-v2
    [*] --> ViewingCalendar : "Access Calendar UI"
    ViewingCalendar --> SelectingSlot : "Click to Block Date"
    SelectingSlot --> Submitting : "POST /api/v1/mc/calendar/blockout"
    Submitting --> ErrorState : "Conflict / Validation Error"
    ErrorState --> SelectingSlot : "Fix input"
    Submitting --> SlotSaved : "Success"
    SlotSaved --> [*]: Calendar displays Red Block
```

### 3. Interaction / Sequence Diagram

```mermaid
sequenceDiagram
    actor MC
    participant FE as Frontend
    participant Ctrl as mcController
    participant Svc as MCService
    participant Repo as ScheduleRepository
    participant DB as MongoDB (Schedule)

    MC->>FE: Select date/time -> Click "Block Date"
    FE->>Ctrl: POST /api/v1/mc/calendar/blockout
    Ctrl->>Svc: blockDate(userId, {date, startTime, endTime})
    Svc->>Repo: create({mc, date, startTime, endTime, status: 'Busy'})
    Repo->>DB: Schedule.insert()
    DB-->>Repo: successful doc insert
    Repo-->>Svc: newSchedule
    Svc-->>Ctrl: data
    Ctrl-->>FE: HTTP 201 Created
    FE-->>MC: Show new Busy schedule chunk on UI
```

### 4. Integrated Communication Diagram

```mermaid
flowchart LR
    MC((MC)) -->|1. Submit Block| FE[Frontend]
    FE -->|2. POST Request| Ctrl[mcController]
    Ctrl -->|3. Process| Svc[MCService]
    Svc -->|4. Create| Repo[ScheduleRepository]
    Repo -->|5. Insert| DB[(MongoDB)]
    DB -->|6. Return| Repo
    Repo -->|7. Map| Svc
    Svc -->|8| Ctrl
    Ctrl -->|9. JSON Response| FE
    FE -->|10. Update UI| MC
```

### 5. Detail Design

**Figure III-4.22** Detailed Design Classes for UC: Update Busy Schedule

| Component | Detail |
|-----------|--------|
| **API Endpoint** | `POST /api/v1/mc/calendar/blockout` |
| **Request Body** | `{ date: "2026-03-20", startTime: "09:00", endTime: "17:00" }` |
| **Controller** | `mcController.blockDate(req, res)` |
| **Service** | `MCService.blockDate(userId, { date, startTime, endTime })` |
| **Repository** | `ScheduleRepository.create({ mc, date, startTime, endTime, status: 'Busy' })` |
| **Database Query** | `Schedule.insert()` |
| **Database Model** | `Schedule` — document created with `status = "Busy"` |
| **Response** | HTTP 201 Created |

### 6. System High-Level Design

```mermaid
flowchart TB
    subgraph ClientLayer ["Client Layer"]
        FE[Frontend Block Form]
    end
    subgraph BusinessLayer ["Business Layer"]
        Ctrl[mcController]
        Svc[MCService]
    end
    subgraph DataLayer ["Data Access Layer"]
        Repo[ScheduleRepository]
        Model[Schedule Model]
    end
    subgraph StorageLayer ["Storage Layer"]
        DB[(MongoDB)]
    end

    FE --> Ctrl --> Svc --> Repo --> Model --> DB
```

---

## UC23 - Set Availability Status

### 1. Use Case Description

**Name:** Set Availability Status
**Actor:** MC
**Description:** MC manually sets custom slot statuses (Available / Busy) depending on availability, allowing granular control rather than just full-time blocking.

### 2. State Diagram

```mermaid
stateDiagram-v2
    [*] --> ViewingAvailabilityUI : "Access Availability Modal"
    ViewingAvailabilityUI --> CreatingSlot : "Toggle Available/Busy status"
    CreatingSlot --> Validating : "POST /api/v1/availability"
    Validating --> ErrorState : "DB Error"
    ErrorState --> ViewingAvailabilityUI : "Reject"
    Validating --> Updated : "Saved to DB"
    Updated --> [*] : "Reflect slot changes on UI"
```

### 3. Interaction / Sequence Diagram

```mermaid
sequenceDiagram
    actor MC
    participant FE as Frontend
    participant Ctrl as availabilityController
    participant Svc as AvailabilityService
    participant Repo as ScheduleRepository
    participant DB as MongoDB (Schedule)

    MC->>FE: Toggle status for a period (Avail/Busy)
    FE->>Ctrl: POST /api/v1/availability (Body: {isAvailable})
    Ctrl->>Svc: createAvailability(userId, slotData)
    Svc->>Svc: compute status = isAvailable ? "Available" : "Busy"
    Svc->>Repo: create({mc, date, status, ...})
    Repo->>DB: Schedule.insert()
    DB-->>Repo: inserted schedule slot
    Repo-->>Svc: slot
    Svc-->>Ctrl: slot
    Ctrl-->>FE: HTTP 201 Created
    FE-->>MC: Visually display new availability slots
```

### 4. Integrated Communication Diagram

```mermaid
flowchart LR
    MC((MC)) -->|1. Submit Availability| FE[Frontend]
    FE -->|2. POST Request| Ctrl[availabilityController]
    Ctrl -->|3. Process| Svc[AvailabilityService]
    Svc -->|4. Create| Repo[ScheduleRepository]
    Repo -->|5. Insert| DB[(MongoDB)]
    DB -->|6. Return| Repo
    Repo -->|7. Data| Svc
    Svc -->|8. Data| Ctrl
    Ctrl -->|9. JSON Response| FE
    FE -->|10. Render UI| MC
```

### 5. Detail Design

**Figure III-4.23** Detailed Design Classes for UC: Set Availability Status

| Component | Detail |
|-----------|--------|
| **API Endpoint** | `POST /api/v1/availability` |
| **Request Body** | `{ isAvailable: true/false, date: "...", startTime: "...", endTime: "..." }` |
| **Controller** | `availabilityController.createAvailability(req, res)` |
| **Service** | `AvailabilityService.createAvailability(userId, slotData)` |
| **Business Logic** | `status = isAvailable ? "Available" : "Busy"` (computed inside Service) |
| **Repository** | `ScheduleRepository.create({ mc, date, status, startTime, endTime })` |
| **Database Query** | `Schedule.insert()` |
| **Database Model** | `Schedule` — status determined by `isAvailable` boolean from frontend |
| **Response** | HTTP 201 Created |

### 6. System High-Level Design

```mermaid
flowchart TB
    subgraph ClientLayer ["Client Layer"]
        FE[Frontend SPA]
    end
    subgraph BusinessLayer ["Business Layer"]
        Ctrl[availabilityCtrl]
        Svc[AvailabilityService]
    end
    subgraph DataLayer ["Data Access Layer"]
        Repo[ScheduleRepository]
        Model[Schedule Model]
    end
    subgraph StorageLayer ["Storage Layer"]
        DB[(MongoDB)]
    end

    FE --> Ctrl --> Svc --> Repo --> Model --> DB
```

---

## UC32 - View Users Lists

### 1. Use Case Description

**Name:** View Users Lists
**Actor:** Admin
**Description:** The Administrator views a complete list of all Users registered on the system (both Clients and MCs) to manage them.

### 2. State Diagram

```mermaid
stateDiagram-v2
    [*] --> Dashboard : "Admin logs into Admin Panel"
    Dashboard --> LoadingUsers : "Click 'User Management'"
    LoadingUsers --> RenderedList : "API Returns Data"
    LoadingUsers --> ErrorState : "Request Failure"
    ErrorState --> Dashboard : "Retry"
    RenderedList --> [*] : "Admin views table"
```

### 3. Interaction / Sequence Diagram

```mermaid
sequenceDiagram
    actor Admin
    participant FE as Admin Dashboard
    participant Ctrl as adminController
    participant Svc as UserService
    participant Repo as UserRepository
    participant DB as MongoDB (User Model)

    Admin->>FE: Access "Users List" Tab
    FE->>Ctrl: GET /api/v1/admin/users
    Ctrl->>Svc: getAllUsers()
    Svc->>Repo: findAll()
    Repo->>DB: User.find()
    DB-->>Repo: Array of User docs
    Repo-->>Svc: Array of users
    Svc-->>Ctrl: Array of users
    Ctrl-->>FE: HTTP 200 { status: 'success', data: { users } }
    FE-->>Admin: Render DataGrid Table of users
```

### 4. Integrated Communication Diagram

```mermaid
flowchart LR
    Admin((Admin)) -->|1. Click Tab| FE[Admin Frontend]
    FE -->|2. GET Request| Ctrl[adminController]
    Ctrl -->|3. call service| Svc[UserService]
    Svc -->|4. call repo| Repo[UserRepository]
    Repo -->|5. execute query| DB[(MongoDB)]
    DB -->|6. Array of Users| Repo
    Repo -->|7. return data| Svc
    Svc -->|8. return data| Ctrl
    Ctrl -->|9. JSON Response| FE
    FE -->|10. Render DataGrid| Admin
```

### 5. Detail Design

**Figure III-4.32** Detailed Design Classes for UC: View Users Lists

| Component | Detail |
|-----------|--------|
| **API Endpoint** | `GET /api/v1/admin/users` |
| **Controller** | `adminController.getAllUsers(req, res)` |
| **Service** | `UserService.getAllUsers()` |
| **Repository** | `UserRepository.findAll()` |
| **Database Query** | `User.find()` — fetches all registered users (all roles) |
| **Business Logic** | No complex filtering; data rendering is managed by the client-side DataGrid table |
| **Response** | HTTP 200 `{ status: 'success', data: { users } }` |

### 6. System High-Level Design

```mermaid
flowchart TB
    subgraph ClientLayer ["Client Layer"]
        FE[Admin Dashboard UI]
    end
    subgraph APILayer ["API Layer"]
        Route[Admin Routes]
    end
    subgraph BusinessLayer ["Business Layer"]
        Ctrl[adminController]
        Svc[UserService]
    end
    subgraph DataLayer ["Data Access Layer"]
        Repo[UserRepository]
        DB[(MongoDB - User Collection)]
    end

    FE --> Route --> Ctrl --> Svc --> Repo --> DB
```

---

## UC33 - Lock/Unlock Account

### 1. Use Case Description

**Name:** Lock/Unlock Account
**Actor:** Admin
**Description:** Admin changes the account accessibility status of any User by modifying the `isActive` flag, practically banning them or giving them access back to the system.

### 2. State Diagram

```mermaid
stateDiagram-v2
    [*] --> ViewingUser : Admin opens user row
    ViewingUser --> ModifyingStatus : Admin toggles Lock Account switch
    ModifyingStatus --> Requesting : Send PATCH request to update isActive
    Requesting --> Saved : Account Banned Successfully
    Requesting --> Failed : Unsuccessful execution
    Failed --> ViewingUser : Return
    Saved --> [*] : Visual confirmation
```

### 3. Interaction / Sequence Diagram

```mermaid
sequenceDiagram
    actor Admin
    participant FE as Admin UI
    participant Ctrl as adminController
    participant Svc as UserService
    participant Repo as UserRepository
    participant DB as MongoDB (User Model)

    Admin->>FE: Toggle Switch (Lock/Unlock User)
    FE->>Ctrl: PATCH /api/v1/admin/users/:id { isActive: false/true }
    Ctrl->>Svc: updateUserStatus(id, { isActive })
    Svc->>Repo: updateById(id, { isActive })
    Repo->>DB: User.findByIdAndUpdate(id, {isActive}, {new:true})
    DB-->>Repo: updatedUserDoc / Null
    Repo-->>Svc: updatedUserDoc / Null
    Svc-->>Ctrl: updatedUserDoc / Null
    alt User not found
        Ctrl-->>FE: HTTP 404 (User not found)
    else Update successful
        Ctrl-->>FE: HTTP 200 { data: { user } }
        FE-->>Admin: Notification "Status updated successfully"
    end
```

### 4. Integrated Communication Diagram

```mermaid
flowchart LR
    Admin((Admin)) -->|1. Toggle Switch| FE[Admin Frontend]
    FE -->|2. PATCH Request| Ctrl[adminController]
    Ctrl -->|3. call service| Svc[UserService]
    Svc -->|4. call repo| Repo[UserRepository]
    Repo -->|5. findByIdAndUpdate| DB[(MongoDB)]
    DB -->|6. Updated Doc| Repo
    Repo -->|7. return data| Svc
    Svc -->|8. return data| Ctrl
    Ctrl -->|9. JSON Response| FE
    FE -->|10. Show Alert| Admin
```

### 5. Detail Design

**Figure III-4.33** Detailed Design Classes for UC: Lock/Unlock Account

| Component | Detail |
|-----------|--------|
| **API Endpoint** | `PATCH /api/v1/admin/users/:id` |
| **Request Body** | `{ isActive: true / false }` |
| **Controller** | `adminController.updateUserStatus(req, res)` |
| **Service** | `UserService.updateUserStatus(id, { isActive })` |
| **Repository** | `UserRepository.updateById(id, { isActive })` |
| **Database Query** | `User.findByIdAndUpdate(id, { isActive }, { new: true })` |
| **Target Field** | `isActive` boolean on the `User` schema |
| **Response** | HTTP 200 `{ data: { user } }` on success · HTTP 404 if user not found |

### 6. System High-Level Design

```mermaid
flowchart TB
    subgraph ClientLayer ["Client Layer"]
        FE[Admin Dashboard UI]
    end
    subgraph BusinessLayer ["Business Layer"]
        Ctrl[adminController]
        Svc[UserService]
    end
    subgraph DataLayer ["Data Access Layer"]
        Repo[UserRepository]
        DB[(MongoDB)]
    end

    FE --> Ctrl --> Svc --> Repo --> DB
```

---

## UC34 - Verify MC

### 1. Use Case Description

**Name:** Verify MC
**Actor:** Admin
**Description:** The Administrator verifies and authenticates the expertise/identity documents of an MC, altering the `isVerified` status of their account.

### 2. State Diagram

```mermaid
stateDiagram-v2
    [*] --> Unverified : New MC registered
    Unverified --> Appraising : Admin reviews submitted info
    Appraising --> Confirming : Admin clicks Verify Account
    Confirming --> Processing : Send PATCH request to update isVerified
    Processing --> Success : Successfully Approved
    Processing --> Failed : Database Error
    Failed --> Appraising : Re-retry
    Success --> [*] : Account marked Verified
```

### 3. Interaction / Sequence Diagram

```mermaid
sequenceDiagram
    actor Admin
    participant FE as Admin UI
    participant Ctrl as adminController
    participant Svc as UserService
    participant Repo as UserRepository
    participant DB as MongoDB (User Model)

    Admin->>FE: Click Verify on MC User row
    FE->>Ctrl: PATCH /api/v1/admin/users/:id { isVerified: true }
    Ctrl->>Svc: updateUserStatus(id, { isVerified })
    Svc->>Repo: updateById(id, { isVerified })
    Repo->>DB: User.findByIdAndUpdate(id, {isVerified}, {new:true})
    DB-->>Repo: updatedUserDoc / Null
    Repo-->>Svc: updatedUserDoc / Null
    Svc-->>Ctrl: updatedUserDoc / Null
    alt Target not found
        Ctrl-->>FE: HTTP 404 (User not found)
    else Update successful
        Ctrl-->>FE: HTTP 200 { data: { user } }
        FE-->>Admin: Notification "MC Verified Successfully"
    end
```

### 4. Integrated Communication Diagram

```mermaid
flowchart LR
    Admin((Admin)) -->|1. Click Verify| FE[Admin Frontend]
    FE -->|2. PATCH Request| Ctrl[adminController]
    Ctrl -->|3. call service| Svc[UserService]
    Svc -->|4. call repo| Repo[UserRepository]
    Repo -->|5. update query| DB[(MongoDB)]
    DB -->|6. Updated User| Repo
    Repo -->|7. return data| Svc
    Svc -->|8. return data| Ctrl
    Ctrl -->|9. JSON Response| FE
    FE -->|10. Update UI Element| Admin
```

### 5. Detail Design

**Figure III-4.34** Detailed Design Classes for UC: Verify MC

| Component | Detail |
|-----------|--------|
| **API Endpoint** | `PATCH /api/v1/admin/users/:id` |
| **Request Body** | `{ isVerified: true }` |
| **Controller** | `adminController.updateUserStatus(req, res)` |
| **Service** | `UserService.updateUserStatus(id, { isVerified })` |
| **Repository** | `UserRepository.updateById(id, { isVerified })` |
| **Database Query** | `User.findByIdAndUpdate(id, { isVerified }, { new: true })` |
| **Target Field** | `isVerified` boolean on the `User` schema |
| **Note** | Uses the same endpoint and controller method as UC33 but targets `isVerified` instead of `isActive` |
| **Response** | HTTP 200 `{ data: { user } }` on success · HTTP 404 if user not found |

### 6. System High-Level Design

```mermaid
flowchart TB
    subgraph ClientLayer ["Client Layer"]
        FE[Admin Dashboard UI]
    end
    subgraph BusinessLayer ["Business Layer"]
        Ctrl[adminController]
        Svc[UserService]
    end
    subgraph DataLayer ["Data Access Layer"]
        Repo[UserRepository]
        DB[(MongoDB)]
    end

    FE --> Ctrl --> Svc --> Repo --> DB
```

---

## UC36 - View All Bookings

### 1. Use Case Description

**Name:** View All Bookings
**Actor:** Admin
**Description:** Admin accesses the centralized transaction log viewing all Booking interactions transpiring system-wide among Clients and MCs.

### 2. State Diagram

```mermaid
stateDiagram-v2
    [*] --> Dashboard : "Admin enters main dashboard"
    Dashboard --> Fetching : "Admin clicks 'Bookings Management'"
    Fetching --> Loading : "GET /api/v1/admin/bookings"
    Loading --> ErrorState : "Fail to process"
    Loading --> Rendering : "Success fetching array"
    Rendering --> [*] : "Displays comprehensive logs"
```

### 3. Interaction / Sequence Diagram

```mermaid
sequenceDiagram
    actor Admin
    participant FE as Admin UI
    participant Ctrl as adminController
    participant Svc as BookingService
    participant Repo as BookingRepository
    participant DB as MongoDB (Booking Model)

    Admin->>FE: Open "All Bookings Transaction" tab
    FE->>Ctrl: GET /api/v1/admin/bookings
    Ctrl->>Svc: getAllBookings()
    Svc->>Repo: findAll()
    Repo->>DB: Booking.find().populate('mc').populate('client')
    DB-->>Repo: Populated bookings array
    Repo-->>Svc: bookings (with mc + client details)
    Svc-->>Ctrl: bookings
    Ctrl-->>FE: HTTP 200 JSON { bookings }
    FE-->>Admin: Render table displaying transactions (Client ⇔ MC)
```

### 4. Integrated Communication Diagram

```mermaid
flowchart LR
    Admin((Admin)) -->|1. Click Tab| FE[Admin Frontend]
    FE -->|2. GET Request| Ctrl[adminController]
    Ctrl -->|3. call service| Svc[BookingService]
    Svc -->|4. call repo| Repo[BookingRepository]
    Repo -->|5. find and populate| DB[(MongoDB)]
    DB -->|6. Populated Array| Repo
    Repo -->|7. return data| Svc
    Svc -->|8. return data| Ctrl
    Ctrl -->|9. JSON Response| FE
    FE -->|10. Render Booking Table| Admin
```

### 5. Detail Design

**Figure III-4.36** Detailed Design Classes for UC: View All Bookings

| Component | Detail |
|-----------|--------|
| **API Endpoint** | `GET /api/v1/admin/bookings` |
| **Controller** | `adminController.getAllBookings(req, res)` |
| **Service** | `BookingService.getAllBookings()` |
| **Repository** | `BookingRepository.findAll()` |
| **Database Query** | `Booking.find().populate('mc').populate('client')` |
| **Population** | Nested MC and Client user records (name, email) are populated into each Booking document |
| **Response** | HTTP 200 `{ bookings }` with fully populated booking array |

### 6. System High-Level Design

```mermaid
flowchart TB
    subgraph ClientLayer ["Client Layer"]
        FE[Admin Dashboard]
    end
    subgraph APILayer ["API Layer"]
        Route[Admin Routes]
    end
    subgraph BusinessLayer ["Business Layer"]
        Ctrl[adminController]
        Svc[BookingService]
    end
    subgraph DataLayer ["Data Access Layer"]
        Repo[BookingRepository]
        DB[(MongoDB - Booking Collection)]
    end

    FE --> Route --> Ctrl --> Svc --> Repo --> DB
```

---

## UC37 - Resolve Disputes

### 1. Use Case Description

**Name:** Resolve Disputes / Ticketing
**Actor:** Admin
**Description:** (Theoretical Design - Pending Implementation) Admin receives complaints logged between clients and MCs, evaluates communication logs/evidence, and dictates resolution decisions (e.g., Refunds, Payouts, or Penalties). This process finalizes the dispute and cascades the outcome to the booking status.

### 2. State Diagram

```mermaid
stateDiagram-v2
    [*] --> Pending : "Dispute submitted by Client/MC"
    Pending --> UnderReview : "Admin claims and starts reviewing"
    UnderReview --> WaitingEvidence : "Admin requests additional evidence"
    WaitingEvidence --> UnderReview : "User submits evidence"
    UnderReview --> Resolved : "Admin enforces final decision"
    Resolved --> [*] : "Dispute Closed"
```

### 3. Interaction / Sequence Diagram

```mermaid
sequenceDiagram
    actor Admin
    participant FE as Admin Panel
    participant Ctrl as disputeController
    participant Svc as DisputeService
    participant Repo as DisputeRepository
    participant BookingRepo as BookingRepository
    participant DB as MongoDB

    Admin->>FE: Review details & Click "Resolve Dispute" (Submit Decision)
    FE->>Ctrl: POST /api/v1/admin/disputes/:id/resolve (decision)
    Ctrl->>Svc: processResolution(disputeId, decision)
    Svc->>Repo: updateDisputeStatus(disputeId, 'Resolved', decision)
    Repo->>DB: Dispute.findByIdAndUpdate(disputeId, ...)
    DB-->>Repo: disputeDoc
    Repo-->>Svc: updatedDispute

    opt If decision mandates Booking status change (e.g., Refunded)
        Svc->>BookingRepo: updateStatus(bookingId, decisionState)
        BookingRepo->>DB: Booking.findByIdAndUpdate(bookingId, { status: decisionState })
        DB-->>BookingRepo: updatedBooking
        BookingRepo-->>Svc: updatedBooking
    end

    Svc-->>Ctrl: executionResult
    Ctrl-->>FE: HTTP 200 { status: 'success', data }
    FE-->>Admin: Render Success state & updated data
```

### 4. Integrated Communication Diagram

```mermaid
flowchart LR
    Admin((Admin)) -->|1. Submit Decision| FE[Admin Frontend]
    FE -->|2. POST request| Ctrl[disputeController]
    Ctrl -->|3. process resolution| Svc[DisputeService]
    Svc -->|4. execute update| Repo[DisputeRepository]
    Repo -->|5. update status| DB[(MongoDB)]
    DB -->|6. return doc| Repo
    Repo -->|7. return doc| Svc
    Svc -->|8. update Booking status| BookingRepo[BookingRepository]
    BookingRepo -->|9. findByIdAndUpdate| DB
    DB -->|10. return booking| BookingRepo
    BookingRepo -->|11. return booking| Svc
    Svc -->|12. result| Ctrl
    Ctrl -->|13. JSON response| FE
    FE -->|14. Render UI| Admin
```

### 5. Detail Design

**Figure III-4.37** Detailed Design Classes for UC: Resolve Disputes

| Component | Detail |
|-----------|--------|
| **API Endpoint** | `POST /api/v1/admin/disputes/:id/resolve` *(Theoretical)* |
| **Request Body** | `{ decision: "Refund" / "Payout" / "Penalty" }` |
| **Controller** | `disputeController.resolveDispute(req, res)` |
| **Service** | `DisputeService.processResolution(disputeId, decision)` |
| **Repository 1** | `DisputeRepository.updateDisputeStatus(disputeId, 'Resolved', decision)` → `Dispute.findByIdAndUpdate()` |
| **Repository 2** | `BookingRepository.updateStatus(bookingId, decisionState)` → `Booking.findByIdAndUpdate()` *(optional branch)* |
| **Optional Branch** | Booking status update only triggered when `decision = Refund` or `Penalty` |
| **Dispute Model** | Fields: `bookingId`, `reportedBy`, `reason`, `evidenceUrls`, `status: ['Pending','UnderReview','Resolved']`, `decision` |
| **Response** | HTTP 200 `{ status: 'success', data }` |

### 6. System High-Level Design

```mermaid
flowchart TB
    subgraph ClientLayer ["Client Layer"]
        FE[Admin Dashboard UI]
    end
    subgraph APILayer ["API Layer"]
        Route[Admin/Dispute Routes]
    end
    subgraph BusinessLayer ["Business Layer"]
        Ctrl[disputeController]
        Svc[DisputeService]
    end
    subgraph DataLayer ["Data Access Layer"]
        Repo[DisputeRepository]
        BookingRepo[BookingRepository]
        Model[Dispute / Booking Models]
    end
    subgraph StorageLayer ["Storage Layer"]
        DB[(MongoDB)]
    end

    FE -->|POST: resolve| Route
    Route --> Ctrl --> Svc --> Repo --> Model --> DB
    Svc -->|opt| BookingRepo --> Model
```

---

## UC38 - View All Transactions

### 1. Use Case Description

**Name:** View All Transactions
**Actor:** Admin
**Description:** Admin monitors all financial movements on the platform, including deposits, final payments, and theoretical refund transactions.

### 2. State Diagram

```mermaid
stateDiagram-v2
    [*] --> Dashboard : "Admin enters Finance section"
    Dashboard --> FetchingData : "Trigger GET /api/v1/admin/transactions"
    FetchingData --> Processing : "Server query"
    Processing --> Error : "Database error"
    Processing --> Loaded : "Success"
    Error --> Dashboard : "Retry"
    Loaded --> [*] : "Display transaction table"
```

### 3. Interaction / Sequence Diagram

```mermaid
sequenceDiagram
    actor Admin
    participant FE as Admin Panel
    participant Ctrl as adminController
    participant Svc as TransactionService
    participant Repo as TransactionRepository
    participant DB as MongoDB (Transaction Model)

    Admin->>FE: Open "Platform Transactions" page
    FE->>Ctrl: GET /api/v1/admin/transactions
    Ctrl->>Svc: getAllTransactions()
    Svc->>Repo: findAll()
    Repo->>DB: Transaction.find().populate('mc').populate('client')
    DB-->>Repo: Array of populated transactions
    Repo-->>Svc: transactions (with mc + client name/email)
    Svc-->>Ctrl: transactions
    Ctrl-->>FE: HTTP 200 { data: { transactions } }
    FE-->>Admin: Render transaction list with IDs, amounts, and statuses
```

### 4. Integrated Communication Diagram

```mermaid
flowchart LR
    Admin((Admin)) -->|1. View Finance| FE[Admin Frontend]
    FE -->|2. GET Request| Ctrl[adminController]
    Ctrl -->|3. call service| Svc[TransactionService]
    Svc -->|4. call repo| Repo[TransactionRepository]
    Repo -->|5. find and populate| DB[(MongoDB)]
    DB -->|6. Results| Repo
    Repo -->|7. return data| Svc
    Svc -->|8. return data| Ctrl
    Ctrl -->|9. JSON Response| FE
    FE -->|10. Render List| Admin
```

### 5. Detail Design

**Figure III-4.38** Detailed Design Classes for UC: View All Transactions

| Component | Detail |
|-----------|--------|
| **API Endpoint** | `GET /api/v1/admin/transactions` |
| **Controller** | `adminController.getAllTransactions(req, res)` |
| **Service** | `TransactionService.getAllTransactions()` |
| **Repository** | `TransactionRepository.findAll()` |
| **Database Query** | `Transaction.find().populate('mc').populate('client')` |
| **Population** | Retrieves `client` and `mc` name/email to provide context for each financial record |
| **Response** | HTTP 200 `{ data: { transactions } }` with populated transaction array |

### 6. System High-Level Design

```mermaid
flowchart TB
    subgraph ClientLayer ["Client Layer"]
        FE[Admin Finance UI]
    end
    subgraph BusinessLayer ["Business Layer"]
        Ctrl[adminController]
        Svc[TransactionService]
    end
    subgraph DataLayer ["Data Access Layer"]
        Repo[TransactionRepository]
        DB[(MongoDB - Transaction Collection)]
    end

    FE --> Ctrl --> Svc --> Repo --> DB
```
