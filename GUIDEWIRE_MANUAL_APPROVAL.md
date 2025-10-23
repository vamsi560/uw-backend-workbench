# 🚨 Guidewire Manual Approval Required

## Issue Summary
**Job Number:** 0000749253  
**Internal Job ID:** pc:SaFJf4ZwC8X-E8FnwJZex  
**Problem:** Job approved in our system but still shows "UW Review" in Guidewire

## Root Cause
- Guidewire API connection timeout during approval process
- Our system marked as approved, but Guidewire never received the approval
- API endpoint: `pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net` is not accessible

## Manual Fix Required

### Steps for Guidewire Team:
1. **Log into Guidewire UI**
2. **Search for job:** `0000749253` or `pc:SaFJf4ZwC8X-E8FnwJZex`
3. **Check current status:** Should show "UW Review" 
4. **Find pending UW issues** that need approval
5. **Manually approve all UW issues**
6. **Verify status changes** from "UW Review" to "Approved"

### Expected Result:
- Job status in Guidewire changes to "Approved"
- Matches the status in our underwriting system
- Process can continue to quote generation

## Technical Details for IT Team

### Connection Issue:
```
Error: HTTPSConnectionPool timed out
Host: pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net
Port: 443
Timeout: 30 seconds
```

### Possible Solutions:
1. **Check Guidewire server status** - Is the dev environment down?
2. **Network connectivity** - Firewall or VPN issues?
3. **Use production URL** - Is there a prod Guidewire environment?
4. **Increase timeout** - Server might be slow but responding

### API Endpoint Used:
- **UW Issues:** `GET /rest/job/v1/jobs/{job_id}/uw-issues`
- **Approval:** `POST /rest/job/v1/jobs/{job_id}/uw-issues/{issue_id}/approve`

## Prevention for Future
1. **Add retry logic** for Guidewire API calls
2. **Better error handling** when Guidewire is unavailable  
3. **Status sync verification** after approval
4. **Fallback to manual process** when API fails

---
**Created:** October 22, 2025  
**Priority:** High - Customer waiting for quote  
**Status:** Requires manual intervention in Guidewire