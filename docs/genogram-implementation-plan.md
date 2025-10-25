# Complete Genogram Implementation Plan

Based on [GenoPro Genogram Rules](https://genopro.com/genogram/rules/), this document outlines the implementation for a complete, professional genogram system.

## Phase 1: Data Models ✅ (COMPLETED)

### New Database Tables

1. **`partnerships`** - Romantic/marital relationships
   - Tracks marriages, divorces, separations, common-law, dating, etc.
   - Includes start/end dates, location, relationship quality
   - Custody information for children

2. **`households`** - Family units/living arrangements
   - Tracks who lives together
   - Established and dissolved dates
   - Address information

3. **`household_members`** - Links people to households
   - Start and end dates for residency
   - Head of household designation

4. **`life_events`** - Significant life events
   - Marriages, divorces, relocations, education, career changes
   - Health events, legal events, achievements, traumas
   - Can be linked to other users or partnerships
   - Privacy controls for sensitive events

5. **`medical_conditions`** - Health information
   - Diagnoses, genetic conditions, chronic illnesses
   - Cause of death tracking
   - Privacy controls

### Enums Created
- `RelationshipType`: married, divorced, separated, common_law, engaged, dating, etc.
- `RelationshipQuality`: close, very_close, distant, estranged, conflicted, abusive, normal
- `CustodyType`: sole_mother, sole_father, joint, split, primary_mother, primary_father, other_guardian
- `LifeEventType`: 25+ event types covering relationships, family, health, legal, career, etc.

## Phase 2: Database Migration (NEXT)

1. Create Alembic migration for new tables
2. Add foreign key constraints
3. Test migration up/down
4. Deploy to database

## Phase 3: API Endpoints

### Partnership Management
- `POST /api/partnerships` - Create partnership
- `GET /api/partnerships/<id>` - Get partnership details
- `PUT /api/partnerships/<id>` - Update partnership
- `DELETE /api/partnerships/<id>` - Delete partnership
- `GET /api/users/<id>/partnerships` - Get all partnerships for a user

### Household Management
- `POST /api/households` - Create household
- `GET /api/households/<id>` - Get household details
- `PUT /api/households/<id>` - Update household
- `DELETE /api/households/<id>` - Delete household
- `POST /api/households/<id>/members` - Add member to household
- `DELETE /api/households/<id>/members/<user_id>` - Remove member

### Life Events
- `POST /api/life-events` - Create life event
- `GET /api/life-events/<id>` - Get event details
- `PUT /api/life-events/<id>` - Update event
- `DELETE /api/life-events/<id>` - Delete event
- `GET /api/users/<id>/life-events` - Get all events for a user

### Medical Conditions
- `POST /api/medical-conditions` - Create condition
- `GET /api/medical-conditions/<id>` - Get condition details
- `PUT /api/medical-conditions/<id>` - Update condition
- `DELETE /api/medical-conditions/<id>` - Delete condition
- `GET /api/users/<id>/medical-conditions` - Get conditions for a user

### Enhanced Genogram API
- `GET /api/genogram` - Get complete genogram data including:
  - All people in network
  - Parent-child relationships
  - Partnerships with dates and status
  - Household groupings
  - Life events for each person
  - Medical conditions (respecting privacy)

## Phase 4: Genogram Visualization Enhancements

### According to GenoPro Standards

#### Relationship Lines
- **Marriage**: Solid line connecting partners
- **Divorce**: Solid line with two slashes (//)
- **Separation**: Solid line with one slash (/)
- **Common-law/Living together**: Dashed line
- **Engagement**: Dashed line with "E"
- **Former relationship**: Dashed line with slash

#### Emotional Relationships (between any two people)
- **Close**: Single solid line
- **Very close/Fused**: Triple solid lines
- **Distant**: Dashed line
- **Estranged/Cut off**: Solid line with break
- **Conflicted**: Zigzag line
- **Abusive**: Line with arrow pointing to victim

#### Custody Indicators
- Visual markers showing which parent has custody
- Dashed lines from non-custodial parent
- Joint custody indicated with special marker

#### Household Boundaries
- Dashed rectangle around people living together
- Label with household name/address

#### Medical/Health Symbols
- Standard medical symbols overlaid on person symbol
- Color coding for genetic conditions
- Special markers for cause of death

#### Person Symbol Enhancements
- **Current styling**: Circle (female), Square (male), Diamond (unknown)
- **Add**: 
  - Pregnancy indicator (triangle inside female symbol)
  - Miscarriage/Abortion (small filled circle)
  - Twins indicator (special connection)
  - Adopted (bracket around symbol)

#### Life Event Timeline
- Small icons/markers along connection lines
- Dates for significant events
- Hover to see event details

## Phase 5: User Interface

### Genogram Page Enhancements
1. **Toolbar**:
   - Add Partnership button
   - Add Life Event button
   - Add Medical Condition button
   - Create Household button
   - Filter controls (show/hide medical, show/hide events, etc.)
   - Print/Export options

2. **Interactive Features**:
   - Click person to see detailed info panel
   - Click relationship line to edit partnership details
   - Drag to reposition (manual layout override)
   - Zoom and pan controls
   - Legend showing all symbols and line types

3. **Detail Panel** (when clicking a person):
   - Basic info (name, birth, death)
   - All partnerships with dates
   - Children with custody info
   - Life events timeline
   - Medical history (if user has permission)
   - Edit buttons for each section

### New Pages/Modals

1. **Partnership Editor**:
   - Select two people
   - Relationship type dropdown
   - Start date, end date
   - Location
   - Relationship quality
   - Custody arrangements
   - Notes

2. **Life Event Editor**:
   - Event type dropdown
   - Title and description
   - Date and end date
   - Location
   - Related person (if applicable)
   - Privacy toggle
   - Show on genogram checkbox

3. **Medical Condition Editor**:
   - Condition name autocomplete
   - Diagnosis date
   - Is genetic/chronic/terminal checkboxes
   - Cause of death checkbox
   - Notes
   - Privacy toggle

4. **Household Manager**:
   - Household name and address
   - Member list with add/remove
   - Start/end dates for each member
   - Head of household selection

## Phase 6: Privacy & Permissions

### Privacy Levels
1. **Public**: Visible to all family members
2. **Family Only**: Visible to close family
3. **Private**: Only visible to person and admins
4. **Medical Privacy**: Special rules for health information

### Permission Controls
- Users can mark their own medical info as private
- Users can mark life events as private
- Admins can see all information
- Family members see based on relationship distance

## Phase 7: Data Import/Export

### Export Formats
- **GEDCOM**: Standard genealogy format
- **PDF**: Printable genogram
- **PNG/SVG**: Image export
- **JSON**: Data backup

### Import
- GEDCOM import to create family tree
- CSV import for bulk life events
- Medical history import from templates

## Implementation Priority

### Immediate (This Session):
1. ✅ Create data models
2. Create Alembic migration
3. Update genogram API to include partnerships
4. Add marriage lines to SVG visualization

### Short Term (Next):
5. Create partnership CRUD endpoints
6. Build partnership editor UI
7. Add household boundaries to genogram
8. Create life events system

### Medium Term:
9. Medical conditions system
10. Emotional relationship indicators
11. Custody indicators
12. Enhanced person symbols

### Long Term:
13. Export functionality
14. Advanced filtering
15. Print layouts
16. Mobile responsive design
17. GEDCOM import/export

## Technical Notes

### SVG Symbol Library
Need to create reusable SVG components for:
- Different relationship line styles
- Emotional relationship indicators
- Medical symbols
- Event markers
- Household boundaries

### Performance Considerations
- Lazy loading for large family trees
- Caching genogram data
- Incremental updates instead of full reload
- Virtualization for very large trees

### Database Indexes
Add indexes on:
- Partnership person IDs
- Household member user IDs
- Life event dates and user IDs
- Medical condition user IDs

## References
- [GenoPro Genogram Rules](https://genopro.com/genogram/rules/)
- [Standard Genogram Symbols](https://genopro.com/genogram/symbols/)
- [Genogram Tutorial](https://genopro.com/genogram/)
