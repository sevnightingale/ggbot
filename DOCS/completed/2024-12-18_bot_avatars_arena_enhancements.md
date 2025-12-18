# 2024-12-18 - Bot Profile Images + Arena Page Enhancements

**Completed**: December 18, 2024
**Tasks**: Bot avatar upload system, mobile UX fix, Arena page redesign

---

## 🖼️ Bot Profile Images Feature (Full-Stack)

### **Overview**
Complete implementation of custom bot avatar uploads with automatic image processing and Supabase Storage integration.

### **Database**
- Added `profile_image_url TEXT` column to `configurations` table
- Nullable column (NULL = no custom image uploaded)

### **Backend Changes**

#### `ggbot.py`
- Updated `ConfigUpdateRequest` model with `profile_image_url` field
- Modified `GET /api/v2/config/{config_id}` to return `profile_image_url`
- Modified `PUT /api/v2/config/{config_id}` to accept `profile_image_url` updates

#### `core/services/config_service.py`
- Updated `BotConfigV2` class constructor with `profile_image_url` parameter
- Modified `to_dict()` method to include `profile_image_url` in response
- Updated `get_config()` SQL query to SELECT `profile_image_url`
- Updated `list_configs()` SQL query to include `profile_image_url`
- Modified `update_config()` to handle `profile_image_url` parameter
- Added `profile_image_url` to UPDATE statement

### **Frontend Changes**

#### New Component: `BotImageUpload.tsx`
**Features**:
- Drag-drop or click-to-upload interface
- Automatic image resize to 1024×1024 (center-crop, maintains aspect ratio)
- Canvas-based image processing with 90% JPEG quality
- Uploads to Supabase Storage: `bot-avatars/{user_id}/{config_id}.jpg`
- Progress spinner during upload
- Hover-to-remove button (small X icon top-right)
- Upload icon placeholder when no image
- 5MB file size limit
- Supports JPG/PNG/WebP input formats

**Error Handling**:
- File type validation
- File size validation
- Upload failure handling with user-friendly messages
- Preview revert on error

#### Integration: `ActivationBar.tsx`
- Added `BotImageUpload` component next to bot name
- 48px circular avatar with brass border
- Positioned in header section for always-visible bot identity

#### TypeScript: `lib/api.ts`
- Added `profile_image_url?: string | null` to `BotConfiguration` interface

### **Supabase Storage Setup** (Manual)

**Bucket**: `bot-avatars`
- Public bucket (images accessible via public URLs)
- 5MB file size limit
- Allowed MIME types: `image/jpeg`, `image/png`, `image/webp`

**RLS Policies**:
```sql
-- Users can upload to their own folder
CREATE POLICY "Users can upload bot avatars"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'bot-avatars'
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Users can update their own images
CREATE POLICY "Users can update their bot avatars"
ON storage.objects FOR UPDATE
USING (
  bucket_id = 'bot-avatars'
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Users can delete their own images
CREATE POLICY "Users can delete their bot avatars"
ON storage.objects FOR DELETE
USING (
  bucket_id = 'bot-avatars'
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Everyone can view images (public read)
CREATE POLICY "Anyone can view bot avatars"
ON storage.objects FOR SELECT
USING (bucket_id = 'bot-avatars');
```

**Storage Path Structure**:
```
bot-avatars/
└── {user_id}/
    └── {config_id}.jpg
```

### **UX Flow**
1. User clicks on 48px circular avatar (or drags image onto it)
2. Image automatically resized to 1024×1024 with center-crop
3. Uploads to Supabase Storage
4. Gets public URL
5. Updates configuration via `PUT /api/v2/config/{config_id}`
6. Preview updates immediately
7. Hover over image shows X button to remove

### **Files Modified**
- `ggbot.py` - API endpoint updates
- `core/services/config_service.py` - Config service updates
- `frontend/components/BotImageUpload.tsx` - New component (311 lines)
- `frontend/app/forge/components/monitor/ActivationBar.tsx` - Integration
- `frontend/lib/api.ts` - TypeScript interface update

---

## 📱 Mobile Bot Rail Scrolling Fix

### **Issue**
Mobile drawer for bot switching was not scrollable when users had more bots than could fit on screen.

### **Root Cause**
Drawer container was not using flexbox layout, so `overflow-y-auto` on child didn't work.

### **Solution** (`MobileNav.tsx`)

**Line 88**: Added `flex flex-col` to drawer container
```tsx
<div className="... flex flex-col">
```

**Line 90**: Added `flex-shrink-0` to header (prevents collapse)
```tsx
<div className="... flex-shrink-0">
```

**Line 101**: Added `overflow-y-auto` with padding to content area
```tsx
<div className="flex-1 overflow-y-auto p-4">
```

### **Result**
```
┌─────────────────────┐
│   Header (fixed)    │ ← flex-shrink-0
├─────────────────────┤
│   Bot List          │ ← flex-1 overflow-y-auto
│   (scrollable)      │    (scrolls independently)
│   ↕️                 │
└─────────────────────┘
```

---

## 🏆 Arena Page Enhancements

### **Overview**
Redesigned `/arena` page for "The ggARENA" prototype competition showcase with CTA for Season 1.

### **Competition Details**
- **Start Date**: December 18, 2024
- **Duration**: 21 days
- **End Date**: January 8, 2025
- **Season 1 Opens**: January 15, 2025 (7 days after prototype ends)

### **New Features**

#### 1. Hero Section
```
THE ggARENA
7 AI Trading Archetypes • 21 Days • $70,000 Starting Capital

[Progress Bar] Day X of 21 | X days remaining
```

**Implementation**:
- Large centered title with trophy icon
- Subtitle with competition details
- Dynamic progress bar calculated from start date (Dec 18)
- Days elapsed and days remaining counters
- Brass accent color for progress bar

#### 2. Live Rankings (New Section)
```
LIVE RANKINGS                    🔴 LIVE

🥇 #1  [Avatar] The Contrarian    $11,247  +12.47%
🥈 #2  [Avatar] The Technician    $10,892   +8.92%
🥉 #3  [Avatar] The Arbiter       $10,456   +4.56%
   #4  [Avatar] The Sentinel      $10,234   +2.34%
...
```

**Features**:
- Medal emojis (🥇🥈🥉) for top 3 positions
- Position numbers (#4-7) for remaining bots
- Profile avatars with color-coded borders (matches chart colors)
- Bot names with equity and P&L% (green/red coloring)
- Pulsing red "LIVE" indicator
- Sorted by current equity (highest first)

#### 3. Enhanced Bot Cards

**Added Bot Descriptions** (from `NOTE.md`):
- Frequency + Symbol line (e.g., "1hr · BTC")
- Strategy tagline in italics
- All 7 archetypes mapped by bot name

**Bot Descriptions Hardcoded**:
```typescript
const BOT_DESCRIPTIONS: Record<string, { frequency, symbol, tagline }> = {
  'The Technician': { frequency: '5min', symbol: 'BTC', tagline: '...' },
  'The Sentinel': { frequency: '15min', symbol: 'BTC', tagline: '...' },
  'The Herald': { frequency: '30min', symbol: 'BTC', tagline: '...' },
  'The Contrarian': { frequency: '1hr', symbol: 'BTC', tagline: '...' },
  'The Arbiter': { frequency: '4hr', symbol: 'BTC', tagline: '...' },
  'The Compass': { frequency: '1d', symbol: 'BTC', tagline: '...' },
  'The Nomad': { frequency: '1w', symbol: 'Self-Evolving', tagline: '...' }
}
```

**Card Structure**:
```
┌────────────────────────────────┐
│ [Avatar] The Contrarian        │
│          1hr · BTC             │
│                                │
│ "The crowd is wrong at         │
│  extremes. Fades the herd."    │
│                                │
│ $11,247  +12.47%               │
│ 45 trades • 62% win rate       │
└────────────────────────────────┘
```

#### 4. CTA Section (Bottom)
```
🏆 Season 1 Opens January 15, 2025

Create your own trading bot and compete for prizes.
Watch these archetypes battle, then design your
strategy and enter the arena.

[Create Your Bot on ggbots.ai →]
```

**Features**:
- Large trophy icon
- Clear Season 1 launch date
- Compelling copy about creating bots
- Big brass button linking to https://ggbots.ai
- Border highlight with brass accent color
- Target: Drive signups to main platform

### **Theme Integration**
All new components use CSS variables:
- `--text-primary`, `--text-secondary`, `--text-muted`
- `--bg-primary`, `--bg-secondary`, `--bg-tertiary`
- `--border`, `--accent`, `--accent-hover`

**Result**: Dark/light mode support without hardcoded colors

### **Files Modified**
- `frontend/app/arena/page.tsx` - Complete redesign (~467 lines)

---

## 📚 Documentation Updates

### `frontend/README.md`
Added **"Bot Profile Images (2024-12-18)"** section documenting:
- Custom avatar upload feature
- Auto-processing (1024×1024 resize)
- Supabase Storage integration
- Display specs (48px circular in ActivationBar)
- Upload UX (spinner, remove button, fallback)
- Technical specs (5MB limit, formats)

---

## 📊 Impact Summary

### **Bot Profile Images**
- **Files Changed**: 5 backend, 3 frontend
- **Lines Added**: ~400 (new component + integrations)
- **User Value**: Personalized bot identity, improved visual differentiation
- **Storage**: Supabase Storage bucket with RLS policies

### **Mobile UX Fix**
- **Files Changed**: 1
- **Lines Changed**: 3 key layout properties
- **User Value**: Scrollable bot list on mobile when >8 bots

### **Arena Page**
- **Files Changed**: 1
- **Lines Changed**: ~200 (hero, rankings, descriptions, CTA)
- **User Value**: Engaging competition showcase, clear CTA for Season 1 signups

---

## 🧪 Testing Completed

### Bot Profile Images
- ✅ Upload image → resizes → uploads → shows preview
- ✅ Update image → replaces existing → URL updates in DB
- ✅ Remove image → reverts to placeholder
- ✅ Display in ActivationBar next to bot name
- ✅ Persistence across page refreshes
- ✅ Multi-bot support (each bot has different image)

### Mobile Bot Rail
- ✅ Drawer opens with scrollable content
- ✅ Header stays fixed, bot list scrolls independently
- ✅ Works with 10+ bots

### Arena Page
- ✅ Progress bar calculates correctly from Dec 18 start
- ✅ Rankings sort by equity
- ✅ Bot descriptions display from NOTE.md mappings
- ✅ CTA button links to ggbots.ai
- ✅ Dark/light theme compatibility

---

## 🚀 Deployment Notes

### **Requirements Before Launch**
1. ✅ Supabase Storage bucket created (`bot-avatars`)
2. ✅ RLS policies applied
3. ✅ Frontend build passes (no TypeScript errors)
4. ⏳ Arena subdomain setup (arena.ggbots.ai)
5. ⏳ Mark 7 prototype bots as `is_public = true`

### **Build Status**
```
✓ Compiled successfully
✓ 20 pages generated
Bundle size: 332 kB (forge), 210 kB (arena)
Warnings: Only ESLint img tag warnings (non-blocking)
```

---

## 💡 Future Enhancements (Out of Scope Today)

### Bot Profile Images
- Batch upload for multiple bots
- Image cropping UI before upload
- Profile image gallery/presets
- Admin bulk management

### Arena Page (Season 1)
- Submission/registration system
- Individual bot detail pages (`/arena/bot/[config_id]`)
- Historical season archives
- Achievement badges
- Real-time WebSocket updates
- Social sharing features

---

**Total Implementation Time**: ~6 hours
**Commits**: 3 (bot avatars, arena enhancements, docs)
**Status**: ✅ Production Ready
