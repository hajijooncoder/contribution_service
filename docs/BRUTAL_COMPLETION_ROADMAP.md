
# نقشه راه تکمیل سختگیرانه پلتفرم مشارکتی MAHOUNN
**Classification:** Executive Roadmap — Brutal Reality Edition  
**Version:** 1.0.0  
**Date:** ۴ نوامبر ۲۰۲۶  
**Target Duration:** ۸ هفته (۶۰ روز)

---

## 🎯 خلاصه اجرایی

پلتفرم مشارکت حقوقی MAHOUNN در حال حاضر **۶۰٪ کامل** است:
- ✅ Backend: ۱۰۰٪ (۴ router، ۵ model، ۱۲ core module، ۱۶۱ test)
- ⚠️ Frontend: ۶۰٪ (۷ component موجود، اما Dashboard، Admin Panel، Real-time و E2E tests ندارد)

**هدف:** تکمیل ۴۰٪ باقیمانده در ۸ هفته با رویکرد سختگیرانه و مبتنی بر شواهد.

---

## 📊 وضعیت فعلی (Baseline — ۴ نوامبر ۲۰۲۶)

### ✅ موارد تکمیل‌شده

**Backend (`/home/haji/Desktop/contribution_service/backend/`):**
- API Endpoints: `auth.py`, `contribution.py`, `review.py`, `export.py`
- Models: `User`, `Submission`, `UploadedFile`, `Review`, `AuditLog`
- Core: Quarantine، FSM، Ledger، Duplicate Detection، Text Enhancement
- Tests: ۱۸ فایل، ۱۶۱+ test، همه پاس می‌شوند

**Frontend (`/home/haji/Desktop/contribution_service/frontend/`):**
- Components: `ContributionForm`, `ContributionHistory`, `ReviewerQueue`, `Header`, `Footer`, `LoginModal`, `TextEnhancementPreviewModal`
- UI/UX: Tailwind CSS 4، RTL، Persian-first، زیبا و حرفه‌ای

### ❌ موارد ناقص

| مورد | وضعیت | تأثیر |
|------|--------|-------|
| Dashboard صفحه اصلی | ❌ ندارد | HIGH — کاربران بعد از login صفحه اصلی ندارند |
| Admin Panel | ❌ ندارد | HIGH — مدیریت کاربران و نظارت ممکن نیست |
| Real-time Validation | ❌ ندارد | MEDIUM — UX ضعیف‌تر است |
| WebSocket Notifications | ❌ ندارد | MEDIUM — کاربران باید صفحه را refresh کنند |
| E2E Tests | ❌ ندارد | CRITICAL — regression ممکن است |
| Advanced Search | ❌ ندارد | LOW — nice-to-have |

---

## 🗓️ نقشه راه ۸ هفته‌ای

### **Week 1-2: Dashboard & Real-time Validation**

#### ✅ Deliverable 1: Dashboard Page
**صفحه اصلی پس از ورود کاربر**

**Backend (۱ روز):**
```python
# New endpoint: GET /contribution/recent-activity
@router.get("/recent-activity", response_model=List[RecentActivityItem])
def get_recent_activity(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns last 5 activities for current user"""
    submissions = (
        db.query(Submission)
        .filter(Submission.submitter_id == current_user.id)
        .order_by(Submission.updated_at.desc())
        .limit(limit)
        .all()
    )
    return [
        RecentActivityItem(
            id=sub.id,
            title=sub.legal_document_name,
            status=sub.status,
            date=sub.updated_at.isoformat()
        )
        for sub in submissions
    ]
```

**Frontend (۳ روز):**
```typescript
// New: DashboardPage.tsx
import { apiClient } from '../api/client';

interface Stats {
  total_submissions: number;
  pending_submissions: number;
  accepted_submissions: number;
  rejected_submissions: number;
  contribution_credits: number;
}

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [recentActivity, setRecentActivity] = useState([]);
  
  useEffect(() => {
    Promise.all([
      apiClient.getStats(),
      apiClient.getRecentActivity()
    ]).then(([statsData, activityData]) => {
      setStats(statsData);
      setRecentActivity(activityData);
    });
  }, []);
  
  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard title="کل مشارکت‌ها" value={stats?.total_submissions} />
        <StatCard title="در حال داوری" value={stats?.pending_submissions} />
        <StatCard title="تأیید شده" value={stats?.accepted_submissions} />
        <StatCard title="امتیازات MCC" value={stats?.contribution_credits} />
      </div>
      
      {/* Recent Activity */}
      <RecentActivityList items={recentActivity} />
      
      {/* Quick Actions */}
      <QuickActions />
    </div>
  );
};
```

**Tests (۱ روز):**
```typescript
// DashboardPage.test.tsx
describe('DashboardPage', () => {
  it('fetches and displays stats', async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText('۱۲۳')).toBeInTheDocument(); // total
    });
  });
});
```

**Definition of Done:**
- [ ] Endpoint `/recent-activity` implemented & tested
- [ ] DashboardPage component complete
- [ ] Unit tests passing
- [ ] Responsive design verified
- [ ] Screenshot added to docs

---

#### ✅ Deliverable 2: Real-time URL Validation
**بازخورد فوری در فرم ارسال**

**Backend (۱ روز):**
```python
@router.post("/validate-url")
async def validate_url_realtime(url: str):
    is_valid, authority, error = validate_official_legal_source_url(url)
    return {
        "valid": is_valid,
        "authority": authority,
        "error": error
    }
```

**Frontend (۲ روز):**
```typescript
// Update ContributionForm.tsx
const [urlValidation, setUrlValidation] = useState<{
  valid: boolean | null;
  authority: string | null;
  error: string | null;
}>({ valid: null, authority: null, error: null });

// Debounced validation
useEffect(() => {
  const timer = setTimeout(async () => {
    if (sourceUrl.length > 10) {
      const result = await apiClient.validateUrl(sourceUrl);
      setUrlValidation(result);
    }
  }, 500);
  return () => clearTimeout(timer);
}, [sourceUrl]);

// UI feedback
<div className="relative">
  <input value={sourceUrl} onChange={e => setSourceUrl(e.target.value)} />
  {urlValidation.valid && <CheckCircle className="text-green-500" />}
  {urlValidation.valid === false && <XCircle className="text-red-500" />}
</div>
```

**Definition of Done:**
- [ ] `/validate-url` endpoint working
- [ ] Debounced validation (500ms)
- [ ] Visual feedback (✓/✗ icons)
- [ ] Test coverage

---

### **Week 3-4: Admin Panel**

#### ✅ Deliverable 3: Admin User Management

**Backend (۳ روز):**
```python
# New file: backend/app/api/v1/admin.py
router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users")
def list_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    users = query.offset(skip).limit(limit).all()
    total = query.count()
    return {"users": users, "total": total}

@router.put("/users/{user_id}/activate")
def toggle_activation(
    user_id: str,
    activate: bool,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.is_active = activate
    db.commit()
    return {"user_id": user_id, "is_active": activate}

@router.get("/stats/overview")
def admin_overview(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return {
        "total_users": db.query(func.count(User.id)).scalar(),
        "total_submissions": db.query(func.count(Submission.id)).scalar(),
        "pending_reviews": db.query(func.count(Submission.id)).filter(
            Submission.status.in_(["submitted", "under_review"])
        ).scalar()
    }
```

**Frontend (۴ روز):**
```typescript
// New: AdminPanel.tsx
export const AdminPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'users' | 'submissions' | 'stats'>('users');
  
  return (
    <div className="max-w-7xl mx-auto py-8 px-4">
      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tab value="users">مدیریت کاربران</Tab>
        <Tab value="submissions">نظارت بر مشارکت‌ها</Tab>
        <Tab value="stats">آمار سیستم</Tab>
      </Tabs>
      
      {activeTab === 'users' && <UserManagementTable />}
      {activeTab === 'submissions' && <SubmissionMonitoring />}
      {activeTab === 'stats' && <SystemStats />}
    </div>
  );
};

// UserManagementTable component
const UserManagementTable: React.FC = () => {
  const [users, setUsers] = useState([]);
  
  return (
    <table className="w-full">
      <thead>
        <tr>
          <th>نام</th>
          <th>ایمیل</th>
          <th>نقش</th>
          <th>وضعیت</th>
          <th>عملیات</th>
        </tr>
      </thead>
      <tbody>
        {users.map(user => (
          <tr key={user.id}>
            <td>{user.full_name}</td>
            <td>{user.email}</td>
            <td>{user.role}</td>
            <td>{user.is_active ? 'فعال' : 'غیرفعال'}</td>
            <td>
              <RolePromoteButton userId={user.id} currentRole={user.role} />
              <ActivateToggle userId={user.id} isActive={user.is_active} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
```

**Definition of Done:**
- [ ] 3 admin endpoints implemented
- [ ] AdminPanel component complete
- [ ] Access control: only admin can see
- [ ] Tests for all endpoints
- [ ] Manual E2E verification

---

### **Week 5-6: E2E Tests & WebSocket**

#### ✅ Deliverable 4: E2E Test Suite (Playwright)

**Setup (۱ روز):**
```bash
cd frontend
npm install -D @playwright/test
npx playwright install
```

**Test Scenarios (۵ روز):**
```typescript
// tests/e2e/user-journey.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Complete User Journey', () => {
  test('user can register, login, submit contribution', async ({ page }) => {
    // 1. Register
    await page.goto('http://localhost:3000');
    await page.click('text=ثبت‌نام');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'Pass123!');
    await page.fill('[name="full_name"]', 'کاربر تست');
    await page.click('button:has-text("ثبت‌نام")');
    
    // 2. Should redirect to dashboard
    await expect(page).toHaveURL(/dashboard/);
    
    // 3. Submit contribution
    await page.click('text=ارسال مشارکت');
    await page.fill('[name="legal_document_name"]', 'قانون تست');
    await page.fill('[name="source_url"]', 'https://rc.majlis.ir/fa/law/test');
    await page.fill('[name="raw_legal_text"]', 'متن تست قانون...');
    await page.click('button:has-text("ثبت")');
    
    // 4. Verify success
    await expect(page.locator('text=با موفقیت ثبت شد')).toBeVisible();
  });
  
  test('reviewer can approve submission', async ({ page }) => {
    // Login as reviewer
    await page.goto('http://localhost:3000/login');
    await page.fill('[name="email"]', 'reviewer@test.com');
    await page.fill('[name="password"]', 'Pass123!');
    await page.click('button:has-text("ورود")');
    
    // Navigate to reviewer queue
    await page.click('text=صف داوری');
    await expect(page).toHaveURL(/reviewer/);
    
    // Approve first submission
    await page.click('button:has-text("تأیید"):first-of-type');
    await expect(page.locator('text=رأی شما ثبت شد')).toBeVisible();
  });
});
```

**Definition of Done:**
- [ ] 15+ E2E scenarios written
- [ ] All tests passing
- [ ] CI/CD integration
- [ ] Documentation

---

#### ✅ Deliverable 5: WebSocket Real-time Notifications

**Backend (۳ روز):**
```python
# backend/app/websocket/manager.py
from fastapi import WebSocket
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
    
    async def send_notification(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for ws in self.active_connections[user_id]:
                await ws.send_json(message)

manager = ConnectionManager()

# backend/app/api/v1/websocket.py
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
```

**Frontend (۲ روز):**
```typescript
// hooks/useWebSocket.ts
export const useWebSocket = (userId: string | null) => {
  const [notifications, setNotifications] = useState<any[]>([]);
  
  useEffect(() => {
    if (!userId) return;
    
    const ws = new WebSocket(`ws://localhost:8080/api/v1/ws/${userId}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setNotifications(prev => [data, ...prev]);
      toast.success(data.message); // Show toast
    };
    
    ws.onerror = () => {
      // Reconnect logic
      setTimeout(() => {
        // Retry connection
      }, 3000);
    };
    
    return () => ws.close();
  }, [userId]);
  
  return { notifications };
};
```

**Definition of Done:**
- [ ] WebSocket server working
- [ ] Frontend hook implemented
- [ ] Toast notifications showing
- [ ] Reconnection logic tested
- [ ] Integration tests

---

### **Week 7-8: Polish & Documentation**

#### ✅ Deliverable 6: Advanced Search
**Backend:** Endpoint با full-text search  
**Frontend:** Search bar + filters  
**Time:** ۳ روز

#### ✅ Deliverable 7: Performance Optimization
- Query optimization (indexes)
- Code splitting
- Bundle size < 1.5MB
**Time:** ۲ روز

#### ✅ Deliverable 8: Documentation
```
docs/
├── USER_GUIDE_FA.md
├── DEVELOPER_GUIDE.md
├── API_REFERENCE.md
├── TESTING_GUIDE.md
└── DEPLOYMENT.md
```
**Time:** ۳ روز

---

## 📈 معیارهای موفقیت

| Metric | Current | Target |
|--------|---------|--------|
| Frontend Coverage | 0% | >80% |
| E2E Tests | 0 | 15+ |
| Bundle Size | 2MB | <1.5MB |
| Lighthouse Score | ? | >90 |

---

## 🎯 نتیجه‌گیری

**این نقشه راه واقع‌بینانه است:**
- ✅ مبتنی بر کد موجود
- ✅ با شواهد فنی
- ✅ زمان‌بندی منطقی
- ✅ قابل اجرا در ۸ هفته

**قانون طلایی:** اگر تست پاس نکرد، کار تمام نشده است.

---

**نسخه:** 1.0.0  
**تهیه‌کننده:** Kiro AI  
**تاریخ:** ۴ نوامبر ۲۰۲۶
