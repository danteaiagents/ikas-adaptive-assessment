# IKAS — OCI Deployment Guide

> Deploys IKAS to Oracle Cloud Infrastructure Always Free tier.  
> Estimated time: 45–60 minutes for first deployment.

---

## Prerequisites

- An OCI account with Always Free resources available
- SSH key pair (generate if needed: `ssh-keygen -t ed25519 -C "ikas-oci"`)
- Your Claude API key (`sk-ant-...`)
- The IKAS codebase on your local machine

---

## Step 1: Create OCI VM Instance

1. Log into [cloud.oracle.com](https://cloud.oracle.com)
2. Navigate to **Compute → Instances → Create Instance**
3. Configure:
   - **Name**: `ikas-server`
   - **Image**: Ubuntu 22.04 (Canonical)
   - **Shape**: `VM.Standard.A1.Flex` — **Ampere ARM, Always Free**
     - OCPUs: **4** | Memory: **24 GB** (maximum Always Free)
   - **Networking**: Create new VCN, or use existing. Enable **Assign public IPv4**.
   - **SSH keys**: Upload your public key (`~/.ssh/ikas-oci.pub`)
4. Click **Create**. Note the **Public IP** when the instance is `RUNNING`.

---

## Step 2: Open Firewall Ports in OCI Console

OCI has **two** layers of firewall. Both must be opened.

### 2a. Security List (VCN level)
1. Go to **Networking → Virtual Cloud Networks → your VCN → Security Lists → Default**
2. Add **Ingress Rules**:

| Protocol | Source | Port | Description |
|----------|--------|------|-------------|
| TCP | 0.0.0.0/0 | 22 | SSH |
| TCP | 0.0.0.0/0 | 80 | HTTP |
| TCP | 0.0.0.0/0 | 443 | HTTPS |

### 2b. OS-level firewall
The `setup.sh` script handles this automatically (runs `ufw` on Ubuntu).

---

## Step 3: Connect and Run Setup Script

```bash
# SSH into your OCI VM
ssh -i ~/.ssh/ikas-oci ubuntu@YOUR_VM_IP

# On the VM: download and run setup script
curl -O https://raw.githubusercontent.com/.../deploy/oci/setup.sh
# OR copy from your local machine:
# scp -i ~/.ssh/ikas-oci deploy/oci/setup.sh ubuntu@YOUR_VM_IP:~/

chmod +x setup.sh
./setup.sh

# Log out and back in (required for Docker group to apply)
exit
ssh -i ~/.ssh/ikas-oci ubuntu@YOUR_VM_IP
```

---

## Step 4: Copy Application Code to VM

From your **local machine** (in the IKAS repo root):

```bash
# Copy entire project (excluding node_modules, .git, __pycache__)
rsync -avz --progress \
  --exclude 'node_modules' \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude 'frontend/.next' \
  -e "ssh -i ~/.ssh/ikas-oci" \
  ./ ubuntu@YOUR_VM_IP:/opt/ikas/
```

---

## Step 5: Configure Production Environment

On the VM:

```bash
cd /opt/ikas/deploy/oci
cp .env.production.example .env.production
nano .env.production
```

Fill in all `CHANGE_ME` values:

```env
SECRET_KEY=<run: python3 -c "import secrets; print(secrets.token_hex(32))">
JWT_SECRET_KEY=<run: python3 -c "import secrets; print(secrets.token_hex(32))">
POSTGRES_USER=ikas_user
POSTGRES_PASSWORD=<strong password, no special shell chars>
NEO4J_PASSWORD=<strong password>
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514
LLM_API_KEY=sk-ant-your_claude_api_key
CORS_ORIGINS=http://YOUR_VM_IP
OCI_AUTH_TYPE=instance_principal
OCI_REGION=us-ashburn-1
```

---

## Step 6: Build and Start Containers

```bash
cd /opt/ikas/deploy/oci

# Build images from source (first deploy)
docker compose -f docker-compose.prod.yml --env-file .env.production build

# Start all containers
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# Verify all containers are running
docker compose -f docker-compose.prod.yml ps
```

Expected output:
```
NAME              STATUS          PORTS
ikas-neo4j        Up (healthy)    7687/tcp
ikas-postgres     Up (healthy)    5432/tcp
ikas-backend      Up              5000/tcp
ikas-frontend     Up              0.0.0.0:80->80/tcp
```

---

## Step 7: Seed Neo4j Knowledge Graph

```bash
cd /opt/ikas/deploy/oci

export NEO4J_PASSWORD=your_neo4j_password
chmod +x seed.sh
./seed.sh
```

Expected output:
```
topic         | questions
t-ai-llm      | 50
```

---

## Step 8: Verify the Deployment

```bash
# Test backend health
curl http://YOUR_VM_IP/api/v1/presets

# Should return:
# {"success":true,"data":[{"id":"quick","name":"Quick Check",...},...]}
```

Open `http://YOUR_VM_IP` in your browser — you should see the IKAS login page.

Complete a full test:
1. Register a new account
2. Take a Quick Check (10 questions)
3. Verify results page shows real mastery data

---

## Step 9: Set Up OCI Object Storage (for Sprint 3 Image Uploads)

1. In OCI Console: **Storage → Object Storage → Create Bucket**
   - Name: `ikas-uploads`
   - Visibility: **Private**
2. Note your **Namespace** (shown on the bucket page)
3. Update `.env.production`:
   ```env
   OCI_NAMESPACE=your_tenancy_namespace
   OCI_BUCKET_NAME=ikas-uploads
   OCI_COMPARTMENT_ID=ocid1.compartment.oc1..xxxxx
   OCI_AUTH_TYPE=instance_principal
   ```
4. Enable **Instance Principal** auth on your VM:
   - In OCI Console: **Identity → Dynamic Groups → Create**
   - Rule: `ANY {instance.id = 'ocid1.instance.oc1..xxxxx'}`
   - Create a **Policy**: `Allow dynamic-group ikas-servers to manage objects in compartment ikas-compartment`
5. Restart backend: `docker compose -f docker-compose.prod.yml restart backend`

---

## Maintenance Commands

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend

# Restart a service
docker compose -f docker-compose.prod.yml restart backend

# Update after code changes (from /opt/ikas/deploy/oci):
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend

# Run tests in production container
docker compose -f docker-compose.prod.yml exec backend python -m pytest tests/ -v

# Neo4j browser (tunnel — don't expose 7474 publicly)
# On local machine:
ssh -L 7474:localhost:7474 -i ~/.ssh/ikas-oci ubuntu@YOUR_VM_IP
# Then open: http://localhost:7474
```

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| Can't reach `http://VM_IP` | OCI Security List not updated | Add port 80 ingress rule in OCI Console |
| Can't reach `http://VM_IP` | OS firewall blocking | `setup.sh` runs `ufw allow 80` — re-run or check `sudo ufw status` |
| Backend not starting | Missing env vars | Check `.env.production` for empty `CHANGE_ME` values |
| Neo4j not healthy after 5 min | Insufficient memory | ARM VM (24GB) is recommended; AMD (1GB) is too small for Neo4j |
| `CORS` errors in browser | `CORS_ORIGINS` wrong | Must match exactly: `http://YOUR_VM_IP` (no trailing slash) |
| Claude API errors | Wrong `LLM_API_KEY` | Verify key starts with `sk-ant-` |

---

## Resource Usage (Estimated)

| Container | RAM | CPU |
|-----------|-----|-----|
| Neo4j | ~400–600 MB | Low |
| PostgreSQL | ~80 MB | Low |
| Backend (gunicorn 2 workers) | ~200 MB | Low-medium |
| Frontend (nginx) | ~10 MB | Very low |
| **Total** | **~700–900 MB** | Well within 24GB ARM |

---

## Sprint 0 Completion Checklist

- [ ] OCI VM created (ARM, 4 OCPU, 24GB)
- [ ] Firewall ports 80/443 open in OCI Security List + OS
- [ ] `setup.sh` ran successfully on VM
- [ ] Code transferred to VM
- [ ] `.env.production` configured (no `CHANGE_ME` values left)
- [ ] All 4 containers running (`docker compose ps`)
- [ ] Neo4j seeded (50 questions)
- [ ] Full test session completed on production URL
- [ ] OCI Object Storage bucket `ikas-uploads` created
- [ ] `docs/HANDOVER.md` updated with production URL and VM IP
