# API

---

v1

```
POST   /api/v1/auth/telegram/
GET    /api/v1/users/me/
PATCH  /api/v1/users/me/
GET    /api/v1/users/me/token-limit/

GET    /api/v1/assessments/tests/
GET    /api/v1/assessments/tests/<pk>/
POST   /api/v1/assessments/tests/<pk>/start/
GET    /api/v1/assessments/sessions/<pk>/
POST   /api/v1/assessments/sessions/<pk>/answer/
GET    /api/v1/assessments/sessions/<pk>/result/

GET    /api/v1/hard-stops/
POST   /api/v1/hard-stops/
PATCH  /api/v1/hard-stops/<pk>/
DELETE /api/v1/hard-stops/<pk>/

GET    /api/v1/criteria/
POST   /api/v1/criteria/
PATCH  /api/v1/criteria/<pk>/
DELETE /api/v1/criteria/<pk>/

GET    /api/v1/candidates/
POST   /api/v1/candidates/
GET    /api/v1/candidates/<pk>/
PATCH  /api/v1/candidates/<pk>/
POST   /api/v1/candidates/<pk>/archive/
GET    /api/v1/candidates/<pk>/score/
GET    /api/v1/candidates/<pk>/status-history/
POST   /api/v1/candidates/<pk>/status/

GET    /api/v1/events/?candidate=<id>
POST   /api/v1/events/
GET    /api/v1/events/<pk>/
PATCH  /api/v1/events/<pk>/confirm/

GET    /api/v1/reports/
POST   /api/v1/reports/generate/
```

---
