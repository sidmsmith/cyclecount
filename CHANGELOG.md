# Changelog

All notable changes to the Cycle Count application will be documented in this file.

## [1.3.0] - 2026-01-26

### Added
- **Upload Progress Bar**: Added real-time progress bar directly under the Upload button that displays:
  - Current processing status (e.g., "Processing 3/10 rows...")
  - Percentage completion (0% to 100%)
  - Estimated time remaining (e.g., "~2m 30s remaining")
  - Visual progress bar with smooth animations
  - Final completion status showing success/failure counts
  - Auto-hides 2 seconds after completion

### Changed
- **UI Text Colors**: Enhanced text color enforcement for better visibility:
  - "Changes detected - will use edited data" message now displays in white
  - "Successfully uploaded..." status message now displays in white
  - Used `!important` CSS flags and specific ID selectors to override Bootstrap classes

### Technical Details
- Progress bar updates after each row completes (success or failure)
- Tracks processing time per row to calculate accurate time estimates
- Progress bar styled to match Item Generator app's Cloudinary upload progress bar
- Uses CSS transitions for smooth progress bar animations

## [1.2.0] - 2026-01-26

### Added
- **Console Visibility Control**: Added URL parameter support for controlling console button and window visibility
  - `Console=Y`: Shows console window on page load (button remains visible)
  - `Console=N`: Hides both console button and window completely
  - No Console parameter: Default behavior - button visible, console hidden (user can toggle)

### Changed
- **Console Display Logic**: Enhanced console visibility handling to support cross-app integration scenarios

## [1.1.0] - 2026-01-26

### Added
- **Editable File Preview**: File preview window is now editable, allowing users to modify cycle count data directly in the preview without reloading the file
- **Real-time Change Detection**: System detects when preview data has been edited and shows visual indicators
- **Smart Upload Logic**: Upload function automatically uses edited preview data when changes are detected
- **Quantity Mismatch Warning Handling**: Enhanced `acceptQuantity` API to treat quantity mismatch warnings as success (allows cycle count to proceed even when quantities don't match expected values)
- **Extensive Debug Logging**: Added comprehensive debug logging for API responses to aid in troubleshooting

### Changed
- **TransactionId and CriteriaId Updates**: Updated API calls 2, 4, 5, 6, and 7 to use `"Cycle Count Active-API"` and `"Cycle Count Active-API Mode"` instead of previous values
- **Upload Button Behavior**: Upload button text now reflects actual upload results after completion instead of reverting to original file count
- **UI Color Improvements**: Set text colors to white for better visibility in dark theme:
  - Cycle Count File input field text
  - Preview window data
  - Success/status messages

### Fixed
- **400 Status Code Handling**: Fixed backend to properly handle 400 BAD_REQUEST responses that contain warning messages (previously truncated responses)
- **Response Parsing**: Improved parsing logic to correctly detect WARNING type messages in API responses
- **Button Text Updates**: Fixed upload button to maintain correct singular/plural text after upload completion

### Technical Details
- Backend now parses JSON responses regardless of HTTP status code (200, 201, or 400)
- Frontend includes `hasQuantityMismatchWarning()` function to detect and handle quantity mismatch warnings
- Preview parsing function `parsePreviewText()` handles both header and data rows with proper spacing
- Real-time change detection updates button text and status indicators as user edits preview

## [1.0.0] - Initial Release

### Features
- Authentication with Manhattan WMS
- Cycle count file upload (CSV, Excel, TXT formats)
- File preview with header detection
- Sequential API workflow for cycle count processing:
  1. Authentication
  2. Initiate Count
  3. Get Inventory (ItemId lookup)
  4. Validate Item and Get Item Details
  5. Accept Quantity
  6. Persist Count Details
  7. End Count
- Console logging for debugging
- Dark theme support
- Theme selector (Dark, Manhattan themes)
