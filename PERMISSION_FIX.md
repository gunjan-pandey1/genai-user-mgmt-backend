# Railway Deployment Fix - Permission Denied Error

## 🐛 Problem

When deploying to Railway, the backend container was failing with:
```
/bin/sh: 1: uvicorn: Permission denied
```

## 🔍 Root Cause

The issue was in the Dockerfile's multi-stage build:

1. **Builder stage**: Installed Python packages to `/root/.local` (as root user)
2. **Production stage**: 
   - Copied packages from `/root/.local` to `/root/.local`
   - Created `appuser` (non-root user)
   - Switched to `appuser`
   - Set PATH to `/root/.local/bin`

**The Problem**: The `appuser` doesn't have permission to access `/root/.local` directory!

When the container tried to run `uvicorn`, it couldn't find it because:
- `uvicorn` was in `/root/.local/bin/uvicorn`
- `appuser` couldn't access `/root/` directory
- Result: Permission denied

## ✅ Solution

Fixed the Dockerfile to copy packages to the correct location:

### Before (Broken):
```dockerfile
# Copy to /root/.local
COPY --from=builder /root/.local /root/.local

# Set PATH for root
ENV PATH=/root/.local/bin:$PATH

# Create and switch to appuser
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# appuser can't access /root/.local! ❌
```

### After (Fixed):
```dockerfile
# Create appuser first
RUN useradd -m -u 1000 appuser

# Copy to appuser's home directory
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY . .

# Set ownership for appuser
RUN chown -R appuser:appuser /app /home/appuser/.local

# Switch to appuser
USER appuser

# Set PATH for appuser
ENV PATH=/home/appuser/.local/bin:$PATH

# Now appuser can access /home/appuser/.local! ✅
```

## 🔑 Key Changes

1. **Create user first**: `useradd` before copying packages
2. **Copy to user's home**: `/home/appuser/.local` instead of `/root/.local`
3. **Set ownership**: `chown` both `/app` and `/home/appuser/.local`
4. **Switch user**: `USER appuser` after setting ownership
5. **Set PATH correctly**: `/home/appuser/.local/bin` for appuser

## 🚀 Testing the Fix

### Local Test:
```bash
cd genai-user-mgmt-backend

# Build the image
docker build -t backend-test .

# Run the container
docker run -p 8000:8000 \
  -e MONGODB_URL=mongodb://localhost:27017 \
  -e DB_NAME=test_db \
  -e GROQ_API_KEY=test_key \
  backend-test

# Should start without "Permission denied" error
```

### Railway Deployment:
1. Commit the fixed Dockerfile
2. Push to GitHub
3. Railway will automatically redeploy
4. Check logs - should see:
   ```
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:XXXX
   ```

## 📊 Verification

After deploying, verify:

1. **Check Railway Logs**:
   - No "Permission denied" errors
   - Server starts successfully
   - Uvicorn is running

2. **Test Health Endpoint**:
   ```bash
   curl https://your-backend.railway.app/health
   ```
   Expected: `{"status": "healthy", "service": "genai-user-mgmt-backend"}`

3. **Test API Docs**:
   - Visit: `https://your-backend.railway.app/docs`
   - Should load Swagger UI

## 🎯 Why This Matters

### Security Benefits:
- ✅ Running as non-root user (best practice)
- ✅ Minimal permissions for appuser
- ✅ Isolated user environment

### Proper Permissions:
- ✅ appuser owns `/app` (application code)
- ✅ appuser owns `/home/appuser/.local` (Python packages)
- ✅ appuser can execute uvicorn
- ✅ No permission issues

## 📝 Summary

**Problem**: Permission denied when running uvicorn as non-root user  
**Cause**: Python packages in `/root/.local`, inaccessible to `appuser`  
**Solution**: Copy packages to `/home/appuser/.local` with proper ownership  
**Result**: Container runs successfully with non-root user ✅

---

**The fix is now applied and ready for deployment! 🚀**
