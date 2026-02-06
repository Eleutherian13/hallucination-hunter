# Testing Guide for Hallucination Hunter v2.0

## Prerequisites

Both servers should be running:
- **Backend**: http://localhost:8000 (FastAPI with 8-layer pipeline)
- **Frontend**: http://localhost:3000 (Next.js React app)

## Test Scenario: Complete Workflow

### 1. Health Check
Navigate to: http://localhost:3000

**Expected Result:**
- Home page loads with statistics
- "Start Verification" button is visible
- Navigation menu shows all pages

---

### 2. Pipeline Inspection
Navigate to: http://localhost:3000/pipeline

**What to Test:**
- Click the **Refresh** button (top right)
- Observe pipeline status banner (should show "Full Pipeline" mode)
- Verify all 8 layers are displayed:
  1. Ingestion Layer
  2. Claim Extraction Layer
  3. Retrieval Layer
  4. Verification Layer
  5. Drift Detection Layer
  6. Scoring Layer
  7. Correction Layer
  8. Output Formatting Layer

**Expected Backend Call:**
```
GET http://localhost:8000/api/pipeline/info
```

**Expected Response:**
- Each layer shows "Active" status
- Layer count: 8
- Active layers: 8

---

### 3. Settings Configuration
Navigate to: http://localhost:3000/settings

**What to Test:**
1. Adjust **Confidence Threshold** slider to 80%
2. Toggle **Auto-generate Corrections** ON
3. Set **Max Claims per Document** to 100
4. Click **Save Settings** button
5. Refresh the page
6. Verify settings persist

**Expected Result:**
- Green success banner shows "Settings saved successfully!"
- Settings are stored in localStorage
- Values remain after page refresh

---

### 4. Document Verification (Main Feature)

Navigate to: http://localhost:3000/verify

#### Step A: Load Demo Data
1. Click **Load Demo Data** button
2. Verify text appears in both fields

#### Step B: Start Verification
1. Click **Verify Document** button
2. Watch progress bar advance through pipeline stages:
   - Uploading files...
   - Ingesting documents...
   - Extracting claims...
   - Retrieving evidence...
   - Verifying claims...
   - Scoring results...
   - Complete!

**Expected Backend Call:**
```
POST http://localhost:8000/api/verify
Content-Type: multipart/form-data

Form Fields:
- source_files: [File object]
- llm_output: "text content"
- config: JSON with settings
```

**Expected Flow:**
1. Progress bar fills 0% → 100%
2. Steps change from pending → processing → completed
3. Automatic redirect to `/results?id=<unique_id>`
4. Result stored in sessionStorage

---

### 5. Results Analysis
After verification completes, you should be on: http://localhost:3000/results

**What to Test:**
1. **Stats Row** (top):
   - Total Claims: Should show count
   - Verified: Green badges
   - Hallucinations: Red badges
   - Unverified: Yellow badges
   - Overall Confidence: Percentage

2. **Claims List** (left side):
   - Each claim card shows:
     - Claim text
     - Status badge (Verified/Hallucination/Unverified)
     - Confidence meter
   - Click on claims to see details

3. **Tabs** (right side):
   - **Source Document**: Shows original document
   - **Citations**: References to source paragraphs
   - **Corrections**: Shows suggested fixes for hallucinations
   - **Explainability**: AI reasoning for each decision

4. **Action Buttons** (bottom):
   - **Export Report**: Downloads JSON file
   - **New Verification**: Returns to verify page

**Test Export:**
1. Click **Export Report**
2. JSON file downloads with name: `verification-report-<timestamp>.json`
3. Open file to verify it contains:
   - Summary statistics
   - All claims with status, confidence, explanations
   - Corrections for hallucinations

---

### 6. HaluEval Benchmark
Navigate to: http://localhost:3000/benchmarks

**What to Test:**
1. Click **Run Benchmark** button
2. Wait for processing (shows spinner)
3. View results table

**Expected Backend Call:**
```
POST http://localhost:8000/api/benchmark/run
Body: { "dataset": "halueval", "sample_size": 20 }
```

**Expected Response:**
- **True Positives (TP)**: Correctly identified hallucinations
- **True Negatives (TN)**: Correctly identified valid claims
- **False Positives (FP)**: Wrongly flagged as hallucination
- **False Negatives (FN)**: Missed hallucinations

**Metrics:**
- Accuracy: (TP + TN) / Total
- Precision: TP / (TP + FP)
- Recall: TP / (TP + FN)
- F1 Score: Harmonic mean of precision and recall

**Success Criteria:**
- Accuracy > 85%
- Pipeline mode shows "full"
- No errors displayed

---

### 7. Documentation
Navigate to: http://localhost:3000/docs

**What to Test:**
- All sections are readable
- Code examples display correctly
- API reference shows endpoints

---

## Backend Verification

### Check Backend Logs

You should see these console outputs:

```
✓ Verification layers loaded successfully
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Test Endpoints Directly

**1. Health Check:**
```bash
curl http://localhost:8000/api/health
```
Expected: `{"status": "healthy", "layers_available": true}`

**2. Pipeline Info:**
```bash
curl http://localhost:8000/api/pipeline/info
```
Expected: JSON with 8 layers, each showing "active" status

---

## Common Issues & Solutions

### Issue: "Backend connection failed"
**Solution:**
1. Check backend is running on port 8000
2. Verify no CORS errors in browser console
3. Check firewall isn't blocking localhost:8000

### Issue: "Pipeline shows demo mode"
**Solution:**
- Backend failed to load layers
- Check backend console for import errors
- Verify `src/` directory exists with all layer files

### Issue: Verification gets stuck at 0%
**Solution:**
1. Check backend logs for errors
2. Verify file upload size isn't too large
3. Check browser console for network errors

### Issue: Settings don't persist
**Solution:**
- Browser may be blocking localStorage
- Check browser console for storage errors
- Try clearing browser cache

---

## Success Indicators

✅ **All buttons are clickable and functional**
✅ **Pipeline page shows 8 active layers**
✅ **Verification completes and shows results**
✅ **Export downloads JSON file**
✅ **Benchmark executes and shows metrics**
✅ **Settings save and load correctly**
✅ **No console errors in browser or backend**

---

## Performance Benchmarks

- **Verification Time**: < 3 seconds for small documents
- **Page Load**: < 2 seconds initial load
- **API Response**: < 500ms for pipeline info
- **Benchmark Run**: < 10 seconds for 20 samples

---

## Next Steps

If all tests pass:
1. ✅ Frontend is fully connected to backend
2. ✅ All 8 layers are operational
3. ✅ Ready for larger dataset testing
4. ✅ Can extend HaluEval to 500 samples
5. ✅ Production-ready for demonstration
