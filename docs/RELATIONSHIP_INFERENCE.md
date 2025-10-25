# Automatic Family Relationship Inference

## Overview

The `infer_family_relationships.py` script automatically infers and creates extended family relationships based on existing direct relationships. This helps maintain a complete and consistent family tree without manual data entry for every relationship.

## How It Works

The script applies relationship inference rules to determine indirect relationships. For example:

- If **Waylon** has **Justin** as father, and **Justin** has **Cindy** as mother, then:
  - **Waylon** gets **Cindy** as grandmother
  - **Cindy** gets **Waylon** as grandson

- If **Justin** has **Cindy** as mother, and **Cindy** has **Jeremy** as son, then:
  - **Justin** gets **Jeremy** as brother
  - **Jeremy** gets **Justin** as brother

## Supported Relationship Inferences

The script supports inference for:

### Grandparent Relationships
- Parent → Parent = Grandparent
- Parent → Adoptive Parent = Grandparent

### Great-Grandparent Relationships
- Grandparent → Parent = Great-Grandparent

### Aunt/Uncle Relationships
- Parent → Sibling = Aunt/Uncle

### Niece/Nephew Relationships
- Sibling → Child = Niece/Nephew

### In-Law Relationships
- Spouse → Parent = Parent-in-Law
- Spouse → Child = Step-child
- Child → Spouse = Child-in-Law
- Sibling → Spouse = Sibling-in-Law
- Spouse → Sibling = Sibling-in-Law

### Cousin Relationships
- Child → Niece/Nephew = Cousin

## Gender-Aware Reciprocals

The script automatically creates properly gendered reciprocal relationships:

- If a male child has a grandmother, the grandmother gets a **grandson** (not granddaughter)
- If a female child has an uncle, the uncle gets a **niece** (not nephew)
- Non-gendered fallback relationships are used when sex is not specified

## Usage

### Running in Docker

**Dry Run** (see what would be created without making changes):
```bash
docker compose exec app python /app/scripts/infer_family_relationships.py --dry-run
```

**Run for Real** (create the relationships):
```bash
docker compose exec app python /app/scripts/infer_family_relationships.py
```

**Quiet Mode** (suppress detailed output):
```bash
docker compose exec app python /app/scripts/infer_family_relationships.py --quiet
```

### Running Locally (with venv)

```bash
export DATABASE_URL=mysql+pymysql://user:pass@host:3306/kfamily?charset=utf8mb4
export PYTHONPATH=src
python scripts/infer_family_relationships.py --dry-run
```

## Command Options

- `--dry-run`: Show what relationships would be created without making any database changes
- `--quiet`: Suppress detailed output (only show summary)

## Running Periodically

### Automatic Execution (Docker Compose - Default)

The KFamily application includes an automated relationship inference service that runs every 15 minutes by default. This service is defined in `docker-compose.yml` and starts automatically when you run `docker compose up`.

**Check the service status:**

```bash
docker compose ps
```

**View inference logs:**

```bash
# View recent logs
docker compose logs relationship-inference --tail 50

# Follow logs in real-time
docker compose logs relationship-inference -f
```

**Manually trigger an inference run:**

```bash
# This will run immediately without waiting for the scheduled interval
docker compose exec relationship-inference python /app/scripts/infer_family_relationships.py
```

**Adjust the interval:**

Edit `docker-compose.yml` and change `sleep 900` (15 minutes) to your desired interval:
- 5 minutes: `sleep 300`
- 30 minutes: `sleep 1800`
- 1 hour: `sleep 3600`

Then restart the service:

```bash
docker compose up -d --force-recreate relationship-inference
```

### Option 1: Cron Job (Linux/Mac)

Add to your crontab to run daily at 2 AM:

```bash
0 2 * * * cd /path/to/KFamily && /usr/local/bin/docker compose exec -T app python /app/scripts/infer_family_relationships.py --quiet >> /var/log/kfamily-inference.log 2>&1
```

Or run hourly:

```bash
0 * * * * cd /path/to/KFamily && /usr/local/bin/docker compose exec -T app python /app/scripts/infer_family_relationships.py --quiet
```

### Option 2: Docker Compose Scheduled Service

Add a separate service to `docker-compose.yml`:

```yaml
services:
  inference-cron:
    image: kfamily-app  # Same as app image
    environment:
      DATABASE_URL: mysql+pymysql://kfamily:kfamilypass@db:3306/kfamily?charset=utf8mb4
    depends_on:
      db:
        condition: service_healthy
    command: >
      sh -c "while true; do
        sleep 3600;
        python /app/scripts/infer_family_relationships.py --quiet;
      done"
    restart: unless-stopped
```

### Option 3: Systemd Timer (Linux)

Create `/etc/systemd/system/kfamily-inference.service`:

```ini
[Unit]
Description=KFamily Relationship Inference
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/path/to/KFamily
ExecStart=/usr/local/bin/docker compose exec -T app python /app/scripts/infer_family_relationships.py --quiet
```

Create `/etc/systemd/system/kfamily-inference.timer`:

```ini
[Unit]
Description=Run KFamily Relationship Inference Daily

[Timer]
OnCalendar=daily
OnBootSec=10min
Persistent=true

[Install]
WantedBy=timers.target
```

Enable the timer:

```bash
sudo systemctl enable kfamily-inference.timer
sudo systemctl start kfamily-inference.timer
```

### Option 4: Manual Trigger via API (Future Enhancement)

You could create an admin API endpoint to trigger inference on-demand:

```python
@admin_bp.post("/api/admin/infer-relationships")
@api_require_groups(["admin", "super-admin"])
def trigger_relationship_inference():
    from scripts.infer_family_relationships import run_inference
    count = run_inference(dry_run=False, verbose=False)
    return jsonify({"relationships_created": count})
```

## Example Output

```
Analyzing 6 users for relationship inference...

Found 8 new relationships to create

  Waylon Kumpe -> grandmother -> Cindy Kumpe
    (reciprocal: Cindy Kumpe -> grandson -> Waylon Kumpe)
  Waylon Kumpe -> grandfather -> Jeff Kumpe
    (reciprocal: Jeff Kumpe -> grandson -> Waylon Kumpe)
  Waylon Kumpe -> uncle -> Jeremy Kumpe
    (reciprocal: Jeremy Kumpe -> nephew -> Waylon Kumpe)
  Zach Kumpe -> grandmother -> Cindy Kumpe
    (reciprocal: Cindy Kumpe -> grandson -> Zach Kumpe)
  Zach Kumpe -> grandfather -> Jeff Kumpe
    (reciprocal: Jeff Kumpe -> grandson -> Zach Kumpe)
  Zach Kumpe -> uncle -> Jeremy Kumpe
    (reciprocal: Jeremy Kumpe -> nephew -> Zach Kumpe)
  Jeremy Kumpe -> nephew -> Waylon Kumpe
  Jeremy Kumpe -> nephew -> Zach Kumpe

✅ Successfully created 12 new relationships for 3 users

Inference complete. 12 relationships created.
```

## Features

✅ **Idempotent**: Safe to run multiple times - won't create duplicates  
✅ **Gender-Aware**: Creates properly gendered reciprocal relationships  
✅ **Multi-Path Inference**: Handles relationships inferred through multiple family paths  
✅ **Auto-Generated Notes**: Marks inferred relationships with "Auto-inferred relationship" note  
✅ **Dry Run Mode**: Test before making changes  
✅ **Comprehensive Rules**: Supports grandparents, aunts/uncles, in-laws, cousins, and more

## Limitations

- Does not infer relationships that would create logical inconsistencies
- Does not update existing relationships (only creates new ones)
- Requires direct relationships to be entered manually first
- Does not handle half-siblings or step-relationships (yet)

## Best Practices

1. **Run after bulk imports**: If you import many users at once, run the inference script afterward
2. **Run periodically**: Set up a cron job to run daily or weekly to catch new relationships
3. **Test with dry-run first**: Always test with `--dry-run` before running on production data
4. **Monitor output**: Check the script output to ensure relationships are being created correctly
5. **Review inferred relationships**: Periodically review auto-generated relationships in the family tree

## Troubleshooting

**Script reports "0 new relationships" but I expected more:**
- Check that direct relationships are entered correctly
- Verify user sex is set (required for gender-specific reciprocals)
- Run with `--dry-run` and check the output

**Duplicate relationship errors:**
- Should not happen with the current implementation (commits per-relationship)
- If it does, check database constraints and existing relationships

**Performance issues with large family trees:**
- The script processes all users each run
- For very large trees (1000+ users), consider optimizing or running less frequently
- Use `--quiet` flag to reduce output overhead

## Future Enhancements

Potential improvements for future versions:

- [ ] Parallel processing for large family trees
- [ ] Incremental inference (only check recently modified users)
- [ ] Confidence scoring for inferred relationships
- [ ] Conflict detection (when multiple inference paths suggest different relationships)
- [ ] Half-sibling and step-relationship inference
- [ ] Web UI integration for manual review/approval
- [ ] Undo capability for inferred relationships
- [ ] Batch mode with progress tracking
