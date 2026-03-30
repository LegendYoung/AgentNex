# AgentNex Platform API Reference v1.0

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API Version**: v1
- **认证方式**: JWT Bearer Token
- **Content-Type**: `application/json`

---

## 认证相关接口

### 1. 用户注册

**POST** `/api/v1/auth/register`

**请求体**：
```json
{
  "email": "user@example.com",
  "password": "Pass@123",      // 8-32字符，含大小写字母+数字+特殊字符
  "name": "User Name"          // 可选，2-32字符
}
```

**响应**：`200 OK`
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "name": "User Name",
    "role": "user",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

**错误码**：
- `400`: 参数校验失败
- `409`: 邮箱已存在

---

### 2. 用户登录

**POST** `/api/v1/auth/login`

**请求体**：
```json
{
  "email": "user@example.com",
  "password": "Pass@123"
}
```

**响应**：`200 OK`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "user_id": "uuid",
    "email": "user@example.com",
    "name": "User Name",
    "role": "user",
    "require_password_change": false
  }
}
```

**错误码**：
- `401`: 邮箱或密码错误
- `403`: 账号已禁用

---

### 3. 刷新 Token

**POST** `/api/v1/auth/refresh`

**请求头**：`Authorization: Bearer {refresh_token}`

**响应**：`200 OK`
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer"
  }
}
```

---

### 4. 修改密码

**POST** `/api/v1/auth/change-password`

**请求头**：`Authorization: Bearer {access_token}`

**请求体**：
```json
{
  "old_password": "OldPass@123",
  "new_password": "NewPass@456"
}
```

**响应**：`200 OK`
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

**错误码**：
- `400`: 旧密码错误
- `401`: Token 无效

---

### 5. 获取当前用户信息

**GET** `/api/v1/auth/me`

**请求头**：`Authorization: Bearer {access_token}`

**响应**：`200 OK`
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "name": "User Name",
    "role": "user",
    "status": "active",
    "created_at": "2024-01-01T00:00:00",
    "last_login_at": "2024-01-01T12:00:00"
  }
}
```

---

## 用户管理接口（管理员）

### 6. 获取用户列表

**GET** `/api/v1/users`

**权限**：`admin` 或 `super_admin`

**请求头**：`Authorization: Bearer {access_token}`

**查询参数**：
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 20）
- `role`: 角色筛选（可选）
- `search`: 搜索关键词（可选）

**响应**：`200 OK`
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "user_id": "uuid",
        "email": "user@example.com",
        "name": "User Name",
        "role": "user",
        "status": "active",
        "created_at": "2024-01-01T00:00:00",
        "last_login_at": "2024-01-01T12:00:00"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 7. 修改用户角色

**PATCH** `/api/v1/users/{user_id}/role`

**权限**：`super_admin`

**请求头**：`Authorization: Bearer {access_token}`

**请求体**：
```json
{
  "role": "admin"
}
```

**响应**：`200 OK`
```json
{
  "success": true,
  "message": "User role updated to admin"
}
```

**错误码**：
- `400`: 不能修改自己的角色
- `403`: 不能修改其他超级管理员的角色
- `404`: 用户不存在

---

### 8. 修改用户状态

**PATCH** `/api/v1/users/{user_id}/status`

**权限**：`admin` 或 `super_admin`

**请求头**：`Authorization: Bearer {access_token}`

**请求体**：
```json
{
  "status": "disabled"
}
```

**响应**：`200 OK`
```json
{
  "success": true,
  "message": "User status updated to disabled"
}
```

---

### 9. 删除用户

**DELETE** `/api/v1/users/{user_id}`

**权限**：`super_admin`

**请求头**：`Authorization: Bearer {access_token}`

**响应**：`200 OK`
```json
{
  "success": true,
  "message": "User deleted successfully"
}
```

---

## 团队管理接口

### 10. 创建团队

**POST** `/api/v1/teams`

**权限**：已登录用户

**请求头**：`Authorization: Bearer {access_token}`

**请求体**：
```json
{
  "name": "团队名称",              // 2-32字符
  "description": "团队描述"        // 可选，10-200字符
}
```

**响应**：`200 OK`
```json
{
  "success": true,
  "data": {
    "team_id": "uuid",
    "name": "团队名称",
    "description": "团队描述",
    "creator_id": "uuid",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

---

### 11. 获取团队列表

**GET** `/api/v1/teams`

**权限**：已登录用户

**请求头**：`Authorization: Bearer {access_token}`

**响应**：`200 OK`
```json
{
  "success": true,
  "data": {
    "teams": [
      {
        "team_id": "uuid",
        "name": "团队名称",
        "description": "团队描述",
        "role": "admin",
        "member_count": 5,
        "created_at": "2024-01-01T00:00:00"
      }
    ],
    "total": 1
  }
}
```

---

### 12. 邀请成员

**POST** `/api/v1/teams/{team_id}/invitations`

**权限**：团队管理员

**请求头**：`Authorization: Bearer {access_token}`

**请求体**：
```json
{
  "email": "newuser@example.com",
  "role": "editor"     // admin, editor, viewer
}
```

**响应**：`200 OK`
```json
{
  "success": true,
  "data": {
    "invitation_id": "uuid",
    "invite_code": "abc123...",
    "invite_url": "https://your-domain.com/register?invite=abc123...&email=newuser@example.com",
    "expires_at": "2024-01-02T00:00:00",
    "email": "newuser@example.com",
    "role": "editor"
  }
}
```

---

### 13. 获取团队邀请列表

**GET** `/api/v1/teams/{team_id}/invitations`

**权限**：团队管理员

**请求头**：`Authorization: Bearer {access_token}`

**响应**：`200 OK`
```json
{
  "success": true,
  "data": {
    "invitations": [
      {
        "invitation_id": "uuid",
        "email": "newuser@example.com",
        "role": "editor",
        "status": "pending",
        "created_at": "2024-01-01T00:00:00",
        "expires_at": "2024-01-02T00:00:00"
      }
    ],
    "total": 1
  }
}
```

---

### 14. 加入团队

**POST** `/api/v1/teams/join`

**权限**：已登录用户

**请求头**：`Authorization: Bearer {access_token}`

**请求体**：
```json
{
  "invite_code": "abc123..."
}
```

**响应**：`200 OK`
```json
{
  "success": true,
  "data": {
    "team_id": "uuid",
    "team_name": "团队名称",
    "role": "editor"
  }
}
```

**错误码**：
- `400`: 邀请码已使用/已过期
- `403`: 邮箱不匹配
- `404`: 邀请码无效

---

### 15. 获取团队成员列表

**GET** `/api/v1/teams/{team_id}/members`

**权限**：团队成员

**请求头**：`Authorization: Bearer {access_token}`

**响应**：`200 OK`
```json
{
  "success": true,
  "data": {
    "members": [
      {
        "user_id": "uuid",
        "name": "User Name",
        "email": "user@example.com",
        "role": "admin",
        "joined_at": "2024-01-01T00:00:00"
      }
    ],
    "total": 5
  }
}
```

---

### 16. 修改成员角色

**PATCH** `/api/v1/teams/{team_id}/members/{user_id}/role`

**权限**：团队管理员

**请求头**：`Authorization: Bearer {access_token}`

**查询参数**：`role` (admin/editor/viewer)

**响应**：`200 OK`
```json
{
  "success": true,
  "message": "Member role updated successfully"
}
```

---

### 17. 移除成员

**DELETE** `/api/v1/teams/{team_id}/members/{user_id}`

**权限**：团队管理员

**请求头**：`Authorization: Bearer {access_token}`

**响应**：`200 OK`
```json
{
  "success": true,
  "message": "Member removed successfully"
}
```

---

### 18. 删除团队

**DELETE** `/api/v1/teams/{team_id}`

**权限**：团队创建者

**请求头**：`Authorization: Bearer {access_token}`

**响应**：`200 OK`
```json
{
  "success": true,
  "message": "Team deleted successfully"
}
```

---

## 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "detail": "Error message"
}
```

**HTTP 状态码**：
- `400`: 请求参数错误
- `401`: 未授权（Token 无效/过期）
- `403`: 权限不足
- `404`: 资源不存在
- `409`: 资源冲突（如邮箱已存在）
- `500`: 服务器内部错误

---

## 认证说明

### JWT Token 使用

1. 登录成功后获取 `access_token` 和 `refresh_token`
2. 在所有需要认证的请求中添加请求头：
   ```
   Authorization: Bearer {access_token}
   ```
3. `access_token` 有效期 2 小时
4. `refresh_token` 有效期 7 天
5. 使用 `/api/v1/auth/refresh` 刷新 `access_token`

### 角色权限说明

| 角色 | 权限范围 |
|------|---------|
| `super_admin` | 全平台最高权限，管理所有用户/资源/系统配置 |
| `admin` | 管理用户、审核资源、查看日志，不可修改系统核心配置 |
| `user` | 管理自己创建的资源、共享给自己的资源、可创建/加入团队 |

### 团队角色说明

| 角色 | 权限 |
|------|------|
| `admin` | 邀请/移除成员、修改角色、管理团队资源 |
| `editor` | 可编辑团队共享资源，不可管理成员 |
| `viewer` | 仅可查看团队共享资源 |

---

## 在线文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
