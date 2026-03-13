## Phân tích thiết kế chi tiết (Detail Design) dựa trên kiến trúc hệ thống

Đây là phần thiết kế chi tiết và cấu trúc giao tiếp hệ thống cho hệ thống MC Hub, được xây dựng dựa trên mã nguồn thực tế của thư mục `src/controllers`, `src/services`, `src/dtos`, `src/repositories`, `src/models` của Backend Node.js.

### Quy ước chung về System High-Level Design cho toàn bộ Use Case

Kiến trúc backend của tất cả các Use Case đều tuân thủ mô hình sau:

```mermaid
flowchart TB
    subgraph ClientLayer ["Lớp Giao Diện (Client Layer)"]
        FE[React SPA / Mobile App]
    end
    
    subgraph APILayer ["Lớp Giao Tiếp (API Layer)"]
        Route[Express Router]
        Auth[Auth Middleware - JWT]
    end
    
    subgraph BusinessLayer ["Lớp Nghiệp Vụ (Business Layer)"]
        Ctrl[Controller]
        Svc[Service]
        DTO[Data Transfer Object]
    end
    
    subgraph DataLayer ["Lớp Dữ Liệu (Data Access Layer)"]
        Repo[Repository]
        Model[Mongoose Model]
    end
    
    subgraph StorageLayer ["Lớp Lưu Trữ (Storage Layer)"]
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

**Use Case Description:** MC cập nhật hồ sơ năng lực (khu vực hoạt động, kinh nghiệm, cát-xê, loại sự kiện, v.v.)
**Actor:** MC

### State Diagram
```mermaid
stateDiagram-v2
    [*] --> ViewingProfile: Đăng nhập thành công
    ViewingProfile --> EditingProfile: Nhấn "Chỉnh sửa"
    EditingProfile --> ValidatingInput: Submit Form (PUT /api/v1/mc/profile)
    ValidatingInput --> EditingProfile: Validation DTO thất bại
    ValidatingInput --> UpdatingDatabase: DTO hợp lệ
    UpdatingDatabase --> ProfileUpdated: Cập nhật CSDL thành công
    UpdatingDatabase --> ErrorState: Lỗi CSDL
    ErrorState --> EditingProfile: Thử lại
    ProfileUpdated --> ViewingProfile: Nhận HTTP 200 & Render dữ liệu mới
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

    MC->>FE: Điền thông tin profile & Nhấn Lưu
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
    FE-->>MC: Hiển thị thông báo cập nhật thành công
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
- **DTO Validation:** `MCProfileDTO.fromOnboardingRequest` ánh xạ biến đầu vào (VD: chuyển `niche` -> `eventTypes`).
- **Database Model:** `MCProfile` (mongoose schema) liên kết với `User` Model qua `user` ref ObjectId.

---

## UC20 - Upload Media

**Use Case Description:** MC tải tập tin (ảnh/video showreel) thông qua Frontend upload trực tiếp lên Storage, gửi URL về DB.
**Actor:** MC

### State Diagram
```mermaid
stateDiagram-v2
    [*] --> UploadingToCloud: MC chọn file và tải lên (Client-side)
    UploadingToCloud --> UploadFailed: Mạng yếu / File quá khổ
    UploadFailed --> [*]: Thử lại
    UploadingToCloud --> CloudURLReceived: Cloud trả về URL (AWS/Cloudinary)
    CloudURLReceived --> UpdatingProfile: Gửi PUT /api/v1/mc/profile (biến 'media')
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

    MC->>FE: Chọn Video/Ảnh & Nhấn Tải lên
    FE->>Cloud: POST Media File (Direct Upload)
    Cloud-->>FE: Trả về file URL
    FE->>Ctrl: PUT /api/v1/mc/profile { media: [{ url: "...", type: "video" }] }
    Ctrl->>Repo: udpateByUserId() (thông qua MCService)
    Repo->>DB: Cập nhật trường `showreels` array
    DB-->>Repo: success
    Repo-->>Ctrl: updatedProfile
    Ctrl-->>FE: HTTP 200 OK
    FE-->>MC: Preview ảnh/video vừa tải
```

### Detail Design
- Không có backend controller chuyên biệt xử lý form-data file upload (Multer không được sử dụng ở layer profile).
- **Trường CSDL:** Lưu vào biến `showreels: [ { url: String, type: Enum['image','video'] } ]` trong `MCProfile`.

---

## UC21 - View Schedule

**Use Case Description:** Chức năng hiển thị lịch làm việc, tổng hợp giữa các lịch bị block thủ công và các Booking đã được khách hàng đặt thành công chức năng.
**Actor:** MC

### State Diagram
```mermaid
stateDiagram-v2
    [*] --> RequestingCalendar: Mở trang Dashboard Lịch
    RequestingCalendar --> QueryingDB: GET /api/v1/mc/calendar
    QueryingDB --> CalculatingSchedules: CSDL trả về Schedule & Bookings
    CalculatingSchedules --> RenderingUI: Merge và sắp xếp sự kiện
    RenderingUI --> [*]: Hiển thị lịch trên màn hình
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

    MC->>FE: Mở Calendar view
    FE->>Ctrl: GET /api/v1/mc/calendar
    Ctrl->>AvailSvc: getAvailability(userId)
    
    par Truy vấn song song
        AvailSvc->>SRepo: findByMCId(userId)
        SRepo->>DB: Schedule.find({mc: userId})
        AvailSvc->>BRepo: findCalendarByMCId(userId)
        BRepo->>DB: Booking.find({mc: userId}).populate()
    end
    
    DB-->>SRepo: list of Manual Schedules
    DB-->>BRepo: list of Bookings
    SRepo-->>AvailSvc: (Busy, Available slots)
    BRepo-->>AvailSvc: (Confirmed Bookings)
    AvailSvc->>AvailSvc: Merge array & Sort theo thời gian
    AvailSvc-->>Ctrl: formatted calendar array
    Ctrl-->>FE: JSON Array (isAvailable, status, title...)
    FE-->>MC: Vẽ khối màu trên giao diện Lịch
```

### Detail Design
- **Controller:** `mcController.getCalendar`
- Việc thống kê Lịch được gộp bởi 2 Model độc lập là `Schedule` (lịch do MC tự khoá báo bận) và `Booking` (Hợp đồng thực tế diễn ra). Mapping bởi `AvailabilityService`.

---

## UC22 & UC23 - Update Busy Schedule / Set Availability Status

**Use Case Description:** MC khoá lịch (báo bận) trong một khoảng thời gian cụ thể (qua UC22) hoặc đánh dấu Slot Available khả dụng (UC23).
**Actor:** MC

*Backend sử dụng chung Table `Schedule` để đánh dấu trạng thái "Busy" hoặc "Available" cho khoảng thời gian này.*

### Sequence / Interaction Diagram
```mermaid
sequenceDiagram
    actor MC
    participant FE as Frontend 
    participant Ctrl as mcController / availabilityController
    participant Svc as MCService / AvailabilitySvc
    participant Repo as ScheduleRepository
    participant DB as MongoDB (Schedule)

    MC->>FE: Chọn ngày giờ -> Đánh dấu Bận / Chờ Book
    FE->>Ctrl: POST /api/v1/mc/calendar/blockout (hoặc POST /availability)
    Ctrl->>Svc: blockDate(userId, {date, startTime, endTime})
    Svc->>Repo: create({mc, date, startTime, endTime, status: 'Busy'/'Available'})
    Repo->>DB: Schedule.insert()
    DB-->>Repo: successful doc insert
    Repo-->>Svc: newSchedule
    Svc-->>Ctrl: data
    Ctrl-->>FE: HTTP 201 Created
    FE-->>MC: Chuyển ô lịch thành màu Đỏ (Busy) hoặc Xanh (Available)
```

### Detail Design
- **API (Block Date):** `POST /api/v1/mc/calendar/blockout` -> gán tự động `status = 'Busy'`.
- **API (Set Availability):** `POST /api/v1/availability` -> gán `status` phụ thuộc vào cờ `isAvailable` truyền từ Client.
- **Model:** `Schedule` chứa schema `status: { enum: ["Available", "Booked", "Busy"] }`.

---

## UC32 - View Users Lists

**Use Case Description:** Admin xem danh sách toàn bộ Users trên hệ thống.
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
    FE-->>Admin: Table (DataGrid) hiển thị danh sách
```

---

## UC33 & UC34 - Lock/Unlock Account & Verify MC

**Use Case Description:** Admin xác nhận hồ sơ của MC (Verify = true) hoặc khóa mõm User vi phạm (Active = false).
**Actor:** Admin

### State Diagram
```mermaid
stateDiagram-v2
    [*] --> Unverified_Active: Tài khoản mới tạo
    Unverified_Active --> Verified_Active: Admin duyệt Verify (isVerified = true)
    Verified_Active --> Verified_Banned: Admin khóa tài khoản (isActive = false)
    Verified_Banned --> Verified_Active: Admin mở khóa (isActive = true)
    Unverified_Active --> Unverified_Banned: Admin khóa ngay (isActive = false)
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
    DB-->>Ctrl: updatedUserDoc / Null (nếu ko tìm thấy id)
    alt Không tìm thấy User
        Ctrl-->>FE: HTTP 404 (User not found)
    else Cập nhật thành công
        Ctrl-->>FE: HTTP 200 { data: { user } }
        FE-->>Admin: Notification "Cập nhật trạng thái thành công"
    end
```

### Detail Design
- Cả hai thao tác (Khóa/Mở và Xác nhận tài liệu MC) đều chung 1 hàm Controller `adminController.updateUserStatus`.
- **Database Fields:** `User.isActive` (Mặc định: true), `User.isVerified` (Mặc định: false). Chỉ thay đổi Boolean thông qua Update MongoDB.

---

## UC36 - View All Bookings

**Use Case Description:** Trình quản lý toàn bộ các giao dịch hợp đồng trên hệ thống giúp Admin theo dõi doanh thu và tiến độ.
**Actor:** Admin

### Sequence / Interaction Diagram
```mermaid
sequenceDiagram
    actor Admin
    participant FE as Admin UI
    participant Ctrl as adminController
    participant DB as MongoDB (Booking Model)

    Admin->>FE: Mở xem tab "All Bookings Transaction"
    FE->>Ctrl: GET /api/v1/admin/bookings
    Ctrl->>DB: Booking.find().populate('mc').populate('client')
    DB-->>Ctrl: Bookings populated with User Data Details
    Ctrl-->>FE: HTTP 200 JSON
    FE-->>Admin: Render bảng hiển thị lịch sử mua/bán (Client ⇔ MC)
```

---

## UC37 - Resolve Disputes (Giải quyết tranh chấp)

_Tính năng này theo thực tế Check Code backend chưa được hiện thực hóa ở file tuyến APIs (api/v1/admin) cũng như `adminController.js`, do vậy không có Detail Design hay Sequence Diagram cho logic backend. Logic hoàn toàn Missing in Codebase._ 
_Yêu cầu phía Backend / PM phát hành thêm Issue để Develop tính năng Complaint/Dispute Tracking._
