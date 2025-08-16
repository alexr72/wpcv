# expectations_wp.md

# 🧭 WordPress Stack Expectations

This file defines the architectural, behavioral, and validation expectations for the WPCV1 stack. All contributors and validators must align with these standards.

---

## 🧱 1. Environment Expectations

- **PHP Version:** `>=8.0`
- **WordPress Version:** `>=6.0`
- **Required Plugins:**
  - `my-custom-plugin` (v1.2.3)
  - `acf-pro` (v6.x)
- **Folder Structure:**
  - `/wp-content/plugins/my-custom-plugin/`
  - `/scripts/WPCV1/`
- **Permissions:**
  - Owner: `www-data`
  - Group: `www-data`
  - Mode: `755` for folders, `644` for files

---

## 🧩 2. Frontend Expectations (JS/Vue)

- **Vue Version:** `3.x` (Composition API)
- **Build Tool:** `Vite` or `Webpack`
- **Component Structure:**
  - `/components/Form.vue`
  - `/components/Feedback.vue`
- **Form Submission:**
  - Endpoint: `POST /wp-json/myplugin/v1/submit`
  - Payload: `{ name: string, email: string, message: string }`
- **Validation Rules:**
  - `name`: required, min 2 chars
  - `email`: valid format
  - `message`: required
- **Error Handling:** Show inline feedback + log to `/logs/frontend_errors.log`

---

## 🔌 3. Backend Expectations (PHP/API)

- **REST Routes:**
  - `myplugin/v1/submit`
  - `myplugin/v1/webhook`
- **Payload Schema:**
  - Must include: `name`, `email`, `message`
- **Security:**
  - Nonce verification
  - Capability check: `current_user_can('submit_form')`
- **Response Format:**
  ```json
  {
    "success": true,
    "data": {
      "id": 123,
      "status": "received"
    }
  }
