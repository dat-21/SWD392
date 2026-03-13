import os
import re

filepath = r"d:\code\Spring2026\SWD392\UC_Diagrams_EN.md"
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# ================================
# UC19: Update MC Profile
# ================================
# No major flow changes, just DTO mapping notes
text = text.replace(
    "| `MCProfileDTO.fromOnboardingRequest` | Validate & sanitize input data |",
    "| `MCProfileDTO.fromOnboardingRequest` | Maps niche -> eventTypes, media -> showreels, and sanitizes |"
)

# ================================
# UC20: Upload Media
# ================================
# Remove backend Multer flow, as backend just receives urls in PUT /profile.
uc20_frontend_upload_main_flow = """| **Main Flow** | 1. MC navigates to the Portfolio/Media page<br>2. MC selects a file (image/video)<br>3. System validates the file (type, size)<br>4. System uploads the file to Cloud Storage (S3/Cloudinary)<br>5. System saves the URL into MCProfile.showreels<br>6. New media is displayed in the gallery |"""
uc20_frontend_new_main_flow = """| **Main Flow** | 1. MC navigates to the Portfolio/Media page<br>2. MC selects a file<br>3. Frontend uploads to Cloud Storage<br>4. Cloud Storage returns URL<br>5. Frontend sends Media URL via PUT /api/v1/mc/profile<br>6. New media is displayed |"""
text = text.replace(uc20_frontend_upload_main_flow, uc20_frontend_new_main_flow)

uc20_seq_old = """    MC->>FE: Select file & click Upload
    FE->>FE: Validate file type & size (client-side)
    FE->>Router: POST /api/v1/mc/profile/media (multipart/form-data)
    Router->>Ctrl: uploadMedia(req, res)
    Ctrl->>Ctrl: Validate file (server-side)
    Ctrl->>Cloud: Upload file (multer + cloud SDK)
    Cloud-->>Ctrl: { url, publicId }
    Ctrl->>Svc: addShowreel(userId, {url, type})
    Svc->>Repo: pushShowreel(userId, showreelData)
    Repo->>DB: MCProfile.findOneAndUpdate($push: {showreels})
    DB-->>Repo: updatedProfile
    Repo-->>Svc: updatedProfile
    Svc-->>Ctrl: updatedProfile
    Ctrl-->>Router: res.status(201).json({status: 'success'})
    Router-->>FE: HTTP 201 Response
    FE-->>MC: Display new media in gallery"""

uc20_seq_new = """    MC->>FE: Select file & click Upload
    FE->>FE: Validate file type & size
    FE->>Cloud: Upload directly to S3/Cloudinary SDK
    Cloud-->>FE: URL returned {url, type}
    FE->>Router: PUT /api/v1/mc/profile
    Note right of FE: {media: [{url, type}]}
    Router->>Ctrl: updateProfile(req, res)
    Ctrl->>Svc: updateProfile(userId, {showreels})
    Svc->>Repo: updateByUserId
    Repo->>DB: MCProfile.findOneAndUpdate()
    DB-->>Repo: updatedProfile
    Repo-->>Svc: updatedProfile
    Svc-->>Ctrl: updatedProfile
    Ctrl-->>Router: res.status(200).json({status: 'success'})
    Router-->>FE: HTTP 200 Response
    FE-->>MC: Display new media in gallery"""
text = text.replace(uc20_seq_old, uc20_seq_new)

uc20_icd_old = """    MC((MC)) -->|1. Upload file| FE[Frontend]
    FE -->|2. multipart/form-data| API[API Server]
    API -->|3. Auth Check| AUTH[JWT Middleware]
    AUTH -->|4. Multer parse| MULTER[Multer Middleware]
    MULTER -->|5. File buffer| CTRL[mcController]
    CTRL -->|6. Upload stream| CLOUD[Cloud Storage]
    CLOUD -->|7. URL response| CTRL
    CTRL -->|8. Save URL| SVC[MCService]
    SVC -->|9. $push showreel| REPO[MCProfileRepository]
    REPO -->|10. Write| DB[(MongoDB)]
    DB -->|11. Confirm| REPO
    REPO -->|12. Result| SVC
    SVC -->|13. DTO| CTRL
    CTRL -->|14. JSON| FE
    FE -->|15. Render gallery| MC"""
    
uc20_icd_new = """    MC((MC)) -->|1. Upload file| FE[Frontend]
    FE -->|2. File stream| CLOUD[Cloud Storage]
    CLOUD -->|3. URL| FE
    FE -->|4. PUT /mc/profile| API[API Server]
    API -->|5. Auth Check| AUTH[JWT Middleware]
    AUTH -->|6. Call update| CTRL[mcController]
    CTRL -->|7. updateProfile| SVC[MCService]
    SVC -->|8. Save showreels| REPO[MCProfileRepository]
    REPO -->|9. Write| DB[(MongoDB)]
    DB -->|10. Result| REPO
    REPO -->|11. Profile| SVC
    SVC -->|12. DTO| CTRL
    CTRL -->|13. JSON Response| FE
    FE -->|14. Render gallery| MC"""
text = text.replace(uc20_icd_old, uc20_icd_new)

text = text.replace(
    "- **URL:** `/api/v1/mc/profile/media`",
    "- **URL:** `/api/v1/mc/profile` (Frontend handles cloud upload and sends URL via profile update)"
)
text = text.replace(
    "- **Method:** POST",
    "- **Method:** PUT"
)

# ================================
# UC21: View Schedule
# ================================
# Need to show getAvailability combining Schedule and Booking
uc21_seq_old = """    MC->>FE: Access Calendar page
    FE->>Router: GET /api/v1/mc/calendar
    Router->>Ctrl: getCalendar(req, res)
    Ctrl->>Svc: getCalendar(userId)
    Svc->>Repo: findByMCId(userId)
    Repo->>DB: Schedule.find({mc: userId}).populate('bookingId')
    DB-->>Repo: scheduleEntries[]
    Repo-->>Svc: scheduleEntries[]
    Svc-->>Ctrl: calendar data
    Ctrl-->>Router: res.status(200).json({data: {calendar}})
    Router-->>FE: HTTP 200 JSON
    FE->>FE: Render calendar (day/week/month view)
    FE-->>MC: Display color-coded calendar"""
    
uc21_seq_new = """    MC->>FE: Access Calendar page
    FE->>Router: GET /api/v1/mc/calendar
    Router->>Ctrl: getCalendar(req, res)
    Ctrl->>Svc: getCalendar(userId)
    Svc->>AvailSvc: getAvailability(userId)
    
    par Concurrent Data Fetch
        AvailSvc->>SchedRepo: findByMCId(userId)
        SchedRepo->>DB: Schedule.find({mc: userId})
        DB-->>SchedRepo: schedules[]
        
        AvailSvc->>BookRepo: findCalendarByMCId(userId)
        BookRepo->>DB: Booking.find({mc: userId}).populate()
        DB-->>BookRepo: bookings[]
    end
    
    AvailSvc->>AvailSvc: Merge & Map schedules + bookings
    AvailSvc-->>Svc: sorted calendar array
    Svc-->>Ctrl: calendar data
    Ctrl-->>Router: res.status(200).json({data: {calendar}})
    Router-->>FE: HTTP 200 JSON
    FE->>FE: Render calendar
    FE-->>MC: Display color-coded calendar"""
text = text.replace(uc21_seq_old, uc21_seq_new)

uc21_icd_old = """    SVC -->|6. findByMCId| REPO[ScheduleRepository]
    REPO -->|7. Query + populate| DB[(MongoDB)]
    DB -->|8. Schedule docs| REPO
    REPO -->|9. Array| SVC
    SVC -->|10. Calendar data| CTRL
    CTRL -->|11. JSON 200| FE
    FE -->|12. Calendar UI| MC"""
uc21_icd_new = """    SVC -->|6. getAvailability| ASVC[AvailabilityService]
    ASVC -->|7. Concurrency Query| SREPO[ScheduleRepository]
    ASVC -->|7. Concurrency Query| BREPO[BookingRepository]
    SREPO -->|8. Schedules| ASVC
    BREPO -->|8. Bookings| ASVC
    ASVC -->|9. Merged Array| SVC
    SVC -->|10. Calendar data| CTRL
    CTRL -->|11. JSON 200| FE
    FE -->|12. Calendar UI| MC"""
text = text.replace(uc21_icd_old, uc21_icd_new)


# ================================
# UC22: Update Busy Schedule
# ================================
# Remove checkConflict as backend just blindly inserts Busy block
uc22_seq_old = """    Ctrl->>Svc: blockDate(userId, dateData)
    Svc->>Repo: checkConflict(userId, date, startTime, endTime)
    Repo->>DB: Schedule.findOne({mc, date, status: 'Booked', overlap})
    DB-->>Repo: null (no conflict)
    Repo-->>Svc: no conflict
    Svc->>Repo: create({mc: userId, ...dateData, status: 'Busy'})"""
uc22_seq_new = """    Ctrl->>Svc: blockDate(userId, dateData)
    Svc->>Repo: create({mc: userId, ...dateData, status: 'Busy'})"""
text = text.replace(uc22_seq_old, uc22_seq_new)

uc22_act_old = """    J --> K[MCService.blockDate checks for conflicts]
    K --> L{Slot already Booked?}
    L -- Yes --> M[Return error: Slot conflict]
    M --> C
    L -- No --> N[ScheduleRepository.create with status Busy]"""
uc22_act_new = """    J --> K[MCService.blockDate]
    K --> N[ScheduleRepository.create with status Busy]"""
text = text.replace(uc22_act_old, uc22_act_new)

uc22_icd_old = """    SVC -->|6. Check conflict| REPO[ScheduleRepository]
    REPO -->|7. Query existing| DB[(MongoDB)]
    DB -->|8. No conflict| REPO
    SVC -->|9. Create entry| REPO"""
uc22_icd_new = """    SVC -->|6. Create entry| REPO[ScheduleRepository]"""
text = text.replace(uc22_icd_old, uc22_icd_new)
text = text.replace(
    "| **Alternative Flows** | 4a. Slot already has a Booking → Display error \"Cannot block a slot with an existing booking\"<br>4b. Date in the past → Display error |",
    "| **Alternative Flows** | 4a. Date in the past → Display error (client-side handling) |"
)
text = text.replace(
    "4. System checks if the slot is already Booked<br>5. System creates Schedule entry",
    "4. System creates Schedule entry"
)

# ================================
# UC23: Set Availability Status
# ================================
# Remove complex pending bookings check
uc23_seq_old = """    Ctrl->>Svc: updateProfile(userId, { status: "Busy" })
    
    opt Switching to Busy
        Svc->>BookRepo: findPendingByMCId(userId)
        BookRepo->>DB: Booking.find({mc: userId, status: 'Pending'})
        DB-->>BookRepo: pendingBookings[]
        BookRepo-->>Svc: pendingBookings (if any - warn)
    end
    
    Svc->>McRepo: updateByUserId(userId, {status: "Busy"})"""
uc23_seq_new = """    Ctrl->>Svc: updateProfile(userId, { status: "Busy" })
    Svc->>McRepo: updateByUserId(userId, {status: "Busy"})"""
text = text.replace(uc23_seq_old, uc23_seq_new)

# ================================
# UC33: Lock/Unlock Account
# ================================
# Remove Email & Notification dispatch
uc33_seq_old = """    par Send notifications in parallel
        Ctrl->>Email: Send Lock notification email
        Ctrl->>Notif: Create system notification
    end
    
    Ctrl-->>Router: res.status(200).json({data: {user}})"""
uc33_seq_new = """    Ctrl-->>Router: res.status(200).json({data: {user}})"""
text = text.replace(uc33_seq_old, uc33_seq_new)

# ================================
# UC34: Verify MC
# ================================
# Similar to UC33, no email/notif parallel
uc34_seq_old = """    par Notify MC
        Ctrl->>Notif: createNotification({user: mcId, title: 'Verified!'})
        Notif->>DB: Save notification
        Ctrl->>Email: sendVerificationEmail(mc.email)
    end

    Ctrl-->>FE: HTTP 200"""
uc34_seq_new = """    Ctrl-->>FE: HTTP 200"""
text = text.replace(uc34_seq_old, uc34_seq_new)

# ================================
# UC36 & UC37 notes
# ================================
text = text.replace(
    "| **Use Case ID** | UC37 |",
    "| **Use Case ID** | UC37 (Note: Requires separate microservice/module expansion) |"
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)

print("Document updated successfully.")
