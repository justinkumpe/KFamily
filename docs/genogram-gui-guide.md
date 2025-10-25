# Genogram GUI User Guide

## Overview
The KFamily Genogram provides a professional, interactive family tree visualization with complete data management capabilities based on GenoPro standards.

## Accessing the Genogram
Navigate to: `http://localhost:8000/tree`

## Main Interface Components

### 1. Genogram Toolbar
Located at the top of the genogram display with the following buttons:

#### Data Entry Buttons
- **Add Partnership** - Create romantic/marital relationships between family members
- **Add Life Event** - Record significant life events for any person
- **Add Medical Condition** - Track health information for family members

#### Utility Buttons
- **Clear Selection** - Deselect any selected people
- **Refresh** - Reload the genogram from the database

### 2. Interactive Genogram Canvas
The main visualization area displays:
- **Person Symbols**:
  - Males: Blue squares
  - Females: Pink circles
  - Unknown/Other: Purple diamonds
  - Current user: Gold border with glow effect
  - Deceased: X marks through symbol

- **Relationship Lines**:
  - Married: Solid red line
  - Divorced: Gray line with // slashes
  - Separated: Gray line with / slash
  - Common Law: Dashed red line
  - Engaged: Dashed blue line with 'E' marker
  - Parent-Child: Gray connecting lines

### 3. Person Detail Panel
Click on any person symbol to open the side panel showing:
- Full name
- Date of birth
- Gender
- Quick action buttons:
  - Select for Partnership
  - Add Life Event
  - Add Medical Condition

## Creating Data

### Adding a Partnership

**Method 1: Using the Toolbar**
1. Click "Add Partnership" in the toolbar
2. Select Person 1 from dropdown
3. Select Person 2 from dropdown
4. Choose relationship type
5. Fill in optional details (dates, quality, custody, notes)
6. Click "Save Partnership"

**Method 2: Using Person Selection**
1. Click on the first person's symbol
2. Click on the second person's symbol
3. Partnership modal opens automatically with both people selected
4. Fill in details and save

**Partnership Fields:**
- **Required**:
  - Person 1
  - Person 2
  - Relationship Type (married, divorced, separated, common_law, engaged, dating, former_partner, widowed)

- **Optional**:
  - Relationship Quality (normal, close, very_close, distant, estranged, conflicted, abusive)
  - Start Date
  - End Date (leave blank if ongoing)
  - Location
  - Has Children (checkbox)
  - Custody Type (if has children):
    - Joint Custody
    - Sole Custody - Mother/Father
    - Primary Custody - Mother/Father
    - Split Custody
    - Other Guardian
  - Custody Notes
  - General Notes

### Adding a Life Event

1. Click "Add Life Event" in toolbar
2. Select the person
3. Choose event type from categorized list:
   - **Life Milestones**: Birth, Death, Adoption
   - **Relationships**: Marriage, Divorce, Separation, Engagement
   - **Family**: Child Born, Child Adopted, Gained/Lost Custody
   - **Education & Career**: Started/Completed Education, Started Career, Career Change, Retirement
   - **Health**: Diagnosis, Hospitalization, Recovery, Surgery
   - **Legal**: Arrest, Incarceration, Release
   - **Other**: Relocation, Military Service, Immigration, Religious Event, Achievement, Trauma, Other

4. Enter event date
5. Provide a title
6. Add description (optional)
7. Set location and end date if applicable
8. Toggle "Show on genogram" and "Mark as private"
9. Click "Save Event"

**Quick Access**: Click person symbol → "Add Life Event" button in detail panel

### Adding a Medical Condition

1. Click "Add Medical Condition" in toolbar
2. Select the person
3. Enter condition name
4. Set diagnosis date (optional)
5. Set resolution date if condition is resolved
6. Check applicable attributes:
   - Genetic/Hereditary condition
   - Chronic condition
   - Terminal condition
   - Cause of death
7. Add notes
8. Set privacy (defaults to private)
9. Click "Save Condition"

**Quick Access**: Click person symbol → "Add Medical Condition" button in detail panel

## Workflow Examples

### Recording a Marriage
1. Click on spouse 1's symbol in the genogram
2. Click on spouse 2's symbol
3. Partnership modal opens with both selected
4. Select "Married" as relationship type
5. Enter marriage date
6. Enter location (e.g., "Las Vegas, NV")
7. If they have children, check "This partnership has children"
8. Select custody arrangement if applicable
9. Click "Save Partnership"
10. **Result**: Red line appears connecting the spouses

### Documenting a Divorce
Option A - Create new divorced partnership:
1. Follow marriage steps but select "Divorced" as type
2. Enter start date (when married) and end date (when divorced)
3. Set custody details
4. **Result**: Gray line with // appears

Option B - Update existing marriage:
1. (Future feature) Edit existing partnership
2. Change type to "Divorced"
3. Set end date

### Tracking Health History
1. Click on person's symbol
2. Click "Add Medical Condition" in detail panel
3. Enter "Diabetes Type 2"
4. Set diagnosis date
5. Check "Chronic condition"
6. Check "Genetic/Hereditary condition" if applicable
7. Add notes: "Managed with metformin, regular monitoring required"
8. Keep "Mark as private" checked
9. Click "Save Condition"

### Recording Major Life Events
**Example: College Graduation**
1. Click "Add Life Event"
2. Select the person
3. Event Type: "EDUCATION_COMPLETE"
4. Title: "Graduated from University of California"
5. Description: "Bachelor of Science in Computer Science, 3.8 GPA"
6. Event Date: Graduation date
7. Location: "Berkeley, CA"
8. Check "Show on genogram"
9. Click "Save Event"

## Tips & Best Practices

### Data Entry
- Start with partnerships (marriages) as they're most visible on genogram
- Use consistent date formats
- Be descriptive in notes for future reference
- Mark sensitive information as private
- Use "Show on genogram" to control what displays on the visual diagram

### Partnership Creation
- The order of Person 1 and Person 2 doesn't matter
- System prevents creating partnerships between a person and themselves
- You can create multiple partnerships for the same person (e.g., first marriage, second marriage)

### Privacy
- Medical conditions default to private
- Life events can be toggled private/public
- Private data is still visible to authorized users but marked as sensitive

### Genogram Navigation
- Symbols are clickable - click to see person details
- Use the side panel for quick actions
- Refresh after adding data to see updated visualization
- Clear selection before starting new partnership creation

## API Endpoints (For Developers)

### Partnerships
- `POST /api/partnerships` - Create partnership
- `GET /api/partnerships/<id>` - Get specific partnership
- `PUT /api/partnerships/<id>` - Update partnership
- `DELETE /api/partnerships/<id>` - Delete partnership

### Life Events
- `POST /api/life-events` - Create event
- `GET /api/life-events/<id>` - Get specific event
- `PUT /api/life-events/<id>` - Update event
- `DELETE /api/life-events/<id>` - Delete event

### Medical Conditions
- `POST /api/medical-conditions` - Create condition
- `GET /api/medical-conditions/<id>` - Get specific condition
- `PUT /api/medical-conditions/<id>` - Update condition
- `DELETE /api/medical-conditions/<id>` - Delete condition

### Genogram Data
- `GET /api/tree` - Get complete genogram data including people, relationships, partnerships, events, and medical conditions

## Database Schema

### Partnerships Table
Stores romantic/marital relationships with:
- person1_id, person2_id (foreign keys to users)
- relationship_type (enum)
- relationship_quality (enum)
- start_date, end_date
- location
- has_children (boolean)
- custody_type (enum)
- custody_notes, notes

### Life Events Table
Stores significant life events with:
- user_id (foreign key)
- event_type (enum with 25+ types)
- title, description
- event_date, end_date
- location
- related_user_id, related_partnership_id
- is_private, show_on_genogram (boolean flags)

### Medical Conditions Table
Stores health history with:
- user_id (foreign key)
- condition_name
- diagnosis_date, resolution_date
- is_genetic, is_chronic, is_terminal, is_cause_of_death (boolean flags)
- notes
- is_private (defaults to true)

## Future Enhancements
- Edit existing partnerships, events, and conditions
- Delete functionality from UI
- Household boundaries (dashed rectangles)
- Event timeline view
- Medical history filtering
- Export genogram as PDF/image
- Import from GEDCOM format
- Relationship strength indicators
- Advanced filtering and search
- Print-optimized view

## Troubleshooting

**Genogram doesn't load**
- Check browser console (F12) for errors
- Verify you're logged in
- Ensure database connection is working
- Try refreshing the page

**Can't save partnership**
- Ensure both people are selected
- Check that required fields are filled
- Verify people aren't the same person
- Check browser console for API errors

**Partnership line doesn't appear**
- Verify both people are in the genogram
- Ensure they're on the same generation level
- Refresh the genogram
- Check that partnership was saved successfully

**Modal won't open**
- Ensure JavaScript is enabled
- Check for browser console errors
- Try clearing browser cache
- Verify Bootstrap is loading correctly

## Support
For issues or questions, check:
1. Browser console for error messages
2. Docker logs: `docker compose logs app`
3. Database connection: `docker compose ps`
4. API responses: Network tab in browser dev tools
