# Login and Encryption Feature Plan

## Overview
User requested: "Login and encryption to be enabled"

This is a significant feature that requires careful planning and implementation to ensure user data security and privacy while maintaining the app's current "no signup needed" value proposition.

## Current State
- Guest sessions only (anonymous, server-side sessions)
- No persistent user accounts
- No data encryption at rest
- Privacy-focused: "No signup, no data stored, free forever"

## Proposed Implementation Strategy

### 1. Hybrid Authentication Model
**Goal**: Preserve the "no signup" experience while enabling optional persistent accounts

**Approach**:
- Continue supporting anonymous guest sessions (default)
- Add optional account creation for users who want to:
  - Save scenarios across devices
  - Access historical projections
  - Share results with partners/advisors
  - Export data

**Implementation**:
```
- Anonymous mode (current): No changes
- Optional signup: Email + password OR social auth (Google, etc.)
- Progressive enhancement: Guest → Account upgrade path
```

### 2. Data Encryption

#### 2.1 Encryption at Rest
**Sensitive Fields to Encrypt**:
- Financial data (assets, income, expenses)
- Family details (names, ages)
- Venture/business details
- Future plans and goals

**Implementation Options**:
1. **Database-level encryption**: Use Django's field encryption or db-level encryption
2. **Application-level**: Encrypt before saving, decrypt on load
   - Library: `django-encrypted-model-fields` or `cryptography`
   - Key management: Django SECRET_KEY + per-user salt

**Recommended**: Application-level encryption with user-specific keys

#### 2.2 Encryption in Transit
- Already have: HTTPS/TLS (assumed for production)
- Add: Certificate pinning for mobile apps (if applicable)

### 3. Authentication Flow

```
┌─────────────────────────────────────────────────┐
│ Landing Page                                     │
│ ┌─────────────────┐  ┌────────────────────────┐ │
│ │ Start (Guest)   │  │ Login / Sign Up        │ │
│ └─────────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────┘
         │                        │
         ▼                        ▼
   Guest Session          Authenticated User
         │                        │
         ▼                        ▼
    Questions Flow          Questions Flow
         │                        │
         ▼                        ▼
    Results (temp)         Results (saved)
         │                        │
         └──────┬─────────────────┘
                ▼
         "Want to save? Sign up"
```

### 4. Privacy-Preserving Features

#### 4.1 Zero-Knowledge Architecture (Advanced)
- Encrypt data with user-derived key (password-based)
- Server never sees decryption key
- Trade-off: Password reset = data loss

#### 4.2 Pseudonymous Identifiers
- No real names required
- Email only for account recovery
- Optional profile data

#### 4.3 Data Retention Policies
- Auto-delete guest sessions after 30 days
- User-controlled data deletion
- Clear data export before deletion

### 5. Technical Implementation Plan

#### Phase 1: Core Authentication (Week 1-2)
- [ ] Add Django authentication backend
- [ ] Create User model (extend AbstractUser)
- [ ] Implement login/signup views
- [ ] Add session management
- [ ] Email verification (optional)

#### Phase 2: Data Migration & Encryption (Week 2-3)
- [ ] Add encryption utilities
- [ ] Encrypt sensitive model fields
- [ ] Migrate existing guest data structure
- [ ] Key management system
- [ ] Backup/recovery flow

#### Phase 3: UI/UX Integration (Week 3-4)
- [ ] Login/signup pages
- [ ] Guest → Account upgrade flow
- [ ] Settings page (change password, delete account)
- [ ] Privacy policy update
- [ ] Security best practices guide

#### Phase 4: Testing & Security Audit (Week 4-5)
- [ ] Penetration testing
- [ ] OWASP top 10 compliance
- [ ] Privacy compliance (GDPR considerations)
- [ ] Load testing with encryption overhead
- [ ] Recovery flow testing

### 6. Security Considerations

#### 6.1 Authentication
- Password strength requirements (min 12 chars, complexity)
- Rate limiting on login attempts
- CSRF protection (already in Django)
- Session timeout (30 min inactive)
- Optional 2FA for high-value users

#### 6.2 Encryption
- AES-256 for data at rest
- Unique salt per user
- Key derivation: PBKDF2 (100k+ iterations)
- Secure key storage (environment vars + secrets management)

#### 6.3 Compliance
- GDPR: Right to erasure, data portability
- Data residency: India-based servers (if applicable)
- Audit logging for sensitive operations

### 7. Migration Path for Existing Users

```
Current guest users:
1. Show banner: "Save your data? Create an account"
2. On signup: Transfer current session data to new account
3. Encrypt existing data with new user key
4. Delete guest session after transfer
```

### 8. Development Checklist

**Before Starting**:
- [ ] Discuss with user: Full auth or simplified version?
- [ ] Clarify: Is this for compliance or feature request?
- [ ] Decide: Zero-knowledge vs server-encrypted?

**Must-Haves**:
- [ ] Secure password storage (bcrypt/Argon2)
- [ ] HTTPS in production
- [ ] Encrypted database backups
- [ ] Security headers (CSP, HSTS, etc.)

**Nice-to-Haves**:
- [ ] Social auth (Google, etc.)
- [ ] Biometric login (for mobile)
- [ ] Hardware security key support (U2F)
- [ ] Encrypted exports (GPG/PGP)

### 9. Performance Impact

**Encryption Overhead**:
- ~5-10ms per record (encrypt/decrypt)
- Batch operations may need optimization
- Cache decrypted data in session (memory trade-off)

**Mitigation**:
- Lazy decryption (only when needed)
- Caching strategy
- Async encryption for bulk operations

### 10. Documentation Needs

- [ ] User guide: How to create account
- [ ] Security whitepaper: Encryption details
- [ ] Privacy policy update
- [ ] Developer docs: Encryption API
- [ ] Incident response plan

---

## Next Steps

1. **Validate Requirements**: Confirm with user:
   - Is login mandatory or optional?
   - What level of encryption (basic vs zero-knowledge)?
   - Timeline/priority

2. **Prototype**: Build minimal auth + encryption POC
   - Simple email/password login
   - Encrypt one model field
   - Test performance

3. **User Feedback**: Show prototype, iterate

4. **Production Rollout**: Phase 1-4 implementation

---

## Open Questions

1. Should anonymous mode remain the default?
2. Is this for regulatory compliance or user demand?
3. What's the acceptable performance trade-off?
4. Do we need audit trails (who accessed what)?
5. Mobile app considerations (biometric, keychain)?

---

**Status**: Planning phase
**Priority**: TBD (discuss with user)
**Estimated Effort**: 4-5 weeks (full implementation)
